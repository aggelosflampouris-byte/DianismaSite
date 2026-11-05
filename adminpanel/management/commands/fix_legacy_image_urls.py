"""
Django management command to permanently normalize legacy Cloudinary URLs in the database.

Fixes:
- Replaces 'res.cloudinary.com/dianisma/' with active cloud name in Article.lead_image_url and Article.content.
- Replaces 'image/upload/image/upload/' with 'image/upload/'.
- Replaces 'res.cloudinary.com/dianisma/' in Profile.avatar_url.
- Upgrades http:// to https://.
"""
from typing import Any
from django.core.management.base import BaseCommand
from django.db import transaction
from adminpanel.models import Article, Profile
from dianisma_project.storage import normalize_media_url, get_cloudinary_cloud_name


class Command(BaseCommand):
    help = "Normalize legacy Cloudinary URLs in Article and Profile database records."

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Report what would be changed without modifying the database.',
        )

    def handle(self, *args: Any, **options: Any) -> None:
        dry_run = options.get('dry_run', False)
        cloud_name = get_cloudinary_cloud_name()
        self.stdout.write(f"Running URL normalization with cloud name: {cloud_name} (dry_run={dry_run})")

        articles_updated = 0
        profiles_updated = 0

        with transaction.atomic():
            for article in Article.objects.all():
                modified = False

                if article.lead_image_url:
                    normalized_url = normalize_media_url(article.lead_image_url)
                    if normalized_url != article.lead_image_url:
                        article.lead_image_url = normalized_url
                        modified = True

                if article.content and 'res.cloudinary.com/dianisma/' in article.content:
                    article.content = article.content.replace(
                        'res.cloudinary.com/dianisma/',
                        f'res.cloudinary.com/{cloud_name}/'
                    )
                    modified = True

                if modified:
                    articles_updated += 1
                    if not dry_run:
                        article.save(update_fields=['lead_image_url', 'content', 'updated_at'])

            for profile in Profile.objects.all():
                if profile.avatar_url:
                    normalized_avatar = normalize_media_url(profile.avatar_url)
                    if normalized_avatar != profile.avatar_url:
                        profile.avatar_url = normalized_avatar
                        profiles_updated += 1
                        if not dry_run:
                            profile.save(update_fields=['avatar_url'])

            if dry_run:
                self.stdout.write(self.style.WARNING(
                    f"[DRY-RUN] Would update {articles_updated} articles and {profiles_updated} profiles."
                ))
            else:
                self.stdout.write(self.style.SUCCESS(
                    f"Successfully updated {articles_updated} articles and {profiles_updated} profiles."
                ))

