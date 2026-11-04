"""
Django views for DIANISMA.GR Custom Boss Admin Dashboard (/adminpanel/).
Full CMS: articles, users, categories, activity log, settings.
"""
import uuid
import json

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout, update_session_auth_hash
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, Count, Q
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from .models import Article, Category, AuthorApplication, Profile

User = get_user_model()


def _parse_article_post(post: dict, files, existing_pdf=None) -> tuple:
    """
    Parse and validate article POST data shared by article_create and article_edit.

    Args:
        post: request.POST QueryDict.
        files: request.FILES QueryDict.
        existing_pdf: The existing pdf_file on the article being edited, or None
                      when creating a new article.

    Returns:
        (parsed: dict, errors: dict) — errors is empty when validation passes.
    """
    errors: dict = {}

    title = post.get('title', '').strip()
    cat_slug = post.get('category', '').strip()
    author_name = post.get('author_name', '').strip()
    excerpt = post.get('excerpt', '').strip()
    content = post.get('content', '').strip()
    lead_image_url = post.get('lead_image_url', '').strip()
    status_val = post.get('status', Article.STATUS_DRAFT).strip()
    is_featured = post.get('is_featured') == 'on'

    try:
        read_time = int(post.get('read_time_minutes', 5))
    except (ValueError, TypeError):
        read_time = 5

    if not title:
        errors['title'] = 'Ο τίτλος είναι υποχρεωτικός.'
    if not excerpt:
        errors['excerpt'] = 'Η σύνοψη είναι υποχρεωτική.'
    if not content and not files.get('pdf_file') and not existing_pdf:
        errors['content'] = 'Το κυρίως κείμενο ή το PDF είναι υποχρεωτικό.'

    category = Category.objects.filter(slug=cat_slug).first()
    if not category:
        errors['category'] = 'Επιλέξτε έγκυρη κατηγορία.'

    parsed = {
        'title': title,
        'category': category,
        'author_name': author_name,
        'excerpt': excerpt,
        'content': content,
        'lead_image_url': lead_image_url,
        'status_val': status_val,
        'is_featured': is_featured,
        'read_time': read_time,
    }
    return parsed, errors


# ─── Auth ──────────────────────────────────────────────────────────────────────

def login_view(request):
    """Custom admin login view."""
    if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
        return redirect('adminpanel:dashboard')

    error = None
    next_url = request.GET.get('next') or request.POST.get('next') or '/adminpanel/'

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if user.is_staff or user.is_superuser:
                auth_login(request, user)
                return redirect(next_url)
            else:
                error = 'Δεν διαθέτετε δικαιώματα διαχειριστή (staff access).'
        else:
            error = 'Λάθος όνομα χρήστη ή κωδικός πρόσβασης.'

    return render(request, 'adminpage/login.html', {
        'error': error,
        'next': next_url,
    })


def logout_view(request):
    """Custom admin logout view. Requires POST to prevent CSRF-based logout via GET."""
    if request.method != 'POST':
        return redirect('adminpanel:dashboard')
    auth_logout(request)
    return redirect('adminpanel:login')


# ─── Dashboard ─────────────────────────────────────────────────────────────────

@staff_member_required(login_url='/adminpanel/login/')
def dashboard(request):
    """Boss Dashboard overview with real KPIs, charts, and activity feed."""
    total_articles = Article.objects.count()
    published_articles = Article.objects.filter(status=Article.STATUS_PUBLISHED).count()
    draft_articles = Article.objects.filter(status=Article.STATUS_DRAFT).count()
    pending_articles = Article.objects.filter(status=Article.STATUS_PENDING).count()
    total_views = Article.objects.aggregate(Sum('views_count'))['views_count__sum'] or 0
    total_authors = Profile.objects.filter(status=Profile.STATUS_APPROVED).count()
    total_users = User.objects.count()
    pending_apps = AuthorApplication.objects.filter(status=AuthorApplication.STATUS_PENDING).count()

    # Category distribution
    cat_data = []
    all_cats = Category.objects.annotate(art_count=Count('articles')).order_by('order')
    for cat in all_cats:
        pct = round((cat.art_count / total_articles * 100)) if total_articles > 0 else 0
        cat_data.append({'name': cat.name, 'slug': cat.slug, 'count': cat.art_count, 'pct': pct})

    # Top articles by views
    top_articles = Article.objects.filter(
        status=Article.STATUS_PUBLISHED
    ).select_related('category').order_by('-views_count')[:8]

    # Recent articles & applications
    recent_articles = Article.objects.select_related('category', 'author').order_by('-created_at')[:8]
    recent_applications = AuthorApplication.objects.order_by('-created_at')[:5]

    # Per-author stats
    author_stats = (
        Article.objects.filter(status=Article.STATUS_PUBLISHED)
        .values('author_name')
        .annotate(count=Count('id'), views=Sum('views_count'))
        .order_by('-views')[:6]
    )

    kpis = {
        'total_articles': total_articles,
        'published_articles': published_articles,
        'draft_articles': draft_articles,
        'pending_articles': pending_articles,
        'total_views': total_views,
        'total_authors': total_authors,
        'total_users': total_users,
        'pending_applications': pending_apps,
        'category_data': cat_data,
        'top_articles': top_articles,
        'recent_articles': recent_articles,
        'recent_applications': recent_applications,
        'author_stats': author_stats,
    }

    return render(request, 'adminpage/dashboard.html', {
        'kpis': kpis,
        'active_page': 'dashboard',
    })


# ─── Articles ──────────────────────────────────────────────────────────────────

@staff_member_required(login_url='/adminpanel/login/')
def articles_list(request):
    """List of all articles with filtering, searching, and batch controls."""
    query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip()
    category_filter = request.GET.get('category', '').strip()

    qs = Article.objects.select_related('category', 'author').order_by('-created_at')

    if query:
        qs = qs.filter(Q(title__icontains=query) | Q(author_name__icontains=query) | Q(excerpt__icontains=query))
    if status_filter:
        qs = qs.filter(status=status_filter)
    if category_filter:
        qs = qs.filter(category__slug=category_filter)

    categories = Category.objects.all().order_by('order', 'name')

    return render(request, 'adminpage/articles_list.html', {
        'articles': qs,
        'categories': categories,
        'query': query,
        'status_filter': status_filter,
        'category_filter': category_filter,
        'active_page': 'articles',
    })


@staff_member_required(login_url='/adminpanel/login/')
def article_create(request):
    """Create a new editorial or community article."""
    categories = Category.objects.all().order_by('order', 'name')
    errors = {}

    if request.method == 'POST':
        parsed, errors = _parse_article_post(request.POST, request.FILES)

        if not errors:
            article = Article.objects.create(
                title=parsed['title'],
                category=parsed['category'],
                author=request.user,
                author_name=parsed['author_name'] or request.user.get_full_name() or request.user.username,
                excerpt=parsed['excerpt'],
                content=parsed['content'],
                pdf_file=request.FILES.get('pdf_file'),
                lead_image_url=parsed['lead_image_url'],
                read_time_minutes=parsed['read_time'],
                status=parsed['status_val'],
                is_featured=parsed['is_featured'],
                published_at=timezone.now() if parsed['status_val'] == Article.STATUS_PUBLISHED else None,
            )
            messages.success(request, f'Το άρθρο «{article.title}» δημιουργήθηκε επιτυχώς!')
            return redirect('adminpanel:articles_list')

    return render(request, 'adminpage/article_form.html', {
        'is_edit': False,
        'categories': categories,
        'status_choices': Article.STATUS_CHOICES,
        'form_data': request.POST if request.method == 'POST' else {},
        'errors': errors,
        'active_page': 'articles',
    })


@staff_member_required(login_url='/adminpanel/login/')
def article_edit(request, article_id):
    """Edit an existing article."""
    article = get_object_or_404(Article, id=article_id)
    categories = Category.objects.all().order_by('order', 'name')
    errors = {}

    if request.method == 'POST':
        parsed, errors = _parse_article_post(
            request.POST, request.FILES, existing_pdf=article.pdf_file
        )

        if not errors:
            article.title = parsed['title']
            article.category = parsed['category']
            if parsed['author_name']:
                article.author_name = parsed['author_name']
            article.excerpt = parsed['excerpt']
            article.content = parsed['content']
            if 'pdf_file' in request.FILES:
                article.pdf_file = request.FILES['pdf_file']
            article.lead_image_url = parsed['lead_image_url']
            article.read_time_minutes = parsed['read_time']
            article.status = parsed['status_val']
            article.is_featured = parsed['is_featured']
            if parsed['status_val'] == Article.STATUS_PUBLISHED and not article.published_at:
                article.published_at = timezone.now()
            article.save()
            messages.success(request, f'Το άρθρο «{article.title}» ενημερώθηκε!')
            return redirect('adminpanel:articles_list')

    form_data = {
        'title': article.title,
        'category': article.category.slug if article.category else '',
        'author_name': article.author_name,
        'excerpt': article.excerpt,
        'content': article.content,
        'lead_image_url': article.lead_image_url,
        'read_time_minutes': article.read_time_minutes,
        'status': article.status,
        'is_featured': article.is_featured,
    }

    return render(request, 'adminpage/article_form.html', {
        'is_edit': True,
        'article': article,
        'categories': categories,
        'status_choices': Article.STATUS_CHOICES,
        'form_data': request.POST if request.method == 'POST' else form_data,
        'errors': errors,
        'active_page': 'articles',
    })


@staff_member_required(login_url='/adminpanel/login/')
def article_delete(request, article_id):
    """Delete an article (POST only)."""
    if request.method == 'POST':
        article = get_object_or_404(Article, id=article_id)
        title = article.title
        article.delete()
        messages.success(request, f'Το άρθρο «{title}» διαγράφηκε.')
    return redirect('adminpanel:articles_list')


@staff_member_required(login_url='/adminpanel/login/')
def article_toggle_status(request, article_id):
    """Toggle article status between published and draft."""
    if request.method == 'POST':
        article = get_object_or_404(Article, id=article_id)
        if article.status == Article.STATUS_PUBLISHED:
            article.status = Article.STATUS_DRAFT
        else:
            article.status = Article.STATUS_PUBLISHED
            if not article.published_at:
                article.published_at = timezone.now()
        article.save()
        messages.success(request, f'Η κατάσταση του άρθρου άλλαξε σε {article.get_status_display()}.')
    return redirect('adminpanel:articles_list')


@staff_member_required(login_url='/adminpanel/login/')
def article_toggle_featured(request, article_id):
    """Toggle is_featured flag on an article."""
    if request.method == 'POST':
        article = get_object_or_404(Article, id=article_id)
        article.is_featured = not article.is_featured
        article.save()
        state = 'Featured ✅' if article.is_featured else 'κανονικό'
        messages.success(request, f'Το άρθρο «{article.title}» ορίστηκε ως {state}.')
    return redirect('adminpanel:articles_list')


# ─── Authors / Applications ────────────────────────────────────────────────────

@staff_member_required(login_url='/adminpanel/login/')
def authors_list(request):
    """List of all contributor applications for Writers."""
    status_filter = request.GET.get('status', '').strip()
    qs = AuthorApplication.objects.all().order_by('-created_at')

    if status_filter:
        qs = qs.filter(status=status_filter)

    pending_count = AuthorApplication.objects.filter(status=AuthorApplication.STATUS_PENDING).count()

    return render(request, 'adminpage/authors_list.html', {
        'applications': qs,
        'status_filter': status_filter,
        'pending_count': pending_count,
        'active_page': 'authors',
    })


@staff_member_required(login_url='/adminpanel/login/')
def author_detail(request, app_id):
    """Review dossier for a single author application."""
    application = get_object_or_404(AuthorApplication, id=app_id)
    decision_choices = [
        ('approved', '✅ Έγκριση Συντάκτη'),
        ('rejected', '❌ Απόρριψη'),
        ('pending', '⏳ Παραμονή σε Εκκρεμότητα'),
    ]
    return render(request, 'adminpage/author_detail.html', {
        'application': application,
        'decision_choices': decision_choices,
        'active_page': 'authors',
    })


@staff_member_required(login_url='/adminpanel/login/')
def author_review(request, app_id):
    """Submit review decision for author application."""
    if request.method == 'POST':
        application = get_object_or_404(AuthorApplication, id=app_id)
        decision = request.POST.get('decision', '').strip()
        admin_notes = request.POST.get('admin_notes', '').strip()

        if decision in ['approved', 'rejected', 'pending']:
            application.status = decision
            application.admin_notes = admin_notes
            application.reviewed_by = request.user
            application.reviewed_at = timezone.now()
            application.save()

            if decision == 'approved':
                # Derive a unique username from the email prefix, avoiding collisions.
                base_username = application.email.split('@')[0]
                username = base_username
                while User.objects.filter(username=username).exists():
                    username = f"{base_username}_{uuid.uuid4().hex[:6]}"

                user, _ = User.objects.get_or_create(
                    email=application.email,
                    defaults={
                        'username': username,
                        'first_name': application.full_name.split()[0],
                        'last_name': (
                            " ".join(application.full_name.split()[1:])
                            if len(application.full_name.split()) > 1
                            else ''
                        ),
                    }
                )
                profile, _ = Profile.objects.get_or_create(user=user)
                profile.profession = application.profession
                profile.topic_interest = application.topic_interest
                profile.bio = application.bio
                profile.status = Profile.STATUS_APPROVED
                profile.is_verified_contributor = True
                profile.save()

            messages.success(request, f'Η απόφαση για την αίτηση του/της {application.full_name} καταχωρήθηκε ({decision}).')
            return redirect('adminpanel:author_detail', app_id=app_id)

    return redirect('adminpanel:authors_list')


# ─── Users Management ──────────────────────────────────────────────────────────

@staff_member_required(login_url='/adminpanel/login/')
def users_list(request):
    """Boss-only: list all registered users with management controls."""
    if not request.user.is_superuser:
        messages.error(request, 'Μόνο ο Super Admin έχει πρόσβαση σε αυτή τη σελίδα.')
        return redirect('adminpanel:dashboard')

    query = request.GET.get('q', '').strip()
    qs = User.objects.select_related('profile').order_by('-date_joined')
    if query:
        qs = qs.filter(Q(username__icontains=query) | Q(email__icontains=query) |
                       Q(first_name__icontains=query) | Q(last_name__icontains=query))

    return render(request, 'adminpage/users_list.html', {
        'users': qs,
        'query': query,
        'active_page': 'users',
    })


@staff_member_required(login_url='/adminpanel/login/')
def user_toggle_active(request, user_id):
    """Toggle active/blocked state for a user (superuser only)."""
    if not request.user.is_superuser:
        messages.error(request, 'Δεν έχετε δικαίωμα εκτέλεσης αυτής της ενέργειας.')
        return redirect('adminpanel:dashboard')
    if request.method == 'POST':
        target = get_object_or_404(User, id=user_id)
        if target == request.user:
            messages.warning(request, 'Δεν μπορείτε να απενεργοποιήσετε τον δικό σας λογαριασμό.')
        else:
            target.is_active = not target.is_active
            target.save()
            state = 'ενεργοποιήθηκε' if target.is_active else 'απενεργοποιήθηκε'
            messages.success(request, f'Ο χρήστης {target.username} {state}.')
    return redirect('adminpanel:users_list')


@staff_member_required(login_url='/adminpanel/login/')
def user_create(request):
    """Create a new staff/author user (superuser only)."""
    if not request.user.is_superuser:
        messages.error(request, 'Δεν έχετε δικαίωμα εκτέλεσης αυτής της ενέργειας.')
        return redirect('adminpanel:dashboard')

    errors = {}
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        password = request.POST.get('password', '').strip()
        role = request.POST.get('role', 'author')

        if not username:
            errors['username'] = 'Το username είναι υποχρεωτικό.'
        elif User.objects.filter(username=username).exists():
            errors['username'] = 'Το username χρησιμοποιείται ήδη.'
        if not password or len(password) < 8:
            errors['password'] = 'Ο κωδικός πρέπει να έχει τουλάχιστον 8 χαρακτήρες.'

        if not errors:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
            )
            if role == 'superadmin':
                user.is_superuser = True
                user.is_staff = True
            elif role == 'editor':
                user.is_staff = True
            user.save()
            # Create profile and approve if author/editor
            profile = Profile.objects.get_or_create(user=user)[0]
            if role in ('editor', 'author'):
                profile.status = Profile.STATUS_APPROVED
                profile.is_verified_contributor = True
                profile.save()
            messages.success(request, f'Ο χρήστης «{username}» δημιουργήθηκε επιτυχώς!')
            return redirect('adminpanel:users_list')

    return render(request, 'adminpage/user_form.html', {
        'is_edit': False,
        'form_data': request.POST if request.method == 'POST' else {},
        'errors': errors,
        'active_page': 'users',
    })


@staff_member_required(login_url='/adminpanel/login/')
def user_edit(request, user_id):
    """Edit an existing user (superuser only)."""
    if not request.user.is_superuser:
        messages.error(request, 'Δεν έχετε δικαίωμα εκτέλεσης αυτής της ενέργειας.')
        return redirect('adminpanel:dashboard')

    target_user = get_object_or_404(User, id=user_id)
    errors = {}

    if target_user.is_superuser:
        current_role = 'superadmin'
    elif target_user.is_staff:
        current_role = 'editor'
    else:
        current_role = 'author'

    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        role = request.POST.get('role', current_role)

        target_user.first_name = first_name
        target_user.last_name = last_name
        target_user.email = email

        if role == 'superadmin':
            target_user.is_superuser = True
            target_user.is_staff = True
        elif role == 'editor':
            target_user.is_superuser = False
            target_user.is_staff = True
        else:
            target_user.is_superuser = False
            target_user.is_staff = False

        target_user.save()
        messages.success(request, f'Τα στοιχεία του χρήστη «{target_user.username}» ενημερώθηκαν.')
        return redirect('adminpanel:users_list')

    form_data = {
        'username': target_user.username,
        'email': target_user.email,
        'first_name': target_user.first_name,
        'last_name': target_user.last_name,
        'role': current_role,
    }

    return render(request, 'adminpage/user_form.html', {
        'is_edit': True,
        'target_user': target_user,
        'form_data': form_data,
        'errors': errors,
        'active_page': 'users',
    })


@staff_member_required(login_url='/adminpanel/login/')
@require_POST
def api_user_change_password(request, user_id):
    """API endpoint: Securely change a user's password (superuser only)."""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'Δεν έχετε δικαίωμα εκτέλεσης αυτής της ενέργειας.'}, status=403)

    try:
        target_user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Ο χρήστης δεν βρέθηκε.'}, status=404)

    if request.content_type == 'application/json':
        try:
            payload = json.loads(request.body.decode('utf-8'))
        except (ValueError, UnicodeDecodeError):
            return JsonResponse({'success': False, 'error': 'Μη έγκυρη μορφή δεδομένων (Invalid JSON).'}, status=400)
    else:
        payload = request.POST

    new_password = payload.get('new_password', '').strip()
    confirm_password = payload.get('confirm_password', '').strip()

    if not new_password or not confirm_password:
        return JsonResponse({'success': False, 'error': 'Παρακαλώ συμπληρώστε και τα δύο πεδία κωδικού.'}, status=400)

    if len(new_password) < 8:
        return JsonResponse({'success': False, 'error': 'Ο κωδικός πρόσβασης πρέπει να αποτελείται από τουλάχιστον 8 χαρακτήρες.'}, status=400)

    if new_password != confirm_password:
        return JsonResponse({'success': False, 'error': 'Οι κωδικοί πρόσβασης δεν ταιριάζουν.'}, status=400)

    target_user.set_password(new_password)
    target_user.save()

    if request.user.id == target_user.id:
        update_session_auth_hash(request, target_user)

    return JsonResponse({
        'success': True,
        'message': f'Ο κωδικός πρόσβασης για τον χρήστη «{target_user.username}» άλλαξε επιτυχώς!'
    })


# ─── Categories ────────────────────────────────────────────────────────────────

@staff_member_required(login_url='/adminpanel/login/')
def categories_list(request):
    """Manage site categories."""
    cats = Category.objects.annotate(art_count=Count('articles')).order_by('order', 'name')
    return render(request, 'adminpage/categories_list.html', {
        'categories': cats,
        'active_page': 'categories',
    })


@staff_member_required(login_url='/adminpanel/login/')
def category_create(request):
    """Create a new category."""
    errors = {}
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        slug = request.POST.get('slug', '').strip()
        description = request.POST.get('description', '').strip()
        try:
            order = int(request.POST.get('order', 0))
        except ValueError:
            order = 0

        if not name:
            errors['name'] = 'Το όνομα κατηγορίας είναι υποχρεωτικό.'

        if not errors:
            cat = Category(name=name, description=description, order=order)
            if slug:
                cat.slug = slug
            cat.save()
            messages.success(request, f'Η κατηγορία «{name}» δημιουργήθηκε.')
            return redirect('adminpanel:categories_list')

    return render(request, 'adminpage/category_form.html', {
        'is_edit': False,
        'form_data': request.POST if request.method == 'POST' else {},
        'errors': errors,
        'active_page': 'categories',
    })


@staff_member_required(login_url='/adminpanel/login/')
def category_edit(request, cat_id):
    """Edit an existing category."""
    category = get_object_or_404(Category, id=cat_id)
    errors = {}

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        try:
            order = int(request.POST.get('order', 0))
        except ValueError:
            order = 0

        if not name:
            errors['name'] = 'Το όνομα κατηγορίας είναι υποχρεωτικό.'

        if not errors:
            category.name = name
            category.description = description
            category.order = order
            category.save()
            messages.success(request, f'Η κατηγορία «{name}» ενημερώθηκε.')
            return redirect('adminpanel:categories_list')

    form_data = {
        'name': category.name,
        'slug': category.slug,
        'description': category.description,
        'order': category.order,
    }
    return render(request, 'adminpage/category_form.html', {
        'is_edit': True,
        'category': category,
        'form_data': request.POST if request.method == 'POST' else form_data,
        'errors': errors,
        'active_page': 'categories',
    })


# ─── Settings ──────────────────────────────────────────────────────────────────

@staff_member_required(login_url='/adminpanel/login/')
def site_settings(request):
    """Global site settings page (SEO, social, layout).

    NOTE: Persistence is not yet implemented. POST requests are rejected
    with a clear error until a SiteSettings model or similar backing store
    is added.
    """
    if not request.user.is_superuser:
        messages.error(request, 'Μόνο ο Super Admin έχει πρόσβαση στις ρυθμίσεις.')
        return redirect('adminpanel:dashboard')

    if request.method == 'POST':
        # TODO: Implement a SiteSettings model and persist values here.
        messages.error(request, 'Η αποθήκευση ρυθμίσεων δεν είναι ακόμη διαθέσιμη.')
        return redirect('adminpanel:site_settings')

    return render(request, 'adminpage/site_settings.html', {
        'active_page': 'settings',
    })
