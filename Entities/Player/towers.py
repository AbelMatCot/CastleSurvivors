import pygame
from Entities.Player.projectiles import Arrow, Fireball, Kunai

# Diccionario maestro de estadísticas basado en el PDF
TOWER_STATS = {
    "arrow": {
        1: {"cost": 18, "limit": 4, "range": 120, "damage": 5, "cd": 0.8, "proj": 1, "pierce": 1, "slow": 0},
        2: {"cost": 20, "limit": 4, "range": 120, "damage": 8, "cd": 0.8, "proj": 1, "pierce": 1, "slow": 0},
        3: {"cost": 25, "limit": 4, "range": 120, "damage": 8, "cd": 0.6, "proj": 1, "pierce": 1, "slow": 0},
        4: {"cost": 34, "limit": 5, "range": 120, "damage": 8, "cd": 0.6, "proj": 1, "pierce": 2, "slow": 0},
        5: {"cost": 47, "limit": 5, "range": 120, "damage": 12, "cd": 0.6, "proj": 1, "pierce": 2, "slow": 0},
        6: {"cost": 63, "limit": 5, "range": 120, "damage": 12, "cd": 0.4, "proj": 1, "pierce": 2, "slow": 0},
        7: {"cost": 83, "limit": 6, "range": 120, "damage": 12, "cd": 0.4, "proj": 1, "pierce": 3, "slow": 0},
        8: {"cost": 212, "limit": 6, "range": 150, "damage": 22, "cd": 0.3, "proj": 1, "pierce": 3, "slow": 0},
    },
    "fireball": {
        1: {"cost": 25, "limit": 2, "range": 80, "damage": 10, "cd": 1.5, "proj": 1, "area": 10, "pierce": 1, "slow": 0},
        2: {"cost": 29, "limit": 2, "range": 80, "damage": 15, "cd": 1.5, "proj": 1, "area": 10, "pierce": 1, "slow": 0},
        3: {"cost": 39, "limit": 2, "range": 80, "damage": 15, "cd": 1.3, "proj": 1, "area": 15, "pierce": 1, "slow": 0},
        4: {"cost": 57, "limit": 3, "range": 80, "damage": 25, "cd": 1.3, "proj": 1, "area": 15, "pierce": 1, "slow": 0},
        5: {"cost": 83, "limit": 3, "range": 90, "damage": 25, "cd": 1.1, "proj": 1, "area": 15, "pierce": 1, "slow": 0},
        6: {"cost": 115, "limit": 3, "range": 90, "damage": 40, "cd": 1.1, "proj": 1, "area": 18, "pierce": 1, "slow": 0},
        7: {"cost": 155, "limit": 4, "range": 90, "damage": 40, "cd": 1.1, "proj": 1, "area": 18, "pierce": 1, "slow": 0},
        8: {"cost": 403, "limit": 4, "range": 110, "damage": 60, "cd": 0.9, "proj": 1, "area": 20, "pierce": 1, "slow": 0},
    },
    "kunai": {
        1: {"cost": 29, "limit": 2, "range": 90, "damage": 7, "cd": 1.0, "proj": 1, "pierce": 1, "slow": 0},
        2: {"cost": 32, "limit": 2, "range": 90, "damage": 7, "cd": 0.9, "proj": 1, "pierce": 1, "slow": 0},
        3: {"cost": 39, "limit": 2, "range": 90, "damage": 7, "cd": 0.9, "proj": 3, "pierce": 1, "slow": 0},
        4: {"cost": 52, "limit": 3, "range": 90, "damage": 15, "cd": 0.9, "proj": 3, "pierce": 1, "slow": 0},
        5: {"cost": 69, "limit": 3, "range": 90, "damage": 15, "cd": 0.9, "proj": 5, "pierce": 1, "slow": 0},
        6: {"cost": 92, "limit": 3, "range": 100, "damage": 15, "cd": 0.8, "proj": 5, "pierce": 1, "slow": 0},
        7: {"cost": 119, "limit": 4, "range": 100, "damage": 15, "cd": 0.8, "proj": 5, "pierce": 1, "slow": 0},
        8: {"cost": 303, "limit": 4, "range": 120, "damage": 25, "cd": 0.7, "proj": 7, "pierce": 1, "slow": 0},
    },
    "laser": {
        1: {"cost": 22, "limit": 2, "range": 60, "damage": 1, "cd": 0.2, "proj": 1, "pierce": 1, "slow": 0.20},
        2: {"cost": 25, "limit": 2, "range": 60, "damage": 2, "cd": 0.2, "proj": 1, "pierce": 1, "slow": 0.20},
        3: {"cost": 34, "limit": 2, "range": 70, "damage": 2, "cd": 0.2, "proj": 1, "pierce": 1, "slow": 0.25},
        4: {"cost": 49, "limit": 3, "range": 70, "damage": 4, "cd": 0.2, "proj": 1, "pierce": 1, "slow": 0.25},
        5: {"cost": 70, "limit": 3, "range": 80, "damage": 4, "cd": 0.2, "proj": 1, "pierce": 1, "slow": 0.30},
        6: {"cost": 97, "limit": 3, "range": 80, "damage": 6, "cd": 0.2, "proj": 1, "pierce": 1, "slow": 0.30},
        7: {"cost": 130, "limit": 4, "range": 80, "damage": 6, "cd": 0.2, "proj": 1, "pierce": 1, "slow": 0.30},
        8: {"cost": 338, "limit": 4, "range": 90, "damage": 8, "cd": 0.2, "proj": 1, "pierce": 1, "slow": 0.40},
    }
}

class LaserMixin:
    def init_laser_vars(self):
        self.is_firing = False
        self.target = None
        self.laser_timer = 0.0

    def update_laser(self, dt):
        if getattr(self, "is_firing", False):
            self.laser_timer -= dt
            if self.laser_timer <= 0:
                self.is_firing = False
                self.target = None

    def fire_laser(self, enemy, stats):
        enemy.take_damage(stats["damage"])
        enemy.apply_slow(stats["slow"], 0.5)
        self.target = enemy
        self.is_firing = True
        # El tiempo visual ahora dura exactamente lo mismo que el cooldown
        self.laser_timer = stats["cd"]

class Tower(pygame.sprite.Sprite):
    def __init__(self, x, y, tower_id, projectile_class, color="blue"):
        super().__init__()
        self.tower_id = tower_id
        self.shoot_timer = 0.0
        self.projectile_class = projectile_class

        self.image = pygame.Surface((30, 30), pygame.SRCALPHA)
        pygame.draw.circle(self.image, color, (15, 15), 10)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.x = x
        self.y = y

    def update(self, dt, enemy_group, bullet_group, tower_levels, passive_levels):
        level = max(1, tower_levels.get(self.tower_id, 1))
        original_stats = TOWER_STATS[self.tower_id][level]

        # Clonamos el diccionario para no sobreescribir los stats base
        stats = original_stats.copy()

        # --- PASIVAS: Cadencia y Rango/Área ---
        stats["cd"] = original_stats["cd"] * (1.0 - (passive_levels.get("firerate", 0) * 0.05))

        range_buff = 1.0 + (passive_levels.get("range", 0) * 0.05)
        stats["range"] = original_stats["range"] * range_buff
        if "area" in stats:
            stats["area"] = original_stats["area"] * range_buff

        self.shoot_cooldown = stats["cd"]
        self.range = stats["range"]

        self.shoot_timer += dt
        if self.shoot_timer >= self.shoot_cooldown:
            closest_enemy = None
            min_dist = float("inf")
            tower_pos = pygame.math.Vector2(self.x, self.y)

            for enemy in enemy_group:
                dist = tower_pos.distance_to(enemy.pos)
                if dist < min_dist and dist <= self.range:
                    min_dist = dist
                    closest_enemy = enemy

            if closest_enemy:
                self.shoot_timer = 0.0
                if self.projectile_class:
                    projs = stats["proj"]
                    if projs == 1:
                        bullet_group.add(self.projectile_class((self.x, self.y), closest_enemy.pos, stats))
                    else:
                        # Disparo en abanico para múltiples proyectiles (ej. Kunai nivel 3+)
                        base_dir = (closest_enemy.pos - pygame.math.Vector2(self.x, self.y)).normalize()
                        spread_angle = 15
                        start_angle = - (projs // 2) * spread_angle
                        for i in range(projs):
                            angle = start_angle + i * spread_angle
                            new_dir = base_dir.rotate(angle)
                            fake_target = pygame.math.Vector2(self.x, self.y) + new_dir * 100
                            bullet_group.add(self.projectile_class((self.x, self.y), fake_target, stats))
                else:
                    self.fire_laser(closest_enemy, stats)

    def fire_laser(self, enemy, stats):
        pass


class ArrowTower(Tower):
    def __init__(self, x, y):
        super().__init__(x, y, "arrow", Arrow, color="white")

class FireballTower(Tower):
    def __init__(self, x, y):
        super().__init__(x, y, "fireball", Fireball, color="orange")

class KunaiTower(Tower):
    def __init__(self, x, y):
        super().__init__(x, y, "kunai", Kunai, color="gray")

class LaserTower(LaserMixin, Tower):
    def __init__(self, x, y):
        super().__init__(x, y, "laser", None, color="cyan")
        self.init_laser_vars()

    def update(self, dt, enemy_group, bullet_group, tower_levels):
        super().update(dt, enemy_group, bullet_group, tower_levels)
        self.update_laser(dt)