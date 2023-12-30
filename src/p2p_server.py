import json
import socket
import logging
from concurrent.futures import ThreadPoolExecutor
from db import DB

db = DB()

logging.basicConfig(level=logging.INFO, filename='./logs/server.log', format='%(asctime)s - %(levelname)s - %(message)s')

class P2PServer():
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

    def serve(self):
        """
        Start the server, listen for incoming connections, and handle them using a thread pool.
        """
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()

        logging.info(f"[SERVER]: Listening on {self.host}:{self.port}")

        with ThreadPoolExecutor() as executor:
            while True:
                try:
                    client_socket, client_address = self.server_socket.accept()
                    logging.info(f"[SERVER]: Connection established with {client_address}")

                    # Submit the handle_client function to the thread pool
                    executor.submit(self.handle_client, client_socket)
                except KeyboardInterrupt:
                    self.stop()


    def handle_client(self, client_socket):
        """
        Handle client connections and messages.

        Args:
        - client_socket (socket): Socket object representing the client connection.
        - client_address (tuple): Tuple containing client's IP address and port.
        """
        while True:
            data = client_socket.recv(1024).decode()
            data = json.loads(data)
            if data["command"] == "join_room":
                logging.info(f"[SERVER]: Sending notification to all peers in the chat room to referesh their peers")
                room_name = data["chat_room_name"]
                if room_name not in self.chat_rooms:
                    self.chat_rooms[room_name] = []
                self.chat_rooms[room_name].append(client_socket)
                for sock in self.chat_rooms[data["chat_room_name"]]:
                    sock.sendall(f"refresh:{data['chat_room_name']}".encode())
                data = {}
            elif data["command"] == "disconnect":
                logging.info(f"[SERVER]: Sending notification to all peers in the chat room to remove {data['username']}")
                for sock in self.chat_rooms[data["chat_room_name"]]:
                    if sock != client_socket:
                        sock.sendall(f"delete:{data['username']}".encode())
                data = {}
            else:
                logging.info(f"[SERVER]: That's not a valid command")

    def stop(self):
        self.server_socket.close()

if __name__ == "__main__":
    HOST = '127.0.0.1'
    PORT = 12345

    chat_server = P2PServer(HOST, PORT)
    chat_server.serve()
