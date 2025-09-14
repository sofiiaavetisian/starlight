from django.core.management.base import BaseCommand
import httpx
from satellites.services.tle_fetcher import parse_tle_catalog, upsert_tles

CELESTRAK_ACTIVE = "https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=TLE"

class Command(BaseCommand):
    help = "Import/refresh the satellite catalog (TLE table) from CelesTrak 'active' group."

    def handle(self, *args, **options):
        self.stdout.write("Downloading active satellites catalog from CelesTrak...")
        with httpx.Client(timeout=30.0, follow_redirects=True) as client:
            r = client.get(CELESTRAK_ACTIVE)
            r.raise_for_status()
            text = r.text
        records = parse_tle_catalog(text)
        count = upsert_tles(records)
        self.stdout.write(self.style.SUCCESS(f"Upserted {count} TLE records."))
