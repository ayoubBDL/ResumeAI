from loguru import logger
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem
from reportlab.lib.units import inch
import os
import pdfplumber
import uuid
import io
import re
from datetime import datetime

class PDFGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Set up all custom styles for the PDF"""
        # Define colors
        self.colors = {
            'primary': colors.HexColor('#2C3E50'),
            'secondary': colors.HexColor('#34495E'),
            'text': colors.HexColor('#2D3748')
        }

        # Remove existing styles if they exist
        style_names = ['Name', 'JobTitle', 'ContactInfo', 'SectionHeading', 'NormalText', 
                      'BulletText', 'CompanyName', 'BoldText']
        for style_name in style_names:
            if style_name in self.styles:
                del self.styles[style_name]

        # Name style - centered
        self.styles.add(ParagraphStyle(
            name='Name',
            parent=self.styles['Heading1'],
            fontSize=20,
            spaceAfter=12,
            textColor=self.colors['primary'],
            fontName='Helvetica-Bold',
            alignment=1  # Center alignment
        ))

        # Job Title style
        self.styles.add(ParagraphStyle(
            name='JobTitle',
            parent=self.styles['Normal'],
            fontSize=12,
            spaceAfter=10,
            textColor=self.colors['secondary'],
            fontName='Helvetica-Bold',
            alignment=1
        ))

        # Contact info style
        self.styles.add(ParagraphStyle(
            name='ContactInfo',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=3,
            fontName='Helvetica',
            textColor=self.colors['secondary'],
            alignment=1
        ))

        # Section Heading style (for ***TITLE***)
        self.styles.add(ParagraphStyle(
            name='SectionHeading',
            parent=self.styles['Heading2'],
            fontSize=12,
            spaceBefore=12,
            spaceAfter=4,
            textColor=self.colors['primary'],
            fontName='Helvetica-Bold'
        ))

        # Sub Heading style (for **Title**)
        self.styles.add(ParagraphStyle(
            name='SubHeading',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceBefore=6,
            spaceAfter=4,
            textColor=self.colors['secondary'],
            fontName='Helvetica-Bold'
        ))

        # Bold Text style (for *text*)
        self.styles.add(ParagraphStyle(
            name='BoldText',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=4,
            fontName='Helvetica-Bold',
            textColor=self.colors['text']
        ))

        # Normal text style
        self.styles.add(ParagraphStyle(
            name='NormalText',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=4,
            fontName='Helvetica'
        ))

        # Bullet point style
        self.styles.add(ParagraphStyle(
            name='BulletText',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=2,
            fontName='Helvetica',
            leading=12,
            leftIndent=20
        ))

    def _is_section_header(self, line, previous_line="", next_line=""):
        """
        Determine if a line is a section header based on its characteristics and context.
        """
        line = line.strip()
        if not line:
            return False
            
        # Skip obvious non-headers
        if line.startswith('•') or line.startswith('-') or ':' in line:
            return False
        
        # Check length (most section headers are 1-4 words)
        words = line.split()
        if len(words) > 4:
            return False
            
        # Check formatting characteristics
        is_all_caps = line.isupper()
        is_title_case = line.istitle()
        
        # Check context
        next_line = next_line.strip()
        previous_line = previous_line.strip()
        
        # Headers often have different formatting than surrounding text
        followed_by_bullet = next_line.startswith('•') or next_line.startswith('-')
        preceded_by_space = not previous_line
        
        # Scoring system for header likelihood
        score = 0
        if is_all_caps:
            score += 2
        if is_title_case:
            score += 1
        if followed_by_bullet:
            score += 2
        if preceded_by_space:
            score += 1
        if len(words) <= 2:
            score += 1
            
        return score >= 3

    def _process_bold_text(self, text):
        """Process bold text markers in the content"""
        # Handle **text** format
        text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
        # Handle __text__ format
        text = re.sub(r'__(.*?)__', r'<b>\1</b>', text)
        return text

    def _process_text_formatting(self, line: str) -> tuple[str, str]:
        """Process text formatting and return the processed text and appropriate style name"""
        
        line = line.strip()
        
        # Handle section titles (***TITLE***)
        if line.startswith('***') and line.endswith('***'):
            title = line[3:-3].strip()  # Remove *** from both ends
            return title, 'SectionHeading'
        
        # Handle sub-titles (**Title**)
        if line.startswith('**') and line.endswith('**'):
            subtitle = line[2:-2].strip()  # Remove ** from both ends
            return subtitle, 'SubHeading'
        
        # Handle bold text (*text*)
        if '*' in line:
            # Find all text between * and replace with just the text
            line = re.sub(r'\*(.*?)\*', r'\1', line)
            return line, 'BoldText'
        
        return line, 'NormalText'

    def create_pdf_from_text(self, text: str) -> bytes:
        """Create a PDF from resume text"""
        try:
            buffer = io.BytesIO()
            
            doc = SimpleDocTemplate(
                buffer,
                pagesize=letter,
                leftMargin=0.75*inch,
                rightMargin=0.75*inch,
                topMargin=0.75*inch,
                bottomMargin=0.75*inch
            )
            
            # Use simple styling like cover letter
            styles = getSampleStyleSheet()
            normal_style = ParagraphStyle(
                'ResumeBody',
                parent=styles['Normal'],
                fontSize=12,
                fontName='Helvetica',
                leading=16,
                spaceBefore=12,
                spaceAfter=12
            )
            
            header_style = ParagraphStyle(
                'ResumeHeader',
                parent=styles['Normal'],
                fontSize=14,
                fontName='Helvetica-Bold',
                leading=16,
                spaceBefore=12,
                spaceAfter=12
            )
            
            story = []
            lines = text.split('\n')
            is_first_line = True
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # Skip separator lines
                if line.startswith('---') or line.startswith('==='):
                    continue
                    
                # Use header style for first line and section headers
                if is_first_line or line.isupper():
                    story.append(Paragraph(line, header_style))
                    is_first_line = False
                else:
                    story.append(Paragraph(line, normal_style))
            
            doc.build(story)
            pdf_data = buffer.getvalue()
            buffer.close()
            
            return pdf_data
            
        except Exception as e:
            print(f"Error creating resume PDF: {str(e)}")
            raise       
    def clean_text(self, text):
        """Clean extracted text by removing extra spaces and formatting"""
        lines = text.splitlines()
        cleaned_lines = []
        
        for line in lines:
            cleaned_line = ' '.join(word for word in line.split() if word)
            if cleaned_line:
                cleaned_lines.append(cleaned_line)
        
        return '\n'.join(cleaned_lines)

    def extract_text_from_pdf(self, file_storage):
        """Extract text from uploaded PDF file"""
        try:
            print(f"[PDF Extraction] Starting PDF text extraction for file: {file_storage.filename}")
            
            pdf_bytes = io.BytesIO(file_storage.read())
            print("[PDF Extraction] Successfully read file into buffer")
            
            text_content = []
            with pdfplumber.open(pdf_bytes) as pdf:
                num_pages = len(pdf.pages)
                print(f"[PDF Extraction] PDF has {num_pages} pages")
                
                for i, page in enumerate(pdf.pages):
                    page_text = page.extract_text(layout=True)
                    if page_text:
                        cleaned_text = self.clean_text(page_text)
                        text_content.append(cleaned_text)
                    print(f"[PDF Extraction] Extracted {len(page_text) if page_text else 0} characters from page {i+1}")
            
            final_text = "\n\n".join(text_content).strip()
            print(f"[PDF Extraction] Total extracted text length: {len(final_text)} characters")
            
            return final_text
            
        except Exception as e:
            print(f"[PDF Extraction ERROR] Error extracting text from PDF: {str(e)}")
            raise Exception("Failed to extract text from PDF file")

    async def generate(self, content: dict) -> str:
        """Generate a PDF file from the optimized resume content"""
        try:
            output_dir = "downloads"
            os.makedirs(output_dir, exist_ok=True)

            filename = f"resume_{uuid.uuid4().hex[:8]}.pdf"
            filepath = os.path.join(output_dir, filename)

            doc = SimpleDocTemplate(
                filepath,
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72
            )

            story = []
            resume_lines = content["optimized_resume"].split('\n')

            for line in resume_lines:
                line = line.strip()
                if not line:
                    continue

                if line.isupper() and len(line) < 50:
                    story.append(Paragraph(line, self.styles['SectionHeading']))
                    story.append(Spacer(1, 12))
                else:
                    story.append(Paragraph(line, self.styles['NormalText']))
                    story.append(Spacer(1, 8))

            doc.build(story)
            return filepath

        except Exception as e:
            raise Exception(f"Failed to generate PDF: {str(e)}")

    def create_cover_letter_pdf(self, text: str) -> bytes:
        """Create a PDF from cover letter text"""
        try:
            buffer = io.BytesIO()
            
            doc = SimpleDocTemplate(
                buffer,
                pagesize=letter,
                leftMargin=1*inch,
                rightMargin=1*inch,
                topMargin=1*inch,
                bottomMargin=1*inch
            )
            
            styles = getSampleStyleSheet()
            normal_style = ParagraphStyle(
                'CoverLetterBody',
                parent=styles['Normal'],
                fontSize=12,
                fontName='Helvetica',
                leading=16,
                spaceBefore=12,
                spaceAfter=12
            )
            
            story = []
            paragraphs = text.strip().split('\n\n')
            for paragraph in paragraphs:
                if paragraph.strip():
                    cleaned_paragraph = paragraph.replace('\n', ' ').strip()
                    story.append(Paragraph(cleaned_paragraph, normal_style))
            
            doc.build(story)
            pdf_data = buffer.getvalue()
            buffer.close()
            
            return pdf_data
            
        except Exception as e:
            print(f"Error creating cover letter PDF: {str(e)}")
            raise