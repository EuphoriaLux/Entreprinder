from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from entreprinder.models import EntrepreneurProfile
import random

class Command(BaseCommand):
    help = 'Creates test profiles for the Entreprinder application'

    def add_arguments(self, parser):
        parser.add_argument('total', type=int, help='Indicates the number of profiles to be created')

    def handle(self, *args, **kwargs):
        total = kwargs['total']
        industries = ['Technology', 'Finance', 'Healthcare', 'Education', 'Retail']
        locations = ['New York', 'San Francisco', 'London', 'Tokyo', 'Berlin']

        for i in range(total):
            username = f'testuser{i}'
            email = f'testuser{i}@example.com'
            password = 'testpassword123'
            user = User.objects.create_user(username=username, email=email, password=password)
            
            profile = EntrepreneurProfile.objects.create(
                user=user,
                bio=f'This is a test bio for {username}',
                company=f'Test Company {i}',
                industry=random.choice(industries),
                looking_for='Test collaborations and partnerships',
                location=random.choice(locations)
            )
            
            self.stdout.write(self.style.SUCCESS(f'Successfully created profile for {username}'))

        self.stdout.write(self.style.SUCCESS(f'Successfully created {total} test profiles'))