import pygame

class Enemy(pygame.sprite.Sprite):
    def __init__(self, pixel_x, pixel_y):
        pygame.sprite.Sprite.__init__(self)

        self.image = pygame.Surface((16,16), pygame.SRCALPHA)

        #aspecto
        pygame.draw.circle(self.image, "red", (8,8), 8)

        self.rect = self.image.get_rect()

        #movimiento
        self.pos = pygame.math.Vector2(pixel_x, pixel_y)
        self.rect.center = (round(self.pos.x), round(self.pos.y))

        #stats
        self.speed = 1.5
        self.health = 10