# Backend - Agentic AI Travel Intelligence Platform (FastAPI)

FastAPI-powered backend implementing clean modular architecture, Pydantic validation, Supabase JWT authentication, and Supabase PostgreSQL database integration.

---

## Setup Instructions

### 1. Create and Activate Virtual Environment
```bash
# Navigate to the backend directory
cd backend

# Create Python virtual environment
python -m venv venv

# Activate virtual environment
# On Windows (PowerShell):
.\venv\Scripts\activate
# On macOS / Linux:
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables
```bash
cp .env.example .env
```
Fill in your Supabase project credentials in `.env`:
* `SUPABASE_URL`: Your Supabase project URL (e.g. `https://xyz.supabase.co`)
* `SUPABASE_ANON_KEY`: Your Supabase public anonymous API key
* `SUPABASE_SERVICE_ROLE_KEY`: Your Supabase service role key (keep secret, server-side only)
* `SUPABASE_JWT_SECRET`: Optional secret for fast local JWT verification

### 4. Execute Supabase Database Migration
1. Go to your [Supabase Dashboard](https://supabase.com/dashboard).
2. Select your project and navigate to the **SQL Editor** from the left navigation bar.
3. Open [`backend/supabase/schema.sql`](file:///c:/Users/sumit/OneDrive/Desktop/SIH%20-%20AGENT/backend/supabase/schema.sql) and paste its contents into the SQL Editor.
4. Click **Run** to execute the migration. This creates the `profiles`, `trips`, and `itineraries` tables along with Row Level Security (RLS) policies and automatic triggers.

### 5. Start the FastAPI Development Server
```bash
uvicorn app.main:app --reload --port 8000
```

### 6. Verify Endpoints and Documentation
* **Swagger UI / OpenAPI Documentation:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
* **Redoc:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
* **Health Check:** [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)
  ```json
  {
    "status": "ok",
    "service": "travel-intelligence-backend"
  }
  ```

---

## API Endpoints Overview

| Method | Endpoint | Description | Authentication |
|---|---|---|---|
| `GET` | `/api/health` | Service health status check | Public |
| `GET` | `/api/users/me` | Current authenticated user profile | Bearer Token |
| `GET` | `/api/auth/me` | Current authenticated session metadata | Bearer Token |
| `GET` | `/api/trips` | List all trips owned by user | Bearer Token |
| `POST` | `/api/trips` | Create new travel trip configuration | Bearer Token |
| `GET` | `/api/trips/{trip_id}` | Retrieve specific trip (enforces ownership) | Bearer Token |
| `PUT` | `/api/trips/{trip_id}` | Update trip (enforces ownership) | Bearer Token |
| `DELETE` | `/api/trips/{trip_id}` | Delete trip (enforces ownership) | Bearer Token |

---

## Running Automated Tests
```bash
# Set PYTHONPATH and execute pytest
pytest -v tests/test_api.py
```
