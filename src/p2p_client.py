from enum import Enum
import os
import socket
import threading
import json
import random
from colorama import Fore
from db import DB

db = DB()

class LoginState(Enum):
    LOGGED_OUT = 0,
    LOGGED_IN  = 1,
    LOGIN_SUCC = 2,
    LOGIN_FAIL = 3,

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
class P2PClient:
    """
    Represents a client for a chat application.

    Attributes:
    - server_host (str): The hostname of the chat server.
    - server_port (int): The port number of the chat server.
    - username (str): The username of the client. Default is None.
    - room (str): The room the client is currently in. Default is an empty string.
    - color (str): The color associated with the client. Default is an empty string.
    - client_socket (socket.socket): The TCP socket used for client-server communication.
    - udp_socket (socket.socket): The UDP socket used for peer-to-peer communication.
    - peers (dict): A dictionary to store information about connected peers.
    - receive_thread (threading.Thread): Thread for receiving messages from the peers.
    - receive_peer_thread (threading.Thread): Thread for receiving peers from server
    """
    def __init__(self, server_host, server_port):
        self.username = None
        self.room = ""
        self.color = ""
        self.server_host = server_host
        self.server_port = server_port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.peers = {}
        self.receive_thread = threading.Thread(target=self.receive_message)
        self.receive_peer_thread = threading.Thread(target=self.recieve_peer_from_server)

    def connect(self):
        """
        Establish a connection with the server.
        """
        try:
            self.client_socket.connect((self.server_host, self.server_port))
        except ConnectionRefusedError:
            print("Connection refused. Make sure the server is running.")


    def connect_udp(self):
        """
        Bind the udp socket to a random port.
        """
        try:
            self.udp_socket.bind(('127.0.0.1', random.randint(8000, 60000)))
        except OSError as e:
            print(f"Error occurred: {e}")

    def send_message(self, payload):
        """
        Send a message to the server.

        Args:
        - payload (str): The payload to be sent.
        """
        try:
            self.client_socket.sendall(json.dumps(payload).encode('utf-8'))
        except ConnectionError:
            print("Error sending message. Disconnected.")

    def send_message_to_peers(self, message):
        """
        Send a message to peers

        Args:
        - message (str): The message to be sent.
        """
        for name, peer in self.peers.items():
            if name != chat_client.username and db.is_user_online(name):
                chat_client.udp_socket.sendto(message.encode(), (peer["ip"], peer["port"]))

    def recieve_peer_from_server(self):
        """
        Listen for incoming messages from the server.
        """
        try:
            while True:
                try:
                    message = self.client_socket.recv(1024).decode('utf-8').split(':')
                    if message[0] == "refresh":
                        self.peers = db.get_chat_room_peers(message[1])
                        msg = f"{self.username} joined the room!\033[39m"
                        self.send_message_to_peers(msg)
                    if message[0] == "delete":
                        del self.peers[message[1]]
                        msg = f"{self.username} left the room :(\033[39m"
                        self.send_message_to_peers(msg)
                    if not message:
                        break
                except KeyboardInterrupt:
                    break
        except ConnectionError:
            print("Disconnected.")

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
        self.receive_peer_thread.start()

    def sign_up_stress_test(self, username, password):
        """
        Register a new user by sending registration credentials to the database
        """
        ip, port = self.udp_socket.getsockname()
        user = {
            "username": username,
            "password": password,
            "ip": ip,
            "port": port,
        }
        self.username = user["username"]
        if db.is_account_exist(user["username"]):
            print(f"An account with username '{user['username']}' already exists try another username")
        else:
            db.register(user)

    def sign_up(self):
        """
        Register a new user by sending registration credentials to the database
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
        if db.is_account_exist(user["username"]):
            print(f"An account with username '{user['username']}' already exists try another username")
        else:
            db.register(user)

    def login_stress_test(self, username, password):
        """
        Send login credentials to the server for authentication.
        """
        login_payload = {
            "username": username,
            "password": password,
        }
        self.username = username
        if db.is_user_online(username):
            print(f"The account with username '{username}' is already logged in on some other device")
            return LoginState.LOGGED_IN
        else:
            if db.login_user(login_payload):
                return LoginState.LOGIN_SUCC
            else:
                return LoginState.LOGIN_FAIL

    def login(self):
        """
        Send login credentials to the server for authentication.
        """
        username = input("Username: ")
        password = input("Password: ")
        login_payload = {
            "username": username,
            "password": password,
        }
        self.username = username
        if db.is_user_online(username):
            print(f"The account with username '{username}' is already logged in on some other device")
            return LoginState.LOGGED_IN
        else:
            if db.login_user(login_payload):
                return LoginState.LOGIN_SUCC
            else:
                return LoginState.LOGIN_FAIL



    def disconnect(self):
        """
        Disconnect from the server and log out the user.
        """
        self.client_socket.close()
        self.udp_socket.close()
        db.user_logout(self.username)



def join_room(name, chat_client):
    """
    Joins a chat room if the client is not already in it.

    Args:
    - name (str): The name of the room to join.
    - chat_client (P2PClient): An instance of the ChatClient class.

    If the client is not in the specified room, it adds the client as a peer in the room,
    updates the client's room attribute, sends a join room command to the server,
    and notifies peers about the client joining.
    """
    if chat_client.room != name:
        ip, port = chat_client.udp_socket.getsockname()
        if name in db.get_chatrooms():
            db.add_peer(name, chat_client.username, {"ip": ip, "port": port })
            chat_client.room = name
            chat_client.send_message({"command": "join_room", "chat_room_name": name })
            msg = f"{chat_client.username} joined the room!\n> \033[39m"
            chat_client.send_message_to_peers(msg)
        else:
            print(f"Room with name {name} doesn't exist")

    else:
        print("You are already in this room.")

def list_rooms():
    """
    Prints a list of available chat rooms retrieved from the database.
    """
    if len(db.get_chatrooms()) == 0:
        print("There is no current rooms on the server try creating your own with /create_room your_room_name")
    for room in db.get_chatrooms():
        print(room)

def create_room(name):
    """
    Creates a new chat room.

    Args:
    - name (str): The name of the new chat room.
    """
    if db.add_chat_room(name):
        print(f"Room {name} was created succssefully.")
    else:
        print(f"Couldn't create room due to an error in db")

def help():
    """
    Displays usage information.
    """
    print(USAGE)

def logout(chat_client, login_state):
    """
    Logs out the user from the chat application.

    Args:
    - chat_client (P2PClient): An instance of the ChatClient class.

    Sends a leave message to peers, sets the user's online status to False,
    sends a disconnect command to the server, disconnects the client, and exits the system.
    """
    login_state[0] = LoginState.LOGGED_OUT
    msg = f"{chat_client.username} left the room :(\033[39m"
    chat_client.send_message_to_peers(msg)
    db.set_user_online_status(chat_client.username, False)
    chat_client.send_message({"command": "disconnect", "chat_room_name": chat_client.room, "username": chat_client.username })
    print("logging out...")
    chat_client.disconnect()
    db.user_logout(chat_client.username)

def menu(chat_client: P2PClient, login_state: list[LoginState]):
    """
    Provides a menu interface for user actions.

    Args:
    - chat_client (ChatClient): An instance of the ChatClient class.
    - login_state (bool): Indicates if the user is logged in or not.

    Displays a menu with options for signup, login, and exiting the system.
    """
    while login_state[0] == LoginState.LOGGED_OUT:
        print(login_state[0])
        print("Menu:")
        print("1. Signup")
        print("2. Login")
        print("3. Exit")
        choice = input("Enter your choice (1/2/3): ")
        if choice == '1':
            chat_client.sign_up()
        elif choice == '2':
            print("before", login_state[0])
            login_state[0] = chat_client.login()
            print("after", login_state[0])
            if login_state[0] == LoginState.LOGIN_FAIL:
                print("The username or password is incorrect")
        elif choice == '3':
            print("Exiting...")
            os._exit(0)
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")

def init_client():
    HOST = '127.0.0.1'
    PORT = 12345

    chat_client = P2PClient(HOST, PORT)
    chat_client.connect()
    chat_client.connect_udp()

    print("│───────────────────────────────────────│")
    print("│──────── Welcome to chatshell ─────────│")
    print("│───────────────────────────────────────│")

    # Start the separate thread for receiving messages
    chat_client.start_receive_thread()
    return chat_client

# Usage example:
if __name__ == "__main__":
    chat_client = init_client()
    login_state = [LoginState.LOGGED_OUT]

    # Loop for sending messages
    while True:
        try:
            if login_state[0] == LoginState.LOGGED_OUT or login_state[0] == LoginState.LOGGED_IN:
                menu(chat_client, login_state)
            else:
                message = input(f"{Fore.WHITE}> ")
                msg = message
                message = message.split(' ')
                if message[0] == "/help":
                    help()
                elif message[0] == "/create_room":
                    create_room(message[1])
                elif message[0] == "/join_room":
                    join_room(message[1], chat_client)
                elif message[0] == "/list_rooms":
                    list_rooms()
                elif message[0] == "/logout":
                    logout(chat_client, login_state)
                elif message[0][0] == '/':
                    print("That's not a valid command try one of these commands: ")
                    help()
                else:
                    if chat_client.room != "":
                        if chat_client.color == "":
                            chat_client.color = get_color()
                        msg = f"{chat_client.color}{chat_client.username}: {msg}\033[39m"
                        chat_client.send_message_to_peers(msg)
                    else:
                        print("""You can't message anyone because you are not in a room to join a room use the 
/join_room command and to see what rooms are avilable you can use the /list_rooms command
                            """)
        except KeyboardInterrupt:
            chat_client.disconnect()
            os._exit(1)
