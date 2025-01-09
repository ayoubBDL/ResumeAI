import requests
from .openai_optimizer import OpenAIOptimizer
import os
import aiohttp
import asyncio

class ResumeOptimizer:
    def __init__(self):
        self.model_name = os.getenv("LLAMA_MODEL_NAME", "llama3.1")  # Restored original model name
        self.api_base = "http://localhost:11434/api/generate"
        self.openai_optimizer = OpenAIOptimizer()

    async def check_ollama(self) -> bool:
        """Check if Ollama is running and the model is available"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:11434/api/tags") as response:
                    if response.status != 200:
                        return False
                    data = await response.json()
                    models = [model.get("name") for model in data.get("models", [])]
                    return self.model_name in models
        except:
            return False

    async def optimize(self, resume_text: str, job_description: str, 
                      job_title: str, company: str, 
                      custom_instructions: str = None,
                      use_openai: bool = False) -> dict:
        print(f"Starting resume optimization for {job_title} position at {company}")
        
        try:
            if use_openai:
                print("Using OpenAI for optimization")
                return await self.openai_optimizer.optimize(
                    resume_text,
                    job_description,
                    job_title,
                    company,
                    custom_instructions
                )

            # Check if Ollama is available
            print("Checking Ollama availability...")
            if not await self.check_ollama():
                raise Exception(
                    "Ollama is not running or the model is not available. "
                    "Please make sure Ollama is running and the model is installed. "
                    "Run 'ollama run llama2' in your terminal."
                )

            print("Constructing optimization prompt...")
            prompt = self._construct_prompt(
                resume_text, 
                job_description, 
                job_title, 
                company, 
                custom_instructions
            )

            print("Sending request to Ollama...")
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.api_base,
                    json={
                        "model": self.model_name,
                        "prompt": prompt,
                        "stream": False
                    }
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"Ollama API error (status {response.status}): {error_text}")
                    
                    result = await response.json()
                    if not result.get("response"):
                        raise Exception("Empty response from Ollama")
                    
                    print("Parsing optimization response...")
                    optimized_content = self._parse_response(result["response"])
                    print("Resume optimization completed successfully")
                    return optimized_content

        except Exception as e:
            print(f"Error during optimization: {str(e)}")
            # If Ollama fails and OpenAI is configured, try OpenAI as fallback
            if not use_openai and self.openai_optimizer.api_key:
                print("Attempting fallback to OpenAI...")
                try:
                    return await self.openai_optimizer.optimize(
                        resume_text,
                        job_description,
                        job_title,
                        company,
                        custom_instructions
                    )
                except Exception as openai_error:
                    print(f"OpenAI fallback failed: {str(openai_error)}")
                    raise Exception(f"Both Ollama and OpenAI optimization failed. Original error: {str(e)}")
            raise Exception(f"Resume optimization failed: {str(e)}")

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
        """
        return prompt.strip()

    def _parse_response(self, response: str) -> dict:
        try:
            # Split the response into sections
            sections = response.split('\n\n')
            result = {}
            
            current_section = None
            current_content = []
            
            for section in sections:
                if section.startswith('SUMMARY:'):
                    current_section = 'summary'
                    current_content = [section.replace('SUMMARY:', '').strip()]
                elif section.startswith('OPTIMIZED_RESUME:'):
                    if current_section:
                        result[current_section] = '\n'.join(current_content)
                    current_section = 'optimized_resume'
                    current_content = [section.replace('OPTIMIZED_RESUME:', '').strip()]
                elif section.startswith('CHANGES_MADE:'):
                    if current_section:
                        result[current_section] = '\n'.join(current_content)
                    current_section = 'changes'
                    current_content = [section.replace('CHANGES_MADE:', '').strip()]
                elif current_section:
                    current_content.append(section.strip())
            
            if current_section:
                result[current_section] = '\n'.join(current_content)
            
            # Validate the response
            required_sections = ['summary', 'optimized_resume', 'changes']
            missing_sections = [s for s in required_sections if s not in result]
            if missing_sections:
                raise Exception(f"Missing sections in response: {', '.join(missing_sections)}")
            
            return result
            
        except Exception as e:
            raise Exception(f"Failed to parse optimization response: {str(e)}")
