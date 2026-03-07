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
        else:
            print("Invalid command")
            return

        self.player_position = (x, y)
        print(f"Moved to ({x}, {y})")
        self.encounter(x, y)
        
	 def encounter(self, x, y):
        hello = self.field[x][y]
        if hello is not None:
            print(cowsay.cowsay(hello))
	 def add_monster(self, x, y, hello):
        if (x, y) == self.player_position:
            print("Cannot add monster to player's position")
            return

        old_mon = self.field[x][y] is not None
        self.field[x][y] = hello
        print(f"Added monster to ({x}, {y}) saying {hello}")

        if old_mon:
            print("Replaced the old monster")
