from django.contrib import admin
from django import forms
from django.core.management import call_command
from django.contrib import messages
from .models import (
    Country, Season, Competition, CompetitionSeason, CompetitionStage,
    Stadium, Team, Player, HeadCoach, Standing, PlayerTeamSeason,
    Match, MatchEvent, MatchTeamStatistic, MatchPlayerStatistic, LiveMatchTracking
)

@admin.action(description='🔄 Обновить статистику выбранных матчей')
def action_update_single_matches(modeladmin, request, queryset):
    """
    Вызывает команду 'update_match' для каждого выбранного матча по его ID.
    Команда: update_match.py
    """
    success_count = 0
    error_count = 0

    for match in queryset:
        try:
            # Вызываем команду: manage.py update_match <match_id>
            call_command('update_match', match.id)
            success_count += 1
        except Exception as e:
            error_count += 1
            modeladmin.message_user(
                request,
                f"Ошибка при обновлении матча #{match.id} ({match}): {e}",
                messages.ERROR
            )

    if success_count:
        modeladmin.message_user(
            request,
            f"Успешно обновлено матчей: {success_count}.",
            messages.SUCCESS
        )


@admin.action(description='🚀 Запустить массовое обновление ВСЕХ матчей и лиг')
def action_run_mass_matches_update(modeladmin, request, queryset):
    """
    Вызывает команду полного обновления матчей по пяти топ-лигам.
    Команда: update_matches.py (Аргументов не требует)
    """
    try:
        modeladmin.message_user(request, "Процесс обновления матчей запущен...", messages.WARNING)
        call_command('update_matches')
        modeladmin.message_user(request, "Все матчи и статистика успешно обновлены!", messages.SUCCESS)
    except Exception as e:
        modeladmin.message_user(request, f"Ошибка массового обновления: {e}", messages.ERROR)

# ==========================================
# 2. ACTIONS ДЛЯ МОДЕЛИ СОРЕВНОВАНИЙ (Competition)
# ==========================================

@admin.action(description='📊 Обновить сезонную статистику игроков (PlayerTeamSeason)')
def action_update_player_seasons(modeladmin, request, queryset):
    """
    Вызывает команду для обновления статы игроков по коду выбранной лиги.
    Команда: update_player_team_seasons.py --competition-code=<CODE>
    """
    for comp in queryset:
        if not comp.competition_code:
            modeladmin.message_user(
                request,
                f"У соревнования {comp.name} отсутствует код (competition_code)!",
                messages.WARNING
            )
            continue

        try:
            # manage.py update_player_team_seasons --competition-code=PL --season=2025-2026
            call_command('update_player_team_seasons', competition_code=comp.competition_code, season='2025-2026')
            modeladmin.message_user(
                request,
                f"Статистика игроков для лиги {comp.name} успешно пересчитана.",
                messages.SUCCESS
            )
        except Exception as e:
            modeladmin.message_user(
                request,
                f"Ошибка обновления статистики игроков для {comp.name}: {e}",
                messages.ERROR
            )


@admin.action(description='📈 Спарсить актуальную турнирную таблицу')
def action_parse_standings(modeladmin, request, queryset):
    """
    Вызывает парсер таблицы для выбранных лиг.
    Команда: parse_current_standings.py <competition_code>
    """
    for comp in queryset:
        if not comp.competition_code:
            continue
        try:
            # manage.py parse_current_standings PL --season-name=2025-2026
            call_command('parse_current_standings', comp.competition_code, season_name='2025-2026')
            modeladmin.message_user(
                request,
                f"Турнирная таблица {comp.name} успешно обновлена.",
                messages.SUCCESS
            )
        except Exception as e:
            modeladmin.message_user(request, f"Ошибка парсинга таблицы {comp.name}: {e}", messages.ERROR)


@admin.action(description='🌐 Обновить таблицы ВСЕХ лиг сразу')
def action_update_all_standings(modeladmin, request, queryset):
    """
    Вызывает команду общего обновления таблиц.
    Команда: update_current_standings.py
    """
    try:
        call_command('update_current_standings')
        modeladmin.message_user(request, "Все турнирные таблицы успешно обновлены!", messages.SUCCESS)
    except Exception as e:
        modeladmin.message_user(request, f"Ошибка обновления всех таблиц: {e}", messages.ERROR)

# --- ГЕОГРАФИЯ И СЕЗОНЫ ---

@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'name_ru', 'alpha3')
    search_fields = ('name', 'name_ru', 'alpha3')


@admin.register(Season)
class SeasonAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'is_current')
    list_filter = ('is_current',)
    search_fields = ('name',)


# --- ТУРНИРЫ ---

@admin.register(Competition)
class CompetitionAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'competition_code', 'country', 'competition_type')
    list_filter = ('competition_type', 'country')
    search_fields = ('name', 'name_ru', 'competition_code')
    prepopulated_fields = {'slug': ('name',)}
    actions = [
        action_update_player_seasons,
        action_parse_standings,
        action_update_all_standings
    ]


@admin.register(CompetitionSeason)
class CompetitionSeasonAdmin(admin.ModelAdmin):
    list_display = ('id', 'competition', 'season', 'date_start', 'date_end', 'status', 'current_matchday')
    list_filter = ('status', 'season', 'competition')
    search_fields = ('competition__name', 'season__name')


@admin.register(CompetitionStage)
class CompetitionStageAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'stage_type')
    list_filter = ('stage_type',)
    search_fields = ('name',)


# --- КОМАНДЫ, ИГРОКИ И ТРЕНЕРЫ ---

@admin.register(Stadium)
class StadiumAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'city', 'country', 'capacity')
    list_filter = ('country', 'city')
    search_fields = ('name', 'city')


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'short_name', 'tla', 'country', 'stadium')
    list_filter = ('country',)
    search_fields = ('name', 'short_name', 'name_ru', 'tla')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'current_team', 'main_position', 'date_of_birth', 'market_value')
    list_filter = ('main_position', 'preferred_foot', 'current_team__country')
    search_fields = ('name', 'normalized_name', 'current_team__name')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(HeadCoach)
class HeadCoachAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'current_team', 'country')
    list_filter = ('country', 'current_team')
    search_fields = ('name', 'normalized_name', 'current_team__name')
    prepopulated_fields = {'slug': ('name',)}


# --- ТУРНИРНЫЕ ТАБЛИЦЫ И СТАТИСТИКА СЕЗОНА ---

@admin.register(Standing)
class StandingAdmin(admin.ModelAdmin):
    list_display = ('id', 'competition_season', 'team', 'position', 'played', 'points', 'table_type', 'group')
    list_filter = ('table_type', 'competition_season', 'group')
    search_fields = ('team__name', 'competition_season__competition__name')


class PlayerTeamSeasonForm(forms.ModelForm):
    class Meta:
        model = PlayerTeamSeason
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = False


@admin.register(PlayerTeamSeason)
class PlayerTeamSeasonAdmin(admin.ModelAdmin):
    form = PlayerTeamSeasonForm

    list_display = ('id', 'player', 'team', 'competition_season', 'shirt_number', 'matches', 'goals', 'assists')
    list_filter = ('competition_season', 'team')
    search_fields = ('player__name', 'team__name')


# --- МАТЧИ И ИХ ДАННЫЕ ---

class MatchEventInline(admin.TabularInline):
    model = MatchEvent
    extra = 1


class MatchTeamStatisticInline(admin.TabularInline):
    model = MatchTeamStatistic
    extra = 2
    max_num = 2


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ('id', 'competition_season', 'home_team', 'away_team', 'match_datetime', 'status', 'home_score', 'away_score')
    list_filter = ('status', 'competition_season', 'match_datetime')
    search_fields = ('home_team__name', 'away_team__name', 'stadium__name')
    date_hierarchy = 'match_datetime'
    inlines = [MatchTeamStatisticInline, MatchEventInline]
    actions = [action_update_single_matches, action_run_mass_matches_update]


@admin.register(MatchEvent)
class MatchEventAdmin(admin.ModelAdmin):
    list_display = ('id', 'match', 'team', 'event_type', 'minute', 'player')
    list_filter = ('event_type', 'match__competition_season')
    search_fields = ('match__home_team__name', 'match__away_team__name', 'player__name', 'description')


@admin.register(MatchTeamStatistic)
class MatchTeamStatisticAdmin(admin.ModelAdmin):
    list_display = ('id', 'match', 'team', 'possession_percent', 'formation', 'xg')
    list_filter = ('formation', 'match__competition_season')
    search_fields = ('team__name', 'match__home_team__name', 'match__away_team__name')


@admin.register(MatchPlayerStatistic)
class MatchPlayerStatisticAdmin(admin.ModelAdmin):
    list_display = ('id', 'match', 'team', 'player', 'minutes_played', 'rating', 'is_starting', 'is_captain')
    list_filter = ('is_starting', 'is_captain', 'formation_position', 'match__competition_season')
    search_fields = ('player__name', 'team__name', 'match__home_team__name', 'match__away_team__name')


# --- ЛАЙВ-ОТ СЛЕЖИВАНИЕ ---

@admin.register(LiveMatchTracking)
class LiveMatchTrackingAdmin(admin.ModelAdmin):
    list_display = ('id', 'match', 'status', 'started_at', 'finished_at', 'last_update_at')
    list_filter = ('status',)
    search_fields = ('match__home_team__name', 'match__away_team__name', 'error_message')

