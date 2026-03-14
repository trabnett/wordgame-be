import random

from django.conf import settings
from django.db import models


class Game(models.Model):
    STATUS_WAITING = 'waiting'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_COMPLETED = 'completed'
    STATUS_CHOICES = [
        (STATUS_WAITING, 'Waiting for opponent'),
        (STATUS_IN_PROGRESS, 'In progress'),
        (STATUS_COMPLETED, 'Completed'),
    ]

    player_one = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='games_as_player_one',
    )
    player_two = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='games_as_player_two',
        null=True,
        blank=True,
    )
    winner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='games_won',
        null=True,
        blank=True,
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_WAITING,
    )
    board_state = models.JSONField(default=list)
    hand_letters = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=~models.Q(player_one=models.F('player_two')),
                name='players_must_be_different',
            ),
        ]

    def __str__(self):
        return f'Game {self.id}: {self.player_one} vs {self.player_two}'

    def initialize_game_state(self):
        letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        self.board_state = [None] * 5
        self.hand_letters = [random.choice(letters) for _ in range(3)]
