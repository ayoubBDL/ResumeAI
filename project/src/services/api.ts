import { supabase } from '../lib/supabaseClient';

const API_URL = import.meta.env.VITE_RESUME_API_URL;
const JOB_API_URL = import.meta.env.VITE_JOB_API_URL;

export interface JobApplication {
  id: string;
  user_id: string;
  resume_id: string | null;
  job_title: string;
  company: string;
  job_description: string | null;
  job_url: string | null;
  status: 'pending' | 'applied' | 'interviewing' | 'offered' | 'rejected';
  created_at: string;
  updated_at: string;
}

export interface Resume {
  id: string;
  user_id: string;
  title: string;
  created_at: string;
  optimized_pdf_url: string | null;
  analysis: string | null;
  job_url: string | null;
  status: 'processing' | 'completed' | 'failed';
}

export interface OptimizedResume {
  id: string;
  title: string;
  created_at: string;
  pdf_url: string;
  analysis: string;
  job_url: string;
}

// Resume optimization service
export const optimizeResume = async (formData: FormData): Promise<Resume> => {
  try {
    // Get the current user and session
    const { data: { session } } = await supabase.auth.getSession();
    if (!session?.user) {
      throw new Error('User not authenticated');
    }

    // Call the optimization endpoint first
    const response = await fetch(`${API_URL}/optimize`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('Optimization error:', errorText);
      throw new Error('Failed to optimize resume');
    }

    // Get the PDF blob from the response
    const pdfBlob = await response.blob();
    if (pdfBlob.size === 0) {
      throw new Error('Received empty PDF from server');
    }

    const originalFile = formData.get('resume') as File;
    const safeFileName = originalFile.name.replace(/[^a-zA-Z0-9.-]/g, '_');
    const filename = `${Date.now()}_${safeFileName}`;
    
    console.log('Uploading file:', {
      filename,
      contentType: pdfBlob.type,
      size: pdfBlob.size
    });
    
    // Create a new blob with explicit PDF type
    const pdfBlobWithType = new Blob([pdfBlob], { type: 'application/pdf' });
    
    // Upload optimized PDF to Supabase Storage
    const { error: uploadError } = await supabase.storage
      .from('resumes')
      .upload(filename, pdfBlobWithType, {
        cacheControl: '3600',
        upsert: false,
        contentType: 'application/pdf'
      });

    if (uploadError) {
      console.error('Upload error:', uploadError);
      throw uploadError;
    }

    // Get public URL for the PDF
    const { data } = await supabase.storage
      .from('resumes')
      .createSignedUrl(filename, 60 * 60); // 1 hour expiry

    if (!data?.signedUrl) {
      throw new Error('Failed to get signed URL');
    }

    console.log('File uploaded successfully:', {
      filename,
      url: data.signedUrl
    });

    // Create database record
    const { data: resumeRecord, error: createError } = await supabase
      .from('resumes')
      .insert({
        user_id: session.user.id,
        title: safeFileName,
        job_url: formData.get('job_url'),
        optimized_pdf_url: data.signedUrl,
        status: 'completed'
      })
      .select()
      .single();

    if (createError) {
      console.error('Database error:', createError);
      throw createError;
    }

    return resumeRecord;
  } catch (error) {
    console.error('Error in optimizeResume:', error);
    throw error;
  }
};

// Helper function to download a file from Supabase Storage
export const getResumeDownloadUrl = async (filePath: string): Promise<string> => {
  try {
    // Get the current user and session
    const { data: { session } } = await supabase.auth.getSession();
    if (!session?.user) {
      throw new Error('User not authenticated');
    }

    // Get the signed URL with an expiry of 60 minutes
    const { data, error } = await supabase.storage
      .from('public')
      .createSignedUrl(filePath, 60 * 60);

    if (error || !data?.signedUrl) {
      console.error('Error generating signed URL:', error);
      throw new Error('Failed to generate download URL');
    }

    return data.signedUrl;
  } catch (error) {
    console.error('Error in getResumeDownloadUrl:', error);
    throw error;
  }
};

// Helper function to convert base64 to Blob
function base64ToBlob(base64: string, type: string): Blob {
  const byteCharacters = atob(base64);
  const byteArrays = [];

  for (let offset = 0; offset < byteCharacters.length; offset += 512) {
    const slice = byteCharacters.slice(offset, offset + 512);
    const byteNumbers = new Array(slice.length);

    for (let i = 0; i < slice.length; i++) {
      byteNumbers[i] = slice.charCodeAt(i);
    }

    const byteArray = new Uint8Array(byteNumbers);
    byteArrays.push(byteArray);
  }

  return new Blob(byteArrays, { type });
}

export const getRecentResumes = async (): Promise<Resume[]> => {
  try {
    // Get the current user and session
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) {
      throw new Error('No active session');
    }

    // Get user from session
    const user = session.user;
    if (!user) {
      throw new Error('User not authenticated');
    }

    // Use explicit query parameters
    const { data, error } = await supabase
      .from('resumes')
      .select(`
        id,
        user_id,
        title,
        created_at,
        optimized_pdf_url,
        analysis,
        job_url,
        status
      `)
      .eq('user_id', user.id)
      .order('created_at', { ascending: false })
      .limit(10);

    if (error) {
      console.error('Error fetching resumes:', error);
      throw error;
    }

    return (data || []) as Resume[];
  } catch (error) {
    console.error('Error in getRecentResumes:', error);
    throw error;
  }
};

// Supabase database operations
export const saveJobApplication = async (
  userId: string,
  jobTitle: string,
  company: string,
  jobDescription: string,
  jobUrl: string,
  resumeId?: string
) => {
  const { data, error } = await supabase
    .from('job_applications')
    .insert([
      {
        user_id: userId,
        resume_id: resumeId,
        job_title: jobTitle,
        company,
        job_description: jobDescription,
        job_url: jobUrl,
        status: 'pending'
      }
    ])
    .select()
    .single();

  if (error) throw error;
  return data;
};

export const getJobApplications = async (userId: string) => {
  const { data, error } = await supabase
    .from('job_applications')
    .select('*, resumes(*)')
    .eq('user_id', userId)
    .order('created_at', { ascending: false });

  if (error) throw error;
  return data;
};

export const updateJobApplicationStatus = async (jobId: string, status: JobApplication['status']) => {
  const { data, error } = await supabase
    .from('job_applications')
    .update({ status })
    .eq('id', jobId)
    .select()
    .single();

  if (error) throw error;
  return data;
};
