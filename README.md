# 🎭 FaceTools Suite

A professional, high-performance AI suite for face manipulation, identity management, and forensic-grade clustering. **FaceTools** integrates two powerful engines—**FaceSwap** and **FaceVision**—into a unified microservices architecture with a premium React frontend.

---

## 🚀 Key Features

### 🔄 FaceSwap Engine (FastAPI)
*   **Identity Transfer:** Seamlessly swap faces using `inswapper_128.onnx`.
*   **Face Restoration:** Integrated **GFPGAN v1.4** for ultra-crisp results.
*   **Advanced Blending:** Multi-tier fallback masking (XSeg/BiSeNet) with Poisson seamless cloning for natural skin-tone matching.
*   **Real-time Processing:** Optimized for high-throughput AI inference.

### 🔍 FaceVision Engine (Django)
*   **Identity Clustering:** Automatic person grouping using **DBSCAN** on 512-dim ArcFace embeddings.
*   **Search & Retrieval:** Find similar faces across thousands of images using cosine similarity.
*   **Database Management:** Robust PostgreSQL-backed metadata storage for forensic analysis.
*   **Async Pipeline:** Background processing of large image batches via integrated worker tasks.

### 💻 Unified Interface (React)
*   **Premium Tech Aesthetic:** Glassmorphism UI with professional typography (**Plus Jakarta Sans**).
*   **Live Analytics:** Real-time metrics dashboard for processing status and system health.
*   **Integrated Gateway:** All features accessible via a single Nginx entry point on port 80.

---

## 🏗️ Architecture

```text
/faceswap-backend/   -> FastAPI (AI Processing)
/facevision-backend/ -> Django (Data & Clustering)
/frontend/           -> React (Unified UI)
/nginx/              -> Gateway / Reverse Proxy
/models/             -> Shared AI Model Weights
/templates/          -> FaceSwap Templates
```

---

## 🛠️ Quick Start

### 1. Prerequisites
*   Docker & Docker Compose
*   AI Models (place in `/models`):
    *   `inswapper_128.onnx`
    *   `gfpgan_1.4.onnx`

### 2. Launch Suite
Run the orchestrator from the project root:
```powershell
docker-compose up --build -d
```

### 3. Access
Open your browser and navigate to:
👉 **[http://localhost/](http://localhost/)**

---

## ⚙️ Development & Maintenance

*   **Logs:** `docker-compose logs -f [service_name]`
*   **Restarting:** `docker-compose restart nginx` (to apply routing changes)
*   **Cleanup:** `docker-compose down -v` (removes volumes and database)

---

## 🛡️ Engineering Standards
*   **Microservices:** Services are isolated with specific dependencies (`bookworm` for AI, `alpine` for Gateway).
*   **Routing:** Nginx handles `/api/` (Django) and `/swap/` (FastAPI) transparently.
*   **Performance:** Preloaded AI models on startup to ensure minimal latency during user interaction.

---

## 📜 Credits & Acknowledgments

The **FaceVision** engine and initial architectural foundations were inspired by and adapted from the [facevision](https://github.com/Prateekshenoy/facevision) repository by **Prateekshenoy**. Special thanks for the high-quality forensic face analysis pipeline and clustering logic.
