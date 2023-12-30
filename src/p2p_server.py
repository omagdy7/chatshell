import socket
from colorama import Fore
import random
from concurrent.futures import ThreadPoolExecutor
from db import DB

db = DB()

USAGE = """
/help Prints available commands"
/create_room [NAME] creates a chat room with NAME
/join_room [NAME] joins the chat room with specified NAME
/list_rooms lists all available chat rooms
/disconnect disconnects current user
"""

class ChatRoom():
    def __init__(self, name):
        self.name = name
        self.peers = []

    def add_peer(self, peer):
        self.peers.append(peer)

    def remove_peer(self, peer):
        self.peers.remove(peer)

colors = [(Fore.RED,     False),
          (Fore.GREEN,   False),
          (Fore.YELLOW,  False),
          (Fore.BLUE,    False),
          (Fore.MAGENTA, False),
          (Fore.CYAN,    False)]

def reset_colors():
    for item in colors:
        item = (item[0], False)

def get_color():
    # To avoid infinte loop reset colors and reuse them if the clients are more than len(colors)
    if all(item[1] for item in colors):
        reset_colors()

    rand_color = colors[random.randint(0, len(colors) - 1)]
    while rand_color[1]:
        rand_color = colors[random.randint(0, len(colors) - 1)]
    rand_color = (rand_color[0], True)
    return rand_color[0]



def get_key_from_value(dictionary, search_value):
    for key, value in dictionary.items():
        if value == search_value:
            return key
    return None  # Return None if the value is not found

class Server():
    def __init__(self, host, port):
        """
        Initialize the Server class.

        Args:
        - host (str): The host IP address.
        - port (int): The port number to listen on.
        """
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.chat_rooms = {}
        self.clients = {}

    def serve(self):
        """
        Start the server, listen for incoming connections, and handle them using a thread pool.
        """
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()

        print(f"[LOG]: Listening on {self.host}:{self.port}")

        with ThreadPoolExecutor() as executor:
            while True:
                try:
                    client_socket, client_address = self.server_socket.accept()
                    print(f"[LOG]: Connection established with {client_address}")

                    # Submit the handle_client function to the thread pool
                    executor.submit(self.handle_client, client_socket, client_address)
                except KeyboardInterrupt:
                    self.stop()


    def handle_client(self, client_socket, client_address):
        """
        Handle client connections and messages.

        Args:
        - client_socket (socket): Socket object representing the client connection.
        - client_address (tuple): Tuple containing client's IP address and port.
        """
        while True:
            message = client_socket.recv(1024).decode().split(' ')
            if message[0] == "/help":
                client_socket.sendall(USAGE.encode())

            elif message[0] == "/create_room":
                print(f"[LOG]: Client created room {message[1]} - {client_address}")
                db.add_chat_room(message[1])
                self.chat_rooms[message[1]] = ChatRoom(message[1])
                self.chat_rooms[message[1]].add_peer(client_socket)

            elif message[0] == "/join_room":
                print(f"[LOG]: Client joined room {message[1]} - {client_socket.getpeername()} {client_address}")
                self.chat_rooms[message[1]].add_peer(client_socket)
                for peer in self.chat_rooms[message[1]].peers:
                    print(f"[LOG]: peer.getpeername() {peer.getpeername()}")
                    if peer.getpeername()[1] != client_address[1]:
                        print(f"[log]: sending peer {peer.getpeername()[0]} - {peer.getpeername()[1]}")
                        client_socket.sendall(f"recieved peer:\n peer_address: {peer.getpeername()[0]} peer_port: {peer.getpeername()[1]}".encode())

            elif message[0] == "/list_rooms":
                print(f"[LOG]: Avialable Rooms: {self.chat_rooms}")
                # client_socket.sendall(self.chat_rooms)
            elif message[0] == "/disconnect":
                pass

    def stop(self):
        self.server_socket.close()

# Usage example:
if __name__ == "__main__":
    HOST = '127.0.0.1'  # Replace with your server's IP address
    PORT = 12345         # Replace with your desired port number

    chat_server = Server(HOST, PORT)
    chat_server.serve()
