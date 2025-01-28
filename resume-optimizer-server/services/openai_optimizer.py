import os
import openai
from typing import Dict
import re

class OpenAIOptimizer:
   def __init__(self):
      self.api_key = os.getenv("OPENAI_API_KEY")
      if self.api_key:
            openai.api_key = self.api_key

   async def optimize(self, resume_text: str, job_description: str, 
                     job_title: str, company: str, 
                     custom_instructions: str = None) -> Dict:
      try:
            if not self.api_key:
               raise ValueError("OpenAI API key not configured")
   
            # Construct the prompt
            prompt = self._construct_prompt(
               resume_text, 
               job_description, 
               job_title, 
               company, 
               custom_instructions
            )

            # Call OpenAI API
            response = openai.ChatCompletion.create(
               model="GPT-4o mini",  # or gpt-3.5-turbo
               messages=[
                  {"role": "system", "content": "You are an expert resume optimizer with years of experience in HR and recruitment."},
                  {"role": "user", "content": prompt}
               ],
               temperature=0.7,
               max_tokens=4000
            )

            
            # Parse the response
            return self._parse_response(response.choices[0].message.content)

      except Exception as e:
            raise Exception(f"Failed to optimize resume with OpenAI: {str(e)}")

   def _construct_prompt(self, resume_text: str, job_description: str, 
                        job_title: str, company: str, 
                        custom_instructions: str = None) -> str:
      prompt = f"""
      You are an expert resume optimizer with deep experience in technical recruitment and HR. Your task is to optimize the following resume for the position of {job_title} at {company}.

      Job Description:
      {job_description}

      Original Resume:
      {resume_text}

      {f'Additional Instructions: {custom_instructions}' if custom_instructions else ''}

      Follow these optimization guidelines carefully:

      1. RESUME STRUCTURE AND FORMATTING:
         - Use markdown formatting: *** for main section titles, ** for subtitles
         - Maintain consistent spacing between sections
         - Ensure clear visual hierarchy
         - Use bullet points for achievements and responsibilities
         - Keep formatting ATS-friendly

      2. REQUIRED SECTIONS (in order):
         a) ***PERSONAL INFORMATION***
            - Full name (prominently displayed)
            - Professional title aligned with job
            - Contact details (phone, email)
            - Location
            - LinkedIn/GitHub profiles

         b) ***PROFESSIONAL SUMMARY***
            - 3-4 impactful sentences
            - Highlight years of experience
            - Mention key technical expertise
            - Align with job requirements

         c) ***TECHNICAL SKILLS***
            Group into clear categories:
            - Programming Languages
            - Frameworks & Libraries
            - Databases & Storage
            - Cloud & DevOps
            - Tools & Methodologies
            - Soft Skills

         d) ***PROFESSIONAL EXPERIENCE***
            For each role:
            - Company name and location
            - Position title
            - Dates (MM/YYYY)
            - 4-6 achievement-focused bullets
            - Include metrics and technical details
            - Match keywords from job description

         e) ***PROJECTS***
            For each significant project:
            - Project name and purpose
            - Technologies used
            - Your role and responsibilities
            - Quantifiable outcomes
            - Links to live demos/repositories

         f) ***EDUCATION***
            - Degree and major
            - Institution name
            - Graduation date
            - Relevant coursework (if applicable)
            - Academic achievements

         g) ***CERTIFICATIONS*** (if any)
            - Name of certification
            - Issuing organization
            - Date obtained/expiration

         h) ***LANGUAGES***
            - List languages with proficiency levels

      3. CONTENT OPTIMIZATION:
         - Use strong action verbs
         - Include specific technical terms from job description
         - Quantify achievements with metrics
         - Highlight leadership and collaboration
         - Show problem-solving abilities
         - Demonstrate business impact

      4. TECHNICAL DETAILS:
         - Mention specific versions of technologies
         - Include methodologies and best practices
         - Show full stack capabilities
         - Highlight scalability and performance improvements
         - Include security and optimization work

      5. KEYWORDS AND ATS:
         - Include exact matches from job description
         - Add industry-standard variations
         - Spell out acronyms
         - Use recognized industry terms

      PART 1: OPTIMIZED RESUME
      Provide the complete optimized resume text here, using the markdown formatting and structure specified above.

      PART 2: DETAILED ANALYSIS
      Format the analysis exactly as shown below, maintaining the exact structure and markers:

      [SECTION:IMPROVEMENTS]
      • Reorganized Content
      - Restructured sections for better flow
      - Enhanced readability and scannability
      
      • Enhanced Technical Skills
      - Added relevant technologies
      - Prioritized key skills
      
      • Strengthened Experience
      - Added quantifiable metrics
      - Highlighted leadership roles
      
      • Optimized Keywords
      - Incorporated job-specific terms
      - Added industry-standard variations
      [/SECTION]

      [SECTION:INTERVIEW]
      • Technical Topics
      - Review system design principles
      - Practice algorithm optimization
      
      • Project Highlights
      - Prepare STAR stories for key projects
      - Focus on technical challenges solved
      
      • Key Questions
      - How do you handle scalability?
      - Describe your testing approach
      
      • Discussion Points
      - Team collaboration examples
      - Code quality practices
      [/SECTION]

      [SECTION:NEXTSTEPS]
      • Skills Development
      - Learn new framework versions
      - Deepen cloud expertise
      
      • Certifications
      - Relevant technical certifications
      - Industry-specific training
      
      • Portfolio Enhancement
      - Add more complex projects
      - Showcase specific skills
      
      • Industry Knowledge
      - Follow technology trends
      - Join professional communities
      [/SECTION]

      Ensure each section follows this exact format with main points marked by • and sub-points marked by -. 
      Keep the section markers exactly as shown: [SECTION:NAME] and [/SECTION].
      """
      return prompt

   def _parse_response(self, response: str) -> Dict:
      # Split into resume and analysis parts
      parts = response.split('PART 2: DETAILED ANALYSIS')
      
      # Get the resume part
      resume_part = parts[0].split('PART 1: OPTIMIZED RESUME')[-1].strip()
      
      # Get the analysis part
      analysis_part = parts[1].strip() if len(parts) > 1 else ""
      
      return {
            "optimized_resume": resume_part,
            "analysis": analysis_part
      }

   def generate_with_openai(self, job_title, company, resume_text, job_description):
      """Generate optimization suggestions using OpenAI"""
      try:
         print("[OpenAI] Sending request to OpenAI API...")

         optimization_prompt = f"""
            Please optimize this resume and provide improvement suggestions. Format your response in clear sections as follows:

            1. First, provide the optimized resume content with proper formatting.

            2. Then add the following sections, each starting with its section marker:

            [SECTION: IMPROVEMENTS]
            List specific improvements made to the resume and why they enhance it.

            [SECTION: INTERVIEW]
            Provide preparation tips for interviews based on this resume.

            [SECTION: NEXTSTEPS]
            Suggest next steps for career development and resume enhancement.
            """
         if job_title and company:
            optimization_prompt += f" Optimize specifically for the position of {job_title} at {company}."
            
            optimization_prompt += f"""
            
            Original Resume:
            {resume_text}
            """
            
            if job_description:
                optimization_prompt += f"""
                
                Job Description:
                {job_description}
                """
         print("[OpenAI] Hello...", job_title, company)

         response = openai.ChatCompletion.create(
               model="gpt-4o-mini",  # Using the original model
               messages=[
                  {"role": "system", "content": """You are a professional career advisor that helps optimize resumes and prepare candidates for job opportunities. Your task is to create an ATS-friendly resume that SPECIFICALLY targets this job position.

         CRITICAL - ABSOLUTELY REQUIRED RULES:
         1. JOB MATCHING (HIGHEST PRIORITY):
            ‼️ Analyze the job description thoroughly
            ‼️ Identify key requirements, skills, and qualifications
            ‼️ Reorganize and emphasize resume content to match job requirements
            ‼️ Use similar terminology as the job description
            ‼️ Highlight experiences that directly relate to job requirements
            ‼️ Ensure technical skills match what's asked in the job

         PART 1: OPTIMIZED RESUME
         =======================
         Create a clean, professional resume with these sections:
         1. Contact Information (keep original details)
         2. Professional Summary (concise, impactful)
         3. Technical Skills (prioritize job-relevant skills)
         4. Professional Experience (emphasize relevant achievements)
         5. Education (keep as in original)

         FORMAT RULES:
         - NO headers like "ATS-FRIENDLY" or separator lines
         - Clean, minimal formatting
         - Use bullet points (•) for experience and skills
         - Consistent spacing
         - No tables or columns

         PART 2: IMPROVEMENT ANALYSIS
         ===========================
         Format the analysis EXACTLY as shown below, maintaining the exact structure and markers:

         [SECTION:IMPROVEMENTS]
         • Reorganized Content
         - Restructured sections for better flow
         - Enhanced readability and scannability
         
         • Enhanced Technical Skills
         - Added relevant technologies from job description
         - Prioritized key required skills
         
         • Strengthened Experience
         - Added quantifiable metrics
         - Highlighted leadership roles
         
         • Optimized Keywords
         - Incorporated job-specific terms
         - Added industry-standard variations
         [/SECTION]

         [SECTION:INTERVIEW]
         • Technical Topics
         - Key areas from job requirements
         - System design considerations
         
         • Project Highlights
         - Prepare STAR stories for key projects
         - Focus on technical challenges solved
         
         • Key Questions
         - Prepare for role-specific scenarios
         - Technical implementation details
         
         • Discussion Points
         - Team collaboration examples
         - Code quality practices
         [/SECTION]

         [SECTION:NEXTSTEPS]
         • Skills Development
         - Identify skill gaps
         - Learning resources
         
         • Certifications
         - Relevant technical certifications
         - Industry-specific training
         
         • Portfolio Enhancement
         - Project suggestions
         - Skills to demonstrate
         
         • Industry Knowledge
         - Technology trends
         - Professional networking
         [/SECTION]

         FINAL CHECK - VERIFY:
         1. Resume is SPECIFICALLY TAILORED to job description
         2. ALL experience is included but PRIORITIZED for relevance
         3. Skills and technologies MATCH job requirements
         4. NO fictional or assumed information
         5. Original contact details preserved
         6. Analysis sections use EXACT format with [SECTION:NAME] markers

         ‼️ IMPORTANT: Show the COMPLETE response with both parts clearly separated.
         """},
                  {"role": "user", "content": optimization_prompt}
               ],
               temperature=0.7,
               max_tokens=2000
         )
         
         print("[OpenAI] Successfully received response")
         print("\n[OpenAI] Response content:")
         print("=" * 80)
         print(response.choices[0].message.content)
         print("=" * 80)
         
         return response.choices[0].message.content
         
      except Exception as e:
         print(f"[OpenAI ERROR] Error generating optimization suggestions: {str(e)}")
         raise

   def split_ai_response(self, response):
      """Split OpenAI response into resume and analysis parts"""
      # Find all sections using regex
      sections = re.split(r'\[SECTION:\s*([^\]]+)\]', response)
      
      if len(sections) > 1:
         # First part is the resume content
         resume_content = sections[0].strip()
         
         # Combine all sections into analysis
         analysis_parts = []
         for i in range(1, len(sections), 2):
               if i + 1 < len(sections):
                  section_name = sections[i].strip()
                  section_content = sections[i + 1].strip()
                  analysis_parts.append(f"[{section_name}]\n{section_content}")
         
         analysis = "\n\n".join(analysis_parts)
      else:
         # If no sections found, treat everything as resume content
         resume_content = response.strip()
         analysis = ""
      
      return resume_content, analysis
