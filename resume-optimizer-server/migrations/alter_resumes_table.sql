-- Add cover letter related columns to resumes table
ALTER TABLE resumes
ADD COLUMN IF NOT EXISTS cover_letter_pdf_url text,
ADD COLUMN IF NOT EXISTS cover_letter text;
