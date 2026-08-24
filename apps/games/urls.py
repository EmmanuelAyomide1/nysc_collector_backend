from django.urls import path

from apps.games.views import GameScoreCreateView, LeaderboardView

app_name = "games"

urlpatterns = [
    path("scores/", GameScoreCreateView.as_view(), name="game-score-create"),
    path("leaderboard/", LeaderboardView.as_view(), name="game-leaderboard"),
]
