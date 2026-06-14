from integrations.mappers.thesportsdb_mapper import map_found_players, map_player, map_stadium


def test_map_found_players():
    data = {"player": [{"id": 1}, {"id": 2}]}
    assert map_found_players(data) == [{"id": 1}, {"id": 2}]


def test_map_found_players_empty():
    assert map_found_players({}) == []


def test_map_player():
    player = {
        "dateBorn": "1990-05-15T00:00:00Z",
        "strNationality": "England",
        "strCutout": "http://example.com/photo.png",
        "strPlayer": "Harry Kane",
        "strTeam": "Bayern Munich",
    }
    result = map_player(player)
    assert result["name"] == "Harry Kane"
    assert result["country"] == "England"
    assert result["team"] == "Bayern Munich"
    assert result["date_born"] is not None


def test_map_stadium():
    stadium = {
        "strVenue": "Emirates Stadium",
        "strCountry": "England",
        "intCapacity": "60704",
        "strLocation": "London",
    }
    result = map_stadium(stadium)
    assert result["name"] == "Emirates Stadium"
    assert result["capacity"] == "60704"
    assert result["location"] == "London"
