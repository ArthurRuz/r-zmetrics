from django.db.models import Avg, Q, Sum, Count
from django.db.models.functions import Coalesce
from football.models import Team, CompetitionSeason, Standing, MatchTeamStatistic, Match
from football.services.utils import get_standing, safe_round, safe_percent


def get_team_stats(team: Team, competition_season: CompetitionSeason):
    team_total_stats, team_home_stats, team_away_stats = get_team_standings(team, competition_season)

    match_stats = (MatchTeamStatistic.objects
                   .select_related('match', 'match__competition_season',
                                   'match__home_team', 'match__away_team')
                   .filter(team=team,
                           match__competition_season=competition_season,
                           match__status=Match.Status.FINISHED)
                   .order_by('match__match_datetime'))

    match_opponent_stats = (MatchTeamStatistic.objects
                            .select_related('match', 'match__competition_season',
                                            'match__home_team', 'match__away_team')
                            .filter(~Q(team=team),
                                    match__competition_season=competition_season,
                                    match__status=Match.Status.FINISHED)
                            .filter(Q(match__home_team=team) | Q(match__away_team=team))
                            .order_by('match__match_datetime'))

    avg_stats = get_average_stats(team_total_stats, match_stats, match_opponent_stats)
    avg_home_stats = get_average_stats(team_home_stats,
                                       match_stats.filter(match__home_team=team),
                                       match_opponent_stats.filter(match__home_team=team))
    avg_away_stats = get_average_stats(team_away_stats,
                                       match_stats.filter(match__away_team=team),
                                       match_opponent_stats.filter(match__away_team=team))

    xg_total, xga_total = get_total_xg(match_stats, match_opponent_stats)
    goals_for_conclusion = make_conclusion_based_on_xg(team_total_stats.goals_for, xg_total)
    goals_against_conclusion = make_conclusion_based_on_xg(team_total_stats.goals_against, xga_total, 'пропустила')

    defensive_stats = get_defensive_stats(team_total_stats, match_stats, match_opponent_stats, team)

    xg_goal_chart = get_xg_goal_chart(match_stats, team)

    return {
        'team_total_stats': team_total_stats,
        'team_home_stats': team_home_stats,
        'team_away_stats': team_away_stats,

        'avg_stats': avg_stats,
        'avg_home_stats': avg_home_stats,
        'avg_away_stats': avg_away_stats,

        'xg_total': xg_total,
        'xga_total': xga_total,

        'goals_for_conclusion': goals_for_conclusion,
        'goals_against_conclusion': goals_against_conclusion,

        'defensive_stats': defensive_stats,
        'xg_goal_chart': xg_goal_chart,

        'home_points_per_match': get_points_per_match(team_home_stats),
        'away_points_per_match': get_points_per_match(team_away_stats),
    }


def get_team_standings(team: Team, competition_season: CompetitionSeason):
    team_total_stats = get_standing(
        team=team,
        competition_season=competition_season,
        table_type=Standing.TableType.TOTAL
    )

    team_home_stats = get_standing(
        team=team,
        competition_season=competition_season,
        table_type=Standing.TableType.HOME
    )

    team_away_stats = get_standing(
        team=team,
        competition_season=competition_season,
        table_type=Standing.TableType.AWAY
    )

    return team_total_stats, team_home_stats, team_away_stats


def get_total_xg(match_stats, match_opponent_stats):
    return match_stats.aggregate(xG=Sum('xg'))['xG'], match_opponent_stats.aggregate(xG=Sum('xg'))['xG']


def get_average_stats(total_stats: Standing, match_stats, match_opponent_stats):
    played = total_stats.played or 0

    goals_scored_per_match = safe_round(total_stats.goals_for / played, 1) if played else 0
    goals_against_per_match = safe_round(total_stats.goals_against / played, 1) if played else 0

    xg_per_match = safe_round(match_stats.aggregate(xG=Avg('xg'))['xG'], 2)
    xga_per_match = safe_round(match_opponent_stats.aggregate(xG=Avg('xg'))['xG'], 2)

    possession_per_match = safe_round(match_stats.aggregate(pos=Avg('possession_percent'))['pos'], 0)
    shots_per_match = safe_round(match_stats.aggregate(shots=Avg('shots_total'))['shots'], 1)
    shots_on_target_per_match = safe_round(match_stats.aggregate(shots=Avg('shots_on_target'))['shots'], 1)

    passes_data = match_stats.aggregate(
        accurate=Coalesce(Sum('passes_accurate'), 0),
        total=Coalesce(Sum('passes_total'), 0),
    )

    passes_accurate = safe_percent(
        passes_data['accurate'],
        passes_data['total']
    )

    corners_per_match = safe_round(match_stats.aggregate(corners=Avg('corners'))['corners'], 1)
    fouls_per_match = safe_round(match_stats.aggregate(fouls=Avg('fouls'))['fouls'], 1)

    return {
        'goals_scored_per_match': goals_scored_per_match,
        'goals_against_per_match': goals_against_per_match,
        'xG_per_match': xg_per_match,
        'xGA_per_match': xga_per_match,
        'possession_per_match': possession_per_match,
        'shots_per_match': shots_per_match,
        'shots_on_target_per_match': shots_on_target_per_match,
        'passes_accurate': passes_accurate,
        'corners_per_match': corners_per_match,
        'fouls_per_match': fouls_per_match,
    }


def make_conclusion_based_on_xg(goals, xg, side='забила'):
    diff = xg - goals

    if -1.0 < diff < 1.0:
        return f'Команда {side} голы согласно ожидаемым по xG.'
    elif diff >= 1.0:
        diff = round(diff)
        return f'Команда {side} на {diff} {pluralize_goals(diff)} больше ожидаемого по xG'
    else:
        diff = round(abs(diff))
        return f'Команда {side} на {diff} {pluralize_goals(diff)} меньше ожидаемого по xG'


def pluralize_goals(value: int):
    forms = ['гол', 'гола', 'голов']

    if 11 <= value % 100 <= 14:
        return forms[2]

    if value % 10 == 1:
        return forms[0]
    elif value % 10 in (2, 3, 4):
        return forms[1]
    else:
        return forms[2]


def get_defensive_stats(total_stats: Standing, match_stats, match_opponent_stats, team: Team):
    played = total_stats.played or 0

    clean_sheets = (
        match_stats
        .filter(
            Q(match__home_team=team, match__away_score=0) |
            Q(match__away_team=team, match__home_score=0)
        )
        .count()
    )

    clean_sheet_percent = safe_percent(clean_sheets, played)

    opponent_shots_per_match = safe_round(
        match_opponent_stats.aggregate(shots=Avg('shots_total'))['shots'],
        1
    )

    opponent_shots_on_target_per_match = safe_round(
        match_opponent_stats.aggregate(shots=Avg('shots_on_target'))['shots'],
        1
    )

    goals_against_per_match = safe_round(
        total_stats.goals_against / played,
        1
    ) if played else 0

    if goals_against_per_match <= 0.8:
        reliability_text = 'Надёжная оборона'
    elif goals_against_per_match <= 1.4:
        reliability_text = 'Средняя надёжность'
    else:
        reliability_text = 'Есть проблемы в обороне'

    return {
        'clean_sheets': clean_sheets,
        'clean_sheet_percent': clean_sheet_percent,
        'goals_against_per_match': goals_against_per_match,
        'opponent_shots_per_match': opponent_shots_per_match,
        'opponent_shots_on_target_per_match': opponent_shots_on_target_per_match,
        'reliability_text': reliability_text,
    }


def get_team_goals_in_match(match, team: Team):
    if match.home_team_id == team.id:
        return match.home_score

    return match.away_score


def get_match_label(match, team: Team):
    opponent = match.away_team if match.home_team_id == team.id else match.home_team

    opponent_name = opponent.short_name or opponent.name
    date_label = match.match_datetime.strftime('%d.%m')

    if match.home_team_id == team.id:
        return f'{date_label} vs {opponent_name}'

    return f'{date_label} @ {opponent_name}'


def get_xg_goal_chart(match_stats, team: Team):
    chart_items = []

    for stat in match_stats:
        if stat.xg is None:
            continue

        chart_items.append({
            'label': get_match_label(stat.match, team),
            'goals': get_team_goals_in_match(stat.match, team),
            'xg': float(stat.xg),
        })

    if not chart_items:
        return []

    max_chart_value = max(
        max(item['goals'] for item in chart_items),
        max(item['xg'] for item in chart_items),
        1
    )

    for item in chart_items:
        item['goals_width'] = round(item['goals'] / max_chart_value * 100)
        item['xg_width'] = round(item['xg'] / max_chart_value * 100)

    return chart_items


def get_points_per_match(standing: Standing):
    if not standing or not standing.played:
        return 0

    return round(standing.points / standing.played, 2)