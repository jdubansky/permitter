import yaml
from django.core.management.base import BaseCommand
from api_tester.models import Profile
from django.utils import timezone

class Command(BaseCommand):
    help = 'Import profiles from a YAML file'

    def add_arguments(self, parser):
        parser.add_argument('input_file', type=str, help='Path to input YAML file')
        parser.add_argument('--overwrite', action='store_true', help='Overwrite existing profiles with same name')

    def handle(self, *args, **options):
        input_file = options['input_file']
        overwrite = options['overwrite']

        # Read YAML file
        with open(input_file, 'r') as f:
            profiles_data = yaml.safe_load(f)

        imported_count = 0
        skipped_count = 0

        for profile_data in profiles_data:
            name = profile_data['name']
            
            # Check if profile exists
            existing_profile = Profile.objects.filter(name=name).first()
            
            if existing_profile and not overwrite:
                self.stdout.write(self.style.WARNING(f'Skipping profile "{name}" - already exists'))
                skipped_count += 1
                continue

            # Create or update profile
            profile, created = Profile.objects.update_or_create(
                name=name,
                defaults={
                    'cookies': profile_data['cookies'],
                    'common_params': profile_data['common_params'],
                    'updated_at': timezone.now()
                }
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f'Created profile "{name}"'))
            else:
                self.stdout.write(self.style.SUCCESS(f'Updated profile "{name}"'))
            
            imported_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'Successfully imported {imported_count} profiles, skipped {skipped_count} profiles'
        )) 