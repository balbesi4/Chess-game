import socket
import threading
from queue import Queue


class Server:
    _clients = []
    _games = []

    def __init__(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(('localhost', 65432))
        self.server_socket.listen(5)
        print("Server is listening on localhost:65432")

        message_queue = Queue()
        threading.Thread(target=self.handle_messages, args=(message_queue,)).start()

        while True:
            client_socket, addr = self.server_socket.accept()
            print(f"{addr} connected to server")
            self._clients.append(client_socket)

            if len(self._clients) == 2:
                threading.Thread(target=self.start_game, args=(self._clients[0], self._clients[1])).start()
                self._clients.clear()

            threading.Thread(target=self.handle_client, args=(client_socket, addr, message_queue)).start()

    def handle_client(self, client_socket, client_address, message_queue):
        while True:
            message = client_socket.recv(1024).decode('utf-8')
            if not message:
                continue

            if message == "player_resigned":
                print(f"Received message from {client_address}: {message}")
            message_queue.put((client_socket, message))

        client_socket.close()
        print(f"Connection closed with {client_address}")

    def handle_messages(self, message_queue):
        while True:
            client_socket, message = message_queue.get()
            if message == "player_resigned":
                game = self.find_game(client_socket)
                game.remove(client_socket)
                for c in game:
                    c.send("victory".encode("utf-8"))
                    print(f"sent message victory to {c}")
                self._games.remove(game)
                break
            else:
                print(f"Received chess move: {message}")
                game = self.find_game(client_socket)
                for client in game:
                    if client_socket != client:
                        client.send(message.encode("utf-8"))
                        print(f"sent message '''{message}''' to {client}")

    def start_game(self, client1, client2):
        game = [client1, client2]
        self._games.append(game)
        counter = 0
        sides = ["white", "black"]
        for c in game:
            c.send(f"side={sides[counter]}".encode('utf-8'))
            counter += 1
        print(f"game for {client1} and {client2} started")

    def find_game(self, client_socket):
        for game in self._games:
            if client_socket in game:
                return game
