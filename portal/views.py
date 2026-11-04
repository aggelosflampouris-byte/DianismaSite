"""
Views for DIANISMA.GR public portal and contributor interactions.
"""
import logging
import urllib.parse

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import F, Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template import TemplateDoesNotExist
from django.template.loader import get_template, render_to_string

from adminpanel.models import Article, AuthorApplication, Category, Profile
from .forms import WriterApplicationForm, WriterArticleSubmitForm

logger = logging.getLogger(__name__)


def index(request):
    """Homepage view with editorial hero grid and rich category feeds."""

    published = Article.objects.filter(status=Article.STATUS_PUBLISHED).select_related('category')

    # Lead hero article
    lead_article = published.filter(is_featured=True).first() or published.first()
    lead_id = lead_article.id if lead_article else 0

    # Secondary articles for the hero sidebar (3)
    secondary_articles = list(published.exclude(id=lead_id)[:3])
    sec_ids = [a.id for a in secondary_articles]

    # Latest articles grid (12 per page, strictly limited for initial load)
    excluded_ids = [lead_id] + sec_ids
    latest_qs = published.exclude(id__in=excluded_ids).order_by('-published_at')

    # Strictly initial 12 articles for homepage latest news grid
    paginator = Paginator(latest_qs, 12)
    latest_page = paginator.get_page(1)

    # Per-category blocks (4 articles each)
    def cat_articles(slug, exclude_ids=()):
        return list(published.filter(category__slug=slug).exclude(id__in=exclude_ids)[:4])

    politics_articles  = cat_articles('politiki',  [lead_id])
    economy_articles   = cat_articles('oikonomia', [lead_id])
    koinonia_articles  = cat_articles('koinonia',  [lead_id])
    analyseis_articles = cat_articles('analyseis', [lead_id])

    # Opinions (up to 4 for carousel)
    opinions = published.filter(category__slug='apopseis')[:4]

    # Popular sidebar
    popular = published.order_by('-views_count')[:5]

    context = {
        'lead_article':        lead_article,
        'secondary_articles':  secondary_articles,
        'latest_articles':     latest_page,
        'latest_paginator':    paginator,
        'has_next':            latest_page.has_next(),
        'next_page':           latest_page.next_page_number() if latest_page.has_next() else None,
        'excluded_ids_str':    ",".join(str(i) for i in excluded_ids if i),
        'politics_articles':   politics_articles,
        'economy_articles':    economy_articles,
        'koinonia_articles':   koinonia_articles,
        'analyseis_articles':  analyseis_articles,
        'opinions':            opinions,
        'popular_articles':    popular,
    }
    return render(request, 'index.html', context)


def category_view(request, slug, template_name):
    """Generic category view helper with 12-article initial pagination."""

    category = Category.objects.filter(slug=slug).first()
    published = Article.objects.filter(status=Article.STATUS_PUBLISHED)
    
    if category:
        category_articles = published.filter(category=category)
    else:
        category_articles = published

    hero_article = category_articles.filter(is_featured=True).first() or category_articles.first()
    hero_id = hero_article.id if hero_article else 0
    other_articles = category_articles.exclude(id=hero_id).order_by('-published_at')

    # Strictly 12 articles on initial page load
    paginator = Paginator(other_articles, 12)
    articles_page = paginator.get_page(1)

    # Prioritize category-specific popular articles, fallback to global published popular
    cat_popular = list(category_articles.order_by('-views_count')[:5]) if category else []
    if len(cat_popular) < 5:
        existing_ids = [a.id for a in cat_popular]
        global_popular = list(published.exclude(id__in=existing_ids).order_by('-views_count')[:5 - len(cat_popular)])
        popular = cat_popular + global_popular
    else:
        popular = cat_popular

    context = {
        'category':          category,
        'hero_article':      hero_article,
        'articles':          articles_page,
        'has_next':          articles_page.has_next(),
        'next_page':         articles_page.next_page_number() if articles_page.has_next() else None,
        'category_slug':     slug,
        'exclude_ids_str':   str(hero_id) if hero_id else '',
        'popular_articles':  popular,
    }
    return render(request, template_name, context)


def load_more_articles(request):
    """
    AJAX endpoint for loading next batch of 12 articles dynamically.
    Returns rendered HTML cards and pagination metadata in JSON format.
    """

    MAX_PAGE_SIZE = 48  # hard cap to prevent DoS via large page requests

    category_slug = request.GET.get('category', '').strip()
    card_type = request.GET.get('card_type', 'category').strip()  # 'news' or 'category'
    exclude_ids_raw = request.GET.get('exclude_ids', '').strip()

    try:
        page_num = int(request.GET.get('page', 2))
        page_size = min(int(request.GET.get('page_size', 12)), MAX_PAGE_SIZE)
    except (ValueError, TypeError):
        return JsonResponse({'success': False, 'error': 'Invalid page or page_size parameter.'}, status=400)

    if page_num < 1:
        page_num = 1

    exclude_ids = []
    if exclude_ids_raw:
        for val in exclude_ids_raw.split(','):
            if val.strip().isdigit():
                exclude_ids.append(int(val.strip()))

    published = Article.objects.filter(status=Article.STATUS_PUBLISHED).select_related('category')

    if category_slug:
        published = published.filter(category__slug=category_slug)

    if exclude_ids:
        published = published.exclude(id__in=exclude_ids)

    qs = published.order_by('-published_at')

    paginator = Paginator(qs, page_size)
    page_obj = paginator.get_page(page_num)

    template_name = 'components/news_card.html' if card_type == 'news' else 'components/category_card.html'

    cards_html = [
        render_to_string(template_name, {'art': art}, request=request)
        for art in page_obj
    ]

    return JsonResponse({
        'success': True,
        'has_next': page_obj.has_next(),
        'next_page': page_obj.next_page_number() if page_obj.has_next() else None,
        'count': len(page_obj.object_list),
        'html': "".join(cards_html)
    })


def search(request):
    """Global search view for public articles."""
    query = request.GET.get('q', '').strip()
    if '%' in query:
        try:
            query = urllib.parse.unquote(query).strip()
        except Exception:
            pass
    published = Article.objects.filter(status=Article.STATUS_PUBLISHED)
    results = []
    
    if query:
        results = published.filter(
            Q(title__icontains=query) |
            Q(excerpt__icontains=query) |
            Q(content__icontains=query) |
            Q(author_name__icontains=query) |
            Q(category__name__icontains=query)
        ).distinct()

    popular = published.order_by('-views_count')[:5]

    return render(request, 'search.html', {
        'query': query,
        'results': results,
        'popular_articles': popular,
    })


def politiki(request):
    return category_view(request, 'politiki', 'politiki.html')


def oikonomia(request):
    return category_view(request, 'oikonomia', 'oikonomia.html')


def koinonia(request):
    return category_view(request, 'koinonia', 'koinonia.html')


def analyseis(request):
    return category_view(request, 'analyseis', 'analyseis.html')


def apopseis(request):
    return category_view(request, 'apopseis', 'apopseis.html')


def category_generic(request, slug):
    """Generic fallback view for any category slug.

    Resolves the appropriate template (dedicated or politiki fallback) then
    delegates entirely to category_view, eliminating duplicated hero/popular logic.
    """
    get_object_or_404(Category, slug=slug)  # 404 on unknown slug before any DB work
    try:
        get_template(f'{slug}.html')
        template = f'{slug}.html'
    except TemplateDoesNotExist:
        template = 'politiki.html'
    return category_view(request, slug, template)


def apply_writer(request):
    """Handle writer applications (POST)."""
    if request.method == 'POST':
        name = request.POST.get('full_name') or request.POST.get('name')
        email = request.POST.get('email')
        profession = request.POST.get('profession') or request.POST.get('role')
        topic_interest = request.POST.get('topic_interest') or request.POST.get('topic', 'apopseis')
        bio = request.POST.get('bio') or request.POST.get('appBio', '')
        sample_text = request.POST.get('sample_text', '')

        if name and email and profession:
            AuthorApplication.objects.create(
                full_name=name.strip(),
                email=email.strip(),
                profession=profession.strip(),
                topic_interest=topic_interest.strip(),
                bio=bio.strip(),
                sample_text=sample_text.strip(),
                status=AuthorApplication.STATUS_PENDING
            )
            messages.success(request, 'Η αίτησή σας υποβλήθηκε επιτυχώς! Η συντακτική ομάδα θα επικοινωνήσει μαζί σας.')
            return redirect('apopseis')
        else:
            messages.error(request, 'Παρακαλούμε συμπληρώστε όλα τα απαιτούμενα πεδία.')

    form = WriterApplicationForm()
    return render(request, 'apply_writer.html', {'application_form': form})


@login_required
def writer_dashboard(request):
    """Allow approved contributors to submit an article with PDF."""
    user = request.user
    profile = getattr(user, 'profile', None)

    # Check permission: must be approved contributor or staff
    if not (user.is_staff or (profile and profile.status == Profile.STATUS_APPROVED)):
        messages.warning(request, 'Απαιτείται έγκριση συντάκτη για την υποβολή άρθρου.')
        return redirect('index')

    if request.method == 'POST':
        form = WriterArticleSubmitForm(request.POST, request.FILES)
        if form.is_valid():
            article = form.save(commit=False)
            article.author = user
            article.author_name = user.get_full_name() or user.username
            article.author_title = profile.profession if profile else ''
            article.status = Article.STATUS_PENDING  # Pending approval
            article.save()
            messages.success(request, 'Το άρθρο σας υποβλήθηκε επιτυχώς και βρίσκεται υπό έλεγχο από τη συντακτική ομάδα!')
            return redirect('writer_dashboard')
    else:
        form = WriterArticleSubmitForm()

    # Get recent submissions by this user
    my_articles = Article.objects.filter(author=user).order_by('-created_at')[:10]

    return render(request, 'writer_dashboard.html', {'form': form, 'my_articles': my_articles})


def article_detail(request, slug):
    """Full detail page for any published article."""
    article = get_object_or_404(Article, slug=slug, status=Article.STATUS_PUBLISHED)
    
    # Increment views count uniquely per session
    viewed_articles = request.session.get('viewed_articles', [])
    if article.id not in viewed_articles:
        Article.objects.filter(id=article.id).update(views_count=F('views_count') + 1)
        viewed_articles.append(article.id)
        request.session['viewed_articles'] = viewed_articles
        article.refresh_from_db()

    # Related articles (3 articles from same category, fallback to latest)
    related = list(Article.objects.filter(
        category=article.category,
        status=Article.STATUS_PUBLISHED
    ).exclude(id=article.id)[:3])

    if len(related) < 3:
        existing_ids = [a.id for a in related] + [article.id]
        more = list(Article.objects.filter(status=Article.STATUS_PUBLISHED).exclude(id__in=existing_ids).order_by('-published_at')[:3 - len(related)])
        related.extend(more)

    popular = Article.objects.filter(status=Article.STATUS_PUBLISHED).order_by('-views_count')[:5]

    context = {
        'article': article,
        'related_articles': related,
        'popular_articles': popular,
    }
    return render(request, 'article_detail.html', context)


def robots_txt(request):
    """Serve dynamic robots.txt file pointing to sitemap.xml."""
    host = request.get_host()
    scheme = request.scheme
    content = f"User-agent: *\nAllow: /\nDisallow: /adminpanel/\nDisallow: /admin/\n\nSitemap: {scheme}://{host}/sitemap.xml\n"
    return HttpResponse(content, content_type="text/plain")




def legacy_tag_redirect(request, tag_name=''):
    """
    301 Permanent Redirect for legacy tag URLs (e.g. /tag/<slug>/, /tags/<slug>/).
    Preserves SEO authority from Google index and redirects users to site search.
    """
    decoded = urllib.parse.unquote(tag_name or '')
    while '%' in decoded:
        new_dec = urllib.parse.unquote(decoded)
        if new_dec == decoded:
            break
        decoded = new_dec
    clean_tag = decoded.rstrip('/').replace('-', ' ').replace('_', ' ').strip()
    if clean_tag:
        return redirect(f"/search/?q={urllib.parse.quote(clean_tag)}", permanent=True)
    return redirect('/', permanent=True)

def custom_404(request, exception=None):
    """Custom 404 error page handler."""
    return render(request, '404.html', status=404)


# ── LEGAL & COMPLIANCE VIEWS ──

def terms(request):
    """Terms of Service / Terms of Use page."""
    return render(request, 'legal/terms.html')


def privacy(request):
    """Privacy Policy (GDPR) page."""
    return render(request, 'legal/privacy.html')


def cookie_policy(request):
    """Cookie Policy page."""
    return render(request, 'legal/cookies.html')


def copyright_notice(request):
    """Copyright Policy & Republication Rules page."""
    return render(request, 'legal/copyright.html')


def about(request):
    """About Us & Editorial Team page."""
    return render(request, 'legal/about.html')


def contact(request):
    """Contact page & Form handler.

    TODO: Replace the logger call with Django send_mail / a ContactMessage
    model once the email backend or persistence layer is configured.
    """

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        subject = request.POST.get('subject', '').strip()
        message_text = request.POST.get('message', '').strip()

        if name and email and message_text:
            # Log the contact request so it is not silently lost.
            # Replace this with send_mail() or a ContactMessage.objects.create() call.
            logger.info(
                "Contact form submission — from: %s <%s>, subject: %r",
                name,
                email,
                subject or '(no subject)',
            )
            messages.warning(
                request,
                'Το μήνυμά σας ελήφθη αλλά η αποστολή email δεν είναι ακόμη διαθέσιμη. Επικοινωνήστε μαζί μας απευθείας στο email.'
            )
            return redirect('contact')
        else:
            messages.error(request, 'Παρακαλούμε συμπληρώστε όλα τα απαιτούμενα πεδία της φόρμας.')

    return render(request, 'legal/contact.html')

