import { getCSRFToken } from './common.js';
import { startLiveScoresPolling, stopLiveScoresPolling } from './club-live-scores.js';

let currentTab = "overview";

document.querySelectorAll(".nav-button").forEach(button => {
    button.addEventListener("click", () => {
        document.querySelectorAll(".nav-button").forEach(btn => {
            btn.classList.remove("is-current-but");
        });

        button.classList.add("is-current-but");

        const tabName = button.dataset.tab;
        currentTab = tabName;

        loadTab(tabName);
    });
});

async function loadTab(tabName) {
    stopLiveScoresPolling();

    document.querySelectorAll(".tab").forEach(tab => {
        tab.classList.remove("active");
        tab.innerHTML = "";
    });

    const container = document.getElementById(tabName);

    if (!container) {
        console.error(`Контейнер вкладки "${tabName}" не найден`);
        return;
    }

    container.classList.add("active");

    try {
        const url = buildUrl(tabName);

        const response = await fetch(url);

        if (!response.ok) {
            throw new Error(`Ошибка HTTP: ${response.status}`);
        }

        const data = await response.json();

        if (data.error) {
            container.innerHTML = `<div class="error">${data.error}</div>`;
            return;
        }

        if (Array.isArray(data.html)) {
            data.html.forEach(html => {
                container.insertAdjacentHTML("beforeend", html);
            });

            if (tabName === "overview") {
                startLiveScoresPolling(document.getElementById('overview'));
            }
            if (tabName === "games") {
                requestAnimationFrame(() => {
                    scrollToNearestMatchDate();
                });
                startLiveScoresPolling(document.getElementById('games'));
            }
            if (tabName === "player-stats"){
                bindModalButtons();
            }
        } else {
            container.innerHTML = '<div class="error">Некорректный формат ответа</div>';
        }

    } catch (error) {
        container.innerHTML = '<div class="error">Ошибка загрузки данных</div>';
        console.error(error);
    }
}

function buildUrl(tabName) {
    if (tabName == "standings") {
        return `/api/club/${clubSlug}/standings/2025-2026/`
    }

    if (tabName == "games") {
        return `/api/club/${clubSlug}/games/2025-2026/`;
    }

    if (tabName.includes("stats")) {
        return `/api/club/${clubSlug}/${leagueSlug}/2025-2026/${tabName}/`;
    }

    return `/api/club/${clubSlug}/${tabName}/`;
}

document.addEventListener("DOMContentLoaded", () => {
    loadTab(currentTab);
});


document.addEventListener("click", async function (e) {
    const seasonItem = e.target.closest(".club-standings-season-item");
    if (!seasonItem) return;

    const season = seasonItem.dataset.season;
    const pageType = seasonItem.dataset.pageType;


    try {
        let url;

        if (pageType == "player-stats") { url = `/api/club/${clubSlug}/${leagueSlug}/${season}/player-stats/`; }
        else if (pageType == "stats") { url = `/api/club/${clubSlug}/${leagueSlug}/${season}/stats/`; }
        else { url = `/api/club/${clubSlug}/standings/${season}/`; }


        const response = await fetch(url);

        if (!response.ok) {
            throw new Error(`Ошибка HTTP: ${response.status}`);
        }

        const data = await response.json();

        if (data.error) {
            console.error(data.error);
            return;
        }

        if (pageType === "player-stats") {
            const statsContainer = document.getElementById("player-stats");

            if (!statsContainer) {
                console.error("Контейнер статистики не найден");
                return;
            }

            statsContainer.innerHTML = "";
            statsContainer.insertAdjacentHTML("beforeend", data.html[0]);
        } else {
            const standingsContainer = document.getElementById("top-5");

            if (!standingsContainer) {
                console.error("Контейнер таблицы не найден");
                return;
            }

            standingsContainer.outerHTML = data.html[0];
        }

    } catch (error) {
        console.error("Ошибка загрузки таблицы:", error);
    }
});


document.addEventListener("click", async function (e) {
    const seasonItem = e.target.closest(".club-matches-season-item");
    if (!seasonItem) return;

    const season = seasonItem.dataset.season;

    try {
        const response = await fetch(`/api/club/${clubSlug}/games/${season}/`);

        if (!response.ok) {
            throw new Error(`Ошибка HTTP: ${response.status}`);
        }

        const data = await response.json();

        if (data.error) {
            console.error(data.error);
            return;
        }

        const gamesContainer = document.getElementById("club-matches");

        if (!gamesContainer) {
            console.error("Контейнер матчей не найден");
            return;
        }

        stopLiveScoresPolling();
        gamesContainer.outerHTML = data.html[0];

        requestAnimationFrame(() => {
            scrollToNearestMatchDate();
        });
        startLiveScoresPolling(document.getElementById('games'));

    } catch (error) {
        console.error("Ошибка загрузки матчей:", error);
    }
});


function scrollToNearestMatchDate() {
    const matchesList = document.querySelector("#games .club-matches-list");

    if (!matchesList) {
        return;
    }

    const dateElements = matchesList.querySelectorAll(".club-matches-date[data-match-date]");

    if (!dateElements.length) {
        return;
    }

    const today = new Date();
    today.setHours(0, 0, 0, 0);

    let nearestElement = null;
    let minDiff = Infinity;

    dateElements.forEach(dateElement => {
        const dateValue = dateElement.dataset.matchDate;

        const matchDate = new Date(`${dateValue}T00:00:00`);
        matchDate.setHours(0, 0, 0, 0);

        const diff = matchDate - today;

        if (diff < 0) {
            return;
        }

        if (diff < minDiff) {
            minDiff = diff;
            nearestElement = dateElement;
        }
    });

    if (!nearestElement) {
        return;
    }

    const listTop = matchesList.getBoundingClientRect().top;
    const elementTop = nearestElement.getBoundingClientRect().top;

    matchesList.scrollTop += elementTop - listTop - 16;
}


function openModal(data) {
  overlay.style.display = 'block';
  modal.style.display = 'block';
  document.body.style.overflow = 'hidden';
  loadModalData(data);
}


async function loadModalData(data) {
    let cur_season = document.getElementById('clubStandingsSelectedSeason').textContent;
    let url = `/api/club/${clubSlug}/${leagueSlug}/${cur_season}/player-stats/${data.id}/`;
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


const btnNotification = document.getElementById("btnNotification");

if (btnNotification) {
    btnNotification.addEventListener("click", async function () {
        const heartIcon = btnNotification.querySelector(".club-heart");

        if (!heartIcon) {
            console.error("Иконка сердца не найдена");
            return;
        }

        btnNotification.disabled = true;

        try {
            const response = await fetch(`/club/${clubSlug}/favorite/`, {
                method: "POST",
                headers: {
                    "X-CSRFToken": getCSRFToken(),
                    "X-Requested-With": "XMLHttpRequest",
                },
            });

            if (!response.ok) {
                throw new Error(`Ошибка HTTP: ${response.status}`);
            }

            const data = await response.json();

            if (data.error) {
                console.error(data.error);
                return;
            }

            heartIcon.classList.toggle("is-favorite", data.is_favorite);

        } catch (error) {
            console.error("Ошибка изменения избранной команды:", error);
        } finally {
            btnNotification.disabled = false;
        }
    });
}
