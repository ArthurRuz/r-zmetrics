

document.querySelectorAll('.nav-button').forEach(btn => {
    btn.addEventListener('click', () => {

        document.querySelectorAll('.nav-button').forEach(button => {
            button.classList.remove('is-current-but');
        });
        
        btn.classList.add('is-current-but');

        const tabName = btn.dataset.tab;

        console.log(`Tab opened ${tabName}`);

        loadTab(tabName);
    });
});

async function loadTab(tabName) {
    document.querySelectorAll('.tab').forEach(tab => {
        tab.classList.remove('active');
        tab.innerHTML = "";
    });
    
    const container = document.getElementById(tabName);
    container.classList.add('active');

    try {
        let url = buildUrl(tabName);
        
        const response = await fetch(url);
        const data = await response.json();
        
        
        for (let template in data){
            let element = document.getElementById(tabName);
            element.insertAdjacentHTML('beforeend', data[template]);

        }

        if (tabName == "stats"){
            updateAllBars();
        }
        

    } catch (error) {
        container.innerHTML = '<div class="error">Ошибка загрузки данных</div>';
        console.error(error);
    }
    return;
}

function buildUrl(tabName){
    let url;
    return `/api/match/${matchId}/${tabName}/`;
}

document.addEventListener('DOMContentLoaded', function() {
    loadTab('overview');
});