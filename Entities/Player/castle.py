import pygame
from Entities.Player.towers import Tower, LaserMixin
from Entities.Player.projectiles import Arrow, Fireball, Kunai

class Castle(Tower):
    def __init__(self, x, y, cooldown, range_px, projectile_class, color="yellow"):
        # Hereda directamente de la clase base Tower con sus stats únicos
        super().__init__(x, y, cooldown, range_px, projectile_class, color)

        # Mantenemos el renderizado del bloque del Reino central
        self.image = pygame.Surface((60, 60))
        self.image.fill("yellow")

        self.rect = self.image.get_rect()
        self.rect.center = (x, y)

# --- SUBCLASES DE CASTILLOS CON TORRES INCORPORADAS ---
class ArrowCastle(Castle):
    def __init__(self, x, y):
        super().__init__(x, y, cooldown=0.8, range_px=120.0, projectile_class=Arrow)
        print("¡Castillo Flecha listo! Torres de flechas incorporadas nativamente.")

class FireballCastle(Castle):
    def __init__(self, x, y):
        super().__init__(x, y, cooldown=1.5, range_px=75.0, projectile_class=Fireball)
        print("¡Castillo Fuego listo! Torres de fuego incorporadas nativamente.")

class KunaiCastle(Castle):
    def __init__(self, x, y):
        super().__init__(x, y, cooldown=1.0, range_px=90.0, projectile_class=Kunai)
        print("¡Castillo Kunai listo! Torres de kunais incorporadas nativamente.")

class LaserCastle(Castle, LaserMixin):
    def __init__(self, x, y):
        # Asegúrate de poner aquí los valores de cooldown y rango que use tu castillo
        super().__init__(x, y, cooldown=0.2, range_px=100.0, projectile_class=None, color="cyan")
        self.init_laser_vars()

    def update(self, dt, enemy_group, bullet_group):
        super().update(dt, enemy_group, bullet_group)
        self.update_laser(dt)