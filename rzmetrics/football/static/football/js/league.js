import { getCSRFToken } from './common.js';

let currentRound = currentMatchday;

document.querySelectorAll('.nav-button').forEach(btn => {
    btn.addEventListener('click', () => {

        document.querySelectorAll('.nav-button').forEach(button => {
            button.classList.remove('is-current-but');
        });
        
        btn.classList.add('is-current-but');

        const tabName = btn.dataset.tab;

        console.log(`Tab opened ${tabName}`);

        const season = document.getElementById('selectedSeason').textContent;


        loadTab(tabName, season, currentRound);
    });
});

async function loadTab(tabName, season, matchday = null) {
    document.querySelectorAll('.tab').forEach(tab => {
        tab.classList.remove('active');
        tab.innerHTML = "";
    });
    
    const container = document.getElementById(tabName);
    container.classList.add('active');

    console.log("Открыта вкладка статистики")

    try {

        let url = buildUrl(tabName, season, matchday)

        const response = await fetch(url);
        const data = await response.json();
        
        
        for (let template in data){
            let element = document.getElementById(tabName);
            element.insertAdjacentHTML('beforeend', data[template]);

            if (tabName == "games"){
                const roundToShow = matchday || currentRound;
                const selectedRoundSpan = document.getElementById('selectedRound');
                if (selectedRoundSpan && roundToShow) {
                    selectedRoundSpan.textContent = "Раунд: " + roundToShow;
                }
            }
            if (tabName == "stats"){
                bindModalButtons();
            }
        }

    } catch (error) {
        container.innerHTML = '<div class="error">Ошибка загрузки данных</div>';
        console.error(error);
    }
    return;
}

function buildUrl(tabName, season, matchday){
    let url;

    console.log('matchday value:', matchday, 'type:', typeof matchday);

    if (tabName === "games") {
        return `/api/league/${leagueSlug}/${season}/${tabName}/${matchday}/`;
    }
    return `/api/league/${leagueSlug}/${season}/${tabName}/`;
}

document.querySelectorAll('.season-item').forEach(item => {
    item.addEventListener('click', function() {
        const season = this.textContent;
        document.getElementById('selectedSeason').textContent = season;
        
        const tab_id = document.querySelector('.tab.active').id;
        console.log(tab_id);
        loadTab(tab_id, season);
    });
});

document.addEventListener('click', function(e) {
    const roundItem = e.target.closest('.round-item');
    if (!roundItem) return;
    
    console.log('Клик по туру:', roundItem.textContent);
    
    const round = roundItem.textContent.trim();
    currentRound = round; 
    
    const season = document.getElementById('selectedSeason').textContent;
    const tab_id = document.querySelector('.tab.active').id;
    
    loadTab(tab_id, season, round);
});


function openModal(data) {
  overlay.style.display = 'block';
  modal.style.display = 'block';
  document.body.style.overflow = 'hidden';
  loadModalData(data); 
}

async function loadModalData(data) {
    let cur_season = document.getElementById('selectedSeason').textContent;
    let url = `/api/league/${leagueSlug}/${cur_season}/stats/${data.id}/`;
    console.log(url);
    const response = await fetch(url);
    const stats_html = await response.json();
    document.getElementById('modal-players').innerHTML = stats_html.html[0];
}

function bindModalButtons() {
    const modal = document.getElementById('modal');
    const overlay = document.getElementById('overlay');
    document.querySelector('.close').onclick = closeModal;
    document.querySelector('.overlay').onclick = closeModal;

    document.querySelectorAll('.more-button').forEach(item => {
        item.removeEventListener('click', handleMoreButtonClick);
        item.addEventListener('click', handleMoreButtonClick);
    });
}

function handleMoreButtonClick(event) {
    const button = event.currentTarget; 
    openModal(button);
}

function closeModal() {
  overlay.style.display = 'none';
  modal.style.display = 'none';
  document.body.style.overflow = '';
}

const element = document.getElementById('modal');
const moveHandle = document.querySelector('.resize-handle');

let startY, startHeight, isResizingTop = false;

// Перетаскивание за ВЕРХНИЙ край
moveHandle.addEventListener('mousedown', function(e) {
    e.preventDefault();
    isResizingTop = true;
    startY = e.clientY;
    startHeight = element.offsetHeight;
    
    document.addEventListener('mousemove', onMouseMove);
    document.addEventListener('mouseup', onMouseUp);
});


function onMouseMove(e) {
    const delta = e.clientY - startY;
    let newHeight;
    
    if (isResizingTop) {
        newHeight = startHeight - delta;
        element.style.marginTop = `${delta}px`;
    } else {
        newHeight = startHeight + delta;
        element.style.marginTop = '0px';
    }
    
    newHeight = Math.max(150, Math.min( window.innerHeight * 0.9, newHeight));
    element.style.height = `${newHeight}px`;
}

function onMouseUp() {
    document.removeEventListener('mousemove', onMouseMove);
    document.removeEventListener('mouseup', onMouseUp);
    
    if (isResizingTop) {
        element.style.marginTop = '0px';
    }
}



document.addEventListener('DOMContentLoaded', function() {
    loadTab("overview", "2025-2026");
    console.log(`League page opened`);
});

