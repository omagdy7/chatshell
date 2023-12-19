import socket
from db import DB

class Client:
    def __init__(self, server_host, server_port):
        self.server_host = server_host
        self.server_port = server_port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self):
        try:
            self.client_socket.connect((self.server_host, self.server_port))
            print(f"Connected to server at {self.server_host}:{self.server_port}")
        except ConnectionRefusedError:
            print("Connection refused. Make sure the server is running.")

    def send_message(self, message):
        try:
            self.client_socket.sendall(message.encode())
        except ConnectionError:
            print("Error sending message. Disconnected.")

    def receive_message(self):
        try:
            while True:
                message = self.client_socket.recv(1024).decode()
                print(f"Received message: {message}")
                if not message:
                    break
                print(f"Received message: {message}")
        except ConnectionError:
            print("Disconnected.")

    def sign_up(self, creds):
        username, password = creds.split('\n')
        db = DB()
        print(f"Signing up...: {username}")
        db.add_user(username, password)

    def login(self, creds):
        print("Loging in...")
        creds = "admin\npassword"
        self.send_message(creds)

    def disconnect(self):
        self.client_socket.close()

# Usage example:
if __name__ == "__main__":
    HOST = '127.0.0.1'  # Replace with the server's IP address
    PORT = 12345         # Replace with the server's port number

    chat_client = Client(HOST, PORT)
    chat_client.connect()
    creds = "admin\npassword"
    chat_client.sign_up(creds)
    chat_client.login(creds)

    # Example message sending and receiving (for demonstration)
    chat_client.receive_message()

    # Disconnect when done
    chat_client.disconnect()
