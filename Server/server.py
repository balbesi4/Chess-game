import socket
import threading
from queue import Queue
import random


class ClientManager:
    def __init__(self):
        self.new_clients = []
        self.bots = []
        self.bot_game_clients = []
        self.player_game_clients = []

    def add_player_game_client(self, client):
        self.new_clients.remove(client)
        self.player_game_clients.append(client)

    def add_bot_game_client(self, client):
        self.new_clients.remove(client)
        self.bot_game_clients.append(client)

    def add_bot(self, bot):
        self.bots.append(bot)

    def add_new_client(self, client):
        self.new_clients.append(client)

    def get_player_game_clients(self):
        client1 = self.player_game_clients[0]
        client2 = self.player_game_clients[1]
        self.player_game_clients.clear()
        return client1, client2

    def get_bot_game_clients(self):
        player = self.bot_game_clients.pop(0)
        bot = self.bots.pop(0)
        return player, bot

    def remove_client(self, client):
        if client in self.new_clients:
            self.new_clients.remove(client)


class Server:
    _games = []
    _numbers_to_letters = {0: "a", 1: "b", 2: "c", 3: "d", 4: "e", 5: "f", 6: "g", 7: "h"}

    def __init__(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(('localhost', 65432))
        self.server_socket.listen(5)
        self.client_manager = ClientManager()
        print("Server is listening on localhost:65432")

        message_queue = Queue()
        threading.Thread(target=self.handle_messages, args=(message_queue,)).start()

        while True:
            client_socket, addr = self.server_socket.accept()
            self.client_manager.add_new_client(client_socket)

            threading.Thread(target=self.handle_client, args=(client_socket, addr, message_queue)).start()

    def handle_client(self, client_socket, client_address, message_queue):
        while True:
            try:
                message = client_socket.recv(1024).decode('utf-8')
                if not message:
                    continue
                message_queue.put((client_socket, message))
            except ConnectionResetError:
                client_socket.close()
                self.client_manager.remove_client(client_socket)
            except OSError:
                self.client_manager.remove_client(client_socket)

    def handle_messages(self, message_queue):
        while True:
            client_socket, message = message_queue.get()
            if message == "player_resigned":
                game = self.find_game(client_socket)
                game.remove(client_socket)
                for c in game[:-2]:
                    c.send("victory".encode("utf-8"))
                print(f"{game[-2]} выиграли")
                self._games.remove(game)
                break
            elif message == "play_with_bot":
                self.client_manager.add_bot_game_client(client_socket)
                clients = self.client_manager.get_bot_game_clients()
                threading.Thread(target=self.start_bot_game, args=(clients,)).start()
            elif message == "play_with_player":
                self.client_manager.add_player_game_client(client_socket)
                if len(self.client_manager.player_game_clients) == 2:
                    threading.Thread(target=self.start_player_game,
                                     args=(self.client_manager.get_player_game_clients(),)).start()
            elif message == "bot":
                self.client_manager.add_bot(client_socket)
                # print("bot")
            else:
                game = self.find_game(client_socket)
                print(f"Игра {game[-1]}: {game[-2]} сделали ход {self.reformat_move(message)}")
                for client in game[:-2]:
                    if client_socket != client:
                        client.send(message.encode("utf-8"))
                game[-2] = "Белые" if game[-2] == "Черные" else "Черные"

    def start_bot_game(self, clients):
        player, bot = clients
        game = [player, bot, "Белые", len(self._games) + 1]
        self._games.append(game)
        sides = ["white", "black"]
        for client in game[:-2]:
            side = random.choice(sides)
            client.send(f"side={side}".encode("utf-8"))
            sides.remove(side)
        print(f"game for player {player} and bot {bot} started")

    def start_player_game(self, clients):
        client1, client2 = clients
        game = [client1, client2, "Белые", len(self._games) + 1]
        self._games.append(game)
        counter = 0
        sides = ["white", "black"]
        for c in game[:-2]:
            c.send(f"side={sides[counter]}".encode('utf-8'))
            counter += 1
        print(f"game for {client1} and {client2} started")

    def reformat_move(self, move):
        move_part1, move_part2 = move.split()[0], move.split()[1]
        reformed_move_part1 = f"{self._numbers_to_letters[int(move_part1.split(',')[0])]}{8 - int(move_part1.split(',')[1])}"
        reformed_move_part2 = f"{self._numbers_to_letters[int(move_part2.split(',')[0])]}{8 - int(move_part2.split(',')[1])}"
        return f"{reformed_move_part1} - {reformed_move_part2}"

    def find_game(self, client_socket):
        for game in self._games:
            if client_socket in game[:-2]:
                return game
        return None
