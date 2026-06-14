import pytest
from django.db import IntegrityError

from football.models import Team
from integrations.models import ExternalSource, TeamExternalMapping


@pytest.mark.django_db
def test_external_source_creation():
    source = ExternalSource.objects.create(
        name="football-data.org",
        base_url="https://api.football-data.org/v4",
        is_active=True,
    )
    assert source.is_active is True


@pytest.mark.django_db
def test_team_external_mapping_unique_constraint(country):
    source = ExternalSource.objects.create(name="test-source")
    team1 = Team.objects.create(
        name="Team A",
        short_name="TA",
        name_ru="Команда А",
        country=country,
        slug="team-a",
    )
    team2 = Team.objects.create(
        name="Team B",
        short_name="TB",
        name_ru="Команда Б",
        country=country,
        slug="team-b",
    )

    TeamExternalMapping.objects.create(
        source=source,
        team=team1,
        external_id="100",
    )

    with pytest.raises(IntegrityError):
        TeamExternalMapping.objects.create(
            source=source,
            team=team2,
            external_id="100",
        )


@pytest.mark.django_db
def test_team_external_mapping_allows_same_external_id_different_source(country):
    source1 = ExternalSource.objects.create(name="source-1")
    source2 = ExternalSource.objects.create(name="source-2")
    team = Team.objects.create(
        name="Team C",
        short_name="TC",
        name_ru="Команда В",
        country=country,
        slug="team-c",
    )

    TeamExternalMapping.objects.create(source=source1, team=team, external_id="200")
    mapping2 = TeamExternalMapping.objects.create(source=source2, team=team, external_id="200")
    assert mapping2.external_id == "200"
