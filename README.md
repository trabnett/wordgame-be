# WordGame Backend

A Django REST Framework backend for WordGame — a Wordle-meets-Scrabble multiplayer word game. See `ai_context/proposal.md` in the project root for the full product proposal.

## Tech Stack

- **Framework:** Django + Django REST Framework
- **Database:** PostgreSQL
- **Auth:** JWT via `djangorestframework-simplejwt`, phone-based via Twilio
- **Frontend:** Flutter (separate repo in `wordgame-fe/`)

## Prerequisites

- Python 3.11+
- PostgreSQL 14+ (installed and running) — or Docker
- A Twilio account (for SMS features — not needed for local dev)

## Getting Started (Docker)

The quickest way to get running. Docker Compose spins up two containers:

- **db** — PostgreSQL 16, mapped to host port `5433` (to avoid conflicts with local Postgres)
- **backend** — Django app on port `8181`

### 1. Configure environment

```bash
cd wordgame-be
cp .env.example .env
```

### 2. Build and run

```bash
docker compose up --build
```

The `entrypoint.sh` script handles startup automatically:
1. Waits for PostgreSQL to be ready
2. Runs `manage.py migrate`
3. Starts the Django dev server on `0.0.0.0:8181`

The API will be available at `http://localhost:8181`.

### Create a superuser (optional)

```bash
docker compose exec backend python manage.py createsuperuser
```

Then log in at `http://localhost:8181/admin/`.

### Connect to the database directly

```bash
psql -h localhost -p 5433 -U wordgame wordgame
```

### Common commands

```bash
docker compose up --build     # Build and start
docker compose up -d          # Start in background
docker compose down           # Stop containers
docker compose down -v        # Stop and wipe database
docker compose logs -f        # Tail logs
docker compose exec backend python manage.py <command>  # Run manage.py commands
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

### 3. Set up PostgreSQL

Make sure PostgreSQL is running:

```bash
pg_isready
```

Create the database:

```bash
psql postgres -c "CREATE DATABASE wordgame;"
```

Check your local Postgres user (Homebrew installs typically use your macOS username with no password):

```bash
psql postgres -c "SELECT current_user;"
```

### 4. Configure environment variables

Copy the example and edit as needed:

```bash
cp .env.example .env
```

Key values to set:

| Variable | Description | Local Default |
|----------|-------------|---------------|
| `DJANGO_SECRET_KEY` | Django secret key | Change for production |
| `DJANGO_DEBUG` | Enable debug mode | `True` |
| `DB_NAME` | PostgreSQL database name | `wordgame` |
| `DB_USER` | PostgreSQL user | `wordgame` |
| `DB_PASSWORD` | PostgreSQL password | Empty for local Homebrew |
| `DB_HOST` | Database host | `localhost` |
| `DB_PORT` | Database port | `5432` |

### 5. Run migrations

```bash
python manage.py migrate
```

### 6. Start the development server

```bash
python manage.py runserver 8181
```

The API will be available at `http://localhost:8181`.

## API Routes

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/welcome` | Simple welcome page |
| GET | `/api/welcome` | JSON welcome response |

## Project Structure

```
wordgame-be/
├── config/          # Django project settings and root URL config
│   ├── settings.py
│   ├── urls.py
│   └── ...
├── auth/            # Auth app (views, models, phone auth)
│   ├── views.py     # Template views
│   ├── urls.py      # Template URL routes
│   └── api/         # DRF API views
│       ├── views.py
│       └── urls.py
├── .env             # Environment variables (not committed)
├── requirements.txt
├── docker-compose.yml
├── Dockerfile
├── entrypoint.sh    # Waits for Postgres, runs migrations, starts server
└── manage.py
```
