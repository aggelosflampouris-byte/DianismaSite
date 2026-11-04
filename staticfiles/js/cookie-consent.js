/**
 * Dianisma.gr - GDPR Cookie Consent Banner Script
 */
document.addEventListener('DOMContentLoaded', function() {
    const banner = document.getElementById('cookieConsentBanner');
    const modal = document.getElementById('cookieSettingsModal');
    if (!banner) return;

    const consent = localStorage.getItem('dianisma_cookie_consent');

    // Show banner if user has not set preference yet
    if (!consent) {
        banner.style.display = 'block';
    }

    // Accept All
    const btnAccept = document.getElementById('btnAcceptCookies');
    if (btnAccept) {
        btnAccept.addEventListener('click', function() {
            localStorage.setItem('dianisma_cookie_consent', 'all');
            banner.style.display = 'none';
            if (modal) modal.style.display = 'none';
        });
    }

    // Reject Non-Essential
    const btnReject = document.getElementById('btnRejectCookies');
    if (btnReject) {
        btnReject.addEventListener('click', function() {
            localStorage.setItem('dianisma_cookie_consent', 'necessary');
            banner.style.display = 'none';
            if (modal) modal.style.display = 'none';
        });
    }

    // Open Modal Settings
    const btnSettings = document.getElementById('btnCookieSettings');
    if (btnSettings && modal) {
        btnSettings.addEventListener('click', function() {
            modal.style.display = 'flex';
        });
    }

    // Close Modal
    const btnCloseModal = document.getElementById('btnCloseCookieModal');
    if (btnCloseModal && modal) {
        btnCloseModal.addEventListener('click', function() {
            modal.style.display = 'none';
        });
    }

    // Global helper to re-open settings anytime (e.g. from footer link)
    window.openCookieConsent = function() {
        if (modal) {
            modal.style.display = 'flex';
        } else if (banner) {
            banner.style.display = 'block';
        }
    };
});
