# Render Deployment Setup

## Important: Configure Start Command in Render Dashboard

If Render is running `python run.py` instead of using gunicorn, you need to configure the start command in the Render dashboard:

1. Go to your service in Render dashboard
2. Navigate to **Settings** → **Build & Deploy**
3. Set the **Start Command** to:
   ```
   gunicorn run:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
   ```

Alternatively, Render should automatically detect and use the `Procfile` if it's in the root of your repository.

## Current Configuration

- **Procfile**: Uses gunicorn with production settings
- **render.yaml**: Contains deployment configuration (if using Blueprint)
- **run.py**: Updated to work with both gunicorn (production) and direct execution (fallback)

## Environment Variables

Make sure these are set in Render dashboard:
- `FLASK_ENV=production`
- `SECRET_KEY` (auto-generated or set manually)
- `TRUSTMEBRO_ADMIN_TOKEN` (optional, for admin setup)

## Verification

After deployment, check:
1. App should bind to `0.0.0.0` (not `127.0.0.1`)
2. Debug mode should be OFF
3. Should use gunicorn (not Flask dev server)
4. Port should match Render's `$PORT` environment variable

