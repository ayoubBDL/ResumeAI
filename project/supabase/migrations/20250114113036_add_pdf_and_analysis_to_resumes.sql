-- Add columns to resumes table if they don't exist
DO $$ 
BEGIN 
    IF NOT EXISTS (SELECT 1 FROM pg_tables WHERE tablename = 'resumes') THEN
        RAISE NOTICE 'Table resumes does not exist, skipping...';
        RETURN;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'resumes' AND column_name = 'original_pdf_url') THEN
        ALTER TABLE resumes ADD COLUMN original_pdf_url TEXT;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'resumes' AND column_name = 'optimized_pdf_url') THEN
        ALTER TABLE resumes ADD COLUMN optimized_pdf_url TEXT;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'resumes' AND column_name = 'analysis') THEN
        ALTER TABLE resumes ADD COLUMN analysis TEXT;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'resumes' AND column_name = 'job_url') THEN
        ALTER TABLE resumes ADD COLUMN job_url TEXT;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'resumes' AND column_name = 'status') THEN
        ALTER TABLE resumes ADD COLUMN status TEXT DEFAULT 'processing';
    END IF;
END $$;