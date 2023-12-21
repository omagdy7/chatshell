# TODO: Find a proper way to disconnect users(It currently spams messages to other when a user tries to diconnect)

import socket
import threading
from colorama import Fore
from db import DB

db = DB()

# Create a Client class to handle the client-side functionality of the chat application
class Client:
    def __init__(self, server_host, server_port):
        """
        Initialize the Client class.

        Args:
        - server_host (str): The server's host IP address.
        - server_port (int): The server's port number.
        """
        self.username = None
        self.server_host = server_host
        self.server_port = server_port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.receive_thread = threading.Thread(target=self.receive_message)

    def connect(self):
        """
        Establish a connection with the server.
        """
        try:
            self.client_socket.connect((self.server_host, self.server_port))
            print(f"Connected to server at {self.server_host}:{self.server_port}")
        except ConnectionRefusedError:
            print("Connection refused. Make sure the server is running.")

    def send_message(self, message):
        """
        Send a message to the server.

        Args:
        - message (str): The message to be sent.
        """
        try:
            self.client_socket.sendall(message.encode())
        except ConnectionError:
            print("Error sending message. Disconnected.")

    def receive_message(self):
        """
        Listen for incoming messages from the server.
        """
        try:
            while True:
                try:
                    message = self.client_socket.recv(1024).decode()
                    print(f"{message}")
                    if not message:
                        break
                except KeyboardInterrupt:
                    break
        except ConnectionError:
            print("Disconnected.")

    def start_receive_thread(self):
        """
        Start the thread for receiving messages.
        """
        self.receive_thread.start()

    def stop_receive_thread(self):
        """
        Stop the thread for receiving messages.
        """
        self.receive_thread.start()

    def sign_up(self, creds):
        """
        Register a new user by sending registration credentials to the server.

        Args:
        - creds (str): User credentials in the format 'username:password'.
        """
        username, password = creds.split(':')
        self.username = username
        db.register(username, password)

    def login(self, creds):
        """
        Send login credentials to the server for authentication.

        Args:
        - creds (str): User credentials in the format 'username:password'.
        """
        self.send_message(creds)

    def disconnect(self):
        """
        Disconnect from the server and log out the user.
        """
        self.client_socket.close()
        db.user_logout(self.username)

# Usage example:
if __name__ == "__main__":
    HOST = '127.0.0.1'  # Replace with the server's IP address
    PORT = 12345         # Replace with the server's port number

    chat_client = Client(HOST, PORT)
    chat_client.connect()
    username = input("Username: ")
    password = input("Password: ")
    print("----------------------------------------")
    creds = f"{username}:{password}"
    chat_client.sign_up(creds)
    chat_client.login(creds)

    # Start the separate thread for receiving messages
    chat_client.start_receive_thread()

    # Loop for sending messages
    while True:
        try:
            message = input(f"{Fore.WHITE}")
            chat_client.send_message(message)
        except KeyboardInterrupt:
            chat_client.disconnect()
            break
