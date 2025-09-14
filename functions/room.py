class Room:
    ptrA = 0
    ptrB = 0
    capacity = None
    roomId = None
    arrangement = None

    def __init__(self,roomId : str, capacity : int):
        self.roomId = roomId
        self.capacity = capacity
        self.arrangement = [[None,None] for _ in range(capacity)]

    def allocate(self, student_id: str, seat_type: str) -> bool:
        if seat_type == "SeatA":
            if(self.capacity == self.ptrA):
                return False
            while self.ptrA < self.capacity and self.arrangement[self.ptrA][0] is not None:
                self.ptrA += 1
            if self.ptrA < self.capacity:
                self.arrangement[self.ptrA][0] = student_id
                return True
        else:
            if(self.capacity == self.ptrB):
                return False
            while self.ptrB < self.capacity and self.arrangement[self.ptrB][1] is not None:
                self.ptrB += 1
            if self.ptrB < self.capacity:
                self.arrangement[self.ptrB][1] = student_id
                return True
        return False

    def left(self,seat_type):
        if(seat_type == "A"):
            return self.capacity - self.ptrA 
        else:
            return self.capacity - self.ptrB