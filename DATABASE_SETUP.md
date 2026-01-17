# Database Setup for Render

## Overview

The application supports both **SQLite** (for local development) and **PostgreSQL** (for production on Render).

## Automatic Detection

The app automatically detects which database to use:
- If `DATABASE_URL` environment variable is set → Uses PostgreSQL
- Otherwise → Uses SQLite (local development)

## Setting Up PostgreSQL on Render

1. **Create a PostgreSQL Database**:
   - Go to Render Dashboard
   - Click "New +" → "PostgreSQL"
   - Choose a name (e.g., `trustmebro-db`)
   - Select a plan (Free tier available)
   - Click "Create Database"

2. **Link Database to Your Web Service**:
   - Go to your web service settings
   - Navigate to "Environment" tab
   - Under "Environment Variables", you'll see `DATABASE_URL` automatically added
   - Or manually link it in the "Connections" section

3. **Deploy**:
   - The app will automatically detect `DATABASE_URL` and use PostgreSQL
   - Tables will be created automatically on first run

## Local Development (SQLite)

For local development, no setup is needed:
- Just run `python run.py`
- SQLite database will be created at `instance/trustmebro.db`
- No `DATABASE_URL` needed

## Environment Variables

- `DATABASE_URL` (optional): PostgreSQL connection string
  - Format: `postgresql://user:password@host:port/database`
  - Automatically set by Render when database is linked

## Migration Notes

- The app automatically creates all tables on first run
- Data structure is identical between SQLite and PostgreSQL
- No manual migration needed - just set `DATABASE_URL` and redeploy

