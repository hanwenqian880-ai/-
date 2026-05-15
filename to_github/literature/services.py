"""
Plagiarism checking service.
"""
import os
import hashlib
import logging
from django.conf import settings
from django.utils import timezone
from .models import Literature, PlagiarismCheck, SystemSettings

logger = logging.getLogger('literature')


class PlagiarismChecker:
    """Service for checking plagiarism in PDF documents."""

    def __init__(self):
        self.threshold = float(SystemSettings.get_setting('similarity_threshold', '0.7'))
        self.api_url = settings.LITERATURE_SETTINGS.get('PLAGIARISM_API_URL', '')
        self.api_key = settings.LITERATURE_SETTINGS.get('PLAGIARISM_API_KEY', '')

    def check(self, literature):
        """
        Check plagiarism for a literature.
        Returns dict with similarity score and sources.
        """
        # Try external API first if configured
        if self.api_url and self.api_key:
            try:
                return self._check_with_external_api(literature)
            except Exception as e:
                logger.warning(f"External API check failed: {e}, falling back to local check")

        # Fallback to local similarity check
        return self._check_locally(literature)

    def _check_with_external_api(self, literature):
        """Check using external plagiarism API."""
        import requests

        with literature.file.open('rb') as f:
            files = {'file': (literature.file.name, f, 'application/pdf')}
            headers = {'Authorization': f'Bearer {self.api_key}'}

            response = requests.post(
                self.api_url,
                files=files,
                headers=headers,
                timeout=60
            )

        if response.status_code == 200:
            data = response.json()
            return {
                'similarity': data.get('similarity', 0),
                'is_duplicate': data.get('similarity', 0) >= self.threshold,
                'sources': data.get('sources', []),
                'provider': 'external_api'
            }
        else:
            raise Exception(f"API returned {response.status_code}: {response.text}")

    def _check_locally(self, literature):
        """
        Check similarity against local database.
        Uses text extraction and similarity comparison.
        """
        # Extract text from PDF
        text = self._extract_text(literature.file.path)

        if not text:
            # If text extraction fails, use metadata comparison
            return self._check_by_metadata(literature)

        # Get all other literature texts
        other_literatures = Literature.objects.filter(
            is_active=True
        ).exclude(id=literature.id)

        sources = []
        max_similarity = 0

        for other in other_literatures:
            try:
                other_text = self._extract_text(other.file.path)
                if other_text:
                    similarity = self._calculate_similarity(text, other_text)
                    if similarity > 0.3:  # Only record significant matches
                        sources.append({
                            'title': other.title,
                            'authors': other.authors,
                            'similarity': similarity,
                            'matched_literature_id': str(other.id),
                            'url': ''
                        })
                        max_similarity = max(max_similarity, similarity)
            except Exception as e:
                logger.debug(f"Error comparing with {other.id}: {e}")

        # Sort by similarity
        sources.sort(key=lambda x: x['similarity'], reverse=True)

        return {
            'similarity': max_similarity,
            'is_duplicate': max_similarity >= self.threshold,
            'sources': sources[:10],  # Top 10 matches
            'provider': 'local'
        }

    def _check_by_metadata(self, literature):
        """Check similarity based on metadata (title, authors, DOI)."""
        sources = []
        max_similarity = 0

        # Check for exact DOI match
        if literature.doi:
            matches = Literature.objects.filter(
                is_active=True,
                doi=literature.doi
            ).exclude(id=literature.id)

            for match in matches:
                sources.append({
                    'title': match.title,
                    'authors': match.authors,
                    'similarity': 1.0,
                    'matched_literature_id': str(match.id),
                    'url': f'https://doi.org/{match.doi}'
                })
                max_similarity = 1.0

        # Check title similarity
        if literature.title and max_similarity < 1.0:
            other_literatures = Literature.objects.filter(
                is_active=True
            ).exclude(id=literature.id)

            for other in other_literatures:
                title_sim = self._string_similarity(
                    literature.title.lower(),
                    other.title.lower()
                )
                if title_sim > 0.8:
                    sources.append({
                        'title': other.title,
                        'authors': other.authors,
                        'similarity': title_sim,
                        'matched_literature_id': str(other.id),
                        'url': ''
                    })
                    max_similarity = max(max_similarity, title_sim)

        sources.sort(key=lambda x: x['similarity'], reverse=True)

        return {
            'similarity': max_similarity,
            'is_duplicate': max_similarity >= self.threshold,
            'sources': sources[:5],
            'provider': 'metadata'
        }

    def _extract_text(self, pdf_path):
        """Extract text content from PDF file."""
        try:
            import pdfplumber

            text_parts = []
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages[:20]:  # First 20 pages
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)

            return ' '.join(text_parts)
        except Exception as e:
            logger.error(f"Error extracting text from {pdf_path}: {e}")
            return ''

    def _calculate_similarity(self, text1, text2):
        """Calculate text similarity using TF-IDF and cosine similarity."""
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity

            # Limit text length for performance
            text1 = text1[:10000]
            text2 = text2[:10000]

            vectorizer = TfidfVectorizer(
                max_features=1000,
                stop_words='english'
            )

            tfidf_matrix = vectorizer.fit_transform([text1, text2])
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]

            return float(similarity)
        except Exception as e:
            logger.error(f"Error calculating similarity: {e}")
            return 0.0

    def _string_similarity(self, str1, str2):
        """Calculate string similarity using Levenshtein distance."""
        try:
            import difflib
            return difflib.SequenceMatcher(None, str1, str2).ratio()
        except Exception:
            return 0.0


def calculate_file_hash(file_path):
    """Calculate MD5 hash of a file."""
    md5 = hashlib.md5()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            md5.update(chunk)
    return md5.hexdigest()
