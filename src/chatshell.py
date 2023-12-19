import threading
from server import Server
from client import Client

if __name__ == "__main__":
    SERVER_HOST = '127.0.0.1'  # Replace with your server's IP address
    SERVER_PORT = 12345         # Replace with your desired port number

    # Create instances of Server and Client
    chat_server = Server(SERVER_HOST, SERVER_PORT)
    chat_client = Client(SERVER_HOST, SERVER_PORT)

    # Run server and client on separate threads
    server_thread = threading.Thread(target=chat_server.serve)
    # Start the threads
    server_thread.start()

    chat_client.connect()
    creds = "admin\npassword"
    chat_client.sign_up(creds)
    chat_client.login(creds)



    # Example message sending and receiving (for demonstration)
    # chat_client.receive_message()


