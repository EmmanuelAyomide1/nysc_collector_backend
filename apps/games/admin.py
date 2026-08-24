from django.contrib import admin

from apps.games.models import GameScore


@admin.register(GameScore)
class GameScoreAdmin(admin.ModelAdmin):
    list_display = ["player", "game", "score", "created_at"]
    list_filter = ["game"]
    search_fields = ["player__email"]
