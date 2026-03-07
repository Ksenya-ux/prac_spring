import sys
import cowsay

class MUD:
    def __init__(self):
        self.field = [[None for _ in range(10)] for _ in range(10)]
        self.player_position = (0, 0)

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

    def add_monster(self, x, y, hello):
        if (x, y) == self.player_position:
            print("Cannot add monster to player's position")
            return

        old_mon = self.field[x][y] is not None
        self.field[x][y] = hello
        print(f"Added monster to ({x}, {y}) saying {hello}")

        if old_mon:
            print("Replaced the old monster")

    def encounter(self, x, y):
        hello = self.field[x][y]
        if hello is not None:
            print(cowsay.cowsay(hello))

    def process_cmd(self, command):
        parts = command.split()
        if not parts:
            print("Invalid command")
            return

        if parts[0] in ['up', 'down', 'left', 'right']:
            self.move_player(parts[0])
        elif parts[0] == 'addmon' and len(parts) == 4:
            try:
                x, y = int(parts[1]), int(parts[2])
                hello = parts[3]
                self.add_monster(x, y, hello)
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
