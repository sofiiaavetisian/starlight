from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from satellites.models import TLE, Favorite
from satellites.services.tle_fetcher import get_or_refresh_tle

class Command(BaseCommand):
    help = "Refresh TLEs for favorites if older than 48 hours."

    def handle(self, *args, **options):
        self.stdout.write("Refreshing TLEs for favorites (max age 48h)...")
        count = 0
        for fav in Favorite.objects.all():
            get_or_refresh_tle(fav.norad_id, max_age_hours=48)
            count += 1
        self.stdout.write(self.style.SUCCESS(f"Refreshed/checked {count} favorites."))
