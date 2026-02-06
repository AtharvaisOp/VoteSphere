"""
Script to create a superuser for admin access
Run this after migrations
"""
from django.contrib.auth import get_user_model
from django.core.management import execute_from_command_line

User = get_user_model()

# Check if superuser already exists
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser(
        username='admin',
        email='admin@votesphere.edu',
        password='admin123',  # Change this in production!
        first_name='Admin',
        last_name='User'
    )
    print("✅ Superuser created: username='admin', password='admin123'")
else:
    print("ℹ️  Superuser already exists")
