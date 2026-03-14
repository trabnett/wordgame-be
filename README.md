# WordGame Backend

Django REST Framework + Django Channels backend for WordGame — a Wordle-meets-Scrabble multiplayer word game. See `ai_context/proposal.md` in the project root for the full product proposal.

## Tech Stack

- **Framework:** Django 5.1 + Django REST Framework
- **Real-Time:** Django Channels + Daphne (ASGI server)
- **Database:** PostgreSQL 16
- **Channel Layer:** Redis 7
- **Auth:** JWT via `djangorestframework-simplejwt`, phone-based login
- **Frontend:** Flutter (separate repo in `wordgame-fe/`)

## Prerequisites

- Docker and Docker Compose

## Getting Started (Docker)

Docker Compose spins up three containers:

- **db** — PostgreSQL 16, mapped to host port `5433`
- **redis** — Redis 7, mapped to host port `6379`
- **backend** — Django/Daphne on port `8181`

### 1. Configure environment

```bash
cd wordgame-be
cp .env.example .env
```

Key values to set:

| Variable | Description | Local Default |
|----------|-------------|---------------|
| `DJANGO_SECRET_KEY` | Django secret key | Change for production |
| `DJANGO_DEBUG` | Enable debug mode | `True` |
| `DB_NAME` | PostgreSQL database name | `wordgame` |
| `DB_USER` | PostgreSQL user | `wordgame` |
| `CORS_ALLOWED_ORIGINS` | Allowed frontend origins | `http://localhost:3081` |

Database host, password, and Redis host are overridden by `docker-compose.yml` and don't need to be set in `.env`.

### 2. Build and run

```bash
docker compose up --build
```

The `entrypoint.sh` script handles startup automatically:
1. Waits for PostgreSQL to be ready
2. Runs `manage.py migrate`
3. Starts Daphne on `0.0.0.0:8181`

The API will be available at `http://localhost:8181`.

### 3. Create test users

There's no registration endpoint yet. Create users via the Django shell:

```bash
docker compose exec backend python manage.py shell
```

```python
from authentication.models import User
User.objects.create_user(username='alice', first_name='Alice', phone_number='+15551234567')
User.objects.create_user(username='bob', first_name='Bob', phone_number='+15559876543')
```

Or create a superuser for admin access:

```bash
docker compose exec backend python manage.py createsuperuser
```

Then log in at `http://localhost:8181/admin/`.

## Rebuilding After Code Changes

The Docker image copies code at build time (no volume mount), so after editing backend code:

```bash
docker compose up --build -d
```

## Common Commands

```bash
docker compose up --build     # Build and start
docker compose up -d          # Start in background
docker compose down           # Stop containers
docker compose down -v        # Stop and wipe database
docker compose logs -f        # Tail logs
docker compose exec backend python manage.py <command>  # Run manage.py commands
```

### Connect to the database directly

```bash
psql -h localhost -p 5433 -U wordgame wordgame
```

## Getting Started (Local venv)

### 1. Create and activate a virtual environment

```bash
cd wordgame-be
python3 -m venv venv
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set up PostgreSQL and Redis

Make sure both are running locally. Create the database:

```bash
psql postgres -c "CREATE DATABASE wordgame;"
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

### 5. Run migrations and start the server

```bash
python manage.py migrate
daphne -b 0.0.0.0 -p 8181 config.asgi:application
```

Note: Use `daphne` (not `runserver`) to get WebSocket support.

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/welcome/` | No | Health check / welcome message |
| POST | `/api/login/` | No | Phone-based login, returns JWT tokens |
| POST | `/api/token/refresh/` | No | Refresh an expired access token |
| GET | `/api/user/` | Yes | Get current user's profile |
| POST | `/api/game/` | Yes | Create a new game (optional `phone_number` to invite) |
| POST | `/api/game/<id>/join/` | Yes | Join a waiting game |

## WebSocket Endpoints

| Path | Auth | Description |
|------|------|-------------|
| `ws/lobby/` | None | Live-updating list of waiting games |
| `ws/game/<id>/?token=<jwt>` | JWT query param | Game state sync and tile placement |

### Game WebSocket Messages

**Client sends:**
```json
{"type": "place_tile", "slot_index": 0, "hand_index": 1}
```

**Server sends:**
```json
{"type": "game_state", "board_state": [null,null,null,null,null], "hand_letters": ["A","B","C"], "status": "in_progress", "player_one": "Alice", "player_two": "Bob"}
```
```json
{"type": "game_start", "game": {"id": 1, "status": "in_progress", "player_one": "Alice", "player_two": "Bob"}}
```
```json
{"type": "game_update", "board_state": ["A",null,null,null,null], "hand_letters": ["","B","C"]}
```
```json
{"type": "game_over", "winner_is_you": true, "board_state": ["A","B",null,null,null]}
```

## Project Structure

```
wordgame-be/
├── config/              # Django project settings, ASGI config, root URL conf
│   ├── settings.py
│   ├── urls.py
│   └── asgi.py          # ProtocolTypeRouter for HTTP + WebSocket
├── authentication/      # Custom User model (phone number field), JWT login
│   ├── models.py
│   └── api/
│       ├── views.py     # PhoneLoginView, UserProfileView, WelcomeView
│       └── urls.py
├── game/                # Game model, REST views, WebSocket consumers
│   ├── models.py        # Game model with board_state, hand_letters (JSONFields)
│   ├── consumers.py     # LobbyConsumer, GameConsumer
│   ├── routing.py       # WebSocket URL patterns
│   └── api/
│       ├── views.py     # CreateGameView, JoinGameView
│       └── urls.py
├── .env.example
├── requirements.txt
├── docker-compose.yml
├── Dockerfile
├── entrypoint.sh        # Waits for Postgres, runs migrations, starts Daphne
└── manage.py
```
