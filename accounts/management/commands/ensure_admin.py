from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Ensures admin superuser exists with correct flags'

    def handle(self, *args, **options):
        superuser_email = 'josuekabalisa@gmail.com'
        superuser_password = 'Uwamahor12345@@'

        # Try to get existing superuser
        user = User.objects.filter(email=superuser_email).first()

        if user:
            # Update existing user flags
            updated = False
            if not user.is_active:
                user.is_active = True
                updated = True
            if not user.is_admin:
                user.is_admin = True
                updated = True
            if not user.is_staff:
                user.is_staff = True
                updated = True
            if not user.is_superuser:
                user.is_superuser = True
                updated = True

            if updated:
                user.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Updated existing superuser: {superuser_email}'
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Superuser already has correct flags: {superuser_email}'
                    )
                )
        else:
            # Create new superuser
            try:
                user = User.objects.create_superuser(
                    email=superuser_email,
                    password=superuser_password,
                    first_name='Admin',
                    last_name='User'
                )
                # Explicitly set is_admin flag
                user.is_admin = True
                user.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Created new superuser: {superuser_email}'
                    )
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error creating superuser: {str(e)}')
                )

        # Final verification
        final_user = User.objects.filter(email=superuser_email).first()
        if final_user:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Final verification for {superuser_email}:'
                )
            )
            self.stdout.write(f'  - is_active: {final_user.is_active}')
            self.stdout.write(f'  - is_admin: {final_user.is_admin}')
            self.stdout.write(f'  - is_staff: {final_user.is_staff}')
            self.stdout.write(f'  - is_superuser: {final_user.is_superuser}')
            self.stdout.write(f'  - password_valid: {final_user.check_password(superuser_password)}')
