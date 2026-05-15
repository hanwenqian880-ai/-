"""
Views for literature management system.
"""
import os
import json
import hashlib
import logging
from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse, Http404, HttpResponseForbidden
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.conf import settings
from django.utils import timezone
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage

from .models import (
    User, Literature, PlagiarismCheck, DuplicateSource,
    OperationLog, SystemSettings
)
from .forms import (
    CustomAuthenticationForm, UserRegistrationForm, UserUpdateForm,
    LiteratureForm, LiteratureUpdateForm, LiteratureSearchForm,
    BatchUpdateForm, SettingsForm
)
from .services import PlagiarismChecker

logger = logging.getLogger('literature')


# ==================== Helper Functions ====================

def get_client_ip(request):
    """Get client IP address."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def log_operation(request, action, target='', target_id='', details=None):
    """Log user operation."""
    OperationLog.objects.create(
        user=request.user if request.user.is_authenticated else None,
        action=action,
        target=target,
        target_id=target_id,
        details=details or {},
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
    )


def admin_required(view_func):
    """Decorator to check if user is admin."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not request.user.is_admin():
            return HttpResponseForbidden('需要管理员权限')
        return view_func(request, *args, **kwargs)
    return wrapper


# ==================== Authentication Views ====================

def user_login(request):
    """User login view."""
    if request.user.is_authenticated:
        return redirect('literature_list')

    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            log_operation(request, OperationLog.Action.LOGIN, str(user))
            messages.success(request, f'欢迎回来，{user.get_full_name() or user.username}！')
            next_url = request.GET.get('next', 'literature_list')
            return redirect(next_url)
        else:
            messages.error(request, '用户名或密码错误')
    else:
        form = CustomAuthenticationForm()

    return render(request, 'literature/login.html', {'form': form})


def user_logout(request):
    """User logout view."""
    log_operation(request, OperationLog.Action.LOGOUT, str(request.user))
    logout(request)
    messages.info(request, '已成功退出登录')
    return redirect('login')


@login_required
def user_profile(request):
    """User profile view."""
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, '个人信息已更新')
            return redirect('user_profile')
    else:
        form = UserUpdateForm(instance=request.user)

    return render(request, 'literature/profile.html', {'form': form})


# ==================== Literature Views ====================

@login_required
def literature_list(request):
    """List all literature with search and filter."""
    literatures = Literature.objects.filter(is_active=True).select_related('uploader')

    # Search and filter
    form = LiteratureSearchForm(request.GET)
    if form.is_valid():
        search = form.cleaned_data.get('search')
        if search:
            literatures = literatures.filter(
                Q(title__icontains=search) |
                Q(authors__icontains=search) |
                Q(keywords__icontains=search) |
                Q(abstract__icontains=search)
            )

        title = form.cleaned_data.get('title')
        if title:
            literatures = literatures.filter(title__icontains=title)

        authors = form.cleaned_data.get('authors')
        if authors:
            literatures = literatures.filter(authors__icontains=authors)

        presenter = form.cleaned_data.get('presenter')
        if presenter:
            literatures = literatures.filter(presenter__icontains=presenter)

        year_from = form.cleaned_data.get('year_from')
        year_to = form.cleaned_data.get('year_to')
        if year_from:
            literatures = literatures.filter(year__gte=year_from)
        if year_to:
            literatures = literatures.filter(year__lte=year_to)

        date_from = form.cleaned_data.get('date_from')
        date_to = form.cleaned_data.get('date_to')
        if date_from:
            literatures = literatures.filter(created_at__date__gte=date_from)
        if date_to:
            literatures = literatures.filter(created_at__date__lte=date_to)

        uploader = form.cleaned_data.get('uploader')
        if uploader:
            literatures = literatures.filter(uploader_id=uploader)

    # Pagination
    paginator = Paginator(literatures, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Get uploaders for filter
    uploaders = User.objects.filter(
        id__in=literatures.values_list('uploader_id', flat=True)
    ).distinct()

    context = {
        'page_obj': page_obj,
        'form': form,
        'uploaders': uploaders,
        'total_count': literatures.count(),
    }
    return render(request, 'literature/literature_list.html', context)


@login_required
def literature_detail(request, pk):
    """View literature details."""
    literature = get_object_or_404(Literature, pk=pk, is_active=True)

    # Get plagiarism checks
    checks = literature.plagiarism_checks.all()[:5]

    context = {
        'literature': literature,
        'checks': checks,
        'can_modify': request.user.can_modify_literature(literature),
    }
    return render(request, 'literature/literature_detail.html', context)


@login_required
def literature_upload(request):
    """Upload new literature."""
    if request.method == 'POST':
        form = LiteratureForm(request.POST, request.FILES)
        if form.is_valid():
            literature = form.save(commit=False)
            literature.uploader = request.user

            # Calculate file hash
            uploaded_file = request.FILES.get('file')
            if uploaded_file:
                literature.file_size = uploaded_file.size
                # Calculate MD5 hash
                md5 = hashlib.md5()
                for chunk in uploaded_file.chunks():
                    md5.update(chunk)
                literature.file_hash = md5.hexdigest()

            literature.save()

            log_operation(
                request,
                OperationLog.Action.UPLOAD,
                literature.title,
                str(literature.id),
                {'file_size': literature.file_size}
            )

            messages.success(request, f'文献《{literature.title}》上传成功！')

            # Auto plagiarism check
            if request.POST.get('auto_check') == 'on':
                return redirect('plagiarism_check', pk=literature.id)

            return redirect('literature_detail', pk=literature.id)
    else:
        form = LiteratureForm()

    return render(request, 'literature/literature_upload.html', {'form': form})


@login_required
def literature_edit(request, pk):
    """Edit literature."""
    literature = get_object_or_404(Literature, pk=pk, is_active=True)

    # Permission check
    if not request.user.can_modify_literature(literature):
        return HttpResponseForbidden('您没有权限修改此文献')

    if request.method == 'POST':
        form = LiteratureUpdateForm(request.POST, instance=literature)
        if form.is_valid():
            form.save()
            log_operation(
                request,
                OperationLog.Action.UPDATE,
                literature.title,
                str(literature.id)
            )
            messages.success(request, '文献信息已更新')
            return redirect('literature_detail', pk=literature.id)
    else:
        form = LiteratureUpdateForm(instance=literature)

    return render(request, 'literature/literature_edit.html', {
        'form': form,
        'literature': literature
    })


@login_required
@require_POST
def literature_delete(request, pk):
    """Delete literature (soft delete)."""
    literature = get_object_or_404(Literature, pk=pk, is_active=True)

    # Permission check
    if not request.user.can_modify_literature(literature):
        return JsonResponse({'success': False, 'message': '您没有权限删除此文献'}, status=403)

    literature.is_active = False
    literature.save()

    log_operation(
        request,
        OperationLog.Action.DELETE,
        literature.title,
        str(literature.id)
    )

    return JsonResponse({'success': True, 'message': '文献已删除'})


@login_required
@require_POST
def literature_batch_delete(request):
    """Batch delete literature."""
    ids = request.POST.getlist('ids[]')
    if not ids:
        return JsonResponse({'success': False, 'message': '未选择任何文献'})

    literatures = Literature.objects.filter(id__in=ids, is_active=True)

    # Permission check
    for lit in literatures:
        if not request.user.can_modify_literature(lit):
            return JsonResponse({
                'success': False,
                'message': f'您没有权限删除《{lit.title}》'
            }, status=403)

    count = literatures.update(is_active=False)

    log_operation(
        request,
        OperationLog.Action.DELETE,
        f'批量删除{count}篇文献',
        ','.join(ids)
    )

    return JsonResponse({'success': True, 'message': f'已删除{count}篇文献'})


@login_required
@require_POST
def literature_batch_update(request):
    """Batch update literature."""
    form = BatchUpdateForm(request.POST)
    if not form.is_valid():
        return JsonResponse({'success': False, 'message': '表单数据无效'})

    ids = form.cleaned_data['literature_ids'].split(',')
    literatures = Literature.objects.filter(id__in=ids, is_active=True)

    # Permission check
    for lit in literatures:
        if not request.user.can_modify_literature(lit):
            return JsonResponse({
                'success': False,
                'message': f'您没有权限修改《{lit.title}》'
            }, status=403)

    update_data = {}
    if form.cleaned_data.get('presenter'):
        update_data['presenter'] = form.cleaned_data['presenter']
    if form.cleaned_data.get('meeting_date'):
        update_data['meeting_date'] = form.cleaned_data['meeting_date']
    if form.cleaned_data.get('notes'):
        update_data['notes'] = form.cleaned_data['notes']

    if update_data:
        count = literatures.update(**update_data)
        log_operation(
            request,
            OperationLog.Action.UPDATE,
            f'批量更新{count}篇文献',
            ','.join(ids),
            update_data
        )
        return JsonResponse({'success': True, 'message': f'已更新{count}篇文献'})

    return JsonResponse({'success': False, 'message': '未提供更新数据'})


@login_required
def literature_download(request, pk):
    """Download literature PDF."""
    literature = get_object_or_404(Literature, pk=pk, is_active=True)

    if not literature.file:
        raise Http404('文件不存在')

    log_operation(
        request,
        OperationLog.Action.DOWNLOAD,
        literature.title,
        str(literature.id)
    )

    response = HttpResponse(
        literature.file.open('rb').read(),
        content_type='application/pdf'
    )
    response['Content-Disposition'] = f'attachment; filename="{literature.title}.pdf"'
    return response


# ==================== Plagiarism Check Views ====================

@login_required
def plagiarism_check(request, pk):
    """Run plagiarism check on literature."""
    literature = get_object_or_404(Literature, pk=pk, is_active=True)

    # Create check record
    check = PlagiarismCheck.objects.create(
        literature=literature,
        status=PlagiarismCheck.Status.PROCESSING
    )

    try:
        checker = PlagiarismChecker()
        result = checker.check(literature)

        check.status = PlagiarismCheck.Status.COMPLETED
        check.similarity_score = result['similarity']
        check.is_duplicate = result['is_duplicate']
        check.result_data = result
        check.completed_at = timezone.now()
        check.save()

        # Save duplicate sources
        for source in result.get('sources', []):
            DuplicateSource.objects.create(
                plagiarism_check=check,
                source_title=source.get('title', ''),
                source_authors=source.get('authors', ''),
                source_url=source.get('url', ''),
                similarity=source.get('similarity', 0),
                matched_content=source.get('matched_content', ''),
                matched_literature_id=source.get('matched_literature_id')
            )

        log_operation(
            request,
            OperationLog.Action.CHECK,
            literature.title,
            str(literature.id),
            {'similarity': result['similarity']}
        )

        messages.success(request, f'查重完成，相似度：{result["similarity"]:.1%}')

    except Exception as e:
        check.status = PlagiarismCheck.Status.FAILED
        check.error_message = str(e)
        check.save()
        messages.error(request, f'查重失败：{str(e)}')

    return redirect('literature_detail', pk=literature.id)


@login_required
def plagiarism_result(request, pk):
    """View plagiarism check result."""
    check = get_object_or_404(PlagiarismCheck, pk=pk)

    context = {
        'check': check,
        'sources': check.duplicate_sources.all(),
    }
    return render(request, 'literature/plagiarism_result.html', context)


# ==================== Export Views ====================

@login_required
def export_excel(request):
    """Export literature list to Excel."""
    import pandas as pd
    from io import BytesIO

    literatures = Literature.objects.filter(is_active=True).select_related('uploader')

    # Apply filters
    form = LiteratureSearchForm(request.GET)
    if form.is_valid():
        # Apply same filters as literature_list
        pass

    data = []
    for lit in literatures:
        data.append({
            '标题': lit.title,
            '作者': lit.authors,
            '期刊/会议': lit.journal,
            '年份': lit.year,
            'DOI': lit.doi,
            '关键词': lit.keywords,
            '分享人': lit.presenter,
            '组会日期': lit.meeting_date,
            '上传者': lit.uploader.get_full_name() or lit.uploader.username,
            '上传时间': lit.created_at.strftime('%Y-%m-%d %H:%M'),
            '备注': lit.notes,
        })

    df = pd.DataFrame(data)

    # Create Excel file
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='文献列表')

    output.seek(0)

    log_operation(request, 'export', f'导出{len(data)}篇文献')

    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="literature_list_{timezone.now().strftime("%Y%m%d")}.xlsx"'
    return response


# ==================== Admin Views ====================

@admin_required
def user_list(request):
    """List all users (admin only)."""
    users = User.objects.all().order_by('-created_at')

    # Search
    search = request.GET.get('search', '')
    if search:
        users = users.filter(
            Q(username__icontains=search) |
            Q(email__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)
        )

    paginator = Paginator(users, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'literature/user_list.html', {
        'page_obj': page_obj,
        'search': search
    })


@admin_required
def user_create(request):
    """Create new user (admin only)."""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = request.POST.get('role', User.Role.MEMBER)
            user.save()
            log_operation(
                request,
                OperationLog.Action.USER_CREATE,
                str(user),
                str(user.id)
            )
            messages.success(request, f'用户 {user.username} 创建成功')
            return redirect('user_list')
    else:
        form = UserRegistrationForm()

    return render(request, 'literature/user_form.html', {'form': form, 'title': '创建用户'})


@admin_required
def user_edit(request, pk):
    """Edit user (admin only)."""
    user = get_object_or_404(User, pk=pk)

    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            log_operation(
                request,
                OperationLog.Action.USER_UPDATE,
                str(user),
                str(user.id)
            )
            messages.success(request, '用户信息已更新')
            return redirect('user_list')
    else:
        form = UserUpdateForm(instance=user)

    return render(request, 'literature/user_form.html', {
        'form': form,
        'user_obj': user,
        'title': '编辑用户'
    })


@admin_required
@require_POST
def user_delete(request, pk):
    """Delete user (admin only)."""
    user = get_object_or_404(User, pk=pk)

    if user == request.user:
        return JsonResponse({'success': False, 'message': '不能删除自己'}, status=400)

    username = str(user)
    user.delete()

    log_operation(request, OperationLog.Action.USER_DELETE, username, str(pk))

    return JsonResponse({'success': True, 'message': '用户已删除'})


@admin_required
def operation_logs(request):
    """View operation logs (admin only)."""
    logs = OperationLog.objects.all().select_related('user')

    # Filter by action
    action = request.GET.get('action', '')
    if action:
        logs = logs.filter(action=action)

    # Filter by user
    user_id = request.GET.get('user', '')
    if user_id:
        logs = logs.filter(user_id=user_id)

    # Date range
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    if date_from:
        logs = logs.filter(created_at__date__gte=date_from)
    if date_to:
        logs = logs.filter(created_at__date__lte=date_to)

    paginator = Paginator(logs, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    users = User.objects.all()

    return render(request, 'literature/operation_logs.html', {
        'page_obj': page_obj,
        'users': users,
        'action': action,
        'user_id': user_id,
        'date_from': date_from,
        'date_to': date_to,
    })


@admin_required
def system_settings(request):
    """System settings (admin only)."""
    if request.method == 'POST':
        form = SettingsForm(request.POST)
        if form.is_valid():
            SystemSettings.set_setting(
                'similarity_threshold',
                str(form.cleaned_data['similarity_threshold']),
                request.user,
                '查重相似度阈值'
            )
            SystemSettings.set_setting(
                'max_file_size',
                str(form.cleaned_data['max_file_size']),
                request.user,
                '最大文件大小(MB)'
            )
            log_operation(request, OperationLog.Action.SETTINGS_CHANGE, '系统设置')
            messages.success(request, '设置已保存')
    else:
        threshold = float(SystemSettings.get_setting('similarity_threshold', '0.7'))
        max_size = int(SystemSettings.get_setting('max_file_size', '50'))
        form = SettingsForm(initial={
            'similarity_threshold': threshold,
            'max_file_size': max_size
        })

    return render(request, 'literature/settings.html', {'form': form})


# ==================== Dashboard ====================

@login_required
def dashboard(request):
    """Dashboard view."""
    total_literatures = Literature.objects.filter(is_active=True).count()
    total_users = User.objects.count()
    total_checks = PlagiarismCheck.objects.filter(
        status=PlagiarismCheck.Status.COMPLETED
    ).count()
    duplicates = PlagiarismCheck.objects.filter(
        status=PlagiarismCheck.Status.COMPLETED,
        is_duplicate=True
    ).count()

    recent_literatures = Literature.objects.filter(
        is_active=True
    ).order_by('-created_at')[:5]

    recent_logs = OperationLog.objects.all().order_by('-created_at')[:10]

    context = {
        'total_literatures': total_literatures,
        'total_users': total_users,
        'total_checks': total_checks,
        'duplicates': duplicates,
        'recent_literatures': recent_literatures,
        'recent_logs': recent_logs,
    }
    return render(request, 'literature/dashboard.html', context)
