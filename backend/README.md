# Hack2Hire Backend

FastAPI foundation with PostgreSQL, SQLAlchemy 2.0, Alembic, Pydantic v2, and JWT authentication.

## Requirements

- Python 3.12+
- PostgreSQL 14+

## Setup

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
```

Create the database:

```sql
CREATE DATABASE hack2hire;
```

Run migrations:

```bash
alembic upgrade head
```

Start the API:

```bash
python main.py
```

Or:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/health` | Liveness check |
| GET | `/api/v1/health/ready` | Readiness check (database) |
| POST | `/api/v1/auth/register` | Register account |
| POST | `/api/v1/auth/login` | Login |
| POST | `/api/v1/auth/refresh` | Refresh tokens |
| GET | `/api/v1/auth/me` | Current user (Bearer token) |
| POST | `/api/v1/resume/upload` | Upload PDF resume (multipart `file`) |
| GET | `/api/v1/resume` | Get current resume |
| POST | `/api/v1/jd/upload` | Save job description `{ content, title? }` |
| GET | `/api/v1/jd` | Get current job description |

Docs (development): http://localhost:8000/docs

## Docker

From the **project root** (not `backend/`):

```bash
cp .env.example .env   # at repo root — see root README
docker compose up --build
```

The API, PostgreSQL, Redis, and migrations start automatically.
