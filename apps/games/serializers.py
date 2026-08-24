from rest_framework import serializers

from apps.games.models import GameScore


class GameScoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = GameScore
        fields = ["id", "player", "game", "score", "created_at"]
        read_only_fields = ["id", "player", "created_at"]
