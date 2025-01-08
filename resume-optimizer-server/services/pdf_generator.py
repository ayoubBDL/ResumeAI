from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch
import os
import uuid

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
