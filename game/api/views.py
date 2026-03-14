import phonenumbers
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from authentication.models import User
from game.models import Game


class CreateGameView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        phone_number = request.data.get('phone_number')
        player_two = None

        if phone_number:
            # Normalize the phone number
            if not phone_number.startswith('+'):
                phone_number = f'+{phone_number}'

            try:
                parsed = phonenumbers.parse(phone_number, None)
                normalized = phonenumbers.format_number(
                    parsed, phonenumbers.PhoneNumberFormat.E164
                )
            except phonenumbers.NumberParseException:
                return Response(
                    {"success": False, "message": "Invalid phone number."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            player_two = User.objects.filter(phone_number=normalized).first()
            if not player_two:
                return Response(
                    {"success": False, "message": "No user found with that phone number."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            if player_two == request.user:
                return Response(
                    {"success": False, "message": "You can't invite yourself."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        game = Game.objects.create(
            player_one=request.user,
            player_two=player_two,
            status=Game.STATUS_IN_PROGRESS if player_two else Game.STATUS_WAITING,
        )

        return Response({
            "success": True,
            "game": {
                "id": game.id,
                "status": game.status,
                "player_one": game.player_one.first_name or game.player_one.username,
                "player_two": (player_two.first_name or player_two.username) if player_two else None,
            },
        }, status=status.HTTP_201_CREATED)
