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
    const response = await fetch(`/api/optimize`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('Optimization error:', errorText);
      throw new Error('Failed to optimize resume');
    }

    // Check content type
    const contentType = response.headers.get('content-type');
    if (!contentType?.includes('application/json')) {
      console.error('Unexpected content type:', contentType);
      throw new Error('Server returned invalid response format');
    }

    // Get the response data
    let responseData;
    try {
      responseData = await response.json();
      console.log('[DEBUG] Response data:', responseData);
    } catch (error) {
      console.error('Error parsing response:', error);
      throw new Error('Failed to parse server response');
    }

    if (!responseData.success || !responseData.pdf_data || !responseData.analysis) {
      console.error('Invalid response data:', responseData);
      throw new Error('Server returned incomplete data');
    }

    // Convert base64 PDF to blob
    const pdfBlob = base64ToBlob(responseData.pdf_data, 'application/pdf');
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
        analysis: responseData.analysis,  // Store the analysis from the response
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

// Get recent resumes
export async function getRecentResumes(): Promise<Resume[]> {
  const { data: { session } } = await supabase.auth.getSession();
  if (!session?.user) {
    throw new Error('Not authenticated');
  }

  const response = await fetch(`/api/resumes`, {
    method: 'GET',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      'X-User-Id': session.user.id
    }
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to get resumes');
  }

  return response.json();
}

// Delete resume
export async function deleteResume(id: string): Promise<void> {
  const { data: { session } } = await supabase.auth.getSession();
  if (!session?.user) {
    throw new Error('Not authenticated');
  }

  const response = await fetch(`/api/resumes/${id}`, {
    method: 'DELETE',
    headers: {
      'Content-Type': 'application/json',
      'X-User-Id': session.user.id
    }
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to delete resume');
  }
}

// Get resume download URL
export const getResumeDownloadUrl = async (resumeId: string) => {
  try {
    const { data: { session } } = await supabase.auth.getSession();
    if (!session?.user) {
      throw new Error('Not authenticated');
    }

    const response = await fetch(`/api/resumes/${resumeId}/download`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'X-User-Id': session.user.id
      }
    });

    if (!response.ok) {
      throw new Error('Failed to download resume');
    }

    // Create blob from response
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    
    // Create and click download link
    const a = document.createElement('a');
    a.href = url;
    a.download = `${resumeId}_resume.pdf`;
    document.body.appendChild(a);
    a.click();
    
    // Cleanup
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  } catch (error) {
    console.error('Error downloading resume:', error);
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
