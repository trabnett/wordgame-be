# WordGame Backend

A Django REST Framework backend for WordGame — a Wordle-meets-Scrabble multiplayer word game. See `ai_context/proposal.md` in the project root for the full product proposal.

## Tech Stack

- **Framework:** Django + Django REST Framework
- **Database:** PostgreSQL
- **Auth:** JWT via `djangorestframework-simplejwt`, phone-based via Twilio
- **Frontend:** Flutter (separate repo in `wordgame-fe/`)

## Prerequisites

- Python 3.11+
- PostgreSQL 14+ (installed and running)
- A Twilio account (for SMS features — not needed for local dev)

## Getting Started

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
| `DB_USER` | PostgreSQL user | Your macOS username |
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
└── manage.py
```
