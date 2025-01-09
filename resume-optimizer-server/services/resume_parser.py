from PyPDF2 import PdfReader
import io

class ResumeParser:
    async def parse(self, file) -> str:
        try:
            print(f"Starting to parse file: {file.filename}")
            # Read the uploaded file
            content = await file.read()
            print(f"File content read, size: {len(content)} bytes")
            
            if file.filename.endswith('.pdf'):
                print("Detected PDF file, parsing...")
                return await self._parse_pdf(content)
            elif file.filename.endswith(('.doc', '.docx')):
                # For future implementation
                raise NotImplementedError("DOC/DOCX parsing not yet implemented")
            elif file.filename.endswith('.txt'):
                return content.decode('utf-8')
            else:
                raise ValueError(f"Unsupported file format: {file.filename}")

        except Exception as e:
            print(f"Error in parse method: {str(e)}")
            raise Exception(f"Failed to parse resume: {str(e)}")

    async def _parse_pdf(self, content: bytes) -> str:
        try:
            # Create a PDF reader object
            print("Creating PDF reader...")
            pdf = PdfReader(io.BytesIO(content))
            
            # Extract text from all pages
            text = ""
            print(f"PDF has {len(pdf.pages)} pages")
            for i, page in enumerate(pdf.pages):
                print(f"Extracting text from page {i+1}")
                text += page.extract_text() + "\n"
            
            print(f"Successfully extracted {len(text)} characters")
            return text.strip()

        except Exception as e:
            print(f"Error in _parse_pdf method: {str(e)}")
            raise Exception(f"Failed to parse PDF: {str(e)}")
