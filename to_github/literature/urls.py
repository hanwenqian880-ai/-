"""
URL configuration for literature management system.
"""
from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('profile/', views.user_profile, name='user_profile'),

    # Dashboard
    path('', views.dashboard, name='dashboard'),
    path('dashboard/', views.dashboard, name='dashboard'),

    # Literature
    path('literature/', views.literature_list, name='literature_list'),
    path('literature/upload/', views.literature_upload, name='literature_upload'),
    path('literature/<uuid:pk>/', views.literature_detail, name='literature_detail'),
    path('literature/<uuid:pk>/edit/', views.literature_edit, name='literature_edit'),
    path('literature/<uuid:pk>/delete/', views.literature_delete, name='literature_delete'),
    path('literature/batch-delete/', views.literature_batch_delete, name='literature_batch_delete'),
    path('literature/batch-update/', views.literature_batch_update, name='literature_batch_update'),
    path('literature/<uuid:pk>/download/', views.literature_download, name='literature_download'),

    # Plagiarism check
    path('literature/<uuid:pk>/check/', views.plagiarism_check, name='plagiarism_check'),
    path('plagiarism/<uuid:pk>/', views.plagiarism_result, name='plagiarism_result'),

    # Export
    path('export/', views.export_excel, name='export_excel'),

    # Admin - Users
    path('admin/users/', views.user_list, name='user_list'),
    path('admin/users/create/', views.user_create, name='user_create'),
    path('admin/users/<int:pk>/edit/', views.user_edit, name='user_edit'),
    path('admin/users/<int:pk>/delete/', views.user_delete, name='user_delete'),

    # Admin - Logs
    path('admin/logs/', views.operation_logs, name='operation_logs'),

    # Admin - Settings
    path('admin/settings/', views.system_settings, name='system_settings'),
]