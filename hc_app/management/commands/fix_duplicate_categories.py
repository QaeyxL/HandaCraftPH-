from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from hc_app.models import Category, Product
from django.db.models import Count


class Command(BaseCommand):
    help = (
        "Detect and optionally merge duplicate Category rows (by name).\n"
        "Usage: manage.py fix_duplicate_categories --report\n"
        "       manage.py fix_duplicate_categories --merge [--dry-run]\n"
    )

    def add_arguments(self, parser):
        parser.add_argument('--report', action='store_true', help='Only report duplicates')
        parser.add_argument('--merge', action='store_true', help='Merge duplicates into canonical category')
        parser.add_argument('--dry-run', action='store_true', help='Show what would be done without applying changes')

    def handle(self, *args, **options):
        report_only = options['report']
        do_merge = options['merge']
        dry_run = options['dry_run']

        # Find duplicate names
        dup_qs = Category.objects.values('name').annotate(cnt=Count('id')).filter(cnt__gt=1)
        if not dup_qs.exists():
            self.stdout.write(self.style.SUCCESS('No duplicate categories found.'))
            return

        for row in dup_qs:
            name = row['name']
            cats = list(Category.objects.filter(name=name).order_by('id'))
            self.stdout.write(f"Duplicate category name: '{name}' -> {len(cats)} rows")
            for c in cats:
                self.stdout.write(f"  id={c.id}, slug={c.slug!r}")

            if do_merge:
                canonical = cats[0]
                duplicates = cats[1:]
                self.stdout.write(f"  -> canonical id={canonical.id} (will absorb {len(duplicates)} rows)")
                if dry_run:
                    continue
                # perform merge inside transaction
                try:
                    with transaction.atomic():
                        for dup in duplicates:
                            # reassign products
                            products = Product.objects.filter(category=dup)
                            count = products.update(category=canonical)
                            self.stdout.write(f"    moved {count} products from {dup.id} to {canonical.id}")
                            # delete duplicate category
                            dup.delete()
                        self.stdout.write(self.style.SUCCESS(f"Merged duplicates for '{name}', canonical id={canonical.id}"))
                except Exception as e:
                    raise CommandError(f"Failed to merge duplicates for '{name}': {e}")
            elif report_only:
                continue

        if report_only and not do_merge:
            self.stdout.write(self.style.SUCCESS('Duplicate report complete.'))

