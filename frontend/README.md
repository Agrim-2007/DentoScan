# DentoScan Frontend

## Local Development

1. Install dependencies:
   ```bash
   npm install
   ```
2. Start the frontend:
   ```bash
   npm run dev
   ```

The Vite dev server proxies `/api`, `/static`, and `/health` to the FastAPI backend running at `http://127.0.0.1:8000`.

## Optional Backend Override

If you want the frontend to talk to a deployed backend directly, create `frontend/.env` and set:

```bash
VITE_API_BASE_URL=https://your-backend-url
```

## Checks

- Build:
  ```bash
  npm run build
  ```
- Lint:
  ```bash
  npm run lint
  ```
