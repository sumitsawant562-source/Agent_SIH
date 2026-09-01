-- ==============================================================================
-- AGENTIC AI PERSONALIZED TRAVEL INTELLIGENCE PLATFORM
-- Stage 2: Complete Supabase PostgreSQL Schema & Security Policies
--
-- This file is IDEMPOTENT — safe to run multiple times.
-- Execute this in the Supabase SQL Editor (Dashboard → SQL Editor).
-- ==============================================================================

-- 1. EXTENSIONS
-- ==============================================================================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ==============================================================================
-- 2. TABLE: profiles
-- Linked to auth.users; auto-created by trigger on signup.
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.profiles (
    id          UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email       TEXT NOT NULL,
    full_name   TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- ==============================================================================
-- 3. TABLE: trips
-- Stores user trip configurations. Extended in Stage 2 with coordinates,
-- start/end dates, currency, JSONB interests, and special requirements.
-- ==============================================================================

-- Drop the old Stage 1 version if it exists with the narrow schema.
-- If you already have production data, use ALTER TABLE instead.
-- This CREATE TABLE IF NOT EXISTS ensures idempotency on a fresh DB.
CREATE TABLE IF NOT EXISTS public.trips (
    id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id                     UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,

    -- Core trip details
    title                       TEXT NOT NULL,
    start_location              TEXT,
    starting_location           TEXT,
    start_latitude              DOUBLE PRECISION,
    start_longitude             DOUBLE PRECISION,
    destination                 TEXT NOT NULL,
    destination_latitude        DOUBLE PRECISION,
    destination_longitude       DOUBLE PRECISION,

    -- Scheduling
    start_date                  DATE,
    end_date                    DATE,
    travel_date                 DATE,
    duration_days               INTEGER DEFAULT 1 CHECK (duration_days > 0),

    -- Group
    travelers                   INTEGER DEFAULT 1 CHECK (travelers >= 1),
    adults                      INTEGER DEFAULT 1 CHECK (adults >= 1),
    children                    INTEGER DEFAULT 0 CHECK (children >= 0),

    -- Budget
    budget                      NUMERIC DEFAULT 0 CHECK (budget >= 0),
    currency                    TEXT DEFAULT 'INR',

    -- Preferences
    transport_mode              TEXT DEFAULT 'flight',
    food_preference             TEXT DEFAULT 'no preference',
    stay_preference             TEXT DEFAULT 'hotel',
    accommodation_preference    TEXT DEFAULT 'hotel',
    travel_style                TEXT DEFAULT 'balanced',
    interests                   JSONB DEFAULT '[]'::jsonb,
    special_requirements        TEXT,

    -- Status tracking
    status                      TEXT NOT NULL DEFAULT 'draft'
                                    CHECK (status IN ('draft', 'planning', 'generating', 'completed', 'cancelled')),

    -- Timestamps
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at                  TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

COMMENT ON TABLE public.trips IS 'Stores user travel configurations and preferences. Core entity for itinerary generation.';

-- Idempotent column migrations for existing databases
DO $$
BEGIN
    -- Coordinate columns
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='trips' AND column_name='start_latitude') THEN
        ALTER TABLE public.trips ADD COLUMN start_latitude DOUBLE PRECISION;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='trips' AND column_name='start_longitude') THEN
        ALTER TABLE public.trips ADD COLUMN start_longitude DOUBLE PRECISION;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='trips' AND column_name='destination_latitude') THEN
        ALTER TABLE public.trips ADD COLUMN destination_latitude DOUBLE PRECISION;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='trips' AND column_name='destination_longitude') THEN
        ALTER TABLE public.trips ADD COLUMN destination_longitude DOUBLE PRECISION;
    END IF;
    -- Location aliases
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='trips' AND column_name='start_location') THEN
        ALTER TABLE public.trips ADD COLUMN start_location TEXT;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='trips' AND column_name='starting_location') THEN
        ALTER TABLE public.trips ADD COLUMN starting_location TEXT;
    END IF;
    -- Date columns
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='trips' AND column_name='start_date') THEN
        ALTER TABLE public.trips ADD COLUMN start_date DATE;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='trips' AND column_name='end_date') THEN
        ALTER TABLE public.trips ADD COLUMN end_date DATE;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='trips' AND column_name='travel_date') THEN
        ALTER TABLE public.trips ADD COLUMN travel_date DATE;
    END IF;
    -- Travelers & Group
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='trips' AND column_name='travelers') THEN
        ALTER TABLE public.trips ADD COLUMN travelers INTEGER DEFAULT 1 CHECK (travelers >= 1);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='trips' AND column_name='adults') THEN
        ALTER TABLE public.trips ADD COLUMN adults INTEGER DEFAULT 1 CHECK (adults >= 1);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='trips' AND column_name='children') THEN
        ALTER TABLE public.trips ADD COLUMN children INTEGER DEFAULT 0 CHECK (children >= 0);
    END IF;
    -- Currency & Budget
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='trips' AND column_name='currency') THEN
        ALTER TABLE public.trips ADD COLUMN currency TEXT DEFAULT 'INR';
    END IF;
    -- Preferences & Style
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='trips' AND column_name='stay_preference') THEN
        ALTER TABLE public.trips ADD COLUMN stay_preference TEXT DEFAULT 'hotel';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='trips' AND column_name='accommodation_preference') THEN
        ALTER TABLE public.trips ADD COLUMN accommodation_preference TEXT DEFAULT 'hotel';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='trips' AND column_name='travel_style') THEN
        ALTER TABLE public.trips ADD COLUMN travel_style TEXT DEFAULT 'balanced';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='trips' AND column_name='special_requirements') THEN
        ALTER TABLE public.trips ADD COLUMN special_requirements TEXT;
    END IF;
END $$;

-- Trigger to keep column aliases in sync automatically
CREATE OR REPLACE FUNCTION public.sync_trip_column_aliases()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.start_location IS NULL AND NEW.starting_location IS NOT NULL THEN
        NEW.start_location := NEW.starting_location;
    ELSIF NEW.starting_location IS NULL AND NEW.start_location IS NOT NULL THEN
        NEW.starting_location := NEW.start_location;
    END IF;

    IF NEW.start_date IS NULL AND NEW.travel_date IS NOT NULL THEN
        NEW.start_date := NEW.travel_date;
    ELSIF NEW.travel_date IS NULL AND NEW.start_date IS NOT NULL THEN
        NEW.travel_date := NEW.start_date;
    END IF;

    IF NEW.stay_preference IS NULL AND NEW.accommodation_preference IS NOT NULL THEN
        NEW.stay_preference := NEW.accommodation_preference;
    ELSIF NEW.accommodation_preference IS NULL AND NEW.stay_preference IS NOT NULL THEN
        NEW.accommodation_preference := NEW.stay_preference;
    END IF;

    IF NEW.travelers IS NULL THEN
        NEW.travelers := COALESCE(NEW.adults, 1) + COALESCE(NEW.children, 0);
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tr_sync_trip_aliases ON public.trips;
CREATE TRIGGER tr_sync_trip_aliases
    BEFORE INSERT OR UPDATE ON public.trips
    FOR EACH ROW EXECUTE PROCEDURE public.sync_trip_column_aliases();

-- ==============================================================================
-- 4. TABLE: itineraries
-- Stores AI-generated itineraries for a trip. Supports versioning.
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.itineraries (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trip_id             UUID NOT NULL REFERENCES public.trips(id) ON DELETE CASCADE,
    version             INTEGER NOT NULL DEFAULT 1 CHECK (version >= 1),
    itinerary_data      JSONB DEFAULT '{}'::jsonb,
    estimated_cost      NUMERIC,
    currency            TEXT DEFAULT 'INR',
    status              TEXT NOT NULL DEFAULT 'draft'
                            CHECK (status IN ('draft', 'generating', 'completed', 'failed')),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

COMMENT ON TABLE public.itineraries IS 'AI-generated itineraries linked to trips. Supports versioning for re-generation and adaptation.';

-- ==============================================================================
-- 5. INDEXES
-- ==============================================================================
CREATE INDEX IF NOT EXISTS idx_trips_user_id        ON public.trips(user_id);
CREATE INDEX IF NOT EXISTS idx_trips_status          ON public.trips(status);
CREATE INDEX IF NOT EXISTS idx_trips_created_at      ON public.trips(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_itineraries_trip_id   ON public.itineraries(trip_id);
CREATE INDEX IF NOT EXISTS idx_itineraries_status    ON public.itineraries(status);

-- ==============================================================================
-- 6. ROW LEVEL SECURITY (RLS)
-- ==============================================================================

-- Enable RLS on all tables
ALTER TABLE public.profiles    ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.trips       ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.itineraries ENABLE ROW LEVEL SECURITY;

-- ---------- profiles ----------
DROP POLICY IF EXISTS "Users can view own profile" ON public.profiles;
CREATE POLICY "Users can view own profile"
    ON public.profiles FOR SELECT
    USING (auth.uid() = id);

DROP POLICY IF EXISTS "Users can insert own profile" ON public.profiles;
CREATE POLICY "Users can insert own profile"
    ON public.profiles FOR INSERT
    WITH CHECK (auth.uid() = id);

DROP POLICY IF EXISTS "Users can update own profile" ON public.profiles;
CREATE POLICY "Users can update own profile"
    ON public.profiles FOR UPDATE
    USING (auth.uid() = id)
    WITH CHECK (auth.uid() = id);

-- ---------- trips ----------
DROP POLICY IF EXISTS "Users can view own trips" ON public.trips;
CREATE POLICY "Users can view own trips"
    ON public.trips FOR SELECT
    USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can create own trips" ON public.trips;
CREATE POLICY "Users can create own trips"
    ON public.trips FOR INSERT
    WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own trips" ON public.trips;
CREATE POLICY "Users can update own trips"
    ON public.trips FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete own trips" ON public.trips;
CREATE POLICY "Users can delete own trips"
    ON public.trips FOR DELETE
    USING (auth.uid() = user_id);

-- ---------- itineraries ----------
-- Users can only access itineraries where the parent trip belongs to them.
DROP POLICY IF EXISTS "Users can view own itineraries" ON public.itineraries;
CREATE POLICY "Users can view own itineraries"
    ON public.itineraries FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.trips
            WHERE trips.id = itineraries.trip_id
              AND trips.user_id = auth.uid()
        )
    );

DROP POLICY IF EXISTS "Users can create itineraries for own trips" ON public.itineraries;
CREATE POLICY "Users can create itineraries for own trips"
    ON public.itineraries FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.trips
            WHERE trips.id = itineraries.trip_id
              AND trips.user_id = auth.uid()
        )
    );

DROP POLICY IF EXISTS "Users can update own itineraries" ON public.itineraries;
CREATE POLICY "Users can update own itineraries"
    ON public.itineraries FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM public.trips
            WHERE trips.id = itineraries.trip_id
              AND trips.user_id = auth.uid()
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.trips
            WHERE trips.id = itineraries.trip_id
              AND trips.user_id = auth.uid()
        )
    );

DROP POLICY IF EXISTS "Users can delete own itineraries" ON public.itineraries;
CREATE POLICY "Users can delete own itineraries"
    ON public.itineraries FOR DELETE
    USING (
        EXISTS (
            SELECT 1 FROM public.trips
            WHERE trips.id = itineraries.trip_id
              AND trips.user_id = auth.uid()
        )
    );

-- ==============================================================================
-- 7. FUNCTIONS & TRIGGERS
-- ==============================================================================

-- Auto-create profile on user signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (id, email, full_name, created_at, updated_at)
    VALUES (
        new.id,
        new.email,
        COALESCE(new.raw_user_meta_data->>'full_name', split_part(new.email, '@', 1)),
        now(),
        now()
    )
    ON CONFLICT (id) DO UPDATE
    SET email = EXCLUDED.email,
        full_name = COALESCE(EXCLUDED.full_name, profiles.full_name),
        updated_at = now();
    RETURN new;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE PROCEDURE public.handle_new_user();

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = timezone('utc'::text, now());
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS handle_profiles_updated_at ON public.profiles;
CREATE TRIGGER handle_profiles_updated_at
    BEFORE UPDATE ON public.profiles
    FOR EACH ROW EXECUTE PROCEDURE public.set_updated_at();

DROP TRIGGER IF EXISTS handle_trips_updated_at ON public.trips;
CREATE TRIGGER handle_trips_updated_at
    BEFORE UPDATE ON public.trips
    FOR EACH ROW EXECUTE PROCEDURE public.set_updated_at();

DROP TRIGGER IF EXISTS handle_itineraries_updated_at ON public.itineraries;
CREATE TRIGGER handle_itineraries_updated_at
    BEFORE UPDATE ON public.itineraries
    FOR EACH ROW EXECUTE PROCEDURE public.set_updated_at();
