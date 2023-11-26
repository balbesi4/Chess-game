import chess
import chess.engine
import socket
from boardcell import BoardCell
from gameboard import GameBoard
from piece import *
import threading
import select


class BotGameState:
    def __init__(self):
        self.running = True


class Bot:
    def __init__(self):
        self.engine = chess.engine.SimpleEngine.popen_uci("Stockfish\\stockfish-windows-x86-64-avx2.exe")
        self.board = GameBoard()
        game_state = BotGameState()

        self.server_address = ('localhost', 65432)
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect(self.server_address)
        self.client_socket.setblocking(False)
        self.client_socket.send("bot".encode('utf-8'))

        self.move_side = "w"
        self.side = ''
        self.wait_for_side()
        if self.side == self.move_side:
            self.find_best_move()

        self.listening_messages = True
        self.message_thread = threading.Thread(target=self.check_for_incoming_messages, args=(game_state,))
        self.message_thread.start()

    @staticmethod
    def create():
        bot = Bot()

    def wait_for_side(self):
        waiting_for_opponent = True
        while waiting_for_opponent:
            try:
                message = self.client_socket.recv(1024).decode('utf-8')
                if "side=" in message:
                    self.side = message.split('=')[1][0]
                    waiting_for_opponent = False
            except BlockingIOError:
                pass

    def send_move_message(self, move):
        self.client_socket.send(move.encode('utf-8'))

    def parse_bot_move(self, move):
        initial = move[:2]
        final = move[2:]
        initial_ints = (BoardCell.get_number(initial[0]), 8 - int(initial[1]))
        final_ints = (BoardCell.get_number(final[0]), 8 - int(final[1]))
        formatted_move = f"{initial_ints[0]},{initial_ints[1]} {final_ints[0]},{final_ints[1]}"
        self.board.parse_server_move(initial_ints, final_ints)
        return formatted_move

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
                else:
                    move_start, move_end = response.split()[0], response.split()[1]
                    initial = [int(move_start.split(',')[0]), int(move_start.split(',')[1])]
                    final = [int(move_end.split(',')[0]), int(move_end.split(',')[1])]
                    self.board.parse_server_move(initial, final)
                    side = "white" if self.side == "w" else "black"
                    if self.board.check_lose(side):
                        game_state.running = False
                        self.lose(game_state)
                    else:
                        self.find_best_move()
                        self.move_side = "w" if self.move_side == "b" else "b"

    def lose(self, game_state):
        self.client_socket.send("player_resigned".encode('utf-8'))
        game_state.running = False
        self.listening_messages = False
        self.client_socket.close()

    def find_best_move(self):
        s = ''
        for row in self.board.cells:
            free_row = 0
            for cell in row:
                if cell.is_empty():
                    free_row += 1
                else:
                    piece = cell.piece
                    val = piece.value
                    if free_row > 0:
                        s += str(free_row)
                        free_row = 0
                    if isinstance(piece, Pawn):
                        if val > 0:
                            s += 'P'
                        else:
                            s += 'p'
                    if isinstance(piece, Knight):
                        if val > 0:
                            s += 'N'
                        else:
                            s += 'n'
                    if isinstance(piece, Bishop):
                        if val > 0:
                            s += 'B'
                        else:
                            s += 'b'
                    if isinstance(piece, Rook):
                        if val > 0:
                            s += 'R'
                        else:
                            s += 'r'
                    if isinstance(piece, Queen):
                        if val > 0:
                            s += 'Q'
                        else:
                            s += 'q'
                    if isinstance(piece, King):
                        if val > 0:
                            s += 'K'
                        else:
                            s += 'k'
            if free_row > 0:
                s += str(free_row)
            s += '/'
        s = s[:-1]
        s += f' {self.side} '
        s += 'KQkq - 0 1'
        # print(s)
        final_board = chess.Board(s)
        move = self.engine.play(final_board, chess.engine.Limit(time=2.0)).move
        # print(move)
        self.send_move_message(self.parse_bot_move(move.__str__()))
