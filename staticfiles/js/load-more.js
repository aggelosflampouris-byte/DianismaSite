document.addEventListener('DOMContentLoaded', function() {
    const loadMoreBtn = document.getElementById('loadMoreBtn');
    if (!loadMoreBtn) return;

    // Determine the article container (check custom data-target or default class selectors)
    const targetSelector = loadMoreBtn.dataset.target || '#newsGrid, #articlesGrid, .articles-2col-grid, .magazine-grid, .analysis-grid, .news-grid';
    const gridContainer = document.querySelector(targetSelector);
    if (!gridContainer) return;

    loadMoreBtn.addEventListener('click', function(e) {
        e.preventDefault();

        const nextPage = loadMoreBtn.dataset.nextPage;
        if (!nextPage || loadMoreBtn.disabled) return;

        const category = loadMoreBtn.dataset.category || '';
        const cardType = loadMoreBtn.dataset.cardType || 'category';
        const excludeIds = loadMoreBtn.dataset.excludeIds || '';

        // Disable button and set loading indicator
        loadMoreBtn.disabled = true;
        const originalHTML = loadMoreBtn.innerHTML;
        loadMoreBtn.innerHTML = '<span>ΦΟΡΤΩΣΗ...</span> <i class="fas fa-spinner fa-spin"></i>';

        const url = `/api/articles/load-more/?category=${encodeURIComponent(category)}&page=${nextPage}&card_type=${encodeURIComponent(cardType)}&exclude_ids=${encodeURIComponent(excludeIds)}`;

        fetch(url)
            .then(function(response) { return response.json(); })
            .then(function(data) {
                if (data.success && data.html) {
                    const temp = document.createElement('div');
                    temp.innerHTML = data.html;
                    while (temp.firstChild) {
                        gridContainer.appendChild(temp.firstChild);
                    }

                    if (data.has_next) {
                        loadMoreBtn.dataset.nextPage = data.next_page;
                        loadMoreBtn.disabled = false;
                        loadMoreBtn.innerHTML = originalHTML;
                    } else {
                        // Hide button / container when no more articles exist
                        const wrap = loadMoreBtn.closest('.load-more-wrap') || loadMoreBtn.closest('.section-footer') || loadMoreBtn;
                        wrap.style.display = 'none';
                    }
                } else {
                    const wrap = loadMoreBtn.closest('.load-more-wrap') || loadMoreBtn.closest('.section-footer') || loadMoreBtn;
                    wrap.style.display = 'none';
                }
            })
            .catch(function(err) {
                console.error('Error loading articles:', err);
                loadMoreBtn.disabled = false;
                loadMoreBtn.innerHTML = originalHTML;
            });
    });
});
