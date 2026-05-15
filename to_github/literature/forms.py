"""
Form definitions for literature management system.
"""
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import User, Literature


class CustomAuthenticationForm(AuthenticationForm):
    """Custom login form with Bootstrap styling."""
    username = forms.CharField(
        label='用户名',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '请输入用户名',
            'autofocus': True
        })
    )
    password = forms.CharField(
        label='密码',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '请输入密码'
        })
    )


class UserRegistrationForm(UserCreationForm):
    """User registration form."""

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'phone', 'department']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs['class'] = 'form-control'
        self.fields['password2'].widget.attrs['class'] = 'form-control'


class UserUpdateForm(forms.ModelForm):
    """User update form for admins."""

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'phone', 'department', 'role', 'is_active']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class LiteratureForm(forms.ModelForm):
    """Form for creating and updating literature."""

    class Meta:
        model = Literature
        fields = [
            'title', 'authors', 'journal', 'year', 'doi', 'keywords',
            'abstract', 'notes', 'file', 'presenter', 'meeting_date'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '请输入文献标题'
            }),
            'authors': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '多个作者用逗号分隔'
            }),
            'journal': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '期刊或会议名称'
            }),
            'year': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1900,
                'max': timezone.now().year + 1
            }),
            'doi': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'DOI号'
            }),
            'keywords': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '多个关键词用逗号分隔'
            }),
            'abstract': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': '文献摘要'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '备注信息'
            }),
            'file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf'
            }),
            'presenter': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '组会分享人姓名'
            }),
            'meeting_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }

    def clean_file(self):
        """Validate uploaded file."""
        file = self.cleaned_data.get('file')
        if file:
            # Check file extension
            if not file.name.lower().endswith('.pdf'):
                raise ValidationError('只支持PDF格式的文件')

            # Check file size (50MB limit)
            max_size = 50 * 1024 * 1024  # 50MB
            if file.size > max_size:
                raise ValidationError(f'文件大小不能超过50MB，当前文件大小为 {file.size / (1024*1024):.1f}MB')

        return file


class LiteratureUpdateForm(forms.ModelForm):
    """Form for updating literature (without file)."""

    class Meta:
        model = Literature
        fields = [
            'title', 'authors', 'journal', 'year', 'doi', 'keywords',
            'abstract', 'notes', 'presenter', 'meeting_date'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'authors': forms.TextInput(attrs={'class': 'form-control'}),
            'journal': forms.TextInput(attrs={'class': 'form-control'}),
            'year': forms.NumberInput(attrs={'class': 'form-control'}),
            'doi': forms.TextInput(attrs={'class': 'form-control'}),
            'keywords': forms.TextInput(attrs={'class': 'form-control'}),
            'abstract': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'presenter': forms.TextInput(attrs={'class': 'form-control'}),
            'meeting_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class LiteratureSearchForm(forms.Form):
    """Form for searching literature."""

    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '搜索标题、作者、关键词...'
        })
    )
    title = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    authors = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    presenter = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    year_from = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    year_to = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    date_from = forms.DateField(required=False, widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))
    date_to = forms.DateField(required=False, widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))
    uploader = forms.IntegerField(required=False, widget=forms.Select(attrs={'class': 'form-select'}))


class BatchUpdateForm(forms.Form):
    """Form for batch updating literature."""

    literature_ids = forms.CharField(widget=forms.HiddenInput())
    presenter = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    meeting_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2})
    )


class SettingsForm(forms.Form):
    """Form for system settings."""

    similarity_threshold = forms.FloatField(
        label='查重相似度阈值',
        min_value=0,
        max_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01'
        }),
        help_text='相似度超过此阈值将被判定为重复（0-1之间）'
    )
    max_file_size = forms.IntegerField(
        label='最大文件大小(MB)',
        min_value=1,
        max_value=100,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        help_text='上传文件的最大大小限制'
    )
