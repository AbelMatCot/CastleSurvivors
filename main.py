import pygame
import random
import configparser
import os
import sys


from Entities.Player.castle import ArrowCastle, FireballCastle, KunaiCastle, LaserCastle
from Entities.Player.towers import ArrowTower, FireballTower, KunaiTower, LaserTower, TOWER_STATS
from Entities.spawn import Spawn
from Entities.effects import Effect

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

width_gameboard = 720
height_gameboard = 720
offsetX = 280
grid_size = 30
col = 24
row = 24

time_scale = 1.0

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
ui_font_large = pygame.font.SysFont("Arial", 28, bold=True)
ui_font_medium = pygame.font.SysFont("Arial", 20, bold=True)
ui_font_small = pygame.font.SysFont("Arial", 14, bold=True)

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
    (90, "balanced"), (180, "balanced"), (270, "balanced"), (360, "balanced"),
    (450, "balanced"), (540, "balanced"), (630, "balanced"), (720, "balanced"),
    (810, "wildcard"), (900, "wildcard"),
]
random_time_1 = random.uniform(910, 1040)
random_time_2 = random.uniform(910, 1040)
spawn_schedule.extend([(random_time_1, "balanced"), (random_time_2, "balanced"), (1050, "wildcard")])
spawn_schedule.sort(key=lambda x: x[0])


# --- FUNCIONES ---
def get_valid_border(spawn_type):
    if spawn_type == "wildcard":
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
    if not side: return

    valid_pos = False
    attempts = 0
    center = 0

    while not valid_pos and attempts < 50:
        # random.randint incluye ambos extremos. 2 evita la esquina (0) y su adyacente (1).
        center = random.randint(2, col - 3)
        conflict = False
        for pos in existing_spawns_pos[side]:
            if abs(center - pos) <= 2:
                conflict = True
                break
        if not conflict:
            valid_pos = True
        attempts += 1

    if not valid_pos: return

    existing_spawns_pos[side].append(center)
    spawn_counts[side] += 1

    if side == "North":
        for i in range(0, margin): grid[i][center] = spawn_zone
        new_spawn = Spawn(center, -1, side)
    elif side == "South":
        for i in range(row - margin, row): grid[i][center] = spawn_zone
        new_spawn = Spawn(center, row, side)
    elif side == "West":
        for i in range(0, margin): grid[center][i] = spawn_zone
        new_spawn = Spawn(-1, center, side)
    elif side == "East":
        for i in range(col - margin, col): grid[center][i] = spawn_zone
        new_spawn = Spawn(col, center, side)

    spawn_group.add(new_spawn)
    fx = offsetX + (new_spawn.spawn_x * grid_size) + (grid_size / 2)
    fy = (new_spawn.spawn_y * grid_size) + (grid_size / 2)
    dust = Effect(fx, fy, dust_sheet, scale_size=60, fps=12)
    effects_group.add(dust)


def get_level_up_cards():
    pool = []
    for t_id in ["arrow", "fireball", "kunai", "laser"]:
        lvl = tower_levels[t_id]
        if lvl == 0:
            pool.append({"title": f"Unlock {t_id.capitalize()}", "type": "upgrade", "id": t_id})
        elif lvl < 8:
            pool.append({"title": f"Upgrade {t_id.capitalize()} (Lvl{lvl + 1})", "type": "upgrade", "id": t_id})

    if global_damage_buff < 1.0:
        pool.append({"title": "Global Damage +10%", "type": "dmg_buff"})

    random.shuffle(pool)
    cards = pool[:3]
    fallbacks = [{"title": "Gold Sack (+50)", "type": "gold"}, {"title": "Heal Castle 50%", "type": "heal"}]
    while len(cards) < 3:
        cards.append(random.choice(fallbacks))
    return cards


def get_tile(sheet, x, y, width, height, scale_size):
    image = pygame.Surface((width, height), pygame.SRCALPHA)
    image.blit(sheet, (0, 0), (x, y, width, height))
    return pygame.transform.scale(image, (scale_size, scale_size))


def get_tile_for_cell(col_idx, row_idx, target_types, tile_dict, oob_is_target=True):
    N = (row_idx == 0 and oob_is_target) or (row_idx > 0 and grid[row_idx - 1][col_idx] in target_types)
    S = (row_idx == row - 1 and oob_is_target) or (row_idx < row - 1 and grid[row_idx + 1][col_idx] in target_types)
    W = (col_idx == 0 and oob_is_target) or (col_idx > 0 and grid[row_idx][col_idx - 1] in target_types)
    E = (col_idx == col - 1 and oob_is_target) or (col_idx < col - 1 and grid[row_idx][col_idx + 1] in target_types)
    key = (int(N), int(S), int(W), int(E))
    return tile_dict.get(key, tile_dict.get((1, 1, 1, 1)))


# =====================================================================
# --- MOTOR DE UI ---
# =====================================================================

def extract_sprite(sheet, col, row, cols_total, rows_total):
    w = sheet.get_width() // cols_total
    h = sheet.get_height() // rows_total
    sub = sheet.subsurface((col * w, row * h, w, h))
    bounding = sub.get_bounding_rect()
    if bounding.width > 0 and bounding.height > 0:
        return sub.subsurface(bounding)
    return sub


def draw_paper(surface, sheet, rect):
    parts = [extract_sprite(sheet, c, r, 3, 3) for r in range(3) for c in range(3)]
    tl, tc, tr = parts[0], parts[1], parts[2]
    ml, mc, mr = parts[3], parts[4], parts[5]
    bl, bc, br = parts[6], parts[7], parts[8]

    scale = 2
    cw, ch = tl.get_width() * scale, tl.get_height() * scale
    cw = min(cw, rect.width // 2)
    ch = min(ch, rect.height // 2)

    mid_w = max(0, rect.width - cw * 2)
    mid_h = max(0, rect.height - ch * 2)

    def blit_safe(part, dx, dy, dw, dh):
        if dw > 0 and dh > 0:
            surface.blit(pygame.transform.scale(part, (int(dw), int(dh))), (int(dx), int(dy)))

    blit_safe(tl, rect.x, rect.y, cw, ch)
    blit_safe(tc, rect.x + cw, rect.y, mid_w, ch)
    blit_safe(tr, rect.right - cw, rect.y, cw, ch)

    blit_safe(ml, rect.x, rect.y + ch, cw, mid_h)
    blit_safe(mc, rect.x + cw, rect.y + ch, mid_w, mid_h)
    blit_safe(mr, rect.right - cw, rect.y + ch, cw, mid_h)

    blit_safe(bl, rect.x, rect.bottom - ch, cw, ch)
    blit_safe(bc, rect.x + cw, rect.bottom - ch, mid_w, ch)
    blit_safe(br, rect.right - cw, rect.bottom - ch, cw, ch)


def draw_9_slice_button(surface, image, rect, edge_px=8):
    w, h = image.get_size()
    e_x = min(edge_px, w // 2 - 1, rect.width // 2)
    e_y = min(edge_px, h // 2 - 1, rect.height // 2)

    src_parts = [
        (0, 0, e_x, e_y), (e_x, 0, w - e_x * 2, e_y), (w - e_x, 0, e_x, e_y),
        (0, e_y, e_x, h - e_y * 2), (e_x, e_y, w - e_x * 2, h - e_y * 2), (w - e_x, e_y, e_x, h - e_y * 2),
        (0, h - e_y, e_x, e_y), (e_x, h - e_y, w - e_x * 2, e_y), (w - e_x, h - e_y, e_x, e_y)
    ]
    o_x, o_y = e_x, e_y
    dst_parts = [
        (rect.x, rect.y, o_x, o_y),
        (rect.x + o_x, rect.y, rect.width - o_x * 2, o_y),
        (rect.right - o_x, rect.y, o_x, o_y),
        (rect.x, rect.y + o_y, o_x, rect.height - o_y * 2),
        (rect.x + o_x, rect.y + o_y, rect.width - o_x * 2, rect.height - o_y * 2),
        (rect.right - o_x, rect.y + o_y, o_x, rect.height - o_y * 2),
        (rect.x, rect.bottom - o_y, o_x, o_y),
        (rect.x + o_x, rect.bottom - o_y, rect.width - o_x * 2, o_y),
        (rect.right - o_x, rect.bottom - o_y, o_x, o_y)
    ]

    for src, dst in zip(src_parts, dst_parts):
        if src[2] > 0 and src[3] > 0 and dst[2] > 0 and dst[3] > 0:
            surface.blit(pygame.transform.scale(image.subsurface(src), (int(dst[2]), int(dst[3]))),
                         (int(dst[0]), int(dst[1])))


def draw_bar(surface, x, y, w, h, ratio, base_sheet, fill_sheet):
    left = extract_sprite(base_sheet, 0, 0, 3, 1)
    mid = extract_sprite(base_sheet, 1, 0, 3, 1)
    right = extract_sprite(base_sheet, 2, 0, 3, 1)

    edge_w = min(w // 2, int(h * (left.get_width() / left.get_height())))
    mid_w = max(0, w - (edge_w * 2))

    surface.blit(pygame.transform.scale(left, (edge_w, h)), (x, y))
    if mid_w > 0:
        surface.blit(pygame.transform.scale(mid, (mid_w, h)), (x + edge_w, y))
    surface.blit(pygame.transform.scale(right, (edge_w, h)), (x + edge_w + mid_w, y))

    if ratio > 0:
        fill_crop = extract_sprite(fill_sheet, 0, 0, 1, 1)
        pad_x = int(edge_w * 0.45)
        pad_y = int(h * 0.25)
        inner_w = max(1, w - (pad_x * 2))
        inner_h = max(1, h - (pad_y * 2))
        fill_w = max(1, int(inner_w * ratio))
        surface.blit(pygame.transform.scale(fill_crop, (fill_w, inner_h)), (x + pad_x, y + pad_y))


def draw_ribbon(surface, x, y, w, h, sheet, row=0):
    left = extract_sprite(sheet, 0, row, 3, 2)
    mid = extract_sprite(sheet, 1, row, 3, 2)
    right = extract_sprite(sheet, 2, row, 3, 2)

    edge_w = min(w // 2, int(h * (left.get_width() / left.get_height())))
    mid_w = max(0, w - (edge_w * 2))

    surface.blit(pygame.transform.scale(left, (edge_w, h)), (x, y))
    if mid_w > 0:
        surface.blit(pygame.transform.scale(mid, (mid_w, h)), (x + edge_w, y))
    surface.blit(pygame.transform.scale(right, (edge_w, h)), (x + edge_w + mid_w, y))


# --- INICIALIZACIÓN DE PYGAME ---
pygame.init()
screen = pygame.display.set_mode((1280, 720), pygame.RESIZABLE)
base_res = (1280, 720)
gameboard = pygame.Surface(base_res)
clock = pygame.time.Clock()
running = True

# --- CARGA DE ASSETS ---
path_color2 = os.path.join("Assets", "Sprites", "Tiles", "Tilemap_color2.png")
path_color4 = os.path.join("Assets", "Sprites", "Tiles", "Tilemap_color4.png")
path_elevation = os.path.join("Assets", "Sprites", "Tiles", "Tilemap_Elevation.png")

try:
    color2_sheet = pygame.image.load(path_color2).convert_alpha()
    color4_sheet = pygame.image.load(path_color4).convert_alpha()
    elevation_sheet = pygame.image.load(path_elevation).convert_alpha()
except FileNotFoundError:
    print("ERROR: Faltan las texturas de terreno en la carpeta Assets.")
    pygame.quit()
    sys.exit()

effects_group = pygame.sprite.Group()
explosion_sheet = pygame.image.load(os.path.join("Assets", "Sprites", "Effects", "Explosion_01.png")).convert_alpha()
dust_sheet = pygame.image.load(os.path.join("Assets", "Sprites", "Effects", "Dust_02.png")).convert_alpha()

ui_path = os.path.join("Assets", "UI")
try:
    btn_sheet = pygame.image.load(os.path.join(ui_path, "Button_Hover.png")).convert_alpha()
    ribbon_sheet = pygame.image.load(os.path.join(ui_path, "SmallRibbons.png")).convert_alpha()
    special_paper_sheet = pygame.image.load(os.path.join(ui_path, "SpecialPaper.png")).convert_alpha()
    big_bar_base = pygame.image.load(os.path.join(ui_path, "BigBar_Base.png")).convert_alpha()
    big_bar_fill = pygame.image.load(os.path.join(ui_path, "BigBar_Fill.png")).convert_alpha()
    small_bar_base = pygame.image.load(os.path.join(ui_path, "SmallBar_Base.png")).convert_alpha()
    small_bar_fill = pygame.image.load(os.path.join(ui_path, "SmallBar_Fill.png")).convert_alpha()
except FileNotFoundError as e:
    print(f"ERROR UI: No se encontró la imagen {e}. Revisa Assets/UI")
    pygame.quit()
    sys.exit()

btn_small_img = extract_sprite(btn_sheet, 0, 0, 2, 3)
btn_wide_img = extract_sprite(btn_sheet, 0, 1, 2, 3)

background_tile = get_tile(color4_sheet, 64, 64, 64, 64, grid_size)
buildable_tiles = {
    (1, 1, 1, 1): get_tile(color2_sheet, 64, 64, 64, 64, grid_size),
    (0, 1, 1, 1): get_tile(color2_sheet, 64, 0, 64, 64, grid_size),
    (1, 0, 1, 1): get_tile(color2_sheet, 64, 128, 64, 64, grid_size),
    (1, 1, 0, 1): get_tile(color2_sheet, 0, 64, 64, 64, grid_size),
    (1, 1, 1, 0): get_tile(color2_sheet, 128, 64, 64, 64, grid_size),
    (0, 1, 0, 1): get_tile(color2_sheet, 0, 0, 64, 64, grid_size),
    (0, 1, 1, 0): get_tile(color2_sheet, 128, 0, 64, 64, grid_size),
    (1, 0, 0, 1): get_tile(color2_sheet, 0, 128, 64, 64, grid_size),
    (1, 0, 1, 0): get_tile(color2_sheet, 128, 128, 64, 64, grid_size),
}

mountain_tiles = {
    (1, 0, 1, 1): get_tile(elevation_sheet, 64, 192, 64, 64, grid_size),
    (0, 1, 1, 1): get_tile(elevation_sheet, 64, 0, 64, 64, grid_size),
    (1, 1, 0, 1): get_tile(elevation_sheet, 0, 64, 64, 64, grid_size),
    (1, 1, 1, 0): get_tile(elevation_sheet, 128, 64, 64, 64, grid_size),
    (1, 0, 0, 1): get_tile(elevation_sheet, 0, 192, 64, 64, grid_size),
    (1, 0, 1, 0): get_tile(elevation_sheet, 128, 192, 64, 64, grid_size),
    (0, 1, 0, 1): get_tile(elevation_sheet, 0, 0, 64, 64, grid_size),
    (0, 1, 1, 0): get_tile(elevation_sheet, 128, 0, 64, 64, grid_size),
    (1, 1, 1, 1): get_tile(elevation_sheet, 64, 64, 64, 64, grid_size),
}

grid = [[0 for _ in range(col)] for _ in range(row)]
for y in range(row):
    for x in range(col):
        if x == 0 or x == col - 1 or y == 0 or y == row - 1:
            grid[y][x] = mountain
        elif x < margin or x >= col - margin or y < margin or y >= row - margin:
            grid[y][x] = forbid
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

show_grid = False

player_group = pygame.sprite.Group()
enemy_group = pygame.sprite.Group()
bullet_group = pygame.sprite.Group()
spawn_group = pygame.sprite.Group()

castle_obj = ArrowCastle(640, 360)
player_group.add(castle_obj)

for _ in range(2):
    setup_spawn_point(spawn_group, "balanced")

game_time = 0.0
current_minute = 0
difficulty_multiplier = 1.0

# --- BUCLE PRINCIPAL ---
while running:
    keys = pygame.key.get_pressed()
    time_scale = 1.0
    if keys[pygame.K_x]:
        time_scale = 4.0
    elif keys[pygame.K_z]:
        time_scale = 2.0

    mouseX, mouseY = pygame.mouse.get_pos()
    limitW = offsetX + (margin * grid_size)
    limitE = offsetX + (col - margin) * grid_size
    limitN = margin * grid_size
    limitS = (row - margin) * grid_size

    on_grid = limitW <= mouseX < limitE and limitN <= mouseY < limitS

    if on_grid:
        hoverCol = (mouseX - offsetX) // grid_size
        hoverRow = mouseY // grid_size

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

            elif game_state == "PLAYING" and on_grid:
                if current_tool == "sell":
                    if grid[hoverRow][hoverCol] in [wall, turret]:
                        cell_type = grid[hoverRow][hoverCol]
                        grid[hoverRow][hoverCol] = allow
                        coords = (hoverRow, hoverCol)
                        if coords in structures_hp: del structures_hp[coords]

                        if cell_type == wall:
                            player_gold += 2
                        elif cell_type == turret:
                            for t in player_group:
                                if "castle" in type(t).__name__.lower(): continue
                                if hasattr(t, "x") and hasattr(t, "y"):
                                    t_col = int((t.x - offsetX) // grid_size)
                                    t_row = int(t.y // grid_size)
                                    if t_col == hoverCol and t_row == hoverRow:
                                        t.kill()
                                        player_gold += 10
                                        break

                elif grid[hoverRow][hoverCol] == allow:
                    if current_tool == "wall":
                        if player_gold >= 5:
                            player_gold -= 5
                            grid[hoverRow][hoverCol] = wall
                            structures_hp[(hoverRow, hoverCol)] = 150
                    elif current_tool in ["arrow", "fireball", "kunai", "laser"]:
                        lvl = tower_levels[current_tool]
                        stats = TOWER_STATS[current_tool][max(1, lvl)]
                        current_count = sum(1 for t in player_group if type(t).__name__.lower().startswith(
                            current_tool) and "castle" not in type(t).__name__.lower())

                    if current_count < stats["limit"]:
                        cost = stats["cost"]
                        if player_gold >= cost:
                            player_gold -= cost
                            grid[hoverRow][hoverCol] = turret
                            structures_hp[(hoverRow, hoverCol)] = 80
                            posX_px = offsetX + (hoverCol * grid_size) + (grid_size // 2)
                            posY_px = (hoverRow * grid_size) + (grid_size // 2)

                            if current_tool == "arrow":
                                player_group.add(ArrowTower(posX_px, posY_px))
                            elif current_tool == "fireball":
                                player_group.add(FireballTower(posX_px, posY_px))
                            elif current_tool == "kunai":
                                player_group.add(KunaiTower(posX_px, posY_px))
                            elif current_tool == "laser":
                                player_group.add(LaserTower(posX_px, posY_px))

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

    # --- DIBUJADO DE CAPAS BASE Y TERRENO ---
    gameboard.fill("#222222")
    pygame.draw.rect(gameboard, "#000000", (offsetX, 0, width_gameboard, height_gameboard))

    for y in range(row):
        for x in range(col):
            posX = offsetX + (x * grid_size)
            posY = y * grid_size
            gameboard.blit(background_tile, (posX, posY))

    buildable_targets = [allow, castle, wall, turret]

    for y in range(row):
        for x in range(col):
            posX = offsetX + (x * grid_size)
            posY = y * grid_size
            cell = grid[y][x]

            if cell in buildable_targets:
                tile = get_tile_for_cell(x, y, buildable_targets, buildable_tiles, False)
                gameboard.blit(tile, (posX, posY))
            elif cell == mountain:
                tile = get_tile_for_cell(x, y, [mountain], mountain_tiles, True)
                gameboard.blit(tile, (posX, posY))

            if cell == castle:
                pygame.draw.rect(gameboard, "yellow", (posX, posY, grid_size, grid_size))
            elif cell == wall:
                pygame.draw.rect(gameboard, "brown", (posX, posY, grid_size, grid_size))
            elif cell == turret:
                pygame.draw.rect(gameboard, "blue", (posX, posY, grid_size, grid_size))

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
    effects_group.draw(gameboard)

    # El rayo láser se dibuja solo si la torre dice que está disparando y tiene objetivo vivo
    for tower in player_group:
        if getattr(tower, "is_firing", False) and getattr(tower, "target", None) is not None:
            if tower.target.alive():
                start_pos = tower.rect.center
                end_pos = tower.target.rect.center
                pygame.draw.line(gameboard, (0, 191, 255), start_pos, end_pos, 3)
            else:
                tower.is_firing = False

    # ==========================================
    # --- DIBUJADO DE LA INTERFAZ DE USUARIO ---
    # ==========================================

    # ================= PANEL IZQUIERDO =================
    clock_rect = pygame.Rect(75, 40, 120, 60)
    draw_paper(gameboard, special_paper_sheet, clock_rect)

    time_str = f"{current_minute:02d}:{int(game_time % 60):02d}"
    time_surf = ui_font_large.render(time_str, True, "white")
    gameboard.blit(time_surf,
                   (clock_rect.centerx - time_surf.get_width() // 2, clock_rect.centery - time_surf.get_height() // 2))

    hp_ratio = max(0, castle_hp / castle_max_hp)
    draw_bar(gameboard, 25, 140, 220, 35, hp_ratio, big_bar_base, big_bar_fill)
    hp_text = ui_font_medium.render(f"HP: {int(castle_hp)}/{castle_max_hp}", True, "white")
    gameboard.blit(hp_text, (135 - hp_text.get_width() // 2, 147))

    xp_ratio = min(1, player_xp / xp_to_next_level)
    draw_bar(gameboard, 40, 190, 190, 25, xp_ratio, small_bar_base, small_bar_fill)
    xp_text = ui_font_small.render(f"Lvl: {player_level}", True, "white")
    gameboard.blit(xp_text, (135 - xp_text.get_width() // 2, 195))

    # ================= PANEL DERECHO =================
    rx = 1000


    def draw_slot(x, y, size, key_text, cost=None):
        gameboard.blit(pygame.transform.scale(btn_small_img, (size, size)), (x, y))

        pygame.draw.rect(gameboard, "#3b2f2f", (x - 8, y - 8, 22, 22), border_radius=4)
        pygame.draw.rect(gameboard, "#d2b48c", (x - 8, y - 8, 22, 22), 2, border_radius=4)
        key_surf = ui_font_small.render(key_text.upper(), True, "white")
        gameboard.blit(key_surf, (x - 1, y - 5))

        # DIBUJAMOS EL LAZO SIEMPRE (aunque no haya torre desbloqueada)
        draw_ribbon(gameboard, x - 5, y + size + 2, 60, 25, ribbon_sheet, row=1)

        # Si hay coste, ponemos el texto encima
        if cost is not None:
            cost_surf = ui_font_small.render(f"{cost} G", True, "black")
            gameboard.blit(cost_surf, (x + 25 - cost_surf.get_width() // 2, y + size + 7))


    tower_costs = [18, 25, 29, 33]
    tower_ids = ["arrow", "fireball", "kunai", "laser"]
    # Torres
    for i in range(4):
        slot_x = rx + 15 + (i * 65)
        key_name = pygame.key.name(controls[f"slot_{i + 1}"])

        # Leemos del orden real de desbloqueo
        if i < len(unlocked_towers_order):
            t_id = unlocked_towers_order[i]
            lvl = tower_levels[t_id]
            cost = TOWER_STATS[t_id][max(1, lvl)]["cost"]
            draw_slot(slot_x, 50, 50, key_name, cost)
        else:
            # Si el slot aún no tiene torre desbloqueada, lo dibujamos sin coste
            draw_slot(slot_x, 50, 50, key_name, None)

    for i in range(4):
        slot_x = rx + 15 + (i * 65)
        gameboard.blit(pygame.transform.scale(btn_small_img, (50, 50)), (slot_x, 150))

    wall_key = pygame.key.name(controls["wall"])
    draw_slot(rx + 15, 250, 50, wall_key, 5)

    draw_ribbon(gameboard, rx + 100, 260, 140, 40, ribbon_sheet, row=0)
    gold_surf = ui_font_large.render(f"{player_gold} G", True, "black")
    gameboard.blit(gold_surf, (rx + 170 - gold_surf.get_width() // 2, 265))


    def draw_action_btn(x, y, w, h, key_text, label, cost=None):
        draw_9_slice_button(gameboard, btn_wide_img, pygame.Rect(x, y, w, h), edge_px=14)

        pygame.draw.rect(gameboard, "#3b2f2f", (x - 10, y - 10, 26, 26), border_radius=4)
        pygame.draw.rect(gameboard, "#d2b48c", (x - 10, y - 10, 26, 26), 2, border_radius=4)
        key_surf = ui_font_medium.render(key_text.upper(), True, "white")
        gameboard.blit(key_surf, (x - 3, y - 8))

        label_surf = ui_font_medium.render(label, True, "black")
        gameboard.blit(label_surf,
                       (x + (w // 2) - (label_surf.get_width() // 2), y + (h // 2) - (label_surf.get_height() // 2)))

        if cost is not None:
            ry = y + h + 2
            rw = 80
            rh = 28
            rx_ribbon = x + (w // 2) - (rw // 2)
            draw_ribbon(gameboard, rx_ribbon, ry, rw, rh, ribbon_sheet, row=0)
            cost_surf = ui_font_small.render(f"{cost} G", True, "black")
            gameboard.blit(cost_surf, (rx_ribbon + (rw // 2) - (cost_surf.get_width() // 2), ry + 6))


    repair_all_cost = int((castle_max_hp - castle_hp) * 2)
    sell_key = pygame.key.name(controls["sell"])

    draw_action_btn(rx + 40, 420, 200, 50, sell_key, "Demolish")
    draw_action_btn(rx + 40, 510, 200, 50, "e", "Repair")
    draw_action_btn(rx + 40, 600, 200, 50, "r", "Repair All", repair_all_cost)

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
        title_text = ui_font_large.render("LEVEL UP! CHOOSE A REWARD", True, "yellow")
        gameboard.blit(title_text, (640 - title_text.get_width() // 2, 100))

        for i, card in enumerate(level_up_options):
            cx = start_x + i * (card_width + spacing)
            cy = start_y
            rect = pygame.Rect(cx, cy, card_width, card_height)
            card_rects.append(rect)

            pygame.draw.rect(gameboard, "#112233", rect)
            pygame.draw.rect(gameboard, "white", rect, 3)

            text_surf = ui_font_medium.render(card["title"], True, "white")
            gameboard.blit(text_surf, (cx + 10, cy + 130))

    screensize = screen.get_size()
    rescaled_gameboard = pygame.transform.scale(gameboard, screensize)
    screen.blit(rescaled_gameboard, (0, 0))

    pygame.display.flip()
    dt = clock.tick(60) / 1000

    # --- LÓGICA DE JUEGO ---
    if game_state == "PLAYING":
        game_time += dt * time_scale
        current_minute = int(game_time // 60)
        difficulty_multiplier = round(1 + (current_minute / 8) ** 1.8, 2)

        if len(spawn_schedule) > 0:
            next_spawn_time, next_spawn_type = spawn_schedule[0]
            if game_time >= next_spawn_time:
                setup_spawn_point(spawn_group, next_spawn_type)
                spawn_schedule.pop(0)

        spawn_group.update(dt * time_scale, enemy_group, grid, offsetX, grid_size)
        enemy_group.update(dt * time_scale, grid, enemy_group=enemy_group, structures_hp=structures_hp)

        collisions = pygame.sprite.groupcollide(enemy_group, enemy_group, False, False)
        for enemy, others in collisions.items():
            push_final = pygame.math.Vector2(0, 0)
            for other in others:
                if other == enemy: continue
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

        player_group.update(dt * time_scale, enemy_group, bullet_group, tower_levels)
        bullet_group.update(dt * time_scale)
        effects_group.update(dt * time_scale)

        for bullet in bullet_group:
            bx = int((bullet.pos.x - offsetX) // grid_size)
            by = int(bullet.pos.y // grid_size)
            if 0 <= bx < col and 0 <= by < row:
                if grid[by][bx] == mountain:
                    if hasattr(bullet, "aoe_radius"):
                        exp = Effect(bullet.rect.centerx, bullet.rect.centery, explosion_sheet,
                                     int(bullet.aoe_radius * 3.5), fps=20)
                        effects_group.add(exp)
                    bullet.kill()

        hits = pygame.sprite.groupcollide(bullet_group, enemy_group, False, False)

        for arrow, enemies_hit in hits.items():
            for enemy in enemies_hit:
                if enemy not in arrow.hit_enemies:
                    arrow.hit_enemies.add(enemy)
                    final_damage = arrow.damage * (1.0 + global_damage_buff)

                    if hasattr(arrow, "aoe_radius"):
                        exp = Effect(arrow.rect.centerx, arrow.rect.centery, explosion_sheet,
                                     int(arrow.aoe_radius * 3.5), fps=20)
                        effects_group.add(exp)

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