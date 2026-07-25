from rest_framework.views import APIView
from rest_framework.response import Response

from apps.users.serializers import UserSerializer


class CurrentUserView(APIView):
    def get(self, request):
        return Response({"success": True, "data": UserSerializer(request.user).data})
