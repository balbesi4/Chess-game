class BoardCell:
    _number_to_letters = {0: 'a', 1: 'b', 2: 'c', 3: 'd', 4: 'e', 5: 'f', 6: 'g', 7: 'h'}

    def __init__(self, row, col, piece=None):
        self.row = row
        self.col = col
        self.piece = piece
        self.letter = self._number_to_letters[col]

    def __eq__(self, other):
        return self.row == other.row and self.col == other.col

    def has_piece(self):
        return self.piece is not None

    def is_empty(self):
        return not self.has_piece()

    def has_team_piece(self, color):
        return self.has_piece() and self.piece.color == color

    def has_enemy_piece(self, color):
        return self.has_piece() and self.piece.color != color

    def is_empty_or_enemy(self, color):
        return self.is_empty() or self.has_enemy_piece(color)

    @staticmethod
    def in_range(*cords):
        for cord in cords:
            if cord < 0 or cord > 7:
                return False
        return True

    @staticmethod
    def get_letter(col):
        return BoardCell._number_to_letters[col]

    @staticmethod
    def get_number(letter):
        for number in BoardCell._number_to_letters:
            if BoardCell._number_to_letters[number] == letter:
                return number
