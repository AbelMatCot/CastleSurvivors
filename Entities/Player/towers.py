import pygame
import math
import os
from Entities.Player.projectiles import Arrow, Fireball, Kunai

try:
    lightning_sheet = pygame.image.load(os.path.join("Assets", "Sprites", "Effects", "lightning.png")).convert_alpha()
except FileNotFoundError:
    lightning_sheet = None
try:
    thorns_sheet = pygame.image.load(os.path.join("Assets", "Sprites", "Effects", "thorns.png")).convert_alpha()
except FileNotFoundError:
    thorns_sheet = None

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
    },
    "lightning": {
        1: {"cost": 20, "limit": 3, "range": 80, "damage": 4, "cd": 0.8, "proj": 1, "bounces": 2, "pierce": 1, "slow": 0},
        2: {"cost": 23, "limit": 3, "range": 80, "damage": 8, "cd": 0.8, "proj": 1, "bounces": 2, "pierce": 1, "slow": 0},
        3: {"cost": 33, "limit": 3, "range": 80, "damage": 8, "cd": 0.7, "proj": 1, "bounces": 2, "pierce": 1, "slow": 0},
        4: {"cost": 49, "limit": 4, "range": 80, "damage": 8, "cd": 0.7, "proj": 1, "bounces": 3, "pierce": 1, "slow": 0},
        5: {"cost": 71, "limit": 4, "range": 80, "damage": 15, "cd": 0.7, "proj": 1, "bounces": 3, "pierce": 1, "slow": 0},
        6: {"cost": 100, "limit": 4, "range": 80, "damage": 15, "cd": 0.6, "proj": 1, "bounces": 4, "pierce": 1, "slow": 0},
        7: {"cost": 135, "limit": 5, "range": 80, "damage": 15, "cd": 0.6, "proj": 1, "bounces": 4, "pierce": 1, "slow": 0},
        8: {"cost": 354, "limit": 5, "range": 100, "damage": 20, "cd": 0.5, "proj": 1, "bounces": 5, "pierce": 1, "slow": 0},
    },
    "thorns": {
        1: {"cost": 24, "limit": 3, "range": 90, "damage": 3, "cd": 2.0, "proj": 1, "area": 25, "pierce": 4, "slow": 0},
        2: {"cost": 28, "limit": 3, "range": 90, "damage": 5, "cd": 2.0, "proj": 1, "area": 25, "pierce": 4, "slow": 0},
        3: {"cost": 36, "limit": 3, "range": 90, "damage": 5, "cd": 1.8, "proj": 1, "area": 35, "pierce": 6, "slow": 0},
        4: {"cost": 52, "limit": 4, "range": 100, "damage": 8, "cd": 1.8, "proj": 1, "area": 35, "pierce": 6, "slow": 0},
        5: {"cost": 76, "limit": 4, "range": 100, "damage": 8, "cd": 1.8, "proj": 1, "area": 35, "pierce": 8, "slow": 0},
        6: {"cost": 110, "limit": 4, "range": 100, "damage": 12, "cd": 1.5, "proj": 1, "area": 45, "pierce": 8, "slow": 0},
        7: {"cost": 145, "limit": 5, "range": 110, "damage": 12, "cd": 1.5, "proj": 1, "area": 45, "pierce": 10, "slow": 0},
        8: {"cost": 380, "limit": 5, "range": 120, "damage": 20, "cd": 1.2, "proj": 1, "area": 55, "pierce": 12, "slow": 0},
    },
}

class LightningVisual(pygame.sprite.Sprite):
    def __init__(self, start_pos, end_pos):
        super().__init__()
        self.frames = []
        dx = end_pos[0] - start_pos[0]
        dy = end_pos[1] - start_pos[1]

        if lightning_sheet:
            h = lightning_sheet.get_height()
            w = lightning_sheet.get_width()
            num_frames = w // h
            dist = max(1, math.hypot(dx, dy))
            angle = math.degrees(math.atan2(-dy, dx))

            for i in range(num_frames):
                frame = pygame.Surface((h, h), pygame.SRCALPHA)
                frame.blit(lightning_sheet, (0, 0), (i * h, 0, h, h))
                frame = pygame.transform.scale(frame, (int(dist), 20))
                frame = pygame.transform.rotate(frame, angle)
                self.frames.append(frame)

        self.current_frame = 0
        self.image = self.frames[0] if self.frames else pygame.Surface((0, 0))
        self.rect = self.image.get_rect(center=(start_pos[0] + dx / 2, start_pos[1] + dy / 2))
        self.timer = 0.0

    def update(self, dt):
        self.timer += dt
        if self.timer >= 0.05:  # Flash súper rápido
            self.timer = 0.0
            self.current_frame += 1
            if self.current_frame < len(self.frames):
                self.image = self.frames[self.current_frame]
            else:
                self.kill()


class ThornsArea(pygame.sprite.Sprite):
    def __init__(self, x, y, stats, enemy_group):
        super().__init__()
        self.stats = stats
        self.enemy_group = enemy_group
        self.radius = stats.get("area", 25)
        self.max_size = int(self.radius * 2)

        self.frames = []
        if thorns_sheet:
            h = thorns_sheet.get_height()
            w = thorns_sheet.get_width()
            num_frames = min(2, w // h)
            for i in range(num_frames):
                frame = pygame.Surface((h, h), pygame.SRCALPHA)
                frame.blit(thorns_sheet, (0, 0), (i * h, 0, h, h))
                self.frames.append(frame)
        else:
            surf = pygame.Surface((10, 10))
            surf.fill("darkgreen")
            self.frames.append(surf)

        self.life_timer = 0.0
        self.total_life = 1.5

        # Empezamos en 0.5 para que dé el primer bocado nada más nacer
        self.tick_timer = 0.5
        self.pulse_duration = 0.0

        self.image = pygame.Surface((0, 0))
        self.rect = self.image.get_rect(center=(x, y))
        self.x = x
        self.y = y

    def update(self, dt):
        self.life_timer += dt
        if self.life_timer >= self.total_life:
            self.kill()
            return

        # 1. El Temporizador de Daño y Latido
        self.tick_timer += dt
        if self.tick_timer >= 0.5:
            self.tick_timer -= 0.5
            self.pulse_duration = 0.15  # Duración del frame de latido

            # Repartir daño con el límite de perforación
            hit_count = 0
            max_hits = self.stats.get("pierce", 4)
            damage = self.stats.get("damage", 3)

            for e in self.enemy_group:
                if e.alive() and pygame.math.Vector2(self.x, self.y).distance_to(e.pos) <= self.radius:
                    e.take_damage(damage)
                    hit_count += 1
                    if hit_count >= max_hits:
                        break

        # 2. Control Visual del Latido
        if self.pulse_duration > 0:
            self.pulse_duration -= dt
            frame_idx = 1 if len(self.frames) > 1 else 0
        else:
            frame_idx = 0

        base_frame = self.frames[frame_idx]

        # 3. Animación de Crecer (0.2s) y Encoger (0.2s finales)
        grow_time = 0.2
        shrink_time = 0.2
        if self.life_timer < grow_time:
            scale_factor = self.life_timer / grow_time
        elif self.life_timer > self.total_life - shrink_time:
            scale_factor = (self.total_life - self.life_timer) / shrink_time
        else:
            scale_factor = 1.0

        # Transformación final
        current_size = max(1, int(self.max_size * scale_factor))
        self.image = pygame.transform.scale(base_frame, (current_size, current_size))
        self.rect = self.image.get_rect(center=(self.x, self.y))

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

    def fire_instant(self, enemy, stats, enemy_group, bullet_group):
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
                    self.fire_instant(closest_enemy, stats, enemy_group, bullet_group)

                def fire_instant(self, enemy, stats, enemy_group, bullet_group):
                    pass

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

    def update(self, dt, enemy_group, bullet_group, tower_levels, passive_levels=None):
        super().update(dt, enemy_group, bullet_group, tower_levels, passive_levels)
        self.update_laser(dt)


class LightningTower(Tower):
    def __init__(self, x, y):
        super().__init__(x, y, "lightning", None, color="yellow")

    def fire_instant(self, enemy, stats, enemy_group, bullet_group):
        hit_enemies = [enemy]
        current_target = enemy

        # Daño al objetivo inicial y dibujamos su rayo desde la torre
        current_target.take_damage(stats["damage"])
        bullet_group.add(LightningVisual((self.x, self.y), current_target.pos))

        for _ in range(stats.get("bounces", 0)):
            next_target = None
            min_dist = float("inf")
            bounce_range = stats["range"] / 2

            for e in enemy_group:
                if e not in hit_enemies:
                    dist = current_target.pos.distance_to(e.pos)
                    if dist <= bounce_range and dist < min_dist:
                        min_dist = dist
                        next_target = e

            if next_target:
                next_target.take_damage(stats["damage"])
                # Rayo entre el enemigo viejo y el nuevo
                bullet_group.add(LightningVisual(current_target.pos, next_target.pos))
                hit_enemies.append(next_target)
                current_target = next_target
            else:
                break

class ThornsTower(Tower):
    def __init__(self, x, y):
        super().__init__(x, y, "thorns", None, color="darkgreen")

    def fire_instant(self, enemy, stats, enemy_group, bullet_group):
        thorns = ThornsArea(enemy.pos.x, enemy.pos.y, stats, enemy_group)
        bullet_group.add(thorns)