from __future__ import annotations

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Swagger "Try it out" helper — generates 128 synthetic sitting-posture points
# so the POST /predict-window example body is ready to execute immediately.
# ---------------------------------------------------------------------------
def _sitting_example(n: int = 128) -> list[dict]:
    """128 synthetic sensor samples simulating a stationary sitting posture.

    Values reflect a device lying flat:
    - az ≈ 9.81 m/s² (gravity on Z)
    - ax, ay ≈ 0 with tiny oscillation
    - gx, gy, gz ≈ 0 (no rotation)
    """
    base_ts = 1710000000.0
    sign = 1
    points = []
    for i in range(n):
        sign = 1 if i % 2 == 0 else -1
        points.append({
            "timestamp": round(base_ts + i * 0.02, 3),
            "ax": round(0.05 + sign * 0.01, 3),
            "ay": round(0.02 + sign * 0.01, 3),
            "az": round(9.81 + sign * 0.02, 3),
            "gx": round(0.001 * (i % 5), 4),
            "gy": round(-0.001 * (i % 3), 4),
            "gz": 0.0,
        })
    return points


class SensorPoint(BaseModel):
    timestamp: float = Field(..., description="Unix timestamp in seconds or milliseconds")
    ax: float = Field(..., description="Accelerometer X-axis (m/s²)")
    ay: float = Field(..., description="Accelerometer Y-axis (m/s²)")
    az: float = Field(..., description="Accelerometer Z-axis (m/s²)")
    gx: float = Field(..., description="Gyroscope X-axis (deg/s or rad/s)")
    gy: float = Field(..., description="Gyroscope Y-axis (deg/s or rad/s)")
    gz: float = Field(..., description="Gyroscope Z-axis (deg/s or rad/s)")

    model_config = {
        "json_schema_extra": {
            "example": {
                "timestamp": 1710000000.001,
                "ax": 0.12,
                "ay": -0.03,
                "az": 9.81,
                "gx": 0.01,
                "gy": -0.02,
                "gz": 0.00,
            }
        }
    }


class WindowPredictRequest(BaseModel):
    points: list[SensorPoint] = Field(
        ...,
        min_length=128,
        max_length=128,
        description="Exactly 128 consecutive sensor measurements (20 ms apart → 2.56 s window)",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "points": _sitting_example(128)
            }
        }
    }


class PredictionResponse(BaseModel):
    label: str = Field(..., description="Predicted activity: WALKING, SITTING, or STANDING")
    confidence: float = Field(..., description="Model confidence score (0.0 to 1.0)")
    probabilities: dict[str, float] = Field(..., description="Class probabilities for all activities")
    processing_ms: float = Field(..., description="Server-side inference latency in milliseconds")
    server_timestamp: float = Field(..., description="Server time when prediction was emitted")
    window_start_timestamp: float = Field(..., description="Timestamp of first sample in window")
    window_end_timestamp: float = Field(..., description="Timestamp of last sample in window")
    window_size: int = Field(..., description="Number of samples in prediction window")

    model_config = {
        "json_schema_extra": {
            "example": {
                "label": "SITTING",
                "confidence": 0.92,
                "probabilities": {"SITTING": 0.92, "STANDING": 0.07, "WALKING": 0.01},
                "processing_ms": 12.5,
                "server_timestamp": 1710000000.001,
                "window_start_timestamp": 1710000000.001,
                "window_end_timestamp": 1710000002.561,
                "window_size": 128,
            }
        }
    }
