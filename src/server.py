# DONE: User Registraion and Login
# DONE: Implement Basic Messeaging Functionality
# DONE: Implement storing a hash of the password instead of plain text
# DONE: Fix get_color bug it will enter infinite loop if we have more than 6 clients
# TODO: Store online clients in database instead of holding them as an object in the server class
# TODO: When a client closes the connection remove him from current online clients
# TODO: Find a way to make the database handle authentication

import socket
from colorama import Fore
import hashlib
import random
from concurrent.futures import ThreadPoolExecutor
from db import DB

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
        self.clients = {}
        self.db = DB()

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
            # User already authed
            if client_socket in self.clients.values():
                message = client_socket.recv(1024).decode()
                self.broadcast_message(client_socket, message)
            # User isn't authed
            else:
                self.handle_auth(client_socket, client_address)

    def broadcast_message(self, client_socket, message):
        """
        Broadcast a message from one client to all other connected clients.

        Args:
        - client_socket (socket): Socket object representing the sender.
        - message (str): The message to be broadcasted.
        """
        # TODO: Handle the case when get_key_from_value returns None
        username, _, color = get_key_from_value(self.clients, client_socket).split(':')
        for sock in self.clients.values():
            if sock != client_socket:
                # \033[39m just resets the color is a special code that resets the color
                sock.sendall(f"{color}{username}: {message}\033[39m".encode())

    def handle_auth(self, client_socket, client_address):
        """
        Handle authentication for new clients attempting to connect to the server.

        Args:
        - client_socket (socket): Socket object representing the client connection.
        - client_address (tuple): Tuple containing client's IP address and port.
        """
        creds = client_socket.recv(1024).decode()
        username, password = creds.split(':')
        if self.authenticate_user(username, password):
            # If authenticated, add the client to the dictionary of connected clients
            client_id = f"{username}:{str(client_address)}:{str(get_color())}"
            self.clients[client_id] = client_socket

            # Send a welcome message to in the chat room
            for sock in self.clients.values():
                sock.sendall(f"Welcome to the chat! {username}".encode())

        else:
            # If not authenticated, close the connection
            print("[LOG]: Authentication Failed.")
            client_socket.sendall("Authentication failed. Closing connection.".encode())
            client_socket.close()

    def authenticate_user(self, username, password):
        """
        Authenticate a user based on the provided username and password.

        Args:
        - username (str): The username to be authenticated.
        - password (str): The password associated with the username.

        Returns:
        - bool: True if authentication succeeds, False otherwise.
        """
        print("[LOG]: Authenticating user")
        if self.db.is_account_exist(username):
            hashed_pass = hashlib.sha256(password.encode('utf-8')).hexdigest()
            if self.db.get_password(username) == hashed_pass:
                print("[LOG]: Authentication was succssful")
                return True
        return False



    def stop(self):
        self.server_socket.close()

# Usage example:
if __name__ == "__main__":
    HOST = '127.0.0.1'  # Replace with your server's IP address
    PORT = 12345         # Replace with your desired port number

    chat_server = Server(HOST, PORT)
    chat_server.serve()
