"""
Database models for literature management system.
"""
import os
import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.utils import timezone
from django.conf import settings


def literature_file_path(instance, filename):
    """Generate unique file path for uploaded literature."""
    ext = filename.split('.')[-1].lower()
    filename = f"{instance.id}_{timezone.now().strftime('%Y%m%d%H%M%S')}.{ext}"
    return os.path.join('literature', filename)


class User(AbstractUser):
    """Custom user model with role support."""

    class Role(models.TextChoices):
        ADMIN = 'admin', '管理员'
        MEMBER = 'member', '普通成员'

    groups = models.ManyToManyField(
        Group,
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='literature_user_set',
        related_query_name='literature_user',
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='literature_user_set',
        related_query_name='literature_user',
    )

    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.MEMBER,
        verbose_name='用户角色'
    )
    phone = models.CharField(max_length=20, blank=True, verbose_name='联系电话')
    department = models.CharField(max_length=100, blank=True, verbose_name='所属部门')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '用户'
        verbose_name_plural = '用户'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    def is_admin(self):
        """Check if user is admin."""
        return self.role == self.Role.ADMIN or self.is_superuser

    def can_modify_literature(self, literature):
        """Check if user can modify a literature."""
        return self.is_admin() or literature.uploader == self


class Literature(models.Model):
    """Literature model for PDF documents."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=500, verbose_name='文献标题')
    authors = models.CharField(max_length=500, blank=True, verbose_name='作者')
    journal = models.CharField(max_length=200, blank=True, verbose_name='期刊/会议')
    year = models.IntegerField(null=True, blank=True, verbose_name='发表年份')
    doi = models.CharField(max_length=100, blank=True, verbose_name='DOI')
    keywords = models.CharField(max_length=500, blank=True, verbose_name='关键词')
    abstract = models.TextField(blank=True, verbose_name='摘要')
    notes = models.TextField(blank=True, verbose_name='备注')

    # File information
    file = models.FileField(
        upload_to=literature_file_path,
        verbose_name='PDF文件',
        help_text='仅支持PDF格式，最大50MB'
    )
    file_size = models.BigIntegerField(default=0, verbose_name='文件大小(字节)')
    file_hash = models.CharField(max_length=64, blank=True, verbose_name='文件MD5哈希')

    # Metadata
    uploader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='literatures',
        verbose_name='上传者'
    )
    presenter = models.CharField(max_length=100, blank=True, verbose_name='分享人')
    meeting_date = models.DateField(null=True, blank=True, verbose_name='组会日期')

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='上传时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    # Status
    is_active = models.BooleanField(default=True, verbose_name='是否有效')

    class Meta:
        verbose_name = '文献'
        verbose_name_plural = '文献'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['authors']),
            models.Index(fields=['year']),
            models.Index(fields=['uploader']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return self.title

    def get_file_size_display(self):
        """Return human-readable file size."""
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    def delete(self, *args, **kwargs):
        """Delete file when literature is deleted."""
        if self.file:
            if os.path.isfile(self.file.path):
                os.remove(self.file.path)
        super().delete(*args, **kwargs)


class PlagiarismCheck(models.Model):
    """Plagiarism check record."""

    class Status(models.TextChoices):
        PENDING = 'pending', '待检测'
        PROCESSING = 'processing', '检测中'
        COMPLETED = 'completed', '已完成'
        FAILED = 'failed', '检测失败'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    literature = models.ForeignKey(
        Literature,
        on_delete=models.CASCADE,
        related_name='plagiarism_checks',
        verbose_name='文献'
    )

    # Check results
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name='检测状态'
    )
    similarity_score = models.FloatField(null=True, blank=True, verbose_name='相似度')
    is_duplicate = models.BooleanField(default=False, verbose_name='是否重复')

    # Detailed results
    result_data = models.JSONField(default=dict, blank=True, verbose_name='详细结果')
    error_message = models.TextField(blank=True, verbose_name='错误信息')

    # External API info
    external_id = models.CharField(max_length=100, blank=True, verbose_name='外部检测ID')
    api_provider = models.CharField(max_length=50, blank=True, verbose_name='API提供商')

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='检测时间')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='完成时间')

    class Meta:
        verbose_name = '查重记录'
        verbose_name_plural = '查重记录'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.literature.title} - {self.similarity_score or 'N/A'}%"


class DuplicateSource(models.Model):
    """Duplicate source from plagiarism check."""

    plagiarism_check = models.ForeignKey(
        PlagiarismCheck,
        on_delete=models.CASCADE,
        related_name='duplicate_sources',
        verbose_name='查重记录'
    )
    source_title = models.CharField(max_length=500, verbose_name='来源文献标题')
    source_authors = models.CharField(max_length=500, blank=True, verbose_name='来源作者')
    source_url = models.URLField(blank=True, verbose_name='来源链接')
    similarity = models.FloatField(verbose_name='相似度')
    matched_content = models.TextField(blank=True, verbose_name='匹配内容')

    # Reference to internal literature if matched
    matched_literature = models.ForeignKey(
        Literature,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='matched_as_duplicate',
        verbose_name='匹配的内部文献'
    )

    class Meta:
        verbose_name = '重复来源'
        verbose_name_plural = '重复来源'
        ordering = ['-similarity']


class OperationLog(models.Model):
    """Operation log for audit trail."""

    class Action(models.TextChoices):
        LOGIN = 'login', '登录'
        LOGOUT = 'logout', '登出'
        UPLOAD = 'upload', '上传文献'
        DOWNLOAD = 'download', '下载文献'
        UPDATE = 'update', '更新文献'
        DELETE = 'delete', '删除文献'
        CHECK = 'check', '查重'
        USER_CREATE = 'user_create', '创建用户'
        USER_UPDATE = 'user_update', '更新用户'
        USER_DELETE = 'user_delete', '删除用户'
        SETTINGS_CHANGE = 'settings_change', '修改设置'

    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='operation_logs',
        verbose_name='操作用户'
    )
    action = models.CharField(
        max_length=20,
        choices=Action.choices,
        verbose_name='操作类型'
    )
    target = models.CharField(max_length=500, blank=True, verbose_name='操作对象')
    target_id = models.CharField(max_length=100, blank=True, verbose_name='对象ID')
    details = models.JSONField(default=dict, blank=True, verbose_name='操作详情')
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name='IP地址')
    user_agent = models.CharField(max_length=500, blank=True, verbose_name='用户代理')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='操作时间')

    class Meta:
        verbose_name = '操作日志'
        verbose_name_plural = '操作日志'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['action']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        username = self.user.username if self.user else 'Anonymous'
        return f"{username} - {self.get_action_display()} - {self.created_at}"


class SystemSettings(models.Model):
    """System-wide settings."""

    key = models.CharField(max_length=100, unique=True, verbose_name='设置键')
    value = models.TextField(verbose_name='设置值')
    description = models.CharField(max_length=200, blank=True, verbose_name='描述')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='更新者'
    )

    class Meta:
        verbose_name = '系统设置'
        verbose_name_plural = '系统设置'

    def __str__(self):
        return self.key

    @classmethod
    def get_setting(cls, key, default=None):
        """Get setting value by key."""
        try:
            return cls.objects.get(key=key).value
        except cls.DoesNotExist:
            return default

    @classmethod
    def set_setting(cls, key, value, user=None, description=''):
        """Set setting value."""
        obj, created = cls.objects.update_or_create(
            key=key,
            defaults={
                'value': value,
                'updated_by': user,
                'description': description
            }
        )
        return obj
