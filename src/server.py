# TODO: User Registraion and Login
# TODO: Implement Basic Messeaging Functionality

import socket
import threading
from db import DB

# Set up a socket to listen for incoming connections.
# Initialize data structures to store user credentials (e.g., usernames and passwords).
class Server():
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clients = {}

    def serve(self):
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()

        print(f"Server is listening on {self.host}:{self.port}")

        while True:
            client_socket, client_address = self.server_socket.accept()
            print(f"Connection established with {client_address}")

            # Create a new thread to handle the client connection
            client_thread = threading.Thread(target=self.handle_client, args=(client_socket, client_address))
            client_thread.start()

    def handle_client(self, client_socket, client_address):
        # Receive username and password from the client
        creds = client_socket.recv(1024).decode()
        username, password = creds.split('\n')

        # Implement user authentication logic here (for example, a basic check)
        if self.authenticate_user(username, password):
            # If authenticated, add the client to the dictionary of connected clients
            self.clients[username] = client_socket
            print(f"{username} connected.")

            # Example: Send a welcome message to the client
            client_socket.sendall(f"Welcome to the chat! {username}".encode())

        else:
            # If not authenticated, close the connection
            print("Authentication failed.")
            client_socket.sendall("Authentication failed. Closing connection.".encode())
            client_socket.close()

    def authenticate_user(self, username, password):
        db = DB()
        if username in db.credentials:
            if db.get_password(username) == password:
                return True

        return False



    def stop(self):
        self.server_socket.close()

# # Usage example:
# if __name__ == "__main__":
#     HOST = '127.0.0.1'  # Replace with your server's IP address
#     PORT = 12345         # Replace with your desired port number
#
#     chat_server = Server(HOST, PORT)
#     chat_server.serve()
