FROM python:3.10-slim-bullseye

ENV DEBIAN_FRONTEND=noninteractive
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# ── apt config ─────────────────────────────────────────────
RUN echo 'Acquire::Retries "5";' > /etc/apt/apt.conf.d/80-retries \
 && echo 'Acquire::http::Timeout "30";' >> /etc/apt/apt.conf.d/80-retries \
 && echo 'Acquire::https::Timeout "30";' >> /etc/apt/apt.conf.d/80-retries

# ── system deps ────────────────────────────────────────────
RUN apt-get update --fix-missing && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    libglib2.0-0 \
    libglib2.0-dev \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    libgl1-mesa-glx \
    libgl1 \
    pkg-config \
    wget \
    curl \
    ca-certificates \
    ffmpeg \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ── Python base ────────────────────────────────────────────
RUN pip install --upgrade pip setuptools wheel

# 🔥 CRITICAL FIX: Install correct protobuf FIRST
RUN pip install protobuf==3.20.3

# ── Django stack ───────────────────────────────────────────
RUN pip install \
    Django==4.2.7 \
    djangorestframework==3.14.0 \
    django-cors-headers==4.3.1 \
    psycopg2-binary==2.9.9 \
    gunicorn==21.2.0 \
    dj-database-url==2.1.0 \
    python-decouple==3.8

# ── ML stack ───────────────────────────────────────────────
RUN pip install \
    numpy==1.24.4 \
    scipy==1.11.4 \
    scikit-learn==1.3.2

# ── CV stack ───────────────────────────────────────────────
RUN pip install \
    Pillow==10.1.0 \
    opencv-python-headless==4.8.1.78

# ── MediaPipe (needs protobuf 3.x) ─────────────────────────
RUN pip install mediapipe==0.10.7

# ── ONNX + InsightFace ─────────────────────────────────────
RUN pip install onnxruntime==1.16.3
RUN pip install insightface==0.7.3

# 🔥 CRITICAL FIX AGAIN: force protobuf back (prevents override)
RUN pip install protobuf==3.20.3 --force-reinstall

# ── Preload InsightFace model ──────────────────────────────
RUN python - <<'EOF' || true
from insightface.app import FaceAnalysis
app = FaceAnalysis(name='buffalo_sc', providers=['CPUExecutionProvider'])
app.prepare(ctx_id=0, det_size=(640, 640))
print("InsightFace model pre-loaded successfully.")
EOF

# ── App code ───────────────────────────────────────────────
COPY . .

RUN mkdir -p media/uploads media/processed media/faces

EXPOSE 8000