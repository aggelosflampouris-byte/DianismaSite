"""
Forms for DIANISMA.GR Custom Admin Panel.

Provides form classes for article management, author application
review, and content filtering. Follows Clean Architecture / PEP 8.
"""


class ArticleAdminForm:
    """
    Form for creating and editing editorial articles.

    Fields mirror the Article model: title, slug, category,
    author_name, excerpt, content, lead_image_url,
    read_time_minutes, status, is_featured.
    """

    REQUIRED_FIELDS = [
        'title',
        'category',
        'excerpt',
        'content',
        'status',
    ]

    STATUS_CHOICES = [
        ('draft', '📝 Πρόχειρο'),
        ('pending', '⏳ Προς Έγκριση'),
        ('published', '✅ Δημοσιευμένο'),
        ('rejected', '❌ Απορριφθέν'),
    ]

    @staticmethod
    def validate(data: dict) -> tuple:
        """
        Validate form submission data.

        Returns (is_valid, errors) where errors maps field names
        to human-readable Greek error messages.
        """
        errors = {}
        required = ArticleAdminForm.REQUIRED_FIELDS

        for field in required:
            if not data.get(field, '').strip():
                errors[field] = 'Το πεδίο είναι υποχρεωτικό.'

        title = data.get('title', '')
        if len(title) > 255:
            errors['title'] = 'Ο τίτλος δεν μπορεί να υπερβαίνει τους 255 χαρακτήρες.'

        excerpt = data.get('excerpt', '')
        if len(excerpt) > 600:
            errors['excerpt'] = 'Η σύνοψη δεν μπορεί να υπερβαίνει τους 600 χαρακτήρες.'

        return (len(errors) == 0, errors)


class AuthorApprovalForm:
    """
    Form for admin review of author applications.

    Captures the decision (approve / reject / request_clarification)
    and optional admin notes.
    """

    DECISION_CHOICES = [
        ('approved', '✅ Έγκριση Συντάκτη'),
        ('rejected', '❌ Απόρριψη'),
        ('clarification', '📝 Αίτημα Διευκρινίσεων'),
    ]

    @staticmethod
    def validate(data: dict) -> tuple:
        """Validate admin review submission."""
        errors = {}

        decision = data.get('decision', '').strip()
        valid_decisions = [c[0] for c in AuthorApprovalForm.DECISION_CHOICES]
        if decision not in valid_decisions:
            errors['decision'] = 'Επιλέξτε έγκυρη απόφαση.'

        return (len(errors) == 0, errors)


class ArticleFilterForm:
    """
    Form for filtering the articles list view.

    Supports filtering by category slug, status value,
    and free-text search query.
    """

    STATUS_OPTIONS = [
        ('', 'Όλες οι καταστάσεις'),
        ('draft', '📝 Πρόχειρα'),
        ('pending', '⏳ Προς Έγκριση'),
        ('published', '✅ Δημοσιευμένα'),
        ('rejected', '❌ Απορριφθέντα'),
    ]

    @staticmethod
    def parse(args: dict) -> dict:
        """
        Parse query-string arguments into filter parameters.

        Returns a normalised dict with keys:
          - q       : str  (search query)
          - category: str  (category slug or '')
          - status  : str  (status value or '')
          - sort    : str  ('newest' | 'oldest' | 'views')
        """
        return {
            'q': args.get('q', '').strip(),
            'category': args.get('category', '').strip(),
            'status': args.get('status', '').strip(),
            'sort': args.get('sort', 'newest').strip(),
        }
