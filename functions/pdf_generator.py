import os
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, A4

def first_two_words(name: str) -> str:
    if not name:
        return ""
    return " ".join(name.split()[:2])

def generate_seating_pdf(rooms, filename: str,date,time):
    if len(rooms) == 0:
        return
    
    rooms = dict(sorted(rooms.items()))
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, filename if filename.endswith(".pdf") else filename + ".pdf")

    # Landscape A4 page, with very small margins (4pt)
    doc = SimpleDocTemplate(filepath, pagesize=landscape(A4),
                            leftMargin=4, rightMargin=4,
                            topMargin=4, bottomMargin=4)
    styles = getSampleStyleSheet()

    # Custom text styles
    title_style = ParagraphStyle(
        'title',
        parent=styles['Heading1'],
        alignment=1,  # Centered
        fontSize=14,
        textColor=colors.black,   # white text on gray
        spaceAfter=0,
        spaceBefore=0
    )
    subtitle_style = ParagraphStyle(
        'subtitle',
        parent=styles['Normal'],
        alignment=1,
        fontSize=10,
        spaceAfter=12
    )

    elements = []
    idx = 0
    for key in rooms:
        room = rooms[key]

        # ==== Title Bar ====
        title_para = Paragraph("Mid Term Examination", title_style)
        title_table = Table([[title_para]], colWidths=[10.5*inch])  # one-cell table as title bar
        title_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(title_table)

        # Subtitle

        elements.append(Paragraph("Seating Plan for Program Core Courses", subtitle_style))
        elements.append(Paragraph("Date : "+date+" Slot : "+ time, subtitle_style))

        # ==== Main Table ====
        data = [['Sr. No.', 'Student ID', 'Name', 'Batch', 'Room No.', 'Seat No.',
                 'Student ID', 'Name', 'Batch', 'Room No.', 'Seat No.']]

        # Fill rows
        for seat_num in range(room.capacity):
            student_a = room.arrangement[seat_num][0] or ["","",""]
            student_b = room.arrangement[seat_num][1] or ["","",""]
            data.append([
                str(seat_num + 1), student_a[0], first_two_words(student_a[1]), student_a[2], room.roomId, str(seat_num+1)+'A',
                student_b[0], first_two_words(student_b[1]), student_b[2], room.roomId, str(seat_num+1)+'B'
            ])

        # Column widths with extra space left/right
        col_widths = [0.5*inch, 1.1*inch, 1.7*inch, 0.8*inch, 1*inch, 0.8*inch,
                      1.1*inch, 1.7*inch, 0.8*inch, 1*inch, 0.8*inch]

        table = Table(data, colWidths=col_widths, repeatRows=1, hAlign="CENTER")

        # Styling
        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.gray),   # header bg
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 7),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('TOPPADDING', (0, 0), (-1, -1), 1),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
            ('LEFTPADDING', (0, 0), (-1, -1), 2),
            ('RIGHTPADDING', (0, 0), (-1, -1), 2),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ])

        # Zebra striping
        for i in range(1, len(data)):
            bg_color = colors.whitesmoke if i % 2 == 0 else colors.white
            style.add('BACKGROUND', (0, i), (-1, i), bg_color)

        table.setStyle(style)

        elements.append(table)

        if idx < len(rooms) - 1:
            idx += 1
            elements.append(PageBreak())

    doc.build(elements)
