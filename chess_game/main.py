import sys
import threading
import time
import select
import pygame
from constants import *
from tkinter import *
from game import Game
from boardcell import BoardCell
from move import Move
from botik import Bot
import socket


class GameState:
    def __init__(self):
        self.running = True
        self.result = "You lost!"


class Player:
    def __init__(self, game_mode):
        pygame.init()
        self.server_address = ('localhost', 65432)
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect(self.server_address)
        self.client_socket.setblocking(False)
        self.side = ""
        game_state = GameState()

        if game_mode == "bot":
            self.client_socket.send("play_with_bot".encode('utf-8'))
        else:
            self.client_socket.send("play_with_player".encode('utf-8'))
        self.wait_for_connection()

        self.listening_messages = True
        self.message_thread = threading.Thread(target=self.check_for_incoming_messages, args=(game_state,))
        self.message_thread.start()

        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.button_width = 0
        self.button_rect = None
        self.button_height = 0
        pygame.font.init()
        font = pygame.font.Font(None, 36)
        self.button_text = font.render("Сдаться", True, (255, 255, 255))
        self.create_lose_button()

        pygame.display.set_caption('Chess')
        self.game = Game()
        self.mainloop(game_state)
        self.make_final_window(game_state.result)

    @staticmethod
    def create(game_mode):
        Player(game_mode)

    def wait_for_connection(self):
        screen = pygame.display.set_mode((400, 300))
        pygame.display.set_caption("Шахматы")

        font = pygame.font.SysFont('monospace', 18, bold=True)
        text = font.render("Ожидание соперника...", 1, (0, 0, 0))
        text_rect = text.get_rect(center=(200, 150))

        waiting_for_opponent = True
        while waiting_for_opponent:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    exit()
            try:
                message = self.client_socket.recv(1024).decode('utf-8')
                if "side=" in message:
                    self.side = message.split('=')[1]
                    # print(self.side)
                    waiting_for_opponent = False
            except BlockingIOError:
                pass

            screen.fill((255, 255, 255))
            screen.blit(text, text_rect)
            pygame.display.flip()

        pygame.quit()

    def create_lose_button(self):
        self.button_rect = self.button_text.get_rect()
        self.button_rect.topleft = (360, 905)
        self.button_width = self.button_rect.width + 20
        self.button_height = self.button_rect.height + 20

    def draw_button(self):
        pygame.draw.rect(self.screen, (100, 100, 100), [0, 800, 800, 200])
        pygame.draw.rect(self.screen, (150, 150, 150), self.button_rect)
        self.screen.blit(self.button_text, (360, 905))

    def lose(self, game_state):
        self.client_socket.send("player_resigned".encode('utf-8'))
        game_state.running = False
        self.listening_messages = False
        pygame.quit()
        self.client_socket.close()
        game_state.result = "You lost!"

    def check_for_incoming_messages(self, game_state):
        while self.listening_messages:
            ready_to_read, _, _ = select.select([self.client_socket], [], [], 0)
            if ready_to_read:
                response = self.client_socket.recv(1024).decode('utf-8')
                # print(response)
                if response == "victory":
                    game_state.running = False
                    self.listening_messages = False
                    self.client_socket.close()
                    game_state.result = "You won!"
                else:
                    move_start, move_end = response.split()[0], response.split()[1]
                    initial = [int(move_start.split(',')[0]), int(move_start.split(',')[1])]
                    final = [int(move_end.split(',')[0]), int(move_end.split(',')[1])]
                    self.game.board.parse_server_move(initial, final)
                    if self.game.board.check_lose(self.side):
                        game_state.result = "You lost!"
                        game_state.running = False
                        self.send_move_to_server("player_resigned")
                        self.listening_messages = False
                    else:
                        self.game.next_turn()

    def send_move_to_server(self, move_message):
        self.client_socket.send(move_message.encode('utf-8'))

    def make_final_window(self, message):
        if self.screen:
            pygame.quit()
        pygame.init()
        pygame.font.init()
        width, height = 400, 300
        screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Result")
        black = (0, 0, 0)
        white = (255, 255, 255)
        font = pygame.font.SysFont("monospace", 55, bold=True)
        text = font.render(f"{message}", True, white)

        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
            screen.fill(black)
            screen.blit(text, (50, 125))
            pygame.display.flip()

        pygame.quit()

    def can_make_move(self):
        return self.game.next_player == self.side

    def mainloop(self, game_state):
        screen = self.screen
        game = self.game
        board = self.game.board
        piece_mover = self.game.piece_mover

        while game_state.running:
            game.show_bg(screen)
            game.show_check(screen)
            game.show_last_move(screen)
            game.show_moves(screen)
            game.show_pieces(screen)
            game.show_hover(screen)
            self.draw_button()

            if piece_mover.moving:
                piece_mover.update_blit(screen)

            for event in pygame.event.get():
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.button_rect.collidepoint(event.pos):
                        self.lose(game_state)
                        return
                    elif self.can_make_move():
                        piece_mover.update_mouse(event.pos)
                        clicked_row = piece_mover.mouseY // SQUARE_SIZE
                        clicked_col = piece_mover.mouseX // SQUARE_SIZE
                        if 0 <= clicked_col <= 7 and 0 <= clicked_row <= 7:
                            if board.cells[clicked_row][clicked_col].has_piece():
                                piece = board.cells[clicked_row][clicked_col].piece
                                if piece.color == game.next_player:
                                    board.calc_moves(piece, clicked_row, clicked_col, flag=True)
                                    piece_mover.save_initial(event.pos)
                                    piece_mover.drag_piece(piece)

                elif event.type == pygame.MOUSEMOTION:
                    motion_row = event.pos[1] // SQUARE_SIZE
                    motion_col = event.pos[0] // SQUARE_SIZE
                    game.set_hover(motion_row, motion_col)
                    if piece_mover.moving:
                        piece_mover.update_mouse(event.pos)
                        piece_mover.update_blit(screen)

                elif event.type == pygame.MOUSEBUTTONUP and self.can_make_move():
                    if piece_mover.moving:
                        piece_mover.update_mouse(event.pos)
                        released_row = piece_mover.mouseY // SQUARE_SIZE
                        released_col = piece_mover.mouseX // SQUARE_SIZE

                        if 0 <= released_col <= 7 and 0 <= released_row <= 7:
                            initial = BoardCell(piece_mover.initial_row, piece_mover.initial_col)
                            final = BoardCell(released_row, released_col)
                            move = Move(initial, final)
                            if board.valid_move(piece_mover.piece, move):
                                board.move(piece_mover.piece, move)
                                board.set_true_en_passant(piece_mover.piece)
                                self.send_move_to_server(str(move))
                                board.clear_all_moves()
                                # print(move)
                                game.next_turn()
                    piece_mover.stop_dragging_piece()

                elif event.type == pygame.QUIT:
                    self.lose(game_state)
                    return
            pygame.display.update()


class StartWindow:
    def __init__(self):
        self.window = Tk()
        self.window.resizable(False, False)
        self.window.geometry("400x300")
        self.window.grab_set()
        self.draw_buttons()
        self.window.mainloop()

    def draw_buttons(self):
        bot_button = Button(self.window, text="Играть с ботом", font=("Roboto", 14), height=2, width=16,
                            command=lambda: self.start_game("bot"))
        player_button = Button(self.window, text="Играть с человеком", font=("Roboto", 14), height=2, width=16,
                               command=lambda: self.start_game("player"))
        chess_label = Label(self.window, text="Шахматы", font=("Roboto", 30))
        chess_label.grid(row=0, column=0, columnspan=2, padx=70, pady=50)
        bot_button.grid(row=1, column=0, padx=5, pady=5)
        player_button.grid(row=1, column=1, padx=5, pady=5)

    def start_game(self, game_mode):
        self.window.destroy()
        if game_mode == "bot":
            threading.Thread(target=Bot.create).start()
        time.sleep(1)
        threading.Thread(target=Player.create, args=(game_mode,)).start()


if __name__ == "__main__":
    start_window = StartWindow()
