import json

import pytest
from django.contrib.auth import get_user_model
from django.utils.text import slugify

from football.models import Competition, Match, Player, Team

User = get_user_model()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "query",
    ["", "a", "  "],
)
def test_search_short_query_returns_empty(client, query):
    response = client.get("/search/", {"q": query})
    assert response.status_code == 200
    assert json.loads(response.content)["results"] == []


@pytest.mark.django_db
def test_search_finds_player(client):
    Player.objects.create(
        name="Erling Haaland",
        slug=slugify("Erling Haaland"),
        photo_url="players_photos/haaland.jpg",
    )
    response = client.get("/search/", {"q": "Haaland"})
    data = json.loads(response.content)
    assert len(data["results"]) >= 1
    assert data["results"][0]["type"] == "player"
    assert "Haaland" in data["results"][0]["title"]


@pytest.mark.django_db
def test_search_finds_team(client, home_team):
    response = client.get("/search/", {"q": "Arsenal"})
    data = json.loads(response.content)
    types = [r["type"] for r in data["results"]]
    assert "team" in types


@pytest.mark.django_db
def test_search_finds_competition(client, competition):
    response = client.get("/search/", {"q": "Premier"})
    data = json.loads(response.content)
    types = [r["type"] for r in data["results"]]
    assert "competition" in types


@pytest.mark.django_db
def test_search_player_result_structure(client):
    Player.objects.create(
        name="Bukayo Saka",
        slug=slugify("Bukayo Saka"),
        photo_url="players_photos/saka.jpg",
    )
    response = client.get("/search/", {"q": "Saka"})
    result = json.loads(response.content)["results"][0]
    assert "title" in result
    assert "icon" in result
    assert "url" in result
    assert result["url"].startswith("/player/")


@pytest.mark.django_db
def test_api_match_scores_empty_ids(client):
    response = client.get("/api/matches/scores/")
    assert response.status_code == 200
    assert json.loads(response.content)["matches"] == {}


@pytest.mark.django_db
def test_api_match_scores_invalid_ids(client):
    response = client.get("/api/matches/scores/", {"ids": "abc,def"})
    assert response.status_code == 400


@pytest.mark.django_db
def test_api_match_scores_returns_scores(client, finished_match):
    response = client.get(
        "/api/matches/scores/",
        {"ids": f"{finished_match.id}"},
    )
    data = json.loads(response.content)
    match_data = data["matches"][str(finished_match.id)]
    assert match_data["home_score"] == 2
    assert match_data["away_score"] == 1


@pytest.mark.django_db
def test_api_match_scores_multiple_ids(client, finished_match, competition_season, home_team, away_team):
    match2 = Match.objects.create(
        competition_season=competition_season,
        home_team=away_team,
        away_team=home_team,
        match_datetime=finished_match.match_datetime,
        home_score=0,
        away_score=0,
        status=Match.Status.FINISHED,
    )
    ids = f"{finished_match.id},{match2.id}"
    response = client.get("/api/matches/scores/", {"ids": ids})
    data = json.loads(response.content)
    assert len(data["matches"]) == 2


@pytest.mark.django_db
def test_api_match_scores_limits_to_100_ids(client):
    ids = ",".join(str(i) for i in range(1, 150))
    response = client.get("/api/matches/scores/", {"ids": ids})
    assert response.status_code == 200


@pytest.mark.django_db
def test_toggle_favorite_add(client, home_team):
    user = User.objects.create_user(username="fan", password="pass12345")
    client.force_login(user)

    response = client.post(f"/club/{home_team.slug}/favorite/")
    data = json.loads(response.content)
    assert data["is_favorite"] is True
    assert user.favorite_teams.filter(pk=home_team.pk).exists()


@pytest.mark.django_db
def test_toggle_favorite_remove(client, home_team):
    user = User.objects.create_user(username="fan2", password="pass12345")
    user.favorite_teams.add(home_team)
    client.force_login(user)

    response = client.post(f"/club/{home_team.slug}/favorite/")
    data = json.loads(response.content)
    assert data["is_favorite"] is False
    assert not user.favorite_teams.filter(pk=home_team.pk).exists()


@pytest.mark.django_db
def test_toggle_favorite_unknown_club(client):
    user = User.objects.create_user(username="fan3", password="pass12345")
    client.force_login(user)
    response = client.post("/club/nonexistent-club/favorite/")
    assert response.status_code == 404


@pytest.mark.django_db
def test_index_page_loads(client):
    response = client.get("/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_league_page_loads(client, competition):
    response = client.get(f"/league/{competition.slug}/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_api_match_overview(client, finished_match, home_team, away_team):
    from decimal import Decimal

    from football.models import MatchPlayerStatistic, MatchTeamStatistic, Player

    for team in (home_team, away_team):
        MatchTeamStatistic.objects.create(
            match=finished_match,
            team=team,
            possession_percent=Decimal("50.00"),
            shots_total=10,
            shots_on_target=4,
            corners=5,
            offsides=1,
            fouls=8,
            passes_total=300,
            passes_accurate=250,
            xg=Decimal("1.50"),
        )

    for team, slug in ((home_team, "home-gk"), (away_team, "away-gk")):
        player = Player.objects.create(
            name=f"GK {slug}",
            slug=slug,
            main_position="GK",
            current_team=team,
        )
        MatchPlayerStatistic.objects.create(
            match=finished_match,
            team=team,
            player=player,
            is_starting=True,
            formation_position="GK",
            shirt_number=1,
        )

    response = client.get(f"/api/match/{finished_match.id}/overview/")
    assert response.status_code == 200
    data = json.loads(response.content)
    assert "html" in data


@pytest.mark.django_db
def test_club_page_loads(client, home_team):
    response = client.get(f"/club/{home_team.slug}/")
    assert response.status_code == 200
