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
        Your task is to optimize the following resume for the position of {job_title} at {company}.

        Job Description:
        {job_description}

        Original Resume:
        {resume_text}

        {f'Additional Instructions: {custom_instructions}' if custom_instructions else ''}

        Please optimize the resume following these guidelines:
        1. Match keywords and skills from the job description
        2. Quantify achievements where possible
        3. Use action verbs
        4. Maintain ATS-friendly formatting
        5. Highlight relevant experience
        6. Remove irrelevant information
        7. Ensure proper ordering of information
        8. Add any missing relevant skills from the job description

        Provide your response in the following format:
        SUMMARY:
        [Brief summary of changes made]

        OPTIMIZED_RESUME:
        [The complete optimized resume text]

        CHANGES_MADE:
        [Bullet points of significant changes]
        """
        return prompt

    def _parse_response(self, response: str) -> Dict:
        sections = response.split('\n\n')
        result = {
            "summary": "",
            "optimized_resume": "",
            "changes": []
        }

        current_section = None
        for section in sections:
            if section.startswith('SUMMARY:'):
                current_section = "summary"
                result["summary"] = section.replace('SUMMARY:', '').strip()
            elif section.startswith('OPTIMIZED_RESUME:'):
                current_section = "optimized_resume"
                result["optimized_resume"] = section.replace('OPTIMIZED_RESUME:', '').strip()
            elif section.startswith('CHANGES_MADE:'):
                current_section = "changes"
                changes = section.replace('CHANGES_MADE:', '').strip().split('\n')
                result["changes"] = [change.strip('- ') for change in changes if change.strip()]
            elif current_section:
                if current_section == "changes":
                    result["changes"].extend([change.strip('- ') for change in section.split('\n') if change.strip()])
                else:
                    result[current_section] += '\n' + section.strip()

        return result
