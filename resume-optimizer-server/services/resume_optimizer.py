import requests
from .openai_optimizer import OpenAIOptimizer
import os

class ResumeOptimizer:
    def __init__(self):
        self.model_name = os.getenv("LLAMA_MODEL_NAME", "llama3.1")
        self.api_base = "http://localhost:11434/api/generate"
        self.openai_optimizer = OpenAIOptimizer()

    async def optimize(self, resume_text: str, job_description: str, 
                      job_title: str, company: str, 
                      custom_instructions: str = None,
                      use_openai: bool = False) -> dict:
        try:
            if use_openai:
                return await self.openai_optimizer.optimize(
                    resume_text,
                    job_description,
                    job_title,
                    company,
                    custom_instructions
                )

            # Use Ollama by default
            prompt = self._construct_prompt(
                resume_text, 
                job_description, 
                job_title, 
                company, 
                custom_instructions
            )

            # Generate optimized resume using Ollama
            response = requests.post(
                self.api_base,
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False
                }
            )
            
            if response.status_code != 200:
                raise Exception(f"Ollama API error: {response.text}")

            # Parse the response
            result = response.json()
            optimized_content = self._parse_response(result["response"])

            return optimized_content

        except Exception as e:
            # If Ollama fails and OpenAI is configured, try OpenAI as fallback
            if not use_openai and self.openai_optimizer.api_key:
                try:
                    return await self.openai_optimizer.optimize(
                        resume_text,
                        job_description,
                        job_title,
                        company,
                        custom_instructions
                    )
                except:
                    pass
            raise Exception(f"Failed to optimize resume: {str(e)}")

    def _construct_prompt(self, resume_text: str, job_description: str, 
                         job_title: str, company: str, 
                         custom_instructions: str = None) -> str:
        prompt = f"""
        You are an expert resume optimizer with years of experience in HR and recruitment.
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

        ###
        """
        return prompt

    def _parse_response(self, response: str) -> dict:
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
