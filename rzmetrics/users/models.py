from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    favorite_teams = models.ManyToManyField(
        'football.Team',
        blank=True,
        related_name='users'
    )
    favorite_players = models.ManyToManyField(
        'football.Player',
        blank=True,
        related_name='users'
    )
    favorite_competitions = models.ManyToManyField(
        'football.Competition',
        blank=True,
        related_name='users'
    )
    avatar = models.ImageField(
        upload_to='users/avatars/',
        null=True,
        blank=True
    )
    date_birth = models.DateField(blank=True, null=True, verbose_name="Дата рождения")

    class Meta:
        db_table = 'auth_user'

        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

