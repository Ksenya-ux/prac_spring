import asyncio
import cowsay


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

    async def send(self, writer, message):
        writer.write((message + '\n').encode())
        await writer.drain()

    async def broadcast(self, message):
        for info in list(self.players.values()):
            info['writer'].write((message + '\n').encode())
        for info in list(self.players.values()):
            await info['writer'].drain()

    def login(self, name, writer):
        if name in self.players:
            return False
        self.players[name] = {'pos': (0, 0), 'writer': writer}
        return True

    def logout(self, name):
        self.players.pop(name, None)

    def _encounter_message(self, name, hello):
        if name == 'jgsbat':
            with open('/tmp/jgsbat.cow', 'r') as f:
                jgsbat = cowsay.read_dot_cow(f)
            return cowsay.cowsay(message=hello, cowfile=jgsbat)
        return cowsay.cowsay(message=hello, cow=name)

    def _move_to(self, player, x, y):
        x %= 10
        y %= 10
        self.players[player]['pos'] = (x, y)
        messages = [f"Moved to ({x}, {y})"]
        monster = self.field[x][y]
        if monster is not None:
            name, hello, hp = monster
            messages.append(self._encounter_message(name, hello))
        return messages

    def move_player(self, player, direction):
        x, y = self.players[player]['pos']
        if direction == 'up':
            y = (y - 1) % 10
        elif direction == 'down':
            y = (y + 1) % 10
        elif direction == 'left':
            x = (x - 1) % 10
        elif direction == 'right':
            x = (x + 1) % 10
        return self._move_to(player, x, y), []

    def move_absolute(self, player, x, y):
        return self._move_to(player, x, y), []

    def add_monster(self, player, name, x, y, hello, hp):
        if name not in self.available_monsters and name != 'jgsbat':
            return ["Cannot add unknown monster"], []

        old_mon = self.field[x][y] is not None
        self.field[x][y] = (name, hello, hp)

        personal = [f"Added monster {name} to ({x}, {y}) saying {hello} with {hp} hp"]
        if old_mon:
            personal.append("Replaced the old monster")
        broadcast = [f"{player} added monster {name} to ({x}, {y}) saying {hello} with {hp} hp"]
        return personal, broadcast

    def attack(self, player, monster_name, weapon):
        x, y = self.players[player]['pos']
        monster = self.field[x][y]

        if monster is None:
            if monster_name:
                return [f"No {monster_name} here"], []
            return ["No monster here"], []

        name, hello, hp = monster

        if monster_name and name != monster_name:
            return [f"No {monster_name} here"], []

        damage = min(hp, self.weapons[weapon])
        hp = hp - damage

        personal = [f"Attacked {name}, damage {damage} hp"]
        if hp <= 0:
            self.field[x][y] = None
            personal.append(f"{name} died")
            broadcast = [f"{player} attacked {name} with {weapon}, damage {damage} hp, {name} died"]
        else:
            self.field[x][y] = (name, hello, hp)
            personal.append(f"{name} now has {hp}")
            broadcast = [f"{player} attacked {name} with {weapon}, damage {damage} hp, {name} now has {hp}"]
        return personal, broadcast


game = Game()


def handle_command(player, line):
    parts = line.split()
    if not parts:
        return [], []

    if parts[0] == "move":
        return game.move_player(player, parts[1])

    if parts[0] == "moveabs":
        return game.move_absolute(player, int(parts[1]), int(parts[2]))

    if parts[0] == "addmon":
        name = parts[1]
        x = int(parts[2])
        y = int(parts[3])
        hello = parts[4]
        hp = int(parts[5])
        return game.add_monster(player, name, x, y, hello, hp)

    if parts[0] == "attack":
        monster_name = None if parts[1] == '*' else parts[1]
        weapon = parts[2]
        return game.attack(player, monster_name, weapon)

    return [], []


async def handle_client(reader, writer):
    name = None
    try:
        data = await reader.readline()
        if not data:
            return
        name = data.decode().strip()
        if not name or ' ' in name or name in game.players:
            await game.send(writer, 'Login failed')
            return

        game.login(name, writer)
        await game.send(writer, 'Connected')
        await game.broadcast(f'{name} entered the MUD')

        while data := await reader.readline():
            personal, common = handle_command(name, data.decode().strip())
            for msg in personal:
                await game.send(writer, msg)
            for msg in common:
                await game.broadcast(msg)
    finally:
        if name in game.players:
            game.logout(name)
            await game.broadcast(f'{name} left the MUD')
        writer.close()
        await writer.wait_closed()


async def main():
    server = await asyncio.start_server(handle_client, '127.0.0.1', 1337)
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
