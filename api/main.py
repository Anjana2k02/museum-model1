from __future__ import annotations

import os
import time
from pathlib import Path

import numpy as np
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from api.schemas import PredictionResponse, SensorPoint, WindowPredictRequest
from inference.predictor import HarPredictor
from inference.stream_buffer import SensorSample, SlidingWindowBuffer


WINDOW_SIZE = int(os.getenv("HAR_WINDOW_SIZE", "128"))
STEP_SIZE = int(os.getenv("HAR_STEP_SIZE", "10"))
MODEL_PATH = os.getenv("HAR_MODEL_PATH", str(Path(__file__).resolve().parents[1] / "har_position_model.joblib"))

_HOST = os.getenv("HOST", "0.0.0.0")
_PORT = os.getenv("PORT", "8888")
_PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "").strip()
_BASE_URL = _PUBLIC_BASE_URL or f"http://{_HOST}:{_PORT}"

_tags_metadata = [
    {
        "name": "Info",
        "description": "Health check and server information.",
    },
    {
        "name": "Inference",
        "description": (
            "Activity prediction endpoints. "
            "Submit a **128-sample sensor window** via REST (`POST /predict-window`), "
            "or stream samples continuously over **WebSocket** (`/stream`)."
        ),
    },
]

app = FastAPI(
    title="HAR Realtime API",
    version="1.0.0",
    description=(
        "## Human Activity Recognition — Real-time Inference API\n\n"
        "Predicts physical activity (**WALKING**, **SITTING**, **STANDING**) "
        "from raw IMU sensor data (accelerometer + gyroscope).\n\n"
        "### Two prediction modes\n"
        "| Mode | Endpoint | When to use |\n"
        "|------|----------|-------------|\n"
        "| Batch | `POST /predict-window` | You already have a 128-sample buffer |\n"
        "| Stream | `WS /stream` | Continuous real-time sensor stream |\n\n"
        "### Sensor input format\n"
        "Each sample provides **6 axes** at one point in time:\n"
        "- `ax, ay, az` — accelerometer (m/s²)\n"
        "- `gx, gy, gz` — gyroscope (deg/s)\n"
        "- `timestamp` — Unix time (seconds)\n\n"
        "### Quick test via Swagger\n"
        "1. **`GET /health`** → Try it out → Execute — confirms the model is loaded.\n"
        "2. **`POST /predict-window`** → Try it out → Execute — "
        "128 sitting-posture samples are pre-filled in the example body."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=_tags_metadata,
)
predictor: HarPredictor | None = None


@app.on_event("startup")
def startup_event() -> None:
    global predictor
    predictor = HarPredictor(MODEL_PATH)


@app.get("/", tags=["Info"])
def root() -> dict[str, str]:
    return {
        "message": "HAR Realtime API",
        "docs": f"{_BASE_URL}/docs",
        "redoc": f"{_BASE_URL}/redoc",
    }


@app.get("/health", tags=["Info"])
def health() -> dict[str, object]:
    model_loaded = predictor is not None
    classes = predictor.classes if predictor else []
    return {
        "ok": model_loaded,
        "model_path": MODEL_PATH,
        "window_size": WINDOW_SIZE,
        "step_size": STEP_SIZE,
        "classes": classes,
    }


@app.post(
    "/predict-window",
    response_model=PredictionResponse,
    tags=["Inference"],
    summary="Predict from a single 128-sample window",
    description="Submit a complete 128-point sensor window and receive an activity prediction with confidence scores.",
)
def predict_window(payload: WindowPredictRequest) -> PredictionResponse:
    if predictor is None:
        raise HTTPException(status_code=503, detail="Model is not loaded")

    points = payload.points
    if len(points) != WINDOW_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"Expected exactly {WINDOW_SIZE} points, got {len(points)}",
        )

    matrix = np.array([
        [point.ax, point.ay, point.az, point.gx, point.gy, point.gz]
        for point in points
    ], dtype=np.float32)

    prediction = predictor.predict_from_window(matrix)

    return PredictionResponse(
        label=prediction["label"],
        confidence=prediction["confidence"],
        probabilities=prediction["probabilities"],
        processing_ms=prediction["processing_ms"],
        server_timestamp=time.time(),
        window_start_timestamp=points[0].timestamp,
        window_end_timestamp=points[-1].timestamp,
        window_size=WINDOW_SIZE,
    )


@app.websocket("/stream")
async def stream_predictions(websocket: WebSocket) -> None:
    """
    WebSocket endpoint for streaming activity predictions.
    
    - Continuously receives sensor points (ax, ay, az, gx, gy, gz, timestamp).
    - Buffers first 128 samples internally.
    - Emits predictions every `step_size` samples after warm-up.
    - Sends `{"type":"buffering", ...}` during initial window collection.
    - Sends `{"type":"prediction", ...}` with full prediction details after warm-up.
    """
    await websocket.accept()

    if predictor is None:
        await websocket.send_json({"error": "Model is not loaded"})
        await websocket.close(code=1011)
        return

    buffer = SlidingWindowBuffer(window_size=WINDOW_SIZE, step_size=STEP_SIZE)

    try:
        while True:
            payload = await websocket.receive_json()
            point = SensorPoint(**payload)

            sample = SensorSample(
                timestamp=point.timestamp,
                ax=point.ax,
                ay=point.ay,
                az=point.az,
                gx=point.gx,
                gy=point.gy,
                gz=point.gz,
            )

            ready = buffer.add_sample(sample)
            if not ready:
                await websocket.send_json({
                    "type": "buffering",
                    "received": len(buffer),
                    "required": WINDOW_SIZE,
                })
                continue

            matrix = np.array(buffer.to_matrix(), dtype=np.float32)
            prediction = predictor.predict_from_window(matrix)
            window_start, window_end = buffer.time_bounds()

            await websocket.send_json({
                "type": "prediction",
                "label": prediction["label"],
                "confidence": prediction["confidence"],
                "probabilities": prediction["probabilities"],
                "processing_ms": prediction["processing_ms"],
                "server_timestamp": time.time(),
                "window_start_timestamp": window_start,
                "window_end_timestamp": window_end,
                "window_size": WINDOW_SIZE,
                "step_size": STEP_SIZE,
            })

    except WebSocketDisconnect:
        return
    except Exception as exc:  # noqa: BLE001
        await websocket.send_json({"error": str(exc)})
        await websocket.close(code=1011)


@app.exception_handler(Exception)
async def global_error_handler(_, exc: Exception):
    return JSONResponse(status_code=500, content={"error": str(exc)})
