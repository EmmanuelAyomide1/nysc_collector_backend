from django.core.validators import MinValueValidator
from django.db import models

from apps.common.models import BaseModel
from apps.users.models import CustomUser


class GameScore(BaseModel):
    class Game(models.TextChoices):
        ZIP = "zip", "Zip"
        TYPING = "typing", "Typing"

    player = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="game_scores"
    )
    game = models.CharField(max_length=20, choices=Game.choices)
    score = models.PositiveIntegerField(validators=[MinValueValidator(0)])

    def __str__(self):
        return f"{self.player.email} - {self.game} ({self.score})"
