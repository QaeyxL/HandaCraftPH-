from django.core.management.base import BaseCommand
from hc_app.models import UserProfile
import requests
import time
from django.utils import timezone


class Command(BaseCommand):
    help = 'Geocode UserProfile addresses (backfill latitude/longitude) using Nominatim (OpenStreetMap)'

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=200, help='Max profiles to geocode in one run')
        parser.add_argument('--delay', type=float, default=1.0, help='Seconds to wait between requests (politeness)')

    def handle(self, *args, **options):
        limit = options.get('limit')
        delay = options.get('delay')
        qs = UserProfile.objects.filter(latitude__isnull=True).all()[:limit]
        total = qs.count()
        if total == 0:
            self.stdout.write(self.style.SUCCESS('No profiles needing geocoding.'))
            return

        self.stdout.write(f'Geocoding up to {limit} profiles (found {total}) with {delay}s delay...')
        headers = {'User-Agent': 'HandacraftPH-Geocoder/1.0 (+https://example.com)'}
        for idx, profile in enumerate(qs, start=1):
            query_parts = [profile.street, profile.city, profile.state, profile.country]
            query = ', '.join([p for p in query_parts if p])
            if not query:
                self.stdout.write(f'[{idx}/{total}] Skipping profile {profile.user_id}: empty address')
                continue
            params = {'q': query, 'format': 'json', 'limit': 1}
            try:
                r = requests.get('https://nominatim.openstreetmap.org/search', params=params, headers=headers, timeout=8)
                r.raise_for_status()
                data = r.json()
                if data:
                    lat = data[0].get('lat')
                    lon = data[0].get('lon')
                    if lat and lon:
                        profile.latitude = float(lat)
                        profile.longitude = float(lon)
                        profile.geocoded_at = timezone.now()
                        profile.save(update_fields=['latitude', 'longitude', 'geocoded_at'])
                        self.stdout.write(self.style.SUCCESS(f'[{idx}/{total}] Geocoded {profile.user.username} -> {lat},{lon}'))
                    else:
                        self.stdout.write(self.style.WARNING(f'[{idx}/{total}] No lat/lon for {profile.user.username}'))
                else:
                    self.stdout.write(self.style.WARNING(f'[{idx}/{total}] No results for {profile.user.username} ({query})'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'[{idx}/{total}] Error geocoding {profile.user.username}: {e}'))
            time.sleep(delay)

        self.stdout.write(self.style.SUCCESS('Geocoding run complete.'))
