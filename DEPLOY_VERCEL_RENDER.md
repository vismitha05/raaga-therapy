# Deploy Raaga Therapy (Vercel + Render)

## Architecture
- `frontend` (React): deploy to Vercel
- `backend/adaptive_backend` (FastAPI + WebSocket): deploy to Render

## 1. Deploy Backend on Render
1. Push this repo to GitHub.
2. In Render, click `New` -> `Web Service`.
3. Connect your GitHub repo.
4. Configure:
   - Name: `raaga-therapy-backend`
   - Root Directory: `backend`
   - Runtime: `Python`
   - Build Command: `pip install -r requirements_adaptive.txt`
   - Start Command: `uvicorn adaptive_backend.main:app --host 0.0.0.0 --port $PORT`
5. Add environment variable:
   - `CORS_ALLOW_ORIGINS` = `https://<your-vercel-domain>`
   - Optional for multiple domains: comma-separated list
6. Click `Create Web Service`.
7. After deploy, verify:
   - `https://<render-domain>/health`
   - `wss://<render-domain>/api/v1/ws/live` (websocket path)

## 2. Deploy Frontend on Vercel
1. In Vercel, click `Add New` -> `Project`.
2. Import the same GitHub repo.
3. Set `Root Directory` to `frontend`.
4. Framework preset: `Create React App` (auto-detected).
5. Add environment variables:
   - `REACT_APP_API_URL` = `https://<render-domain>`
   - `REACT_APP_WS_URL` = `wss://<render-domain>/api/v1/ws/live`
6. Click `Deploy`.

## 3. Redeploy after env var changes
- Vercel: `Project -> Deployments -> Redeploy`.
- Render: `Manual Deploy -> Deploy latest commit`.

## 4. Post-deploy smoke test
1. Open Vercel app URL.
2. Landing screen: click `Start Analysis`, verify 10-second countdown.
3. After countdown, `Continue Therapy` enabled.
4. Start session and verify:
   - audio plays
   - websocket connected
   - no CORS errors in browser console.
