import asyncio
import cowsay


class Game:
    def __init__(self):
        self.field = [[None for _ in range(10)] for _ in range(10)]
        self.player_position = (0, 0)

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

    def move_player(self, direction):
        x, y = self.player_position
        if direction == 'up':
            y = (y - 1) % 10
        elif direction == 'down':
            y = (y + 1) % 10
        elif direction == 'left':
            x = (x - 1) % 10
        elif direction == 'right':
            x = (x + 1) % 10

        self.player_position = (x, y)
        monster = self.field[x][y]
        if monster is not None:
            name, hello, hp = monster
            return f"MOVED {x} {y}\nENCOUNTER {name} {hello}"
        return f"MOVED {x} {y}"

    def add_monster(self, name, x, y, hello, hp):
        if name not in self.available_monsters and name != 'jgsbat':
            return "Cannot add unknown monster"

        if (x, y) == self.player_position:
            return "Cannot add monster to player's position"

        old_mon = self.field[x][y] is not None
        self.field[x][y] = (name, hello, hp)

        result = f"Added monster {name} to ({x}, {y}) saying {hello} with {hp} hp"
        if old_mon:
            result += "\nReplaced the old monster"
        return result

    def attack(self, monster_name, weapon):
        x, y = self.player_position
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
        result = f"Attacked {name}, damage {damage} hp"

        if hp <= 0:
            self.field[x][y] = None
            result += f"\n{name} died"
        else:
            self.field[x][y] = (name, hello, hp)
            result += f"\n{name} now has {hp}"

        return result


game = Game()


def handle_command(line):
    parts = line.split()
    if not parts:
        return ""

    if parts[0] == "move":
        return game.move_player(parts[1])

    if parts[0] == "addmon":
        name = parts[1]
        x = int(parts[2])
        y = int(parts[3])
        hello = parts[4]
        hp = int(parts[5])
        return game.add_monster(name, x, y, hello, hp)

    if parts[0] == "attack":
        monster_name = None if parts[1] == '*' else parts[1]
        weapon = parts[2]
        return game.attack(monster_name, weapon)

    return ""


async def handle_client(reader, writer):
    try:
        while data := await reader.readline():
            response = handle_command(data.decode().strip())
            writer.write((response + "\n").encode())
            await writer.drain()
    finally:
        writer.close()
        await writer.wait_closed()


async def main():
    server = await asyncio.start_server(handle_client, "127.0.0.1", 1337)
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
