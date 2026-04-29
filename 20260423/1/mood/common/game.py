import cowsay
from .constants import FIELD_SIZE, WEAPONS


class Game:

    def __init__(self):
        self.field = [[None for _ in range(FIELD_SIZE)] for _ in range(FIELD_SIZE)]
        self.players = {}
        self.available_monsters = cowsay.list_cows()
        self.weapons = WEAPONS

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

        with open('/tmp/jgsbat.cow', 'r') as f:
            self.jgsbat = cowsay.read_dot_cow(f)

    def add_player(self, name, writer):
        if name in self.players:
            return False
        self.players[name] = {"pos": (0, 0), "writer": writer, "locale": None}
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
        x %= FIELD_SIZE
        y %= FIELD_SIZE
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
            y = (y - 1) % FIELD_SIZE
        elif direction == 'down':
            y = (y + 1) % FIELD_SIZE
        elif direction == 'left':
            x = (x - 1) % FIELD_SIZE
        elif direction == 'right':
            x = (x + 1) % FIELD_SIZE

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
