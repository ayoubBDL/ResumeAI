import os
import openai
from typing import Dict

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
