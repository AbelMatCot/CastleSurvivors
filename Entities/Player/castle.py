import pygame
from Entities.Player.towers import Tower, LaserMixin
from Entities.Player.projectiles import Arrow, Fireball, Kunai

class Castle(Tower):
    def __init__(self, x, y, tower_id, projectile_class, color="yellow"):
        super().__init__(x, y, tower_id, projectile_class, color)
        self.image = pygame.Surface((60, 60))
        self.image.fill("yellow")
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)

class ArrowCastle(Castle):
    def __init__(self, x, y):
        super().__init__(x, y, "arrow", Arrow)

class FireballCastle(Castle):
    def __init__(self, x, y):
        super().__init__(x, y, "fireball", Fireball)

class KunaiCastle(Castle):
    def __init__(self, x, y):
        super().__init__(x, y, "kunai", Kunai)

class LaserCastle(LaserMixin, Castle):
    def __init__(self, x, y):
        super().__init__(x, y, "laser", None, color="cyan")
        self.init_laser_vars()

    def update(self, dt, enemy_group, bullet_group, tower_levels):
        super().update(dt, enemy_group, bullet_group, tower_levels)
        self.update_laser(dt)