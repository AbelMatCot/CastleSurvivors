import pygame
import os

fireball_img = None

class Projectile(pygame.sprite.Sprite):
    def __init__(self, start_pos, target_pos, speed, damage, size, color, pierce=1):
        super().__init__()
        self.size = size
        self.color = color
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(self.image, color, (size // 2, size // 2), size // 2)
        self.rect = self.image.get_rect()

        self.pos = pygame.math.Vector2(start_pos)
        self.rect.center = (round(self.pos.x), round(self.pos.y))

        self.speed = speed
        self.damage = damage
        self.pierce = pierce
        self.hit_enemies = set()  # Guarda los enemigos que ya ha atravesado

        direction = pygame.math.Vector2(target_pos) - self.pos
        self.dir = direction.normalize() if direction.length() > 0 else pygame.math.Vector2(1, 0)

    def update(self, dt):
        self.pos += self.dir * self.speed * dt
        self.rect.center = (round(self.pos.x), round(self.pos.y))
        if not (0 <= self.pos.x <= 1280 and 0 <= self.pos.y <= 720):
            self.kill()


# SUBCLASES
class Arrow(Projectile):
    def __init__(self, start_pos, target_pos):
        super().__init__(start_pos, target_pos, speed=300.0, damage=5, size=6, color="black", pierce=1)

class Fireball(Projectile):
    def __init__(self, start_pos, target_pos):
        super().__init__(start_pos, target_pos, speed=150.0, damage=10, size=12, color="orange", pierce=1)
        self.aoe_radius = 45

        global fireball_img
        if fireball_img is None:
            path = os.path.join("Assets", "Sprites", "Effects", "Explosion_01.png")
            sheet = pygame.image.load(path).convert_alpha()
            h = sheet.get_height()
            surf = pygame.Surface((h, h), pygame.SRCALPHA)
            surf.blit(sheet, (0, 0), (0, 0, h, h))
            fireball_img = pygame.transform.scale(surf, (24, 24))

        self.image = fireball_img
        self.rect = self.image.get_rect(center=self.rect.center)
        
class Kunai(Projectile):
    def __init__(self, start_pos, target_pos):
        super().__init__(start_pos, target_pos, speed=400.0, damage=7, size=4, color="gray", pierce=1)