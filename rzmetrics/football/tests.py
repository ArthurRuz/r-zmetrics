import pytest
import json
from football.models import Player
from django.utils.text import slugify


@pytest.mark.parametrize('player_name', [
        ("Djed Spence"),
        ("Bukayo Saka"),
        ("Martin Ode"),
        ("Erling Haaland"),
        ("Kevin De Bruyne"),
        ("La liga"),
        ("Premier"),
        ("Harry Kane"),
    ])


@pytest.mark.django_db
def test_search(client, player_name):
    Player.objects.create(
        name=player_name,
        slug=slugify(player_name),
        photo_url=f"players_photos/{player_name}.jpg",
    )

    response = client.get(f'/search/?q={player_name}')
    
    assert response.status_code == 200
    
    data = json.loads(response.content)
    
    assert data['results'][0]['title'] == player_name


