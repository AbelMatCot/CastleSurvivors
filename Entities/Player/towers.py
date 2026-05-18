import pygame
from Entities.Player.projectiles import Arrow, Fireball


class Tower(pygame.sprite.Sprite):
    def __init__(self, x, y, cooldown, range_px, projectile_class):
        super().__init__()
        self.shoot_timer = 0.0
        self.shoot_cooldown = cooldown
        self.range = range_px
        self.projectile_class = projectile_class

        # Dibujo temporal (núcleo azul)
        self.image = pygame.Surface((30, 30), pygame.SRCALPHA)
        pygame.draw.circle(self.image, "blue", (15, 15), 10)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)

        # Posición
        self.x = x
        self.y = y

    def update(self, dt, enemy_group, bullet_group):
        self.shoot_timer += dt
        if self.shoot_timer >= self.shoot_cooldown:
            closest_enemy = None
            min_dist = float("inf")

            # El rango se calcula desde la torre
            tower_pos = pygame.math.Vector2(self.x, self.y)

            for enemy in enemy_group:
                dist = tower_pos.distance_to(enemy.pos)
                if dist < min_dist and dist <= self.range:
                    min_dist = dist
                    closest_enemy = enemy

            if closest_enemy:
                self.shoot_timer = 0.0
                new_bullet = self.projectile_class((self.x, self.y), closest_enemy.pos)
                bullet_group.add(new_bullet)


class ArrowTower(Tower):
    def __init__(self, x, y):
        super().__init__(x, y, cooldown=0.6, range_px=150.0, projectile_class=Arrow)


class FireballTower(Tower):
    def __init__(self, x, y):
        super().__init__(x, y, cooldown=1.5, range_px=200.0, projectile_class=Fireball)