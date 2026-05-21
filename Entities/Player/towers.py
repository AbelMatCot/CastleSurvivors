import pygame
from Entities.Player.projectiles import Arrow, Fireball, Kunai

class LaserMixin:
    def init_laser_vars(self):
        self.slow_factor = 0.8
        self.is_firing = False
        self.target = None
        self.laser_timer = 0.0

    def update_laser(self, dt):
        if getattr(self, "is_firing", False):
            self.laser_timer -= dt
            if self.laser_timer <= 0:
                self.is_firing = False
                self.target = None

    def fire_laser(self, enemy):
        enemy.take_damage(1)
        enemy.apply_slow(self.slow_factor, 0.5)
        self.target = enemy
        self.is_firing = True
        self.laser_timer = 0.1

class Tower(pygame.sprite.Sprite):
    def __init__(self, x, y, cooldown, range_px, projectile_class, color="blue"):
        super().__init__()
        self.shoot_timer = 0.0
        self.shoot_cooldown = cooldown
        self.range = range_px
        self.projectile_class = projectile_class

        self.image = pygame.Surface((30, 30), pygame.SRCALPHA)
        pygame.draw.circle(self.image, color, (15, 15), 10)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.x = x
        self.y = y

    def update(self, dt, enemy_group, bullet_group):
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
                    new_bullet = self.projectile_class((self.x, self.y), closest_enemy.pos)
                    bullet_group.add(new_bullet)
                else:
                    self.fire_laser(closest_enemy)

    def fire_laser(self, enemy):
        pass  # Se usa solo en el láser


class ArrowTower(Tower):
    def __init__(self, x, y):
        super().__init__(x, y, cooldown=0.8, range_px=120.0, projectile_class=Arrow, color="white")


class FireballTower(Tower):
    def __init__(self, x, y):
        super().__init__(x, y, cooldown=1.5, range_px=75.0, projectile_class=Fireball, color="orange")


class KunaiTower(Tower):
    def __init__(self, x, y):
        super().__init__(x, y, cooldown=1.0, range_px=90.0, projectile_class=Kunai, color="gray")


class LaserTower(Tower, LaserMixin):
    def __init__(self, x, y):
        super().__init__(x, y, cooldown=0.2, range_px=60.0, projectile_class=None, color="cyan")
        self.init_laser_vars()

    def update(self, dt, enemy_group, bullet_group):
        super().update(dt, enemy_group, bullet_group)
        self.update_laser(dt)