import hashlib
from pymongo import MongoClient
import logging

logging.basicConfig(level=logging.INFO, filename='./logs/logs.log', format='%(asctime)s - %(levelname)s - %(message)s')

# Includes database operations
class DB:
    # db initializations
    def __init__(self):
        self.client = MongoClient('mongodb://localhost:27017/')
        self.db = self.client['p2p-chat']


    # checks if an account with the username exists
    def is_account_exist(self, username):
        return self.db.users.find_one({'username': username}) is not None

    # registers a user
    def register(self, user):
        hashed_pass = hashlib.sha256(user["password"].encode('utf-8')).hexdigest()
        user = {
            "username": user["username"],
            "password": hashed_pass,
            "ip": user["ip"],
            "port": user["port"],
            "online": False,
        }
        result = self.db.users.insert_one(user)
        if result.inserted_id:
            logging.info("[DB] User inserted successfully with ID:", result.inserted_id)
        else:
            logging.info("[DB] Failed to insert user.")


    # retrieves the password for a given username
    def get_password(self, username):
        user = self.db.users.find_one({"username": username})
        if user:
            return user["password"]
        else:
            logging.info(f"[DB] User {username} wasn't found")


    # checks if an account with the username online
    def is_user_online(self, username):
        user = self.db.users.find_one({"username": username}, {"_id": 0, "online": 1})
        if user:
            return user["online"]
        else: 
            return False

    def set_user_online_status(self, username, status):
        user = self.db.users.find_one({"username": username})
        if user:
            self.db.users.update_one(
                {"username": user["username"]},
                {"$set": {"online": status}}
            )
            logging.info(f"[DB] Set {username} status to {status}")
        else:
            logging.info(f"[DB] User {username} wasn't found")


    def auth_user(self, username, password):
        logging.info(f"[DB] Authenticating user {username}")
        if self.is_account_exist(username):
            hashed_pass = hashlib.sha256(password.encode('utf-8')).hexdigest()
            if self.get_password(username) == hashed_pass:
                return True
        return False
    
    # logs in the user
    def login_user(self, creds):
        logging.info("[DB] Authenticating user")
        if self.is_account_exist(creds["username"]):
            hashed_pass = hashlib.sha256(creds["password"].encode('utf-8')).hexdigest()
            if self.get_password(creds["username"]) == hashed_pass:
                self.set_user_online_status(creds["username"], True)
                return True
            else:
                logging.info(f"[DB] Wrong password")
                return False
        else:
            logging.info(f"[DB] {creds['username']} doesn't exist")
            return False

    # logs out the user 
    def user_logout(self, username):
        self.set_user_online_status(username, False)

    def add_chat_room(self, chat_room_name):
        chat_room = {
            "name": chat_room_name,
            "peers": {}
        }
        logging.info(f"[DB] Added {chat_room_name} room to chatrooms")
        self.db.chatrooms.insert_one(chat_room)
    
    def get_chatrooms(self):
        result = self.db.chatrooms.find({}, {'name': 1, '_id': 0})
        chatroom_names = [doc['name'] for doc in result]
        return chatroom_names


    def get_chat_room_peers(self, chat_room_name):
        # Find the chat room by its name
        chat_room = self.db.chatrooms.find_one({"name": chat_room_name})

        if chat_room:
            return chat_room["peers"]
        else:
            logging.info(f"[DB] room {chat_room_name} wasn't found")
            return None

    def add_peer(self, chat_room_name, peer_name, peer):
        # Find the chat room by its name
        chat_room = self.db.chatrooms.find_one({"name": chat_room_name})

        if chat_room:
            self.db.chatrooms.update_one(
                {"_id": chat_room["_id"]},
                {"$set": {f"peers.{peer_name}": peer}}
            )
            logging.info(f"[DB] Added {peer_name} to the {chat_room_name} chat room.")
        else:
            logging.info(f"[DB] Chat room {chat_room_name} not found.")

    # retrieves the ip address and the port number of the username
    def get_peer_ip_port(self, chat_room_name, username):
        room = self.db.chatrooms.find_one({"name": chat_room_name})
        if room:
            peer = room["peers"][username]
            if peer:
                return (peer["ip"], peer["port"])
            else:
                logging.info(f"[DB] peer {username} wasn't found")
        else:
            logging.info(f"[DB] room {chat_room_name} wasn't found")
