import sys
import asyncio
import cowsay
import shlex
import cmd


class MUD(cmd.Cmd):
    def __init__(self):
        super().__init__()
        self.prompt = 'MUD> '
        self.addmon_params = ['hello', 'hp', 'coords']
        self.weapons = {
            'sword': 10,
            'spear': 15,
            'axe': 20
        }

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
        self.cow_file_path = '/tmp/jgsbat.cow'
        with open('/tmp/jgsbat.cow', 'r') as f:
            self.jgsbat = cowsay.read_dot_cow(f)

        self.available_monsters = cowsay.list_cows()

        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.reader = None
        self.writer = None
        self.loop.run_until_complete(self.connect())

    async def connect(self):
        self.reader, self.writer = await asyncio.open_connection('127.0.0.1', 1337)

    async def request(self, line):
        self.writer.write((line + '\n').encode())
        await self.writer.drain()
        data = await self.reader.readline()
        return data.decode().rstrip('\n')

    def send_request(self, line):
        return self.loop.run_until_complete(self.request(line))

    def _print_move_response(self, response):
        parts = response.split(maxsplit=4)
        if not parts:
            return

        if parts[0] == "MOVED":
            _, x, y = parts
            print(f"Moved to ({x}, {y})")
        elif parts[0] == "MOVED_ENCOUNTER":
            _, x, y, name, hello = parts
            print(f"Moved to ({x}, {y})")
            if name == 'jgsbat':
                print(cowsay.cowsay(message=hello, cowfile=self.jgsbat))
            else:
                print(cowsay.cowsay(message=hello, cow=name))

    def move_player(self, direction):
        response = self.send_request(f"move {direction}")
        self._print_move_response(response)

    def do_move(self, arg):
        try:
            parts = shlex.split(arg)
        except:
            print("Invalid command syntax")
            return

        if len(parts) != 2:
            print("Invalid command syntax")
            return

        try:
            x = int(parts[0])
            y = int(parts[1])
        except:
            print("Invalid command syntax")
            return

        response = self.send_request(f"moveabs {x} {y}")
        self._print_move_response(response)

    def do_up(self, arg):
        self.move_player('up')

    def do_down(self, arg):
        self.move_player('down')

    def do_left(self, arg):
        self.move_player('left')

    def do_right(self, arg):
        self.move_player('right')

    def do_addmon(self, arg):
        try:
            parts = shlex.split(arg)
        except:
            print("Invalid command syntax")
            return
        if len(parts) < 7:
            print("Missing required parametrs!")
            return

        name = None
        hello = None
        hp = None
        x = None
        y = None

        i = 0
        while i < len(parts):
            if parts[i] == 'hello' and i + 1 < len(parts):
                hello = parts[i + 1]
                i += 2
            elif parts[i] == 'hp' and i + 1 < len(parts):
                try:
                    hp = int(parts[i + 1])
                    if hp < 0:
                        print("Hitpoints must be positive")
                        return
                except:
                    print("Invalid hitpoints value")
                    return
                i += 2
            elif parts[i] == 'coords' and i + 2 < len(parts):
                try:
                    x = int(parts[i + 1])
                    y = int(parts[i + 2])
                except:
                    print("Invalid coordinates")
                    return
                i += 3
            else:
                if name is None:
                    name = parts[i]
                    i += 1
                else:
                    print("Invalid command syntax")
                    return

        if None in [name, hello, hp, x, y]:
            print("Missing required parameters")
            return

        response = self.send_request(f"addmon {name} {x} {y} {hello} {hp}")
        parts = response.split(maxsplit=6)
        if not parts:
            return

        if parts[0] == "ADDMON_OK":
            _, name, x, y, hello, hp = parts
            print(f"Added monster {name} to ({x}, {y}) saying {hello} with {hp} hp")
        elif parts[0] == "ADDMON_REPLACED":
            _, name, x, y, hello, hp = parts
            print(f"Added monster {name} to ({x}, {y}) saying {hello} with {hp} hp")
            print("Replaced the old monster")
        elif parts[0] == "ERR_UNKNOWN_MONSTER":
            print("Cannot add unknown monster")
        elif parts[0] == "ERR_PLAYER_CELL":
            print("Cannot add monster to player's position")

    def do_EOF(self, arg):
        print()
        if self.writer is not None:
            self.writer.close()
            self.loop.run_until_complete(self.writer.wait_closed())
        return True

    def complete_addmon(self, text, line, begidx, endidx):
        parts = line[:endidx].split()
        if len(parts) <= 2:
            monsters = self.available_monsters + ['jgsbat']
            result = []
            for m in monsters:
                if m.startswith(text):
                    result.append(m)
            return result
        else:
            last = parts[-1].lower()
            if last not in ('hello', 'hp', 'coords'):
                used = []
                for w in parts:
                    if w.lower() in self.addmon_params:
                        used.append(w.lower())
                available = []
                for p in self.addmon_params:
                    if p not in used:
                        available.append(p)
                result = []
                for a in available:
                    if a.startswith(text.lower()):
                        result.append(a)
                return result
        return []

    def do_attack(self, arg):
        try:
            parts = shlex.split(arg)
        except:
            print("Invalid command syntax")
            return

        monster_name = None
        weapon = 'sword'

        if len(parts) == 0:
            pass
        elif len(parts) == 1:
            monster_name = parts[0]
        elif len(parts) == 2 and parts[0].lower() == 'with':
            weapon = parts[1]
        elif len(parts) == 3 and parts[1].lower() == 'with':
            monster_name = parts[0]
            weapon = parts[2]
        else:
            print("Invalid command syntax")
            return

        if weapon not in self.weapons:
            print("Unknown weapon")
            return

        target = '*' if monster_name is None else monster_name
        response = self.send_request(f"attack {target} {weapon}")
        parts = response.split(maxsplit=3)

        if not parts:
            return

        if parts[0] == "NO_MONSTER":
            if monster_name:
                print(f"No {monster_name} here")
            else:
                print("No monster here")
        elif parts[0] == "ATTACK_DIED":
            _, name, damage = parts
            print(f"Attacked {name}, damage {damage} hp")
            print(f"{name} died")
        elif parts[0] == "ATTACK_LEFT":
            _, name, damage, hp = parts
            print(f"Attacked {name}, damage {damage} hp")
            print(f"{name} now has {hp}")

    def complete_attack(self, text, line, begidx, endidx):
        parts = line[:endidx].split()

        if len(parts) <= 2 and not any(p.lower() == 'with' for p in parts):
            monsters = self.available_monsters + ['jgsbat']
            return [m for m in monsters if m.startswith(text)]
        elif len(parts) >= 2 and parts[-1].lower() == 'with':
            return [w for w in self.weapons.keys() if w.startswith(text)]
        elif len(parts) >= 3 and parts[-2].lower() == 'with':
            return [w for w in self.weapons.keys() if w.startswith(text)]
        else:
            if 'with' not in [p.lower() for p in parts] and 'with'.startswith(text.lower()):
                return ['with']
        return []


def main():
    print("<<< Welcome to Python-MUD 0.1 >>>")
    game = MUD()
    if sys.stdin.isatty():
        game.cmdloop()
    else:
        for line in sys.stdin:
            line = line.strip()
            if line:
                game.onecmd(line)


if __name__ == '__main__':
    main()
