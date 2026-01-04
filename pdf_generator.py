"""
PDF Generator for TRUSTMEBRO
Generates watermarked PDF exports of parody papers
"""

import os
import re
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.platypus.flowables import Flowable
from reportlab.pdfgen import canvas


class WatermarkCanvas(canvas.Canvas):
    """Canvas with watermark on every page"""
    
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self.pages = []
    
    def showPage(self):
        self.pages.append(dict(self.__dict__))
        self._startPage()
    
    def save(self):
        page_count = len(self.pages)
        for page in self.pages:
            self.__dict__.update(page)
            self._draw_watermark()
            self._draw_header_footer()
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)
    
    def _draw_watermark(self):
        """Draw diagonal watermark"""
        self.saveState()
        self.setFillColor(colors.Color(0.8, 0.75, 0.65, alpha=0.15))
        self.setFont('Helvetica-Bold', 50)
        self.translate(4.25*inch, 5.5*inch)
        self.rotate(35)
        self.drawCentredString(0, 0, "TRUSTMEBRO - PARODY")
        self.restoreState()
    
    def _draw_header_footer(self):
        """Draw header and footer"""
        width, height = letter
        
        # Header banner
        self.saveState()
        self.setFillColor(colors.Color(0.78, 0.22, 0.16))  # #C85A28
        self.rect(0, height - 0.5*inch, width, 0.5*inch, fill=1, stroke=0)
        self.setFillColor(colors.white)
        self.setFont('Helvetica-Bold', 10)
        self.drawCentredString(width/2, height - 0.35*inch, 
                               "PARODY / FICTIONAL RESEARCH — DO NOT CITE AS REAL")
        self.restoreState()
        
        # Footer
        self.saveState()
        self.setFillColor(colors.Color(0.3, 0.2, 0.1))
        self.setFont('Helvetica', 8)
        self.drawCentredString(width/2, 0.3*inch, 
                               "Generated parody by TRUSTMEBRO. No claim is factual. All data is simulated.")
        self.restoreState()


class PDFGenerator:
    """Generate PDF versions of parody papers"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_styles()
    
    def _setup_styles(self):
        """Set up custom paragraph styles"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='PaperTitle',
            parent=self.styles['Heading1'],
            fontSize=16,
            spaceAfter=12,
            textColor=colors.Color(0.24, 0.16, 0.08),
            fontName='Helvetica-Bold'
        ))
        
        # Authors style
        self.styles.add(ParagraphStyle(
            name='Authors',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=6,
            alignment=1,  # Center
            textColor=colors.Color(0.3, 0.2, 0.1)
        ))
        
        # Affiliations style
        self.styles.add(ParagraphStyle(
            name='Affiliations',
            parent=self.styles['Normal'],
            fontSize=9,
            spaceAfter=20,
            alignment=1,
            textColor=colors.Color(0.4, 0.3, 0.2),
            fontName='Helvetica-Oblique'
        ))
        
        # Section heading style
        self.styles.add(ParagraphStyle(
            name='SectionHeading',
            parent=self.styles['Heading2'],
            fontSize=12,
            spaceBefore=16,
            spaceAfter=8,
            textColor=colors.Color(0.78, 0.22, 0.16),
            fontName='Helvetica-Bold'
        ))
        
        # Body text style - modify existing BodyText
        self.styles['BodyText'].fontSize = 10
        self.styles['BodyText'].spaceAfter = 8
        self.styles['BodyText'].leading = 14
        self.styles['BodyText'].textColor = colors.Color(0.2, 0.15, 0.1)
        
        # Reference style
        self.styles.add(ParagraphStyle(
            name='Reference',
            parent=self.styles['Normal'],
            fontSize=9,
            spaceAfter=6,
            leftIndent=20,
            firstLineIndent=-20,
            textColor=colors.Color(0.3, 0.25, 0.2)
        ))
        
        # Caption style
        self.styles.add(ParagraphStyle(
            name='Caption',
            parent=self.styles['Normal'],
            fontSize=9,
            spaceAfter=12,
            alignment=1,
            textColor=colors.Color(0.4, 0.3, 0.2),
            fontName='Helvetica-Oblique'
        ))
        
        # Disclaimer style
        self.styles.add(ParagraphStyle(
            name='Disclaimer',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceBefore=12,
            spaceAfter=12,
            backColor=colors.Color(1, 0.95, 0.9),
            borderColor=colors.Color(0.78, 0.22, 0.16),
            borderWidth=1,
            borderPadding=8,
            textColor=colors.Color(0.6, 0.2, 0.1)
        ))
    
    def generate(self, paper_data, filepath):
        """Generate PDF from paper data"""
        doc = SimpleDocTemplate(
            filepath,
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=1*inch,
            bottomMargin=0.75*inch
        )
        
        story = []
        
        # Study ID badge
        study_id = f"Study ID: {paper_data['paper_id']} [FICTIONAL]"
        story.append(Paragraph(study_id, self.styles['Caption']))
        story.append(Spacer(1, 6))
        
        # Title
        story.append(Paragraph(paper_data['title'], self.styles['PaperTitle']))
        
        # Authors
        authors_text = ", ".join(paper_data['authors'])
        story.append(Paragraph(f"<b>{authors_text}</b> [FICTIONAL AUTHORS]", self.styles['Authors']))
        
        # Affiliations
        affiliations_text = " | ".join(paper_data['affiliations'])
        story.append(Paragraph(f"<i>{affiliations_text}</i> [FICTIONAL INSTITUTIONS]", self.styles['Affiliations']))
        
        story.append(Spacer(1, 12))
        
        # Parody notice
        notice = """<b>⚠️ PARODY NOTICE:</b> This document is entirely fictional and was generated 
        for entertainment purposes only. All data, findings, authors, and institutions are fabricated. 
        DO NOT cite this document in any academic, professional, or legal context."""
        story.append(Paragraph(notice, self.styles['Disclaimer']))
        
        story.append(Spacer(1, 12))
        
        # Abstract
        story.append(Paragraph("ABSTRACT", self.styles['SectionHeading']))
        story.append(Paragraph(paper_data['abstract'], self.styles['BodyText']))
        
        # Charts
        if paper_data.get('chart_files'):
            story.append(Spacer(1, 12))
            for i, chart_file in enumerate(paper_data['chart_files']):
                if os.path.exists(chart_file):
                    try:
                        img = Image(chart_file, width=5*inch, height=3*inch)
                        story.append(img)
                        
                        # Caption
                        if paper_data.get('charts') and i < len(paper_data['charts']):
                            caption = paper_data['charts'][i].get('caption', f'Figure {i+1}. Simulated data.')
                            story.append(Paragraph(caption, self.styles['Caption']))
                        
                        story.append(Spacer(1, 12))
                    except Exception:
                        pass
        
        # Full paper sections
        if paper_data.get('introduction'):
            story.append(Paragraph("1. INTRODUCTION", self.styles['SectionHeading']))
            # Handle markdown-like formatting
            intro_text = paper_data['introduction'].replace('\n\n', '<br/><br/>')
            story.append(Paragraph(intro_text, self.styles['BodyText']))
        
        if paper_data.get('methods'):
            story.append(Paragraph("2. METHODS", self.styles['SectionHeading']))
            methods_text = paper_data['methods'].replace('**', '<b>').replace('\n\n', '<br/><br/>')
            # Fix bold tags
            methods_text = re.sub(r'<b>([^<]+)<b>', r'<b>\1</b>', methods_text)
            story.append(Paragraph(methods_text, self.styles['BodyText']))
        
        if paper_data.get('results'):
            story.append(Paragraph("3. RESULTS", self.styles['SectionHeading']))
            results_text = paper_data['results'].replace('**', '<b>').replace('\n\n', '<br/><br/>')
            results_text = re.sub(r'<b>([^<]+)<b>', r'<b>\1</b>', results_text)
            story.append(Paragraph(results_text, self.styles['BodyText']))
        
        if paper_data.get('discussion'):
            story.append(Paragraph("4. DISCUSSION", self.styles['SectionHeading']))
            disc_text = paper_data['discussion'].replace('**', '<b>').replace('\n\n', '<br/><br/>')
            disc_text = re.sub(r'<b>([^<]+)<b>', r'<b>\1</b>', disc_text)
            story.append(Paragraph(disc_text, self.styles['BodyText']))
        
        # Limitations
        story.append(Paragraph("LIMITATIONS & DISCLAIMER", self.styles['SectionHeading']))
        lim_text = paper_data['limitations'].replace('**', '<b>').replace('\n\n', '<br/><br/>')
        lim_text = re.sub(r'<b>([^<]+)<b>', r'<b>\1</b>', lim_text)
        story.append(Paragraph(lim_text, self.styles['BodyText']))
        
        # References
        story.append(Paragraph("REFERENCES [ALL FICTIONAL]", self.styles['SectionHeading']))
        for i, ref in enumerate(paper_data['references'], 1):
            story.append(Paragraph(f"[{i}] {ref}", self.styles['Reference']))
        
        # Final disclaimer
        story.append(Spacer(1, 24))
        final_notice = """<b>GENERATED BY TRUSTMEBRO</b><br/>
        Journal of Unverified Claims — Parody Research Generator<br/>
        <i>Everything in this document is fictional. This is satire.</i>"""
        story.append(Paragraph(final_notice, self.styles['Disclaimer']))
        
        # Build PDF with watermark canvas
        doc.build(story, canvasmaker=WatermarkCanvas)
