from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

class PDFService:
    @staticmethod
    def generate_report_card_pdf(student, exam, report_card):
        """Generates a professional PDF report card using ReportLab."""
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=letter,
            rightMargin=40, 
            leftMargin=40, 
            topMargin=40, 
            bottomMargin=40
        )
        
        styles = getSampleStyleSheet()
        story = []
        
        # Define clean theme colors
        primary_color = colors.HexColor("#1A365D")   # Dark Navy Blue
        secondary_color = colors.HexColor("#2B6CB0") # Medium Blue
        text_color = colors.HexColor("#2D3748")      # Charcoal
        bg_light = colors.HexColor("#F7FAFC")        # Soft Grey
        border_color = colors.HexColor("#E2E8F0")    # Border Grey
        
        # Custom Typography Styles
        title_style = ParagraphStyle(
            name="TitleStyle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=24,
            textColor=primary_color,
            alignment=1,  # Center alignment
            spaceAfter=20
        )
        
        header_style = ParagraphStyle(
            name="HeaderStyle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=16,
            textColor=secondary_color,
            spaceAfter=8,
            spaceBefore=12
        )
        
        body_style = ParagraphStyle(
            name="BodyStyle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            textColor=text_color
        )
        
        body_bold_style = ParagraphStyle(
            name="BodyBoldStyle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=14,
            textColor=text_color
        )

        # Header Title
        story.append(Paragraph("DIGITAL STUDENT REPORT CARD", title_style))
        
        # 1. Student and Exam Metadata Card
        meta_data = [
            [Paragraph("<b>Student Name:</b>", body_style), Paragraph(student.get("name", "N/A"), body_style),
             Paragraph("<b>Exam Name:</b>", body_style), Paragraph(exam.get("examName", "N/A"), body_style)],
            [Paragraph("<b>Student ID:</b>", body_style), Paragraph(student.get("studentId", "N/A"), body_style),
             Paragraph("<b>Term:</b>", body_style), Paragraph(exam.get("term", "N/A"), body_style)],
            [Paragraph("<b>Roll Number:</b>", body_style), Paragraph(student.get("rollNumber", "N/A"), body_style),
             Paragraph("<b>Academic Year:</b>", body_style), Paragraph(exam.get("academicYear", "N/A"), body_style)],
            [Paragraph("<b>Class Enrolled:</b>", body_style), Paragraph(student.get("classId", "N/A"), body_style),
             Paragraph("<b>Exam Status:</b>", body_style), Paragraph("PUBLISHED", body_style)]
        ]
        
        meta_table = Table(meta_data, colWidths=[100, 160, 100, 160])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), bg_light),
            ('BOX', (0,0), (-1,-1), 1, border_color),
            ('PADDING', (0,0), (-1,-1), 8),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        
        story.append(meta_table)
        story.append(Spacer(1, 15))
        
        # 2. Performance Table
        story.append(Paragraph("SUBJECT PERFORMANCE", header_style))
        
        table_data = [
            [Paragraph("<b>Subject Name</b>", body_bold_style), 
             Paragraph("<b>Marks Scored</b>", body_bold_style), 
             Paragraph("<b>Maximum Marks</b>", body_bold_style), 
             Paragraph("<b>Outcome</b>", body_bold_style)]
        ]
        
        max_m = exam.get("maxMarks", 100)
        pass_m = exam.get("passMarks", 35)
        
        for sub_mark in report_card.get("subjectMarks", []):
            marks_val = sub_mark.get("marks", 0.0)
            status_text = "PASS" if marks_val >= pass_m else "FAIL"
            status_color = "#38A169" if status_text == "PASS" else "#E53E3E" # Green vs Red
            
            table_data.append([
                Paragraph(sub_mark.get("subjectName", "N/A"), body_style),
                Paragraph(str(marks_val), body_style),
                Paragraph(str(max_m), body_style),
                Paragraph(status_text, ParagraphStyle(
                    name=f"Status_{sub_mark.get('subjectId')}",
                    parent=body_bold_style,
                    textColor=colors.HexColor(status_color)
                ))
            ])
            
        marks_table = Table(table_data, colWidths=[200, 100, 100, 120])
        marks_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#EDF2F7")),
            ('BOTTOMPADDING', (0,0), (-1,0), 6),
            ('GRID', (0,0), (-1,-1), 1, border_color),
            ('PADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(marks_table)
        story.append(Spacer(1, 15))
        
        # 3. Overall Summary Card
        story.append(Paragraph("EXAMINATION METRICS SUMMARY", header_style))
        
        outcome_text = "PASS" if report_card.get("passed") else "FAIL"
        outcome_color = "#38A169" if report_card.get("passed") else "#E53E3E"
        
        summary_data = [
            [Paragraph("<b>Total Score:</b>", body_bold_style), Paragraph(f"{report_card.get('totalMarks')} marks", body_style),
             Paragraph("<b>Overall Percentage:</b>", body_bold_style), Paragraph(f"{report_card.get('percentage')}%", body_style)],
            [Paragraph("<b>Class Rank:</b>", body_bold_style), Paragraph(f"Rank {report_card.get('rank')}", body_style),
             Paragraph("<b>Assigned Grade:</b>", body_bold_style), Paragraph(report_card.get("grade", "N/A"), body_style)],
            [Paragraph("<b>Result Status:</b>", body_bold_style), Paragraph(
                outcome_text, 
                ParagraphStyle(
                    name="OutcomeStyle",
                    parent=body_bold_style,
                    textColor=colors.HexColor(outcome_color)
                )),
             Paragraph("<b>Date Generated:</b>", body_bold_style), Paragraph(datetime.now().strftime("%Y-%m-%d"), body_style)]
        ]
        
        summary_table = Table(summary_data, colWidths=[100, 160, 100, 160])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#EDF2F7")),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#CBD5E0")),
            ('PADDING', (0,0), (-1,-1), 8),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        story.append(summary_table)
        
        # Compile document layout
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
