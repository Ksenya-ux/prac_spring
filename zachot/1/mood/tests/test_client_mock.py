"""Tests for client command conversion without running a server."""

import unittest
from unittest.mock import patch

from mood.client.client import MUD


class TestClientCommandConversion(unittest.TestCase):
    """Test client command conversion with mocked sending."""

    def make_client(self):
        """Create client without real server connection."""
        with patch("mood.client.client.threading.Thread") as thread_cls:
            thread_cls.return_value.start.return_value = None
            client = MUD("tester")

        client.connected = True
        return client

    def test_up_command(self):
        """Check up command conversion."""
        client = self.make_client()

        with patch.object(client, "send_line") as send:
            client.onecmd("up")

        send.assert_called_once_with("move up")

    def test_right_command(self):
        """Check right command conversion."""
        client = self.make_client()

        with patch.object(client, "send_line") as send:
            client.onecmd("right")

        send.assert_called_once_with("move right")

    def test_attack_with_name_and_weapon(self):
        """Check attack command with monster name and weapon."""
        client = self.make_client()

        with patch.object(client, "send_line") as send:
            client.onecmd("attack dragon with axe")

        send.assert_called_once_with("attack dragon axe")

    def test_attack_with_default_weapon(self):
        """Check attack command with default weapon."""
        client = self.make_client()

        with patch.object(client, "send_line") as send:
            client.onecmd("attack dragon")

        send.assert_called_once_with("attack dragon sword")

    def test_addmon_valid_command(self):
        """Check valid addmon command."""
        client = self.make_client()

        with patch.object(client, "send_line") as send:
            client.onecmd('addmon dragon hello "Hi there" hp 20 coords 1 2')

        send.assert_called_once_with(
            'addmon dragon hello "Hi there" hp 20 coords 1 2'
        )

    def test_addmon_invalid_hp(self):
        """Check invalid addmon is not sent."""
        client = self.make_client()

        with patch.object(client, "send_line") as send:
            with patch("builtins.print"):
                client.onecmd('addmon dragon hello "Hi" hp bad coords 1 2')

        send.assert_not_called()


if __name__ == "__main__":
    unittest.main()
