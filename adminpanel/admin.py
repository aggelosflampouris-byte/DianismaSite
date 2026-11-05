"""
Django admin registrations for DIANISMA.GR models.
"""
from django.contrib import admin
from .models import Category, Article, Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'profession', 'topic_interest', 'status', 'is_verified_contributor', 'created_at')
    list_filter = ('status', 'is_verified_contributor')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'user__email', 'profession')
    actions = ['approve_contributors', 'reject_contributors']

    @admin.action(description='Έγκριση επιλεγμένων συντακτών')
    def approve_contributors(self, request, queryset):
        queryset.update(status=Profile.STATUS_APPROVED, is_verified_contributor=True)

    @admin.action(description='Απόρριψη επιλεγμένων συντακτών')
    def reject_contributors(self, request, queryset):
        queryset.update(status=Profile.STATUS_REJECTED, is_verified_contributor=False)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'order')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('order', 'name')


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'display_author_name', 'status', 'is_featured', 'views_count', 'created_at')
    list_filter = ('status', 'is_featured', 'category')
    search_fields = ('title', 'excerpt', 'content', 'author_name')
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'created_at'
    actions = ['publish_articles', 'draft_articles']

    @admin.action(description='Δημοσίευση επιλεγμένων άρθρων')
    def publish_articles(self, request, queryset):
        from django.utils import timezone
        now = timezone.now()
        # Set published_at for articles that don't yet have it, mirroring Article.save() logic.
        queryset.filter(published_at__isnull=True).update(published_at=now)
        queryset.update(status=Article.STATUS_PUBLISHED)

    @admin.action(description='Μετατροπή σε Πρόχειρα')
    def draft_articles(self, request, queryset):
        queryset.update(status=Article.STATUS_DRAFT)

