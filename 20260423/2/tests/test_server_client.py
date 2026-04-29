import unittest
from unittest.mock import patch

from mood.client.client import MUD


class TestClientCommandMocks(unittest.TestCase):

    def make_client(self):
        with patch.object(MUD, "_run_network", return_value=None):
            client = MUD("tester")
        client.loop.close()
        return client

    def run_client_with_input(self, commands):
        client = self.make_client()

        with patch("builtins.input", side_effect=commands + ["EOF"]), \
             patch.object(client, "send_line") as mock_send_line:
            client.cmdloop()

        return mock_send_line

    def test_move_first_coords(self):
        mock_send = self.run_client_with_input(["move 1 2"])
        mock_send.assert_called_once_with("moveabs 1 2")

    def test_move_second_coords(self):
        mock_send = self.run_client_with_input(["move 5 7"])
        mock_send.assert_called_once_with("moveabs 5 7")

    def test_attack_first_params(self):
        mock_send = self.run_client_with_input(["attack default with axe"])
        mock_send.assert_called_once_with("attack default axe")

    def test_attack_second_params(self):
        mock_send = self.run_client_with_input(["attack dragon with spear"])
        mock_send.assert_called_once_with("attack dragon spear")

    def test_invalid_move_params(self):
        mock_send = self.run_client_with_input(["move 1"])
        mock_send.assert_not_called()


if __name__ == "__main__":
    unittest.main()
