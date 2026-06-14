from datetime import datetime
from django.utils import timezone
from datetime import timedelta
from django.db import models
from django.utils.translation import gettext_lazy as _


class Country(models.Model):
    name = models.CharField(max_length=100)
    name_ru = models.CharField(max_length=100, blank=True, null=True)
    alpha3 = models.CharField(max_length=10)
    flag_url = models.URLField(max_length=500, blank=True, null=True)

    class Meta:
        verbose_name = 'страна'
        verbose_name_plural = 'страны'


class Season(models.Model):
    name = models.CharField(max_length=20)
    is_current = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'сезон'
        verbose_name_plural = 'сезоны'


class Competition(models.Model):
    name = models.CharField(max_length=150)
    name_ru = models.CharField(max_length=150)
    competition_code = models.CharField(max_length=10)
    country = models.ForeignKey('Country', on_delete=models.SET_NULL, null=True, blank=True)
    competition_type = models.CharField(max_length=30)
    logo_url = models.URLField(max_length=500, blank=True, null=True)
    slug = models.SlugField(max_length=255, db_index=True)

    class Meta:
        verbose_name = 'соревнование'
        verbose_name_plural = 'соревнования'


class CompetitionSeason(models.Model):
    competition = models.ForeignKey('Competition', on_delete=models.CASCADE, related_name='competition_seasons')
    season = models.ForeignKey('Season', on_delete=models.CASCADE)
    winner = models.ForeignKey('Team', on_delete=models.SET_NULL, null=True, blank=True)
    date_start = models.DateField(null=True, default=None)
    date_end = models.DateField(null=True, default=None)
    status = models.BooleanField(default=True)
    current_matchday = models.PositiveIntegerField(null=True, blank=True)
    current_stage = models.ForeignKey('CompetitionStage', on_delete=models.SET_NULL, null=True, blank=True)
    updated_at = models.DateTimeField(default=datetime.now, blank=True)

    class Meta:
        verbose_name = 'сезон соревнования'
        verbose_name_plural = 'сезоны соревнований'


class CompetitionStage(models.Model):
    class StageType(models.TextChoices):
        REGULAR = "REG", _("Регулярный сезон")
        GROUP = "GRP", _("Групповой этап")
        PLAYOFF = "POF", _("Плей-офф")

    name = models.CharField(max_length=150)
    stage_type = models.CharField(choices=StageType.choices, default=StageType.REGULAR)

    class Meta:
        verbose_name = 'этап соревнования'
        verbose_name_plural = 'этапы соревнований'


class Stadium(models.Model):
    name = models.CharField(max_length=150)
    country = models.ForeignKey('Country', on_delete=models.SET_NULL, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    capacity = models.PositiveIntegerField()

    class Meta:
        verbose_name = 'стадион'
        verbose_name_plural = 'стадионы'


class Team(models.Model):
    name = models.CharField(max_length=150)
    short_name = models.CharField(max_length=50)
    tla = models.CharField(max_length=10, blank=True, null=True)
    name_ru = models.CharField(max_length=150)
    country = models.ForeignKey('Country', on_delete=models.SET_NULL, null=True, blank=True)
    founded_year = models.PositiveIntegerField(null=True, blank=True)
    logo_url = models.URLField(max_length=500, blank=True, null=True)
    stadium = models.ForeignKey('Stadium', on_delete=models.SET_NULL, null=True, blank=True)
    slug = models.SlugField(max_length=150)

    class Meta:
        verbose_name = 'команда'
        verbose_name_plural = 'команды'


class Position(models.TextChoices):
    F = "FRW", "НАП"
    M = "MF", "ПЗЩ"
    D = "DEF", "ЗАЩ"
    G = "GK", "ВРТ"


class Player(models.Model):
    class Foot(models.IntegerChoices):
        LEFT = 1, "Левая"
        RIGHT = 0, "Правая"
        BOTH = 2, "Обе"

    name = models.CharField(max_length=255)
    date_of_birth = models.DateField(null=True)
    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True, blank=True)
    height = models.PositiveIntegerField(null=True, blank=True)
    preferred_foot = models.PositiveIntegerField(choices=Foot.choices, default=Foot.RIGHT, null=True, blank=True)
    main_position = models.CharField(choices=Position.choices, default=Position.F, max_length=3)
    photo_url = models.URLField(max_length=500, blank=True, null=True)
    current_team = models.ForeignKey('Team', on_delete=models.SET_NULL, null=True, blank=True)
    slug = models.SlugField(max_length=150)
    market_value = models.PositiveIntegerField(null=True, blank=True, default=0)
    normalized_name = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.name}"

    class Meta:
        verbose_name = 'игрок'
        verbose_name_plural = 'игроки'


class HeadCoach(models.Model):
    name = models.CharField(max_length=255)
    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True, blank=True)
    slug = models.SlugField(max_length=150)
    normalized_name = models.CharField(max_length=255, blank=True, null=True)
    current_team = models.ForeignKey('Team', on_delete=models.SET_NULL, null=True, blank=True)
    photo_url = models.URLField(max_length=500, blank=True, null=True)

    class Meta:
        verbose_name = 'главный тренер'
        verbose_name_plural = 'главные тренеры'


class Standing(models.Model):
    class TableType(models.IntegerChoices):
        TOTAL = 0, 'TOTAL'
        HOME = 1, 'HOME'
        AWAY = 2, 'AWAY'

    competition_season = models.ForeignKey('CompetitionSeason', on_delete=models.CASCADE, related_name='standings')
    team = models.ForeignKey('Team', on_delete=models.CASCADE, related_name='team_standings')
    position = models.PositiveIntegerField()
    played = models.PositiveIntegerField(default=0)
    wins = models.PositiveIntegerField(default=0)
    draws = models.PositiveIntegerField(default=0)
    losses = models.PositiveIntegerField(default=0)
    goals_for = models.PositiveIntegerField(default=0)
    goals_against = models.PositiveIntegerField(default=0)
    goal_difference = models.IntegerField(default=0)
    points = models.PositiveIntegerField(default=0)
    form = models.CharField(max_length=20, blank=True)
    table_type = models.PositiveIntegerField(choices=TableType.choices, default=TableType.TOTAL)
    group = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['competition_season', 'team', 'table_type'],
                name='unique_standing_competition_season_team_type'
            )
        ]

        verbose_name = 'положение команды'
        verbose_name_plural = 'положения команд'


class PlayerTeamSeason(models.Model):
    player = models.ForeignKey('Player', on_delete=models.CASCADE)
    team = models.ForeignKey('Team', on_delete=models.CASCADE)
    competition_season = models.ForeignKey('CompetitionSeason', on_delete=models.CASCADE, blank=True, null=True)
    shirt_number = models.PositiveIntegerField(null=True, blank=True)
    matches = models.PositiveIntegerField(default=0)
    started = models.PositiveIntegerField(default=0)
    minutes = models.PositiveIntegerField(default=0)
    goals = models.PositiveIntegerField(default=0)
    assists = models.PositiveIntegerField(default=0)
    penalty_goals = models.PositiveIntegerField(default=0)
    penalty_attempts = models.PositiveIntegerField(default=0)
    yellow_cards = models.PositiveIntegerField(default=0)
    red_cards = models.PositiveIntegerField(default=0)
    saves = models.PositiveIntegerField(null=True, default=None)
    clean_sheets = models.PositiveIntegerField(null=True, default=None)
    goals_allowed = models.PositiveIntegerField(null=True, default=None)
    shots_on_target_allowed = models.PositiveIntegerField(null=True, default=None)
    penalty_shots = models.PositiveIntegerField(null=True, default=None)
    penalty_allowed = models.PositiveIntegerField(null=True, default=None)
    penalty_saved = models.PositiveIntegerField(null=True, default=None)
    penalty_missed = models.PositiveIntegerField(null=True, default=None)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['player', 'team', 'competition_season'],
                name='unique_player_team_season_player_team_season'
            )
        ]

        verbose_name = 'профиль игрока в сезоне'
        verbose_name_plural = 'профили игроков в сезонах'


class Match(models.Model):
    class Winner(models.IntegerChoices):
        DRAW = 0, 'Ничья'
        HOME_TEAM = 1, 'Хозяева'
        AWAY_TEAM = 2, 'Гости'


    class Status(models.IntegerChoices):
        SCHEDULED = 0
        TIMED = 1
        IN_PLAY = 2
        PAUSED = 3
        EXTRA_TIME = 4
        PENALTY_SHOOTOUT = 5
        FINISHED = 6
        SUSPENDED = 7
        POSTPONED = 8
        CANCELLED = 9
        AWARDED = 10


    competition_season = models.ForeignKey('CompetitionSeason', on_delete=models.CASCADE)
    home_team = models.ForeignKey('Team', on_delete=models.CASCADE, related_name='home_matches')
    away_team = models.ForeignKey('Team', on_delete=models.CASCADE, related_name='away_matches')
    stadium = models.ForeignKey('Stadium', on_delete=models.SET_NULL, null=True, blank=True)
    matchday = models.PositiveIntegerField(null=True, blank=True)
    competition_stage = models.ForeignKey('CompetitionStage', on_delete=models.SET_NULL, null=True, blank=True)
    match_datetime = models.DateTimeField()
    home_score = models.PositiveIntegerField(default=0)
    away_score = models.PositiveIntegerField(default=0)
    home_score_first_half = models.PositiveIntegerField(default=0)
    away_score_first_half = models.PositiveIntegerField(default=0)
    home_score_second_half = models.PositiveIntegerField(default=0)
    away_score_second_half = models.PositiveIntegerField(default=0)
    home_score_extra_time = models.PositiveIntegerField(null=True, blank=True)
    away_score_extra_time = models.PositiveIntegerField(null=True, blank=True)
    home_score_penalties = models.PositiveIntegerField(null=True, blank=True)
    away_score_penalties = models.PositiveIntegerField(null=True, blank=True)
    referee_name = models.CharField(max_length=150, null=True, blank=True)
    group = models.CharField(max_length=100, blank=True, null=True)
    status = models.PositiveIntegerField(choices=Status.choices, default=Status.TIMED)
    duration = models.CharField(max_length=100, blank=True, null=True)
    winner = models.PositiveIntegerField(choices=Winner.choices, blank=True, null=True)

    @property
    def is_live(self):
        now = timezone.now()
        start = self.match_datetime
        end = start + timedelta(hours=1, minutes=55)
        return start <= now <= end

    class Meta:
        verbose_name = 'матч'
        verbose_name_plural = 'матчи'


class MatchEvent(models.Model):
    class EventType(models.TextChoices):
        GOAL = "GOAL", _("Гол")
        GOAL_OVERTURNED_BY_VAR = "GOAL_OVERTURNED_BY_VAR", 'Гол отменен после видеопросмотра'
        YELLOW_CARD = "YELLOW_CARD", _("Жёлтая карточка")
        RED_CARD = "RED_CARD", _("Красная карточка")
        SECOND_YELLOW_CARD = "SECOND_YELLOW_CARD", _("Вторая желтая карточка")
        PENALTY = "PENALTY", _("Пенальти")
        SCORED_PENALTY = "SCORED_PENALTY", _("Пенальти реализован")
        MISSED_PENALTY = "MISSED_PENALTY", _("Незабитый пенальти")
        OWN_GOAL = "OWN_GOAL", _("Автогол")
        SUBSTITUTION = "SUBSTITUTION", _("Замена")
        MATCH_STARTED = "MATCH_STARTED", _("Матч начался")
        MATCH_ENDED = "MATCH_ENDED", _("Матч закончился")

    match = models.ForeignKey('Match', on_delete=models.CASCADE)
    team = models.ForeignKey('Team', on_delete=models.CASCADE)
    player = models.ForeignKey('Player', on_delete=models.SET_NULL, null=True, blank=True, related_name='match_events')
    related_player = models.ForeignKey('Player', on_delete=models.SET_NULL, null=True, blank=True, related_name='related_match_events')
    minute = models.PositiveIntegerField()
    extra_minute = models.PositiveIntegerField(null=True, blank=True)
    event_type = models.CharField(choices=EventType.choices, default=EventType.GOAL, max_length=50)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = 'событие матча'
        verbose_name_plural = 'события матчей'


class MatchTeamStatistic(models.Model):
    match = models.ForeignKey('Match', on_delete=models.CASCADE)
    team = models.ForeignKey('Team', on_delete=models.CASCADE)
    possession_percent = models.DecimalField(max_digits=5, decimal_places=2)
    shots_total = models.PositiveIntegerField(default=0)
    shots_on_target = models.PositiveIntegerField(default=0)
    corners = models.PositiveIntegerField(default=0)
    offsides = models.PositiveIntegerField(default=0)
    fouls = models.PositiveIntegerField(default=0)
    yellow_cards = models.PositiveIntegerField(default=0)
    red_cards = models.PositiveIntegerField(default=0)
    passes_total = models.PositiveIntegerField(default=0)
    passes_accurate = models.PositiveIntegerField(default=0)
    xg = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    formation = models.CharField(max_length=15, blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['match', 'team'],
                name='unique_match_team_statistic_match_team'
            )
        ]

        verbose_name = 'статистика команды в матче'
        verbose_name_plural = 'статистика команд в матчах'


class MatchPlayerStatistic(models.Model):
    match = models.ForeignKey('Match', on_delete=models.CASCADE)
    team = models.ForeignKey('Team', on_delete=models.CASCADE)
    player = models.ForeignKey('Player', on_delete=models.CASCADE)
    minutes_played = models.PositiveIntegerField(default=0)
    goals = models.PositiveIntegerField(default=0)
    assists = models.PositiveIntegerField(default=0)
    shots = models.PositiveIntegerField(default=0)
    shots_on_target = models.PositiveIntegerField(default=0)
    passes = models.PositiveIntegerField(default=0)
    accurate_passes = models.PositiveIntegerField(default=0)
    key_passes = models.PositiveIntegerField(default=0)
    tackles = models.PositiveIntegerField(default=0)
    interceptions = models.PositiveIntegerField(default=0)
    saves = models.PositiveIntegerField(default=0)
    dribble_attempts = models.PositiveIntegerField(default=0)
    succ_dribble = models.PositiveIntegerField(default=0)
    fouls = models.PositiveIntegerField(default=0)
    yellow_cards = models.PositiveIntegerField(default=0)
    red_cards = models.PositiveIntegerField(default=0)
    rating = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)

    is_starting = models.BooleanField(default=False)
    formation_position = models.CharField(choices=Position, max_length=50, null=True, blank=True)
    shirt_number = models.PositiveIntegerField(null=True, blank=True)
    is_captain = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['match', 'player'],
                name='unique_match_player_statistic_match_player'
            )
        ]

        verbose_name = 'статистика игрока в матче'
        verbose_name_plural = 'статистика игроков в матчах'


class LiveMatchTracking(models.Model):
    class Status(models.TextChoices):
        PLANNED = "PLANNED", "Запланировано"
        ACTIVE = "ACTIVE", "Активно"
        FINISHED = "FINISHED", "Завершено"
        FAILED = "FAILED", "Ошибка"

    match = models.OneToOneField(
        "Match",
        on_delete=models.CASCADE,
        related_name="live_tracking",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PLANNED,
    )

    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    last_update_at = models.DateTimeField(null=True, blank=True)

    error_message = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "live tracking"
        verbose_name_plural = "live tracking"