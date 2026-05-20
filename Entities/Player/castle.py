import pygame
from Entities.Player.towers import ArrowTower


class Castle(ArrowTower):
    def __init__(self, x, y):
        # Llamamos al constructor de ArrowTower (rango 150, cooldown 0.6)
        super().__init__(x, y)

        # Sobrescribimos el dibujo temporal para que sea el REINO (bloque amarillo grande)
        self.image = pygame.Surface((60, 60))
        self.image.fill("yellow")

        self.rect = self.image.get_rect()
        self.rect.center = (x, y)