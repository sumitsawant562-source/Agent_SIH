# Agentic AI Personalized Travel Intelligence Platform

> **Smart India Hackathon (SIH) Project - Stage 1: Foundation**

A web-based platform for intelligent, budget-aware, and adaptive travel planning. This repository houses the complete full-stack foundation built with **Next.js (App Router, TypeScript, Tailwind CSS)** on the frontend, **FastAPI (Python, Pydantic, Uvicorn)** on the backend, and **Supabase (PostgreSQL with Row Level Security and Supabase Auth)** as the database & identity provider.

---

## Project Structure

```
travel-intelligence-platform/
│
├── frontend/                     # Next.js 14 App Router, TypeScript, Tailwind CSS
│   ├── app/                      # Pages: Landing, Login, Signup, Dashboard, Create-Trip
│   ├── components/               # Navbar, Footer, ProtectedRoute, UI primitives
│   ├── lib/                      # Supabase client/server helpers & backend API client
│   ├── types/                    # Database and trip TypeScript definitions
│   └── package.json
│
├── backend/                      # Python FastAPI application
│   ├── app/
│   │   ├── api/                  # Endpoints: health, auth, trips CRUD
│   │   ├── core/                 # Config & Supabase JWT security dependencies
│   │   ├── db/                   # Supabase DB client helper
│   │   ├── models/               # Internal models
│   │   ├── schemas/              # Pydantic validation schemas
│   │   └── services/             # Trip business logic with user isolation
│   └── requirements.txt
│
├── docs/
│   ├── schema.sql                # Supabase PostgreSQL schema, RLS, triggers & indexes
│   └── architecture.md           # System design & Stage 2 AI Agent roadmap
│
├── .gitignore
├── .env.example
└── README.md
```

---

## Quick Start Guide

### 1. Database Setup (Supabase)
1. Create a project at [Supabase](https://supabase.com).
2. Navigate to the **SQL Editor** in your Supabase dashboard.
3. Run the SQL script found in [`docs/schema.sql`](file:///c:/Users/sumit/OneDrive/Desktop/SIH%20-%20AGENT/docs/schema.sql).
4. Copy your **Project URL**, **Anon Key**, and **Service Role Key** from *Project Settings > API*.

---

### 2. Backend Setup (FastAPI)

1. Navigate to `backend/`:
   ```bash
   cd backend
   ```
2. Create and activate a Python virtual environment:
   ```bash
   # Windows
   python -m venv venv
   .\venv\Scripts\activate

   # macOS / Linux
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure environment variables:
   ```bash
   cp .env.example .env
   ```
   Fill in `SUPABASE_URL`, `SUPABASE_ANON_KEY`, and `SUPABASE_SERVICE_ROLE_KEY`.
5. Run the FastAPI development server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
   Interactive Swagger documentation will be available at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

---

### 3. Frontend Setup (Next.js)

1. Navigate to `frontend/`:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Configure environment variables:
   ```bash
   cp .env.example .env.local
   ```
   Fill in `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`, and `NEXT_PUBLIC_API_URL=http://127.0.0.1:8000`.
4. Run the development server:
   ```bash
   npm run dev
   ```
   Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## API Endpoints (Stage 1)

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/api/health` | Health check endpoint (`{"status": "ok"}`) | No |
| `GET` | `/api/auth/me` | Returns current authenticated user profile | Yes (Bearer Token) |
| `GET` | `/api/trips` | Returns all trips created by the authenticated user | Yes (Bearer Token) |
| `POST` | `/api/trips` | Creates a new trip for the authenticated user | Yes (Bearer Token) |
| `GET` | `/api/trips/{trip_id}` | Retrieves a specific trip (enforces ownership) | Yes (Bearer Token) |
| `PUT` | `/api/trips/{trip_id}` | Updates a trip (enforces ownership) | Yes (Bearer Token) |
| `DELETE` | `/api/trips/{trip_id}` | Deletes a trip (enforces ownership) | Yes (Bearer Token) |
