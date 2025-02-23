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
               model="gpt-4o-mini",
               messages=[
                  {"role": "system", "content": """You are a professional career advisor that helps optimize resumes and prepare candidates for job opportunities. Your task is to create an ATS-friendly resume that SPECIFICALLY targets this job position.

         CRITICAL - ABSOLUTELY REQUIRED RULES:
         1. JOB MATCHING (HIGHEST PRIORITY):
            !! Write ALL content in the DETECTED LANGUAGE from Job description
            !! Analyze the job description thoroughly
            !! Identify key requirements, skills, and qualifications
            !! Reorganize and emphasize resume content to match job requirements
            !! Use similar terminology as the job description
            !! Highlight experiences that directly relate to job requirements
            !! PLEASE DO NOT FORGET TO ADD THE CANDIDATE TITLE AFTER THE NAME eg Software Engineer, Product Manager, etc !! 
            !! Make sure to add *** for Titles of the sections and ** for smaller titles and * for bold text inside the sections !!
            !! Ensure technical skills match what's asked in the job
            - Summarize concisely: Reduce each role's responsibilities into two strong bullet points.  
            - Prioritize impact: Focus on the most significant contributions and achievements.  
            - Use action verbs: Ensure each bullet starts with a strong action verb.  
            - Maintain structure: Keep the formatting clean and consistent.  
            Output Format for Experience Section:  
            [Job Title] – Company name if there is one, otherwise leave blank it is critical !!DO NOT WRITE THE COMPANY NAME IF THERE IS NOT ONE!! – [Dates]**  


         2. SECTION ORGANIZATION (STRICT ORDER):
           !! Use the same order as the original resume !!
           !! Make sure to write content in the DETECTED LANGUAGE !!
           !! Make sure to add *** for Titles of the sections and ** for smaller titles and * for bold text inside the sections !!
           !! TITLES OF THE SECTIONS MUST BE IN THE DETECTED LANGUAGE IT IS CRITICAL !!
           !! CONTACT INFORMATION MUST BE IN THE DETECTED LANGUAGE IT IS CRITICAL !!

         3. LANGUAGE AND FORMATTING:
            !! Use CONSISTENT language throughout (based on job description Make sure to write in the DETECTED LANGUAGE!!)
            !! Format dates according to language (French: "24 juin 2024", English: "June 24, 2024")
            !! NO duplicate sections or titles
            !! NO scattered projects - keep ALL projects in ONE section
            !! Maintain consistent capitalization and style in section titles

         PART 1: OPTIMIZED RESUME
         =======================
         Create a clean, professional resume with these sections:
         1. Contact Information (keep original details with the detected language) AND make sure to add title after the name AND MAKE TITLE BEFORE CONATACT INFO !!
         2. Professional Summary (concise, impactful)
         3. Technical Skills (prioritize job-relevant skills)
         4. Professional Experience (emphasize relevant achievements)
         5. Education (keep as in original)

         FORMAT RULES:
         - NO headers like "ATS-FRIENDLY" or separator lines
         - Clean, minimal formatting
         - Use bullet points (•) for experience and skills
         - Consistent spacing
         - START WITH THE NAME OF THE CANDIDATE AND THEN ADD THE TITLE AFTER THE NAME in a NEW LINE
         - No tables or columns
         - Directly start with Name of the candidate.
         - Do not INCLUDE PART 2 title in the resume !!
         -!! Make sure to add *** for Titles of the sections and ** for smaller titles and * for bold text inside the sections !!
         I will tell you this for millions times ensure to add for titles *** and for smaller titles ** and for bold text inside the sections * and make sure to write in the detected language it is critical !!!

         PART 2: DETAILED ANALYSIS
         ========================
         Provide a concise analysis in these key areas:

         [SECTION:OPTIMIZATION]
         • Content Improvements
         - How the resume was tailored to the job
         - Key skills and experiences highlighted
         - Quantifiable achievements added

         • Technical Alignment
         - Technologies matched to requirements
         - Technical skills prioritized
         - System/architecture experience highlighted

         • Language Adaptation
         - Industry-specific terms used
         - Action verbs strengthened
         - Technical terminology aligned
         [/SECTION]

         [SECTION:INTERVIEW_PREP]
         • Key Discussion Points
         - Technical projects to highlight
         - System design decisions to explain
         - Problem-solving examples

         • Technical Questions
         - Prepare for architecture discussions
         - Code implementation scenarios
         - Technology stack questions

         • Experience Examples
         - Team collaboration stories
         - Leadership examples
         - Technical challenges overcome
         [/SECTION]

         [SECTION:NEXT_STEPS]
         • Skill Enhancement
         - Areas for improvement
         - Suggested certifications
         - Learning priorities

         • Portfolio Development
         - Project suggestions
         - Skills to demonstrate
         - Technical blog topics
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
                  {"role": "user", "content": prompt}
               ],
               temperature=0.7,
               max_tokens=2000
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

         # Ensure we're using the job description
         if not job_description:
            raise ValueError("Job description is required")

         optimization_prompt = f"""
         Please optimize this resume for the following job description:

         Job Description:
         {job_description}

         Original Resume:
         {resume_text}

         Please optimize this resume and provide improvement suggestions. Format your response in clear sections as follows:
         [Rest of your existing prompt...]
         """

         response = openai.ChatCompletion.create(
               model="gpt-4o-mini",
               messages=[
                  {"role": "system", "content": """You are a professional career advisor that helps optimize resumes and prepare candidates for job opportunities. Your task is to create an ATS-friendly resume that SPECIFICALLY targets this job position.

         CRITICAL - ABSOLUTELY REQUIRED RULES:
         1. JOB MATCHING (HIGHEST PRIORITY):
            !! Write ALL content in the DETECTED LANGUAGE from Job description
            !! Analyze the job description thoroughly
            !! Identify key requirements, skills, and qualifications
            !! Reorganize and emphasize resume content to match job requirements
            !! Use similar terminology as the job description
            !! Highlight experiences that directly relate to job requirements
            !! PLEASE DO NOT FORGET TO ADD THE CANDIDATE TITLE AFTER THE NAME eg Software Engineer, Product Manager, etc !! 
            !! Ensure technical skills match what's asked in the job
            - **Summarize concisely**: Reduce each role's responsibilities into two strong bullet points.  
            - **Prioritize impact**: Focus on the most significant contributions and achievements.  
            - **Use action verbs**: Ensure each bullet starts with a strong action verb.  
            - **Maintain structure**: Keep the formatting clean and consistent.  
            **Output Format for Experience Section:**  
            **[Job Title] – Company name if there is one, otherwise leave blank it is critical !!DO NOT WRITE THE COMPANY NAME IF THERE IS NOT ONE!! – [Dates]**  


         2. SECTION ORGANIZATION (STRICT ORDER):
           !! Use the same order as the original resume !!
           !! Make sure to write content in the DETECTED LANGUAGE !!
           !! Make sure to add *** for Titles of the sections and ** for smaller titles and * for bold text inside the sections !!
           !! TITLES OF THE SECTIONS MUST BE IN THE DETECTED LANGUAGE IT IS CRITICAL !!
           !! CONTACT INFORMATION MUST BE IN THE DETECTED LANGUAGE IT IS CRITICAL !!

         3. LANGUAGE AND FORMATTING:
            !! Use CONSISTENT language throughout (based on job description Make sure to write in the DETECTED LANGUAGE!!)
            !! Format dates according to language (French: "24 juin 2024", English: "June 24, 2024")
            !! NO duplicate sections or titles
            !! NO scattered projects - keep ALL projects in ONE section
            !! Maintain consistent capitalization and style in section titles

         PART 1: OPTIMIZED RESUME
         =======================
         Create a clean, professional resume with these sections:
         1. Contact Information (keep original details with the detected language) AND make sure to add title after the name AND MAKE TITLE BEFORE CONATACT INFO !!
         2. Professional Summary (concise, impactful)
         3. Technical Skills (prioritize job-relevant skills)
         4. Professional Experience (emphasize relevant achievements)
         5. Education (keep as in original)

         FORMAT RULES:
         - NO headers like "ATS-FRIENDLY" or separator lines
         - Clean, minimal formatting
         - Use bullet points (•) for experience and skills
         - Consistent spacing
         - START WITH THE NAME OF THE CANDIDATE AND THEN ADD THE TITLE AFTER THE NAME in a NEW LINE
         - No tables or columns
         - Directly start with Name of the candidate.
         - Do not INCLUDE PART 2 title in the resume !!
         -!! Make sure to add *** for Titles of the sections and ** for smaller titles and * for bold text inside the sections !!
         I will tell you this for millions times ensure to add for titles *** and for smaller titles ** and for bold text inside the sections * and make sure to write in the detected language it is critical !!!

         PART 2: DETAILED ANALYSIS
         ========================
         Provide a concise analysis in these key areas:

         [SECTION:OPTIMIZATION]
         • Content Improvements
         - How the resume was tailored to the job
         - Key skills and experiences highlighted
         - Quantifiable achievements added

         • Technical Alignment
         - Technologies matched to requirements
         - Technical skills prioritized
         - System/architecture experience highlighted

         • Language Adaptation
         - Industry-specific terms used
         - Action verbs strengthened
         - Technical terminology aligned
         [/SECTION]

         [SECTION:INTERVIEW_PREP]
         • Key Discussion Points
         - Technical projects to highlight
         - System design decisions to explain
         - Problem-solving examples

         • Technical Questions
         - Prepare for architecture discussions
         - Code implementation scenarios
         - Technology stack questions

         • Experience Examples
         - Team collaboration stories
         - Leadership examples
         - Technical challenges overcome
         [/SECTION]

         [SECTION:NEXT_STEPS]
         • Skill Enhancement
         - Areas for improvement
         - Suggested certifications
         - Learning priorities

         • Portfolio Development
         - Project suggestions
         - Skills to demonstrate
         - Technical blog topics
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
            Please write the cover letter in the detected language of the job description.
            Job Description:
            {job_description}

            Resume:
            {resume_text}

            REQUIRED FORMAT:
            - Begin with: "Dear Hiring Manager," or Use the detected language for the greeting
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
            - Write the cover letter in the detected language of the job description
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
