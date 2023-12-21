import hashlib
from pymongo import MongoClient

# Includes database operations
class DB:
    # db initializations
    def __init__(self):
        self.client = MongoClient('mongodb://localhost:27017/')
        self.db = self.client['p2p-chat']


    # checks if an account with the username exists
    def is_account_exist(self, username):
        return self.db.accounts.find_one({'username': username}) is not None

    # registers a user
    def register(self, username, password):
        hashed_pass = hashlib.sha256(password.encode('utf-8')).hexdigest()
        account = {
            "username": username,
            "password": hashed_pass 
        }
        self.db.accounts.insert_one(account)


    # retrieves the password for a given username
    def get_password(self, username):
        return self.db.accounts.find_one({"username": username})["password"]


    # checks if an account with the username online
    def is_account_online(self, username):
        return self.db.online_peers.find_one({"username": username}) is not None

    def auth_user(self, username, password):
        print("Authenticating user")
        if self.is_account_exist(username):
            hashed_pass = hashlib.sha256(password.encode('utf-8')).hexdigest()
            if self.get_password(username) == hashed_pass:
                return True

        return False

    
    # logs in the user
    def login_user(self, username, ip, port):
        online_peer = {
            "username": username,
            "ip": ip,
            "port": port
        }
        self.db.online_peers.insert(online_peer)

    def user_login(self, username, ip, port):
        online_peer = {
            "username": username,
            "ip": ip,
            "port": port
        }
        self.db.online_peers.insert(online_peer)
    

    # logs out the user 
    def user_logout(self, username):
        self.db.online_peers.remove({"username": username})
    

    # retrieves the ip address and the port number of the username
    def get_peer_ip_port(self, username):
        res = self.db.online_peers.find_one({"username": username})
        return (res["ip"], res["port"])
