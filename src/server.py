# TODO: User Registraion and Login
# TODO: Implement Basic Messeaging Functionality

import socket
from concurrent.futures import ThreadPoolExecutor
from db_mongo import DB

def get_key_from_value(dictionary, search_value):
    for key, value in dictionary.items():
        if value == search_value:
            return key
    return None  # Return None if the value is not found

class Server():
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clients = {}
        self.db = DB()

    def serve(self):
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()

        print(f"Server is listening on {self.host}:{self.port}")

        with ThreadPoolExecutor() as executor:
            while True:
                client_socket, client_address = self.server_socket.accept()
                print(f"Connection established with {client_address}")

                # Submit the handle_client function to the thread pool
                executor.submit(self.handle_client, client_socket, client_address)

    def handle_client(self, client_socket, client_address):
        while True:
            # User already authed
            if client_socket in self.clients.values():
                message = client_socket.recv(1024).decode()
                self.broadcast_message(client_socket, message)

            # User isn't authed
            else:
                self.handle_auth(client_socket, client_address)

    def broadcast_message(self, client_socket, message):
            username, _ = get_key_from_value(self.clients, client_socket).split('_')
            for sock in self.clients.values():
                sock.sendall(f"{username}: {message}".encode())

    def handle_auth(self, client_socket, client_address):
            creds = client_socket.recv(1024).decode()
            username, password = creds.split('\n')
            if self.authenticate_user(username, password):
                # If authenticated, add the client to the dictionary of connected clients
                client_id = username + '_' + str(client_address)
                self.clients[client_id] = client_socket

                # Send a welcome message to in the chat room
                for sock in self.clients.values():
                    sock.sendall(f"Welcome to the chat! {username}".encode())

            else:
                # If not authenticated, close the connection
                print("Authentication failed.")
                client_socket.sendall("Authentication failed. Closing connection.".encode())
                client_socket.close()

    def authenticate_user(self, username, password):
        print("Authenticating user")
        if self.db.is_account_exist(username):
            if self.db.get_password(username) == password:
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
