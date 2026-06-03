function scrollToNearestMatchDate() {
    const matchesList = document.querySelector(".favorites-list");

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

document.addEventListener("DOMContentLoaded", () => {
    requestAnimationFrame(() => {
        scrollToNearestMatchDate();
    });
});