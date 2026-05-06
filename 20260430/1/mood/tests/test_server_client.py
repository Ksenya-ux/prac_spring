import multiprocessing
import socket
import time
import unittest

from mood.common.constants import DEFAULT_HOST, DEFAULT_PORT
from mood.server.server import serve


class TestClientServerCommands(unittest.TestCase):

    def setUp(self):
        self.proc = multiprocessing.Process(target=serve)
        self.proc.start()
        time.sleep(1)

        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((DEFAULT_HOST, DEFAULT_PORT))

        self.send("login tester")
        self.read_line()  # Hello, tester
        self.read_line()  # tester entered the MUD

    def tearDown(self):
        self.s.close()
        self.proc.terminate()
        self.proc.join()

    def send(self, command):
        self.s.sendall((command + "\n").encode())

    def read_line(self):
        data = b""
        while not data.endswith(b"\n"):
            chunk = self.s.recv(4096)
            if not chunk:
                break
            data += chunk
        return data.decode().strip().replace("\\n", "\n")

    def test_add_monster_near_player(self):
        self.send('addmon default hello "Hi!" hp 20 coords 1 0')
        response = self.read_line()

        self.assertIn("tester added monster default to (1, 0)", response)
        self.assertIn("saying Hi!", response)
        self.assertIn("with 20 hp", response)

    def test_move_to_monster_shows_hello(self):
        self.send('addmon default hello "Hi!" hp 20 coords 1 0')
        self.read_line()

        self.send("move right")
        response = self.read_line()

        self.assertIn("Moved to (1, 0)", response)
        self.assertIn("Hi!", response)

    def test_attack_monster(self):
        self.send('addmon default hello "Hi!" hp 20 coords 1 0')
        self.read_line()

        self.send("move right")
        self.read_line()

        self.send("attack default axe")
        response = self.read_line()

        self.assertIn("tester attacked default with axe", response)
        self.assertIn("damage 20 hp", response)
        self.assertIn("default died", response)


if __name__ == "__main__":
    unittest.main()
