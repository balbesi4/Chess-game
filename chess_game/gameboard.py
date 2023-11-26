from constants import *
from boardcell import BoardCell
from piece import *
from move import Move
import copy


class GameBoard:
    def __init__(self):
        self.cells = [[0, 0, 0, 0, 0, 0, 0, 0] for _ in range(COLS)]
        self.last_move = None
        self._create()
        self.is_in_check = False
        self._initialize_pieces('white')
        self._initialize_pieces('black')

    def parse_server_move(self, initial, final):
        initial_cell = self.cells[initial[1]][initial[0]]
        final_cell = self.cells[final[1]][final[0]]
        piece = initial_cell.piece
        self.calc_moves(piece, initial[1], initial[0])
        self.move(piece, Move(initial_cell, final_cell))

    def check_lose(self, side):
        all_moves = 0
        for row in range(ROWS):
            for col in range(COLS):
                piece = self.cells[row][col].piece
                if piece and piece.color == side:
                    self.calc_moves(piece, row, col)
                    all_moves += len(piece.moves)
        # print(all_moves)
        return all_moves == 0

    def clear_all_moves(self):
        for row in range(ROWS):
            for col in range(COLS):
                piece = self.cells[row][col].piece
                if piece:
                    piece.clear_moves()

    def move(self, piece, move, testing=False):
        initial = move.initial
        final = move.final
        is_empty_between = self.cells[final.row][final.col].is_empty()
        self.cells[initial.row][initial.col].piece = None
        self.cells[final.row][final.col].piece = piece

        if isinstance(piece, Pawn):
            diff = final.col - initial.col
            if diff != 0 and is_empty_between:
                self.cells[initial.row][initial.col + diff].piece = None
                self.cells[final.row][final.col].piece = piece
            else:
                self.check_promotion(piece, final)
        if isinstance(piece, King):
            if self.castling(initial, final) and not testing:
                diff = final.col - initial.col
                rook = piece.left_rook if (diff < 0) else piece.right_rook
                self.move(rook, rook.moves[-1])
        piece.moved = True
        piece.clear_moves()
        self.last_move = move

    def valid_move(self, piece, move):
        return move in piece.moves

    def check_promotion(self, piece, final):
        if final.row == 0 or final.row == 7:
            self.cells[final.row][final.col].piece = Queen(piece.color)

    def castling(self, initial, final):
        return abs(initial.col - final.col) == 2

    def set_true_en_passant(self, piece):
        if not isinstance(piece, Pawn):
            return
        for row in range(ROWS):
            for col in range(COLS):
                if isinstance(self.cells[row][col].piece, Pawn):
                    self.cells[row][col].piece.en_passant = False
        piece.en_passant = True

    def in_check(self, piece, move):
        temp_piece = copy.deepcopy(piece)
        temp_board = copy.deepcopy(self)
        temp_board.move(temp_piece, move, testing=True)
        for row in range(ROWS):
            for col in range(COLS):
                if temp_board.cells[row][col].has_enemy_piece(piece.color):
                    temp_piece = temp_board.cells[row][col].piece
                    temp_board.calc_moves(temp_piece, row, col, flag=False)
                    for move in temp_piece.moves:
                        if isinstance(move.final.piece, King):
                            self.is_in_check = True
                            return True
        return False

    def calc_moves(self, piece, row, col, flag=True):
        def pawn_moves():
            steps = 1 if piece.moved else 2
            start = row + piece.dir
            end = row + (piece.dir * (1 + steps))
            for possible_move_row in range(start, end, piece.dir):
                if BoardCell.in_range(possible_move_row):
                    if self.cells[possible_move_row][col].is_empty():
                        initial = BoardCell(row, col)
                        final = BoardCell(possible_move_row, col)
                        move = Move(initial, final)
                        if flag:
                            if not self.in_check(piece, move):
                                piece.add_move(move)
                        else:
                            piece.add_move(move)
                    else:
                        break
                else:
                    break

            possible_move_row = row + piece.dir
            possible_move_cols = [col - 1, col + 1]
            for possible_move_col in possible_move_cols:
                if BoardCell.in_range(possible_move_row, possible_move_col):
                    if self.cells[possible_move_row][possible_move_col].has_enemy_piece(piece.color):
                        initial = BoardCell(row, col)
                        final_piece = self.cells[possible_move_row][possible_move_col].piece
                        final = BoardCell(possible_move_row, possible_move_col, final_piece)
                        move = Move(initial, final)
                        if flag:
                            if not self.in_check(piece, move):
                                piece.add_move(move)
                        else:
                            piece.add_move(move)

            r = 3 if piece.color == 'white' else 4
            fr = 2 if piece.color == 'white' else 5
            if BoardCell.in_range(col - 1) and row == r:
                if self.cells[row][col - 1].has_enemy_piece(piece.color):
                    p = self.cells[row][col - 1].piece
                    if isinstance(p, Pawn):
                        if p.en_passant:
                            initial = BoardCell(row, col)
                            final = BoardCell(fr, col - 1, p)
                            move = Move(initial, final)
                            if flag:
                                if not self.in_check(piece, move):
                                    piece.add_move(move)
                            else:
                                piece.add_move(move)
            if BoardCell.in_range(col + 1) and row == r:
                if self.cells[row][col + 1].has_enemy_piece(piece.color):
                    p = self.cells[row][col + 1].piece
                    if isinstance(p, Pawn):
                        if p.en_passant:
                            initial = BoardCell(row, col)
                            final = BoardCell(fr, col + 1, p)
                            move = Move(initial, final)
                            if flag:
                                if not self.in_check(piece, move):
                                    piece.add_move(move)
                            else:
                                piece.add_move(move)

        def knight_moves():
            possible_moves = [
                (row - 2, col + 1),
                (row - 1, col + 2),
                (row + 1, col + 2),
                (row + 2, col + 1),
                (row + 2, col - 1),
                (row + 1, col - 2),
                (row - 1, col - 2),
                (row - 2, col - 1),
            ]

            for possible_move in possible_moves:
                possible_move_row, possible_move_col = possible_move
                if BoardCell.in_range(possible_move_row, possible_move_col):
                    if self.cells[possible_move_row][possible_move_col].is_empty_or_enemy(piece.color):
                        initial = BoardCell(row, col)
                        final_piece = self.cells[possible_move_row][possible_move_col].piece
                        final = BoardCell(possible_move_row, possible_move_col, final_piece)
                        move = Move(initial, final)
                        if flag:
                            if not self.in_check(piece, move):
                                piece.add_move(move)
                            else:
                                break
                        else:
                            piece.add_move(move)

        def straight_moves(increments):
            for increment in increments:
                row_increment, col_increment = increment
                possible_move_row = row + row_increment
                possible_move_col = col + col_increment

                while True:
                    if BoardCell.in_range(possible_move_row, possible_move_col):
                        initial = BoardCell(row, col)
                        final_piece = self.cells[possible_move_row][possible_move_col].piece
                        final = BoardCell(possible_move_row, possible_move_col, final_piece)
                        move = Move(initial, final)
                        if self.cells[possible_move_row][possible_move_col].is_empty():
                            if flag:
                                if not self.in_check(piece, move):
                                    piece.add_move(move)
                            else:
                                piece.add_move(move)
                        elif self.cells[possible_move_row][possible_move_col].has_enemy_piece(piece.color):
                            if flag:
                                if not self.in_check(piece, move):
                                    piece.add_move(move)
                            else:
                                # break
                                piece.add_move(move)
                            break
                        elif self.cells[possible_move_row][possible_move_col].has_team_piece(piece.color):
                            break
                    else:
                        break

                    possible_move_row = possible_move_row + row_increment
                    possible_move_col = possible_move_col + col_increment

        def king_moves():
            possible_moves = [
                (row - 1, col + 0),
                (row - 1, col + 1),
                (row + 0, col + 1),
                (row + 1, col + 1),
                (row + 1, col + 0),
                (row + 1, col - 1),
                (row + 0, col - 1),
                (row - 1, col - 1),
            ]

            for possible_move in possible_moves:
                possible_move_row, possible_move_col = possible_move
                if BoardCell.in_range(possible_move_row, possible_move_col):
                    if self.cells[possible_move_row][possible_move_col].is_empty_or_enemy(piece.color):
                        initial = BoardCell(row, col)
                        final = BoardCell(possible_move_row, possible_move_col)
                        move = Move(initial, final)
                        if flag:
                            if not self.in_check(piece, move):
                                piece.add_move(move)
                            else:
                                break
                        else:
                            piece.add_move(move)
            if not piece.moved:
                left_rook = self.cells[row][0].piece
                if isinstance(left_rook, Rook):
                    if not left_rook.moved:
                        for c in range(1, 4):
                            if self.cells[row][c].has_piece():
                                break
                            if c == 3:
                                piece.left_rook = left_rook

                                initial = BoardCell(row, 0)
                                final = BoardCell(row, 3)
                                rook_move = Move(initial, final)

                                initial = BoardCell(row, col)
                                final = BoardCell(row, 2)
                                king_move = Move(initial, final)
                                if flag:
                                    if not self.in_check(piece, king_move) and not self.in_check(left_rook, rook_move):
                                        left_rook.add_move(rook_move)
                                        piece.add_move(king_move)
                                else:
                                    left_rook.add_move(rook_move)
                                    piece.add_move(king_move)

                right_rook = self.cells[row][7].piece
                if isinstance(right_rook, Rook):
                    if not right_rook.moved:
                        for c in range(5, 7):
                            if self.cells[row][c].has_piece():
                                break
                            if c == 6:
                                piece.right_rook = right_rook

                                initial = BoardCell(row, 7)
                                final = BoardCell(row, 5)
                                rook_move = Move(initial, final)

                                initial = BoardCell(row, col)
                                final = BoardCell(row, 6)
                                king_move = Move(initial, final)
                                if flag:
                                    if not self.in_check(piece, king_move) and not self.in_check(right_rook, rook_move):
                                        right_rook.add_move(rook_move)
                                        piece.add_move(king_move)
                                else:
                                    right_rook.add_move(rook_move)
                                    piece.add_move(king_move)

        if isinstance(piece, Pawn):
            pawn_moves()
        elif isinstance(piece, Knight):
            knight_moves()
        elif isinstance(piece, Bishop):
            straight_moves([
                (-1, 1),
                (-1, -1),
                (1, 1),
                (1, -1),
            ])
        elif isinstance(piece, Rook):
            straight_moves([
                (-1, 0),
                (0, 1),
                (1, 0),
                (0, -1),
            ])
        elif isinstance(piece, Queen):
            straight_moves([
                (-1, 1),
                (-1, -1),
                (1, 1),
                (1, -1),
                (-1, 0),
                (0, 1),
                (1, 0),
                (0, -1)
            ])

        elif isinstance(piece, King):
            king_moves()

    def _create(self):
        for row in range(ROWS):
            for col in range(COLS):
                self.cells[row][col] = BoardCell(row, col)

    def _initialize_pieces(self, color):
        row_pawn, row_other = (6, 7) if color == 'white' else (1, 0)

        # pawns
        for col in range(COLS):
            self.cells[row_pawn][col] = BoardCell(row_pawn, col, Pawn(color))

        # knights
        self.cells[row_other][1] = BoardCell(row_other, 1, Knight(color))
        self.cells[row_other][6] = BoardCell(row_other, 6, Knight(color))

        # bishops
        self.cells[row_other][2] = BoardCell(row_other, 2, Bishop(color))
        self.cells[row_other][5] = BoardCell(row_other, 5, Bishop(color))

        # rooks
        self.cells[row_other][0] = BoardCell(row_other, 0, Rook(color))
        self.cells[row_other][7] = BoardCell(row_other, 7, Rook(color))

        # queen
        self.cells[row_other][3] = BoardCell(row_other, 3, Queen(color))

        # king
        self.cells[row_other][4] = BoardCell(row_other, 4, King(color))
