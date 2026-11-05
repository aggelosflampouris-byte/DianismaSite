"""
Data Models for DIANISMA.GR Editorial & Community Platform.
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from dianisma_project.storage import normalize_media_url

User = get_user_model()


class Profile(models.Model):
    """Extended user profile for readers, authors and verified contributors."""

    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'

    STATUS_CHOICES = [
        (STATUS_PENDING, '⏳ Προς Έγκριση'),
        (STATUS_APPROVED, '✅ Εγκεκριμένος Συντάκτης'),
        (STATUS_REJECTED, '❌ Μη Εγκεκριμένος'),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name='Χρήστης'
    )
    profession = models.CharField('Ιδιότητα / Επάγγελμα', max_length=150, blank=True)
    topic_interest = models.CharField('Θεματικό Πεδίο', max_length=100, blank=True)
    bio = models.TextField('Σύντομο Βιογραφικό', blank=True)
    avatar = models.ImageField(
        'Avatar / Φωτογραφία',
        upload_to='avatars/%Y/%m/',
        blank=True,
        null=True
    )
    avatar_url = models.URLField('Εξωτερικό Avatar URL (προαιρετικό)', blank=True)
    status = models.CharField(
        'Κατάσταση Συντάκτη',
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING
    )
    is_verified_contributor = models.BooleanField('Πιστοποιημένος Συντάκτης', default=False)
    created_at = models.DateTimeField('Ημερομηνία Εγγραφής', default=timezone.now)

    class Meta:
        verbose_name = 'Προφίλ Συντάκτη'
        verbose_name_plural = 'Προφίλ Συντακτών'

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.get_status_display()})"

    @property
    def display_avatar(self) -> str:
        """Return image url, avatar_url, or a default placeholder."""
        if self.avatar:
            try:
                return normalize_media_url(self.avatar.url)
            except Exception:
                pass
        if self.avatar_url:
            return normalize_media_url(self.avatar_url)
        return 'https://i.pravatar.cc/150?img=68'

    @property
    def can_submit_articles(self):
        """Only approved contributors or staff can submit articles."""
        return self.status == self.STATUS_APPROVED or self.user.is_staff


@receiver(post_save, sender=User)
def create_or_save_user_profile(sender, instance, created, **kwargs):
    """Automatically create or update Profile when a User is saved."""
    if created:
        Profile.objects.create(user=instance)
    else:
        if hasattr(instance, 'profile'):
            instance.profile.save()


GREEK_TO_LATIN = {
    'α': 'a', 'ά': 'a', 'β': 'v', 'γ': 'g', 'δ': 'd', 'ε': 'e', 'έ': 'e',
    'ζ': 'z', 'η': 'i', 'ή': 'i', 'θ': 'th', 'ι': 'i', 'ί': 'i', 'ϊ': 'i', 'ΐ': 'i',
    'κ': 'k', 'λ': 'l', 'μ': 'm', 'ν': 'n', 'ξ': 'x', 'ο': 'o', 'ό': 'o',
    'π': 'p', 'ρ': 'r', 'σ': 's', 'ς': 's', 'τ': 't', 'υ': 'y', 'ύ': 'y',
    'ϋ': 'y', 'ΰ': 'y', 'φ': 'f', 'χ': 'ch', 'ψ': 'ps', 'ω': 'o', 'ώ': 'o',
}


def greek_slugify(text: str) -> str:
    """Convert Greek text to clean SEO-friendly Latin slug."""
    text_lower = (text or '').lower()
    transliterated = "".join(GREEK_TO_LATIN.get(c, c) for c in text_lower)
    return slugify(transliterated) or 'article'


class Category(models.Model):
    """News and opinion categories (e.g. Πολιτική, Οικονομία, etc.)."""
    name = models.CharField('Όνομα Κατηγορίας', max_length=100, unique=True)
    slug = models.SlugField('Slug', max_length=120, unique=True, blank=True)
    description = models.TextField('Περιγραφή', blank=True)
    order = models.PositiveIntegerField('Σειρά εμφάνισης', default=0)

    class Meta:
        verbose_name = 'Κατηγορία'
        verbose_name_plural = 'Κατηγορίες'
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = greek_slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        from django.urls import reverse
        try:
            return reverse(self.slug)
        except Exception:
            return reverse('category', kwargs={'slug': self.slug})


class Article(models.Model):
    """Editorial & contributor news articles."""
    
    STATUS_DRAFT = 'draft'
    STATUS_PENDING = 'pending'
    STATUS_PUBLISHED = 'published'
    STATUS_REJECTED = 'rejected'

    STATUS_CHOICES = [
        (STATUS_DRAFT, '📝 Πρόχειρο'),
        (STATUS_PENDING, '⏳ Προς Έγκριση'),
        (STATUS_PUBLISHED, '✅ Δημοσιευμένο'),
        (STATUS_REJECTED, '❌ Απορριφθέν'),
    ]

    title = models.CharField('Τίτλος Άρθρου', max_length=255)
    slug = models.SlugField('Slug', max_length=280, unique=True, blank=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name='articles',
        verbose_name='Κατηγορία'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='articles',
        verbose_name='Συντάκτης'
    )
    author_name = models.CharField('Όνομα Συντάκτη (Display Name)', max_length=150, blank=True)
    author_title = models.CharField('Τίτλος / Ιδιότητα Συντάκτη', max_length=150, blank=True)
    author_avatar_url = models.URLField('Avatar Συντάκτη URL', blank=True)
    excerpt = models.TextField('Σύνοψη / Lead Paragraph', max_length=600)
    content = models.TextField('Κυρίως Κείμενο (HTML / Rich Text)', blank=True)
    pdf_file = models.FileField(
        'Αρχείο PDF Άρθρου',
        upload_to='articles/pdfs/',
        blank=True,
        null=True
    )
    lead_image = models.ImageField(
        'Κύρια Φωτογραφία',
        upload_to='articles/%Y/%m/',
        blank=True,
        null=True
    )
    lead_image_url = models.URLField('Εξωτερικό URL Εικόνας (προαιρετικό)', blank=True)
    read_time_minutes = models.PositiveIntegerField('Χρόνος Ανάγνωσης (λεπτά)', default=5)
    status = models.CharField(
        'Κατάσταση',
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_DRAFT
    )
    is_featured = models.BooleanField('Κεντρικό Θέμα (Hero / Featured)', default=False)
    views_count = models.PositiveIntegerField('Προβολές (Pageviews)', default=0)
    created_at = models.DateTimeField('Ημερομηνία Δημιουργίας', default=timezone.now)
    updated_at = models.DateTimeField('Τελευταία Ενημέρωση', auto_now=True)
    published_at = models.DateTimeField('Ημερομηνία Δημοσίευσης', null=True, blank=True)

    class Meta:
        verbose_name = 'Άρθρο'
        verbose_name_plural = 'Άρθρα'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = greek_slugify(self.title)
            timestamp = timezone.now().strftime('%Y%m%d%H%M')
            candidate = f"{base_slug}-{timestamp}"
            counter = 1
            while Article.objects.filter(slug=candidate).exclude(pk=self.pk).exists():
                candidate = f"{base_slug}-{timestamp}-{counter}"
                counter += 1
            self.slug = candidate
        if self.status == self.STATUS_PUBLISHED and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('article_detail', kwargs={'slug': self.slug})

    DEFAULT_FALLBACK_IMAGE = 'https://images.unsplash.com/photo-1526304640581-d334cdbbf45e?auto=format&fit=crop&q=80&w=1000'

    @property
    def get_image_url(self) -> str:
        """Return lead_image URL, lead_image_url, or fallback image."""
        if self.lead_image:
            try:
                url = normalize_media_url(self.lead_image.url)
                if url:
                    return url
            except Exception:
                pass
        if self.lead_image_url:
            url = normalize_media_url(self.lead_image_url)
            if url:
                return url

        return self.DEFAULT_FALLBACK_IMAGE

    @property
    def display_author_name(self):
        if self.author_name:
            return self.author_name
        if self.author:
            return self.author.get_full_name() or self.author.username
        return 'Σύνταξη Dianisma'

    @property
    def display_author_avatar(self):
        if self.author_avatar_url:
            return self.author_avatar_url
        if self.author and hasattr(self.author, 'profile'):
            return self.author.profile.display_avatar
        return 'https://i.pravatar.cc/150?img=68'

    @property
    def status_badge_class(self):
        badges = {
            self.STATUS_DRAFT: 'badge-draft',
            self.STATUS_PENDING: 'badge-pending',
            self.STATUS_PUBLISHED: 'badge-published',
            self.STATUS_REJECTED: 'badge-rejected',
        }
        return badges.get(self.status, 'badge-draft')


class AuthorApplication(models.Model):
    """Applications by community members to become Writers."""
    
    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'

    STATUS_CHOICES = [
        (STATUS_PENDING, '⏳ Εκκρεμεί'),
        (STATUS_APPROVED, '✅ Εγκρίθηκε'),
        (STATUS_REJECTED, '❌ Απορρίφθηκε'),
    ]

    full_name = models.CharField('Ονοματεπώνυμο', max_length=150)
    email = models.EmailField('Email Επικοινωνίας')
    profession = models.CharField('Ιδιότητα / Επάγγελμα', max_length=150)
    topic_interest = models.CharField('Κύρια Θεματική Ενδιαφέροντος', max_length=100)
    bio = models.TextField('Σύντομο Βιογραφικό / Παρουσίαση')
    sample_text = models.TextField('Δείγμα Γραφής / Προσχέδιο Άρθρου', blank=True)
    questionnaire_data = models.JSONField(
        'Απαντήσεις Ερωτηματολογίου',
        default=dict,
        blank=True
    )
    status = models.CharField(
        'Κατάσταση Αίτησης',
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING
    )
    admin_notes = models.TextField('Σημειώσεις Διαχειριστή', blank=True)
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_applications',
        verbose_name='Εξετάστηκε από'
    )
    created_at = models.DateTimeField('Ημερομηνία Υποβολής', default=timezone.now)
    reviewed_at = models.DateTimeField('Ημερομηνία Εξέτασης', null=True, blank=True)

    class Meta:
        verbose_name = 'Αίτηση Συντάκτη'
        verbose_name_plural = 'Αιτήσεις Συντακτών'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.full_name} ({self.get_status_display()})"

    @property
    def status_badge_class(self):
        badges = {
            self.STATUS_PENDING: 'badge-pending',
            self.STATUS_APPROVED: 'badge-approved',
            self.STATUS_REJECTED: 'badge-rejected',
        }
        return badges.get(self.status, 'badge-pending')
