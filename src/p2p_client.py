import socket
import threading
import json
import sys
from colorama import Fore
from db import DB

db = DB()

USAGE = """
/help Prints available commands"
/create_room [NAME] creates a chat room with NAME
/join_room [NAME] joins the chat room with specified NAME
/list_rooms lists all available chat rooms
/disconnect disconnects current user
"""

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
        self.room = ""
        self.server_host = server_host
        self.server_port = server_port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.peers = {}
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

    def send_message_to_peers(self, message):
        """
        Send a message to peers

        Args:
        - message (str): The message to be sent.
        """
        try:
            for peer_socket in self.peers:
                peer_socket.sendall(message.encode())
        except ConnectionError:
            print("Error sending message. Disconnected.")

    def receive_message(self):
        """
        Listen for incoming messages from the server.
        """
        try:
            while True:
                try:
                    message, sender_address = self.udp_socket.recvfrom(1024)
                    print(f"Recieved message: {message} from {sender_address}")
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

    def sign_up(self):
        """
        Register a new user by sending registration credentials to the database

        Args:
        - creds (str): User credentials in the format 'username:password'.
        """
        username = input("Username: ")
        password = input("Password: ")
        ip, port = self.udp_socket.getsockname()
        user = {
            "username": username,
            "password": password,
            "ip": ip,
            "port": port,
        }
        self.username = user["username"]
        db.register(user)

    def login(self):
        """
        Send login credentials to the server for authentication.

        Args:
        - creds (str): User credentials in the format 'username:password'.
        """
        username = input("Username: ")
        password = input("Password: ")
        login_payload = {
            "username": username,
            "password": password,
        }
        self.username = username
        return db.login_user(login_payload)

    def disconnect(self):
        """
        Disconnect from the server and log out the user.
        """
        self.client_socket.close()
        db.user_logout(self.username)

# Usage example:
if __name__ == "__main__":
    HOST = '127.0.0.1'
    PORT = 12345

    chat_client = Client(HOST, PORT)
    chat_client.connect()
    print("│───────────────────────────────────────│")
    print("│──────── Welcome to chatshell ─────────│")
    print("│───────────────────────────────────────│")
    logged_in = False

    while not logged_in:
        print("Menu:")
        print("1. Signup")
        print("2. Login")
        print("3. Exit")
        choice = input("Enter your choice (1/2/3): ")
        if choice == '1':
            chat_client.sign_up()
        elif choice == '2':
            logged_in = chat_client.login()
        elif choice == '3':
            print("Exiting...")
            sys.exit(0)
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")

    # Start the separate thread for receiving messages
    chat_client.start_receive_thread()

    # Loop for sending messages
    while True:
        try:
            message = input(f"{Fore.WHITE}> ")
            message = message.split(' ')
            if message[0] == "/help":
                print(USAGE)
            elif message[0] == "/create_room":
                db.add_chat_room(message[1])
            elif message[0] == "/join_room":
                ip, port = chat_client.udp_socket.getsockname()
                db.add_peer(message[1], chat_client.username, {"ip": ip, "port": port })
                chat_client.room = message[1]
                peers = db.get_chat_room_peers(message[1])
                chat_client.peers = peers
                if peers is not None:
                    for k, v in peers.items():
                        print(k, v)
                print(f"[CLIENT]: {peers}")
                # print(f"[CLIENT]: {peer.ip} {peer.port}")
            elif message[0] == "/logout":
                print("loggin out...")
                sys.exit(1)
            else:
                if chat_client.room != "":
                    msg = input()
                    peers = db.get_chat_room_peers(chat_client.room)
                    if peers:
                        for name, peer in peers.items():
                            print(f"[CLIENT]: {peer}")
                            if name != chat_client.username:
                                chat_client.udp_socket.sendto(msg.encode(), (peer["ip"], peer["port"]))
                                print("Sent stuff!!!")
            # chat_client.send_message(message)
        except KeyboardInterrupt:
            chat_client.disconnect()
            sys.exit(1)
