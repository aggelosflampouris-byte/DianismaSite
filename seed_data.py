"""
Seed script to populate initial categories, articles, users and applications in DIANISMA.GR database.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dianisma_project.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone
from adminpanel.models import Category, Article, Profile, AuthorApplication

User = get_user_model()


def seed():
    print("[+] Seeding DIANISMA.GR database...")

    # 1. Create Admin Superuser
    admin_user, created = User.objects.get_or_create(username='admin')
    if created:
        admin_user.set_password('dianisma2024')
        admin_user.is_superuser = True
        admin_user.is_staff = True
        admin_user.email = 'admin@dianisma.gr'
        admin_user.first_name = 'Διαχειριστής'
        admin_user.last_name = 'Dianisma'
        admin_user.save()
        print("  [OK] Superuser 'admin' created.")
    else:
        admin_user.set_password('dianisma2024')
        admin_user.is_superuser = True
        admin_user.is_staff = True
        admin_user.save()
        print("  [OK] Superuser 'admin' updated.")

    # 2. Create Contributors
    user_nikos, _ = User.objects.get_or_create(username='nikos_kalo', defaults={
        'first_name': 'Νίκος',
        'last_name': 'Καλοκαιρινός',
        'email': 'n.kalokairinos@dianisma.gr'
    })
    user_nikos.set_password('dianisma2024')
    user_nikos.save()
    profile_nikos, _ = Profile.objects.get_or_create(user=user_nikos)
    profile_nikos.profession = 'Αρχιτέκτων - Πολεοδόμος'
    profile_nikos.topic_interest = 'Περιβάλλον & Πόλεις'
    profile_nikos.bio = 'Ειδικός σε θέματα βιώσιμης αστικής κινητικότητας και συμμετοχικού σχεδιασμού γειτονιάς.'
    profile_nikos.avatar_url = 'https://i.pravatar.cc/150?img=68'
    profile_nikos.status = Profile.STATUS_APPROVED
    profile_nikos.is_verified_contributor = True
    profile_nikos.save()

    user_evgenia, _ = User.objects.get_or_create(username='evgenia_mbali', defaults={
        'first_name': 'Ευγενία',
        'last_name': 'Μπαλή',
        'email': 'e.mbali@dianisma.gr'
    })
    user_evgenia.set_password('dianisma2024')
    user_evgenia.save()
    profile_evgenia, _ = Profile.objects.get_or_create(user=user_evgenia)
    profile_evgenia.profession = 'Κοινωνιολόγος & Ερευνήτρια'
    profile_evgenia.topic_interest = 'Κοινωνικές Πρωτοβουλίες'
    profile_evgenia.bio = 'Ερευνήτρια με έμφαση στις ανισότητες στην ψηφιακή εκπαίδευση και τη νεανική απασχόληση.'
    profile_evgenia.avatar_url = 'https://i.pravatar.cc/150?img=47'
    profile_evgenia.status = Profile.STATUS_APPROVED
    profile_evgenia.is_verified_contributor = True
    profile_evgenia.save()

    # 3. Create Categories
    categories_data = [
        ('Πολιτική', 'politiki', 'Έγκυρη ενημέρωση, θεσμικές αναλύσεις και παρασκήνιο από το ελληνικό και ευρωπαϊκό πολιτικό γίγνεσθαι.', 1),
        ('Οικονομία', 'oikonomia', 'Μακροοικονομία, επιχειρήσεις, χρηματαγορές και η νέα ψηφιακή οικονομία.', 2),
        ('Κοινωνία', 'koinonia', 'Παιδεία, υγεία, περιβάλλον και τα μεγάλα κοινωνικά ζητήματα της εποχής.', 3),
        ('Αναλύσεις', 'analyseis', 'Εμπεριστατωμένες αναλύσεις, ερευνητικά αφιερώματα και δεδομένα βάθους.', 4),
        ('Απόψεις', 'apopseis', 'Αρθρογραφία, κριτική σκέψη και παρεμβάσεις από κορυφαίους αναλυτές.', 5),
        ('Dialogues', 'dialogues', 'Η ανοιχτή πλατφόρμα των πολιτών, της ακαδημαϊκής κοινότητας και των δημιουργών.', 6),
    ]

    cats = {}
    for name, slug, desc, order in categories_data:
        cat, _ = Category.objects.get_or_create(slug=slug, defaults={'name': name, 'description': desc, 'order': order})
        cats[slug] = cat
    print(f"  [OK] {len(cats)} Categories initialized.")

    # 4. Create Articles
    articles_data = [
        # Politiki
        {
            'title': 'Αναδιάρθρωση των Θεσμών: Το νέο νομοθετικό πλαίσιο για τη διαφάνεια στη δημόσια διοίκηση',
            'category': cats['politiki'],
            'author_name': 'Δημήτρης Βασιλείου',
            'author_title': 'Πολιτικός Συντάκτης',
            'excerpt': 'Το υπό διαβούλευση νομοσχέδιο εισάγει ριζικές αλλαγές στον τρόπο λειτουργίας των ανεξάρτητων αρχών και τον έλεγχο των δημοσίων συμβάσεων.',
            'content': '<p>Το νέο σχέδιο νόμου θέτει στο επίκεντρο την ψηφιοποίηση των διαδικασιών ελέγχου...</p>',
            'lead_image_url': 'https://images.unsplash.com/photo-1541872703-74c5e44368f9?auto=format&fit=crop&q=80&w=1200',
            'read_time_minutes': 6,
            'is_featured': True,
            'views_count': 1420,
        },
        {
            'title': 'Σύνοδος Κορυφής Ε.Ε.: Οι κρίσιμες ισορροπίες στο νέο ευρωπαϊκό δημοσιονομικό σύμφωνο',
            'category': cats['politiki'],
            'author_name': 'Ελένη Κωνσταντίνου',
            'author_title': 'Ανταποκρίτρια Βρυξελλών',
            'excerpt': 'Μαραθώνιες διαπραγματεύσεις στις Βρυξέλλες για τα περιθώρια εθνικών επενδύσεων στην πράσινη μετάβαση και την άμυνα.',
            'content': '<p>Στο τραπέζι των συνομιλιών τέθηκαν οι κανόνες για τα ελλείμματα...</p>',
            'lead_image_url': 'https://images.unsplash.com/photo-1577962917302-cd874c4e31d2?auto=format&fit=crop&q=80&w=800',
            'read_time_minutes': 5,
            'views_count': 890,
        },
        # Oikonomia
        {
            'title': 'Οικονομία: Η πρόκληση της βιώσιμης ανάπτυξης και η ανάκαμψη των επενδύσεων',
            'category': cats['oikonomia'],
            'author_name': 'Νίκος Παπαδόπουλος',
            'author_title': 'Οικονομικός Αναλυτής',
            'excerpt': 'Μια βαθιά ανάλυση των νέων μακροοικονομικών δεδομένων, των επιτοκίων και της ανταγωνιστικότητας της ελληνικής οικονομίας.',
            'content': '<p>Η πορεία του πληθωρισμού και η εξέλιξη των διεθνών επιτοκίων...</p>',
            'lead_image_url': 'https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?auto=format&fit=crop&q=80&w=1200',
            'read_time_minutes': 8,
            'is_featured': True,
            'views_count': 2340,
        },
        {
            'title': 'Χρηματιστήριο Αθηνών: Νέο υψηλό δεκαετίας με οδηγό τις τράπεζες και την ενέργεια',
            'category': cats['oikonomia'],
            'author_name': 'Μάριος Γεωργακόπουλος',
            'author_title': 'Αναλυτής Αγορών',
            'excerpt': 'Ισχυρές εισροές ξένων κεφαλαίων και έντονο ενδιαφέρον για τα εταιρικά ομόλογα υψηλής απόδοσης.',
            'content': '<p>Η ανοδική πορεία της κεφαλαιαγοράς αντανακλά τη βελτίωση του κλίματος...</p>',
            'lead_image_url': 'https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?auto=format&fit=crop&q=80&w=800',
            'read_time_minutes': 4,
            'views_count': 1150,
        },
        # Koinonia
        {
            'title': 'Ψηφιακό Σχολείο και Κοινωνικές Ανισότητες: Η πρόκληση της νέας γενιάς στην παιδεία',
            'category': cats['koinonia'],
            'author_name': 'Σοφία Αντωνιάδου',
            'author_title': 'Συντάκτρια Παιδείας',
            'excerpt': 'Πώς η ενσωμάτωση εργαλείων τεχνητής νοημοσύνης και διαδραστικών συστημάτων επηρεάζει την εκπαιδευτική διαδικασία στα σχολεία.',
            'content': '<p>Η τεχνολογική πρόοδος φέρνει νέες ευκαιρίες αλλά και κινδύνους διεύρυνσης του χάσματος...</p>',
            'lead_image_url': 'https://images.unsplash.com/photo-1427504494785-3a9ca7044f45?auto=format&fit=crop&q=80&w=1200',
            'read_time_minutes': 7,
            'is_featured': True,
            'views_count': 1890,
        },
        {
            'title': 'Βιώσιμες Πόλεις: Το παράδειγμα ανάπλασης κοινόχρηστων χώρων και μικροκινητικότητας',
            'category': cats['koinonia'],
            'author_name': 'Γιώργος Λεοντής',
            'author_title': 'Συντάκτης Περιβάλλοντος',
            'excerpt': 'Πιλοτικά προγράμματα πεζοδρομήσεων και δικτύων ποδηλατοδρόμων αλλάζουν τη φυσιογνωμία των ελληνικών αστικών κέντρων.',
            'content': '<p>Η αναβάθμιση του αστικού περιβάλλοντος απαιτεί ολοκληρωμένο σχεδιασμό...</p>',
            'lead_image_url': 'https://images.unsplash.com/photo-1477959858617-67f30bc75b82?auto=format&fit=crop&q=80&w=800',
            'read_time_minutes': 5,
            'views_count': 940,
        },
        # Analyseis
        {
            'title': 'Γεωπολιτική Αρχιτεκτονική στην Ανατολική Μεσόγειο: Ενεργειακοί διάδρομοι και συμμαχίες',
            'category': cats['analyseis'],
            'author_name': 'Δρ. Αλέξανδρος Φωκάς',
            'author_title': 'Καθηγητής Διεθνών Σχέσεων',
            'excerpt': 'Μια εκτενής ανάλυση των στρατηγικών συμφερόντων, των υποθαλάσσιων καλωδίων διασύνδεσης και των νέων ισορροπιών ισχύος.',
            'content': '<p>Η ευρύτερη περιφέρεια της Ανατολικής Μεσογείου εισέρχεται σε φάση αναδιάταξης...</p>',
            'lead_image_url': 'https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&q=80&w=1200',
            'read_time_minutes': 12,
            'is_featured': True,
            'views_count': 3100,
        },
        # Apopseis
        {
            'title': 'Η Δημοκρατία στην Εποχή των Αλγορίθμων: Ποιος αποφασίζει για τον δημόσιο λόγο;',
            'category': cats['apopseis'],
            'author_name': 'Μιχαήλ Θεοδωρίδης',
            'author_title': 'Αρθρογράφος / Φιλόσοφος Δικαίου',
            'excerpt': 'Όταν τα κοινωνικά δίκτυα καθορίζουν την ατζέντα, ο κριτικός στοχασμός και ο σεβασμός στην αντίθετη άποψη καθίστανται υπαρξιακά αγαθά.',
            'content': '<p>Ο κατακερματισμός της δημόσιας σφαίρας σε ψηφιακούς θαλάμους αντήχησης...</p>',
            'lead_image_url': 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&q=80&w=800',
            'read_time_minutes': 6,
            'is_featured': True,
            'views_count': 1670,
        },
        # Dialogues
        {
            'title': 'Η επανίδρυση της τοπικής δημοκρατίας: Πώς οι συνελεύσεις γειτονιάς μπορούν να αλλάξουν τις πόλεις',
            'category': cats['dialogues'],
            'author': user_nikos,
            'author_name': 'Νίκος Καλοκαιρινός',
            'author_title': 'Αρχιτέκτων - Πολεοδόμος · Πιστοποιημένος Συντάκτης',
            'author_avatar_url': 'https://i.pravatar.cc/150?img=68',
            'excerpt': 'Οι πόλεις μας δεν πάσχουν από έλλειψη σχεδίων, αλλά από έλλειψη ουσιαστικής συμμετοχής. Μια βιωματική πρόταση για τοπικά συμβούλια πολιτών.',
            'content': '<p>Η συμμετοχή των πολιτών στη λήψη αποφάσεων για το άμεσο περιβάλλον διαβίωσής τους...</p>',
            'lead_image_url': 'https://images.unsplash.com/photo-1517048676732-d65bc937f952?auto=format&fit=crop&q=80&w=1200',
            'read_time_minutes': 7,
            'is_featured': True,
            'views_count': 2210,
        },
        {
            'title': 'Ψηφιακός αλφαβητισμός για όλους: Γεφυρώνοντας το χάσμα στις ευάλωτες κοινωνικές ομάδες',
            'category': cats['dialogues'],
            'author': user_evgenia,
            'author_name': 'Ευγενία Μπαλή',
            'author_title': 'Κοινωνιολόγος & Ερευνήτρια · Πιστοποιημένη Συντάκτρια',
            'author_avatar_url': 'https://i.pravatar.cc/150?img=47',
            'excerpt': 'Η πρόσβαση στο διαδίκτυο δεν αρκεί. Χρειαζόμαστε ανοιχτά εργαστήρια δεξιοτήτων σε κάθε δήμο για τους ηλικιωμένους και τους ανέργους.',
            'content': '<p>Η ψηφιοποίηση των υπηρεσιών του κράτους αποτελεί θετικό βήμα, ωστόσο...</p>',
            'lead_image_url': 'https://images.unsplash.com/photo-1531482615713-2afd69097998?auto=format&fit=crop&q=80&w=800',
            'read_time_minutes': 5,
            'views_count': 1340,
        },
    ]

    for item in articles_data:
        article, created = Article.objects.get_or_create(
            title=item['title'],
            defaults={
                'category': item['category'],
                'author': item.get('author'),
                'author_name': item.get('author_name', ''),
                'author_title': item.get('author_title', ''),
                'author_avatar_url': item.get('author_avatar_url', ''),
                'excerpt': item['excerpt'],
                'content': item['content'],
                'lead_image_url': item.get('lead_image_url', ''),
                'read_time_minutes': item.get('read_time_minutes', 5),
                'status': Article.STATUS_PUBLISHED,
                'is_featured': item.get('is_featured', False),
                'views_count': item.get('views_count', 0),
                'published_at': timezone.now(),
            }
        )
    print(f"  [OK] {len(articles_data)} Articles populated.")

    # 5. Author Applications
    apps_data = [
        {
            'full_name': 'Κωνσταντίνος Σταματίου',
            'email': 'k.stamatiou@example.com',
            'profession': 'Περιβαλλοντολόγος',
            'topic_interest': 'Περιβάλλον & Πόλεις',
            'bio': 'Ειδικός σε θέματα κυκλικής οικονομίας και ανανεώσιμων πηγών ενέργειας.',
            'sample_text': 'Πρόταση για τη διαχείριση αποβλήτων σε νησιωτικούς δήμους με χρήση τεχνολογιών διαλογής στην πηγή...',
            'status': AuthorApplication.STATUS_PENDING,
            'questionnaire_data': {'experience_years': 6, 'previous_publications': 'GreenTech Review, EcoNews'},
        },
        {
            'full_name': 'Μαρία Δούκα',
            'email': 'm.douka@example.com',
            'profession': 'Οικονομολόγος / Ερευνήτρια',
            'topic_interest': 'Οικονομία & Καινοτομία',
            'bio': 'Υποψήφια διδάκτωρ με έρευνα στις νεοφυείς επιχειρήσεις και τη χρηματοδότηση καινοτομίας.',
            'sample_text': 'Ανάλυση των τάσεων Venture Capital στην Ελλάδα και την Ευρώπη τα τελευταία πέντε χρόνια...',
            'status': AuthorApplication.STATUS_APPROVED,
            'questionnaire_data': {'experience_years': 4, 'previous_publications': 'Startupper, Financial Studies'},
        },
    ]

    for app_item in apps_data:
        AuthorApplication.objects.get_or_create(
            email=app_item['email'],
            defaults=app_item
        )
    print(f"  [OK] {len(apps_data)} Author Applications seeded.")
    print("[SUCCESS] Seeding completed successfully!")


if __name__ == '__main__':
    seed()
