"""
Management command to initialize the system.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from literature.models import SystemSettings

User = get_user_model()


class Command(BaseCommand):
    help = 'Initialize the literature management system with default data'

    def handle(self, *args, **options):
        self.stdout.write('Initializing system...')

        # Create default admin user
        if not User.objects.filter(username='admin').exists():
            admin = User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin123',
                first_name='系统',
                last_name='管理员',
                role=User.Role.ADMIN
            )
            self.stdout.write(self.style.SUCCESS(f'Created admin user: {admin.username}'))
        else:
            self.stdout.write('Admin user already exists')

        # Create default settings
        SystemSettings.set_setting('similarity_threshold', '0.7', None, '查重相似度阈值')
        SystemSettings.set_setting('max_file_size', '50', None, '最大文件大小(MB)')
        self.stdout.write(self.style.SUCCESS('Created default settings'))

        self.stdout.write(self.style.SUCCESS('System initialization completed!'))
        self.stdout.write('Default admin credentials: admin / admin123')
        self.stdout.write('Please change the admin password after first login!')