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
import logging
import PyPDF2
from fastapi import UploadFile

class PDFGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Set up all custom styles for the PDF"""
        # Define modern color scheme
        self.colors = {
            'primary': colors.HexColor('#1a365d'),    # Deep blue
            'secondary': colors.HexColor('#1b3857'),  # Medium blue
            'accent': colors.HexColor('#4299e1'),     # Light blue
            'text': colors.HexColor('#2d3748'),       # Dark gray
            'subtext': colors.HexColor('#718096')     # Medium gray
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

    def create_pdf_from_text(self, text):
        buffer = io.BytesIO()
        try:
            # Log the input text length for debugging
            logger.info(f"Creating PDF from text of length: {len(text)}")
            
            doc = SimpleDocTemplate(
                buffer,
                pagesize=letter,
                leftMargin=0.75*inch,
                rightMargin=0.75*inch,
                topMargin=0.75*inch,
                bottomMargin=0.75*inch
            )
            
            story = []
            lines = text.split('\n')
            is_first_content = True
            
            # Log number of lines being processed
            logger.info(f"Processing {len(lines)} lines")
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Skip separator lines and age
                if (line.startswith('---') or 
                    line.startswith('===') or 
                    line == '---' or 
                    re.match(r'^\d+\s*yo\s*$', line, re.IGNORECASE)):
                    continue
                    
                # Process the line formatting
                processed_text, style_name = self._process_text_formatting(line)
                
                # Handle first line (name) specially
                if is_first_content:
                    story.append(Paragraph(processed_text, self.styles['Name']))
                    is_first_content = False
                    continue
                
                # Add the processed text with appropriate style
                story.append(Paragraph(processed_text, self.styles[style_name]))
                
                # Add extra space after sections
                if style_name == 'SectionHeading':
                    story.append(Spacer(1, 8))
            
            # Log before building the PDF
            logger.info(f"Building PDF with {len(story)} elements")
            
            doc.build(story)
            
            # Get the PDF data
            pdf_data = buffer.getvalue()
            
            # Validate PDF data
            if not pdf_data.startswith(b'%PDF-'):
                raise ValueError("Generated data is not a valid PDF")
                
            # Log PDF size
            logger.info(f"Successfully generated PDF of size: {len(pdf_data)} bytes")
            
            return pdf_data
            
        except Exception as e:
            logger.error(f"Error creating PDF: {str(e)}", exc_info=True)
            raise
        finally:
            # Always close the buffer
            buffer.close()
            
    def clean_text(self, text):
        """Clean extracted text by removing extra spaces and formatting"""
        lines = text.splitlines()
        cleaned_lines = []
        
        for line in lines:
            cleaned_line = ' '.join(word for word in line.split() if word)
            if cleaned_line:
                cleaned_lines.append(cleaned_line)
        
        return '\n'.join(cleaned_lines)

    async def extract_text_from_pdf(self, file_storage: UploadFile) -> str:
        try:
            pdf_bytes = io.BytesIO(await file_storage.read())
            pdf_reader = PyPDF2.PdfReader(pdf_bytes)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
            return text
        except Exception as e:
            logging.error(f"PDF extraction error: {str(e)}")
            raise ValueError(f"Failed to extract text from PDF: {str(e)}")

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
            raise ValueError("Failed to create cover letter PDF")