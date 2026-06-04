import pygame
import random
from Entities.Enemies.enemies import Basic, Fast, Tank, Generator, Shooter, Flyer
from Entities.effects import Effect
from gamedata import col, row, margin, offsetX, grid_size

def get_valid_border(spawn_type, forced_initial_spawns, spawn_counts):
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

def setup_spawn_point(spwn_grp, effects_group, grid, spawn_type, forced_initial_spawns, spawn_counts, existing_spawns_pos, assets):
    side = get_valid_border(spawn_type, forced_initial_spawns, spawn_counts)
    if not side: return

    valid_pos = False
    attempts = 0
    center = 0

    while not valid_pos and attempts < 50:
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
        spawn_x, spawn_y = center, -1
        grid[0][center] = margin
        fx_base = offsetX + (center * grid_size) + 15
        fy_base = 0 * grid_size + 15
    elif side == "South":
        spawn_x, spawn_y = center, row
        grid[row - 1][center] = margin
        fx_base = offsetX + (center * grid_size) + 15
        fy_base = (row - 1) * grid_size + 15
    elif side == "West":
        spawn_x, spawn_y = -1, center
        grid[center][0] = margin
        fx_base = offsetX + 0 * grid_size + 15
        fy_base = (center * grid_size) + 15
    elif side == "East":
        spawn_x, spawn_y = col, center
        grid[center][col - 1] = margin
        fx_base = offsetX + (col - 1) * grid_size + 15
        fy_base = (center * grid_size) + 15

    new_spawn = Spawn(spawn_x, spawn_y)
    spwn_grp.add(new_spawn)

    offsets = [(0, 0, 0.0), (-14, 8, 0.15), (14, 18, 0.3)]
    for ox, oy, dly in offsets:
        dust = Effect(fx_base + ox, fy_base + oy, assets.dust_sheet, scale_size=70, fps=11, delay=dly)
        effects_group.add(dust)

class Spawn(pygame.sprite.Sprite):
    def __init__(self, spawn_x, spawn_y):
        super().__init__()
        self.spawn_x = spawn_x
        self.spawn_y = spawn_y

        self.image = pygame.Surface((30, 30), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self.rect.x = spawn_x
        self.rect.y = spawn_y

        self.timer = 0.0
        self.base_cooldown = 2.5  # Un poco más rápido que antes para mantener la presión

    def update(self, dt, enemy_group, grid, offset_x, grid_size,
               current_weight, population_cap, current_pool, cd_multiplier, difficulty_multiplier=1.0):

        self.timer += dt
        current_cd = self.base_cooldown * cd_multiplier

        if self.timer > current_cd:
            self.timer = 0.0

            if current_weight >= population_cap:
                return

            px = offset_x + (self.spawn_x * grid_size) + (grid_size / 2)
            py = (self.spawn_y * grid_size) + (grid_size / 2)

            enemy_types = list(current_pool.keys())
            weights = list(current_pool.values())
            chosen_type = random.choices(enemy_types, weights=weights, k=1)[0]

            if chosen_type == "Basic":
                new_enemy = Basic(px, py, grid_size, offset_x)
            elif chosen_type == "Fast":
                new_enemy = Fast(px, py, grid_size, offset_x)
            elif chosen_type == "Shooter":
                new_enemy = Shooter(px, py, grid_size, offset_x)
            elif chosen_type == "Tank":
                new_enemy = Tank(px, py, grid_size, offset_x)
            elif chosen_type == "Flyer":
                new_enemy = Flyer(px, py, grid_size, offset_x)
            elif chosen_type == "Generator":
                new_enemy = Generator(px, py, grid_size, offset_x)

            # Dificultad
            new_enemy.health *= difficulty_multiplier
            new_enemy.base_damage = int(new_enemy.base_damage * difficulty_multiplier)

            enemy_group.add(new_enemy)