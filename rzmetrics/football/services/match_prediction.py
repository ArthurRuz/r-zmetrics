from django.db.models import Q
from football.models import Standing, Match
from football.services.utils import get_standing

FORM_POINTS = {
    "W": 3,
    "D": 1,
    "L": 0,
}


def calculate_match_prediction(home_team, away_team, competition_season):
    home_total_standing = get_standing(
        team=home_team,
        competition_season=competition_season,
        table_type=Standing.TableType.TOTAL
    )

    away_total_standing = get_standing(
        team=away_team,
        competition_season=competition_season,
        table_type=Standing.TableType.TOTAL
    )

    home_home_standing = get_standing(
        team=home_team,
        competition_season=competition_season,
        table_type=Standing.TableType.HOME
    )

    away_away_standing = get_standing(
        team=away_team,
        competition_season=competition_season,
        table_type=Standing.TableType.AWAY
    )

    home_score = calculate_team_score(
        team=home_team,
        opponent=away_team,
        total_standing=home_total_standing,
        special_standing=home_home_standing,
        competition_season=competition_season,
        is_home=True
    )

    away_score = calculate_team_score(
        team=away_team,
        opponent=home_team,
        total_standing=away_total_standing,
        special_standing=away_away_standing,
        competition_season=competition_season,
        is_home=False
    )

    return convert_scores_to_probabilities(home_score, away_score)


def calculate_team_score(team, opponent, total_standing, special_standing, competition_season, is_home):
    table_score = calculate_table_score(total_standing)
    form_score = calculate_form_score(total_standing)
    home_away_score = calculate_table_score(special_standing)

    if special_standing is None:
        home_away_score = 60 if is_home else 40

    score = (
        table_score * 0.65 +
        form_score * 0.15 +
        home_away_score * 0.2
    )

    return max(score, 1)


def calculate_table_score(standing: Standing):
    if standing is None or standing.played == 0:
        return 50

    points_per_game = standing.points / standing.played
    goal_diff_per_game = standing.goal_difference / standing.played

    points_score = points_per_game / 3 * 100
    goal_diff_score = 50 + goal_diff_per_game * 15
    position_score = max(0, 20 - standing.position) / 19 * 100

    if standing.table_type == Standing.TableType.TOTAL:
        score = (
            points_score * 0.60 +
            goal_diff_score * 0.15 +
            position_score * 0.25
        )
    else:
        score = (
            points_score * 0.30 +
            (70 if standing.table_type == Standing.TableType.HOME else 30) * 0.50 +
            goal_diff_score * 0.10 +
            position_score * 0.10
        )

    return clamp(score, 0, 100)


def calculate_form_score(standing):
    if standing is None or not standing.form:
        return 50

    form = standing.form.replace(",", "").replace(" ", "").upper()

    if not form:
        return 50

    total_points = sum(FORM_POINTS.get(result, 0) for result in form)
    max_points = len(form) * 3

    if max_points == 0:
        return 50

    return total_points / max_points * 100


def calculate_last_h2h_score(team, opponent, competition_season):
    last_match = (
        Match.objects
        .filter(
            competition_season=competition_season,
            status=Match.Status.FINISHED
        )
        .filter(
            Q(home_team=team, away_team=opponent) |
            Q(home_team=opponent, away_team=team)
        )
        .order_by("-match_datetime")
        .first()
    )

    if last_match is None:
        return 50

    if last_match.home_team == team:
        team_goals = last_match.home_score
        opponent_goals = last_match.away_score
    else:
        team_goals = last_match.away_score
        opponent_goals = last_match.home_score

    goal_diff = team_goals - opponent_goals

    if goal_diff > 0:
        return clamp(70 + goal_diff * 5, 70, 90)

    if goal_diff == 0:
        return 50

    return clamp(30 + goal_diff * 5, 10, 30)


def convert_scores_to_probabilities(home_score, away_score):
    total_score = home_score + away_score

    if total_score <= 0:
        return {
            "home_win": 33.3,
            "draw": 33.4,
            "away_win": 33.3,
        }

    diff = abs(home_score - away_score)

    draw_probability = clamp(32 - diff * 0.3, 14, 32)

    remaining = 100 - draw_probability

    home_probability = remaining * home_score / total_score
    away_probability = remaining * away_score / total_score

    rounded_probabilities = round_probabilities_to_100({
        "home_win": home_probability,
        "draw": draw_probability,
        "away_win": away_probability,
    })

    return {
        "home_win": rounded_probabilities["home_win"],
        "draw": rounded_probabilities["draw"],
        "away_win": rounded_probabilities["away_win"],
        "home_score": round(home_score, 2),
        "away_score": round(away_score, 2),
    }


def clamp(value, min_value, max_value):
    return max(min_value, min(value, max_value))


def round_probabilities_to_100(probabilities):
    rounded = {
        key: int(value)
        for key, value in probabilities.items()
    }

    difference = 100 - sum(rounded.values())

    if difference > 0:
        remainders = sorted(
            probabilities.items(),
            key=lambda item: item[1] - int(item[1]),
            reverse=True
        )

        for i in range(difference):
            key = remainders[i][0]
            rounded[key] += 1

    elif difference < 0:
        remainders = sorted(
            probabilities.items(),
            key=lambda item: item[1] - int(item[1])
        )

        for i in range(abs(difference)):
            key = remainders[i][0]
            rounded[key] -= 1

    return rounded