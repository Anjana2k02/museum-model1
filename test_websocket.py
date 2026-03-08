"""
WebSocket streaming test client.
Run the API first:  python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
Then run this:      python test_websocket.py
"""

import asyncio
import json
import time
import websockets


async def stream_walking_motion():
    """Stream walking motion samples via WebSocket."""
    uri = "ws://127.0.0.1:8000/stream"
    
    print("\n" + "=" * 70)
    print("🚶 WEBSOCKET STREAMING TEST - WALKING MOTION")
    print("=" * 70)
    print(f"\nConnecting to {uri}...")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to WebSocket\n")
            
            base_time = time.time()
            samples_sent = 0
            
            # Stream 150 samples (first 128 will trigger initial warm-up)
            # After 128, predictions will emit every 10 samples
            for i in range(150):
                # Simulate walking motion
                phase = (i / 128.0) * 4 * 3.14159
                
                sample = {
                    "timestamp": base_time + i * 0.02,
                    "ax": 0.5 * (i % 64 - 32) / 32,
                    "ay": 0.3 + 0.4 * (i % 16 / 16),
                    "az": 9.8 + 0.5 * ((i % 32 - 16) / 16),
                    "gx": 0.02 + 0.05 * ((i % 20) / 20),
                    "gy": 0.01 + 0.03 * ((i % 25) / 25),
                    "gz": 0.01 + 0.02 * ((i % 32) / 32),
                }
                
                # Send sample
                await websocket.send(json.dumps(sample))
                samples_sent += 1
                
                # Receive response
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                    data = json.loads(response)
                    
                    if data.get("type") == "buffering":
                        print(f"Sample {samples_sent}: 📊 BUFFERING - "
                              f"Received {data['received']}/{data['required']} samples")
                    
                    elif data.get("type") == "prediction":
                        print(f"Sample {samples_sent}: ✅ PREDICTION EMITTED")
                        print(f"   Label: {data['label']}")
                        print(f"   Confidence: {data['confidence']:.2%}")
                        print(f"   Processing: {data['processing_ms']:.2f}ms")
                        print(f"   Probabilities: {data['probabilities']}")
                        print()
                
                except asyncio.TimeoutError:
                    print(f"Sample {samples_sent}: ⏱️  No response (buffering...)")
                
                # Small delay between sends
                await asyncio.sleep(0.01)
            
            print("✅ Stream test complete!")
    
    except Exception as e:
        print(f"❌ Error: {e}")


async def main():
    await stream_walking_motion()


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("HAR WEBSOCKET TEST CLIENT")
    print("=" * 70)
    print("\nMake sure API is running:")
    print("  python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload")
    
    asyncio.run(main())
