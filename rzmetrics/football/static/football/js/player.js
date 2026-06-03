import { getCSRFToken } from './common.js';

let currentTab = "stats";

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

            if (tabName === "games") {
                requestAnimationFrame(() => {
                    scrollToNearestPlayerMatchDate();
                });
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
    return `/api/player/${playerSlug}/${playerId}/${tabName}/`;
}

document.addEventListener("DOMContentLoaded", () => {
    loadTab(currentTab);
});

document.addEventListener("click", async function (e) {
    const seasonItem = e.target.closest(".club-standings-season-item");
    if (!seasonItem) return;

    const competitionSeasonId = seasonItem.dataset.competitionSeasonId;
    const seasonTitle = seasonItem.dataset.seasonTitle;

    try {
        const response = await fetch(
            `/api/player/${playerSlug}/${playerId}/stats/${competitionSeasonId}/`
        );

        if (!response.ok) {
            throw new Error(`Ошибка HTTP: ${response.status}`);
        }

        const data = await response.json();

        if (data.error) {
            console.error(data.error);
            return;
        }

        const statsContainer = document.getElementById("stats");

        if (!statsContainer) {
            console.error("Контейнер статистики игрока не найден");
            return;
        }

        statsContainer.innerHTML = "";
        statsContainer.insertAdjacentHTML("beforeend", data.html[0]);

        const selectedSeason = document.getElementById("PlayerSelectedSeason");

        if (selectedSeason && seasonTitle) {
            selectedSeason.textContent = seasonTitle;
        }

    } catch (error) {
        console.error("Ошибка загрузки статистики игрока:", error);
    }
});

document.addEventListener("click", async function (e) {
    const seasonItem = e.target.closest(".player-matches-season-item");
    if (!seasonItem) return;

    const seasonTitle = seasonItem.dataset.seasonTitle;

    try {
        const response = await fetch(
            `/api/player/${playerSlug}/${playerId}/games/${seasonTitle}/`
        );

        if (!response.ok) {
            throw new Error(`Ошибка HTTP: ${response.status}`);
        }

        const data = await response.json();

        if (data.error) {
            console.error(data.error);
            return;
        }

        const gamesContainer = document.getElementById("player-matches");

        if (!gamesContainer) {
            console.error("Контейнер матчей игрока не найден");
            return;
        }

        gamesContainer.outerHTML = data.html[0];

        const selectedSeason = document.getElementById("PlayerMatchesSelectedSeason");

        if (selectedSeason && seasonTitle) {
            selectedSeason.textContent = seasonTitle;
        }

        requestAnimationFrame(() => {
            scrollToNearestPlayerMatchDate();
        });

    } catch (error) {
        console.error("Ошибка загрузки матчей игрока:", error);
    }
});

function scrollToNearestPlayerMatchDate() {
    const matchesList = document.querySelector("#games .player-matches-list");

    if (!matchesList) {
        return;
    }

    const dateElements = matchesList.querySelectorAll(".player-matches-date[data-match-date]");

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

        const diff = Math.abs(matchDate - today);

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