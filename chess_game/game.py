import pygame
from piece import King
from constants import *
from gameboard import GameBoard
from piecemover import PieceMover
from boardcell import BoardCell
from gameconfig import GameConfig


class Game:
    def __init__(self):
        self.next_player = 'white'
        self.hovered_square = None
        self.board = GameBoard()
        self.piece_mover = PieceMover()
        self.config = GameConfig()

    def show_check(self, surface):
        if self.board.is_in_check:
            for row in range(ROWS):
                for col in range(COLS):
                    cell = self.board.cells[row][col]
                    piece = cell.piece
                    if piece and isinstance(piece, King) and piece.color == self.next_player:
                        color = self.config.check_color.light if (row + col) % 2 == 0 else self.config.check_color.dark
                        rect = (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
                        pygame.draw.rect(surface, color, rect)
                        return

    def show_bg(self, surface):
        for row in range(ROWS):
            for col in range(COLS):
                color = self.config.bg_color.light if (row + col) % 2 == 0 else self.config.bg_color.dark
                rect = (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
                pygame.draw.rect(surface, color, rect)
                if col == 0:
                    color = self.config.bg_color.dark if row % 2 == 0 else self.config.bg_color.light
                    lbl = self.config.font.render(str(ROWS - row), 1, color)
                    lbl_pos = (5, 5 + row * SQUARE_SIZE)
                    surface.blit(lbl, lbl_pos)
                if row == 7:
                    color = self.config.bg_color.dark if (row + col) % 2 == 0 else self.config.bg_color.light
                    lbl = self.config.font.render(BoardCell.get_letter(col), 1, color)
                    lbl_pos = (col * SQUARE_SIZE + SQUARE_SIZE - 20, HEIGHT - 220)
                    surface.blit(lbl, lbl_pos)

    def show_pieces(self, surface):
        for row in range(ROWS):
            for col in range(COLS):
                if self.board.cells[row][col].has_piece():
                    piece = self.board.cells[row][col].piece
                    if piece is not self.piece_mover.piece:
                        piece.set_texture(size=80)
                        img = pygame.image.load(piece.texture)
                        img_center = col * SQUARE_SIZE + SQUARE_SIZE // 2, row * SQUARE_SIZE + SQUARE_SIZE // 2
                        piece.texture_rect = img.get_rect(center=img_center)
                        surface.blit(img, piece.texture_rect)

    def show_moves(self, surface):
        if self.piece_mover.moving:
            piece = self.piece_mover.piece
            for move in piece.moves:
                color = self.config.moves_color.light if (move.final.row + move.final.col) % 2 == 0 else self.config.moves_color.dark
                rect = (move.final.col * SQUARE_SIZE, move.final.row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
                pygame.draw.rect(surface, color, rect)

    def show_last_move(self, surface):
        if self.board.last_move:
            initial = self.board.last_move.initial
            final = self.board.last_move.final
            for pos in [initial, final]:
                color = self.config.trace_color.light if (pos.row + pos.col) % 2 == 0 else self.config.trace_color.dark
                rect = (pos.col * SQUARE_SIZE, pos.row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
                pygame.draw.rect(surface, color, rect)

    def show_hover(self, surface):
        if self.hovered_square:
            color = (180, 180, 180)
            rect = (self.hovered_square.col * SQUARE_SIZE, self.hovered_square.row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
            pygame.draw.rect(surface, color, rect, width=3)

    def next_turn(self):
        self.next_player = 'white' if self.next_player == 'black' else 'black'
        self.board.is_in_check = False

    def set_hover(self, row, col):
        if not (0 <= row <= 7 and 0 <= col <= 7):
            return
        self.hovered_square = self.board.cells[row][col]

    def reset(self):
        self.__init__()
