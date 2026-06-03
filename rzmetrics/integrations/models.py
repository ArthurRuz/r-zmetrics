from django.db import models


class ExternalSource(models.Model):
    name = models.CharField(max_length=100)
    base_url = models.URLField(max_length=500, blank=True)
    is_active = models.BooleanField(default=True)


class TeamExternalMapping(models.Model):
    source = models.ForeignKey('ExternalSource', on_delete=models.CASCADE)
    team = models.ForeignKey('football.Team', on_delete=models.CASCADE, related_name='mappers')
    external_id = models.CharField(max_length=100)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['source', 'external_id'],
                name='unique_team_external_mapping_source_external_id'
            )
        ]


class PlayerExternalMapping(models.Model):
    source = models.ForeignKey('ExternalSource', on_delete=models.CASCADE)
    player = models.ForeignKey('football.Player', on_delete=models.CASCADE, related_name='mappers')
    external_id = models.CharField(max_length=100)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['source', 'external_id'],
                name='unique_player_external_mapping_source_external_id'
            )
        ]


class CompetitionExternalMapping(models.Model):
    source = models.ForeignKey('ExternalSource', on_delete=models.CASCADE)
    competition = models.ForeignKey('football.Competition', on_delete=models.CASCADE, related_name='mappers')
    external_id = models.CharField(max_length=100)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['source', 'external_id'],
                name='unique_competition_external_mapping_source_external_id'
            )
        ]


class MatchExternalMapping(models.Model):
    source = models.ForeignKey('ExternalSource', on_delete=models.CASCADE)
    match = models.ForeignKey('football.Match', on_delete=models.CASCADE, related_name='mappers')
    external_id = models.CharField(max_length=100)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['source', 'external_id'],
                name='unique_match_external_mapping_source_external_id'
            )
        ]


class HeadCoachExternalMapping(models.Model):
    source = models.ForeignKey('ExternalSource', on_delete=models.CASCADE)
    head_coach = models.ForeignKey('football.HeadCoach', on_delete=models.CASCADE, related_name='mappers')
    external_id = models.CharField(max_length=100)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['source', 'external_id'],
                name='unique_head_coach_external_mapping_source_external_id'
            )
        ]