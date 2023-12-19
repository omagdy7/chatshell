from typing import Dict

class DB:
    _instance = None  # Private variable to store the instance
    credentials: Dict[str, str] = {}

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls, *args, **kwargs)
            cls._instance.credentials = {}  # Dictionary to store user credentials
        return cls._instance

    def add_user(self, username, password):
        self.credentials[username] = password

    def get_password(self, username):
        return self.credentials.get(username)
