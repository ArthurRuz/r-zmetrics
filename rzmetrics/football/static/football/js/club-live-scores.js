// Synced with Match.Status in football/models.py
const STATUS = {
    IN_PLAY: 2,
    PAUSED: 3,
    EXTRA_TIME: 4,
    PENALTY_SHOOTOUT: 5,
    FINISHED: 6,
};


const LIVE_STATUSES = new Set([2, 3, 4, 5]);

const LIVE_LABEL_STATUSES = new Set([2, 4, 5]);

const SCORE_VISIBLE_STATUSES = new Set([2, 3, 4, 5, 6]);
const POLL_INTERVAL_MS = 60_000;

const DEFAULT_SELECTOR = [
    '.club-match-score[data-match-id]',
    '.club-match-time[data-match-id]',
    '.club-match-overview[data-match-id]',
].join(', ');

let pollTimerId = null;

function collectPollableElements(root) {
    const scope = root || document;
    return Array.from(scope.querySelectorAll(DEFAULT_SELECTOR)).filter((element) => {
        const status = Number(element.dataset.matchStatus);
        if (LIVE_STATUSES.has(status)) {
            return true;
        }
        return element.dataset.liveCandidate === '1';
    });
}

function collectMatchIds(elements) {
    return elements
        .map((element) => element.dataset.matchId)
        .filter(Boolean);
}

function formatScore(value) {
    return value ?? 0;
}

function getTimeLabel(status) {
    if (status === STATUS.PAUSED) {
        return 'paused';
    }
    if (LIVE_LABEL_STATUSES.has(status)) {
        return 'live';
    }
    return null;
}

function updateMatchTimeElement(element, status) {
    const h3 = element.querySelector('h3');
    if (!h3) return;
    const kickoff = h3.dataset.kickoff ?? h3.textContent;
    const label = getTimeLabel(status);
    element.classList.remove('club-match-time--live', 'club-match-time--paused');
    h3.classList.remove('club-match-time__label--accent');
    if (label) {
        h3.textContent = label;
        element.classList.add(
            label === 'paused' ? 'club-match-time--paused' : 'club-match-time--live',
        );
        h3.classList.add('club-match-time__label--accent');
    } else {
        h3.textContent = kickoff;
    }
    element.dataset.matchStatus = String(status);
    if (!LIVE_STATUSES.has(status) && status >= STATUS.FINISHED) {
        delete element.dataset.liveCandidate;
    }
}

function updateOverviewElement(element, homeScore, awayScore, status) {
    const p = element.querySelector('p');
    const h3 = element.querySelector('h3');
    if (!p || !h3) {
        return;
    }

    const kickoffDate = p.dataset.kickoffDate ?? p.textContent;
    const kickoffTime = h3.dataset.kickoffTime ?? h3.textContent;
    const label = getTimeLabel(status);

    element.classList.remove('club-match-time--live', 'club-match-time--paused');
    p.classList.remove('club-match-time__label--accent');

    if (label) {
        p.textContent = label;
        element.classList.add(
            label === 'paused' ? 'club-match-time--paused' : 'club-match-time--live',
        );
        p.classList.add('club-match-time__label--accent');
    } else {
        p.textContent = kickoffDate;
    }

    if (SCORE_VISIBLE_STATUSES.has(status)) {
        h3.textContent = `${formatScore(homeScore)}:${formatScore(awayScore)}`;
    } else {
        h3.textContent = kickoffTime;
    }

    element.dataset.matchStatus = String(status);

    if (!LIVE_STATUSES.has(status) && status >= STATUS.FINISHED) {
        delete element.dataset.liveCandidate;
    }
}

function updateScoreElement(element, homeScore, awayScore, status) {
    const spans = element.querySelectorAll('span');
    if (spans.length < 2) {
        return;
    }

    if (SCORE_VISIBLE_STATUSES.has(status)) {
        spans[0].textContent = formatScore(homeScore);
        spans[1].textContent = formatScore(awayScore);
    } else {
        spans[0].textContent = '-';
        spans[1].textContent = '-';
    }

    element.dataset.matchStatus = String(status);

    if (LIVE_STATUSES.has(status)) {
        element.classList.add('club-match-score--live');
    } else {
        element.classList.remove('club-match-score--live');
    }

    if (!LIVE_STATUSES.has(status) && status >= 6) {
        delete element.dataset.liveCandidate;
    }
}

export async function refreshLiveScores(root) {
    const elements = collectPollableElements(root);
    const ids = collectMatchIds(elements);

    if (!ids.length) {
        stopLiveScoresPolling();
        return;
    }

    try {
        const response = await fetch(`/api/matches/scores/?ids=${ids.join(',')}`);

        if (!response.ok) {
            console.warn(`Live scores request failed: HTTP ${response.status}`);
            return;
        }

        const data = await response.json();
        const matches = data.matches || {};

        for (const element of elements) {
            const matchId = element.dataset.matchId;
            const matchData = matches[matchId];

            if (!matchData) {
                continue;
            }

            if (element.classList.contains('club-match-overview')) {
                updateOverviewElement(
                    element,
                    matchData.home_score,
                    matchData.away_score,
                    matchData.status,
                );
            } else if (element.classList.contains('club-match-time')) {
                updateMatchTimeElement(element, matchData.status);
            } else {
                updateScoreElement(element, matchData.home_score, matchData.away_score, matchData.status);
            }
        }

        if (!collectPollableElements(root).length) {
            stopLiveScoresPolling();
        }
    } catch (error) {
        console.warn('Live scores request failed:', error);
    }
}

export function startLiveScoresPolling(root, options = {}) {
    const intervalMs = options.intervalMs ?? POLL_INTERVAL_MS;

    stopLiveScoresPolling();

    const pollRoot = root || document;

    void refreshLiveScores(pollRoot);

    pollTimerId = window.setInterval(() => {
        void refreshLiveScores(pollRoot);
    }, intervalMs);
}

export function stopLiveScoresPolling() {
    if (pollTimerId !== null) {
        clearInterval(pollTimerId);
        pollTimerId = null;
    }
}
