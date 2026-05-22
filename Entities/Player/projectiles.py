import pygame
import os

fireball_imgs = {}

class Projectile(pygame.sprite.Sprite):
    def __init__(self, start_pos, target_pos, speed, size, color, stats):
        super().__init__()
        self.size = size
        self.color = color
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(self.image, color, (size // 2, size // 2), size // 2)
        self.rect = self.image.get_rect()

        self.pos = pygame.math.Vector2(start_pos)
        self.rect.center = (round(self.pos.x), round(self.pos.y))

        self.speed = speed
        self.damage = stats["damage"]
        self.pierce = stats["pierce"]
        if stats.get("area", 0) > 0:
            self.aoe_radius = stats["area"]

        self.hit_enemies = set()

        direction = pygame.math.Vector2(target_pos) - self.pos
        self.dir = direction.normalize() if direction.length() > 0 else pygame.math.Vector2(1, 0)

    def update(self, dt):
        self.pos += self.dir * self.speed * dt
        self.rect.center = (round(self.pos.x), round(self.pos.y))
        if not (0 <= self.pos.x <= 1280 and 0 <= self.pos.y <= 720):
            self.kill()


class Arrow(Projectile):
    def __init__(self, start_pos, target_pos, stats):
        super().__init__(start_pos, target_pos, speed=300.0, size=6, color="black", stats=stats)


class Fireball(Projectile):
    def __init__(self, start_pos, target_pos, stats):
        super().__init__(start_pos, target_pos, speed=150.0, size=12, color="orange", stats=stats)

        self.aoe_radius = stats.get("area", 10) * 2.5
        size_px = int(self.aoe_radius * 3.5)

        global fireball_imgs
        radius_key = self.aoe_radius

        if radius_key not in fireball_imgs:
            path = os.path.join("Assets", "Sprites", "Effects", "Explosion_01.png")
            sheet = pygame.image.load(path).convert_alpha()
            h = sheet.get_height()

            surf = pygame.Surface((h, h), pygame.SRCALPHA)
            surf.blit(sheet, (0, 0), (0, 0, h, h))

            # Recortamos la transparencia para que la hitbox sea exacta a la bola
            tight_rect = surf.get_bounding_rect()
            tight_surf = surf.subsurface(tight_rect)

            # Mantenemos la proporción visual escalando solo la parte visible
            scale_factor = size_px / h
            new_w = int(tight_rect.width * scale_factor)
            new_h = int(tight_rect.height * scale_factor)

            fireball_imgs[radius_key] = pygame.transform.scale(tight_surf, (max(1, new_w), max(1, new_h)))

        self.image = fireball_imgs[radius_key]
        self.rect = self.image.get_rect(center=self.rect.center)


class Kunai(Projectile):
    def __init__(self, start_pos, target_pos, stats):
        super().__init__(start_pos, target_pos, speed=400.0, size=4, color="gray", stats=stats)