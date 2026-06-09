from django.urls import path
from . import views

app_name = 'football'

urlpatterns = [
     path('', views.IndexView.as_view(), name='index'),
     path('league/<slug:league_slug>/', views.LeagueView.as_view(), name='league'),
     path('match/<int:match_id>/', views.MatchView.as_view(), name='match'),
     path('club/<slug:club_slug>/', views.ClubView.as_view(), name='club'),
     path('player/<slug:player_slug>/<int:player_id>/', views.PlayerView.as_view(), name='player'),
     path('user/favorites', views.FavoritesView.as_view(), name='favorites'),
     path('search/', views.search, name='search'),

     path('api/league/<slug:league_slug>/<str:season>/overview/', views.api_league_overview,
          name='api_league_overview'),
     path('api/league/<slug:league_slug>/<str:season>/table/', views.api_league_table, name='api_league_table'),
     path('api/league/<slug:league_slug>/<str:season>/games/<int:matchday>/', views.api_league_games,
          name='api_league_games'),
     path('api/league/<slug:league_slug>/<str:season>/stats/', views.api_league_stats, name='api_league_stats'),
     path('api/league/<slug:league_slug>/<str:season>/stats/<str:category>/', views.api_league_stats,
          name='api_league_stats_category'),

     path('club/<slug:club_slug>/favorite/', views.toggle_favorite_team, name='toggle_favorite_team'),
     path('api/club/<slug:club_slug>/overview/', views.api_club_overview, name='api_club_overview'),
     path('api/club/<slug:club_slug>/squad/', views.api_club_squad, name='api_club_squad'),
     path('api/club/<slug:club_slug>/standings/<str:season_name>/', views.api_club_standings,
          name='api_club_standings'),
     path('api/matches/scores/', views.api_match_scores, name='api_match_scores'),
     path('api/club/<slug:club_slug>/games/<str:season_name>/', views.api_club_matches, name='api_club_matches'),
     path('api/club/<slug:club_slug>/<slug:league_slug>/<str:season_name>/player-stats/',
          views.api_club_player_stats,
          name='api_club_player_stats'),
     path('api/club/<slug:club_slug>/<slug:league_slug>/<str:season_name>/player-stats/<str:category>/',
          views.api_club_player_stats,
          name='api_club_player_stats_category'),
     path('api/club/<slug:club_slug>/<slug:league_slug>/<str:season_name>/stats/',
          views.api_club_stats,
          name='api_club_stats'),

     path('api/player/<slug:player_slug>/<int:player_id>/stats/', views.api_player_overview,
          name='api_player_overview'),
     path('api/player/<slug:player_slug>/<int:player_id>/stats/<int:competition_season_id>/',
          views.api_player_overview,
          name='api_player_overview'),
     path('api/player/<slug:player_slug>/<int:player_id>/games/', views.api_player_matches,
          name='api_player_matches'),
     path('api/player/<slug:player_slug>/<int:player_id>/games/<str:season_name>/',
          views.api_player_matches,
          name='api_player_matches'),

     path('api/match/<int:match_id>/overview/', views.api_match_overview, name='api_match_overview'),
     path('api/match/<int:match_id>/squad/', views.api_match_squad, name='api_match_squad'),
     path('api/match/<int:match_id>/stats/', views.api_match_stats, name='api_match_stats'),
     path('api/match/<int:match_id>/table/', views.api_match_table, name='api_match_table'),
]
