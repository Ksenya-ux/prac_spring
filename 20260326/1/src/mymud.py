import sys
import asyncio
import cowsay
import shlex
import cmd
import threading
import readline


class MUD(cmd.Cmd):
    def __init__(self, username):
        super().__init__()
        self.prompt = 'MUD> '
        self.username = username
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
        self.reader = None
        self.writer = None
        self.connected = threading.Event()
        self.failed = False

        self.net_thread = threading.Thread(target=self._network_loop, daemon=True)
        self.net_thread.start()
        self.connected.wait()

    def _network_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.connect())
        if self.writer is not None and not self.failed:
            self.loop.create_task(self.reader_task())
            self.loop.run_forever()

    async def connect(self):
        try:
            self.reader, self.writer = await asyncio.open_connection('127.0.0.1', 1337)
            self.writer.write((self.username + '\n').encode())
            await self.writer.drain()
            data = await self.reader.readline()
            if not data:
                print('Connection closed')
                self.failed = True
                self.connected.set()
                return
            msg = data.decode().rstrip('\n')
            print(msg)
            if msg != 'Connected':
                self.failed = True
                self.writer.close()
                await self.writer.wait_closed()
                self.writer = None
            self.connected.set()
        except Exception:
            print('Connection failed')
            self.failed = True
            self.connected.set()

    async def reader_task(self):
        try:
            while True:
                data = await self.reader.readline()
                if not data:
                    print(f"\nConnection closed\n{self.prompt}{readline.get_line_buffer()}", end='', flush=True)
                    break
                print(f"\n{data.decode().rstrip()}\n{self.prompt}{readline.get_line_buffer()}", end='', flush=True)
        finally:
            if self.writer is not None:
                self.writer.close()
                await self.writer.wait_closed()
            self.loop.stop()

    async def _send(self, line):
        if self.writer is None:
            return
        self.writer.write((line + '\n').encode())
        await self.writer.drain()

    def send_request(self, line):
        if self.writer is None:
            return
        asyncio.run_coroutine_threadsafe(self._send(line), self.loop)

    def move_player(self, direction):
        self.send_request(f"move {direction}")

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

        self.send_request(f"moveabs {x} {y}")

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

        self.send_request(f"addmon {name} {x} {y} {hello} {hp}")

    def do_EOF(self, arg):
        print()
        if self.writer is not None:
            fut = asyncio.run_coroutine_threadsafe(self._close(), self.loop)
            try:
                fut.result(timeout=1)
            except:
                pass
        return True

    async def _close(self):
        if self.writer is not None:
            self.writer.close()
            await self.writer.wait_closed()
            self.writer = None

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
        self.send_request(f"attack {target} {weapon}")

    def complete_attack(self, text, line, begidx, endidx):
        parts = line[:endidx].split()

        if len(parts) >= 2 and parts[-1].lower() == 'with':
            return [w for w in self.weapons.keys() if w.startswith(text)]
        elif len(parts) >= 3 and parts[-2].lower() == 'with':
            return [w for w in self.weapons.keys() if w.startswith(text)]
        else:
            if 'with' not in [p.lower() for p in parts] and 'with'.startswith(text.lower()):
                return ['with']
        return []


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} username")
        return

    print("<<< Welcome to Python-MUD 0.1 >>>")
    game = MUD(sys.argv[1])
    if game.failed:
        return
    if sys.stdin.isatty():
        game.cmdloop()
    else:
        for line in sys.stdin:
            line = line.strip()
            if line:
                game.onecmd(line)


if __name__ == '__main__':
    main()
