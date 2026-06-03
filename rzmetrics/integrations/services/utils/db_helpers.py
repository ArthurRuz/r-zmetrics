from datetime import datetime
from django.utils.text import slugify
from unidecode import unidecode
from football.models import Country, Player, Position
from integrations.models import PlayerExternalMapping


def normalize_text_lib(text: str) -> str:
    return unidecode(text)


def add_player(player, team):
    country = Country.objects.filter(name=player.country.name).first()


    new_player = Player.objects.create(
        name=player.name,
        slug=slugify(player.name),
        height=player.height,
        preferred_foot=Player.Foot[player.preferred_foot.upper() if player.preferred_foot
        else 'RIGHT'],
        main_position=Position[player.position.upper()],
        country=country,
        market_value=player.market_value,
        date_of_birth=datetime.fromtimestamp(player.date_of_birth).date(),
        current_team=team,
        normalized_name=normalize_text_lib(player.name),
    )

    p_map = PlayerExternalMapping.objects.create(
        player=new_player,
        external_id=player.id,
        source_id=4,
    )
    print(f'{new_player.name} {new_player.current_team.name} added')
    return p_map