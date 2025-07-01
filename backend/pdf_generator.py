from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from io import BytesIO
import json
from models import SummaryResponse, OutlineItem, Chunk, KeyPoint, QuizQuestion
from typing import List
from reportlab.lib.colors import HexColor
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

class StudyPackPDFGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        )
        
        self.heading_style = ParagraphStyle(
            'Heading1', fontName='Helvetica-Bold', fontSize=18, leading=24, alignment=TA_CENTER, textColor=HexColor('#6D28D9'), spaceAfter=16, spaceBefore=16
        )
        
        self.subheading_style = ParagraphStyle(
            'Heading2', fontName='Helvetica-Bold', fontSize=14, leading=20, alignment=TA_LEFT, textColor=HexColor('#7C3AED'), spaceAfter=10, spaceBefore=10
        )
        
        self.body_style = ParagraphStyle(
            'Body', fontName='Helvetica', fontSize=11, leading=16, alignment=TA_LEFT, textColor=HexColor('#22223B'), spaceAfter=8
        )
        
        self.key_point_style = ParagraphStyle(
            'KeyPoint', fontName='Helvetica-Oblique', fontSize=11, leading=16, alignment=TA_LEFT, textColor=HexColor('#059669'), leftIndent=16, bulletIndent=8, spaceAfter=6
        )
        
        self.quiz_style = ParagraphStyle(
            'Quiz', fontName='Helvetica', fontSize=11, leading=16, alignment=TA_LEFT, textColor=HexColor('#B91C1C'), leftIndent=16, bulletIndent=8, spaceAfter=6
        )
        
        self.equation_style = ParagraphStyle(
            'Equation', fontName='Courier', fontSize=11, leading=16, alignment=TA_LEFT, textColor=HexColor('#1E293B'), backColor=HexColor('#F1F5F9'), leftIndent=16, spaceAfter=8, spaceBefore=8
        )
        
        self.section_bg_color = HexColor('#F3F0FF')
        self.page_size = letter
        self.margin = 0.75 * inch
    
    def clean_equation(self, text: str) -> str:
        # Collapse multiple spaces, join lines with only math symbols/variables
        import re
        # Remove excessive spaces
        text = re.sub(r' {2,}', ' ', text)
        # Join lines that look like equations (heuristic: lots of =, +, -, *, /, ^, or digits)
        lines = text.split('\n')
        new_lines = []
        buffer = ''
        for line in lines:
            if re.match(r'^[\s\d=+\-*/^().,A-Za-z]+$', line) and len(line.strip()) > 0:
                buffer += line.strip() + ' '
            else:
                if buffer:
                    new_lines.append(buffer.strip())
                    buffer = ''
                new_lines.append(line)
        if buffer:
            new_lines.append(buffer.strip())
        return '\n'.join(new_lines)

    def generate_pdf(self, summary: SummaryResponse, filename: str) -> BytesIO:
        """Generate a PDF study pack from the summary data"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=self.page_size, leftMargin=self.margin, rightMargin=self.margin, topMargin=self.margin, bottomMargin=self.margin)
        story = []
        
        # Title page
        story.append(Paragraph(f"<b>{filename.replace('.pdf', '')} - Study Pack</b>", self.heading_style))
        story.append(Spacer(1, 12))
        story.append(Paragraph(f"Time Limit: {summary.total_reading_time_minutes} minutes", self.subheading_style))
        story.append(Paragraph(f"Total Word Count: {summary.total_word_count:,}", self.body_style))
        story.append(PageBreak())
        
        # Table of Contents (Outline)
        story.append(Paragraph("Outline", self.subheading_style))
        story.append(Spacer(1, 12))
        
        for i, item in enumerate(summary.outline, 1):
            toc_text = f"{i}. {item.title} (Page {item.page_number}, {item.reading_time_minutes:.1f} min)"
            story.append(Paragraph(f"• {toc_text}", self.body_style))
        
        story.append(PageBreak())
        
        # Key Points
        story.append(Paragraph("Key Takeaways", self.subheading_style))
        story.append(Spacer(1, 12))
        
        for point in summary.key_points:
            story.append(Paragraph(f"• {point.point}", self.key_point_style))
        
        story.append(PageBreak())
        
        # Condensed Content
        story.append(Paragraph("Summary", self.subheading_style))
        story.append(Spacer(1, 12))
        
        for chunk in summary.condensed_content:
            # Add headings if present
            if chunk.headings:
                for heading in chunk.headings:
                    story.append(Paragraph(heading, self.subheading_style))
            
            # Clean up equations in text
            clean_text = self.clean_equation(chunk.text)
            # Heuristic: if line looks like an equation, use equation style
            import re
            for line in clean_text.split('\n'):
                if re.match(r'^[\s\d=+\-*/^().,A-Za-z]+$', line) and len(line.strip()) > 0 and any(c in line for c in '=+-*/^'):
                    story.append(Paragraph(line, self.equation_style))
                else:
                    story.append(Paragraph(line, self.body_style))
            
            story.append(Spacer(1, 8))
            
            # Add metadata
            meta_text = f"<i>Page {chunk.page_number} • {chunk.word_count} words • {chunk.reading_time_minutes:.1f} min read</i>"
            story.append(Paragraph(meta_text, self.body_style))
            story.append(Spacer(1, 12))
        
        # Quiz section if available
        if summary.quiz:
            story.append(PageBreak())
            story.append(Paragraph("Quiz Questions", self.subheading_style))
            story.append(Spacer(1, 12))
            
            for i, question in enumerate(summary.quiz, 1):
                story.append(Paragraph(f"Question {i}: {question.question}", self.quiz_style))
                story.append(Spacer(1, 6))
                
                for j, option in enumerate(question.options, 1):
                    option_text = f"{j}. {option}"
                    story.append(Paragraph(option_text, self.body_style))
                
                story.append(Spacer(1, 6))
                answer_text = f"<b>Correct Answer:</b> {question.correct_answer}"
                story.append(Paragraph(answer_text, self.quiz_style))
                story.append(Spacer(1, 6))
                story.append(Paragraph(f"<i>Explanation:</i> {question.explanation}", self.body_style))
                story.append(Spacer(1, 12))
        
        # Processing Notes
        if summary.processing_notes:
            story.append(PageBreak())
            story.append(Paragraph("Processing Notes", self.subheading_style))
            story.append(Spacer(1, 12))
            
            for note in summary.processing_notes:
                story.append(Paragraph(f"• {note}", self.key_point_style))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer 