from PyPDF2 import PdfReader
import io

class ResumeParser:
    async def parse(self, file) -> str:
        try:
            # Read the uploaded file
            content = await file.read()
            
            if file.filename.endswith('.pdf'):
                return await self._parse_pdf(content)
            elif file.filename.endswith(('.doc', '.docx')):
                # For future implementation
                raise NotImplementedError("DOC/DOCX parsing not yet implemented")
            elif file.filename.endswith('.txt'):
                return content.decode('utf-8')
            else:
                raise ValueError("Unsupported file format")

        except Exception as e:
            raise Exception(f"Failed to parse resume: {str(e)}")

    async def _parse_pdf(self, content: bytes) -> str:
        try:
            # Create a PDF reader object
            pdf = PdfReader(io.BytesIO(content))
            
            # Extract text from all pages
            text = ""
            for page in pdf.pages:
                text += page.extract_text() + "\n"
            
            return text.strip()

        except Exception as e:
            raise Exception(f"Failed to parse PDF: {str(e)}")
