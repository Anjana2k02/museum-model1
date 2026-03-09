# Railway Deployment Guide

## Issues Fixed (March 9, 2026)

### ✅ 1. External Access (0.0.0.0 Binding)
**Problem:** Server was binding to `127.0.0.1` (localhost only), making it inaccessible from outside Railway.

**Fix:** Changed default HOST to `0.0.0.0` in:
- `main.py` line 55
- `api/main.py` line 20

**Result:** Server now accepts connections from any IP address.

---

### ✅ 2. scikit-learn Version Mismatch
**Problem:** Model trained with scikit-learn 1.6.1, but Railway installed 1.8.0 (causing 8 warnings).

**Fix:** Pinned scikit-learn version in `requirements.txt`:
```txt
scikit-learn==1.6.1
```

**Result:** Eliminates `InconsistentVersionWarning` messages and ensures model compatibility.

---

### ⚠️ 3. Port Configuration
**Current Behavior:** Railway sets `PORT=8080` via environment variable (shown in logs).

**Default Fallback:** Code defaults to port `8888` if PORT is not set.

**Options:**

**Option A: Use Railway's Port (Recommended)**
- Railway automatically assigns the port via `PORT` environment variable
- Access at: `https://museum-model1-production.up.railway.app` (Railway handles routing)
- **No code changes needed** - server already reads `PORT` from environment

**Option B: Force Port 8888**
- Set Railway environment variable: `PORT=8888`
- Go to Railway dashboard → museum-model1 → Variables → Add `PORT=8888`

**Recommended:** Use Option A (Railway's automatic port). The public URL doesn't expose the port.

---

## Railway Environment Variables

Railway should have these set (most are automatic):

| Variable | Value | Source |
|----------|-------|--------|
| `ENV` | `live` | Manual (set in Railway dashboard) |
| `HOST` | `0.0.0.0` | Code default (✅ fixed) |
| `PORT` | `8080` | Railway automatic |
| `HAR_MODEL_PATH` | `/app/har_position_model.joblib` | Dockerfile |
| `HAR_WINDOW_SIZE` | `128` | Dockerfile |
| `HAR_STEP_SIZE` | `10` | Dockerfile |

### Required Manual Configuration
Set only this variable in Railway dashboard:
```
ENV=live
```

This disables hot-reload and uses production settings.

---

## Deployment Commands

### 1. Commit & Push Changes
```bash
cd museum-model1
git add main.py api/main.py requirements.txt
git commit -m "Fix Railway deployment: bind to 0.0.0.0, pin scikit-learn 1.6.1"
git push origin main
```

### 2. Railway Auto-Deploys
Railway automatically rebuilds when you push to the connected branch.

### 3. Verify Deployment
After deployment completes:

**Check Health Endpoint:**
```bash
curl https://museum-model1-production.up.railway.app/health
```

Expected response:
```json
{
  "ok": true,
  "model_path": "/app/har_position_model.joblib",
  "window_size": 128,
  "step_size": 10,
  "classes": ["WALKING", "SITTING", "STANDING"]
}
```

**Check Logs (should see):**
```
[startup] ENV=live — using container/system environment
INFO:     Uvicorn running on http://0.0.0.0:8080
INFO:     Application startup complete.
```

✅ No more `InconsistentVersionWarning` messages!

---

## Flutter App Configuration

Your Flutter app is already configured correctly in `env_config.dart`:

```dart
// HOSTED
// static const String pythonServer1Url = 'https://museum-model1-production.up.railway.app';
```

To use the production server:
1. Uncomment line 26
2. Comment out line 23 (localhost)
3. Rebuild Flutter app

**WebSocket URL:** The `HARService` automatically converts HTTP to WebSocket:
- HTTP: `https://museum-model1-production.up.railway.app`
- WebSocket: `wss://museum-model1-production.up.railway.app/stream`

---

## Testing Production Server

### Test Health Endpoint
```bash
curl https://museum-model1-production.up.railway.app/health
```

### Test REST Prediction (from terminal)
```bash
curl -X POST https://museum-model1-production.up.railway.app/predict-window \
  -H "Content-Type: application/json" \
  -d @test_payload.json
```

### Test WebSocket (from Flutter app)
1. Update `env_config.dart` to use production URL
2. Run `flutter run`
3. Navigate to map screen
4. Observe top-right activity widget showing predictions

---

## Troubleshooting

### Issue: Still seeing 127.0.0.1 in logs
**Solution:** Changes only apply after redeployment. Push code and wait for Railway to rebuild.

### Issue: Version warnings persist
**Solution:** Railway needs to reinstall dependencies. Try:
1. Railway dashboard → Deployments → Redeploy (force rebuild)
2. Or clear build cache via Railway settings

### Issue: Cannot connect from Flutter
**Check:**
1. Railway service is running (check dashboard)
2. Health endpoint returns 200 OK
3. Flutter env_config.dart has correct HTTPS URL
4. WebSocket connection shows in Railway logs

### Issue: Port mismatch
**Remember:** 
- Internal port (8080) doesn't matter to Flutter app
- Railway exposes service via HTTPS (port 443) automatically
- Flutter app uses: `https://museum-model1-production.up.railway.app`

---

## Summary of Changes

| File | Change | Reason |
|------|--------|--------|
| `main.py:55` | `HOST="0.0.0.0"` | Allow external connections |
| `api/main.py:20` | `HOST="0.0.0.0"` | Allow external connections |
| `requirements.txt` | `scikit-learn==1.6.1` | Match model training version |

**Deploy:** `git push origin main` → Railway auto-deploys  
**Result:** Clean startup logs, no warnings, externally accessible ✅
