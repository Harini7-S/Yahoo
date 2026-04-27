document.addEventListener('DOMContentLoaded', () => {
    // Only fetch news on the homepage where the containers exist
    const newsContainer = document.getElementById('news-feed-container');
    if (newsContainer) {
        fetch('/api/news')
            .then(response => response.json())
            .then(data => {
                renderNewsFeed(data.hero, data.articles);
                renderMarketSummary(data.market);
                renderTrending(data.trending);
            })
            .catch(error => console.error('Error fetching data:', error));
    }

    function renderNewsFeed(hero, articles) {
        const container = document.getElementById('news-feed-container');
        if (!container) return;
        
        let html = `
            <article class="hero-article card">
                <div class="hero-image placeholder-img" style="background: url('${hero.imageUrl}') center/cover;"></div>
                <div class="hero-content">
                    <h2>${hero.title}</h2>
                    <p>${hero.summary}</p>
                </div>
            </article>
            <div class="news-grid">
        `;

        articles.forEach(article => {
            html += `
                <article class="news-card card">
                    <div class="card-image placeholder-img" style="background: url('${article.imageUrl}') center/cover;"></div>
                    <div class="card-content">
                        <h3>${article.title}</h3>
                        <span class="source">${article.source}</span>
                    </div>
                </article>
            `;
        });

        html += `</div>`;
        container.innerHTML = html;
    }

    function renderMarketSummary(market) {
        const container = document.getElementById('market-list-container');
        if (!container) return;
        let html = '';
        market.forEach(item => {
            const colorClass = item.positive ? 'positive' : 'negative';
            html += `
                <li><span>${item.symbol}</span> <span class="${colorClass}">${item.change}</span></li>
            `;
        });
        container.innerHTML = html;
    }

    function renderTrending(trending) {
        const container = document.getElementById('trending-list-container');
        if (!container) return;
        let html = '';
        trending.forEach(item => {
            html += `
                <li><a href="#">${item}</a></li>
            `;
        });
        container.innerHTML = html;
    }
});
