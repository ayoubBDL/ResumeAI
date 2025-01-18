-- Update resumes table schema
ALTER TABLE public.resumes 
  ALTER COLUMN content DROP NOT NULL,
  ALTER COLUMN content SET DEFAULT NULL;

-- Make sure all required columns are nullable except for essential ones
ALTER TABLE public.resumes
  ALTER COLUMN user_id SET NOT NULL,
  ALTER COLUMN title SET NOT NULL,
  ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP,
  ALTER COLUMN status SET DEFAULT 'processing',
  ALTER COLUMN optimized_pdf_url DROP NOT NULL,
  ALTER COLUMN analysis DROP NOT NULL,
  ALTER COLUMN job_url DROP NOT NULL;
