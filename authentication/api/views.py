from rest_framework.response import Response
from rest_framework.views import APIView


class WelcomeView(APIView):
    def get(self, request):
        return Response({"success": True, "message": "welcome message"})
