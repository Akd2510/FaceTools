import os
import traceback
from contextlib import asynccontextmanager

import requests
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pipeline import SwapPipeline
from utils import numpy_to_base64_png, read_image_from_upload, verify_model_file

MODELS_DIR = os.getenv("MODELS_DIR", "./models")
TEMPLATES_DIR = os.getenv("TEMPLATES_DIR", "./templates")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Preload models
    print("[main] Preloading models...")
    inswapper_path = os.path.join(MODELS_DIR, "inswapper_128.onnx")
    gfpgan_path = os.path.join(MODELS_DIR, "gfpgan_1.4.onnx")

    verify_model_file(inswapper_path, "Inswapper")
    verify_model_file(gfpgan_path, "GFPGAN")

    try:
        app.state.pipeline = SwapPipeline(MODELS_DIR)
        app.state.models_loaded = True
    except Exception as e:
        print(f"[ERROR] Failed to load models: {e}")
        traceback.print_exc()
        app.state.models_loaded = False

    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/swap")
async def swap(
    source_image: UploadFile = File(...),
    target_image: UploadFile = File(...),
    enhance: bool = Form(True),
):
    if not app.state.models_loaded:
        raise HTTPException(status_code=500, detail="Models not loaded on server.")

    try:
        source_bytes = await source_image.read()
        target_bytes = await target_image.read()

        source_img = read_image_from_upload(source_bytes)
        target_img = read_image_from_upload(target_bytes)

        result_img, warnings = app.state.pipeline.run(
            source_img, target_img, enhance=enhance
        )
        print(f"[main] Swap completed. Warnings: {warnings}")

        base64_res = numpy_to_base64_png(result_img)

        return {"result": base64_res, "warnings": warnings}

    except ValueError as ve:
        return JSONResponse(status_code=400, content={"error": str(ve)})
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(
            status_code=500, content={"error": "Internal server error."}
        )


@app.post("/swap/url")
async def swap_url(source_url: str, target_url: str, enhance: bool = True):
    if not app.state.models_loaded:
        raise HTTPException(status_code=500, detail="Models not loaded on server.")

    try:

        def download_img(url):
            if not url.startswith(("http://", "https://")):
                raise ValueError("Only http/https URLs allowed.")
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            return read_image_from_upload(resp.content)

        source_img = download_img(source_url)
        target_img = download_img(target_url)

        result_img, warnings = app.state.pipeline.run(
            source_img, target_img, enhance=enhance
        )
        print(f"[main] Swap completed. Warnings: {warnings}")
        base64_res = numpy_to_base64_png(result_img)

        return {"result": base64_res, "warnings": warnings}
    except ValueError as ve:
        return JSONResponse(status_code=400, content={"error": str(ve)})
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/templates")
async def list_templates():
    if not os.path.exists(TEMPLATES_DIR):
        return {"templates": []}
    files = [
        f
        for f in os.listdir(TEMPLATES_DIR)
        if f.lower().endswith((".jpg", ".jpeg", ".png"))
    ]
    return {"templates": sorted(files)}


@app.get("/templates/{filename}")
async def get_template(filename: str):
    if "/" in filename or ".." in filename:
        raise HTTPException(status_code=400, detail="Invalid filename.")
    path = os.path.join(TEMPLATES_DIR, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Template not found.")
    return FileResponse(path)


@app.get("/swap/health")
async def health():
    import uniface

    inswapper_path = os.path.join(MODELS_DIR, "inswapper_128.onnx")
    gfpgan_path = os.path.join(MODELS_DIR, "gfpgan_1.4.onnx")

    return {
        "status": "ok" if app.state.models_loaded else "degraded",
        "models_loaded": app.state.models_loaded,
        "gfpgan_available": app.state.pipeline.restorer.is_available()
        if app.state.models_loaded
        else False,
        "uniface_version": getattr(uniface, "__version__", "unknown"),
        "model_sizes_mb": {
            "inswapper": os.path.getsize(inswapper_path) / 1e6
            if os.path.exists(inswapper_path)
            else None,
            "gfpgan": os.path.getsize(gfpgan_path) / 1e6
            if os.path.exists(gfpgan_path)
            else None,
        },
    }


# Mount frontend if it exists locally for dev
if os.path.exists("frontend"):
    app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
