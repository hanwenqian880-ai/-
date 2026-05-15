"""
Admin configuration for literature management system.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import User, Literature, PlagiarismCheck, DuplicateSource, OperationLog, SystemSettings


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'role', 'is_active', 'created_at']
    list_filter = ['role', 'is_active', 'created_at']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering = ['-created_at']

    fieldsets = (
        ('基本信息', {
            'fields': ('username', 'email', 'first_name', 'last_name')
        }),
        ('权限信息', {
            'fields': ('role', 'is_active', 'is_staff', 'is_superuser')
        }),
        ('联系方式', {
            'fields': ('phone', 'department')
        }),
        ('时间信息', {
            'fields': ('last_login', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['created_at', 'updated_at', 'last_login']


@admin.register(Literature)
class LiteratureAdmin(admin.ModelAdmin):
    list_display = ['title', 'authors', 'year', 'uploader', 'created_at', 'is_active']
    list_filter = ['year', 'is_active', 'created_at']
    search_fields = ['title', 'authors', 'keywords', 'doi']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'

    fieldsets = (
        ('文献信息', {
            'fields': ('title', 'authors', 'journal', 'year', 'doi', 'keywords', 'abstract')
        }),
        ('文件信息', {
            'fields': ('file', 'file_size', 'file_hash')
        }),
        ('组会信息', {
            'fields': ('presenter', 'meeting_date', 'notes')
        }),
        ('元数据', {
            'fields': ('uploader', 'is_active', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['file_size', 'file_hash', 'created_at', 'updated_at']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('uploader')


@admin.register(PlagiarismCheck)
class PlagiarismCheckAdmin(admin.ModelAdmin):
    list_display = ['literature', 'status', 'similarity_score', 'is_duplicate', 'created_at']
    list_filter = ['status', 'is_duplicate', 'created_at']
    search_fields = ['literature__title']
    ordering = ['-created_at']

    fieldsets = (
        ('检测信息', {
            'fields': ('literature', 'status', 'similarity_score', 'is_duplicate')
        }),
        ('API信息', {
            'fields': ('external_id', 'api_provider'),
            'classes': ('collapse',)
        }),
        ('结果详情', {
            'fields': ('result_data', 'error_message'),
            'classes': ('collapse',)
        }),
        ('时间信息', {
            'fields': ('created_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['created_at', 'completed_at']


@admin.register(DuplicateSource)
class DuplicateSourceAdmin(admin.ModelAdmin):
    list_display = ['source_title', 'plagiarism_check', 'similarity', 'matched_literature']
    list_filter = ['similarity']
    search_fields = ['source_title', 'source_authors']


@admin.register(OperationLog)
class OperationLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'target', 'ip_address', 'created_at']
    list_filter = ['action', 'created_at']
    search_fields = ['user__username', 'target']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'

    readonly_fields = ['user', 'action', 'target', 'target_id', 'details',
                       'ip_address', 'user_agent', 'created_at']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    list_display = ['key', 'value', 'updated_at', 'updated_by']
    search_fields = ['key']
    ordering = ['key']
