"""Generate notebooks/NTARINDWA_ML_Colab_Backend.ipynb. Run from repo root or this folder."""
from __future__ import annotations

import json
from pathlib import Path


def cell(cell_type: str, source: str) -> dict:
    lines = source.strip("\n").split("\n")
    text = [line + "\n" for line in lines[:-1]] + ([lines[-1]] if lines else [""])
    item = {"cell_type": cell_type, "metadata": {}, "source": text}
    if cell_type == "code":
        item["execution_count"] = None
        item["outputs"] = []
    return item


cells = [
    cell(
        "markdown",
        """# NTARINDWA ML backend (Google Colab)

This notebook is the **machine-learning backend** for the Professional Portfolio Platform.

The hosted React app and FastAPI API keep auth, profiles, Postgres (Neon), CV PDFs, and analytics. Colab is used for **GPU inference** and for a public tunnel so the hosted site can call the models.

| Piece | Where it runs |
|---|---|
| Public site + dashboard | Hosted React (`profile-web-app`) |
| Auth, profile, CV, analytics | FastAPI + Neon |
| Study-hours linear regression | Trained here; also mirrored in FastAPI |
| Banana-leaf EfficientNet-B0 | Trained and served **here** (GPU) |

**Classes:** Cordana, Healthy, Pestalotiopsis, Sigatoka.

Open in Colab: Runtime → Change runtime type → **GPU**. Then run all cells. Copy the printed public URL into `ML_BACKEND_URL` on the hosted FastAPI server (or into `VITE_API_BASE` if you run the optional full-API mode).""",
    ),
    cell(
        "markdown",
        """## 1. Install packages

Uses FastAPI + Uvicorn for the HTTP API, PyTorch / torchvision for EfficientNet-B0, scikit-learn for the score model, and cloudflared for a public HTTPS URL (so a hosted backend can reach this runtime).""",
    ),
    cell(
        "code",
        r"""import os, sys, subprocess

def pip_install(*packages: str) -> None:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", *packages])

pip_install(
    "fastapi>=0.115",
    "uvicorn[standard]>=0.34",
    "python-multipart",
    "pydantic>=2.10",
    "scikit-learn",
    "matplotlib",
    "pillow",
    "httpx",
)

import torch
print("torch", torch.__version__, "| cuda", torch.cuda.is_available())
if torch.cuda.is_available():
    print("GPU", torch.cuda.get_device_name(0))
else:
    print("No GPU — banana-leaf inference will run on CPU. Runtime → Change runtime type → GPU is recommended.")""",
    ),
    cell(
        "markdown",
        """## 2. Configuration

Set `MODE`:

- `ml` — only the ML microservice (recommended when FastAPI is already hosted).
- `full` — also serve the portfolio FastAPI from this Colab session (needs the `backend/` folder and Neon `DATABASE_URL`).""",
    ),
    cell(
        "code",
        r"""from pathlib import Path

MODE = "ml"  # "ml" or "full"
PORT = 8000
LEAF_CLASSES = ["Cordana", "Healthy", "Pestalotiopsis", "Sigatoka"]
WORK = Path("/content/ntarindwa_ml")
WORK.mkdir(parents=True, exist_ok=True)
WEIGHTS = WORK / "efficientnet_b0_leaf.pt"
DATA_DIR = WORK / "banana_leaf"

# Optional: path to a zip of ImageFolder data (class-named subfolders).
# Example Drive file: /content/drive/MyDrive/banana_leaf.zip
DATASET_ZIP = os.environ.get("BANANA_DATASET_ZIP", "")

try:
    from google.colab import userdata
    def secret(name, default=""):
        try:
            return userdata.get(name)
        except Exception:
            return default
except Exception:
    def secret(name, default=""):
        return os.environ.get(name, default)

# Used only in MODE == "full"
DATABASE_URL = secret("DATABASE_URL", os.environ.get("DATABASE_URL", ""))
SECRET_KEY = secret("SECRET_KEY", os.environ.get("SECRET_KEY", "colab-dev-change-me"))
CORS_ORIGINS = secret(
    "CORS_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173,https://localhost:5173",
)

print("MODE", MODE)
print("work dir", WORK)""",
    ),
    cell(
        "markdown",
        """## 3. Student performance — linear regression

Same demo as the portfolio project: weekly study hours → examination score. Coefficients are saved so FastAPI and Colab stay aligned.""",
    ),
    cell(
        "code",
        r"""import json
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score

rng = np.random.default_rng(42)
hours = rng.uniform(0.5, 12.0, size=80)
noise = rng.normal(0, 4.5, size=80)
scores = np.clip(40.12 + 6.47 * hours + noise, 0, 100)

X = hours.reshape(-1, 1)
y = scores
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=7)

reg = LinearRegression().fit(X_train, y_train)
SCORE_INTERCEPT = float(reg.intercept_)
SCORE_SLOPE = float(reg.coef_[0])
pred = reg.predict(X_test)

print(f"intercept = {SCORE_INTERCEPT:.4f}")
print(f"slope     = {SCORE_SLOPE:.4f}")
print(f"MAE       = {mean_absolute_error(y_test, pred):.3f}")
print(f"R²        = {r2_score(y_test, pred):.3f}")
print("example: 6 hours →", round(float(np.clip(SCORE_INTERCEPT + SCORE_SLOPE * 6, 0, 100)), 2))

(WORK / "score_model.json").write_text(json.dumps({
    "intercept": SCORE_INTERCEPT,
    "slope": SCORE_SLOPE,
    "model": "ordinary least squares linear regression",
}, indent=2))

plt.figure(figsize=(6, 4))
plt.scatter(hours, scores, alpha=0.7, label="samples")
line_x = np.linspace(0, 12, 50)
plt.plot(line_x, SCORE_INTERCEPT + SCORE_SLOPE * line_x, color="black", label="fitted line")
plt.xlabel("Weekly study hours")
plt.ylabel("Examination score")
plt.title("Student performance (OLS)")
plt.legend()
plt.tight_layout()
plt.show()""",
    ),
    cell(
        "markdown",
        """## 4. Banana-leaf disease — EfficientNet-B0

Four-class image classifier. If you attach a real ImageFolder dataset (zip with folders `Cordana`, `Healthy`, `Pestalotiopsis`, `Sigatoka`), this cell fine-tunes EfficientNet-B0. Otherwise it trains a **short demo** on generated leaf-like images so the HTTP API still works end-to-end. Replace the demo weights before any field use.""",
    ),
    cell(
        "code",
        r"""import zipfile
import shutil
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

import torch
from torch import nn
from torch.utils.data import DataLoader
from torchvision import datasets, models, transforms

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def extract_zip_if_given() -> None:
    zip_path = Path(DATASET_ZIP) if DATASET_ZIP else None
    if zip_path and zip_path.exists():
        target = DATA_DIR
        if target.exists():
            shutil.rmtree(target)
        target.mkdir(parents=True)
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(target)
        print("extracted", zip_path, "→", target)
        return
    drive_zip = Path("/content/drive/MyDrive/banana_leaf.zip")
    if drive_zip.exists():
        if not DATA_DIR.exists():
            DATA_DIR.mkdir(parents=True)
            with zipfile.ZipFile(drive_zip) as zf:
                zf.extractall(DATA_DIR)
            print("extracted Drive zip →", DATA_DIR)


def looks_like_imagefolder(root: Path) -> bool:
    if not root.exists():
        return False
    names = {p.name for p in root.iterdir() if p.is_dir()}
    if set(LEAF_CLASSES).issubset(names):
        return True
    for child in root.iterdir():
        if child.is_dir() and set(LEAF_CLASSES).issubset({p.name for p in child.iterdir() if p.is_dir()}):
            return True
    return False


def imagefolder_root(root: Path) -> Path:
    names = {p.name for p in root.iterdir() if p.is_dir()}
    if set(LEAF_CLASSES).issubset(names):
        return root
    for child in root.iterdir():
        if child.is_dir() and set(LEAF_CLASSES).issubset({p.name for p in child.iterdir() if p.is_dir()}):
            return child
    raise FileNotFoundError("ImageFolder class folders not found")


def synthesize_demo_leaves(root: Path, per_class: int = 24) -> None:
    # Small labelled set so the serving pipeline can be tested without Kaggle data.
    rng = np.random.default_rng(11)
    palettes = {
        "Healthy": ((46, 140, 62), (90, 190, 80)),
        "Sigatoka": ((70, 120, 40), (210, 190, 40)),
        "Cordana": ((90, 110, 40), (140, 70, 30)),
        "Pestalotiopsis": ((80, 130, 50), (230, 230, 210)),
    }
    for label, (base, accent) in palettes.items():
        folder = root / label
        folder.mkdir(parents=True, exist_ok=True)
        for i in range(per_class):
            img = Image.new("RGB", (224, 224), base)
            draw = ImageDraw.Draw(img)
            for _ in range(18):
                x, y = int(rng.integers(10, 200)), int(rng.integers(10, 200))
                r = int(rng.integers(6, 28))
                draw.ellipse((x - r, y - r, x + r, y + r), fill=accent)
            img = img.filter(ImageFilter.GaussianBlur(radius=1.2))
            img = ImageEnhance.Color(img).enhance(1.1)
            img.save(folder / f"{label.lower()}_{i:03d}.png")
    print("wrote demo leaves under", root)


extract_zip_if_given()
if looks_like_imagefolder(DATA_DIR):
    LEAF_ROOT = imagefolder_root(DATA_DIR)
    DEMO_DATA = False
    print("using dataset at", LEAF_ROOT)
else:
    LEAF_ROOT = DATA_DIR / "demo"
    synthesize_demo_leaves(LEAF_ROOT)
    DEMO_DATA = True

train_tf = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.RandomHorizontalFlip(),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
])
eval_tf = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
])

full_ds = datasets.ImageFolder(str(LEAF_ROOT), transform=train_tf)
class_to_idx = full_ds.class_to_idx
idx_to_class = {i: c for c, i in class_to_idx.items()}
print("class_to_idx", class_to_idx)

n = len(full_ds)
n_val = max(8, int(0.2 * n))
n_train = n - n_val
train_ds, val_ds = torch.utils.data.random_split(full_ds, [n_train, n_val], generator=torch.Generator().manual_seed(0))
train_loader = DataLoader(train_ds, batch_size=8, shuffle=True)
val_loader = DataLoader(val_ds, batch_size=8)

def build_model() -> nn.Module:
    try:
        weights = models.EfficientNet_B0_Weights.DEFAULT
        model = models.efficientnet_b0(weights=weights)
    except Exception:
        model = models.efficientnet_b0(weights=None)
    in_features = model.classifier[1].in_features
    model.classifier[1] = nn.Linear(in_features, len(LEAF_CLASSES))
    return model.to(DEVICE)

leaf_model = build_model()
epochs = 2 if DEMO_DATA else 4
criterion = nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(leaf_model.parameters(), lr=1e-4)

for epoch in range(1, epochs + 1):
    leaf_model.train()
    running = 0.0
    correct = 0
    total = 0
    for images, labels in train_loader:
        images, labels = images.to(DEVICE), labels.to(DEVICE)
        optimizer.zero_grad()
        logits = leaf_model(images)
        loss = criterion(logits, labels)
        loss.backward()
        optimizer.step()
        running += float(loss.item()) * images.size(0)
        correct += int((logits.argmax(1) == labels).sum().item())
        total += images.size(0)
    leaf_model.eval()
    v_correct = 0
    v_total = 0
    with torch.no_grad():
        for images, labels in val_loader:
            images, labels = images.to(DEVICE), labels.to(DEVICE)
            logits = leaf_model(images)
            v_correct += int((logits.argmax(1) == labels).sum().item())
            v_total += images.size(0)
    print(
        f"epoch {epoch}/{epochs}  train_loss={running/max(total,1):.4f}  "
        f"train_acc={correct/max(total,1):.3f}  val_acc={v_correct/max(v_total,1):.3f}"
    )

torch.save({
    "state_dict": leaf_model.state_dict(),
    "idx_to_class": idx_to_class,
    "class_to_idx": class_to_idx,
    "demo_data": DEMO_DATA,
}, WEIGHTS)
print("saved", WEIGHTS)
leaf_model.eval()""",
    ),
    cell(
        "markdown",
        """## 5. FastAPI microservice

Endpoints the hosted app already calls:

- `GET /` status page (open the public URL in a browser)
- `GET /health` and `GET /status`
- `POST /predict/score` JSON `{"hours": 6}`
- `POST /predict/leaf` multipart file field `file`
- Interactive docs at `/docs`"""
    ),
    cell(
        "code",
        r"""from typing import Dict
from io import BytesIO

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, Field

leaf_model.eval()
LEAF_IDX = idx_to_class


def predict_score_value(hours: float) -> float:
    return round(float(np.clip(SCORE_INTERCEPT + SCORE_SLOPE * hours, 0, 100)), 2)


@torch.no_grad()
def predict_leaf_image(raw: bytes) -> Dict:
    image = Image.open(BytesIO(raw)).convert("RGB")
    tensor = eval_tf(image).unsqueeze(0).to(DEVICE)
    logits = leaf_model(tensor)
    probs = torch.softmax(logits, dim=1)[0].cpu().tolist()
    mapped = {LEAF_IDX[i]: round(float(p), 4) for i, p in enumerate(probs)}
    # Align keys to the portfolio class list when names match.
    ordered = {name: mapped.get(name, mapped.get(str(i), 0.0)) for i, name in enumerate(LEAF_CLASSES)}
    if set(mapped) != set(LEAF_CLASSES):
        ordered = mapped
    label = max(ordered, key=ordered.get)
    return {
        "label": label,
        "confidence": ordered[label],
        "probabilities": ordered,
        "model": "EfficientNet-B0",
        "backend": "colab-gpu" if DEVICE.type == "cuda" else "colab-cpu",
        "device": str(DEVICE),
        "demo_weights": bool(DEMO_DATA),
    }


ml_app = FastAPI(title="NTARINDWA Colab ML backend", version="1.0.0")
origins = [item.strip() for item in CORS_ORIGINS.split(",") if item.strip()] + ["*"]
ml_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ScoreIn(BaseModel):
    hours: float = Field(ge=0, le=24)


@ml_app.get("/")
def root():
    return {
        "status": "ok",
        "app": "NTARINDWA Colab ML backend",
        "mode": MODE,
        "device": str(DEVICE),
        "docs": "/docs",
        "endpoints": {
            "health": "GET /health",
            "status": "GET /status",
            "score": "POST /predict/score",
            "leaf": "POST /predict/leaf",
        },
        "hint": "Set ML_BACKEND_URL to this origin with no path. Do not use the browser home page as the API path.",
    }


@ml_app.get("/favicon.ico")
def favicon():
    return Response(status_code=204)


@ml_app.get("/health")
@ml_app.get("/api/health")
def health():
    return {"status": "ok", "app": "NTARINDWA Colab ML", "mode": MODE, "device": str(DEVICE)}


@ml_app.get("/status")
@ml_app.get("/api/ml/status")
def status():
    return {
        "score_model": "ordinary-least-squares",
        "leaf_backend": "colab",
        "colab_connected": True,
        "classes": LEAF_CLASSES,
        "device": str(DEVICE),
        "demo_weights": bool(DEMO_DATA),
        "intercept": SCORE_INTERCEPT,
        "slope": SCORE_SLOPE,
        "notebook": "notebooks/NTARINDWA_ML_Colab_Backend.ipynb",
    }


@ml_app.post("/predict/score")
@ml_app.post("/api/ml/predict/score")
def score_endpoint(payload: ScoreIn):
    predicted = predict_score_value(payload.hours)
    return {
        "hours": payload.hours,
        "predicted_score": predicted,
        "model": "ordinary least squares linear regression",
        "backend": "colab",
        "note": "Examination score from weekly study hours. Fitted in this notebook.",
    }


@ml_app.post("/predict/leaf")
@ml_app.post("/api/ml/predict/leaf")
async def leaf_endpoint(file: UploadFile = File(...)):
    contents = await file.read()
    if not contents:
        raise HTTPException(400, "Empty file")
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(400, "Please upload an image smaller than 5 MB.")
    try:
        return predict_leaf_image(contents)
    except Exception as exc:
        raise HTTPException(400, f"Could not read that image ({exc.__class__.__name__}).") from exc

print("ML app routes ready")""",
    ),
    cell(
        "markdown",
        """## 6. Optional: full portfolio API on Colab

Only if `MODE = "full"`. Upload or clone the project so `/content/Profile/backend` exists, then this cell serves `app.main:app` against Neon. Leave `MODE = "ml"` if FastAPI is already hosted elsewhere.""",
    ),
    cell(
        "code",
        r"""serve_app = ml_app
full_note = "serving ML microservice only"

if MODE == "full":
    repo = Path("/content/Profile/backend")
    if not repo.exists():
        raise FileNotFoundError(
            "MODE=full requires the project at /content/Profile/backend. "
            "Upload the repo, or git clone it into /content/Profile."
        )
    os.environ["DATABASE_URL"] = DATABASE_URL
    os.environ["SECRET_KEY"] = SECRET_KEY
    os.environ["CORS_ORIGINS"] = CORS_ORIGINS
    os.environ["ML_BACKEND_URL"] = ""  # in-process models; no self-proxy
    os.environ["PUBLIC_API_URL"] = f"http://127.0.0.1:{PORT}"
    sys.path.insert(0, str(repo))
    os.chdir(repo)
    from app.main import app as portfolio_app  # noqa: E402
    from app.api import ml as ml_routes  # noqa: E402
    ml_routes.inprocess_leaf = predict_leaf_image
    serve_app = portfolio_app
    full_note = "serving full Portfolio FastAPI (Neon + in-process leaf model)"

print(full_note)""",
    ),
    cell(
        "markdown",
        """## 7. Public HTTPS tunnel

Starts Uvicorn, then cloudflared. **Paste the `https://….trycloudflare.com` URL** into hosted FastAPI as `ML_BACKEND_URL` (no trailing path). Colab's built-in `proxyPort` only works in your browser, not from a remote server — the tunnel is required for a hosted site.""",
    ),
    cell(
        "code",
        r"""import re
import threading
import time
import uvicorn

uvicorn_server = uvicorn.Server(uvicorn.Config(serve_app, host="0.0.0.0", port=PORT, log_level="info"))
threading.Thread(target=uvicorn_server.run, daemon=True).start()

for _ in range(40):
    time.sleep(0.25)
    try:
        import urllib.request
        with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/health", timeout=1) as resp:
            if resp.status == 200:
                break
    except Exception:
        pass
else:
    print("Uvicorn did not become ready on /health — check the previous cells.")

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
    raise RuntimeError("cloudflared did not print a public URL. Re-run this cell.")

print("\n========== HOSTED PROJECT ==========")
print("Public ML URL:", PUBLIC_URL)
print("Open in the browser:", PUBLIC_URL + "/")
print("Health check:      ", PUBLIC_URL + "/health")
print("API docs:          ", PUBLIC_URL + "/docs")
print()
print("On the hosted FastAPI server set:")
print(f"  ML_BACKEND_URL={PUBLIC_URL}")
print()
print("If this Colab session IS the whole API (MODE=full), build the frontend with:")
print(f"  VITE_API_BASE={PUBLIC_URL}")
print("====================================\n")"""
    ),
    cell(
        "markdown",
        """## 8. Keep the runtime awake

Colab stops idle sessions. Leave this cell running. Re-run the tunnel cell if the URL changes, then update `ML_BACKEND_URL`.""",
    ),
    cell(
        "code",
        r"""from datetime import datetime, timezone

print("Serving until you stop the cell. Started", datetime.now(timezone.utc).isoformat())
print("Public URL:", PUBLIC_URL)
print("Browser check:", PUBLIC_URL + "/health")
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
        "colab": {"provenance": [], "gpuType": "T4"},
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "accelerator": "GPU",
        "language_info": {"name": "python"},
    },
    "cells": cells,
}

out = Path(__file__).resolve().parent / "NTARINDWA_ML_Colab_Backend.ipynb"
out.write_text(json.dumps(nb, indent=1), encoding="utf-8")
print("wrote", out)