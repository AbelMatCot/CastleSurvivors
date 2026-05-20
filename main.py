import pygame
import random
import configparser
import os

from Entities.Player.castle import ArrowCastle, FireballCastle, KunaiCastle, LaserCastle
from Entities.Player.towers import ArrowTower, FireballTower, KunaiTower, LaserTower
from Entities.spawn import Spawn

# --- CONSTANTES ---
allow = 0
forbid = 1
wall = 2
castle = 3
margin = 4
spawn = 5
spawn_zone = 6
mountain = 7
turret = 8

# tamaño del tablero (24x24)
width_gameboard = 720
height_gameboard = 720
offsetX = 280  # (1280 - 720) / 2
grid_size = 30
col = 24
row = 24

# --- CONFIGURACIÓN DE CONTROLES REBINDABLES ---
config = configparser.ConfigParser()
config_file = "config.ini"

if not os.path.exists(config_file):
    config["Keybinds"] = {
        "sell": "q",
        "wall": "w",
        "slot_1": "1",
        "slot_2": "2",
        "slot_3": "3",
        "slot_4": "4"
    }
    with open(config_file, "w") as f:
        config.write(f)
else:
    config.read(config_file)

def get_key(key_str):
    return getattr(pygame, f"K_{key_str.lower()}")

controls = {
    "sell": get_key(config["Keybinds"]["sell"]),
    "wall": get_key(config["Keybinds"]["wall"]),
    "slot_1": get_key(config["Keybinds"]["slot_1"]),
    "slot_2": get_key(config["Keybinds"]["slot_2"]),
    "slot_3": get_key(config["Keybinds"]["slot_3"]),
    "slot_4": get_key(config["Keybinds"]["slot_4"])
}

# --- VARIABLES GLOBALES Y ESTADOS ---
current_tool = None
game_state = "PLAYING"
unlocked_towers_order = ["arrow"]
level_up_options = []
card_rects = []

pygame.font.init()
ui_font = pygame.font.SysFont("Arial", 24, bold=True)

# --- ECONOMÍA Y PROGRESIÓN ---
player_gold = 100
player_level = 1
player_xp = 0
xp_to_next_level = 50

global_damage_buff = 0.0
castle_max_hp = 100
castle_hp = castle_max_hp
structures_hp = {}

tower_levels = {"arrow": 1, "fireball": 0, "kunai": 0, "laser": 0}

tower_limits = {
    "arrow": [0, 4, 4, 4, 5, 5, 5, 6, 6],
    "fireball": [0, 2, 2, 2, 3, 3, 3, 4, 4],
    "kunai": [0, 2, 2, 2, 3, 3, 3, 4, 4],
    "laser": [0, 2, 2, 2, 3, 3, 3, 4, 4]
}

# --- LÓGICA DE SPAWNS AVANZADA Y CALENDARIO ---
spawn_counts = {"North": 0, "South": 0, "East": 0, "West": 0}
existing_spawns_pos = {"North": [], "South": [], "East": [], "West": []}

forced_initial_spawns = random.choice([["North", "South"], ["East", "West"]])
random.shuffle(forced_initial_spawns)

spawn_schedule = [
    (90, "balanced"),
    (180, "balanced"),
    (270, "balanced"),
    (360, "balanced"),
    (450, "balanced"),
    (540, "balanced"),
    (630, "balanced"),
    (720, "balanced"),
    (810, "wildcard"),
    (900, "wildcard"),
]

random_time_1 = random.uniform(910, 1040)
random_time_2 = random.uniform(910, 1040)
spawn_schedule.extend([(random_time_1, "balanced"), (random_time_2, "balanced"), (1050, "wildcard")])
spawn_schedule.sort(key=lambda x: x[0])


# --- FUNCIONES ---
def get_valid_border(spawn_type):
    if spawn_type == "wildcard":
        print("¡SPAWN COMODÍN ACTIVADO!")
        return random.choice(["North", "South", "East", "West"])
    else:
        if len(forced_initial_spawns) > 0:
            return forced_initial_spawns.pop(0)

        min_count = min(spawn_counts.values())
        valid_borders = [b for b, c in spawn_counts.items() if c - min_count < 2]
        if not valid_borders:
            valid_borders = ["North", "South", "East", "West"]
        return random.choice(valid_borders)


def setup_spawn_point(spawn_group, spawn_type="balanced"):
    side = get_valid_border(spawn_type)
    if not side:
        return

    valid_pos = False
    attempts = 0
    center = 0

    while not valid_pos and attempts < 50:
        center = random.randint(margin, col - margin - 1)
        conflict = False
        for pos in existing_spawns_pos[side]:
            if abs(center - pos) <= 1:
                conflict = True
                break
        if not conflict:
            valid_pos = True
        attempts += 1

    if not valid_pos:
        return

    existing_spawns_pos[side].append(center)
    spawn_counts[side] += 1

    if side == "North":
        grid[0][center] = spawn_zone
        new_spawn = Spawn(center, -1, side)
    elif side == "South":
        grid[23][center] = spawn_zone
        new_spawn = Spawn(center, 24, side)
    elif side == "West":
        grid[center][0] = spawn_zone
        new_spawn = Spawn(-1, center, side)
    elif side == "East":
        grid[center][23] = spawn_zone
        new_spawn = Spawn(24, center, side)

    spawn_group.add(new_spawn)


def get_level_up_cards():
    pool = []

    for t_id in ["arrow", "fireball", "kunai", "laser"]:
        lvl = tower_levels[t_id]
        if lvl == 0:
            pool.append({"title": f"Desbloquear {t_id.capitalize()}", "type": "upgrade", "id": t_id})
        elif lvl < 8:
            pool.append({"title": f"Mejorar {t_id.capitalize()} (Nv{lvl + 1})", "type": "upgrade", "id": t_id})

    if global_damage_buff < 1.0:
        pool.append({"title": "Daño Global +10%", "type": "dmg_buff"})

    random.shuffle(pool)
    cards = pool[:3]

    fallbacks = [
        {"title": "Bolsa de Oro (+50)", "type": "gold"},
        {"title": "Curar Castillo 50%", "type": "heal"}
    ]

    while len(cards) < 3:
        cards.append(random.choice(fallbacks))

    return cards


# --- INICIALIZACIÓN DE PYGAME ---
pygame.init()
screen = pygame.display.set_mode((1280, 720), pygame.RESIZABLE)
base_res = (1280, 720)
gameboard = pygame.Surface(base_res)
clock = pygame.time.Clock()
running = True

# --- MATRIZ Y TABLERO ---
grid = [[0 for _ in range(col)] for _ in range(row)]

for y in range(row):
    for x in range(col):
        if x == 0 or x == col - 1 or y == 0 or y == row - 1:
            grid[y][x] = mountain
        elif x < margin or x >= col - margin or y < margin or y >= row - margin:
            grid[y][x] = spawn_zone
        else:
            grid[y][x] = allow

grid[11][11] = castle
grid[11][12] = castle
grid[12][11] = castle
grid[12][12] = castle

grid_overlay = pygame.Surface((width_gameboard, height_gameboard), pygame.SRCALPHA)
white_grid = (255, 255, 255, 150)

for x in range(0, col):
    for y in range(0, row):
        if grid[y][x] == allow:
            pygame.draw.rect(grid_overlay, white_grid, (x * grid_size, y * grid_size, grid_size, grid_size), 1)

show_grid = True

# --- OBJETOS Y GRUPOS ---
player_group = pygame.sprite.Group()
enemy_group = pygame.sprite.Group()
bullet_group = pygame.sprite.Group()
spawn_group = pygame.sprite.Group()

castle_obj = ArrowCastle(640, 360)
player_group.add(castle_obj)

for _ in range(2):
    setup_spawn_point(spawn_group, "balanced")

# --- RELOJ Y DIFICULTAD ---
game_time = 0.0
current_minute = 0
difficulty_multiplier = 1.0

# --- BUCLE PRINCIPAL ---
while running:
    mouseX, mouseY = pygame.mouse.get_pos()

    limitW = offsetX + (margin * grid_size)
    limitE = offsetX + (col - margin) * grid_size
    limitN = margin * grid_size
    limitS = (row - margin) * grid_size

    on_grid = limitW <= mouseX < limitE and limitN <= mouseY < limitS

    if on_grid:
        hoverCol = (mouseX - offsetX) // grid_size
        hoverRow = mouseY // grid_size

    # --- EVENTOS ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.MOUSEBUTTONDOWN:
            if game_state == "LEVEL_UP":
                for i, rect in enumerate(card_rects):
                    if rect.collidepoint(mouseX, mouseY):
                        chosen = level_up_options[i]
                        if chosen["type"] == "upgrade":
                            t_id = chosen["id"]
                            tower_levels[t_id] += 1
                            if tower_levels[t_id] == 1 and t_id not in unlocked_towers_order:
                                unlocked_towers_order.append(t_id)
                        elif chosen["type"] == "heal":
                            castle_hp = min(castle_max_hp, castle_hp + (castle_max_hp // 2))
                        elif chosen["type"] == "dmg_buff":
                            global_damage_buff += 0.1
                        elif chosen["type"] == "gold":
                            player_gold += 50

                        game_state = "PLAYING"
                        title_text = chosen["title"]
                        print(f"Carta elegida: {title_text}")

            elif game_state == "PLAYING" and on_grid:
                if current_tool == "sell":
                    if grid[hoverRow][hoverCol] in [wall, turret]:
                        cell_type = grid[hoverRow][hoverCol]
                        grid[hoverRow][hoverCol] = allow
                        coords = (hoverRow, hoverCol)
                        if coords in structures_hp:
                            del structures_hp[coords]

                        if cell_type == wall:
                            player_gold += 2
                            print("Muro vendido.")
                        elif cell_type == turret:
                            for t in player_group:
                                if "castle" in type(t).__name__.lower():
                                    continue
                                if hasattr(t, "x") and hasattr(t, "y"):
                                    t_col = int((t.x - offsetX) // grid_size)
                                    t_row = int(t.y // grid_size)
                                    if t_col == hoverCol and t_row == hoverRow:
                                        t.kill()
                                        player_gold += 10
                                        print("Torre vendida. Oro devuelto: 10")
                                        break

                elif grid[hoverRow][hoverCol] == allow:
                    if current_tool == "wall":
                        if player_gold >= 5:
                            player_gold -= 5
                            grid[hoverRow][hoverCol] = wall
                            structures_hp[(hoverRow, hoverCol)] = 150
                            print("Muro construido. Oro:", player_gold)
                    elif current_tool in ["arrow", "fireball", "kunai", "laser"]:
                        lvl = tower_levels[current_tool]
                        current_count = sum(
                            1 for t in player_group if type(t).__name__.lower().startswith(current_tool) and "castle" not in type(t).__name__.lower())

                        if current_count < tower_limits[current_tool][lvl]:
                            costs = {"arrow": 18, "fireball": 25, "kunai": 29, "laser": 33}
                            cost = costs[current_tool]
                            if player_gold >= cost:
                                player_gold -= cost
                                grid[hoverRow][hoverCol] = turret
                                structures_hp[(hoverRow, hoverCol)] = 80

                                posX_px = offsetX + (hoverCol * grid_size) + (grid_size // 2)
                                posY_px = (hoverRow * grid_size) + (grid_size // 2)

                                if current_tool == "arrow":
                                    new_tower = ArrowTower(posX_px, posY_px)
                                elif current_tool == "fireball":
                                    new_tower = FireballTower(posX_px, posY_px)
                                elif current_tool == "kunai":
                                    new_tower = KunaiTower(posX_px, posY_px)
                                elif current_tool == "laser":
                                    new_tower = LaserTower(posX_px, posY_px)

                                player_group.add(new_tower)
                                print(f"Torre {current_tool} construida ({current_count + 1}/{tower_limits[current_tool][lvl]}).")
                        else:
                            print(f"Límite de torres {current_tool} alcanzado para el nivel {lvl}.")

        if event.type == pygame.KEYDOWN:
            if game_state == "PLAYING":
                if event.key == pygame.K_g:
                    show_grid = not show_grid
                elif event.key == pygame.K_ESCAPE:
                    current_tool = None
                elif event.key == controls["sell"]:
                    current_tool = "sell" if current_tool != "sell" else None
                elif event.key == controls["wall"]:
                    current_tool = "wall" if current_tool != "wall" else None
                elif event.key == controls["slot_1"] and len(unlocked_towers_order) > 0:
                    t = unlocked_towers_order[0]
                    current_tool = t if current_tool != t else None
                elif event.key == controls["slot_2"] and len(unlocked_towers_order) > 1:
                    t = unlocked_towers_order[1]
                    current_tool = t if current_tool != t else None
                elif event.key == controls["slot_3"] and len(unlocked_towers_order) > 2:
                    t = unlocked_towers_order[2]
                    current_tool = t if current_tool != t else None
                elif event.key == controls["slot_4"] and len(unlocked_towers_order) > 3:
                    t = unlocked_towers_order[3]
                    current_tool = t if current_tool != t else None

    # --- DIBUJADO BASE ---
    gameboard.fill("#222222")
    pygame.draw.rect(gameboard, "#000000", (offsetX, 0, width_gameboard, height_gameboard))

    for y in range(24):
        for x in range(24):
            posY = y * grid_size
            posX = offsetX + (x * grid_size)

            if grid[y][x] == allow:
                pygame.draw.rect(gameboard, "green", (posX, posY, grid_size, grid_size))
            elif grid[y][x] == forbid:
                pygame.draw.rect(gameboard, "gray", (posX, posY, grid_size, grid_size))
            elif grid[y][x] == spawn_zone:
                pygame.draw.rect(gameboard, "darkgray", (posX, posY, grid_size, grid_size))
            elif grid[y][x] == castle:
                pygame.draw.rect(gameboard, "yellow", (posX, posY, grid_size, grid_size))
            elif grid[y][x] == wall:
                pygame.draw.rect(gameboard, "brown", (posX, posY, grid_size, grid_size))
            elif grid[y][x] == turret:
                pygame.draw.rect(gameboard, "blue", (posX, posY, grid_size, grid_size))
            elif grid[y][x] == spawn:
                pygame.draw.rect(gameboard, "purple", (posX, posY, grid_size, grid_size))
            elif grid[y][x] == mountain:
                pygame.draw.rect(gameboard, "orange", (posX, posY, grid_size, grid_size))

    if show_grid:
        gameboard.blit(grid_overlay, (offsetX, 0))

    if on_grid and game_state == "PLAYING":
        posX_trans = offsetX + (hoverCol * grid_size)
        posY_trans = hoverRow * grid_size
        surface_trans = pygame.Surface((grid_size, grid_size), pygame.SRCALPHA)
        current_cell = grid[hoverRow][hoverCol]

        if current_tool == "sell":
            if current_cell in [wall, turret]:
                surface_trans.fill((255, 0, 0, 150))
            else:
                surface_trans.fill((255, 0, 0, 40))
        elif current_tool is not None and current_cell != allow:
            surface_trans.fill((255, 0, 0, 70))
        elif current_tool == "wall":
            surface_trans.fill((165, 42, 42, 120))
        elif current_tool in ["arrow", "fireball", "kunai", "laser"]:
            pygame.draw.circle(surface_trans, (0, 0, 255, 120), (grid_size // 2, grid_size // 2), 10)
        else:
            surface_trans.fill((255, 255, 255, 40))

        gameboard.blit(surface_trans, (posX_trans, posY_trans))

    player_group.draw(gameboard)
    enemy_group.draw(gameboard)
    bullet_group.draw(gameboard)

    # UI Texto
    seconds = int(game_time % 60)
    time_str = f"{current_minute:02d}:{seconds:02d}"
    ui_text = ui_font.render(
        f"Tiempo: {time_str} | Nvl: {player_level} | Oro: {player_gold} | Castillo HP: {castle_hp}/{castle_max_hp}",
        True, "white"
    )
    gameboard.blit(ui_text, (20, 20))

    # UI Nivel
    if game_state == "LEVEL_UP":
        overlay = pygame.Surface((1280, 720), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        gameboard.blit(overlay, (0, 0))

        card_width = 220
        card_height = 300
        spacing = 40
        start_x = offsetX + (width_gameboard - (card_width * 3 + spacing * 2)) // 2
        start_y = 200

        card_rects = []
        title_text = ui_font.render("¡SUBIDA DE NIVEL! ELIGE RECOMPENSA", True, "yellow")
        gameboard.blit(title_text, (offsetX + 150, 100))

        for i, card in enumerate(level_up_options):
            cx = start_x + i * (card_width + spacing)
            cy = start_y
            rect = pygame.Rect(cx, cy, card_width, card_height)
            card_rects.append(rect)

            pygame.draw.rect(gameboard, "#112233", rect)
            pygame.draw.rect(gameboard, "white", rect, 3)

            text_surf = ui_font.render(card["title"], True, "white")
            gameboard.blit(text_surf, (cx + 10, cy + 130))

    screensize = screen.get_size()
    rescaled_gameboard = pygame.transform.scale(gameboard, screensize)
    screen.blit(rescaled_gameboard, (0, 0))

    pygame.display.flip()
    dt = clock.tick(60) / 1000

    # --- LÓGICA DE JUEGO (SOLO SI NO ESTÁ PAUSADO) ---
    if game_state == "PLAYING":
        game_time += dt
        current_minute = int(game_time // 60)
        difficulty_multiplier = round(1 + (current_minute / 8) ** 1.8, 2)

        if len(spawn_schedule) > 0:
            next_spawn_time, next_spawn_type = spawn_schedule[0]
            if game_time >= next_spawn_time:
                setup_spawn_point(spawn_group, next_spawn_type)
                spawn_schedule.pop(0)

        spawn_group.update(dt, enemy_group, grid, offsetX, grid_size)
        enemy_group.update(dt, grid, enemy_group=enemy_group, structures_hp=structures_hp)

        collisions = pygame.sprite.groupcollide(enemy_group, enemy_group, False, False)
        for enemy, others in collisions.items():
            push_final = pygame.math.Vector2(0, 0)
            for other in others:
                if other == enemy:
                    continue
                distance = enemy.pos.distance_to(other.pos)
                if distance < (enemy.radius + other.radius):
                    if distance == 0:
                        enemy.pos += pygame.math.Vector2(random.uniform(-1, 1), random.uniform(-1, 1))
                        continue
                    push_final += (enemy.pos - other.pos).normalize() * 60.0

            if push_final.length() > 0:
                if enemy.is_attacking:
                    tangent = pygame.math.Vector2(-enemy.dir_norm.y, enemy.dir_norm.x)
                    dot_product = push_final.dot(tangent)
                    if abs(dot_product) < 5:
                        dot_product += random.choice([-20.0, 20.0])
                    enemy.pos += tangent * dot_product * dt
                else:
                    enemy.pos += push_final.normalize() * 40.0 * dt
            enemy.rect.center = (round(enemy.pos.x), round(enemy.pos.y))

        player_group.update(dt, enemy_group, bullet_group)
        bullet_group.update(dt)

        # --- COLISIONES OPTIMIZADAS ---
        hits = pygame.sprite.groupcollide(bullet_group, enemy_group, False, False)

        for arrow, enemies_hit in hits.items():
            for enemy in enemies_hit:
                if enemy not in arrow.hit_enemies:
                    arrow.hit_enemies.add(enemy)

                    final_damage = arrow.damage * (1.0 + global_damage_buff)

                    if hasattr(arrow, "aoe_radius"):
                        for e in enemy_group:
                            if pygame.math.Vector2(arrow.rect.center).distance_to(e.pos) <= arrow.aoe_radius:
                                e.take_damage(final_damage)
                                if e.health <= 0:
                                    player_gold += e.gold_value
                                    player_xp += e.xp_value
                                    e.kill()
                    else:
                        enemy.take_damage(final_damage)
                        if enemy.health <= 0:
                            player_gold += enemy.gold_value
                            player_xp += enemy.xp_value
                            enemy.kill()

                    if player_xp >= xp_to_next_level:
                        player_xp -= xp_to_next_level
                        player_level += 1
                        castle_max_hp += 15
                        castle_hp += 15
                        if player_level < 60:
                            xp_to_next_level += 25 + (player_level * 5)
                        else:
                            xp_to_next_level = int(xp_to_next_level * 1.5)
                        game_state = "LEVEL_UP"
                        level_up_options = get_level_up_cards()

                    arrow.pierce -= 1
                    if arrow.pierce <= 0:
                        arrow.kill()
                        break

            if enemy.health <= 0:
                enemy.kill()

pygame.quit()