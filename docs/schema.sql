-- ==============================================================================
-- AGENTIC AI PERSONALIZED TRAVEL INTELLIGENCE PLATFORM
-- Stage 1: Supabase PostgreSQL Schema & Security Policies
-- ==============================================================================

-- 1. EXTENSIONS
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ==============================================================================
-- 2. TABLE: profiles
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT NOT NULL,
    full_name TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- ==============================================================================
-- 3. TABLE: trips
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.trips (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    starting_location TEXT NOT NULL,
    destination TEXT NOT NULL,
    travel_date DATE NOT NULL,
    duration_days INTEGER NOT NULL CHECK (duration_days > 0),
    adults INTEGER NOT NULL DEFAULT 1 CHECK (adults >= 1),
    children INTEGER NOT NULL DEFAULT 0 CHECK (children >= 0),
    budget NUMERIC(12, 2) NOT NULL CHECK (budget > 0),
    transport_mode TEXT NOT NULL CHECK (transport_mode IN ('car', 'bike', 'bus', 'train', 'flight')),
    interests TEXT[] NOT NULL DEFAULT '{}',
    food_preference TEXT NOT NULL CHECK (food_preference IN ('vegetarian', 'non-vegetarian', 'vegan', 'no preference', 'any')),
    accommodation_preference TEXT NOT NULL CHECK (accommodation_preference IN ('hotel', 'homestay', 'hostel', 'resort', 'any')),
    travel_style TEXT NOT NULL CHECK (travel_style IN ('relaxed', 'balanced', 'adventure', 'budget', 'luxury', 'family')),
    status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'planning', 'completed')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_trips_user_id ON public.trips(user_id);
CREATE INDEX IF NOT EXISTS idx_trips_created_at ON public.trips(created_at DESC);

-- ==============================================================================
-- 4. ROW LEVEL SECURITY (RLS) POLICIES
-- ==============================================================================

-- Enable RLS
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.trips ENABLE ROW LEVEL SECURITY;

-- Profiles Policies
DROP POLICY IF EXISTS "Users can view own profile" ON public.profiles;
CREATE POLICY "Users can view own profile"
    ON public.profiles
    FOR SELECT
    USING (auth.uid() = id);

DROP POLICY IF EXISTS "Users can insert own profile" ON public.profiles;
CREATE POLICY "Users can insert own profile"
    ON public.profiles
    FOR INSERT
    WITH CHECK (auth.uid() = id);

DROP POLICY IF EXISTS "Users can update own profile" ON public.profiles;
CREATE POLICY "Users can update own profile"
    ON public.profiles
    FOR UPDATE
    USING (auth.uid() = id)
    WITH CHECK (auth.uid() = id);

-- Trips Policies (Strict isolation: User A cannot read, modify, or delete User B's trips)
DROP POLICY IF EXISTS "Users can view own trips" ON public.trips;
CREATE POLICY "Users can view own trips"
    ON public.trips
    FOR SELECT
    USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can create own trips" ON public.trips;
CREATE POLICY "Users can create own trips"
    ON public.trips
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own trips" ON public.trips;
CREATE POLICY "Users can update own trips"
    ON public.trips
    FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete own trips" ON public.trips;
CREATE POLICY "Users can delete own trips"
    ON public.trips
    FOR DELETE
    USING (auth.uid() = user_id);

-- ==============================================================================
-- 5. AUTOMATIC TRIGGERS & FUNCTIONS
-- ==============================================================================

-- Trigger to automatically create a profile entry when a user signs up via Supabase Auth
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

-- Trigger to automatically update updated_at timestamp on records
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
