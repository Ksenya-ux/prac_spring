import sys
import cowsay
import shlex
import cmd

class MUD(cmd.Cmd):
    def __init__(self):
        super().__init__()
        self.field = [[None for _ in range(10)] for _ in range(10)]
        self.player_position = (0, 0)
        self.prompt = 'MUD> '
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
        self.cow_file_path = '/tmp/jgsbat.cow'
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


    def add_monster(self, name, x, y, hello, hp):
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

        self.add_monster(name, x, y, hello, hp)

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
