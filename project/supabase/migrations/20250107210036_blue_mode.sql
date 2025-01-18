/*
  # Initial schema setup for ResumeAI

  1. Tables
    - profiles
      - id (uuid, references auth.users)
      - created_at (timestamp)
      - updated_at (timestamp)
    
    - resumes
      - id (uuid)
      - user_id (uuid, references profiles.id)
      - original_filename (text)
      - optimized_filename (text)
      - job_url (text)
      - created_at (timestamp)
      - status (text)

  2. Security
    - Enable RLS on all tables
    - Add policies for user data access
*/

-- Create profiles and resumes tables if they don't exist
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_tables WHERE tablename = 'profiles') THEN
        CREATE TABLE profiles (
            id uuid REFERENCES auth.users ON DELETE CASCADE PRIMARY KEY,
            created_at timestamptz DEFAULT now(),
            updated_at timestamptz DEFAULT now()
        );
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_tables WHERE tablename = 'resumes') THEN
        CREATE TABLE resumes (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id uuid REFERENCES profiles(id) ON DELETE CASCADE,
            original_filename text NOT NULL,
            optimized_filename text,
            job_url text NOT NULL,
            created_at timestamptz DEFAULT now(),
            status text DEFAULT 'processing' CHECK (status IN ('processing', 'completed', 'failed'))
        );

        -- Enable RLS
        ALTER TABLE resumes ENABLE ROW LEVEL SECURITY;

        -- Resumes policies
        CREATE POLICY "Users can view own resumes"
          ON resumes FOR SELECT
          TO authenticated
          USING (user_id = auth.uid());

        CREATE POLICY "Users can insert own resumes"
          ON resumes FOR INSERT
          TO authenticated
          WITH CHECK (user_id = auth.uid());

        CREATE POLICY "Users can update own resumes"
          ON resumes FOR UPDATE
          TO authenticated
          USING (user_id = auth.uid());

        CREATE POLICY "Users can delete own resumes"
          ON resumes FOR DELETE
          TO authenticated
          USING (user_id = auth.uid());
    END IF;
END $$;

-- Enable RLS
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

-- Profiles policies
CREATE POLICY "Users can view own profile"
  ON profiles FOR SELECT
  TO authenticated
  USING (auth.uid() = id);

CREATE POLICY "Users can update own profile"
  ON profiles FOR UPDATE
  TO authenticated
  USING (auth.uid() = id);

-- Function to handle profile creation
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS trigger AS $$
BEGIN
  INSERT INTO public.profiles (id)
  VALUES (new.id);
  RETURN new;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger for new user profile creation
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION handle_new_user();