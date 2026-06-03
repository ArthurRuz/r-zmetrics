const searchInput = document.getElementById('search-input');
const resultsContainer = document.getElementById('search-results');
let debounceTimer;

searchInput.addEventListener('input', function() {
    const query = this.value.trim();
    
    // Очищаем предыдущий таймер (чтобы не отправлять запрос на каждую букву)
    clearTimeout(debounceTimer);
    
    if (query.length < 2) {
        resultsContainer.innerHTML = '';
        resultsContainer.classList.remove('active');
        return;
    }
    
    // Ждем 300 мс после последней буквы, потом отправляем запрос
    debounceTimer = setTimeout(() => {
        fetch(`/search/?q=${encodeURIComponent(query)}`)
            .then(response => response.json())
            .then(data => {
                displayResults(data.results);
            })
            .catch(error => console.error('Ошибка:', error));
    }, 300);
});

function displayResults(results) {
    if (results.length === 0) {
        resultsContainer.innerHTML = '<div class="no-results">Ничего не найдено</div>';
        resultsContainer.classList.add('active');
        return;
    }
    
    let html = '';
    for (const item of results) {
        let iconHtml = `<img src="${item.icon}" alt="logo" class="result-icon">`
        
        html += `
            <a href="${item.url}" class="result-item">
                ${iconHtml}
                <div class="result-info">
                    <div class="result-title">${item.title}</div>
                    <div class="result-type">${getTypeLabel(item.type)}</div>
                </div>
            </a>
        `;
    }
    
    resultsContainer.innerHTML = html;
    resultsContainer.classList.add('active');
}

function getTypeLabel(type) {
    const labels = {
        'player': 'Игрок',
        'team': 'Команда',
        'tournament': 'Турнир'
    };
    return labels[type] || type;
}

// Закрываем выпадающий список при клике вне его
document.addEventListener('click', function(e) {
    if (!searchInput.contains(e.target) && !resultsContainer.contains(e.target)) {
        resultsContainer.classList.remove('active');
    }
});