import pygame

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


# SUBCLASES: Solo cambian los stats
class Arrow(Projectile):
    def __init__(self, start_pos, target_pos):
        super().__init__(start_pos, target_pos, speed=300.0, damage=5, size=6, color="black")


class Fireball(Projectile):
    def __init__(self, start_pos, target_pos):
        # Más lenta, pero mete un viaje atómico
        super().__init__(start_pos, target_pos, speed=150.0, damage=25, size=12, color="orange")