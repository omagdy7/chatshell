from math import log
import socket
import threading
import random
import sys
from colorama import Fore
from db import DB

db = DB()

colors = [(Fore.RED,     False),
          (Fore.GREEN,   False),
          (Fore.YELLOW,  False),
          (Fore.BLUE,    False),
          (Fore.MAGENTA, False),
          (Fore.CYAN,    False)]

def reset_colors():
    for item in colors:
        item = (item[0], False)

def get_color() -> str:
    # To avoid infinte loop reset colors and reuse them if the clients are more than len(colors)
    if all(item[1] for item in colors):
        reset_colors()

    rand_color = colors[random.randint(0, len(colors) - 1)]
    while rand_color[1]:
        rand_color = colors[random.randint(0, len(colors) - 1)]
    rand_color = (rand_color[0], True)
    return rand_color[0]

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
        self.color = ""
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


    def connect_udp(self):
        """
        Establish a connection with the server.
        """
        try:
            self.udp_socket.bind(('127.0.0.1', random.randint(8000, 10000)))
        except OSError as e:
            print(f"Error occurred: {e}")

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
        peers = db.get_chat_room_peers(chat_client.room)
        if peers:
            for name, peer in peers.items():
                if name != chat_client.username and db.is_user_online(name):
                    chat_client.udp_socket.sendto(message.encode(), (peer["ip"], peer["port"]))

    def receive_message(self):
        """
        Listen for incoming messages from the server.
        """
        try:
            while True:
                try:
                    message, _ = self.udp_socket.recvfrom(1024)
                    message = message.decode('utf-8')
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
        self.udp_socket.close()
        db.user_logout(self.username)



def join_room(name, chat_client):
    if chat_client.room != name:
        ip, port = chat_client.udp_socket.getsockname()
        db.add_peer(name, chat_client.username, {"ip": ip, "port": port })
        chat_client.room = name
        peers = db.get_chat_room_peers(name)
        chat_client.peers = peers
        msg = f"{chat_client.username} joined the room!\n> \033[39m"
        chat_client.send_message_to_peers(msg)
    else:
        print("You are already in this room.")

def create_room(name):
    db.add_chat_room(name)

def help():
    print(USAGE)

def logout(chat_client):
    msg = f"{chat_client.username} left the room :(\033[39m"
    chat_client.send_message_to_peers(msg)
    db.set_user_online_status(chat_client.username, False)
    print("logging out...")
    chat_client.disconnect()
    sys.exit(1)

def menu(logged_in):
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

def init_client():
    HOST = '127.0.0.1'
    PORT = 12345

    chat_client = Client(HOST, PORT)
    chat_client.connect()
    chat_client.connect_udp()

    print("│───────────────────────────────────────│")
    print("│──────── Welcome to chatshell ─────────│")
    print("│───────────────────────────────────────│")

    # Start the separate thread for receiving messages
    chat_client.start_receive_thread()
    return chat_client

COMMANDS = {
    "/help": help,
    "/create_room": create_room,
    "/join_room": join_room,
    "/logout": logout,
}

def command(command, name, chat_client):
    COMMANDS[command]



# Usage example:
if __name__ == "__main__":
    chat_client = init_client()
    logged_in = False
    menu(logged_in)


    # Loop for sending messages
    while True:
        try:
            message = input(f"{Fore.WHITE}> ")
            msg = message
            message = message.split(' ')
            if message[0] == "/help":
                help()
            elif message[0] == "/create_room":
                create_room(message[1])
            elif message[0] == "/join_room":
                join_room(message[1], chat_client)
            elif message[0] == "/logout":
                logout(chat_client)
            else:
                if chat_client.room != "":
                    if chat_client.color == "":
                        chat_client.color = get_color()
                    msg = f"{chat_client.color}{chat_client.username}: {msg}\033[39m"
                    chat_client.send_message_to_peers(msg)
        except KeyboardInterrupt:
            chat_client.disconnect()
            sys.exit(1)
