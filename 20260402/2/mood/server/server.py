import asyncio
import shlex

from ..common.game import Game
from ..common.constants import DEFAULT_HOST, DEFAULT_PORT, FIELD_SIZE

game = Game()


def handle_command(username, line):
    try:
        parts = shlex.split(line)
    except ValueError:
        return "Invalid command syntax", False

    if not parts:
        return "", False

    if parts[0] == "move":
        return game.move_player(username, parts[1]), False

    if parts[0] == "moveabs":
        x = int(parts[1])
        y = int(parts[2])

        if x < 0 or x >= FIELD_SIZE or y < 0 or y >= FIELD_SIZE:
            return f"Coordinates ({x}, {y}) are outside field (0-{FIELD_SIZE-1})", False
    
        return game.move_absolute(username, x, y), False

    if parts[0] == "addmon":
        if len(parts) < 7:
            return "Missing required parametrs!", False

        name = None
        hello = None
        hp = None
        x = None
        y = None

        i = 1
        while i < len(parts):
            if parts[i] == 'hello' and i + 1 < len(parts):
                hello = parts[i + 1]
                i += 2
            elif parts[i] == 'hp' and i + 1 < len(parts):
                try:
                    hp = int(parts[i + 1])
                except ValueError:
                    return "Invalid hitpoints value", False
                i += 2
            elif parts[i] == 'coords' and i + 2 < len(parts):
                try:
                    x = int(parts[i + 1]) % 10
                    y = int(parts[i + 2]) % 10
                except ValueError:
                    return "Invalid coordinates", False
                i += 3
            else:
                if name is None:
                    name = parts[i]
                    i += 1
                else:
                    return "Invalid command syntax", False

        if None in [name, hello, hp, x, y]:
            return "Missing required parameters", False

        return game.add_monster(username, name, x, y, hello, hp), True

    if parts[0] == "attack":
        monster_name = None if parts[1] == '*' else parts[1]
        weapon = parts[2]
        return game.attack(username, monster_name, weapon), True

    if parts[0] == "sayall":
        if len(parts) < 2:
            return "Usage: sayall <message>", False
        message = ' '.join(parts[1:])
        return f"{username}: {message}", True

    return "", False


async def handle_client(reader, writer):
    username = None
    try:
        data = await reader.readline()
        if not data:
            writer.close()
            await writer.wait_closed()
            return

        try:
            parts = shlex.split(data.decode().strip())
        except ValueError:
            await game.send_to(writer, "Invalid login")
            writer.close()
            await writer.wait_closed()
            return

        if len(parts) != 2 or parts[0] != "login":
            await game.send_to(writer, "Invalid login")
            writer.close()
            await writer.wait_closed()
            return

        username = parts[1]

        if not game.add_player(username, writer):
            await game.send_to(writer, "Username is already taken")
            writer.close()
            await writer.wait_closed()
            return

        await game.send_to(writer, f"Hello, {username}")
        await game.broadcast(f"{username} entered the MUD")

        while True:
            data = await reader.readline()
            if not data:
                break

            response, is_broadcast = handle_command(username, data.decode().strip())
            if not response:
                continue

            if is_broadcast:
                await game.broadcast(response)
            else:
                await game.send_to(writer, response)

    finally:
        if username is not None and username in game.players:
            game.remove_player(username)
            await game.broadcast(f"{username} left the MUD")

        writer.close()
        await writer.wait_closed()


async def run_server():
    server = await asyncio.start_server(handle_client, DEFAULT_HOST, DEFAULT_PORT)
    async with server:
        await server.serve_forever()
