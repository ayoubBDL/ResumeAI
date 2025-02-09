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
            Please optimize this resume and provide improvement suggestions. ‼️ Write ALL content in the DETECTED LANGUAGE from Job description. Format your response in clear sections as follows:

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

         response = openai.ChatCompletion.create(
               model="gpt-4o-mini",  # Using the original model
               messages=[
                  {"role": "system", "content": """You are a professional career advisor that helps optimize resumes and prepare candidates for job opportunities. Your task is to create an ATS-friendly resume that SPECIFICALLY targets this job position.

         CRITICAL - ABSOLUTELY REQUIRED RULES:
         1. JOB MATCHING (HIGHEST PRIORITY):
            ‼️ Write ALL content in the DETECTED LANGUAGE from Job description
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
         - Directly start with Name of the candidate.

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

   def generate_cover_letter(self, resume_text: str, job_description: str, job_title: str, company: str) -> str:
        """Generate a cover letter using the resume and job details"""
        try:
            if not self.api_key:
                raise ValueError("OpenAI API key not configured")

            prompt = f"""
            Generate a professional cover letter for the {job_title} position at {company}. 
            Use the following job description and resume to create a tailored letter.

            Job Description:
            {job_description}

            Resume:
            {resume_text}

            REQUIRED FORMAT:
            - Begin with: "Dear Hiring Manager,"
            - Write exactly three paragraphs
            - End with:
              "Warm regards,
              [Name]"
            - Maximum length: 350 words
            - No dates, addresses, or contact information
            - No headers of any kind
            - No social media links or portfolio references
            - Add a blank line between paragraphs
            - Add a blank line before "Warm regards,"

            PARAGRAPH STRUCTURE:
            1. Opening Paragraph:
               - Express enthusiasm for the specific role at {company}
               - Show understanding of company's industry/mission
               - Brief mention of your relevant expertise

            2. Main Paragraph:
               - Highlight 2-3 specific achievements that match job requirements
               - Include concrete metrics and results
               - Connect your experience directly to the role's needs
               - Focus on technical skills relevant to the position

            3. Closing Paragraph:
               - Brief summary of value you'll bring
               - Clear call to action
               - Keep under 3 sentences

            IMPORTANT RULES:
            - Use active voice
            - Be confident but professional
            - Focus on company's needs
            - No generic phrases or clichés
            - No personal stories
            - No salary discussion
            - No copying resume content verbatim

            The letter should be compelling, concise, and focused entirely on the value the candidate brings to this specific role.
            """

            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert career advisor specializing in creating compelling cover letters."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )

            print("[OpenAI Cover Letter] Successfully received response ", response.choices[0].message.content.strip())

            return response.choices[0].message.content.strip()

        except Exception as e:
            raise Exception(f"Failed to generate cover letter: {str(e)}")
