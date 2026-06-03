from .mapper_utils import parse_datetime

def map_found_players(api_players: dict) -> list:
    return api_players.get('player', [])

def map_player(player: dict) -> dict:
    return {
        'date_born': parse_datetime(player['dateBorn']),
        'country': player['strNationality'],
        'photo': player['strCutout'],
        'name': player['strPlayer'],
        'team': player['strTeam'],
    }

def map_stadium(api_stadium: dict) -> dict:
    return {
        'name': api_stadium.get('strVenue'),
        'country': api_stadium.get('strCountry'),
        'capacity': api_stadium.get('intCapacity'),
        'location': api_stadium.get('strLocation'),
    }