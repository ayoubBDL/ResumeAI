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

class PDFGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        # Heading style
        self.styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=self.styles['Heading1'],
            fontSize=14,
            spaceAfter=20,
            textColor=colors.HexColor('#2D3748')
        ))

        # Section style
        self.styles.add(ParagraphStyle(
            name='Section',
            parent=self.styles['Heading2'],
            fontSize=12,
            spaceAfter=12,
            textColor=colors.HexColor('#4A5568')
        ))

        # Body text style
        self.styles.add(ParagraphStyle(
            name='CustomBody',
            parent=self.styles['Normal'],
            fontSize=10,
            leading=14,
            spaceAfter=8,
            textColor=colors.HexColor('#2D3748')
        ))

    def create_pdf_from_text(self, text):
        """Convert text to PDF using ReportLab with enhanced formatting"""
        try:
            # Create a BytesIO buffer instead of a temporary file
            buffer = io.BytesIO()
            
            # Set up the document with proper margins
            doc = SimpleDocTemplate(
                buffer,
                pagesize=letter,
                leftMargin=0.75*inch,
                rightMargin=0.75*inch,
                topMargin=0.75*inch,
                bottomMargin=0.75*inch
            )
            
            # Create custom styles
            styles = getSampleStyleSheet()
            
            # Name style
            styles.add(ParagraphStyle(
                name='Name',
                parent=styles['Heading1'],
                fontSize=18,
                spaceAfter=12,
                textColor=colors.HexColor('#2C3E50'),
                fontName='Helvetica-Bold'
            ))
            
            # Section heading style
            styles.add(ParagraphStyle(
                name='SectionHeading',
                parent=styles['Heading2'],
                fontSize=14,
                spaceBefore=12,
                spaceAfter=8,
                textColor=colors.HexColor('#2C3E50'),
                fontName='Helvetica-Bold'
            ))
            
            # Normal text style
            styles.add(ParagraphStyle(
                name='NormalText',
                parent=styles['Normal'],
                fontSize=11,
                spaceAfter=6,
                fontName='Helvetica',
                leading=14
            ))
            
            # Contact info style
            styles.add(ParagraphStyle(
                name='ContactInfo',
                parent=styles['Normal'],
                fontSize=11,
                spaceAfter=2,
                fontName='Helvetica',
                textColor=colors.HexColor('#34495E')
            ))
            
            # Parse the text and build the document
            story = []
            lines = text.split('\n')
            current_section = []
            in_contact_section = False
            skip_next = False
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Skip ATS header and separator lines
                if "ATS-FRIENDLY" in line or "=" * 10 in line:
                    continue
                
                # Remove markers and clean up the text
                line = re.sub(r'^PART \d+:', '', line)  # Remove "PART X:" headers
                line = re.sub(r'\*\*|\#\#', '', line)   # Remove ** and ## markers
                line = line.strip()
                if not line:
                    continue
                
                # Handle different sections
                if "PROFESSIONAL SUMMARY" in line.upper():
                    story.append(Paragraph("Summary", styles['SectionHeading']))
                elif "PROFESSIONAL EXPERIENCE" in line.upper():
                    story.append(Paragraph("Experience", styles['SectionHeading']))
                elif "EDUCATION" in line.upper():
                    story.append(Paragraph("Education", styles['SectionHeading']))
                elif "SKILLS" in line.upper():
                    story.append(Paragraph("Skills", styles['SectionHeading']))
                elif "CONTACT SECTION" in line.upper():
                    continue  # Skip this header
                elif line.startswith('[LinkedIn]'):
                    # Clean up LinkedIn URL
                    url = re.search(r'\((.*?)\)', line).group(1)
                    story.append(Paragraph(f'LinkedIn: {url}', styles['ContactInfo']))
                elif ':' in line and not in_contact_section:
                    # Handle contact info
                    label, value = line.split(':', 1)
                    story.append(Paragraph(
                        f'{label.strip()}: {value.strip()}',
                        styles['ContactInfo']
                    ))
                elif line.startswith('•') or line.startswith('-'):
                    # Add bullet point
                    current_section.append(line[1:].strip())
                else:
                    # Add normal paragraph
                    if current_section:
                        # Add any collected bullet points before adding new paragraph
                        story.append(ListFlowable(
                            [ListItem(Paragraph(item, styles['NormalText'])) for item in current_section],
                            bulletType='bullet',
                            leftIndent=20,
                            spaceBefore=4,
                            spaceAfter=4
                        ))
                        current_section = []
                    
                    # Check if this is the name (first non-header line)
                    if not story:
                        story.append(Paragraph(line, styles['Name']))
                    else:
                        story.append(Paragraph(line, styles['NormalText']))
            
            # Add any remaining bullet points
            if current_section:
                story.append(ListFlowable(
                    [ListItem(Paragraph(item, styles['NormalText'])) for item in current_section],
                    bulletType='bullet',
                    leftIndent=20,
                    spaceBefore=4,
                    spaceAfter=4
                ))
            
            # Build PDF into the buffer
            doc.build(story)
            
            # Get the PDF bytes
            pdf_bytes = buffer.getvalue()
            buffer.close()
            
            return pdf_bytes
            
        except Exception as e:
            print(f"Error creating PDF: {str(e)}")
            raise

    def clean_text(self, text):
        """Clean extracted text by removing extra spaces and formatting"""
        # Split into lines and clean each line
        lines = text.splitlines()
        cleaned_lines = []
        
        for line in lines:
            # Remove multiple spaces and tabs
            cleaned_line = ' '.join(word for word in line.split() if word)
            if cleaned_line:
                cleaned_lines.append(cleaned_line)
        
        # Join lines back together
        return '\n'.join(cleaned_lines)
        
    def extract_text_from_pdf(self, file_storage):
        try:
            print(f"[PDF Extraction] Starting PDF text extraction for file: {file_storage.filename}")
            
            # Read the file into a bytes buffer
            pdf_bytes = io.BytesIO(file_storage.read())
            print("[PDF Extraction] Successfully read file into buffer")
            
            text_content = []
            # Use pdfplumber for better text extraction
            with pdfplumber.open(pdf_bytes) as pdf:
                num_pages = len(pdf.pages)
                print(f"[PDF Extraction] PDF has {num_pages} pages")
                
                for i, page in enumerate(pdf.pages):
                    # Extract text with better formatting
                    page_text = page.extract_text(layout=True)
                    if page_text:
                        # Clean the text before adding to content
                        cleaned_text = self.clean_text(page_text)
                        text_content.append(cleaned_text)
                    print(f"[PDF Extraction] Extracted {len(page_text) if page_text else 0} characters from page {i+1}")
            
            # Join all pages with proper spacing
            final_text = "\n\n".join(text_content).strip()
            
            print(f"[PDF Extraction] Total extracted text length: {len(final_text)} characters")
            print("[PDF Extraction] Complete extracted text:")
            print("=" * 80)
            
            return final_text
            
        except Exception as e:
            print(f"[PDF Extraction ERROR] Error extracting text from PDF: {str(e)}")
            raise Exception("Failed to extract text from PDF file")


    async def generate(self, content: dict) -> str:
        try:
            # Create output directory if it doesn't exist
            output_dir = "downloads"
            os.makedirs(output_dir, exist_ok=True)

            # Generate unique filename
            filename = f"resume_{uuid.uuid4().hex[:8]}.pdf"
            filepath = os.path.join(output_dir, filename)

            # Create the PDF document
            doc = SimpleDocTemplate(
                filepath,
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72
            )

            # Build the PDF content
            story = []

            # Add the optimized resume content
            resume_lines = content["optimized_resume"].split('\n')
            current_section = None

            for line in resume_lines:
                line = line.strip()
                if not line:
                    continue

                # Check if this is a section header
                if line.isupper() and len(line) < 50:
                    current_section = line
                    story.append(Paragraph(line, self.styles['CustomHeading']))
                    story.append(Spacer(1, 12))
                else:
                    # Regular content
                    story.append(Paragraph(line, self.styles['CustomBody']))
                    story.append(Spacer(1, 8))

            # Build the PDF
            doc.build(story)

            return filepath

        except Exception as e:
            raise Exception(f"Failed to generate PDF: {str(e)}")
