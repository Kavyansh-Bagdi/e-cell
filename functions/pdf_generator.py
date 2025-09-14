import os
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib import colors

def generate_seating_pdf(rooms, filename: str):

    if len(rooms) == 0:
        return
    
    rooms = dict(sorted(rooms.items()))
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    filepath = os.path.join(output_dir, filename if filename.endswith(".pdf") else filename + ".pdf")

    doc = SimpleDocTemplate(filepath)
    styles = getSampleStyleSheet()
    elements = []

    print(f"Generating PDF: {filepath}...")
    idx = 0
    for key in rooms:
        room = rooms[key]
        title = Paragraph(f"Seating Arrangement: Room {room.roomId}", styles['h2'])
        elements.append(title)
        elements.append(Spacer(1, 0.2 * inch))

        data = [['S. No.', 'Student', 'Student']]
        
        for seat_num in range(room.capacity):
            student_a = room.arrangement[seat_num][0] or ''
            student_b = room.arrangement[seat_num][1] or ''
            data.append([str(seat_num + 1), student_a, student_b])

        table = Table(data, colWidths=[1.5 * inch, 2.5 * inch, 2.5 * inch])
        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.whitesmoke),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),  
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ])
        table.setStyle(style)
        
        elements.append(table)
        
        if idx < len(rooms) - 1:
            idx += 1
            elements.append(PageBreak())

    doc.build(elements)
    print("PDF generation complete.")
