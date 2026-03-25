from django.core.management.base import BaseCommand
from ai_engine.models import LightTiming


class Command(BaseCommand):
    help = 'Initialize light timings for all months with default values'

    def handle(self, *args, **options):
        """
        Initialize all 12 months with default light timing values.
        You can update these values in Django admin or modify them here.
        """
        default_timings = {
            1: {"sunrise": "07:15 AM", "sunset": "05:45 PM", "daylight_hours": 10.5},
            2: {"sunrise": "07:00 AM", "sunset": "06:15 PM", "daylight_hours": 11.25},
            3: {"sunrise": "06:45 AM", "sunset": "06:30 PM", "daylight_hours": 11.75},
            4: {"sunrise": "06:15 AM", "sunset": "06:45 PM", "daylight_hours": 12.5},
            5: {"sunrise": "06:00 AM", "sunset": "07:00 PM", "daylight_hours": 13.0},
            6: {"sunrise": "05:45 AM", "sunset": "07:15 PM", "daylight_hours": 13.5},
            7: {"sunrise": "05:50 AM", "sunset": "07:10 PM", "daylight_hours": 13.33},
            8: {"sunrise": "06:00 AM", "sunset": "07:00 PM", "daylight_hours": 13.0},
            9: {"sunrise": "06:15 AM", "sunset": "06:45 PM", "daylight_hours": 12.5},
            10: {"sunrise": "06:30 AM", "sunset": "06:15 PM", "daylight_hours": 11.75},
            11: {"sunrise": "06:45 AM", "sunset": "05:45 PM", "daylight_hours": 11.0},
            12: {"sunrise": "07:00 AM", "sunset": "05:30 PM", "daylight_hours": 10.5},
        }

        created_count = 0
        updated_count = 0

        for month, timing in default_timings.items():
            obj, created = LightTiming.objects.update_or_create(
                month=month,
                defaults={
                    'sunrise': timing['sunrise'],
                    'sunset': timing['sunset'],
                    'daylight_hours': timing['daylight_hours']
                }
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created light timing for month {month}')
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'✓ Updated light timing for month {month}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Successfully initialized {created_count} and updated {updated_count} light timings!'
            )
        )
        self.stdout.write(
            self.style.WARNING(
                '\n📝 Next step: Go to Django Admin (admin/) and update the timings with your village\'s actual sunrise/sunset times'
            )
        )
