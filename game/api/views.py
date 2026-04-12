import os

import phonenumbers
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from authentication.models import User
from game.models import Game
from services.twilio.twilio_service import TwilioService


def notify_lobby():
    """Broadcast to all lobby WebSocket clients to refresh their game list."""
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        'lobby',
        {'type': 'lobby_update'},
    )


class CreateGameView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        phone_number = request.data.get('phone_number')
        player_two = None

        if phone_number:
            try:
                parsed = phonenumbers.parse(phone_number, 'US')
                normalized = phonenumbers.format_number(
                    parsed, phonenumbers.PhoneNumberFormat.E164
                )
            except phonenumbers.NumberParseException:
                return Response(
                    {"success": False, "message": "Invalid phone number."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            player_two = User.objects.filter(phone_number=normalized).first()

            if player_two and player_two == request.user:
                return Response(
                    {"success": False, "message": "You can't invite yourself."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        game = Game.objects.create(
            player_one=request.user,
            status=Game.STATUS_WAITING,
        )

        notify_lobby()

        if phone_number:
            try:
                twilio = TwilioService()
                base_url = os.getenv('FE_BASE_URL', 'http://35.183.28.89')
                game_path = f'/waiting/{game.id}'
                if player_two:
                    link = f'{base_url}{game_path}'
                else:
                    link = f'{base_url}/login?next={game_path}&phone={normalized}'
                twilio.send_message(
                    normalized,
                    f"A friend has invited you to play Maranga! Join here: {link}",
                )
            except Exception:
                pass

        return Response({
            "success": True,
            "game": {
                "id": game.id,
                "status": game.status,
                "player_one": game.player_one.first_name or game.player_one.username,
                "player_two": (player_two.first_name or player_two.username) if player_two else None,
            },
        }, status=status.HTTP_201_CREATED)


class JoinGameView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, game_id):
        try:
            game = Game.objects.get(id=game_id, status=Game.STATUS_WAITING)
        except Game.DoesNotExist:
            return Response(
                {"success": False, "message": "Game not found or no longer available."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if game.player_one == request.user:
            return Response(
                {"success": False, "message": "You can't join your own game."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        game.player_two = request.user
        game.status = Game.STATUS_IN_PROGRESS
        game.initialize_game_state()
        game.save(update_fields=['player_two', 'status'] + Game.GAME_STATE_FIELDS)

        notify_lobby()

        game_data = {
            "id": game.id,
            "status": game.status,
            "player_one": game.player_one.first_name or game.player_one.username,
            "player_two": request.user.first_name or request.user.username,
        }

        # Notify players waiting on the game WebSocket
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'game_{game.id}',
            {
                'type': 'game_start',
                'game': game_data,
            },
        )

        return Response({
            "success": True,
            "game": game_data,
        })
