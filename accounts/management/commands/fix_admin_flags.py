from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Ensure josuekabalisa@gmail.com has all admin flags set'

    def handle(self, *args, **options):
        email = 'josuekabalisa@gmail.com'
        password = 'Uwamahor12345@@'
        
        # Get or create user
        user, created = User.objects.get_or_create(email=email)
        
        if created:
            user.set_password(password)
            self.stdout.write(f'Created user: {email}')
        else:
            self.stdout.write(f'User exists: {email}')
            # Update password
            user.set_password(password)
        
        # Set all required flags
        user.is_active = True
        user.is_admin = True
        user.is_staff = True
        user.is_superuser = True
        user.first_name = 'Admin'
        user.last_name = 'User'
        user.save()
        
        self.stdout.write(self.style.SUCCESS('✓ Admin flags set:'))
        self.stdout.write(f'  - is_active: {user.is_active}')
        self.stdout.write(f'  - is_admin: {user.is_admin}')
        self.stdout.write(f'  - is_staff: {user.is_staff}')
        self.stdout.write(f'  - is_superuser: {user.is_superuser}')
        self.stdout.write(f'  - password: Set to "Uwamahor12345@@"')
        self.stdout.write(self.style.SUCCESS(f'\n✓ Login at https://novaprofitt.onrender.com/admin/login/'))
        self.stdout.write(self.style.SUCCESS(f'  Email: {email}'))
        self.stdout.write(self.style.SUCCESS(f'  Password: Uwamahor12345@@'))
