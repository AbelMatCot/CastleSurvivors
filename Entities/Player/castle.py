import pygame


# castle
class castle(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()

        self.image = pygame.image.load("Entities/Player/castle.png")

        self.image = pygame.transform.scale(self.image, (60,60))

        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
