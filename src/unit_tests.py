import unittest
import threading
import socket
from unittest.mock import patch, Mock
from p2p_client import logout
from p2p_client import P2PClient, LoginState, db

class TestP2PClient(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Initialize the P2PClient object
        cls.chat_client = P2PClient('test_host', 12345)

    def test_initialization(self):
        # Test the initial state of the client
        self.assertIsNone(self.chat_client.username)
        self.assertEqual(self.chat_client.room, "")
        self.assertEqual(self.chat_client.color, "")
        self.assertEqual(self.chat_client.server_host, 'test_host')
        self.assertEqual(self.chat_client.server_port, 12345)
        self.assertIsNotNone(self.chat_client.client_socket)
        self.assertIsNotNone(self.chat_client.udp_socket)
        self.assertDictEqual(self.chat_client.peers, {})
        self.assertIsInstance(self.chat_client.receive_thread, threading.Thread)
        self.assertIsInstance(self.chat_client.receive_peer_thread, threading.Thread)

    @patch('p2p_client.DB')
    def test_login_success(self, mock_db):
        # Test the login method of the client (successful login)
        mock_input = Mock(side_effect=["test", "test"])
        with patch('builtins.input', mock_input):
            mock_db.is_user_online.return_value = False
            mock_db.login_user.return_value = True
            login_state = self.chat_client.login()

        self.assertEqual(login_state, LoginState.LOGIN_SUCC)

    @patch('p2p_client.DB')
    def test_login_user_already_online(self, mock_db):
        # Test the login method of the client (user already logged in)
        mock_input = Mock(side_effect=["test", "test"])
        with patch('builtins.input', mock_input):
            mock_db.is_user_online.return_value = True
            login_state = self.chat_client.login()

        self.assertEqual(login_state, LoginState.LOGGED_IN)

    @patch('p2p_client.DB')
    def test_login_fail(self, mock_db):
        # Test the login method of the client (login fails)
        mock_input = Mock(side_effect=["test", "wrong password"])
        with patch('builtins.input', mock_input):
            mock_db.is_user_online.return_value = False
            mock_db.login_user.return_value = False
            login_state = self.chat_client.login()

        self.assertEqual(login_state, LoginState.LOGIN_FAIL)

    @patch('p2p_client.DB')
    def test_logout(self):
        # Test the logout method of the client
        self.chat_client.username = "test"
        self.chat_client.room = "test_room"

        login_state = [LoginState.LOGGED_IN]

        logout(self.chat_client, login_state)

        self.assertEqual(login_state[0], LoginState.LOGGED_OUT)

    # Add more test methods for other functionalities...
    
if __name__ == '__main__':
    unittest.main()
