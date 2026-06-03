from football.models import Standing


def get_standing(team, competition_season, table_type):
    return Standing.objects.filter(
        team=team,
        competition_season=competition_season,
        table_type=table_type
    ).first()


def safe_round(value, digits=1, default=0):
    if value is None:
        return default

    return round(value, digits)


def safe_percent(part, total):
    if not total:
        return 0

    return round(part * 100 / total)