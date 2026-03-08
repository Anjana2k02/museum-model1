"""
Test client to demonstrate API input/output with sample motion data.
Run the API first:  python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
Then run this:      python test_client.py
"""

import requests
import json
import time
from typing import List, Dict, Any


BASE_URL = "http://127.0.0.1:8000"


def generate_sitting_window() -> List[Dict[str, float]]:
    """Generate synthetic 128-sample window for SITTING position.
    
    Characteristics:
    - Low accelerometer variance (stable position)
    - Z-axis ~9.8 (gravity effects)
    - Very low gyroscope values (minimal rotation)
    """
    points = []
    base_time = time.time()
    
    for i in range(128):
        points.append({
            "timestamp": base_time + i * 0.02,  # 50 Hz sampling (0.02s intervals)
            "ax": 0.05 + (i % 10) * 0.001,
            "ay": -0.02 + (i % 7) * 0.001,
            "az": 9.81 + (i % 5) * 0.01,
            "gx": 0.001 + (i % 3) * 0.0001,
            "gy": 0.002 + (i % 4) * 0.0001,
            "gz": -0.001 + (i % 2) * 0.0001,
        })
    return points


def generate_standing_window() -> List[Dict[str, float]]:
    """Generate synthetic 128-sample window for STANDING position.
    
    Characteristics:
    - Moderate accelerometer variance (slight body sway)
    - Z-axis ~10 (upright posture)
    - Low gyroscope values
    """
    points = []
    base_time = time.time()
    
    for i in range(128):
        points.append({
            "timestamp": base_time + i * 0.02,
            "ax": 0.1 + (i % 10) * 0.015,
            "ay": 0.05 + (i % 8) * 0.012,
            "az": 9.85 + (i % 6) * 0.02,
            "gx": 0.005 + (i % 5) * 0.001,
            "gy": 0.003 + (i % 4) * 0.001,
            "gz": 0.002 + (i % 3) * 0.0005,
        })
    return points


def generate_walking_window() -> List[Dict[str, float]]:
    """Generate synthetic 128-sample window for WALKING motion.
    
    Characteristics:
    - High accelerometer variance (periodic body motion)
    - Z-axis oscillates around 9.8 (up/down stepping)
    - Higher gyroscope values (body rotation with steps)
    """
    points = []
    base_time = time.time()
    
    for i in range(128):
        # Simulate walking periodicity ~2 Hz (step cycle)
        phase = (i / 128.0) * 4 * 3.14159  # 2 full cycles in 128 samples
        
        points.append({
            "timestamp": base_time + i * 0.02,
            "ax": 0.5 * (i % 64 - 32) / 32,  # Larger acceleration swings
            "ay": 0.3 + 0.4 * (i % 16 / 16),
            "az": 9.8 + 0.5 * ((i % 32 - 16) / 16),  # Vertical bouncing
            "gx": 0.02 + 0.05 * ((i % 20) / 20),  # Torso rotation
            "gy": 0.01 + 0.03 * ((i % 25) / 25),  # Hip sway
            "gz": 0.01 + 0.02 * ((i % 32) / 32),  # Vertical axis rotation
        })
    return points


def test_predict_window(motion_type: str) -> None:
    """Test POST /predict-window endpoint."""
    
    if motion_type.lower() == "sitting":
        points = generate_sitting_window()
        print("\n" + "=" * 70)
        print("🪑 TESTING SITTING POSITION")
        print("=" * 70)
    elif motion_type.lower() == "standing":
        points = generate_standing_window()
        print("\n" + "=" * 70)
        print("🧍 TESTING STANDING POSITION")
        print("=" * 70)
    elif motion_type.lower() == "walking":
        points = generate_walking_window()
        print("\n" + "=" * 70)
        print("🚶 TESTING WALKING MOTION")
        print("=" * 70)
    else:
        print(f"Unknown motion type: {motion_type}")
        return
    
    payload = {"points": points}
    
    print("\n📤 INPUT FORMAT (sending 128-point window):")
    print(f"   First 3 samples:")
    for i, p in enumerate(points[:3]):
        print(f"   Sample {i+1}: {json.dumps(p, indent=6)}")
    print(f"   ... ({len(points)} total samples)")
    
    try:
        response = requests.post(f"{BASE_URL}/predict-window", json=payload, timeout=10)
        response.raise_for_status()
        
        result = response.json()
        print("\n📥 OUTPUT (Server Response):")
        print(json.dumps(result, indent=2))
        
        print(f"\n✅ Prediction: {result['label']}")
        print(f"   Confidence: {result['confidence']:.2%}")
        print(f"   Processing time: {result['processing_ms']:.2f}ms")
        print(f"   Probabilities:")
        for cls, prob in result['probabilities'].items():
            print(f"     - {cls}: {prob:.2%}")
        
    except Exception as e:
        print(f"❌ Error: {e}")


def test_health() -> None:
    """Test GET /health endpoint."""
    print("\n" + "=" * 70)
    print("🏥 TESTING HEALTH ENDPOINT")
    print("=" * 70)
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        response.raise_for_status()
        
        result = response.json()
        print("\n📥 Health Check Response:")
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        print(f"❌ Error: {e}")


def show_input_schema() -> None:
    """Show expected input/output schema."""
    print("\n" + "=" * 70)
    print("📋 API INPUT/OUTPUT SCHEMA")
    print("=" * 70)
    
    print("\n🔵 INPUT: POST /predict-window")
    print("""
Request Body (JSON):
{
  "points": [
    {
      "timestamp": 1710000000.001,    // Unix timestamp (seconds or milliseconds)
      "ax": 0.12,                      // Accelerometer X-axis (m/s²)
      "ay": -0.03,                     // Accelerometer Y-axis (m/s²)
      "az": 9.81,                      // Accelerometer Z-axis (m/s²)
      "gx": 0.01,                      // Gyroscope X-axis (deg/s or rad/s)
      "gy": -0.02,                     // Gyroscope Y-axis
      "gz": 0.00                       // Gyroscope Z-axis
    },
    ... (128 total points required)
  ]
}
""")
    
    print("\n🟢 OUTPUT: Response (JSON)")
    print("""
{
  "label": "SITTING",                           // Activity class
  "confidence": 0.92,                           // Model confidence (0.0-1.0)
  "probabilities": {
    "SITTING": 0.92,
    "STANDING": 0.07,
    "WALKING": 0.01
  },
  "processing_ms": 12.5,                        // Server inference time (ms)
  "server_timestamp": 1710000000.001,           // Prediction timestamp
  "window_start_timestamp": 1710000000.001,     // First sample time
  "window_end_timestamp": 1710000002.561,       // Last sample time (128 * 0.02s)
  "window_size": 128
}
""")
    
    print("\n📡 WebSocket /stream (Continuous Streaming)")
    print("""
Send one sensor point per message:
{
  "timestamp": 1710000000.001,
  "ax": 0.12, "ay": -0.03, "az": 9.81,
  "gx": 0.01, "gy": -0.02, "gz": 0.00
}

Server responds with:
- {"type": "buffering", "received": 50, "required": 128}  (during warm-up)
- {"type": "prediction", ...}                             (every 10 samples after 128)
""")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("HAR API TEST CLIENT")
    print("=" * 70)
    print("\nMake sure API is running:")
    print("  python -m uvicorn api.main:app --host 0.0.0.0 --port 8000")
    
    # Show schema first
    show_input_schema()
    
    # Test health
    test_health()
    
    # Test different motions
    test_predict_window("sitting")
    test_predict_window("standing")
    test_predict_window("walking")
    
    print("\n" + "=" * 70)
    print("✅ Tests complete!")
    print("=" * 70)
