from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import F, Q, Subquery, OuterRef, Count, Sum, Case, When, Value, Prefetch
from django.forms import IntegerField
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView
from football.models import Match, Competition, MatchTeamStatistic, Standing, Season, CompetitionSeason, Player, PlayerTeamSeason, Team, \
    HeadCoach, MatchEvent, MatchPlayerStatistic
from django.utils import timezone
from datetime import date, timedelta
from django.shortcuts import render
from django.core.cache import cache
from django.utils.text import slugify

from football.services.match_prediction import calculate_match_prediction
from football.services.team_statistics import get_team_stats
from football.utils.team_info import get_team_info


def search(request):
    query = request.GET.get('q', '').strip()
    
    if not query or len(query) < 2:
        return JsonResponse({'results': []})
    
    results = []
    
    slug_query = slugify(query)

    players = Player.objects.filter(slug__icontains=slug_query)[:5]
    teams = Team.objects.filter(slug__icontains=slug_query)[:5]
    competitions = Competition.objects.filter(slug__icontains=slug_query)[:5]
    
    results = []
    for player in players:

        icon_path = "/static/football/"
        
        icon_path =  icon_path + player.photo_url if player.photo_url else icon_path + "players_photos/NoPhoto.png"
        url = '/player/' + player.slug + "/" + str(player.id)

        results.append({
            'title': player.name,
            'icon': icon_path,
            'url': url,
            'type': 'player',
        })
        
    for team in teams:

        icon_path = "/static/football/" + team.logo_url

        url = '/club/' + team.slug

        results.append({
            'title': team.name,
            'icon': icon_path,
            'url': url,
            'type': 'team',
        })
    for competition in competitions:

        icon_path = "/static/football/" + competition.logo_url

        url = '/league/' + competition.slug

        results.append({
            'title': competition.name,
            'icon': icon_path,
            'url': url,
            'type': 'competition',
        })

    return JsonResponse({'results': results})


class IndexView(TemplateView):
    template_name = 'football/index.html'

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        nearest_matches = Match.objects.filter(
            match_datetime__gte=timezone.now()
        ).select_related(
            'home_team',     
            'away_team',               
        ).order_by('match_datetime')[:20]

        
        context['nearest_matches'] = nearest_matches
        return context


class LeagueView(TemplateView):
    template_name = 'football/league.html'

    def get_context_data(self, **kwargs):
        context = super(LeagueView, self).get_context_data(**kwargs)
        league_slug = self.kwargs.get('league_slug')

        league = get_object_or_404(
            Competition.objects.select_related('country'),
            slug=league_slug
        )
        seasons = CompetitionSeason.objects.filter(
            competition__slug=league_slug
        ).select_related(
            'competition', 'season'
        ).order_by('-season__name')[:3]
        
        current_competition_season = None
        for season in seasons: 
            if season.season.name == '2025-2026':
                current_competition_season = season
                break
    
        if not current_competition_season and seasons:
            current_competition_season = seasons[0]

        context['league'] = league
        context['seasons'] = seasons

        context['current_matchday'] = getattr(current_competition_season, 'current_matchday', None)
        return context


class MatchView(TemplateView):
    template_name = 'football/match.html'

    def get_context_data(self, **kwargs):
        context = super(MatchView, self).get_context_data(**kwargs)
        match_id = self.kwargs.get('match_id')

        match = Match.objects.select_related('home_team', 'away_team').get(id=match_id)

        match_events = MatchEvent.objects.filter(match=match_id)

        match_statistics = MatchTeamStatistic.objects.filter(match=match_id)
        match_home_team_statistics = match_statistics.get(team=match.home_team)
        match_away_team_statistics =  match_statistics.get(team=match.away_team)

        home_goals = match_events.filter(event_type='GOAL', team=match.home_team)
        away_goals = match_events.filter(event_type='GOAL', team=match.away_team)

        players = MatchPlayerStatistic.objects.filter(match=match_id)
        home_players = players.filter(team=match.home_team)
        away_players = players.filter(team=match.away_team)

        home_subs = home_players.filter(is_starting=0)
        away_subs = away_players.filter(is_starting=0)

        home_gk = home_players.get(formation_position="G", is_starting=1)
        home_defenders = home_players.filter(formation_position="D", is_starting=1)
        home_midfielders = home_players.filter(formation_position="M", is_starting=1)
        home_forwards = home_players.filter(formation_position="F", is_starting=1)

        away_gk = away_players.get(formation_position="G", is_starting=1)
        away_defenders = away_players.filter(formation_position="D", is_starting=1)
        away_midfielders = away_players.filter(formation_position="M", is_starting=1)
        away_forwards = away_players.filter(formation_position="F", is_starting=1)

        match_events = MatchEvent.objects.filter(match=match_id)
        

        context['match'] = match
        context['events'] = match_events
        context['home_stats'] = match_home_team_statistics
        context['away_stats'] = match_away_team_statistics
        context['home_goals'] = home_goals
        context['away_goals'] = away_goals

        context['home_players'] = home_players
        context['home_subs'] = home_subs
        context['home_gk'] = home_gk
        context['home_defenders'] = home_defenders
        context['home_midfielders'] = home_midfielders
        context['home_forwards'] = home_forwards

        context['away_players'] = away_players
        context['away_subs'] = away_subs
        context['away_gk'] = away_gk
        context['away_defenders'] = away_defenders
        context['away_midfielders'] = away_midfielders
        context['away_forwards'] = away_forwards

        context['match_events'] = match_events
        return context


def api_match_overview(request, match_id):
    match = Match.objects.select_related('home_team', 'away_team').get(id=match_id)
    match_events = MatchEvent.objects.filter(match=match_id)

    html = [
        render_to_string('football/includes/match-events.html',
                         {
                            'match_events': match_events,
                            'match': match,
                            }),

    ]
    return JsonResponse({'html': html})


def api_match_stats(request, match_id):
    match = Match.objects.select_related('home_team', 'away_team').get(id=match_id)
    match_statistics = MatchTeamStatistic.objects.filter(match=match)
    match_home_team_statistics = match_statistics.get(team=match.home_team)
    match_away_team_statistics =  match_statistics.get(team=match.away_team)

    html = [
        render_to_string('football/includes/match-stats.html',
                         {
                            'home_stats': match_home_team_statistics,
                            'away_stats': match_away_team_statistics,
                            }),

    ]
    return JsonResponse({'html': html})


def api_match_squad(request, match_id):
    match = Match.objects.select_related('home_team', 'away_team').get(id=match_id)
    players = MatchPlayerStatistic.objects.filter(match=match)
    home_players = players.filter(team=match.home_team)
    away_players = players.filter(team=match.away_team)

    match_statistics = MatchTeamStatistic.objects.filter(match=match_id)
    match_home_team_statistics = match_statistics.get(team=match.home_team)
    match_away_team_statistics =  match_statistics.get(team=match.away_team)


    home_subs = home_players.filter(is_starting=0)
    away_subs = away_players.filter(is_starting=0)

    home_gk = home_players.get(formation_position="G", is_starting=1)
    home_defenders = home_players.filter(formation_position="D", is_starting=1)
    home_midfielders = home_players.filter(formation_position="M", is_starting=1)
    home_forwards = home_players.filter(formation_position="F", is_starting=1)

    away_gk = away_players.get(formation_position="G", is_starting=1)
    away_defenders = away_players.filter(formation_position="D", is_starting=1)
    away_midfielders = away_players.filter(formation_position="M", is_starting=1)
    away_forwards = away_players.filter(formation_position="F", is_starting=1)

    html = [
        render_to_string('football/includes/squad.html',
                         {
                            'match': match,
                            'home_stats': match_home_team_statistics,
                            'away_stats': match_away_team_statistics,

                            'home_players': home_players,
                            'home_subs': home_subs,
                            'home_gk': home_gk,
                            'home_defenders': home_defenders,
                            'home_midfielders': home_midfielders,
                            'home_forwards': home_forwards,

                            'away_players': away_players,
                            'away_subs': away_subs,
                            'away_gk': away_gk,
                            'away_defenders': away_defenders,
                            'away_midfielders': away_midfielders,
                            'away_forwards': away_forwards,
                            }),

    ]
    return JsonResponse({'html': html})


class ClubView(TemplateView):
    template_name = 'football/club.html'

    def get_context_data(self, **kwargs):
        context = super(ClubView, self).get_context_data(**kwargs)
        club_slug = self.kwargs.get('club_slug')

        club = Team.objects.select_related('country', 'stadium').get(slug=club_slug)

        standing = Standing.objects.filter(
            competition_season__season__name="2025-2026",
            team=club
        ).first()

        is_favorite_team = False

        if self.request.user.is_authenticated:
            is_favorite_team = self.request.user.favorite_teams.filter(pk=club.pk).exists()

        context['is_favorite_team'] = is_favorite_team
        context['club'] = club
        context['country'] = club.country
        context['stadium'] = club.stadium
        context['form'] = standing.form.lower().split(',') if standing else None
        context['standing'] = standing
        context['league'] = standing.competition_season.competition if standing else None

        return context


class PlayerView(TemplateView):
    template_name = 'football/player.html'

    def get_context_data(self, **kwargs):
        context = super(PlayerView, self).get_context_data(**kwargs)
        player_id = self.kwargs.get('player_id')
        player_slug = self.kwargs.get('player_slug')

        player = get_object_or_404(Player, pk=player_id, slug=player_slug)

        team = player.current_team
        country = player.country

        shirt_number = PlayerTeamSeason.objects.filter(
            player=player,
            team=team,
            competition_season__season__name='2025-2026',
        ).first()

        season_stats = PlayerTeamSeason.objects.filter(
            player=player,
            competition_season__season__name='2025-2026',
        ).first()

        today = date.today()
        dob = player.date_of_birth
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

        first_name, *other_parts = player.name.split()

        context['player'] = player
        context['shirt_number'] = shirt_number.shirt_number if shirt_number else '0'
        context['age'] = age
        context['first_name'] = first_name
        context['other_parts'] = other_parts
        context['team'] = team
        context['country'] = country
        context['season_stats'] = season_stats

        return context


class FavoritesView(LoginRequiredMixin, TemplateView):
    template_name = 'football/favorites.html'

    def get_context_data(self, **kwargs):
        context = super(FavoritesView, self).get_context_data(**kwargs)

        favorite_teams = self.request.user.favorite_teams.all()

        today_date = date.today()

        favorite_events = (
            Match.objects
            .select_related('home_team', 'away_team', 'competition_season__competition')
            .filter(
                match_datetime__date__gte=(today_date - timedelta(days=14)),
                match_datetime__date__lte=(today_date + timedelta(days=14)),
            )
            .filter(
                Q(home_team__in=favorite_teams) | Q(away_team__in=favorite_teams)
            )
            .order_by('-match_datetime')
        )

        favorite_team_ids = list(favorite_teams.values_list('id', flat=True))

        context['matches'] = favorite_events
        context['favorite_team_ids'] = favorite_team_ids

        return context


def api_league_overview(request, league_slug,  season):
    competition_season = get_object_or_404(
        CompetitionSeason.objects.select_related('competition', 'season'),
        competition__slug=league_slug,
        season__name=season
    )

    upcoming_games = Match.objects.filter(
        match_datetime__date__gte=timezone.now().date(),
        status=Match.Status.TIMED,
        competition_season=competition_season
    ).select_related(
        'home_team',           
        'away_team',          
    ).order_by('match_datetime')[:10]


    standings = Standing.objects.filter(competition_season=competition_season, table_type=Standing.TableType.TOTAL)[:5]

    week_team = {}

    if not standings and not upcoming_games:
        return JsonResponse({'error': 'Нет данных для этой лиги'}, status=404)

    html = [
        render_to_string('football/includes/upcoming-games.html',
                         {'matches': upcoming_games}),

        render_to_string('football/includes/week-team.html', {'week_team': week_team}),

        render_to_string('football/includes/league-table.html', {'standings': standings}),
    ]
    return JsonResponse({'html': html})



def api_league_table(request, league_slug, season):
    try:
        competition_season = CompetitionSeason.objects.get(
            competition__slug=league_slug,
            season__name=season
        )
    except CompetitionSeason.DoesNotExist:
        return JsonResponse({'error': 'Лига или сезон не найдены'}, status=404)

    standings = Standing.objects.filter(
        competition_season=competition_season,
        table_type=Standing.TableType.TOTAL
    ).select_related(
        'team'
    ).order_by(
        'position' 
    )
    
    if not standings:
        return JsonResponse({'error': 'Нет данных для этой лиги'}, status=404)

    html = [
        render_to_string('football/includes/league-table.html', {'standings': standings}),
    ]

    return JsonResponse({'html': html})


def api_league_games(request, league_slug, season, matchday):
    try:
        competition_season = CompetitionSeason.objects.get(
            competition__slug=league_slug,
            season__name=season
        )
    except CompetitionSeason.DoesNotExist:
        return JsonResponse({'error': 'Лига или сезон не найдены'}, status=404)

    matchday_games = Match.objects.filter(
        matchday=matchday,
        competition_season=competition_season,
    ).select_related(
        'home_team',
        'away_team',
    ).order_by('match_datetime__date')

    if not matchday_games:
        return JsonResponse({'error': 'Нет данных для этого раунда'}, status=404)

    matchdays = (Standing.objects.filter(competition_season=competition_season,
                                         table_type=Standing.TableType.TOTAL).count() - 1) * 2

    matchdays_range = [i for i in range(1, matchdays + 1)]

    html = [
        render_to_string('football/includes/league-matches.html',
                         {'matchday_games': matchday_games,
                          'matchdays': matchdays_range
                          }),
    ]

    return JsonResponse({'html': html})


def api_league_stats(request, league_slug, season, category=None):
    try:
        competition_season = CompetitionSeason.objects.get(
            competition__slug=league_slug,
            season__name=season
        )
    except CompetitionSeason.DoesNotExist:
        return JsonResponse({'error': 'Лига или сезон не найдены'}, status=404)


    players = PlayerTeamSeason.objects.filter(
        competition_season=competition_season
    ).select_related(
        'player',           
        'team'            
    )

    if category:
        top_players = players.filter(
            **{f'{category}__gt': 0}
        ).order_by(f'-{category}').annotate(value=F(f'{category}')).select_related('player', 'team')

        context = {
            'player_stats': (f'{category}', top_players),
        }
        html = [
            render_to_string('football/includes/modal-players.html', context=context),
        ]
    else:
        cache_key = f'league_stats_{league_slug}_{season}'
        cached_stats = cache.get(cache_key)
        
        if cached_stats:
            context = cached_stats
        else:
            top_scorers = players.order_by('-goals')[:3].annotate(value=F('goals'))
            top_assists = players.order_by('-assists')[:3].annotate(value=F('assists'))
            top_saves = players.filter(saves__isnull=False).order_by('-saves')[:3].annotate(value=F('saves'))
            top_penalties = players.order_by('-penalty_goals')[:3].annotate(value=F('penalty_goals'))
            top_yellow_cards = players.order_by('-yellow_cards')[:3].annotate(value=F('yellow_cards'))
            top_red_cards = players.order_by('-red_cards')[:3].annotate(value=F('red_cards'))

            context = {
                'stats': {
                    'goals': ('Бомбардиры', top_scorers),
                    'assists': ('Ассистенты', top_assists),
                    'saves': ('Сейвы', top_saves),
                    'penalty_goals': ('Забито пенальти', top_penalties),
                    'yellow_cards': ('Получено жёлтых', top_yellow_cards),
                    'red_cards': ('Получено красных', top_red_cards),
                }
            }
            cache.set(cache_key, context, 300)

        html = [
            render_to_string('football/includes/league-stats.html', context=context),
        ]
    return JsonResponse({'html': html})


@login_required
@require_POST
def toggle_favorite_team(request, club_slug):
    club = get_object_or_404(Team, slug=club_slug)

    if request.user.favorite_teams.filter(pk=club.pk).exists():
        request.user.favorite_teams.remove(club)
        is_favorite = False
    else:
        request.user.favorite_teams.add(club)
        is_favorite = True

    return JsonResponse({
        'is_favorite': is_favorite
    })


def api_club_overview(request, club_slug):
    club = Team.objects.get(slug=club_slug)

    matches = Match.objects.select_related('home_team', 'away_team').all()

    upcoming_match = (matches.select_related('home_team', 'away_team', 'competition_season')
                      .filter(Q(home_team=club) | Q(away_team=club),
                              status__in=[0,1,2,3]).order_by("match_datetime").first())

    home_team_standing = None
    away_team_standing = None
    prediction = None

    if upcoming_match:
        prediction = calculate_match_prediction(
            home_team=upcoming_match.home_team,
            away_team=upcoming_match.away_team,
            competition_season=upcoming_match.competition_season
        )

        home_team_standing = Standing.objects.filter(
            competition_season__season__name="2025-2026",
            team=upcoming_match.home_team,
            table_type=0,
        ).first()

        away_team_standing = Standing.objects.filter(
            competition_season__season__name="2025-2026",
            team=upcoming_match.away_team,
            table_type=0,
        ).first()

    last_matches = matches.filter(Q(home_team=club) | Q(away_team=club),
                                  status=6).order_by("-match_datetime")[:5]

    competitions = Competition.objects.filter(
        competition_seasons__season__name="2025-2026",
        competition_seasons__standings__team=club,
        competition_seasons__standings__table_type=0,
    )

    context = {
        'club': club,
        'upcoming_match': upcoming_match,
        'last_matches': last_matches,
        'home_team_form': home_team_standing.form.lower().split(',') if home_team_standing else None,
        'away_team_form': away_team_standing.form.lower().split(',') if away_team_standing else None,
        'competitions': competitions,
        'prediction': prediction,
        'today': timezone.localdate(),
    }

    return JsonResponse({
        'html': [
            render_to_string('football/includes/club-overview.html', context=context, request=request),
        ]
    })


def api_club_squad(request, club_slug):
    club = Team.objects.get(slug=club_slug)

    shirt_number_subquery = PlayerTeamSeason.objects.filter(
        player=OuterRef('pk'),
        team=club,
        competition_season__season__name='2025-2026',
    ).values('shirt_number')[:1]

    head_coach = HeadCoach.objects.get(current_team=club)

    players = (Player.objects.select_related('country').filter(current_team=club).
    annotate(
        current_shirt_number=Subquery(shirt_number_subquery)
    ))

    goalkeepers = players.filter(main_position='GK')
    defenders = players.filter(main_position='DEF')
    midfielders = players.filter(main_position='MF')
    forwards = players.filter(main_position='FRW')

    context = {
        'club': club,
        'squad': {
            'ВРАТАРИ': goalkeepers,
            'ЗАЩИТНИКИ': defenders,
            'ПОЛУЗАЩИТНИКИ': midfielders,
            'НАПАДАЮЩИЕ': forwards,
        },
        'head_coach': head_coach,
    }

    return JsonResponse({
        'html': [
            render_to_string('football/includes/club-squad.html', context=context),
        ]
    })


def api_club_standings(request, club_slug, season_name="2025-2026"):
    club = get_object_or_404(Team, slug=club_slug)

    competition_season = (
        CompetitionSeason.objects
        .select_related('competition', 'season')
        .filter(
            standings__team=club,
            season__name=season_name,
            standings__table_type=Standing.TableType.TOTAL,
        )
        .distinct()
        .first()
    )

    if competition_season is None:
        return JsonResponse({'error': 'Лига или сезон для клуба не найдены'}, status=404)

    league = competition_season.competition

    seasons = (
        CompetitionSeason.objects
        .select_related('season')
        .filter(
            competition=league,
            standings__team=club,
            standings__table_type=Standing.TableType.TOTAL,
        )
        .distinct()
        .order_by('-season__name')
    )

    standings = (
        Standing.objects
        .select_related('team')
        .filter(
            competition_season=competition_season,
            table_type=Standing.TableType.TOTAL,
        )
        .order_by('position')
    )

    if not standings.exists():
        return JsonResponse({'error': 'Нет данных для этой лиги'}, status=404)

    team_ids = list(standings.values_list('team_id', flat=True))

    next_matches = {}

    if competition_season.season.is_current:
        upcoming_matches = (
            Match.objects
            .select_related('home_team', 'away_team')
            .filter(
                competition_season=competition_season,
                match_datetime__gte=timezone.now(),
            )
            .filter(
                Q(home_team_id__in=team_ids) |
                Q(away_team_id__in=team_ids)
            )
            .order_by('match_datetime')
        )

        for match in upcoming_matches:
            if match.home_team_id not in next_matches:
                next_matches[match.home_team_id] = match

            if match.away_team_id not in next_matches:
                next_matches[match.away_team_id] = match

            if len(next_matches) == len(team_ids):
                break

    context = {
        'club': club,
        'competition_season': competition_season,
        'standings': standings,
        'league': league,
        'seasons': seasons,
        'next_matches': next_matches,
    }

    html = render_to_string(
        'football/includes/club-standings.html',
        context=context,
        request=request,
    )

    return JsonResponse({'html': [html]})


def api_club_matches(request, club_slug, season_name="2025-2026"):
    club = get_object_or_404(Team, slug=club_slug)

    season = (
        Season.objects
        .filter(
            name=season_name,
        )
        .distinct()
        .first()
    )

    if season is None:
        return JsonResponse({'error': 'Лига или сезон для клуба не найдены'}, status=404)

    matches = (
        Match.objects
        .select_related('home_team', 'away_team', 'competition_season__competition')
        .filter(
            competition_season__season=season,
        )
        .filter(
            Q(home_team=club) | Q(away_team=club)
        )
        .order_by('-match_datetime')
    )

    seasons = (
        Season.objects
        .filter(
            competitionseason__standings__team=club,
            competitionseason__standings__table_type=Standing.TableType.TOTAL,
        )
        .distinct()
        .order_by('-name')
    )

    if not matches.exists():
        return JsonResponse({'error': 'Матчи для команды не найдены'}, status=404)

    context = {
        'club': club,
        'matches': matches,
        'season': season,
        'seasons': seasons,
        'today': timezone.localdate(),
    }

    html = render_to_string(
        'football/includes/club-matches.html',
        context=context,
        request=request,
    )

    return JsonResponse({'html': [html]})


def api_match_scores(request):
    ids_param = request.GET.get('ids', '')
    if not ids_param:
        return JsonResponse({'matches': {}})

    try:
        match_ids = [int(i.strip()) for i in ids_param.split(',') if i.strip()]
    except ValueError:
        return JsonResponse({'error': 'Некорректный параметр ids'}, status=400)

    match_ids = match_ids[:100]

    rows = (
        Match.objects
        .filter(id__in=match_ids)
        .values('id', 'home_score', 'away_score', 'status')
    )

    matches = {
        str(row['id']): {
            'home_score': row['home_score'],
            'away_score': row['away_score'],
            'status': row['status'],
        }
        for row in rows
    }

    return JsonResponse({'matches': matches})


def api_club_player_stats(request, club_slug, league_slug, season_name='2025-2026', category=None):
    club = get_object_or_404(Team, slug=club_slug)

    league, competition_season, seasons = get_team_info(club, league_slug, season_name)

    if competition_season is None:
        return JsonResponse({'error': 'Лига или сезон для клуба не найдены'}, status=404)

    players = PlayerTeamSeason.objects.filter(competition_season=competition_season, team=club)

    top_scorers = players.filter(goals__gt=0).order_by('-goals')[:3].annotate(value=F('goals'))
    top_assists = players.filter(assists__gt=0).order_by('-assists')[:3].annotate(value=F('assists'))
    top_saves = players.filter(saves__gt=0).order_by('-saves')[:3].annotate(value=F('saves'))
    top_penalties = (players.filter(penalty_goals__gt=0)
                            .order_by('-penalty_goals')[:3]
                            .annotate(value=F('penalty_goals')))
    top_yellow_cards = (players.filter(yellow_cards__gt=0)
                                .order_by('-yellow_cards')[:3]
                                .annotate(value=F('yellow_cards')))
    top_red_cards = players.filter(red_cards__gt=0).order_by('-red_cards')[:3].annotate(value=F('red_cards'))

    if category:
        top_players = players.filter(
            **{f'{category}__gt': 0}
        ).order_by(f'-{category}').annotate(value=F(f'{category}'))

        context = {
            'player_stats': (f'{category}', top_players),
        }
        html = [
            render_to_string('football/includes/modal-players.html', context=context),
        ]
    else:
        context = {
            'stats': {
                'goals': ('Бомбардиры', top_scorers),
                'assists': ('Ассистенты', top_assists),
                'saves': ('Сейвы', top_saves),
                'penalty_goals': ('Забито пенальти', top_penalties),
                'yellow_cards': ('Получено жёлтых', top_yellow_cards),
                'red_cards': ('Получено красных', top_red_cards),
            },
            'competition_season': competition_season,
            'league': league,
            'seasons': seasons,
        }

        html = [
            render_to_string('football/includes/club-player-stats.html', context=context),
        ]
    return JsonResponse({'html': html})


def api_club_stats(request, club_slug, league_slug, season_name='2025-2026'):
    club = get_object_or_404(Team, slug=club_slug)

    league, competition_season, seasons = get_team_info(club, league_slug, season_name)

    if competition_season is None:
        return JsonResponse({'error': 'Лига или сезон для клуба не найдены'}, status=404)

    team_stats = get_team_stats(club, competition_season)

    context = {
        'stats': team_stats,
        'competition_season': competition_season,
        'league': league,
        'seasons': seasons,
    }

    html = [
        render_to_string('football/includes/club-stats.html', context=context),
    ]

    return JsonResponse({'html': html})


def api_player_overview(request, player_slug, player_id, competition_season_id=None):
    player = get_object_or_404(Player, pk=player_id, slug=player_slug)

    player_competition_seasons = (
        CompetitionSeason.objects
        .filter(playerteamseason__player=player)
        .select_related('competition', 'season')
        .distinct()
        .order_by('-season__name')
    )

    if competition_season_id is None:
        competition_season = player_competition_seasons.first()
    else:
        competition_season = get_object_or_404(
            CompetitionSeason,
            id=competition_season_id,
            playerteamseason__player=player
        )

    stats = (
        PlayerTeamSeason.objects
        .filter(
            player=player,
            competition_season=competition_season
        )
        .aggregate(
            matches=Sum('matches'),
            started=Sum('started'),
            minutes=Sum('minutes'),
            goals=Sum('goals'),
            assists=Sum('assists'),
            penalty_goals=Sum('penalty_goals'),
            penalty_attempts=Sum('penalty_attempts'),
            yellow_cards=Sum('yellow_cards'),
            red_cards=Sum('red_cards'),

            saves=Sum('saves'),
            clean_sheets=Sum('clean_sheets'),
            goals_allowed=Sum('goals_allowed'),
            shots_on_target_allowed=Sum('shots_on_target_allowed'),
            penalty_shots=Sum('penalty_shots'),
            penalty_allowed=Sum('penalty_allowed'),
            penalty_saved=Sum('penalty_saved'),
            penalty_missed=Sum('penalty_missed'),
        )
    )

    stats = {
        key: value or 0
        for key, value in stats.items()
    }

    context = {
        'player': player,
        'player_stats': stats,
        'competition_season': competition_season,
        'player_competition_seasons': player_competition_seasons,
    }

    return JsonResponse({
        'html': [
            render_to_string('football/includes/player-overview.html', context=context),
        ]
    })


def api_player_matches(request, player_slug, player_id, season_name=None):
    player = get_object_or_404(Player, pk=player_id, slug=player_slug)

    player_seasons = (
        Season.objects
        .filter(competitionseason__playerteamseason__player=player)
        .distinct()
        .order_by('-name')
    )

    if not player_seasons.exists():
        return JsonResponse({'error': 'Сезоны игрока не найдены'}, status=404)

    if season_name is None:
        season = player_seasons.first()
    else:
        season = get_object_or_404(
            player_seasons,
            name=season_name,
        )

    card_events_queryset = (
        MatchEvent.objects
        .filter(
            player=player,
            event_type__in=[
                MatchEvent.EventType.YELLOW_CARD,
                MatchEvent.EventType.RED_CARD,
                MatchEvent.EventType.SECOND_YELLOW_CARD,
            ]
        )
        .order_by('minute', 'extra_minute')
    )

    player_match_stats = (
        MatchPlayerStatistic.objects
        .select_related(
            'match',
            'team',
            'match__home_team',
            'match__away_team',
            'match__competition_season',
            'match__competition_season__competition',
            'match__competition_season__season',
        )
        .prefetch_related(
            Prefetch(
                'match__matchevent_set',
                queryset=card_events_queryset,
                to_attr='player_card_events'
            )
        )
        .filter(
            player=player,
            match__competition_season__season=season,
        )
        .order_by('-match__match_datetime')
    )

    if not player_match_stats.exists():
        return JsonResponse({'error': 'Матчи игрока за этот сезон не найдены'}, status=404)

    def get_rating_data(rating):
        if rating is None:
            return {
                'text': '-',
                'class': 'player-match-rating-empty',
            }

        rating_value = float(rating)

        if rating_value < 6:
            rating_class = 'player-match-rating-red'
        elif rating_value < 7:
            rating_class = 'player-match-rating-yellow'
        elif rating_value < 8:
            rating_class = 'player-match-rating-light-green'
        elif rating_value < 9:
            rating_class = 'player-match-rating-green'
        else:
            rating_class = 'player-match-rating-blue'

        return {
            'text': f'{rating_value:.1f}',
            'class': rating_class,
        }

    player_match_items = []

    for stat in player_match_stats:
        rating_data = get_rating_data(stat.rating)

        player_match_items.append({
            'stat': stat,
            'match': stat.match,
            'team': stat.team,
            'rating_text': rating_data['text'],
            'rating_class': rating_data['class'],
            'card_events': getattr(stat.match, 'player_card_events', []),
        })

    context = {
        'player': player,
        'player_match_items': player_match_items,
        'season': season,
        'player_seasons': player_seasons,
    }

    html = render_to_string(
        'football/includes/player-matches.html',
        context=context,
        request=request,
    )

    return JsonResponse({'html': [html]})


