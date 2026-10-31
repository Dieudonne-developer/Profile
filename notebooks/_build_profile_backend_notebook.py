"""Generate notebooks/Profile_backend.ipynb"""
from __future__ import annotations

import json
from pathlib import Path


def cell(kind: str, source: str) -> dict:
    lines = source.strip("\n").split("\n")
    text = [line + "\n" for line in lines[:-1]] + ([lines[-1]] if lines else [""])
    item = {"cell_type": kind, "metadata": {}, "source": text}
    if kind == "code":
        item["execution_count"] = None
        item["outputs"] = []
    return item


cells = [
    cell(
        "markdown",
        """# Profile backend (Google Colab)

This notebook runs the **portfolio FastAPI app** from `backend/` so a hosted React site can use Colab as the API.

It is **not** the banana-leaf ML notebook. Those names (Cordana, Healthy, Pestalotiopsis, Sigatoka) are plant-disease labels for the computer-vision demo in `NTARINDWA_ML_Colab_Backend.ipynb`. This file serves your profile: login, public page data, projects, CV PDF, analytics.

| Layer | What it does |
|---|---|
| React `profile-web-app` | Pages and dashboard (host this on Netlify/Vercel or run locally) |
| This Colab notebook | FastAPI: `/api/auth`, `/api/u/{username}`, CV, projects, analytics |
| Neon Postgres | Stored profiles (set `DATABASE_URL` in Colab secrets) |

CPU is enough. A GPU is not required.

**How to run:** Runtime → Run all. When the tunnel cell prints a `https://….trycloudflare.com` URL, that origin is your API. Open `/` or `/docs` in the browser. Point the frontend at it with `VITE_API_BASE`.""",
    ),
    cell(
        "markdown",
        """## 1. Database URL and frontend origin

The API needs a Neon Postgres `DATABASE_URL`. Use either option:

**Recommended:** Colab left sidebar → key icon (Secrets) → add `DATABASE_URL` → paste the Neon pooled URL → turn **Notebook access** on. Also add `SECRET_KEY` (long random string). Optional: `DATABASE_URL_UNPOOLED`, `OPENAI_API_KEY`.

**Or paste in the next cell:** set `PASTE_DATABASE_URL` (and optionally `PASTE_SECRET_KEY`). Secrets win if both are set.

Use the **pooler** Neon URL (`...-pooler....neon.tech...`). Set `FRONTEND_URL` to the site that will call this API.""",
    ),
    cell(
        "code",
        r"""import os, sys, shutil, subprocess, zipfile
from pathlib import Path

FRONTEND_URL = "http://localhost:5173"
GIT_URL = "https://github.com/Dieudonne-developer/Profile.git"
PORT = 8000
PROJECT = Path("/content/Profile")

# Neon connection (pooler). Colab Secrets named DATABASE_URL still take priority.
PASTE_DATABASE_URL = "postgresql://neondb_owner:npg_sNYgn4GIjz1p@ep-soft-morning-arzidpvr-pooler.c-4.us-west-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
PASTE_DATABASE_URL_UNPOOLED = "postgresql://neondb_owner:npg_sNYgn4GIjz1p@ep-soft-morning-arzidpvr.c-4.us-west-2.aws.neon.tech/neondb?sslmode=require"
PASTE_SECRET_KEY = "dev-local-portfolio-change-before-any-public-deploy"

def clean_url(value):
    return (value or "").strip().strip('"').strip("'")

def secret(name):
    try:
        from google.colab import userdata
        value = userdata.get(name)
        if value:
            return clean_url(value)
    except Exception:
        pass
    return clean_url(os.environ.get(name, ""))

DATABASE_URL = secret("DATABASE_URL") or clean_url(PASTE_DATABASE_URL)
DATABASE_URL_UNPOOLED = secret("DATABASE_URL_UNPOOLED") or clean_url(PASTE_DATABASE_URL_UNPOOLED)
SECRET_KEY = secret("SECRET_KEY") or clean_url(PASTE_SECRET_KEY) or "colab-change-this-secret-key-please"
OPENAI_API_KEY = secret("OPENAI_API_KEY")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is missing. The notebook cannot connect to Neon Postgres.\\n"
        "Recommended: Colab left sidebar \u2192 key icon (Secrets) \u2192 add DATABASE_URL "
        "and enable Notebook access.\\n"
        "Or paste the connection string into PASTE_DATABASE_URL in this cell."
    )

print("FRONTEND_URL", FRONTEND_URL)
print("DATABASE_URL host", DATABASE_URL.split("@")[-1][:80])""",
    ),
    cell(
        "markdown",
        """## 2. Put the project on this runtime

Use one of:

1. Already uploaded `/content/Profile/backend` (Drive or files panel), or
2. Set `GIT_URL` and clone, or
3. Run the next cell and upload a zip of the repo (must contain `backend/app`).""",
    ),
    cell(
        "code",
        r"""def has_backend(root: Path) -> bool:
    return (root / "backend" / "app" / "main.py").exists()

if has_backend(PROJECT):
    print("using existing", PROJECT)
elif GIT_URL:
    if PROJECT.exists():
        shutil.rmtree(PROJECT)
    subprocess.check_call(["git", "clone", "--depth", "1", GIT_URL, str(PROJECT)])
    print("cloned", GIT_URL)
else:
    from google.colab import files
    print("Upload a zip of the Profile repo (top level should include backend/).")
    uploaded = files.upload()
    if not uploaded:
        raise RuntimeError("No zip uploaded and no GIT_URL set.")
    name = next(iter(uploaded))
    zip_path = Path("/content") / name
    extract = Path("/content/_profile_unpack")
    if extract.exists():
        shutil.rmtree(extract)
    extract.mkdir()
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(extract)
    found = None
    for candidate in [extract, *extract.iterdir()]:
        if candidate.is_dir() and has_backend(candidate):
            found = candidate
            break
        if candidate.is_dir() and (candidate / "app" / "main.py").exists():
            PROJECT.mkdir(parents=True, exist_ok=True)
            dest = PROJECT / "backend"
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(candidate, dest)
            found = PROJECT
            break
    if found is None:
        raise RuntimeError("Could not find backend/app/main.py in the zip.")
    if found.resolve() != PROJECT.resolve():
        if PROJECT.exists():
            shutil.rmtree(PROJECT)
        shutil.copytree(found, PROJECT)
    print("unpacked project to", PROJECT)

BACKEND = PROJECT / "backend"
assert (BACKEND / "app" / "main.py").exists(), BACKEND
print("backend", BACKEND)""",
    ),
    cell(
        "markdown",
        """## 3. Install API packages""",
    ),
    cell(
        "code",
        r"""subprocess.check_call([
    sys.executable, "-m", "pip", "install", "-q", "-r", str(BACKEND / "requirements.txt"),
])
print("packages ready")""",
    ),
    cell(
        "markdown",
        """## 4. Environment, schema, seed profile

Writes `backend/.env`, creates tables, and loads `backend/data/resume.json` (NTARINDWA Jean Dieudonne).""",
    ),
    cell(
        "code",
        r"""env_path = BACKEND / ".env"
cors = ",".join([
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    FRONTEND_URL.rstrip("/"),
])
env_path.write_text(
    "\n".join([
        f"DATABASE_URL={DATABASE_URL}",
        f"DATABASE_URL_UNPOOLED={DATABASE_URL_UNPOOLED}",
        f"SECRET_KEY={SECRET_KEY}",
        f"OPENAI_API_KEY={OPENAI_API_KEY}",
        "OPENAI_MODEL=gpt-4o-mini",
        f"PUBLIC_API_URL=http://127.0.0.1:{PORT}",
        f"PUBLIC_APP_URL={FRONTEND_URL.rstrip('/')}",
        f"CORS_ORIGINS={cors}",
        r"CORS_ORIGIN_REGEX=https://.*",
        "ML_BACKEND_URL=",
        "",
    ]),
    encoding="utf-8",
)

os.environ.update({
    "DATABASE_URL": DATABASE_URL,
    "DATABASE_URL_UNPOOLED": DATABASE_URL_UNPOOLED,
    "SECRET_KEY": SECRET_KEY,
    "OPENAI_API_KEY": OPENAI_API_KEY,
    "PUBLIC_API_URL": f"http://127.0.0.1:{PORT}",
    "PUBLIC_APP_URL": FRONTEND_URL.rstrip("/"),
    "CORS_ORIGINS": cors,
    "CORS_ORIGIN_REGEX": r"https://.*",
})

os.chdir(BACKEND)
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.core.config import get_settings
get_settings.cache_clear()

import seed as seed_mod
seed_mod.main()
print("schema + seed done")""",
    ),
    cell(
        "markdown",
        """## 5. Start FastAPI and a public HTTPS URL

After this cell, open the printed URL. You should see JSON with `"status": "ok"` (not Not Found). Interactive docs: `/docs`. Public profile JSON: `/api/u/dieudonne`.""",
    ),
    cell(
        "code",
        r"""import re, threading, time, urllib.request
import uvicorn

from app.core.config import get_settings
get_settings.cache_clear()
from app.main import app as portfolio_app

uvicorn_server = uvicorn.Server(
    uvicorn.Config(portfolio_app, host="0.0.0.0", port=PORT, log_level="info")
)
threading.Thread(target=uvicorn_server.run, daemon=True).start()

ready = False
for _ in range(50):
    time.sleep(0.25)
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/api/health", timeout=2) as resp:
            if resp.status == 200:
                ready = True
                break
    except Exception:
        pass
if not ready:
    raise RuntimeError("FastAPI did not start. Scroll up for import or database errors.")

cf = Path("/content/cloudflared")
if not cf.exists():
    subprocess.check_call([
        "wget", "-q", "-O", str(cf),
        "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64",
    ])
    cf.chmod(0o755)

tunnel = subprocess.Popen(
    [str(cf), "tunnel", "--url", f"http://127.0.0.1:{PORT}", "--no-autoupdate"],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
)

PUBLIC_URL = None
for line in tunnel.stdout:
    print(line.rstrip())
    match = re.search(r"https://[a-z0-9-]+\.trycloudflare\.com", line)
    if match:
        PUBLIC_URL = match.group(0)
        break
if not PUBLIC_URL:
    raise RuntimeError("No public URL. Re-run this cell.")

os.environ["PUBLIC_API_URL"] = PUBLIC_URL
get_settings.cache_clear()

print()
print("========== PROFILE BACKEND ==========")
print("API origin:     ", PUBLIC_URL)
print("Browser check:  ", PUBLIC_URL + "/")
print("Health:         ", PUBLIC_URL + "/api/health")
print("Docs:           ", PUBLIC_URL + "/docs")
print("Public profile: ", PUBLIC_URL + "/api/u/dieudonne")
print()
print("Hosted or local frontend:")
print(f"  VITE_API_BASE={PUBLIC_URL}")
print("Rebuild the React app after setting that, or put it in profile-web-app/.env")
print("====================================")""",
    ),
    cell(
        "markdown",
        """## 6. Connect the profile website

Local UI:

```
cd profile-web-app
echo VITE_API_BASE=YOUR_TRYCLOUDFLARE_URL > .env
npm run dev
```

Hosted UI: set `VITE_API_BASE` to the same URL, rebuild, and redeploy. Also add that site origin to `FRONTEND_URL` above and re-run from the env cell if the browser blocks CORS.

Leave the next cell running so Colab does not idle-stop the API. If the Cloudflare URL changes, update `VITE_API_BASE` again.""",
    ),
    cell(
        "code",
        r"""from datetime import datetime, timezone

print("Serving profile API", PUBLIC_URL)
print("started", datetime.now(timezone.utc).isoformat())
try:
    while True:
        time.sleep(240)
        print(datetime.now(timezone.utc).strftime("%H:%M:%S"), "still serving", PUBLIC_URL, flush=True)
except KeyboardInterrupt:
    print("stopped")""",
    ),
]

nb = {
    "nbformat": 4,
    "nbformat_minor": 5,
    "metadata": {
        "colab": {"provenance": []},
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python"},
    },
    "cells": cells,
}

out = Path(__file__).resolve().parent / "Profile_backend.ipynb"
out.write_text(json.dumps(nb, indent=1), encoding="utf-8")
print("wrote", out)
