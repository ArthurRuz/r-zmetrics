from django.contrib import admin

from django.contrib import admin
from .models import (
    Country, Season, Competition, CompetitionSeason, CompetitionStage,
    Stadium, Team, Player, HeadCoach, Standing, PlayerTeamSeason,
    Match, MatchEvent, MatchTeamStatistic, MatchPlayerStatistic, LiveMatchTracking
)

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


@admin.register(PlayerTeamSeason)
class PlayerTeamSeasonAdmin(admin.ModelAdmin):
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
