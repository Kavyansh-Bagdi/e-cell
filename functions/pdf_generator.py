from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib import colors

class Room:
    """
    Represents a room with a specific seating capacity and arrangement.
    """
    def __init__(self, room_id: str, capacity: int):
        """
        Initializes a Room object.

        Args:
            room_id (str): The unique identifier for the room.
            capacity (int): The number of seats available in the room.
        """
        self.room_id = room_id
        self.capacity = capacity
        # Pointers for next available seat, corrected to be instance variables starting at 0
        self.ptrA = 0
        self.ptrB = 0
        # Arrangement stores student IDs in [SeatA, SeatB] columns
        self.arrangement = [[None, None] for _ in range(capacity)]

    def allocate(self, student_id: str, seat_type: str) -> bool:
        """
        Allocates a student to the next available seat of a given type.

        Args:
            student_id (str): The ID of the student to allocate.
            seat_type (str): The type of seat ("SeatA" or "SeatB").

        Returns:
            bool: True if allocation was successful, False otherwise.
        """
        if seat_type == "SeatA":
            # Find the next available 'A' seat starting from the pointer
            while self.ptrA < self.capacity and self.arrangement[self.ptrA][0] is not None:
                self.ptrA += 1
            
            # If an empty seat is found, allocate the student
            if self.ptrA < self.capacity:
                self.arrangement[self.ptrA][0] = student_id
                return True
        
        elif seat_type == "SeatB":
            # Find the next available 'B' seat starting from the pointer
            while self.ptrB < self.capacity and self.arrangement[self.ptrB][1] is not None:
                self.ptrB += 1
            
            # If an empty seat is found, allocate the student
            if self.ptrB < self.capacity:
                self.arrangement[self.ptrB][1] = student_id
                return True
                
        # Return False if no seat was available or seat_type was invalid
        return False

def generate_seating_pdf(rooms: list, filename: str):
    """
    Generates a PDF file detailing the seating arrangement for a list of rooms.

    Args:
        rooms (list): A list of Room objects.
        filename (str): The name of the output PDF file.
    """
    doc = SimpleDocTemplate(filename)
    styles = getSampleStyleSheet()
    elements = []

    print(f"Generating PDF: {filename}...")

    for i, room in enumerate(rooms):
        # Add the Room ID as a title for this section
        title = Paragraph(f"Seating Arrangement: Room {room.room_id}", styles['h2'])
        elements.append(title)
        elements.append(Spacer(1, 0.2 * inch))

        # Prepare the data for the table
        # Header row
        data = [['Seat Number', 'Student in Seat A', 'Student in Seat B']]
        
        # Populate rows with student data
        for seat_num in range(room.capacity):
            student_a = room.arrangement[seat_num][0] or '--- Empty ---'
            student_b = room.arrangement[seat_num][1] or '--- Empty ---'
            data.append([str(seat_num + 1), student_a, student_b])

        # Create and style the table
        table = Table(data, colWidths=[1.5 * inch, 2.5 * inch, 2.5 * inch])
        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ])
        table.setStyle(style)
        
        elements.append(table)
        
        # Add a page break after each room's table, except for the last one
        if i < len(rooms) - 1:
            elements.append(PageBreak())

    # Build the PDF document
    doc.build(elements)
    print("PDF generation complete.")


# --- Example Usage ---
if __name__ == "__main__":
    # 1. Create room objects
    room101 = Room("101", 10)
    room102 = Room("102", 8)

    # 2. Allocate students to Room 101
    room101.allocate("Student_A01", "SeatA")
    room101.allocate("Student_B01", "SeatB")
    room101.allocate("Student_A02", "SeatA")
    room101.allocate("Student_A03", "SeatA")
    room101.allocate("Student_B02", "SeatB")
    room101.allocate("Student_B03", "SeatB")
    room101.allocate("Student_A04", "SeatA")

    # 3. Allocate students to Room 102
    room102.allocate("Student_C01", "SeatA")
    room102.allocate("Student_D01", "SeatB")
    room102.allocate("Student_C02", "SeatA")
    room102.allocate("Student_D02", "SeatB")
    room102.allocate("Student_D03", "SeatB")
    
    # 4. Create a list of all rooms
    all_rooms = [room101, room102]
    
    # 5. Generate the PDF from the list of rooms
    generate_seating_pdf(all_rooms, "seating_arrangement.pdf")
