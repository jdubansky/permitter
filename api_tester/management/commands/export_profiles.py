import yaml
from django.core.management.base import BaseCommand
from api_tester.models import Profile

class Command(BaseCommand):
    help = 'Export profiles to a YAML file'

    def add_arguments(self, parser):
        parser.add_argument('output_file', type=str, help='Path to output YAML file')
        parser.add_argument('--profile-ids', type=int, nargs='+', help='Specific profile IDs to export')

    def handle(self, *args, **options):
        output_file = options['output_file']
        profile_ids = options['profile_ids']

        # Get profiles
        if profile_ids:
            profiles = Profile.objects.filter(id__in=profile_ids)
        else:
            profiles = Profile.objects.all()

        # Convert profiles to dictionary
        profiles_data = []
        for profile in profiles:
            profile_data = {
                'name': profile.name,
                'cookies': profile.cookies,
                'common_params': profile.common_params,
                'created_at': profile.created_at.isoformat(),
                'updated_at': profile.updated_at.isoformat()
            }
            profiles_data.append(profile_data)

        # Write to YAML file
        with open(output_file, 'w') as f:
            yaml.dump(profiles_data, f, default_flow_style=False)

        self.stdout.write(self.style.SUCCESS(f'Successfully exported {len(profiles_data)} profiles to {output_file}')) 