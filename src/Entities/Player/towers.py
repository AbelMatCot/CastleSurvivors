import pygame
import math
import os
import random
from Entities.Player.projectiles import Arrow, Fireball, Kunai

try:
    lightning_sheet = pygame.image.load(os.path.join("Assets", "Sprites", "Effects", "lightning.png"))
except FileNotFoundError:
    lightning_sheet = None

try:
    thorns_sheet = pygame.image.load(os.path.join("Assets", "Sprites", "Effects", "spikes.png"))
except FileNotFoundError:
    thorns_sheet = None
try:
    smite_sheet = pygame.image.load(os.path.join("Assets", "Sprites", "Effects", "smite.png"))
except FileNotFoundError:
    smite_sheet = None

# Diccionario maestro de estadísticas basado en el PDF (Actualizado y Limpio)
TOWER_STATS = {
    "arrow": {
        1: {"cost": 18, "limit": 3, "range": 120, "damage": 5, "cd": 0.8, "proj": 1, "pierce": 1},
        2: {"cost": 20, "limit": 3, "range": 120, "damage": 8, "cd": 0.8, "proj": 1, "pierce": 1},
        3: {"cost": 25, "limit": 4, "range": 120, "damage": 8, "cd": 0.6, "proj": 1, "pierce": 1},
        4: {"cost": 34, "limit": 4, "range": 120, "damage": 8, "cd": 0.6, "proj": 1, "pierce": 2},
        5: {"cost": 47, "limit": 5, "range": 120, "damage": 12, "cd": 0.6, "proj": 1, "pierce": 2},
        6: {"cost": 63, "limit": 5, "range": 120, "damage": 12, "cd": 0.4, "proj": 1, "pierce": 2},
        7: {"cost": 83, "limit": 6, "range": 120, "damage": 12, "cd": 0.4, "proj": 1, "pierce": 3},
        8: {"cost": 212, "limit": 6, "range": 150, "damage": 22, "cd": 0.3, "proj": 1, "pierce": 3},
    },
    "fireball": {
        1: {"cost": 25, "limit": 2, "range": 80, "damage": 10, "cd": 1.5, "proj": 1, "area": 10, "pierce": 1},
        2: {"cost": 29, "limit": 2, "range": 80, "damage": 15, "cd": 1.5, "proj": 1, "area": 10, "pierce": 1},
        3: {"cost": 39, "limit": 2, "range": 80, "damage": 15, "cd": 1.3, "proj": 1, "area": 15, "pierce": 1},
        4: {"cost": 57, "limit": 3, "range": 80, "damage": 25, "cd": 1.3, "proj": 1, "area": 15, "pierce": 1},
        5: {"cost": 83, "limit": 3, "range": 90, "damage": 25, "cd": 1.1, "proj": 1, "area": 15, "pierce": 1},
        6: {"cost": 115, "limit": 3, "range": 90, "damage": 40, "cd": 1.1, "proj": 1, "area": 18, "pierce": 1},
        7: {"cost": 155, "limit": 4, "range": 90, "damage": 40, "cd": 1.1, "proj": 1, "area": 18, "pierce": 1},
        8: {"cost": 403, "limit": 4, "range": 110, "damage": 60, "cd": 0.9, "proj": 1, "area": 20, "pierce": 1},
    },
    "kunai": {
        1: {"cost": 29, "limit": 2, "range": 90, "damage": 7, "cd": 1.0, "proj": 1, "pierce": 1},
        2: {"cost": 32, "limit": 2, "range": 90, "damage": 7, "cd": 0.9, "proj": 1, "pierce": 1},
        3: {"cost": 39, "limit": 2, "range": 90, "damage": 7, "cd": 0.9, "proj": 3, "pierce": 1},
        4: {"cost": 52, "limit": 3, "range": 90, "damage": 15, "cd": 0.9, "proj": 3, "pierce": 1},
        5: {"cost": 69, "limit": 3, "range": 90, "damage": 15, "cd": 0.9, "proj": 5, "pierce": 1},
        6: {"cost": 92, "limit": 3, "range": 100, "damage": 15, "cd": 0.8, "proj": 5, "pierce": 1},
        7: {"cost": 119, "limit": 4, "range": 100, "damage": 15, "cd": 0.8, "proj": 5, "pierce": 1},
        8: {"cost": 303, "limit": 4, "range": 120, "damage": 25, "cd": 0.7, "proj": 7, "pierce": 1},
    },
    "laser": {
        1: {"cost": 22, "limit": 3, "range": 60, "damage": 1, "cd": 0.2, "proj": 1, "pierce": 1, "slow": 0.20},
        2: {"cost": 25, "limit": 3, "range": 60, "damage": 2, "cd": 0.2, "proj": 1, "pierce": 1, "slow": 0.20},
        3: {"cost": 34, "limit": 3, "range": 70, "damage": 2, "cd": 0.2, "proj": 1, "pierce": 1, "slow": 0.25},
        4: {"cost": 49, "limit": 4, "range": 70, "damage": 4, "cd": 0.2, "proj": 1, "pierce": 1, "slow": 0.25},
        5: {"cost": 70, "limit": 4, "range": 80, "damage": 4, "cd": 0.2, "proj": 1, "pierce": 1, "slow": 0.30},
        6: {"cost": 97, "limit": 4, "range": 80, "damage": 6, "cd": 0.2, "proj": 1, "pierce": 1, "slow": 0.30},
        7: {"cost": 130, "limit": 5, "range": 80, "damage": 6, "cd": 0.2, "proj": 1, "pierce": 1, "slow": 0.30},
        8: {"cost": 338, "limit": 5, "range": 90, "damage": 9, "cd": 0.2, "proj": 1, "pierce": 1, "slow": 0.40},
    },
    "lightning": {
        1: {"cost": 20, "limit": 3, "range": 80, "damage": 4, "cd": 0.8, "proj": 1, "bounces": 2, "pierce": 1},
        2: {"cost": 23, "limit": 3, "range": 80, "damage": 8, "cd": 0.8, "proj": 1, "bounces": 2, "pierce": 1},
        3: {"cost": 33, "limit": 3, "range": 80, "damage": 8, "cd": 0.7, "proj": 1, "bounces": 2, "pierce": 1},
        4: {"cost": 49, "limit": 4, "range": 80, "damage": 8, "cd": 0.7, "proj": 1, "bounces": 3, "pierce": 1},
        5: {"cost": 71, "limit": 4, "range": 80, "damage": 15, "cd": 0.7, "proj": 1, "bounces": 3, "pierce": 1},
        6: {"cost": 100, "limit": 4, "range": 80, "damage": 15, "cd": 0.6, "proj": 1, "bounces": 4, "pierce": 1},
        7: {"cost": 135, "limit": 5, "range": 80, "damage": 15, "cd": 0.6, "proj": 1, "bounces": 4, "pierce": 1},
        8: {"cost": 354, "limit": 5, "range": 100, "damage": 20, "cd": 0.5, "proj": 1, "bounces": 5, "pierce": 1},
    },
    "thorns": {
        1: {"cost": 27, "limit": 2, "range": 70, "damage": 4, "cd": 2.0, "proj": 1, "area": 20, "pierce": 5},
        2: {"cost": 31, "limit": 2, "range": 70, "damage": 7, "cd": 2.0, "proj": 1, "area": 20, "pierce": 5},
        3: {"cost": 41, "limit": 2, "range": 70, "damage": 7, "cd": 1.8, "proj": 1, "area": 20, "pierce": 5},
        4: {"cost": 59, "limit": 3, "range": 70, "damage": 10, "cd": 1.8, "proj": 1, "area": 20, "pierce": 5},
        5: {"cost": 83, "limit": 3, "range": 80, "damage": 10, "cd": 1.8, "proj": 1, "area": 25, "pierce": 5},
        6: {"cost": 115, "limit": 3, "range": 80, "damage": 10, "cd": 1.5, "proj": 1, "area": 25, "pierce": 5},
        7: {"cost": 153, "limit": 4, "range": 80, "damage": 10, "cd": 1.5, "proj": 1, "area": 25, "pierce": 5},
        8: {"cost": 397, "limit": 4, "range": 100, "damage": 14, "cd": 1.2, "proj": 1, "area": 30, "pierce": 5},
    },
    "smite": {
        1: {"cost": 30, "limit": 2, "range": 75, "damage": 13, "cd": 2.0, "proj": 1, "area": 15, "pierce": 1},
        2: {"cost": 34, "limit": 2, "range": 75, "damage": 13, "cd": 1.8, "proj": 1, "area": 15, "pierce": 1},
        3: {"cost": 45, "limit": 2, "range": 75, "damage": 21, "cd": 1.8, "proj": 1, "area": 15, "pierce": 1},
        4: {"cost": 63, "limit": 3, "range": 75, "damage": 21, "cd": 1.8, "proj": 1, "area": 20, "pierce": 1},
        5: {"cost": 89, "limit": 3, "range": 85, "damage": 21, "cd": 1.5, "proj": 1, "area": 20, "pierce": 1},
        6: {"cost": 123, "limit": 3, "range": 85, "damage": 33, "cd": 1.5, "proj": 1, "area": 20, "pierce": 1},
        7: {"cost": 163, "limit": 4, "range": 85, "damage": 33, "cd": 1.5, "proj": 1, "area": 20, "pierce": 1},
        8: {"cost": 423, "limit": 4, "range": 90, "damage": 48, "cd": 1.1, "proj": 1, "area": 25, "pierce": 1},
    },
}


class LightningVisual(pygame.sprite.Sprite):
    def __init__(self, start_pos, end_pos):
        super().__init__()
        self.frames = []
        dx = end_pos[0] - start_pos[0]
        dy = end_pos[1] - start_pos[1]

        if lightning_sheet:
            frame_w = 216
            frame_h = 108
            num_frames = lightning_sheet.get_width() // frame_w

            dist = max(1, math.hypot(dx, dy))
            angle = math.degrees(math.atan2(-dy, dx))

            for i in range(num_frames):
                frame = pygame.Surface((frame_w, frame_h), pygame.SRCALPHA)
                # Recortamos usando el ancho real (frame_w)
                frame.blit(lightning_sheet, (0, 0), (i * frame_w, 0, frame_w, frame_h))
                # Lo estiramos hasta el enemigo manteniendo el grosor de 35
                frame = pygame.transform.scale(frame, (int(dist), 35))
                frame = pygame.transform.rotate(frame, angle)
                self.frames.append(frame)

        self.current_frame = 0
        self.image = self.frames[0] if self.frames else pygame.Surface((0, 0))
        self.rect = self.image.get_rect(center=(start_pos[0] + dx / 2, start_pos[1] + dy / 2))
        self.timer = 0.0

    def update(self, dt):
        self.timer += dt
        if self.timer >= 0.05:
            self.timer = 0.0
            self.current_frame += 1
            if self.current_frame < len(self.frames):
                self.image = self.frames[self.current_frame]
            else:
                self.kill()


class IceBeamVisual(pygame.sprite.Sprite):
    def __init__(self, start_pos, end_pos):
        super().__init__()
        # Calculamos la caja que ocupa el láser
        min_x, max_x = min(start_pos[0], end_pos[0]), max(start_pos[0], end_pos[0])
        min_y, max_y = min(start_pos[1], end_pos[1]), max(start_pos[1], end_pos[1])

        pad = 10
        w = int(max(1, max_x - min_x) + pad * 2)
        h = int(max(1, max_y - min_y) + pad * 2)

        self.image = pygame.Surface((w, h), pygame.SRCALPHA)

        # Coordenadas locales dentro de la Surface
        lx1, ly1 = start_pos[0] - min_x + pad, start_pos[1] - min_y + pad
        lx2, ly2 = end_pos[0] - min_x + pad, end_pos[1] - min_y + pad

        # Dibujamos un resplandor azulado y el núcleo blanco
        pygame.draw.line(self.image, (0, 200, 255, 150), (lx1, ly1), (lx2, ly2), 6)
        pygame.draw.line(self.image, (255, 255, 255), (lx1, ly1), (lx2, ly2), 2)

        self.rect = self.image.get_rect(topleft=(min_x - pad, min_y - pad))
        self.timer = 0.0

    def update(self, dt):
        self.timer += dt
        if self.timer >= 0.2:  # Desaparece rápido
            self.kill()


class ThornsArea(pygame.sprite.Sprite):
    def __init__(self, x, y, stats, enemy_group):
        super().__init__()
        self.stats = stats
        self.enemy_group = enemy_group
        self.radius = stats.get("area", 25)
        self.max_size = int(self.radius * 2)

        self.frames_var1 = []
        self.frames_var2 = []

        if thorns_sheet:
            frame_size = 32
            scale_mult = max(1, round(self.max_size / frame_size))
            final_size = frame_size * scale_mult

            for i in range(7):
                # Fila 0 (Variación 1 - Arriba)
                f1 = pygame.Surface((frame_size, frame_size), pygame.SRCALPHA)
                f1.blit(thorns_sheet, (0, 0), (i * frame_size, 0, frame_size, frame_size))
                self.frames_var1.append(pygame.transform.scale(f1, (final_size, final_size)))

                # Fila 1 (Variación 2 - Abajo)
                f2 = pygame.Surface((frame_size, frame_size), pygame.SRCALPHA)
                f2.blit(thorns_sheet, (0, 0), (i * frame_size, frame_size, frame_size, frame_size))
                self.frames_var2.append(pygame.transform.scale(f2, (final_size, final_size)))
        else:
            for _ in range(7):
                surf = pygame.Surface((self.max_size, self.max_size), pygame.SRCALPHA)
                surf.fill((0, 100, 0, 100))
                self.frames_var1.append(surf)
                self.frames_var2.append(surf)

        self.life_timer = 0.0
        self.total_life = 1.5
        self.tick_timer = 0.5

        self.anim_timer = 0.0
        self.current_frame = 0
        self.ending = False

        # Empezamos con una variación aleatoria
        self.active_frames = random.choice([self.frames_var1, self.frames_var2])

        self.image = self.active_frames[0]
        self.rect = self.image.get_rect(center=(x, y))
        self.x = x
        self.y = y

    def update(self, dt):
        # 1. Animación visual
        self.anim_timer += dt
        if self.anim_timer >= 0.06:
            self.anim_timer = 0.0
            self.current_frame += 1

            if self.current_frame >= len(self.active_frames):
                if self.ending:
                    self.kill()
                    return
                else:
                    self.current_frame = 0
                    # ¡MAGIA AQUÍ! Al terminar el ciclo, elegimos variación nueva
                    self.active_frames = random.choice([self.frames_var1, self.frames_var2])

        self.image = self.active_frames[self.current_frame]

        # 2. Control de tiempo de vida
        self.life_timer += dt
        if self.life_timer >= self.total_life:
            self.ending = True

        # 3. Lógica de daño
        if not self.ending:
            self.tick_timer += dt
            if self.tick_timer >= 0.5:
                self.tick_timer -= 0.5

                hit_count = 0
                max_hits = self.stats.get("pierce", 4)
                damage = self.stats.get("damage", 3)

                for e in self.enemy_group:
                    if e.alive() and pygame.math.Vector2(self.x, self.y).distance_to(e.pos) <= self.radius:
                        e.take_damage(damage)
                        hit_count += 1
                        if hit_count >= max_hits:
                            break

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
        self.laser_timer = stats["cd"]

        # Generamos el visual del láser
        origin_y = self.y - 25
        bullet_group.add(IceBeamVisual((self.x, origin_y), enemy.pos))


class Tower(pygame.sprite.Sprite):
    def __init__(self, x, y, tower_id, projectile_class, color="blue", is_castle=False):
        super().__init__()
        self.tower_id = tower_id
        self.shoot_timer = 0.0
        self.projectile_class = projectile_class
        self.is_castle = is_castle
        self.x = x
        self.y = y

        # --- CARGA DINÁMICA DE SPRITES ---
        tipo_sprite = "castle" if is_castle else "tower"
        ruta_img = os.path.join("Assets", "Sprites", "Player", f"{tower_id}{tipo_sprite}.png")

        try:
            self.image = pygame.image.load(ruta_img).convert_alpha()
        except FileNotFoundError:
            # Fallback si no encuentra el dibujo
            ruta_fallback = os.path.join("Assets", "Sprites", "Player", f"fallback{tipo_sprite}.png")
            try:
                self.image = pygame.image.load(ruta_fallback).convert_alpha()
            except FileNotFoundError:
                # Por si acaso tampoco está el fallback
                self.image = pygame.Surface((60, 60) if is_castle else (30, 60))
                self.image.fill("magenta")

        self.rect = self.image.get_rect()

        # --- AJUSTE PARA EL Y-SORTING ---
        if self.is_castle:
            # El castillo ocupa 2x2. Su centro Y está en medio. La base está 30px abajo.
            self.rect.midbottom = (x, y + 30)
        else:
            # La torre ocupa 1 casilla. Su base está 15px debajo de su centro Y.
            self.rect.midbottom = (x, y + 15)

    def update(self, dt, enemy_group, bullet_group, tower_levels, passive_levels):
        level = max(1, tower_levels.get(self.tower_id, 1))
        self.level = level
        original_stats = TOWER_STATS[self.tower_id][level]

        stats = original_stats.copy()

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
                if getattr(enemy, "is_dying", False) or getattr(enemy, "is_untargetable", False) or enemy.health <= 0:
                    continue

                # Calculamos la distancia hasta el borde del enemigo, no hasta su centro
                dist_to_edge = tower_pos.distance_to(enemy.pos) - getattr(enemy, "radius", 0)

                if dist_to_edge < min_dist and dist_to_edge <= self.range:
                    min_dist = dist_to_edge
                    closest_enemy = enemy

            if closest_enemy:
                self.shoot_timer = 0.0
                origin_y = self.y - 25  # Subimos el cañón a la ventana de la torre

                if self.projectile_class:
                    projs = stats["proj"]
                    if projs == 1:
                        bullet_group.add(self.projectile_class((self.x, origin_y), closest_enemy.pos, stats))
                    else:
                        diff = closest_enemy.pos - pygame.math.Vector2(self.x, origin_y)
                        if diff.length() > 0:
                            base_dir = diff.normalize()
                        else:
                            base_dir = pygame.math.Vector2(1, 0)  # Salvavidas anti-crash

                        spread_angle = 15
                        start_angle = - (projs // 2) * spread_angle
                        for i in range(projs):
                            angle = start_angle + i * spread_angle
                            new_dir = base_dir.rotate(angle)
                            fake_target = pygame.math.Vector2(self.x, origin_y) + new_dir * 100
                            bullet_group.add(self.projectile_class((self.x, origin_y), fake_target, stats))
                else:
                    self.fire_instant(closest_enemy, stats, enemy_group, bullet_group)

    def fire_instant(self, enemy, stats, enemy_group, bullet_group):
        pass


class ArrowTower(Tower):
    def __init__(self, x, y, is_castle=False):
        super().__init__(x, y, "arrow", Arrow, color="white", is_castle=is_castle)


class FireballTower(Tower):
    def __init__(self, x, y, is_castle=False):
        super().__init__(x, y, "fireball", Fireball, color="orange", is_castle=is_castle)


class KunaiTower(Tower):
    def __init__(self, x, y, is_castle=False):
        super().__init__(x, y, "kunai", Kunai, color="gray", is_castle=is_castle)


class LaserTower(LaserMixin, Tower):
    def __init__(self, x, y, is_castle=False):
        super().__init__(x, y, "laser", None, color="cyan", is_castle=is_castle)
        self.init_laser_vars()

    def update(self, dt, enemy_group, bullet_group, tower_levels, passive_levels=None):
        if passive_levels is None:
            passive_levels = {}
        super().update(dt, enemy_group, bullet_group, tower_levels, passive_levels)
        self.update_laser(dt)


class LightningTower(Tower):
    def __init__(self, x, y, is_castle=False):
        super().__init__(x, y, "lightning", None, color="yellow", is_castle=is_castle)

    def fire_instant(self, enemy, stats, enemy_group, bullet_group):
        hit_enemies = [enemy]
        current_target = enemy

        current_target.take_damage(stats["damage"])
        origin_y = self.y - 25
        bullet_group.add(LightningVisual((self.x, origin_y), current_target.pos))

        # Lo sacamos del bucle y arreglamos el orden lógico
        if self.level == 8:
            bounce_range = self.range
        elif self.level >= 3:
            bounce_range = self.range * 0.9
        else:
            bounce_range = self.range * 0.75

        for _ in range(stats.get("bounces", 0)):
            next_target = None
            min_dist = float("inf")

            for e in enemy_group:
                if getattr(e, "is_dying", False) or e.health <= 0:
                    continue
                if e not in hit_enemies:
                    dist = current_target.pos.distance_to(e.pos)
                    # Ahora coincide la variable a la perfección
                    if dist <= bounce_range and dist < min_dist:
                        min_dist = dist
                        next_target = e

            if next_target:
                next_target.take_damage(stats["damage"])
                bullet_group.add(LightningVisual(current_target.pos, next_target.pos))
                hit_enemies.append(next_target)
                current_target = next_target
            else:
                break


class ThornsTower(Tower):
    def __init__(self, x, y, is_castle=False):
        super().__init__(x, y, "thorns", None, color="darkgreen", is_castle=is_castle)

    def fire_instant(self, enemy, stats, enemy_group, bullet_group):
        thorns = ThornsArea(enemy.pos.x, enemy.pos.y, stats, enemy_group)
        bullet_group.add(thorns)

class SmiteArea(pygame.sprite.Sprite):
    def __init__(self, x, y, stats, enemy_group):
        super().__init__()
        self.stats = stats
        self.enemy_group = enemy_group
        # Escalamos el radio para que se vea bien en el grid, como en la bola de fuego
        self.radius = stats.get("area", 15) * 2.5
        self.max_size = int(self.radius * 2)

        self.frames = []
        if smite_sheet:
            frame_size = 128
            for row in range(3):
                for col in range(5):
                    f = pygame.Surface((frame_size, frame_size), pygame.SRCALPHA)
                    f.blit(smite_sheet, (0, 0), (col * frame_size, row * frame_size, frame_size, frame_size))
                    self.frames.append(pygame.transform.scale(f, (self.max_size, self.max_size)))
        else:
            surf = pygame.Surface((self.max_size, self.max_size), pygame.SRCALPHA)
            surf.fill((255, 255, 0, 150))
            self.frames = [surf] * 15

        self.current_frame = 0
        self.image = self.frames[0]
        self.rect = self.image.get_rect(center=(x, y - 15))
        self.x = x
        self.y = y
        self.anim_timer = 0.0
        self.damage_dealt = False

    def update(self, dt):
        self.anim_timer += dt
        if self.anim_timer >= 0.04:  # Velocidad de la animación
            self.anim_timer = 0.0
            self.current_frame += 1

            # El ataque hace daño exactamente en el frame 5 (índice 4)
            if self.current_frame == 4 and not self.damage_dealt:
                damage = self.stats.get("damage", 13)
                for e in self.enemy_group:
                    if e.alive() and pygame.math.Vector2(self.x, self.y).distance_to(e.pos) <= self.radius:
                        e.take_damage(damage)
                self.damage_dealt = True

            if self.current_frame >= len(self.frames):
                self.kill()
            else:
                self.image = self.frames[self.current_frame]


class SmiteTower(Tower):
    def __init__(self, x, y, is_castle=False):
        super().__init__(x, y, "smite", None, color="yellow", is_castle=is_castle)

    def fire_instant(self, enemy, stats, enemy_group, bullet_group):
        smite = SmiteArea(enemy.pos.x, enemy.pos.y, stats, enemy_group)
        bullet_group.add(smite)