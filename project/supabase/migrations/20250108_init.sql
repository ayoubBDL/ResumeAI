-- Create tables if they don't exist
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_tables WHERE tablename = 'profiles') THEN
        CREATE TABLE profiles (
            id UUID REFERENCES auth.users ON DELETE CASCADE,
            email TEXT UNIQUE,
            full_name TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (id)
        );

        -- Enable RLS
        ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

        -- Create policies
        CREATE POLICY "Users can view own profile" ON profiles
            FOR SELECT USING (auth.uid() = id);

        CREATE POLICY "Users can update own profile" ON profiles
            FOR UPDATE USING (auth.uid() = id);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_tables WHERE tablename = 'resumes') THEN
        CREATE TABLE resumes (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
            title TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );

        -- Enable RLS
        ALTER TABLE resumes ENABLE ROW LEVEL SECURITY;

        -- Create policies
        CREATE POLICY "Users can view own resumes" ON resumes
            FOR SELECT USING (auth.uid() = user_id);

        CREATE POLICY "Users can insert own resumes" ON resumes
            FOR INSERT WITH CHECK (auth.uid() = user_id);

        CREATE POLICY "Users can update own resumes" ON resumes
            FOR UPDATE USING (auth.uid() = user_id);

        CREATE POLICY "Users can delete own resumes" ON resumes
            FOR DELETE USING (auth.uid() = user_id);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_tables WHERE tablename = 'job_applications') THEN
        CREATE TABLE job_applications (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID REFERENCES auth.users ON DELETE CASCADE,
            resume_id UUID REFERENCES resumes(id) ON DELETE SET NULL,
            job_title TEXT NOT NULL,
            company TEXT NOT NULL,
            job_description TEXT,
            job_url TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );

        -- Enable RLS
        ALTER TABLE job_applications ENABLE ROW LEVEL SECURITY;

        -- Create policies
        CREATE POLICY "Users can view own job applications" ON job_applications
            FOR SELECT USING (auth.uid() = user_id);

        CREATE POLICY "Users can manage own job applications" ON job_applications
            FOR ALL USING (auth.uid() = user_id);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_tables WHERE tablename = 'subscriptions') THEN
        CREATE TABLE subscriptions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID REFERENCES auth.users ON DELETE CASCADE,
            plan_type TEXT NOT NULL,
            status TEXT NOT NULL,
            current_period_start TIMESTAMP WITH TIME ZONE,
            current_period_end TIMESTAMP WITH TIME ZONE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );

        -- Enable RLS
        ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;

        -- Create policies
        CREATE POLICY "Users can view own subscription" ON subscriptions
            FOR SELECT USING (auth.uid() = user_id);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_tables WHERE tablename = 'usage_credits') THEN
        CREATE TABLE usage_credits (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID REFERENCES auth.users ON DELETE CASCADE,
            credits_remaining INTEGER DEFAULT 0,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );

        -- Enable RLS
        ALTER TABLE usage_credits ENABLE ROW LEVEL SECURITY;

        -- Create policies
        CREATE POLICY "Users can view own credits" ON usage_credits
            FOR SELECT USING (auth.uid() = user_id);
    END IF;
END $$;

-- Create function for handling new users if it doesn't exist
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER AS $BODY$
BEGIN
    INSERT INTO public.profiles (id, email)
    VALUES (new.id, new.email);
    
    INSERT INTO public.usage_credits (user_id, credits_remaining)
    VALUES (new.id, 2);
    
    RETURN new;
END;
$BODY$ LANGUAGE plpgsql SECURITY DEFINER;

-- Drop trigger if exists and recreate
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION handle_new_user();
