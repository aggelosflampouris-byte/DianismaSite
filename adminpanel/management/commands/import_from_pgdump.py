"""
Data Migration Command: Import articles from PostgreSQL pg_dump .dat files
into the new Dianisma Django site.

Usage:
    python manage.py import_from_pgdump --dat-path "C:\\path\\to\\dianismadatabase_p5jm"
"""
import os
import re
import html
import logging
from datetime import datetime, timezone as dt_timezone

from django.db import transaction

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model

from adminpanel.models import Article, Category, greek_slugify

User = get_user_model()
logger = logging.getLogger(__name__)


BLOG_POST_COLUMNS = [
    "id", "title", "body", "category", "created_at",
    "author", "image", "views", "likes", "shares",
    "audio_file", "scheduled_publish_date",
]

CLOUDINARY_BASE = "https://res.cloudinary.com/dh7aqmruq/image/upload/"

CATEGORY_MAP = {
    "politics":    "Πολιτική",
    "economy":     "Οικονομία",
    "society":     "Κοινωνία",
    "technology":  "Τεχνολογία",
    "world":       "Κόσμος",
    "sports":      "Αθλητισμός",
    "culture":     "Πολιτισμός",
    "health":      "Υγεία",
    "environment": "Περιβάλλον",
    "science":     "Επιστήμη",
}


def find_blog_post_file(dat_dir):
    toc_path = os.path.join(dat_dir, "toc.dat")
    with open(toc_path, "rb") as f:
        toc_bytes = f.read()
    target = b"blog_post\x00"
    pos = 0
    while True:
        idx = toc_bytes.find(target, pos)
        if idx == -1:
            break
        search_region = toc_bytes[max(0, idx - 512): idx]
        candidates = re.findall(rb"\x00(\d{4})\x00", search_region)
        if candidates:
            file_number = candidates[-1].decode("ascii")
            candidate_path = os.path.join(dat_dir, f"{file_number}.dat")
            if os.path.exists(candidate_path):
                size = os.path.getsize(candidate_path)
                if size > 1000:
                    return candidate_path
        pos = idx + 1
    return None


def decode_html_entities(text):
    return html.unescape(text or "")


def parse_dat_line(line):
    if line.strip() == "\\.":
        return []
    parts = line.rstrip("\n\r").split("\t")
    result = []
    for part in parts:
        if part == "\\N":
            result.append(None)
        else:
            part = part.replace("\\n", "\n").replace("\\t", "\t").replace("\\\\", "\\")
            result.append(part)
    return result


def parse_timestamp(ts_str):
    if not ts_str:
        return None
    try:
        ts_str = ts_str.strip()
        ts_str = re.sub(r"\+00$", "+00:00", ts_str)
        return datetime.fromisoformat(ts_str).astimezone(dt_timezone.utc)
    except Exception:
        return None


def build_image_url(image_field):
    if not image_field:
        return ""
    if image_field.startswith("http"):
        return image_field
    return CLOUDINARY_BASE + image_field


def get_or_create_category(slug):
    """Safely get or create a Category — uses get_or_create with atomic savepoint."""
    name = CATEGORY_MAP.get(slug)
    if not name:
        name = slug.replace("-", " ").replace("_", " ").title()
    if not name:
        return None
    # Filter first to avoid IntegrityError from concurrent slug generation
    cat = Category.objects.filter(name=name).first()
    if cat:
        return cat
    new_slug = greek_slugify(name)
    cat = Category.objects.filter(slug=new_slug).first()
    if cat:
        return cat
    try:
        with transaction.atomic():
            cat = Category.objects.create(name=name, slug=new_slug)
    except Exception:
        cat = Category.objects.filter(name=name).first()
    return cat


def get_or_create_system_author():
    user, _ = User.objects.get_or_create(
        username="migration_import",
        defaults={
            "email": "migration@dianisma.gr",
            "first_name": "Σύνταξη",
            "last_name": "Dianisma",
            "is_active": True,
        },
    )
    return user


class Command(BaseCommand):
    help = "Import blog posts from a PostgreSQL pg_dump directory into the new site."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dat-path",
            required=True,
            help="Full path to the pg_dump directory (e.g. dianismadatabase_p5jm)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            default=False,
            help="Parse and report without writing to database.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=0,
            help="Import only N articles (0 = all).",
        )
        parser.add_argument(
            "--blog-post-file",
            default=None,
            help="Override auto-detection: specify the exact .dat file for blog_post.",
        )

    def handle(self, *args, **options):
        dat_dir = options["dat_path"]
        dry_run = options["dry_run"]
        limit = options["limit"]

        self.stdout.write(self.style.MIGRATE_HEADING(
            "\n Dianisma Data Migration — pg_dump Import\n"
        ))
        self.stdout.write(f"   Source directory : {dat_dir}")
        self.stdout.write(f"   Dry run          : {dry_run}")
        self.stdout.write(f"   Article limit    : {'all' if not limit else limit}\n")

        if options["blog_post_file"]:
            post_dat = options["blog_post_file"]
        else:
            self.stdout.write("Scanning toc.dat to locate blog_post file...")
            post_dat = find_blog_post_file(dat_dir)

        if not post_dat or not os.path.exists(post_dat):
            self.stdout.write(self.style.WARNING(
                "Auto-detection failed. Using largest .dat file as fallback..."
            ))
            all_dats = [
                os.path.join(dat_dir, f)
                for f in os.listdir(dat_dir)
                if f.endswith(".dat") and f != "toc.dat"
            ]
            if not all_dats:
                self.stderr.write(self.style.ERROR("No .dat files found."))
                return
            post_dat = max(all_dats, key=os.path.getsize)

        self.stdout.write(f"Blog post file  : {post_dat}")
        self.stdout.write(f"File size       : {os.path.getsize(post_dat):,} bytes\n")

        self.stdout.write("Reading and parsing articles...")
        with open(post_dat, "r", encoding="utf-8", errors="replace") as f:
            raw_lines = f.readlines()

        articles_raw = []
        for line in raw_lines:
            line = line.rstrip("\r\n")
            if not line or line == "\\.":
                continue
            parts = parse_dat_line(line)
            if len(parts) < 6:
                continue
            articles_raw.append(parts)

        total_found = len(articles_raw)
        self.stdout.write(self.style.SUCCESS(f"   Found {total_found} articles in source file.\n"))

        if limit:
            articles_raw = articles_raw[:limit]

        system_user = None
        if not dry_run:
            system_user = get_or_create_system_author()

        stats = {
            "imported": 0,
            "skipped_duplicate": 0,
            "skipped_error": 0,
            "errors": [],
        }

        self.stdout.write("Processing articles...\n")
        old_id = "?"

        # Pre-build category cache to avoid repeated DB calls and IntegrityErrors
        category_cache: dict[str, Category | None] = {}

        for idx, parts in enumerate(articles_raw, start=1):
            try:
                # Use local helper to avoid closure bug with loop variable
                def col(p, i, default=None):
                    return p[i] if i < len(p) else default

                old_id      = col(parts, 0, "?")
                title_raw   = col(parts, 1) or ""
                body_raw    = col(parts, 2) or ""
                cat_slug    = col(parts, 3) or ""
                created_raw = col(parts, 4)
                author_raw  = col(parts, 5) or ""
                image_raw   = col(parts, 6)
                col11       = col(parts, 11)

                title   = decode_html_entities(title_raw).strip()
                content = decode_html_entities(body_raw).strip()
                excerpt_plain = re.sub(r"<[^>]+>", "", content)[:400].strip()

                created_at = parse_timestamp(created_raw) or timezone.now()
                scheduled  = parse_timestamp(col11)

                status = Article.STATUS_PUBLISHED
                published_at = scheduled if scheduled else created_at

                image_url = build_image_url(image_raw)

                # Category: use cache to prevent repeated DB hits
                category = None
                if not dry_run and cat_slug:
                    if cat_slug not in category_cache:
                        category_cache[cat_slug] = get_or_create_category(cat_slug)
                    category = category_cache[cat_slug]

                author_display = decode_html_entities(author_raw).strip() or "Σύνταξη Dianisma"

                self.stdout.write(
                    f"  [{idx:>4}/{len(articles_raw)}] ID:{old_id} | "
                    f"Cat:{cat_slug:<12} | {title[:55]}"
                )

                if dry_run:
                    stats["imported"] += 1
                    continue

                existing = Article.objects.filter(
                    title=title,
                    created_at__date=created_at.date(),
                ).first()
                if existing:
                    self.stdout.write(
                        self.style.WARNING(f"       Duplicate (id={existing.pk}) — skipped.")
                    )
                    stats["skipped_duplicate"] += 1
                    continue

                with transaction.atomic():
                    article = Article(
                        title=title,
                        content=content,
                        excerpt=excerpt_plain[:590] if excerpt_plain else title[:590],
                        category=category,
                        author=system_user,
                        author_name=author_display,
                        lead_image_url=image_url,
                        status=status,
                        created_at=created_at,
                        published_at=published_at,
                    )
                    article.save()
                stats["imported"] += 1

            except Exception as exc:
                msg = f"Article idx={idx} old_id={old_id}: {exc}"
                logger.exception(msg)
                stats["skipped_error"] += 1
                stats["errors"].append(msg)
                self.stdout.write(self.style.ERROR(f"       Error: {exc}"))

        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.MIGRATE_HEADING("MIGRATION REPORT"))
        self.stdout.write("=" * 60)
        self.stdout.write(f"  Articles found in source   : {total_found}")
        self.stdout.write(self.style.SUCCESS(f"  Imported successfully    : {stats['imported']}"))
        self.stdout.write(self.style.WARNING(f"  Skipped (duplicates)    : {stats['skipped_duplicate']}"))
        self.stdout.write(self.style.ERROR(f"  Skipped (errors)        : {stats['skipped_error']}"))
        self.stdout.write("=" * 60)

        if stats["errors"]:
            self.stdout.write("\nError log:")
            for err in stats["errors"]:
                self.stdout.write(f"   - {err}")

        if dry_run:
            self.stdout.write(self.style.WARNING("\n   [DRY RUN] No data was written to the database."))
        else:
            self.stdout.write(self.style.SUCCESS("\nMigration complete! Check the admin panel."))
