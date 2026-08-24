from django.db.models import Max
from django.utils.decorators import method_decorator

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.games.models import GameScore
from apps.games.serializers import GameScoreSerializer
from apps.users.models import CustomUser

LEADERBOARD_SIZE = 20


@method_decorator(
    name="post",
    decorator=swagger_auto_schema(tags=["Games"]),
)
class GameScoreCreateView(generics.CreateAPIView):
    serializer_class = GameScoreSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(player=self.request.user)

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)

        if (
            isinstance(response, Response)
            and 200 <= response.status_code < 300
            and isinstance(response.data, dict)
            and "success" not in response.data
        ):
            response.data = {
                "success": True,
                "data": response.data,
            }

        return response


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        tags=["Games"],
        manual_parameters=[
            openapi.Parameter(
                "game",
                openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                required=True,
                description="Game slug, e.g. 'zip'.",
            )
        ],
    ),
)
class LeaderboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        game = request.query_params.get("game")
        if game not in GameScore.Game.values:
            return Response(
                {"success": False, "message": "A valid 'game' query parameter is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ranked_players = list(
            CustomUser.objects.filter(game_scores__game=game)
            .annotate(best_score=Max("game_scores__score"))
            .order_by("-best_score", "id")
        )

        leaderboard = [
            {
                "rank": index + 1,
                "player_name": f"{player.first_name} {player.last_name}".strip(),
                "score": player.best_score,
                "is_you": player.id == request.user.id,
            }
            for index, player in enumerate(ranked_players[:LEADERBOARD_SIZE])
        ]

        personal_best = None
        for index, player in enumerate(ranked_players):
            if player.id == request.user.id:
                personal_best = {"rank": index + 1, "score": player.best_score}
                break

        return Response(
            {
                "success": True,
                "data": {"leaderboard": leaderboard, "personal_best": personal_best},
            }
        )
