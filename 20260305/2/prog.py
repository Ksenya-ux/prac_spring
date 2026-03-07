import sys
import cowsay

class MUD:
    def __init__(self):
        self.field = [[None for _ in range(10)] for _ in range(10)]
        self.player_position = (0, 0)
        self.available_monsters = cowsay.char_names

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

<<<<<<< HEAD
    def add_monster(self, name, x, y, hello):  
=======
    def add_monster(self, name, x, y, hello):
        if name not in self.available_monsters:
            print("Cannot add unknown monster")
            return

>>>>>>> 5476779 (в) добавление в обработку команды addmon проверки того, что <name> - имя штатного существа)
        if (x, y) == self.player_position:
            print("Cannot add monster to player's position")
            return

        old_mon = self.field[x][y] is not None
        self.field[x][y] = (name, hello)  
        print(f"Added monster {name} to ({x}, {y}) saying {hello}")  

        if old_mon:
            print("Replaced the old monster")

    def encounter(self, x, y):
        monster = self.field[x][y] 
        if monster is not None:
<<<<<<< HEAD
            name, hello = monster  
            print(cowsay.cow(hello))  
=======
            name, hello = monster
            print(cowsay.get_output_string(name, hello))
>>>>>>> 5476779 (в) добавление в обработку команды addmon проверки того, что <name> - имя штатного существа)

    def process_cmd(self, command):
        parts = command.split()
        if not parts:
            print("Invalid command")
            return

        if parts[0] in ['up', 'down', 'left', 'right']:
            self.move_player(parts[0])
        elif parts[0] == 'addmon' and len(parts) == 5: 
            try:
                x, y = int(parts[2]), int(parts[3])  # координаты
                name = parts[1]  # имя
                hello = parts[4]  # приветствие
                self.add_monster(name, x, y, hello)
            except ValueError:
                print("Invalid arguments")
        else:
            print("Invalid command")


game = MUD()
if sys.stdin.isatty():
    while True:
        game.process_cmd(input())
else:
    for line in sys.stdin:
        game.process_cmd(line.strip())
