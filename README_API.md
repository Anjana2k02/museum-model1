# HAR FastAPI Server

Low-latency API for posture/activity inference using `har_position_model.joblib`.

## Install

```bash
pip install -r requirements.txt
```

## Run

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

Optional environment variables:

- `HAR_MODEL_PATH` (default: `./har_position_model.joblib`)
- `HAR_WINDOW_SIZE` (default: `128`)
- `HAR_STEP_SIZE` (default: `10`)

## Endpoints

- `GET /health`
- `POST /predict-window`
- `WS /stream`

### `POST /predict-window`

Sends a full 128-point window and gets one prediction.

Request body:

```json
{
  "points": [
    {
      "timestamp": 1710000000.001,
      "ax": 0.12,
      "ay": -0.03,
      "az": 9.81,
      "gx": 0.01,
      "gy": -0.02,
      "gz": 0.00
    }
  ]
}
```

`points` length must be exactly 128.

Response fields:

- `label`
- `confidence`
- `probabilities`
- `processing_ms`
- `server_timestamp`
- `window_start_timestamp`
- `window_end_timestamp`
- `window_size`

### `WS /stream`

Send one sensor point JSON per message. Server returns:

- `{"type":"buffering", ...}` while collecting the initial window
- `{"type":"prediction", ...}` every `step_size` samples

Example sensor point message:

```json
{
  "timestamp": 1710000000.001,
  "ax": 0.12,
  "ay": -0.03,
  "az": 9.81,
  "gx": 0.01,
  "gy": -0.02,
  "gz": 0.00
}
```

## Notes on latency

- First prediction requires collecting `window_size` samples.
- After warm-up, predictions are emitted every `step_size` samples.
- For faster end-to-end latency, keep sensor payload small and stream over WebSocket.

## Accuracy note

This server accepts raw IMU stream and generates a compact feature vector expanded to model input size. It is optimized for speed and online operation. For maximum offline-equivalent accuracy, use the exact UCI HAR feature engineering pipeline at inference time.
