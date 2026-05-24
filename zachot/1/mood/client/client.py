import sys
import asyncio
import cowsay
import shlex
import cmd
import threading
import readline
import time

from ..common.constants import DEFAULT_HOST, DEFAULT_PORT, WEAPONS


class MUD(cmd.Cmd):

    def __init__(self, username, file_mode=False):
        super().__init__()
        self.prompt = 'MUD> '
        self.addmon_params = ['hello', 'hp', 'coords']
        self.weapons = WEAPONS
        self.file_mode = file_mode
        self.last_command_time = 0

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
        self.username = username

        self.loop = asyncio.new_event_loop()
        self.reader = None
        self.writer = None
        self.connected = False
        self.login_done = threading.Event()

        self.net_thread = threading.Thread(target=self._run_network, daemon=True)
        self.net_thread.start()

    def _run_network(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.connect())
        if self.connected:
            self.loop.create_task(self.receive_messages())
            self.loop.run_forever()
        self.login_done.set()

    async def connect(self):
        try:
            self.reader, self.writer = await asyncio.open_connection(DEFAULT_HOST, DEFAULT_PORT)
            self.writer.write("login {}\n".format(self.username).encode())
            await self.writer.drain()

            data = await self.reader.readline()
            if not data:
                print("Connection closed by server")
                self.login_done.set()
                return

            msg = data.decode().rstrip('\n').replace('\\n', '\n')
            print(msg)

            if msg.startswith("Hello"):
                self.connected = True
            else:
                self.writer.close()
                await self.writer.wait_closed()

        except OSError as e:
            print("Connection error: {}".format(e))
        finally:
            self.login_done.set()

    async def receive_messages(self):
        try:
            while True:
                data = await self.reader.readline()
                if not data:
                    print("\nServer disconnected\n{}{}".format(
                        self.prompt,
                        readline.get_line_buffer()
                    ), end="", flush=True)
                    self.connected = False
                    break

                msg = data.decode().rstrip('\n').replace('\\n', '\n')
                print("\n{}\n{}{}".format(
                    msg,
                    self.prompt,
                    readline.get_line_buffer()
                ), end="", flush=True)
        except Exception:
            self.connected = False

    async def send_line_async(self, line):
        if self.writer is None:
            return
        self.writer.write((line + '\n').encode())
        await self.writer.drain()

    def send_line(self, line):
        if not self.connected:
            print("Not connected")
            return

        if self.file_mode:
            current_time = time.time()
            elapsed = current_time - self.last_command_time
            if elapsed < 1.0:
                time.sleep(1.0 - elapsed)

        asyncio.run_coroutine_threadsafe(self.send_line_async(line), self.loop)
        self.last_command_time = time.time()

    def do_locale(self, arg):
        try:
            parts = shlex.split(arg)
        except ValueError:
            print("Invalid command syntax")
            return

        if len(parts) != 1:
            print("Invalid command syntax")
            return

        self.send_line("locale {}".format(parts[0]))

    def do_move(self, arg):
        try:
            parts = shlex.split(arg)
        except ValueError:
            print("Invalid command syntax")
            return

        if len(parts) != 2:
            print("Invalid command syntax")
            return

        try:
            x = int(parts[0])
            y = int(parts[1])
        except ValueError:
            print("Invalid command syntax")
            return

        self.send_line("moveabs {} {}".format(x, y))

    def do_up(self, arg):
        self.send_line('move up')

    def do_down(self, arg):
        self.send_line('move down')

    def do_left(self, arg):
        self.send_line('move left')

    def do_right(self, arg):
        self.send_line('move right')

    def do_addmon(self, arg):
        try:
            parts = shlex.split(arg)
        except ValueError:
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
                except ValueError:
                    print("Invalid hitpoints value")
                    return
                i += 2
            elif parts[i] == 'coords' and i + 2 < len(parts):
                try:
                    x = int(parts[i + 1])
                    y = int(parts[i + 2])
                except ValueError:
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

        self.send_line("addmon {}".format(arg))

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
        except ValueError:
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
        self.send_line("attack {} {}".format(target, weapon))

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

    def do_EOF(self, arg):
        print()
        if self.writer is not None:
            future = asyncio.run_coroutine_threadsafe(self.close_connection(), self.loop)
            try:
                future.result(timeout=2)
            except Exception:
                pass
        if self.loop.is_running():
            self.loop.call_soon_threadsafe(self.loop.stop)
        return True

    async def close_connection(self):
        self.writer.close()
        await self.writer.wait_closed()

    def do_sayall(self, arg):
        if not arg:
            print("Usage: sayall <message>")
            return

        try:
            parts = shlex.split(arg)
            if not parts:
                print("Usage: sayall <message>")
                return
        except ValueError:
            print("Invalid message format")
            return

        self.send_line("sayall {}".format(arg))

    def do_movemonsters(self, arg):
        try:
            parts = shlex.split(arg)
        except ValueError:
            print("Invalid command syntax")
            return

        if len(parts) != 1 or parts[0] not in ("on", "off"):
            print("Invalid command syntax")
            return

        self.send_line("movemonsters {}".format(parts[0]))

    def complete_movemonsters(self, text, line, begidx, endidx):
        return [state for state in ("on", "off") if state.startswith(text)]


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m mood.client username [--file commands.mood]")
        return

    username = sys.argv[1]
    file_mode = False
    file_path = None

    if len(sys.argv) > 2:
        if sys.argv[2] == "--file" and len(sys.argv) > 3:
            file_mode = True
            file_path = sys.argv[3]
        else:
            print("Usage: python -m mood.client username [--file commands.mood]")
            return

    print("<<< Welcome to Python-MOOD 0.1 >>>")
    game = MUD(username, file_mode=file_mode)
    game.login_done.wait()

    if not game.connected:
        return

    if file_mode and file_path:
        game.use_rawinput = False
        game.prompt = ''
        try:
            with open(file_path, 'r') as f:
                commands = [line.strip() for line in f if line.strip()]

            for line in commands:
                game.onecmd(line)
                time.sleep(1.0)
        except FileNotFoundError:
            print("Command file not found: {}".format(file_path))
        except Exception as e:
            print("Error reading command file: {}".format(e))
    else:
        if sys.stdin.isatty():
            game.cmdloop()
        else:
            for line in sys.stdin:
                line = line.strip()
                if line:
                    game.onecmd(line)


if __name__ == '__main__':
    main()
