import json

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.db import transaction
from rest_framework_simplejwt.tokens import AccessToken

from authentication.models import User
from game.models import Game


class LobbyConsumer(AsyncWebsocketConsumer):
    LOBBY_GROUP = 'lobby'

    async def connect(self):
        await self.channel_layer.group_add(self.LOBBY_GROUP, self.channel_name)
        await self.accept()
        await self.send_waiting_games()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.LOBBY_GROUP, self.channel_name)

    async def lobby_update(self, event):
        """Called when the lobby group receives an update."""
        await self.send_waiting_games()

    async def send_waiting_games(self):
        games = await self._get_waiting_games()
        await self.send(text_data=json.dumps({
            'type': 'waiting_games',
            'games': games,
        }))

    @database_sync_to_async
    def _get_waiting_games(self):
        games = Game.objects.filter(
            status=Game.STATUS_WAITING,
        ).select_related('player_one').order_by('-created_at')[:20]

        return [
            {
                'id': game.id,
                'player_one': game.player_one.first_name or game.player_one.username,
                'created_at': game.created_at.isoformat(),
            }
            for game in games
        ]


class GameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.game_id = self.scope['url_route']['kwargs']['game_id']
        self.game_group = f'game_{self.game_id}'

        # Authenticate via JWT query param
        query_string = self.scope.get('query_string', b'').decode()
        params = dict(p.split('=', 1) for p in query_string.split('&') if '=' in p)
        token = params.get('token')

        if not token:
            await self.close()
            return

        try:
            access_token = AccessToken(token)
            self.user_id = access_token['user_id']
        except Exception:
            await self.close()
            return

        await self.channel_layer.group_add(self.game_group, self.channel_name)
        await self.accept()

        # Send current game state
        state = await self._get_game_state()
        if state:
            await self.send(text_data=json.dumps(state))

    async def disconnect(self, close_code):
        if hasattr(self, 'game_group'):
            await self.channel_layer.group_discard(self.game_group, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)

        if data.get('type') == 'place_tile':
            result = await self._place_tile(
                slot_index=data['slot_index'],
                hand_index=data['hand_index'],
            )
            if result and result['type'] == 'game_over':
                await self.channel_layer.group_send(
                    self.game_group,
                    {
                        'type': 'game_over',
                        'winner_id': result['winner_id'],
                        'board_state': result['board_state'],
                    },
                )
            elif result and result['type'] == 'tile_placed':
                await self.channel_layer.group_send(
                    self.game_group,
                    {
                        'type': 'game_update',
                        'board_state': result['board_state'],
                        'hand_letters': result['hand_letters'],
                    },
                )

    async def game_start(self, event):
        """Forwarded when a player joins and the game begins."""
        await self.send(text_data=json.dumps({
            'type': 'game_start',
            'game': event['game'],
        }))

    async def game_update(self, event):
        """Forward game state updates to client."""
        await self.send(text_data=json.dumps({
            'type': 'game_update',
            'board_state': event['board_state'],
            'hand_letters': event['hand_letters'],
        }))

    async def game_over(self, event):
        """Broadcast game over with personalized winner flag."""
        await self.send(text_data=json.dumps({
            'type': 'game_over',
            'winner_is_you': event['winner_id'] == self.user_id,
            'board_state': event['board_state'],
        }))

    @database_sync_to_async
    def _get_game_state(self):
        try:
            game = Game.objects.select_related('player_one', 'player_two').get(id=self.game_id)
        except Game.DoesNotExist:
            return None

        return {
            'type': 'game_state',
            'board_state': game.board_state,
            'hand_letters': game.hand_letters,
            'status': game.status,
            'player_one': game.player_one.first_name or game.player_one.username,
            'player_two': (
                game.player_two.first_name or game.player_two.username
            ) if game.player_two else None,
        }

    @database_sync_to_async
    def _place_tile(self, slot_index, hand_index):
        with transaction.atomic():
            game = Game.objects.select_for_update().get(id=self.game_id)

            if game.status != Game.STATUS_IN_PROGRESS:
                return None

            if slot_index < 0 or slot_index >= len(game.board_state):
                return None
            if hand_index < 0 or hand_index >= len(game.hand_letters):
                return None
            if game.board_state[slot_index] is not None:
                return None

            # Place the tile
            game.board_state[slot_index] = game.hand_letters[hand_index]
            game.hand_letters[hand_index] = ''

            # Count how many tiles are on the board
            placed_count = sum(1 for s in game.board_state if s is not None)

            if placed_count >= 2:
                # Second placement wins
                winner = User.objects.get(id=self.user_id)
                game.winner = winner
                game.status = Game.STATUS_COMPLETED
                game.save(update_fields=['board_state', 'hand_letters', 'winner', 'status'])
                return {
                    'type': 'game_over',
                    'winner_id': self.user_id,
                    'board_state': game.board_state,
                }
            else:
                # First placement — broadcast updated board to both players
                game.save(update_fields=['board_state', 'hand_letters'])
                return {
                    'type': 'tile_placed',
                    'board_state': game.board_state,
                    'hand_letters': game.hand_letters,
                }
