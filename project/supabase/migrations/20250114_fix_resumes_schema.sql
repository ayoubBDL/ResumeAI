-- Drop existing policies
DROP POLICY IF EXISTS "Users can view their own resumes" ON public.resumes;
DROP POLICY IF EXISTS "Users can insert their own resumes" ON public.resumes;
DROP POLICY IF EXISTS "Users can update their own resumes" ON public.resumes;
DROP POLICY IF EXISTS "Users can delete their own resumes" ON public.resumes;

-- Drop dependencies
ALTER TABLE IF EXISTS public.resumes DROP CONSTRAINT IF EXISTS fk_user;

-- Update table schema
ALTER TABLE public.resumes
  DROP COLUMN IF EXISTS content,
  ALTER COLUMN user_id SET NOT NULL,
  ALTER COLUMN title SET NOT NULL,
  ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP,
  ALTER COLUMN optimized_pdf_url DROP NOT NULL,
  ALTER COLUMN analysis DROP NOT NULL,
  ALTER COLUMN job_url DROP NOT NULL,
  ALTER COLUMN status SET DEFAULT 'processing',
  ADD CONSTRAINT status_check CHECK (status IN ('processing', 'completed', 'failed'));

-- Add foreign key constraint
ALTER TABLE public.resumes
  ADD CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES auth.users(id);

-- Enable RLS
ALTER TABLE public.resumes ENABLE ROW LEVEL SECURITY;

-- Create policies
CREATE POLICY "Users can view their own resumes"
ON public.resumes
FOR SELECT
TO authenticated
USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own resumes"
ON public.resumes
FOR INSERT
TO authenticated
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own resumes"
ON public.resumes
FOR UPDATE
TO authenticated
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete their own resumes"
ON public.resumes
FOR DELETE
TO authenticated
USING (auth.uid() = user_id);
