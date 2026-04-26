import asyncio
import shlex
import random
import cowsay

from ..common.game import Game
from ..common.constants import DEFAULT_HOST, DEFAULT_PORT, FIELD_SIZE

game = Game()
move_monsters_enabled = True


async def move_wandering_monsters():
    """
    Каждые 30 секунд выбирает случайного монстра на поле и передвигает его
    на соседнюю клетку в случайном направлении. Если клетка занята другим
    монстром, выбирает другого монстра и направление. При попадании монстра
    на клетку с игроком, игрок видит приветствие монстра.
    """
    directions = ['up', 'down', 'left', 'right']
    
    while True:
        await asyncio.sleep(30)
        
        if not move_monsters_enabled:
            continue
        
        monsters_on_field = []
        for x in range(FIELD_SIZE):
            for y in range(FIELD_SIZE):
                if game.field[x][y] is not None:
                    monsters_on_field.append((x, y, game.field[x][y]))
        
        if not monsters_on_field:
            continue
        
        moved = False
        attempts = 0
        max_attempts = 100
        
        while not moved and attempts < max_attempts:
            attempts += 1
            
            x, y, (name, hello, hp) = random.choice(monsters_on_field)
            direction = random.choice(directions)
            
            new_x, new_y = x, y
            if direction == 'up':
                new_y = (y - 1) % FIELD_SIZE
            elif direction == 'down':
                new_y = (y + 1) % FIELD_SIZE
            elif direction == 'left':
                new_x = (x - 1) % FIELD_SIZE
            elif direction == 'right':
                new_x = (x + 1) % FIELD_SIZE
            
            if game.field[new_x][new_y] is None:
                game.field[new_x][new_y] = (name, hello, hp)
                game.field[x][y] = None
                moved = True
                
                response = f"{name} moved one cell {direction}"
                
                players_on_cell = []
                for player_name, player_info in game.players.items():
                    if player_info["pos"] == (new_x, new_y):
                        players_on_cell.append((player_name, player_info["writer"]))
                
                if players_on_cell:
                    for player_name, writer in players_on_cell:
                        if name == 'jgsbat':
                            monster_message = cowsay.cowsay(message=hello, cowfile=game.jgsbat)
                        else:
                            monster_message = cowsay.cowsay(message=hello, cow=name)
                        await game.send_to(writer, f"{response}\n{monster_message}")
                    
                    for player_name, player_info in game.players.items():
                        if player_info["pos"] != (new_x, new_y):
                            await game.send_to(player_info["writer"], response)
                else:
                    await game.broadcast(response)


def handle_command(username, line):
    """
    Разбирает команду от игрока и вызывает нужный метод игры.
    Поддерживает команды: move, moveabs, addmon, attack, sayall, movemonsters.
    Возвращает ответ сервера и флаг, нужно ли показывать ответ всем игрокам.
    """
    try:
        parts = shlex.split(line)
    except ValueError:
        return "Invalid command syntax", False

    if not parts:
        return "", False

    if parts[0] == "move":
        return game.move_player(username, parts[1]), False

    if parts[0] == "moveabs":
        x = int(parts[1])
        y = int(parts[2])

        if x < 0 or x >= FIELD_SIZE or y < 0 or y >= FIELD_SIZE:
            return f"Coordinates ({x}, {y}) are outside field (0-{FIELD_SIZE-1})", False
    
        return game.move_absolute(username, x, y), False

    if parts[0] == "addmon":
        if len(parts) < 7:
            return "Missing required parametrs!", False

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
                except ValueError:
                    return "Invalid hitpoints value", False
                i += 2
            elif parts[i] == 'coords' and i + 2 < len(parts):
                try:
                    x = int(parts[i + 1]) % 10
                    y = int(parts[i + 2]) % 10
                except ValueError:
                    return "Invalid coordinates", False
                i += 3
            else:
                if name is None:
                    name = parts[i]
                    i += 1
                else:
                    return "Invalid command syntax", False

        if None in [name, hello, hp, x, y]:
            return "Missing required parameters", False

        return game.add_monster(username, name, x, y, hello, hp), True

    if parts[0] == "attack":
        monster_name = None if parts[1] == '*' else parts[1]
        weapon = parts[2]
        return game.attack(username, monster_name, weapon), True

    if parts[0] == "sayall":
        if len(parts) < 2:
            return "Usage: sayall <message>", False
        message = ' '.join(parts[1:])
        return f"{username}: {message}", True

    if parts[0] == "movemonsters":
        global move_monsters_enabled

        if len(parts) != 2 or parts[1] not in ("on", "off"):
            return "Invalid command syntax", False

        move_monsters_enabled = parts[1] == "on"
        return f"{username} switched moving monsters: {parts[1]}", True

    return "", False


async def handle_client(reader, writer):
    """
    Обрабатывает подключение одного игрока. Принимает логин,
    добавляет игрока в игру и в цикле принимает команды пока
    соединение не закроется. При отключении удаляет игрока из игры.
    """
    username = None
    try:
        data = await reader.readline()
        if not data:
            writer.close()
            await writer.wait_closed()
            return

        try:
            parts = shlex.split(data.decode().strip())
        except ValueError:
            await game.send_to(writer, "Invalid login")
            writer.close()
            await writer.wait_closed()
            return

        if len(parts) != 2 or parts[0] != "login":
            await game.send_to(writer, "Invalid login")
            writer.close()
            await writer.wait_closed()
            return

        username = parts[1]

        if not game.add_player(username, writer):
            await game.send_to(writer, "Username is already taken")
            writer.close()
            await writer.wait_closed()
            return

        await game.send_to(writer, f"Hello, {username}")
        await game.broadcast(f"{username} entered the MUD")

        while True:
            data = await reader.readline()
            if not data:
                break

            response, is_broadcast = handle_command(username, data.decode().strip())
            if not response:
                continue

            if is_broadcast:
                await game.broadcast(response)
            else:
                await game.send_to(writer, response)

    finally:
        if username is not None and username in game.players:
            game.remove_player(username)
            await game.broadcast(f"{username} left the MUD")

        writer.close()
        await writer.wait_closed()


async def run_server():
    """
    Запускает сервер MUD. Создаёт фоновую задачу для перемещения
    бродячих монстров и начинает принимать подключения игроков.
    """
    asyncio.create_task(move_wandering_monsters())
    
    server = await asyncio.start_server(handle_client, DEFAULT_HOST, DEFAULT_PORT)
    async with server:
        await server.serve_forever()
