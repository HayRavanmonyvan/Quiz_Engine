// app/static/js/quiz_search.js
/**
 * Instant Client-Side Search Filter for Quiz Engine
 * Powers real-time search across quiz cards, management tables, and catalogs.
 */
document.addEventListener('DOMContentLoaded', function () {
    // 1. Student / Teacher Quiz Card Grid Search
    const quizCardSearchInput = document.getElementById('quizSearchInput');
    if (quizCardSearchInput) {
        setupInstantSearch({
            inputId: 'quizSearchInput',
            clearBtnId: 'clearQuizSearchBtn',
            itemSelector: '.quiz-card-item',
            noResultsId: 'noQuizSearchResults',
            textExtractor: (card) => {
                const title = card.querySelector('.quiz-title')?.textContent || '';
                const desc = card.querySelector('.quiz-desc')?.textContent || '';
                const author = card.querySelector('.quiz-author')?.textContent || '';
                return `${title} ${desc} ${author}`;
            }
        });
    }

    // 2. Teacher Managed Quizzes Table Search
    const teacherTableSearchInput = document.getElementById('teacherQuizSearchInput');
    if (teacherTableSearchInput) {
        setupInstantSearch({
            inputId: 'teacherQuizSearchInput',
            clearBtnId: 'clearTeacherSearchBtn',
            itemSelector: '.teacher-quiz-row',
            noResultsId: 'noTeacherSearchResults',
            textExtractor: (row) => {
                const title = row.querySelector('.quiz-title')?.textContent || '';
                const desc = row.querySelector('.quiz-desc')?.textContent || '';
                const author = row.querySelector('.quiz-author')?.textContent || '';
                return `${title} ${desc} ${author}`;
            }
        });
    }
});

/**
 * Generic instant search helper
 */
function setupInstantSearch(config) {
    const input = document.getElementById(config.inputId);
    if (!input) return;

    const clearBtn = config.clearBtnId ? document.getElementById(config.clearBtnId) : null;
    const noResultsEl = config.noResultsId ? document.getElementById(config.noResultsId) : null;
    const items = document.querySelectorAll(config.itemSelector);

    function filterItems() {
        const query = input.value.trim().toLowerCase();
        let visibleCount = 0;

        if (clearBtn) {
            clearBtn.style.display = query.length > 0 ? 'inline-block' : 'none';
        }

        items.forEach(item => {
            const text = (config.textExtractor ? config.textExtractor(item) : item.textContent).toLowerCase();
            const match = text.includes(query);
            item.style.display = match ? '' : 'none';
            if (match) visibleCount++;
        });

        if (noResultsEl) {
            noResultsEl.style.display = (visibleCount === 0 && items.length > 0) ? '' : 'none';
        }
    }

    input.addEventListener('input', filterItems);

    if (clearBtn) {
        clearBtn.addEventListener('click', function () {
            input.value = '';
            filterItems();
            input.focus();
        });
    }
}
