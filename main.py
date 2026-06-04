import pygame
import random
import os
import sys
import ctypes

from Entities.Player.towers import ArrowTower, FireballTower, KunaiTower, LaserTower, LightningTower, ThornsTower, TOWER_STATS
from Entities.effects import Effect, TowerSmoke
from gamedata import *
from graphics import *
import settings

from map_manager import get_tile_for_cell, update_ruin_masks, update_wall_masks, update_neighbors_walls, generate_initial_grid
from Entities.spawn import setup_spawn_point
from game_logic import get_level_up_cards
from Entities.Enemies.enemies import Boss

# =====================================================================
# INICIALIZACIÓN DEL MOTOR Y ASSETS
# =====================================================================
pygame.init()
pygame.font.init()

# Pantalla completa sin bordes obligatoria
os.environ["SDL_VIDEO_WINDOW_POS"] = "0,0"
desktop_size = pygame.display.get_desktop_sizes()[0]
screen = pygame.display.set_mode(desktop_size, pygame.NOFRAME)

base_res = (1280, 720)
gameboard = pygame.Surface(base_res)
clock = pygame.time.Clock()
running = True

from assets import core_assets as assets
assets.load_all(settings.use_legible_font)

pygame.mouse.set_visible(False)
effects_group = pygame.sprite.Group()

# =====================================================================
# PREPARACIÓN DEL MAPA Y GRUPOS
# =====================================================================
background_tile = get_tile(assets.color4_sheet, 64, 64, 64, 64, grid_size)
buildable_tiles = {
    (1, 1, 1, 1): get_tile(assets.color2_sheet, 64, 64, 64, 64, grid_size),
    (0, 1, 1, 1): get_tile(assets.color2_sheet, 64, 0, 64, 64, grid_size),
    (1, 0, 1, 1): get_tile(assets.color2_sheet, 64, 128, 64, 64, grid_size),
    (1, 1, 0, 1): get_tile(assets.color2_sheet, 0, 64, 64, 64, grid_size),
    (1, 1, 1, 0): get_tile(assets.color2_sheet, 128, 64, 64, 64, grid_size),
    (0, 1, 0, 1): get_tile(assets.color2_sheet, 0, 0, 64, 64, grid_size),
    (0, 1, 1, 0): get_tile(assets.color2_sheet, 128, 0, 64, 64, grid_size),
    (1, 0, 0, 1): get_tile(assets.color2_sheet, 0, 128, 64, 64, grid_size),
    (1, 0, 1, 0): get_tile(assets.color2_sheet, 128, 128, 64, 64, grid_size),
}

mountain_tiles = {
    (1, 0, 1, 1): get_tile(assets.elevation_sheet, 64, 192, 64, 64, grid_size),
    (0, 1, 1, 1): get_tile(assets.elevation_sheet, 64, 0, 64, 64, grid_size),
    (1, 1, 0, 1): get_tile(assets.elevation_sheet, 0, 64, 64, 64, grid_size),
    (1, 1, 1, 0): get_tile(assets.elevation_sheet, 128, 64, 64, 64, grid_size),
    (1, 0, 0, 1): get_tile(assets.elevation_sheet, 0, 192, 64, 64, grid_size),
    (1, 0, 1, 0): get_tile(assets.elevation_sheet, 128, 192, 64, 64, grid_size),
    (0, 1, 0, 1): get_tile(assets.elevation_sheet, 0, 0, 64, 64, grid_size),
    (0, 1, 1, 0): get_tile(assets.elevation_sheet, 128, 0, 64, 64, grid_size),
    (1, 1, 1, 1): get_tile(assets.elevation_sheet, 64, 64, 64, 64, grid_size),
}

grid = generate_initial_grid()

grid_overlay = pygame.Surface((width_gameboard, height_gameboard), pygame.SRCALPHA)
white_grid = (255, 255, 255, 150)
for x in range(0, col):
    for y in range(0, row):
        if grid[y][x] == allow:
            pygame.draw.rect(grid_overlay, white_grid, (x * grid_size, y * grid_size, grid_size, grid_size), 1)

# =====================================================================
# VARIABLES DE ESTADO Y DICCIONARIOS
# =====================================================================
show_grid = False
confirm_action = None

player_group = pygame.sprite.Group()
enemy_group = pygame.sprite.Group()
bullet_group = pygame.sprite.Group()
spawn_group = pygame.sprite.Group()
chest_group = pygame.sprite.Group()

game_state = "MAIN_MENU"
meta_health = 0
player_gems = 0

# Variables del Boss globales para que no peten al reiniciar
next_boss_time = 150.0
bosses_spawned = 0

def reset_game():
    global castle_obj, current_tool, unlocked_towers, active_towers
    global level_up_options, card_rects, pause_rects, main_menu_rects
    global player_gold, player_gems, player_level, player_xp, xp_to_next_level, selected_card_idx
    global castle_max_hp, castle_hp, structures_hp, wall_masks, ruin_masks
    global previous_structures_hp, damage_timers, previous_structures_types
    global tower_levels, active_passives, passive_levels
    global spawn_counts, existing_spawns_pos, spawn_schedule, last_built_cell
    global game_time, current_minute, difficulty_multiplier, time_scale, grid
    global next_boss_time, bosses_spawned, forced_initial_spawns

    player_group.empty()
    enemy_group.empty()
    bullet_group.empty()
    spawn_group.empty()
    chest_group.empty()
    effects_group.empty()

    castle_obj = ArrowTower(640, 360, is_castle=True)
    player_group.add(castle_obj)

    current_tool = None
    unlocked_towers = ["arrow"]
    active_towers = ["arrow", None, None, None]
    level_up_options = []
    card_rects = []
    pause_rects = []
    main_menu_rects = []

    player_gold = 100
    player_level = 1
    player_xp = 0
    xp_to_next_level = 50
    selected_card_idx = None

    castle_max_hp = 100
    castle_hp = castle_max_hp
    structures_hp = {}
    wall_masks = {}
    ruin_masks = {}

    previous_structures_hp = {}
    damage_timers = {}
    previous_structures_types = {}

    tower_levels = {"arrow": 1, "fireball": 0, "kunai": 0, "laser": 0, "lightning": 0, "thorns": 0}

    active_passives = []
    passive_levels = {
        "damage": 0, "firerate": 0, "range": 0, "health": 0, "regen": 0,
        "armor": 0, "thorns": 0, "gold": 0, "xp": 0, "crit": 0
    }

    grid = generate_initial_grid()

    spawn_counts = {"North": 0, "South": 0, "East": 0, "West": 0}
    existing_spawns_pos = {"North": [], "South": [], "East": [], "West": []}

    forced_initial_spawns = random.choice([["North", "South"], ["East", "West"]])
    random.shuffle(forced_initial_spawns)

    for _ in range(2):
        setup_spawn_point(spawn_group, effects_group, grid, "balanced", forced_initial_spawns, spawn_counts, existing_spawns_pos, assets)

    spawn_schedule = [
        (90, "balanced"), (180, "balanced"), (270, "balanced"), (360, "balanced"),
        (450, "balanced"), (540, "balanced"), (630, "balanced"), (720, "balanced"),
        (810, "wildcard"), (900, "wildcard"),
    ]
    random_time_1 = random.uniform(910, 1040)
    random_time_2 = random.uniform(910, 1040)
    spawn_schedule.extend([(random_time_1, "balanced"), (random_time_2, "balanced"), (1050, "wildcard")])
    spawn_schedule.sort(key=lambda x: x[0])

    last_built_cell = None
    game_time = 0.0
    current_minute = 0
    difficulty_multiplier = 1.0
    time_scale = 1.0
    
    next_boss_time = 150.0
    bosses_spawned = 0

# Inicializamos la primera partida al abrir el juego
reset_game()

# =====================================================================
# BUCLE PRINCIPAL
# =====================================================================
while running:
    keys = pygame.key.get_pressed()
    time_scale = 1.0
    if keys[pygame.K_x]:
        time_scale = 8.0
    elif keys[pygame.K_z]:
        time_scale = 4.0


    physical_mouseX, physical_mouseY = pygame.mouse.get_pos()
    current_w, current_h = screen.get_size()
    mouseX = int((physical_mouseX / max(1, current_w)) * 1280)
    mouseY = int((physical_mouseY / max(1, current_h)) * 720)

    limitW = offsetX + (margin * grid_size)
    limitE = offsetX + (col - margin) * grid_size
    limitN = margin * grid_size
    limitS = (row - margin) * grid_size

    on_grid = limitW <= mouseX < limitE and limitN <= mouseY < limitS

    if on_grid:
        hoverCol = (mouseX - offsetX) // grid_size
        hoverRow = mouseY // grid_size
        if last_built_cell and last_built_cell != (hoverRow, hoverCol):
            last_built_cell = None

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.MOUSEBUTTONDOWN:
            if game_state == "PLAYING":
                clicked_chest = False
                for chest in chest_group:
                    if chest.rect.collidepoint(mouseX, mouseY):
                        chest.click()
                        clicked_chest = True
                        break

                if clicked_chest:
                    continue

                if not on_grid:
                    menu_btn_rect = pygame.Rect(40, 600, 200, 50)
                    if menu_btn_rect.collidepoint(mouseX, mouseY):
                        game_state = "PAUSED"

                    rx_click = 1000
                    for i in range(4):
                        t_id = active_towers[i]
                        if t_id:
                            slot_rect = pygame.Rect(rx_click + 25 + (i * 60), 50, 50, 50)
                            if slot_rect.collidepoint(mouseX, mouseY):
                                current_tool = t_id if current_tool != t_id else None

                    wall_rect = pygame.Rect(rx_click + 25, 200, 50, 50)
                    if wall_rect.collidepoint(mouseX, mouseY):
                        current_tool = "wall" if current_tool != "wall" else None

                    sell_rect = pygame.Rect(rx_click + 40, 420, 200, 50)
                    if sell_rect.collidepoint(mouseX, mouseY):
                        current_tool = "sell" if current_tool != "sell" else None

                    rep_rect = pygame.Rect(rx_click + 40, 510, 200, 50)
                    if rep_rect.collidepoint(mouseX, mouseY):
                        current_tool = "repair" if current_tool != "repair" else None

            if game_state == "LEVEL_UP":
                for i, rect in enumerate(card_rects):
                    if rect.collidepoint(mouseX, mouseY):
                        if selected_card_idx == i:
                            chosen = level_up_options[i]

                            if chosen["type"] == "upgrade_tower":
                                t_id = chosen["id"]
                                old_lvl = tower_levels[t_id]
                                tower_levels[t_id] += 1
                                if old_lvl > 0:
                                    hp_buff = 1.0 + (passive_levels.get("health", 0) * 0.05) + meta_health
                                    old_max = int(TOWER_BASE_HP[old_lvl] * hp_buff)
                                    new_max = int(TOWER_BASE_HP[tower_levels[t_id]] * hp_buff)
                                    hp_delta = new_max - old_max
                                    for t in player_group:
                                        if type(t).__name__.lower().startswith(t_id) and "castle" not in type(
                                                t).__name__.lower():
                                            t_col = int((t.x - offsetX) // grid_size)
                                            t_row = int(t.y // grid_size)
                                            if (t_row, t_col) in structures_hp:
                                                structures_hp[(t_row, t_col)] += hp_delta
                                if tower_levels[t_id] == 1 and t_id not in unlocked_towers:
                                    unlocked_towers.append(t_id)
                                    for idx in range(4):
                                        if active_towers[idx] is None:
                                            active_towers[idx] = t_id
                                            break

                            elif chosen["type"] in ["unlock_passive", "upgrade_passive"]:
                                p_id = chosen["id"]
                                old_hp_buff = 1.0 + (passive_levels.get("health", 0) * 0.05) + meta_health

                                if chosen["type"] == "unlock_passive":
                                    active_passives.append(p_id)
                                    passive_levels[p_id] = 1
                                else:
                                    passive_levels[p_id] += 1

                                if p_id == "health":
                                    new_hp_buff = 1.0 + (passive_levels["health"] * 0.05) + meta_health

                                    old_castle_max = int((100 + (player_level * 18)) * old_hp_buff)
                                    new_castle_max = int((100 + (player_level * 18)) * new_hp_buff)
                                    castle_max_hp = new_castle_max
                                    castle_hp += (new_castle_max - old_castle_max)

                                    for coords in list(structures_hp.keys()):
                                        r, c = coords
                                        cell = grid[r][c]

                                        if cell == wall:
                                            old_max = int((25 + (player_level * 1.5)) * old_hp_buff)
                                            new_max = int((25 + (player_level * 1.5)) * new_hp_buff)
                                            structures_hp[coords] += (new_max - old_max)

                                        elif cell == turret:
                                            t_obj = next((t for t in player_group if
                                                          not getattr(t, "is_castle", False) and int(
                                                              (t.x - offsetX) // grid_size) == c and int(
                                                              t.y // grid_size) == r), None)
                                            if t_obj:
                                                t_id = t_obj.tower_id
                                                lvl = max(1, tower_levels.get(t_id, 1))
                                                old_max = int(TOWER_BASE_HP[lvl] * old_hp_buff)
                                                new_max = int(TOWER_BASE_HP[lvl] * new_hp_buff)
                                                structures_hp[coords] += (new_max - old_max)

                            elif chosen["type"] == "heal":
                                castle_hp = min(castle_max_hp, castle_hp + (castle_max_hp // 2))
                            elif chosen["type"] == "gold":
                                player_gold += 50
                            elif chosen["type"] == "heal_20":
                                castle_hp = min(castle_max_hp, castle_hp + int(castle_max_hp * 0.2))
                            elif chosen["type"] == "gold_100":
                                player_gold += 100
                            elif chosen["type"] == "gems_5":
                                player_gems += 5

                            selected_card_idx = None
                            game_state = "PLAYING"
                        else:
                            selected_card_idx = i
                        break

            elif game_state == "PLAYING" and on_grid:
                if current_tool == "sell":
                    if grid[hoverRow][hoverCol] in [wall, turret]:
                        cell_type = grid[hoverRow][hoverCol]
                        coords = (hoverRow, hoverCol)
                        if coords in structures_hp:
                            current_hp = structures_hp[coords]
                            hp_buff = 1.0 + (passive_levels.get("health", 0) * 0.05) + meta_health

                            if cell_type == wall:
                                max_hp = int((25 + (player_level * 1.5)) * hp_buff)
                                total_value = min(50, 10 + int(player_level * 0.8))
                                target_obj = None
                            else:
                                target_obj = next((t for t in player_group if
                                                   not getattr(t, "is_castle", False) and int(
                                                       (t.x - offsetX) // grid_size) == hoverCol and int(
                                                       t.y // grid_size) == hoverRow), None)
                                if target_obj:
                                    t_id = target_obj.tower_id
                                    max_hp = int(TOWER_BASE_HP[max(1, tower_levels[t_id])] * hp_buff)
                                    total_value = TOWER_STATS[t_id][max(1, tower_levels[t_id])]["cost"]
                                else:
                                    max_hp = 1
                                    total_value = 0

                            current_value = total_value * (current_hp / max_hp)
                            player_gold += int(current_value * 0.25)

                            grid[hoverRow][hoverCol] = allow
                            del structures_hp[coords]

                            if cell_type == wall:
                                if coords in wall_masks: del wall_masks[coords]
                                update_neighbors_walls(hoverRow, hoverCol, grid, wall_masks, ruin_masks)
                            elif cell_type == turret and target_obj:
                                target_obj.kill()

                    elif (hoverRow, hoverCol) in ruin_masks:
                        update_ruin_masks(hoverRow, hoverCol, grid, ruin_masks)
                        update_neighbors_walls(hoverRow, hoverCol, grid, wall_masks, ruin_masks)

                        fx_x = offsetX + (hoverCol * grid_size) + (grid_size // 2)
                        fx_y = (hoverRow * grid_size) + (grid_size // 2)
                        effects_group.add(Effect(fx_x, fx_y, assets.wallsmoke_sheet, scale_size=60, fps=15, num_frames=7))

                elif current_tool == "repair":
                    if grid[hoverRow][hoverCol] in [wall, turret]:
                        cell_type = grid[hoverRow][hoverCol]
                        coords = (hoverRow, hoverCol)
                        if coords in structures_hp:
                            current_hp = structures_hp[coords]
                            hp_buff = 1.0 + (passive_levels.get("health", 0) * 0.05) + meta_health

                            if cell_type == wall:
                                max_hp = int((25 + (player_level * 1.5)) * hp_buff)
                                total_value = min(50, 10 + int(player_level * 0.8))
                            else:
                                target_obj = next((t for t in player_group if
                                                   not getattr(t, "is_castle", False) and int(
                                                       (t.x - offsetX) // grid_size) == hoverCol and int(
                                                       t.y // grid_size) == hoverRow), None)
                                if target_obj:
                                    t_id = target_obj.tower_id
                                    max_hp = int(TOWER_BASE_HP[max(1, tower_levels[t_id])] * hp_buff)
                                    total_value = TOWER_STATS[t_id][max(1, tower_levels[t_id])]["cost"]
                                else:
                                    max_hp = 1
                                    total_value = 0

                            if current_hp < max_hp:
                                current_value = total_value * (current_hp / max_hp)
                                repair_price = int((total_value - current_value) * 0.75)
                                if player_gold >= repair_price:
                                    player_gold -= repair_price
                                    structures_hp[coords] = max_hp

                elif grid[hoverRow][hoverCol] == allow:
                    hp_buff = 1.0 + (passive_levels.get("health", 0) * 0.05) + meta_health

                    if current_tool == "wall":
                        current_wall_cost = min(50, 10 + int(player_level * 0.8))
                        if player_gold >= current_wall_cost:
                            player_gold -= current_wall_cost
                            grid[hoverRow][hoverCol] = wall
                            structures_hp[(hoverRow, hoverCol)] = int((25 + (player_level * 1.5)) * hp_buff)

                            if (hoverRow, hoverCol) in ruin_masks:
                                del ruin_masks[(hoverRow, hoverCol)]

                            update_neighbors_walls(hoverRow, hoverCol, grid, wall_masks, ruin_masks)

                            posX_px = offsetX + (hoverCol * grid_size) + (grid_size // 2)
                            posY_px = (hoverRow * grid_size) + (grid_size // 2)
                            effects_group.add(Effect(posX_px, posY_px, assets.dust_sheet, scale_size=55, fps=11))

                    elif current_tool in ["arrow", "fireball", "kunai", "laser", "lightning", "thorns"]:
                        lvl = tower_levels[current_tool]
                        stats = TOWER_STATS[current_tool][max(1, lvl)]
                        current_count = sum(1 for t in player_group if
                                            getattr(t, "tower_id", None) == current_tool and not getattr(t, "is_castle",
                                                                                                         False))

                        if current_count < stats["limit"]:
                            cost = stats["cost"]
                            if player_gold >= cost:
                                player_gold -= cost
                                grid[hoverRow][hoverCol] = turret
                                structures_hp[(hoverRow, hoverCol)] = int(TOWER_BASE_HP[max(1, lvl)] * hp_buff)

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
                                elif current_tool == "lightning":
                                    player_group.add(LightningTower(posX_px, posY_px))
                                elif current_tool == "thorns":
                                    player_group.add(ThornsTower(posX_px, posY_px))

                                base_y = (hoverRow * grid_size) + grid_size
                                effects_group.add(TowerSmoke(posX_px, base_y, assets.smoke_sheet, goes_right=False))
                                effects_group.add(TowerSmoke(posX_px, base_y, assets.smoke_sheet, goes_right=True))

                                last_built_cell = (hoverRow, hoverCol)

        if event.type == pygame.MOUSEBUTTONUP:
            if game_state == "MAIN_MENU":
                for rect, opt in main_menu_rects:
                    if rect.collidepoint(mouseX, mouseY):
                        if opt == "Play":
                            reset_game() # Reiniciamos por si venimos de salir de una partida
                            game_state = "PLAYING"
                        elif opt == "Exit":
                            running = False
                        else:
                            print(f"You clicked {opt}. It is still a work in progress, patience.")
            elif game_state == "PAUSED":
                if confirm_action:
                    yes_rect = pygame.Rect(640 - 120, 360, 100, 50)
                    no_rect = pygame.Rect(640 + 20, 360, 100, 50)
                    if yes_rect.collidepoint(mouseX, mouseY):
                        if confirm_action == "Restart":
                            reset_game()
                            game_state = "PLAYING"
                        elif confirm_action == "Main Menu":
                            reset_game()
                            game_state = "MAIN_MENU"
                        confirm_action = None
                    elif no_rect.collidepoint(mouseX, mouseY):
                        confirm_action = None
                else:
                    for rect, opt in pause_rects:
                        if rect.collidepoint(mouseX, mouseY):
                            if opt == "Resume":
                                game_state = "PLAYING"
                            elif opt in ["Restart", "Retry"]:
                                confirm_action = "Restart"
                            elif opt in ["Main Menu", "Menu", "Quit", "Quit to Menu"]:
                                confirm_action = "Main Menu"
                            else:
                                print(f"You clicked {opt}. It is still a work in progress, patience.")
            elif game_state == "GAME_OVER":
                restart_rect = pygame.Rect(640 - 220, 500, 200, 50)
                quit_rect = pygame.Rect(640 + 20, 500, 200, 50)
                if restart_rect.collidepoint(mouseX, mouseY):
                    reset_game()
                    game_state = "PLAYING"
                elif quit_rect.collidepoint(mouseX, mouseY):
                    reset_game()
                    game_state = "MAIN_MENU"

        if event.type == pygame.KEYDOWN:
            if game_state == "PLAYING":
                if event.key == pygame.K_g:
                    show_grid = not show_grid
                elif event.key == pygame.K_ESCAPE:
                    if current_tool is not None:
                        current_tool = None
                    else:
                        game_state = "PAUSED"
                elif event.key == settings.controls["sell"]:
                    current_tool = "sell" if current_tool != "sell" else None
                elif event.key == settings.controls["repair"]:
                    current_tool = "repair" if current_tool != "repair" else None
                elif event.key == settings.controls["wall"]:
                    current_tool = "wall" if current_tool != "wall" else None
                elif event.key == settings.controls["slot_1"] and active_towers[0]:
                    t = active_towers[0]
                    current_tool = t if current_tool != t else None
                elif event.key == settings.controls["slot_2"] and active_towers[1]:
                    t = active_towers[1]
                    current_tool = t if current_tool != t else None
                elif event.key == settings.controls["slot_3"] and active_towers[2]:
                    t = active_towers[2]
                    current_tool = t if current_tool != t else None
                elif event.key == settings.controls["slot_4"] and active_towers[3]:
                    t = active_towers[3]
                    current_tool = t if current_tool != t else None
                elif event.key == settings.controls["toggle_hp"]:
                    settings.health_bars_mode = (settings.health_bars_mode + 1) % 4
                    settings.config["Settings"]["health_bars_mode"] = str(settings.health_bars_mode)
                    with open(settings.config_file, "w") as f:
                        settings.config.write(f)
            elif game_state == "PAUSED":
                if event.key == pygame.K_ESCAPE:
                    game_state = "PLAYING"

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
                tile = get_tile_for_cell(x, y, buildable_targets, buildable_tiles, grid, False)
                gameboard.blit(tile, (posX, posY))

                if (y, x) in ruin_masks:
                    mask = ruin_masks[(y, x)]
                    gameboard.blit(assets.ruin_sprites[mask], (posX, posY))

                if cell == wall:
                    mask = wall_masks.get((y, x), 0)
                    gameboard.blit(assets.wall_sprites[mask], (posX, posY))

            elif cell == mountain:
                tile = get_tile_for_cell(x, y, [mountain], mountain_tiles, grid, True)
                gameboard.blit(tile, (posX, posY))

    if show_grid:
        gameboard.blit(grid_overlay, (offsetX, 0))

    if on_grid and game_state == "PLAYING":
        posX_trans = offsetX + (hoverCol * grid_size)
        posY_trans = hoverRow * grid_size
        current_cell = grid[hoverRow][hoverCol]

        if current_cell != castle:
            surface_trans = pygame.Surface((grid_size, grid_size), pygame.SRCALPHA)
            if current_tool == "sell":
                if current_cell in [wall, turret] or (hoverRow, hoverCol) in ruin_masks:
                    surface_trans.fill((255, 0, 0, 150))
                else:
                    surface_trans.fill((255, 0, 0, 40))
            elif current_tool is not None and current_cell != allow:
                surface_trans.fill((255, 0, 0, 70))
            else:
                surface_trans.fill((255, 255, 255, 40))
            gameboard.blit(surface_trans, (posX_trans, posY_trans))

    for bullet in bullet_group:
        if type(bullet).__name__ == "ThornsArea":
            gameboard.blit(bullet.image, bullet.rect)

    living_entities = list(player_group) + list(enemy_group)
    for bullet in bullet_group:
        if type(bullet).__name__ in ["IceBeamVisual", "LightningVisual"]:
            living_entities.append(bullet)

    living_entities.sort(key=lambda entity: getattr(entity, "y_sort", entity.rect.bottom))

    for entity in living_entities:
        gameboard.blit(entity.image, entity.rect)

    for bullet in bullet_group:
        if type(bullet).__name__ not in ["ThornsArea", "IceBeamVisual", "LightningVisual"]:
            gameboard.blit(bullet.image, bullet.rect)

    effects_group.draw(gameboard)
    chest_group.draw(gameboard)

    if on_grid and game_state == "PLAYING" and last_built_cell != (hoverRow, hoverCol):
        posX_trans = offsetX + (hoverCol * grid_size)
        posY_trans = hoverRow * grid_size
        current_cell = grid[hoverRow][hoverCol]

        if current_tool in assets.preview_towers:
            tower_img = assets.preview_towers[current_tool].copy()

            if current_tool == "wall":
                can_build = (current_cell == allow) and (player_gold >= min(50, 10 + int(player_level * 0.8)))
                shift_y = 0
                limit_text = None
            else:
                lvl = max(1, tower_levels[current_tool])
                stats = TOWER_STATS[current_tool][lvl]
                limit = stats["limit"]
                cost = stats["cost"]
                current_count = sum(1 for t in player_group if
                                    getattr(t, "tower_id", None) == current_tool and not getattr(t, "is_castle", False))
                can_build = (current_cell == allow) and (current_count < limit) and (player_gold >= cost)
                shift_y = 30
                limit_text = f"{current_count}/{limit}"

            if not can_build:
                tower_img.fill((0, 255, 255, 0), special_flags=pygame.BLEND_RGB_SUB)

            gameboard.blit(tower_img, (posX_trans, posY_trans - shift_y))

            if limit_text:
                text_color = "white" if current_count < limit else "red"
                outline_surf = assets.ui_font_medium.render(limit_text, True, "black")
                for dx, dy in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
                    gameboard.blit(outline_surf, (mouseX + 15 + dx, mouseY + 15 + dy))

                text_surf = assets.ui_font_medium.render(limit_text, True, text_color)
                gameboard.blit(text_surf, (mouseX + 15, mouseY + 15))

    hp_cells_to_draw = set()
    hovered_struct = None

    if on_grid and game_state == "PLAYING":
        if grid[hoverRow][hoverCol] in [wall, turret] and (hoverRow, hoverCol) in structures_hp:
            if current_tool in [None, "sell", "repair"]:
                hovered_struct = (hoverRow, hoverCol)
                hp_cells_to_draw.add(hovered_struct)

        for r in range(row):
            for c in range(col):
                if grid[r][c] in [wall, turret] and (r, c) in structures_hp:
                    is_tower = (grid[r][c] == turret)
                    recently_damaged = (r, c) in damage_timers

                    if settings.health_bars_mode == 0 and is_tower and recently_damaged:
                        hp_cells_to_draw.add((r, c))
                    elif settings.health_bars_mode == 1 and recently_damaged:
                        hp_cells_to_draw.add((r, c))
                    elif settings.health_bars_mode == 2 and is_tower:
                        hp_cells_to_draw.add((r, c))

    for (r, c) in hp_cells_to_draw:
        current_hp = structures_hp[(r, c)]
        hp_buff = 1.0 + (passive_levels.get("health", 0) * 0.05) + meta_health
        max_hp = 1
        cell = grid[r][c]
        t_obj = None

        if cell == wall:
            max_hp = int((25 + (player_level * 1.5)) * hp_buff)
        elif cell == turret:
            t_obj = next((t for t in player_group if
                          not getattr(t, "is_castle", False) and int((t.x - offsetX) // grid_size) == c and int(
                              t.y // grid_size) == r), None)
            if t_obj:
                max_hp = int(TOWER_BASE_HP[max(1, tower_levels.get(t_obj.tower_id, 1))] * hp_buff)

        bar_w = 40
        bx = offsetX + (c * grid_size) + (grid_size // 2) - (bar_w // 2)
        by = (r * grid_size) + grid_size - 15

        alpha = 255
        if settings.health_bars_mode in [0, 1] and (r, c) != hovered_struct and (r, c) in damage_timers:
            timer = damage_timers[(r, c)]
            if timer < 1.0:
                alpha = int(255 * timer)

        if alpha < 255:
            hp_surf_bar = pygame.Surface((bar_w, 6), pygame.SRCALPHA)
            pygame.draw.rect(hp_surf_bar, (255, 0, 0, alpha), (0, 0, bar_w, 6))
            pygame.draw.rect(hp_surf_bar, (0, 255, 0, alpha),
                             (0, 0, max(0, min(bar_w, int((current_hp / max_hp) * bar_w))), 6))
            pygame.draw.rect(hp_surf_bar, (0, 0, 0, alpha), (0, 0, bar_w, 6), 1)
            gameboard.blit(hp_surf_bar, (bx, by))
        else:
            pygame.draw.rect(gameboard, "red", (bx, by, bar_w, 6))
            pygame.draw.rect(gameboard, "green",
                             (bx, by, max(0, min(bar_w, int((current_hp / max_hp) * bar_w))), 6))
            pygame.draw.rect(gameboard, "black", (bx, by, bar_w, 6), 1)

        if (r, c) == hovered_struct:
            hp_str = f"{int(current_hp)}/{int(max_hp)}"
            hp_surf = assets.ui_font_small.render(hp_str, True, "white")

            text_y = by - 14
            text_x = bx + (bar_w // 2) - (hp_surf.get_width() // 2)

            for dx, dy in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
                gameboard.blit(assets.ui_font_small.render(hp_str, True, "black"), (text_x + dx, text_y + dy))
            gameboard.blit(hp_surf, (text_x, text_y))

            total_value = 0
            if cell == wall:
                total_value = min(50, 10 + int(player_level * 0.8))
            elif cell == turret and t_obj:
                total_value = TOWER_STATS[t_obj.tower_id][max(1, tower_levels.get(t_obj.tower_id, 1))]["cost"]

            current_value = total_value * (current_hp / max_hp)
            sell_price = int(current_value * 0.25)
            repair_price = int((total_value - current_value) * 0.75)

            action_text = ""
            color_text = "white"
            if current_tool == "sell":
                action_text = f"+{sell_price} G"
                color_text = "yellow"
            elif current_tool == "repair":
                action_text = "Max HP" if current_hp >= max_hp else f"-{repair_price} G"
                color_text = "gray" if current_hp >= max_hp else "red"

            if action_text:
                for dx, dy in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
                    gameboard.blit(assets.ui_font_medium.render(action_text, True, "black"),
                                   (mouseX + 15 + dx, mouseY + 15 + dy))
                gameboard.blit(assets.ui_font_medium.render(action_text, True, color_text), (mouseX + 15, mouseY + 15))

    if assets.panel_bg:
        gameboard.blit(assets.panel_bg, (0, 0))
        gameboard.blit(assets.panel_bg, (offsetX + width_gameboard, 0))
    else:
        pygame.draw.rect(gameboard, "#222222", (0, 0, offsetX, 720))
        pygame.draw.rect(gameboard, "#222222", (offsetX + width_gameboard, 0, 1280 - (offsetX + width_gameboard), 720))

    clock_rect = pygame.Rect(75, 35, 120, 75)
    draw_paper(gameboard, assets.special_paper_sheet, clock_rect)

    time_str = f"{current_minute:02d}:{int(game_time % 60):02d}"
    time_surf = assets.ui_font_large.render(time_str, True, "white")
    text_x = clock_rect.centerx - time_surf.get_width() // 2
    text_y = (clock_rect.centery - time_surf.get_height() // 2) + 4

    gameboard.blit(time_surf, (text_x, text_y))

    hp_ratio = max(0, castle_hp / castle_max_hp)
    draw_bar(gameboard, 25, 140, 220, 35, hp_ratio, assets.big_bar_base, assets.big_bar_fill)
    hp_text = assets.ui_font_medium.render(f"HP: {int(castle_hp)}/{castle_max_hp}", True, "white")
    gameboard.blit(hp_text, (135 - hp_text.get_width() // 2, 147))

    xp_ratio = min(1, player_xp / xp_to_next_level)
    draw_bar(gameboard, 40, 190, 190, 25, xp_ratio, assets.small_bar_base, assets.small_bar_fill)
    xp_text = assets.ui_font_small.render(f"Lvl: {player_level}", True, "white")
    gameboard.blit(xp_text, (135 - xp_text.get_width() // 2, 195))

    menu_btn_rect = pygame.Rect(40, 600, 200, 50)
    is_menu_pressed = keys[pygame.K_ESCAPE] or (
            pygame.mouse.get_pressed()[0] and menu_btn_rect.collidepoint(mouseX, mouseY))
    draw_action_btn(gameboard, assets, 40, 600, 200, 50, "esc", "Menu", is_pressed=is_menu_pressed)

    rx = 1000
    for i in range(4):
        slot_x = rx + 25 + (i * 60)
        slot_y = 50
        key_str = pygame.key.name(settings.controls[f"slot_{i + 1}"])
        t_id = active_towers[i]

        if t_id:
            is_pressed = (current_tool == t_id)
            lvl = max(1, tower_levels[t_id])
            cost = TOWER_STATS[t_id][lvl]["cost"]
            draw_slot(gameboard, assets, slot_x, slot_y, 50, key_str, cost, is_pressed=is_pressed, t_id=t_id)
        else:
            draw_slot(gameboard, assets, slot_x, slot_y, 50, key_str, None, is_pressed=False)

        p_size = 36
        p_spacing = 6
        start_px = rx + 15
        for i in range(6):
            slot_x = start_px + (i * (p_size + p_spacing))
            gameboard.blit(pygame.transform.scale(assets.btn_small_img, (p_size, p_size)), (slot_x, 140))
            if i < len(active_passives):
                p_id = active_passives[i]
                lvl = passive_levels[p_id]
                pygame.draw.rect(gameboard, "#3b2f2f", (slot_x + 4, 144, p_size - 8, p_size - 8), border_radius=4)
                initial = p_id[0].upper()
                txt_surf = assets.ui_font_small.render(f"{initial}{lvl}", True, "yellow")
                txt_x = slot_x + (p_size // 2) - (txt_surf.get_width() // 2)
                txt_y = 140 + (p_size // 2) - (txt_surf.get_height() // 2)
                gameboard.blit(txt_surf, (txt_x, txt_y))

        current_wall_cost = min(50, 10 + int(player_level * 0.8))
        wall_key = pygame.key.name(settings.controls["wall"])
        is_wall_pressed = (current_tool == "wall")
        draw_slot(gameboard, assets, rx + 25, 200, 50, wall_key, current_wall_cost, is_pressed=is_wall_pressed, t_id="wall")

        draw_ribbon(gameboard, rx + 100, 210, 140, 40, assets.ribbon_sheet, rw=0)
        gold_surf = assets.ui_font_large.render(f"{player_gold} G", True, "black")
        gameboard.blit(gold_surf, (rx + 170 - gold_surf.get_width() // 2, 215))

        repair_all_cost = int((castle_max_hp - castle_hp) * 2)
        sell_key = pygame.key.name(settings.controls["sell"])
        rep_key = pygame.key.name(settings.controls["repair"])
        rep_all_key = pygame.key.name(settings.controls["repair_all"])

        is_sell_pressed = (current_tool == "sell")
        draw_action_btn(gameboard, assets, rx + 40, 420, 200, 50, sell_key, "Demolish", is_pressed=is_sell_pressed)

        is_rep_pressed = (current_tool == "repair")
        draw_action_btn(gameboard, assets, rx + 40, 510, 200, 50, rep_key, "Repair", is_pressed=is_rep_pressed)

        rep_all_rect = pygame.Rect(rx + 40, 600, 200, 50)
        is_rep_all_pressed = keys[settings.controls["repair_all"]] or (
                rep_all_rect.collidepoint(mouseX, mouseY) and pygame.mouse.get_pressed()[0])
        draw_action_btn(gameboard, assets, rx + 40, 600, 200, 50, rep_all_key, "Repair All", repair_all_cost,
                        is_pressed=is_rep_all_pressed)

    if game_state == "GAME_OVER":
        draw_game_over_menu(gameboard, assets, current_minute, game_time)
        
        # Botones de Restart y Menu
        restart_rect = pygame.Rect(640 - 220, 500, 200, 50)
        quit_rect = pygame.Rect(640 + 20, 500, 200, 50)
        
        restart_pressed = pygame.mouse.get_pressed()[0] and restart_rect.collidepoint(mouseX, mouseY)
        quit_pressed = pygame.mouse.get_pressed()[0] and quit_rect.collidepoint(mouseX, mouseY)
        
        draw_action_btn(gameboard, assets, 640 - 220, 500, 200, 50, None, "Restart", is_pressed=restart_pressed)
        draw_action_btn(gameboard, assets, 640 + 20, 500, 200, 50, None, "Menu", is_pressed=quit_pressed)

    elif game_state == "LEVEL_UP":
        card_rects = draw_level_up_menu(gameboard, assets, level_up_options, selected_card_idx, offsetX, width_gameboard)

    elif game_state == "PAUSED":
        # MAGIA: Si hay confirmación, el menú de pausa recibe un ratón fuera de la pantalla
        mx, my = (-1, -1) if confirm_action else (mouseX, mouseY)
        pause_rects = draw_pause_menu(gameboard, assets, mx, my)

        if confirm_action:
            dark_overlay = pygame.Surface((1280, 720), pygame.SRCALPHA)
            dark_overlay.fill((0, 0, 0, 150))
            gameboard.blit(dark_overlay, (0, 0))

            draw_ribbon(gameboard, 640 - 150, 360 - 100, 300, 80, assets.ribbon_sheet)
            q_surf = assets.ui_font_medium.render("Are you sure?", True, "black")
            gameboard.blit(q_surf, (640 - q_surf.get_width() // 2, 360 - 75))

            yes_rect = pygame.Rect(640 - 120, 360, 100, 50)
            no_rect = pygame.Rect(640 + 20, 360, 100, 50)

            yes_pressed = pygame.mouse.get_pressed()[0] and yes_rect.collidepoint(mouseX, mouseY)
            no_pressed = pygame.mouse.get_pressed()[0] and no_rect.collidepoint(mouseX, mouseY)

            draw_action_btn(gameboard, assets, 640 - 120, 360, 100, 50, None, "Yes", is_pressed=yes_pressed)
            draw_action_btn(gameboard, assets, 640 + 20, 360, 100, 50, None, "No", is_pressed=no_pressed)
            
    elif game_state == "MAIN_MENU":
        main_menu_rects = draw_main_menu(gameboard, assets, mouseX, mouseY)

    if assets.cursor_img:
        gameboard.blit(assets.cursor_img, (mouseX, mouseY))

    screensize = screen.get_size()
    rescaled_gameboard = pygame.transform.scale(gameboard, screensize)
    screen.blit(rescaled_gameboard, (0, 0))

    pygame.display.flip()
    dt = clock.tick(60) / 1000

    if game_state == "PLAYING":
        game_time += dt * time_scale
        current_minute = int(game_time // 60)
        difficulty_multiplier = round(1 + (current_minute / 8) ** 1.8, 2)

        regen_lvl = passive_levels.get("regen", 0)
        if regen_lvl > 0:
            castle_hp = min(castle_max_hp, castle_hp + (castle_max_hp * (0.01 * regen_lvl) * dt * time_scale))

        if len(spawn_schedule) > 0:
            next_spawn_time, next_spawn_type = spawn_schedule[0]
            if game_time >= next_spawn_time:
                setup_spawn_point(spawn_group, effects_group, grid, next_spawn_type, forced_initial_spawns, spawn_counts, existing_spawns_pos, assets)
                spawn_schedule.pop(0)

        current_weight = sum(ENEMY_WEIGHTS.get(type(e).__name__, 1.0) for e in enemy_group)
        active_portals = len(spawn_group)

        if game_time >= 1050:
            population_cap = 9999
            spawn_cooldown_multiplier = 0.3
        else:
            population_cap = (15 + (current_minute * 2.0)) * max(1, active_portals)
            spawn_cooldown_multiplier = 1.0

        current_pool_key = max(k for k in WAVE_POOLS.keys() if k <= current_minute)
        current_pool = WAVE_POOLS[current_pool_key]

        spawn_group.update(dt * time_scale, enemy_group, grid, offsetX, grid_size, current_weight, population_cap,
                           current_pool, spawn_cooldown_multiplier, difficulty_multiplier)

        # --- BOSS SPAWNER ---
        if "next_boss_time" not in globals():
            next_boss_time = 150.0
            bosses_spawned = 0

        if game_time >= next_boss_time and bosses_spawned < 6:
            if spawn_group:
                portal = random.choice(spawn_group.sprites())
                from Entities.Enemies.enemies import Boss

                px = offsetX + (portal.spawn_x * grid_size) + (grid_size / 2)
                py = (portal.spawn_y * grid_size) + (grid_size / 2)

                minotaur = Boss(px, py, grid_size, offsetX)

                # Le aplicamos la dificultad también a este tanque
                minotaur.health *= difficulty_multiplier
                minotaur.base_damage = int(minotaur.base_damage * difficulty_multiplier)

                enemy_group.add(minotaur)
                effects_group.add(Effect(px, py, assets.explosion_sheet, scale_size=120, fps=15))

            bosses_spawned += 1
            next_boss_time += 150.0
        # --------------------

        enemy_group.update(dt * time_scale, grid, enemy_group=enemy_group, effects_group=effects_group,
                           structures_hp=structures_hp,
                           passive_levels=passive_levels, thorns_values=THORNS_VALUES)

        for coords, hp in structures_hp.items():
            if coords in previous_structures_hp and hp < previous_structures_hp[coords]:
                damage_timers[coords] = 4

        for coords in list(damage_timers.keys()):
            damage_timers[coords] -= dt * time_scale
            if damage_timers[coords] <= 0:
                del damage_timers[coords]

        for coords in previous_structures_hp.keys():
            if coords not in structures_hp:
                fx_x = offsetX + (coords[1] * grid_size) + (grid_size // 2)
                fx_y = (coords[0] * grid_size) + (grid_size // 2)

                if previous_structures_types.get(coords) == wall:
                    effects_group.add(Effect(fx_x, fx_y, assets.dust_sheet, scale_size=55, fps=15))
                else:
                    effects_group.add(Effect(fx_x, fx_y, assets.dust_sheet, scale_size=100, fps=15))

        previous_structures_hp = structures_hp.copy()
        previous_structures_types = {coords: grid[coords[0]][coords[1]] for coords in structures_hp.keys()}

        broken_walls = []
        for (r, c) in list(wall_masks.keys()):
            if grid[r][c] != wall:
                broken_walls.append((r, c))

        for (r, c) in broken_walls:
            del wall_masks[(r, c)]
            ruin_masks[(r, c)] = 0
            update_ruin_masks(r, c, grid, ruin_masks)
            update_neighbors_walls(r, c, grid, wall_masks, ruin_masks)

        for enemy in enemy_group:
            # IGNORAMOS AL BOSS: Solo los masillas hacen daño de contacto
            if type(enemy).__name__ != "Boss":
                dist = enemy.pos.distance_to(pygame.math.Vector2(castle_obj.rect.center))
                if dist < (enemy.radius + 40):
                    if not hasattr(enemy, "castle_attack_timer"):
                        enemy.castle_attack_timer = 1.0
                    enemy.castle_attack_timer += dt * time_scale
                    if enemy.castle_attack_timer >= 1.0:
                        castle_hp -= getattr(enemy, "base_damage", 5)
                        enemy.castle_attack_timer = 0.0

            # ESTO ES LO QUE APLICA EL DAÑO DEL HACHAZO AL CASTILLO
            if getattr(enemy, "shot_castle", 0) > 0:
                castle_hp -= enemy.shot_castle
                enemy.shot_castle = 0

        if castle_hp <= 0:
            castle_hp = 0
            game_state = "GAME_OVER"

        collisions = pygame.sprite.groupcollide(enemy_group, enemy_group, False, False)
        for enemy, others in collisions.items():
            if type(enemy).__name__ == "Generator" or getattr(enemy, "is_falling", False):
                continue

            push_margin = margin - 2
            e_col = int((enemy.pos.x - offsetX) // grid_size)
            e_row = int(enemy.pos.y // grid_size)

            if e_col < push_margin or e_col >= col - push_margin or e_row < push_margin or e_row >= row - push_margin:
                continue

            push_final = pygame.math.Vector2(0, 0)
            for other in others:
                if other == enemy or type(other).__name__ == "Generator" or getattr(other, "is_falling", False):
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

        for t in player_group:
            if not getattr(t, "is_castle", False) and hasattr(t, "x"):
                t_col = int((t.x - offsetX) // grid_size)
                t_row = int(t.y // grid_size)
                if grid[t_row][t_col] != turret:
                    t.kill()

        player_group.update(dt * time_scale, enemy_group, bullet_group, tower_levels, passive_levels)
        bullet_group.update(dt * time_scale)
        effects_group.update(dt * time_scale)
        chest_group.update(dt * time_scale)

        # Comprobamos si el cofre ha terminado de escupir monedas
        for chest in chest_group:
            if chest.trigger_level_up:
                chest.trigger_level_up = False
                player_gold += 100
                game_state = "LEVEL_UP"
                level_up_options = get_level_up_cards(player_level, active_towers, tower_levels, active_passives, passive_levels)

                # Preparamos el fundido para cuando volvamos a "PLAYING"
                chest.state = "fading_white"
                chest.anim_timer = 0.0

        for bullet in bullet_group:
            if not hasattr(bullet, "pierce"):
                continue
            bx = int((bullet.pos.x - offsetX) // grid_size)
            by = int(bullet.pos.y // grid_size)
            if 0 <= bx < col and 0 <= by < row:
                if grid[by][bx] == mountain:
                    if hasattr(bullet, "aoe_radius"):
                        exp = Effect(bullet.rect.centerx, bullet.rect.centery, assets.explosion_sheet,
                                     int(bullet.aoe_radius * 3.5), fps=20)
                        effects_group.add(exp)
                    bullet.kill()

        hits = pygame.sprite.groupcollide(bullet_group, enemy_group, False, False)
        for arrow, enemies_hit in hits.items():
            if not hasattr(arrow, "pierce"):
                continue

            for enemy in enemies_hit:
                if enemy not in getattr(arrow, "hit_enemies", set()):
                    arrow.hit_enemies.add(enemy)
                    dmg_buff = 1.0 + (passive_levels.get("damage", 0) * 0.05)
                    final_damage = arrow.damage * dmg_buff

                    if random.random() < (passive_levels.get("crit", 0) * 0.10):
                        final_damage *= 1.5

                    if hasattr(arrow, "aoe_radius"):
                        exp = Effect(arrow.rect.centerx, arrow.rect.centery, assets.explosion_sheet,
                                     int(arrow.aoe_radius * 3.5), fps=20)
                        effects_group.add(exp)
                        for e in enemy_group:
                            if pygame.math.Vector2(arrow.rect.center).distance_to(e.pos) <= arrow.aoe_radius:
                                e.take_damage(final_damage)
                    else:
                        enemy.take_damage(final_damage)

                    arrow.pierce -= 1
                    if arrow.pierce <= 0:
                        arrow.kill()
                        break

        for enemy in list(enemy_group):
            if type(enemy).__name__ == "AttachedLeaf":
                continue
            if enemy.health <= 0 and not getattr(enemy, "is_dying", False):
                enemy.is_dying = True
                enemy.state = "death"
                if type(enemy).__name__ == "Boss":
                    from Entities.effects import Chest

                    chest_group.add(Chest(enemy.pos.x, enemy.pos.y, assets))
                enemy.current_frame = 0


                gold_buff = 1.0 + (passive_levels.get("gold", 0) * 0.05)
                xp_buff = 1.0 + (passive_levels.get("xp", 0) * 0.05)
                player_gold += int(enemy.gold_value * gold_buff)
                player_xp += int(enemy.xp_value * xp_buff * difficulty_multiplier)

                if player_xp >= xp_to_next_level:
                    player_xp -= xp_to_next_level
                    player_level += 1
                    hp_buff = 1.0 + (passive_levels.get("health", 0) * 0.05) + meta_health
                    new_castle_max = int((100 + (player_level * 18)) * hp_buff)
                    castle_hp += (new_castle_max - castle_max_hp)
                    castle_max_hp = new_castle_max

                    old_wall_max = int((25 + ((player_level - 1) * 1.5)) * hp_buff)
                    new_wall_max = int((25 + (player_level * 1.5)) * hp_buff)
                    wall_delta = new_wall_max - old_wall_max

                    for r in range(row):
                        for c in range(col):
                            if grid[r][c] == wall and (r, c) in structures_hp:
                                structures_hp[(r, c)] += wall_delta

                    if player_level < 51:
                        xp_to_next_level += 15 + (player_level * 2)
                    else:
                        xp_to_next_level = int(xp_to_next_level * 2.5)

                    game_state = "LEVEL_UP"
                    level_up_options = get_level_up_cards(player_level, active_towers, tower_levels, active_passives, passive_levels)

pygame.quit()
