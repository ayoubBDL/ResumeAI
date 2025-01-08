export interface Profile {
  id: string;
  email: string;
  full_name: string | null;
  created_at: string;
  updated_at: string;
}

export interface Resume {
  id: string;
  user_id: string;
  title: string;
  content: {
    basics: {
      name: string;
      email: string;
      phone?: string;
      location?: string;
      summary?: string;
    };
    experience: Array<{
      company: string;
      position: string;
      startDate: string;
      endDate?: string;
      description: string;
    }>;
    education: Array<{
      institution: string;
      degree: string;
      field: string;
      startDate: string;
      endDate?: string;
    }>;
    skills: Array<{
      name: string;
      level?: string;
    }>;
  };
  is_template: boolean;
  created_at: string;
  updated_at: string;
}

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

export interface Subscription {
  id: string;
  user_id: string;
  plan_type: 'free' | 'pay_as_you_go' | 'pro';
  status: 'active' | 'canceled' | 'expired';
  current_period_start: string;
  current_period_end: string;
  created_at: string;
  updated_at: string;
}

export interface UsageCredits {
  id: string;
  user_id: string;
  credits_remaining: number;
  created_at: string;
  updated_at: string;
}
