"""
Django test suite for DIANISMA.GR portal routes and dialogues contributor workflow.
"""
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from adminpanel.models import Category, Article, Profile, AuthorApplication

User = get_user_model()


class PortalIntegrationTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(name='Πολιτική', slug='politiki')
        self.article = Article.objects.create(
            title='Δοκιμαστικό Άρθρο',
            category=self.category,
            excerpt='Σύνοψη άρθρου',
            content='<p>Κείμενο</p>',
            status=Article.STATUS_PUBLISHED
        )
        self.contributor = User.objects.create_user(
            username='test_contributor',
            password='password123'
        )
        self.contributor.profile.status = Profile.STATUS_APPROVED
        self.contributor.profile.is_verified_contributor = True
        self.contributor.profile.save()

    def test_public_routes(self):
        routes = ['/', '/politiki/', '/oikonomia/', '/koinonia/', '/analyseis/', '/apopseis/', '/dialogues/']
        for r in routes:
            resp = self.client.get(r)
            self.assertEqual(resp.status_code, 200, f"Failed route {r}")

    def test_article_detail(self):
        resp = self.client.get(f'/article/{self.article.slug}/')
        self.assertEqual(resp.status_code, 200)

    def test_dialogues_application_flow(self):
        post_data = {
            'full_name': 'Δοκιμαστικός Αιτών',
            'email': 'applicant@example.com',
            'profession': 'Δημοσιογράφος',
            'topic_interest': 'Πολιτικός Διάλογος & Θεσμοί',
            'bio': 'Βιογραφικό',
            'sample_text': 'Δείγμα κειμένου',
        }
        resp = self.client.post('/dialogues/apply/', post_data, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(AuthorApplication.objects.filter(email='applicant@example.com').exists())

    def test_contributor_submit_permission(self):
        # Anonymous should redirect
        resp_anon = self.client.get('/dialogues/submit/')
        self.assertEqual(resp_anon.status_code, 302)

        # Logged in approved contributor
        self.client.force_login(self.contributor)
        resp_auth = self.client.get('/dialogues/submit/')
        self.assertEqual(resp_auth.status_code, 200)

        # Submit article
        submit_data = {
            'title': 'Νέο Άρθρο Κοινότητας',
            'category': self.category.id,
            'excerpt': 'Σύνοψη νέου άρθρου',
            'content': '<p>Περιεχόμενο</p>',
            'read_time_minutes': 5,
        }
        resp_post = self.client.post('/dialogues/submit/', submit_data, follow=True)
        self.assertEqual(resp_post.status_code, 200)
        self.assertTrue(Article.objects.filter(title='Νέο Άρθρο Κοινότητας', status=Article.STATUS_PENDING).exists())
