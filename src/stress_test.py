import concurrent.futures
import time
from p2p_client import P2PClient, create_room, join_room
HOST = '127.0.0.1'
PORT = 12345

# Function to simulate signup stress test
def signup_stress_test(username, password):
    chat_client = P2PClient(HOST, PORT)
    chat_client.connect()
    chat_client.connect_udp()

    # Simulate signup with provided username and password
    chat_client.sign_up_stress_test(username, password)

    chat_client.disconnect()

# Function to simulate login stress test
def login_stress_test(username, password):
    chat_client = P2PClient(HOST, PORT)
    chat_client.connect()
    chat_client.connect_udp()

    chat_client.login_stress_test(username, password)

    chat_client.disconnect()

def join_room_stress_test(username, password):
    chat_client = P2PClient(HOST, PORT)
    chat_client.connect()
    chat_client.connect_udp()

    chat_client.login_stress_test(username, password)
    join_room("stress_test_room", chat_client)
    msg = f"Stress test message"
    chat_client.send_message_to_peers(msg)


# Number of clients to simulate
num_clients = 1000

# List to hold concurrent client threads
client_threads = []

# Start time
start_time = time.time()

# create chat room for stress testing
create_room("stress_test_room")

# Simulate signup stress test concurrently
with concurrent.futures.ThreadPoolExecutor() as executor:
    for i in range(num_clients):
        username = f"test_user_{i}"
        password = f"password_{i}"
        client_threads.append(executor.submit(signup_stress_test, username, password))

# Wait for all client threads to complete
for thread in concurrent.futures.as_completed(client_threads):
    pass

# Simulate login stress test concurrently
with concurrent.futures.ThreadPoolExecutor() as executor:
    for i in range(num_clients):
        username = f"test_user_{i}"
        password = f"password_{i}"
        client_threads.append(executor.submit(join_room_stress_test, username, password))

# Wait for all client threads to complete
for thread in concurrent.futures.as_completed(client_threads):
    pass

# End time
end_time = time.time()

# Calculate total execution time
execution_time = end_time - start_time

print(f"Signup and loging in and joining rooms and sending messeages in room took : {execution_time} seconds with {num_clients}")
