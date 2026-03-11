import sys
import cowsay
import shlex

class MUD:
    def __init__(self):
        self.field = [[None for _ in range(10)] for _ in range(10)]
        self.player_position = (0, 0)
        with open('/tmp/jgsbat.cow', 'w') as f:
            f.write("""
    ,_                    _,
    ) '-._  ,_    _,  _.-' (
    )  _.-'.|\\--//|.'-._  (
     )'   .'\/o\/o\/'.   `(
      ) .' . \====/ . '. (
       )  / <<    >> \  (
        '-._/``  ``\_.-'
  jgs     __\\'--'//__
         (((""`  `"")))
        """)
        with open('/tmp/jgsbat.cow', 'r') as f:
            self.jgsbat = cowsay.read_dot_cow(f) 
        
        self.available_monsters = cowsay.list_cows()

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
        print(f"Moved to ({x}, {y})")
        self.encounter(x, y)


    def add_monster(self, name, x, y, hello,hp):
        if name not in self.available_monsters and name != 'jgsbat':
            print("Cannot add unknown monster")
            return

        if (x, y) == self.player_position:
            print("Cannot add monster to player's position")
            return

        old_mon = self.field[x][y] is not None
        self.field[x][y] = (name, hello, hp)
        print(f"Added monster {name} to ({x}, {y}) saying {hello} with {hp} hp")

        if old_mon:
            print("Replaced the old monster")

    def encounter(self, x, y):
        monster = self.field[x][y]
        if monster is not None:
            name, hello, hp = monster
            if name == 'jgsbat':
                print(cowsay.cowsay(message=hello, cowfile=self.jgsbat))
            else:
                print(cowsay.cowsay(message=hello, cow=name))

    def process_cmd(self, command):
        try:
            parts = shlex.split(command)
        except:
            print("Invalid command syntax")
            return

        if not parts:
            print("Invalid command")
            return

        if parts[0] in ['up', 'down', 'left', 'right']:
            self.move_player(parts[0])
        elif parts[0] == 'addmon':
            if len(parts) < 8:
                print("Missing required parameters")
                return

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
                        if hp <= 0:
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

            self.add_monster(name, x, y, hello, hp)
        else:
            print("Invalid command")

print("<<< Welcome to Python-MUD 0.1 >>>")
game = MUD()
if sys.stdin.isatty():
    while True:
        game.process_cmd(input())
else:
    for line in sys.stdin:
        game.process_cmd(line.strip())
