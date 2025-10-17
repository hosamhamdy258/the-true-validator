from django.core.cache import cache
from django.core.management.base import BaseCommand

from validatorApi.constants import get_validation_cache_key


class Command(BaseCommand):
    help = "Clear the national ID validation cache"

    def add_arguments(self, parser):
        parser.add_argument("--national-id", type=str, help="Clear cache for specific national ID only")

    def handle(self, *args, **options):
        national_id = options.get("national_id")

        if national_id:
            # Clear specific national ID
            cache_key = get_validation_cache_key(national_id)
            result = cache.delete(cache_key)

            if result:
                self.stdout.write(self.style.SUCCESS(f"Successfully cleared cache for national ID: {national_id}"))
            else:
                self.stdout.write(self.style.WARNING(f"No cache found for national ID: {national_id}"))
        else:
            # Clear all cache
            cache.clear()
            self.stdout.write(self.style.SUCCESS("Successfully cleared all validation cache"))
