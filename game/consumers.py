import json
from collections import Counter

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.db import transaction
from rest_framework_simplejwt.tokens import AccessToken

from authentication.models import User
from game.dictionary import is_valid_word
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

        # Send current game state (personalized)
        state = await self._get_game_state()
        if state:
            await self.send(text_data=json.dumps(state))

    async def disconnect(self, close_code):
        if hasattr(self, 'game_group'):
            await self.channel_layer.group_discard(self.game_group, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)

        if data.get('type') == 'submit_word':
            word = data.get('word', '').upper().strip()
            result = await self._submit_word(word)

            if result['type'] == 'error':
                # Send error only to the submitting player
                await self.send(text_data=json.dumps(result))
            elif result['type'] == 'game_update':
                await self.channel_layer.group_send(
                    self.game_group,
                    {
                        'type': 'game_state_update',
                        'game_state': result['game_state'],
                    },
                )
            elif result['type'] == 'game_over':
                await self.channel_layer.group_send(
                    self.game_group,
                    {
                        'type': 'game_over_update',
                        'game_state': result['game_state'],
                    },
                )

    async def game_start(self, event):
        """Forwarded when a player joins and the game begins."""
        await self.send(text_data=json.dumps({
            'type': 'game_start',
            'game': event['game'],
        }))

    async def game_state_update(self, event):
        """Personalize and forward game state to this client."""
        state = event['game_state']
        is_p1 = self.user_id == state['player_one_id']

        await self.send(text_data=json.dumps({
            'type': 'game_state',
            'board': state['board'],
            'your_hand': state['p1_hand'] if is_p1 else state['p2_hand'],
            'your_pile_count': state['p1_pile_count'] if is_p1 else state['p2_pile_count'],
            'opponent_pile_count': state['p2_pile_count'] if is_p1 else state['p1_pile_count'],
            'your_turn': state['current_turn_id'] == self.user_id if state['current_turn_id'] else False,
            'opponent_hand_count': state['p2_hand_count'] if is_p1 else state['p1_hand_count'],
            'status': state['status'],
            'last_word': state.get('last_word'),
            'last_player': state.get('last_player'),
            'player_one_name': state['player_one_name'],
            'player_two_name': state['player_two_name'],
        }))

    async def game_over_update(self, event):
        """Personalize and forward game over to this client."""
        state = event['game_state']
        is_p1 = self.user_id == state['player_one_id']

        await self.send(text_data=json.dumps({
            'type': 'game_over',
            'winner_is_you': state['winner_id'] == self.user_id if state['winner_id'] else None,
            'your_pile': state['p1_pile'] if is_p1 else state['p2_pile'],
            'opponent_pile': state['p2_pile'] if is_p1 else state['p1_pile'],
            'your_pile_count': len(state['p1_pile']) if is_p1 else len(state['p2_pile']),
            'opponent_pile_count': len(state['p2_pile']) if is_p1 else len(state['p1_pile']),
            'last_word': state.get('last_word'),
            'last_player': state.get('last_player'),
        }))

    @database_sync_to_async
    def _get_game_state(self):
        try:
            game = Game.objects.select_related(
                'player_one', 'player_two', 'current_turn',
            ).get(id=self.game_id)
        except Game.DoesNotExist:
            return None

        p1_name = game.player_one.first_name or game.player_one.username
        p2_name = (
            game.player_two.first_name or game.player_two.username
        ) if game.player_two else None

        if game.status == Game.STATUS_WAITING:
            return {
                'type': 'game_state',
                'status': 'waiting',
                'board': [],
                'your_hand': [],
                'your_pile_count': 0,
                'opponent_pile_count': 0,
                'your_turn': False,
                'opponent_hand_count': 0,
                'last_word': None,
                'last_player': None,
                'player_one_name': p1_name,
                'player_two_name': p2_name,
            }

        is_p1 = self.user_id == game.player_one_id

        return {
            'type': 'game_state',
            'board': game.board_state,
            'your_hand': game.player_one_hand if is_p1 else game.player_two_hand,
            'your_pile_count': len(game.player_one_pile) if is_p1 else len(game.player_two_pile),
            'opponent_pile_count': len(game.player_two_pile) if is_p1 else len(game.player_one_pile),
            'your_turn': game.current_turn_id == self.user_id if game.current_turn_id else False,
            'opponent_hand_count': len(game.player_two_hand) if is_p1 else len(game.player_one_hand),
            'status': game.status,
            'last_word': None,
            'last_player': None,
            'player_one_name': p1_name,
            'player_two_name': p2_name,
        }

    @database_sync_to_async
    def _submit_word(self, word):
        with transaction.atomic():
            game = Game.objects.select_for_update().get(id=self.game_id)

            if game.status != Game.STATUS_IN_PROGRESS:
                return {'type': 'error', 'message': 'Game is not in progress'}

            if game.current_turn_id != self.user_id:
                return {'type': 'error', 'message': "It's not your turn"}

            if len(word) < 2:
                return {'type': 'error', 'message': 'Word must be at least 2 letters'}

            if not word.isalpha():
                return {'type': 'error', 'message': 'Word must contain only letters'}

            if not is_valid_word(word):
                return {'type': 'error', 'message': f'"{word}" is not a valid word'}

            is_p1 = game.player_one_id == self.user_id
            hand = list(game.player_one_hand if is_p1 else game.player_two_hand)
            pile = list(game.player_one_pile if is_p1 else game.player_two_pile)
            board = list(game.board_state)

            word_counts = Counter(word)
            board_counts = Counter(board)
            hand_counts = Counter(hand)

            # Determine which letters come from hand vs board.
            # Duplicate rule: if you play a letter from hand that's also on the
            # board, you must use ALL board copies of that letter too.
            # This makes the allocation deterministic from just the typed word.
            from_hand = Counter()
            from_board = Counter()

            for letter, needed in word_counts.items():
                on_board = board_counts.get(letter, 0)
                if needed > on_board:
                    # Need some from hand — must use all board copies
                    needed_from_hand = needed - on_board
                    if hand_counts.get(letter, 0) < needed_from_hand:
                        return {
                            'type': 'error',
                            'message': f'Not enough "{letter}" available',
                        }
                    from_hand[letter] = needed_from_hand
                    from_board[letter] = on_board
                else:
                    # All from board
                    from_board[letter] = needed

            if sum(from_hand.values()) == 0:
                return {
                    'type': 'error',
                    'message': 'You must play at least one letter from your hand',
                }

            # Unused board letters go to the player's pile
            unused = board_counts.copy()
            for letter, count in from_board.items():
                unused[letter] -= count
            pile_additions = list(unused.elements())

            # Update hand (remove used letters)
            new_hand = list(hand)
            for letter, count in from_hand.items():
                for _ in range(count):
                    new_hand.remove(letter)

            new_pile = pile + pile_additions
            new_board = list(word)

            # Save current player's state
            if is_p1:
                game.player_one_hand = sorted(new_hand)
                game.player_one_pile = sorted(new_pile)
            else:
                game.player_two_hand = sorted(new_hand)
                game.player_two_pile = sorted(new_pile)

            # Fetch player names without triggering a JOIN on the locked row
            p1_user = User.objects.only('first_name', 'username').get(id=game.player_one_id)
            p2_user = User.objects.only('first_name', 'username').get(id=game.player_two_id)
            p1_name = p1_user.first_name or p1_user.username
            p2_name = p2_user.first_name or p2_user.username
            current_name = p1_name if is_p1 else p2_name

            # Check end condition: player emptied their hand
            if len(new_hand) == 0:
                # Other player takes the remaining board (= the word just played)
                other_pile = list(
                    game.player_two_pile if is_p1 else game.player_one_pile
                )
                other_pile.extend(new_board)
                if is_p1:
                    game.player_two_pile = sorted(other_pile)
                else:
                    game.player_one_pile = sorted(other_pile)

                game.board_state = []
                game.status = Game.STATUS_COMPLETED
                game.current_turn = None

                p1_count = len(game.player_one_pile)
                p2_count = len(game.player_two_pile)
                if p1_count < p2_count:
                    game.winner_id = game.player_one_id
                elif p2_count < p1_count:
                    game.winner_id = game.player_two_id
                # else: tie — winner stays None

                game.save(update_fields=Game.GAME_STATE_FIELDS)

                return {
                    'type': 'game_over',
                    'game_state': {
                        'player_one_id': game.player_one_id,
                        'player_two_id': game.player_two_id,
                        'p1_pile': list(game.player_one_pile),
                        'p2_pile': list(game.player_two_pile),
                        'winner_id': game.winner_id,
                        'last_word': word,
                        'last_player': current_name,
                    },
                }

            # Normal turn — switch turns
            game.current_turn_id = game.player_two_id if is_p1 else game.player_one_id
            game.board_state = new_board
            game.save(update_fields=Game.GAME_STATE_FIELDS)

            return {
                'type': 'game_update',
                'game_state': {
                    'board': new_board,
                    'p1_hand': list(game.player_one_hand),
                    'p2_hand': list(game.player_two_hand),
                    'p1_pile_count': len(game.player_one_pile),
                    'p2_pile_count': len(game.player_two_pile),
                    'p1_hand_count': len(game.player_one_hand),
                    'p2_hand_count': len(game.player_two_hand),
                    'current_turn_id': game.current_turn_id,
                    'player_one_id': game.player_one_id,
                    'player_two_id': game.player_two_id,
                    'player_one_name': p1_name,
                    'player_two_name': p2_name,
                    'status': game.status,
                    'last_word': word,
                    'last_player': current_name,
                },
            }
