import asyncio
import cowsay
import shlex


class Game:
    def __init__(self):
        self.field = [[None for _ in range(10)] for _ in range(10)]
        self.players = {}

        with open('/tmp/jgsbat.cow', 'w') as f:
            f.write("""
    ,_                    _,
    ) '-._  ,_    _,  _.-' (
    )  _.-'.|\\--//|.'-._  (
     )'   .'\\/o\\/o\\/'.   `(
      ) .' . \\====/ . '. (
       )  / <<    >> \\  (
        '-._/``  ``\\_.-'
  jgs     __\\'--'//__
         (((""`  `"")))
        """)

        self.available_monsters = cowsay.list_cows()
        self.weapons = {
            'sword': 10,
            'spear': 15,
            'axe': 20
        }

        with open('/tmp/jgsbat.cow', 'r') as f:
            self.jgsbat = cowsay.read_dot_cow(f)

    def add_player(self, name, writer):
        if name in self.players:
            return False
        self.players[name] = {"pos": (0, 0), "writer": writer}
        return True

    def remove_player(self, name):
        if name in self.players:
            del self.players[name]

    async def send_to(self, writer, message):
        payload = message.replace('\n', '\\n')
        writer.write((payload + '\n').encode())
        await writer.drain()

    async def broadcast(self, message):
        payload = message.replace('\n', '\\n')
        bad = []

        for name, info in list(self.players.items()):
            try:
                info["writer"].write((payload + '\n').encode())
            except Exception:
                bad.append(name)

        for name, info in list(self.players.items()):
            if name in bad:
                continue
            try:
                await info["writer"].drain()
            except Exception:
                bad.append(name)

        for name in bad:
            self.remove_player(name)

    def _move_to(self, username, x, y):
        x %= 10
        y %= 10
        self.players[username]["pos"] = (x, y)
        monster = self.field[x][y]

        result = [f"Moved to ({x}, {y})"]

        if monster is not None:
            name, hello, hp = monster
            if name == 'jgsbat':
                result.append(cowsay.cowsay(message=hello, cowfile=self.jgsbat))
            else:
                result.append(cowsay.cowsay(message=hello, cow=name))

        return '\n'.join(result)

    def move_player(self, username, direction):
        x, y = self.players[username]["pos"]

        if direction == 'up':
            y = (y - 1) % 10
        elif direction == 'down':
            y = (y + 1) % 10
        elif direction == 'left':
            x = (x - 1) % 10
        elif direction == 'right':
            x = (x + 1) % 10

        return self._move_to(username, x, y)

    def move_absolute(self, username, x, y):
        return self._move_to(username, x, y)

    def add_monster(self, username, name, x, y, hello, hp):
        if name not in self.available_monsters and name != 'jgsbat':
            return "Cannot add unknown monster"

        old_mon = self.field[x][y] is not None
        self.field[x][y] = (name, hello, hp)

        result = f"{username} added monster {name} to ({x}, {y}) saying {hello} with {hp} hp"
        if old_mon:
            result += "\nReplaced the old monster"
        return result

    def attack(self, username, monster_name, weapon):
        x, y = self.players[username]["pos"]
        monster = self.field[x][y]

        if monster is None:
            if monster_name:
                return f"No {monster_name} here"
            return "No monster here"

        name, hello, hp = monster

        if monster_name and name != monster_name:
            return f"No {monster_name} here"

        damage = min(hp, self.weapons[weapon])
        hp = hp - damage

        if hp <= 0:
            self.field[x][y] = None
            return f"{username} attacked {name} with {weapon}, damage {damage} hp, {name} died"
        else:
            self.field[x][y] = (name, hello, hp)
            return f"{username} attacked {name} with {weapon}, damage {damage} hp, {name} now has {hp}"


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
        return game.move_absolute(username, int(parts[1]), int(parts[2])), False

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
                except:
                    return "Invalid hitpoints value", False
                i += 2
            elif parts[i] == 'coords' and i + 2 < len(parts):
                try:
                    x = int(parts[i + 1]) % 10
                    y = int(parts[i + 2]) % 10
                except:
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

        # 👇 вот здесь приветствие
        await game.send_to(writer, f"Hello, {username}")

        # 👇 и широковещательное сообщение
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


async def main():
    server = await asyncio.start_server(handle_client, "127.0.0.1", 1337)
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
