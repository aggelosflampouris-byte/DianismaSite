"""
Utility helpers for DIANISMA.GR Admin Panel.

Contains KPI calculators, email notification stubs, and
data-formatting helpers. Follows PEP 8 / Clean Architecture.
"""
from datetime import datetime


# ---------------------------------------------------------------------------
# Mock data store — replaced by DB queries in a Django deployment
# ---------------------------------------------------------------------------

MOCK_ARTICLES = [
    {
        'id': 1,
        'title': 'Αναδιάρθρωση των Θεσμών: Προτάσεις Μεταρρύθμισης',
        'slug': 'anadiarthrosi-thesmon',
        'category': 'Πολιτική',
        'category_slug': 'politiki',
        'author_name': 'Γιώργος Παπαδόπουλος',
        'excerpt': 'Ανάλυση των νομοθετικών πρωτοβουλιών για τον εκσυγχρονισμό...',
        'content': '<p>Πλήρες κείμενο άρθρου...</p>',
        'lead_image_url': '',
        'read_time_minutes': 8,
        'status': 'published',
        'is_featured': True,
        'views_count': 4820,
        'created_at': '2024-01-15',
        'published_at': '2024-01-15',
    },
    {
        'id': 2,
        'title': 'ΑΕΠ & Ανάπτυξη: Ο Δρόμος Μπροστά για την Ελληνική Οικονομία',
        'slug': 'aep-anaptyxi-ellhnikh-oikonomia',
        'category': 'Οικονομία',
        'category_slug': 'oikonomia',
        'author_name': 'Μαρία Κωνσταντίνου',
        'excerpt': 'Νέα στοιχεία για την πορεία του ΑΕΠ...',
        'content': '<p>Πλήρες κείμενο άρθρου...</p>',
        'lead_image_url': '',
        'read_time_minutes': 6,
        'status': 'published',
        'is_featured': False,
        'views_count': 3210,
        'created_at': '2024-01-14',
        'published_at': '2024-01-14',
    },
    {
        'id': 3,
        'title': 'Κρίση Στέγης: Η Αόρατη Κοινωνική Έκρηξη',
        'slug': 'krisi-stegis-koinoniki-ekrixi',
        'category': 'Κοινωνία',
        'category_slug': 'koinonia',
        'author_name': 'Νίκος Αλεξίου',
        'excerpt': 'Ρεπορτάζ για την κρίση στέγης...',
        'content': '<p>Πλήρες κείμενο άρθρου...</p>',
        'lead_image_url': '',
        'read_time_minutes': 10,
        'status': 'pending',
        'is_featured': False,
        'views_count': 0,
        'created_at': '2024-01-16',
        'published_at': None,
    },
    {
        'id': 4,
        'title': 'Ψηφιακός Μετασχηματισμός: Ευκαιρίες & Κίνδυνοι',
        'slug': 'psifiakos-metasximatismos',
        'category': 'Αναλύσεις',
        'category_slug': 'analyseis',
        'author_name': 'Ελένη Δημητρίου',
        'excerpt': 'Εκτενής ανάλυση του ψηφιακού μετασχηματισμού...',
        'content': '<p>Πλήρες κείμενο άρθρου...</p>',
        'lead_image_url': '',
        'read_time_minutes': 12,
        'status': 'draft',
        'is_featured': False,
        'views_count': 0,
        'created_at': '2024-01-13',
        'published_at': None,
    },
    {
        'id': 5,
        'title': 'Η Ευρώπη στο Σταυροδρόμι',
        'slug': 'evropi-stavrodromio',
        'category': 'Απόψεις',
        'category_slug': 'apopseis',
        'author_name': 'Κώστας Σταύρου',
        'excerpt': 'Γιατί οι ευρωπαϊκές αξίες είναι πιο σημαντικές από ποτέ...',
        'content': '<p>Πλήρες κείμενο άρθρου...</p>',
        'lead_image_url': '',
        'read_time_minutes': 5,
        'status': 'rejected',
        'is_featured': False,
        'views_count': 0,
        'created_at': '2024-01-12',
        'published_at': None,
    },
]

MOCK_APPLICATIONS = [
    {
        'id': 1,
        'full_name': 'Αλέξανδρος Νικολάου',
        'email': 'a.nikolaou@example.com',
        'profession': 'Δημοσιογράφος',
        'topic_interest': 'Εξωτερική Πολιτική',
        'bio': 'Δημοσιογράφος με 10 χρόνια εμπειρία σε διεθνή ΜΜΕ...',
        'sample_text': 'Η γεωπολιτική αστάθεια στη Μέση Ανατολή...',
        'questionnaire_data': {
            'experience_years': '10',
            'previous_publications': 'Kathimerini, SKAI',
            'motivation': 'Θέλω να συνεισφέρω σε ποιοτική δημοσιογραφία.',
        },
        'status': 'pending',
        'admin_notes': '',
        'created_at': '2024-01-16',
        'reviewed_at': None,
    },
    {
        'id': 2,
        'full_name': 'Σοφία Χριστοδούλου',
        'email': 's.christodoulou@example.com',
        'profession': 'Οικονομολόγος',
        'topic_interest': 'Οικονομική Ανάλυση',
        'bio': 'Οικονομολόγος με ειδίκευση στις χρηματαγορές...',
        'sample_text': 'Η ελληνική αγορά ακινήτων τα τελευταία χρόνια...',
        'questionnaire_data': {
            'experience_years': '7',
            'previous_publications': 'Fortune Greece',
            'motivation': 'Η οικονομική εκπαίδευση του κοινού.',
        },
        'status': 'approved',
        'admin_notes': 'Ισχυρό βιογραφικό. Άμεση έγκριση.',
        'created_at': '2024-01-10',
        'reviewed_at': '2024-01-12',
    },
    {
        'id': 3,
        'full_name': 'Δημήτρης Παπαγεωργίου',
        'email': 'd.papageorgiou@example.com',
        'profession': 'Δικηγόρος',
        'topic_interest': 'Δίκαιο & Κοινωνία',
        'bio': 'Δικηγόρος με εξειδίκευση στο συνταγματικό δίκαιο...',
        'sample_text': 'Η έννοια του κράτους δικαίου σε καιρούς κρίσης...',
        'questionnaire_data': {
            'experience_years': '15',
            'previous_publications': 'Νομικά Χρονικά',
            'motivation': 'Επικοινωνία νομικών ζητημάτων στο ευρύ κοινό.',
        },
        'status': 'rejected',
        'admin_notes': 'Δεν πληροί τα κριτήρια αναλυτικής γραφής.',
        'created_at': '2024-01-08',
        'reviewed_at': '2024-01-11',
    },
]

CATEGORIES = [
    {'name': 'Πολιτική', 'slug': 'politiki'},
    {'name': 'Οικονομία', 'slug': 'oikonomia'},
    {'name': 'Κοινωνία', 'slug': 'koinonia'},
    {'name': 'Αναλύσεις', 'slug': 'analyseis'},
    {'name': 'Απόψεις', 'slug': 'apopseis'},
    {'name': 'Dialogues', 'slug': 'dialogues'},
]


# ---------------------------------------------------------------------------
# KPI Calculators
# ---------------------------------------------------------------------------

def get_admin_dashboard_kpis() -> dict:
    """
    Calculate and return dashboard KPI metrics.

    Returns a dict with keys:
      total_articles, published_articles, pending_articles,
      pending_applications, total_views, recent_articles,
      recent_applications, category_distribution.
    """
    articles = MOCK_ARTICLES
    applications = MOCK_APPLICATIONS

    total_articles = len(articles)
    published_articles = sum(1 for a in articles if a['status'] == 'published')
    pending_articles = sum(1 for a in articles if a['status'] == 'pending')
    pending_applications = sum(
        1 for ap in applications if ap['status'] == 'pending'
    )
    total_views = sum(a['views_count'] for a in articles)

    recent_articles = sorted(
        articles, key=lambda x: x['created_at'], reverse=True
    )[:5]

    recent_applications = sorted(
        applications, key=lambda x: x['created_at'], reverse=True
    )[:3]

    category_distribution = {}
    for article in articles:
        cat = article['category']
        category_distribution[cat] = category_distribution.get(cat, 0) + 1

    return {
        'total_articles': total_articles,
        'published_articles': published_articles,
        'pending_articles': pending_articles,
        'pending_applications': pending_applications,
        'total_views': total_views,
        'recent_articles': recent_articles,
        'recent_applications': recent_applications,
        'category_distribution': category_distribution,
    }


# ---------------------------------------------------------------------------
# Email notification stubs (log to console in Flask; use Django mailer in prod)
# ---------------------------------------------------------------------------

def send_author_status_email(application: dict, status: str) -> None:
    """
    Notify an author application candidate of their review outcome.

    In production replace with Django send_mail / Celery task.
    """
    messages = {
        'approved': f"Συγχαρητήρια {application['full_name']}! Η αίτησή σας εγκρίθηκε.",
        'rejected': f"Αγαπητέ/ή {application['full_name']}, δυστυχώς η αίτησή σας απορρίφθηκε.",
        'clarification': f"Αγαπητέ/ή {application['full_name']}, χρειαζόμαστε διευκρινίσεις.",
    }
    msg = messages.get(status, '')
    print(f"[EMAIL] → {application['email']}: {msg}")


def send_article_status_email(article: dict, status: str) -> None:
    """
    Notify the article author of a status change.

    In production replace with Django send_mail / Celery task.
    """
    print(
        f"[EMAIL] Article '{article['title']}' status changed to '{status}' "
        f"— notifying author: {article['author_name']}"
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_status_badge_class(status: str) -> str:
    """Map a status string to its CSS badge class."""
    badge_map = {
        'draft': 'badge-draft',
        'pending': 'badge-pending',
        'published': 'badge-published',
        'rejected': 'badge-rejected',
        'approved': 'badge-approved',
    }
    return badge_map.get(status, 'badge-draft')


def format_views(count: int) -> str:
    """Format a view count with K suffix for thousands."""
    if count >= 1000:
        return f"{count / 1000:.1f}K"
    return str(count)


def get_article_by_id(article_id: int) -> dict | None:
    """Return article dict by ID from mock store, or None."""
    for article in MOCK_ARTICLES:
        if article['id'] == article_id:
            return article
    return None


def get_application_by_id(app_id: int) -> dict | None:
    """Return application dict by ID from mock store, or None."""
    for application in MOCK_APPLICATIONS:
        if application['id'] == app_id:
            return application
    return None


def filter_articles(q: str = '', category: str = '', status: str = '', sort: str = 'newest') -> list:
    """
    Filter and sort MOCK_ARTICLES based on search parameters.

    Args:
        q: Free-text search against title/author.
        category: Category slug filter.
        status: Status filter string.
        sort: 'newest' | 'oldest' | 'views'.
    """
    results = list(MOCK_ARTICLES)

    if q:
        q_lower = q.lower()
        results = [
            a for a in results
            if q_lower in a['title'].lower() or q_lower in a['author_name'].lower()
        ]

    if category:
        results = [a for a in results if a['category_slug'] == category]

    if status:
        results = [a for a in results if a['status'] == status]

    if sort == 'oldest':
        results.sort(key=lambda x: x['created_at'])
    elif sort == 'views':
        results.sort(key=lambda x: x['views_count'], reverse=True)
    else:  # newest
        results.sort(key=lambda x: x['created_at'], reverse=True)

    return results


def filter_applications(status: str = '') -> list:
    """Filter MOCK_APPLICATIONS by status."""
    if not status:
        return list(MOCK_APPLICATIONS)
    return [a for a in MOCK_APPLICATIONS if a['status'] == status]
