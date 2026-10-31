# Professional Portfolio Platform

A full-stack profile product: public portfolio, private dashboard, downloadable CV, analytics, networking, notifications, and an AI writing assistant.

Stack: **React + Vite**, **FastAPI**, **PostgreSQL**.

## Features

- JWT authentication (register / login)
- Public profile at `/u/{username}` and share links at `/s/{token}`
- Experience, education, skills, languages, and project showcases
- Photo upload and PDF CV download (ReportLab)
- Follows, likes, comments, and in-app notifications
- Visit analytics (views, unique visitors, CV downloads, shares)
- AI rewrite for bios and project descriptions (OpenAI if configured, otherwise a local rewriter)

Seeded owner profile is **NTARINDWA Jean Dieudonne**, an aspiring Machine Learning Engineer. Content comes from `backend/data/resume.json` and the photo at `profile-web-app/public/avatar.jpg`. `python seed.py` copies that photo onto the profile and into `/media`. The Download CV button generates an ATS-style PDF from the live profile.

## Project layout

```
backend/                 FastAPI API, Alembic, seed, tests
profile-web-app/        React dashboard and public pages
notebooks/              Colab: Profile_backend.ipynb (this API) and ML leaf GPU notebook
docker-compose.yml      Local PostgreSQL
```

## Prerequisites

- Python 3.12+
- Node.js 20+
- PostgreSQL 16 (or Docker)

## 1. Database

```bash
docker compose up -d db
```

Or create a database named `portfolio` on a local Postgres instance.

Copy environment values from `backend/.env.example` into `backend/.env` and set a strong `SECRET_KEY` before any real deployment.

## 2. Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
alembic upgrade head
python seed.py
python -m uvicorn app.main:app --reload --port 8000
uvicorn app.main:app --reload --port 8000
```

API docs: http://127.0.0.1:8000/docs  
Health: http://127.0.0.1:8000/api/health

Seeded accounts (local demo only):

- Owner: `ntarindwajean11@gmail.com` / `Portfolio2026!`
- Guest: `guest@portfolio.local` / `Guest12345!`

## 3. Frontend

```bash
cd profile-web-app
npm install
npm run dev
```

App: http://127.0.0.1:5173

Vite proxies `/api` and `/media` to the FastAPI server.

## Tests

```bash
cd backend
pytest
```

Tests run against an isolated SQLite file (`backend/tests/testdb.sqlite`) so they do not need PostgreSQL. They cover auth, public/private profiles, CRUD, likes/comments/follows, notifications, analytics, CV download, photo upload, and the AI rewriter.

## Environment

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | Pooled Postgres URL. Neon `postgresql://...` is converted to `postgresql+psycopg://` and `sslmode=require` is added when needed. |
| `DATABASE_URL_UNPOOLED` | Direct Neon URL for Alembic. Leave empty to reuse `DATABASE_URL`. |
| `SECRET_KEY` | JWT signing key |
| `OPENAI_API_KEY` | Optional. Empty uses the local writing fallback |
| `CORS_ORIGINS` | Comma-separated frontend origins |
| `CORS_ORIGIN_REGEX` | Optional origin pattern (Colab notebook sets `https://.*`) |
| `PUBLIC_APP_URL` / `PUBLIC_API_URL` | Used in generated links |
| `ML_BACKEND_URL` | Public Colab tunnel URL from the notebook (leaf inference) |
| `VITE_API_BASE` | Frontend-only. Remote API origin when the UI is not proxied to FastAPI |

## Vercel

Use **two** Vercel projects from the same GitHub repo (`Dieudonne-developer/Profile`).

### 1. API (`backend`)

On New Project:

| Field | Value |
|---|---|
| Project Name | `profile` (or `profile-api`) |
| Root Directory | `backend` |
| Framework Preset | FastAPI |
| Build Command | leave empty |
| Output Directory | N/A |
| Install Command | `pip install -r requirements.txt` |

Environment variables (Production and Preview). Do not wrap values in quotes:

```
DATABASE_URL=postgresql://USER:PASSWORD@HOST-pooler.REGION.aws.neon.tech/neondb?sslmode=require
SECRET_KEY=a-long-random-string
ACCESS_TOKEN_EXPIRE_MINUTES=10080
PUBLIC_API_URL=https://profile.vercel.app
PUBLIC_APP_URL=https://your-frontend.vercel.app
CORS_ORIGINS=https://your-frontend.vercel.app,http://localhost:5173,http://127.0.0.1:5173
CORS_ORIGIN_REGEX=https://.*\.vercel\.app
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini
ML_BACKEND_URL=
```

After the first deploy, set `PUBLIC_API_URL` to the real API hostname Vercel printed. Drop `channel_binding=require` on Vercel; keep `sslmode=require`.

Check `https://<api>.vercel.app/api/health` and `https://<api>.vercel.app/api/u/dieudonne`.

### 2. Website (`profile-web-app`)

Create a **second** Vercel project:

| Field | Value |
|---|---|
| Root Directory | `profile-web-app` |
| Framework Preset | Vite |
| Build Command | `npm run build` |
| Output Directory | `dist` |

Environment:

```
VITE_API_BASE=https://<api>.vercel.app
```

Then add that frontend origin to the API project's `CORS_ORIGINS` and `PUBLIC_APP_URL`.

Photo uploads on Vercel are stored in `/tmp` and do not persist. Neon still stores the rest of the profile.

## Deployment notes

1. Run PostgreSQL and apply `alembic upgrade head`.
2. Serve FastAPI with Uvicorn/Gunicorn behind HTTPS. Set `SECRET_KEY`, CORS, and public URLs for the real domain.
3. Build the UI with `npm run build` in `profile-web-app` and serve `dist/` from Nginx (or any static host). Proxy `/api` and `/media` to the API.
4. Keep uploads on a persistent volume (`backend/app/static/uploads`).
5. Do not commit `.env` or seed passwords into a public production environment.

Example Nginx locations:

```
location /api/ { proxy_pass http://127.0.0.1:8000; }
location /media/ { proxy_pass http://127.0.0.1:8000; }
location / { try_files $uri $uri/ /index.html; }
```

## API map

- `POST /api/auth/register` `POST /api/auth/login` `GET /api/auth/me`
- `GET|PUT /api/profile/me` `POST /api/profile/photo` `POST /api/profile/share-token`
- `GET /api/u/{username}` `GET /api/s/{token}`
- CRUD `/api/experience` `/api/education` `/api/skills` `/api/languages` `/api/projects`
- `GET /api/projects/feed` likes and comments under `/api/projects/{id}`
- `GET /api/network/people` `POST /api/network/follow/{username}`
- `POST /api/analytics/track` `GET /api/analytics/summary`
- `GET /api/notifications`
- `POST /api/ai/improve`
- `GET /api/cv/me` `GET /api/cv/{username}`
- `GET /api/ml/status` `POST /api/ml/predict/score` `POST /api/ml/predict/leaf`

## Google Colab

Two notebooks, two jobs:

- **`notebooks/Profile_backend.ipynb`** — this project's FastAPI profile API (auth, `/api/u/dieudonne`, CV, projects). CPU runtime. Set Colab secret `DATABASE_URL` (Neon), run all cells, then set `VITE_API_BASE` on the React app to the printed `trycloudflare.com` URL.
- **`notebooks/NTARINDWA_ML_Colab_Backend.ipynb`** — GPU inference only. Cordana / Healthy / Pestalotiopsis / Sigatoka are **banana-leaf disease classes**, not profile fields. Set `ML_BACKEND_URL` on FastAPI to that notebook's URL.

Colab sessions go idle and the public URL changes; re-run the tunnel cell and update the env var.

Linear regression (`POST /api/ml/predict/score`) stays on FastAPI so the study-hours demo works even when the ML notebook is offline.
