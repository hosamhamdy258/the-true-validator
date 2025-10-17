from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken


class Command(BaseCommand):
    help = "Revoke all JWT tokens for a specific user"

    def add_arguments(self, parser):
        parser.add_argument("username", type=str, help="Username to revoke tokens for")

    def handle(self, *args, **options):
        username = options["username"]

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User "{username}" does not exist'))
            return

        # Get all outstanding tokens for the user
        tokens = OutstandingToken.objects.filter(user=user)
        count = 0

        for token in tokens:
            # Check if not already blacklisted
            _, created = BlacklistedToken.objects.get_or_create(token=token)
            if created:
                count += 1

        if count > 0:
            self.stdout.write(self.style.SUCCESS(f'Successfully revoked {count} token(s) for user "{username}"'))
        else:
            self.stdout.write(self.style.WARNING(f'No active tokens found for user "{username}"'))
