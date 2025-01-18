-- Create or update the resumes bucket
DO $$ 
BEGIN
    -- Create bucket if it doesn't exist
    INSERT INTO storage.buckets (id, name, public)
    VALUES ('resumes', 'resumes', true)
    ON CONFLICT (id) DO UPDATE
    SET public = true;

    -- Enable RLS
    ALTER TABLE storage.objects ENABLE ROW LEVEL SECURITY;

    -- Drop existing policies
    DROP POLICY IF EXISTS "Give users access to own folder" ON storage.objects;
    DROP POLICY IF EXISTS "Allow public read access" ON storage.objects;

    -- Create policy for authenticated users to manage their own files
    CREATE POLICY "Give users access to own folder" 
    ON storage.objects
    FOR ALL 
    TO authenticated
    USING (bucket_id = 'resumes')
    WITH CHECK (bucket_id = 'resumes');

    -- Create policy for public read access
    CREATE POLICY "Allow public read access"
    ON storage.objects
    FOR SELECT
    TO public
    USING (bucket_id = 'resumes');
END $$;
