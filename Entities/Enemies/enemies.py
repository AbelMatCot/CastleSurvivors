import pygame
import random


class Enemy(pygame.sprite.Sprite):
    def __init__(self, pixel_x, pixel_y, grid_size, offset_x, health, speed, color, radius, xp_value, gold_value):
        pygame.sprite.Sprite.__init__(self)
        self.radius = radius
        self.base_color = color

        self.gold_value = gold_value
        self.xp_value = xp_value

        self.image = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, color, (radius, radius), radius)
        self.rect = self.image.get_rect()

        self.pos = pygame.math.Vector2(pixel_x, pixel_y)
        self.rect.center = (round(self.pos.x), round(self.pos.y))

        self.speed = speed
        self.health = health

        self.attack_timer = 0.0
        self.attack_cooldown = 1.0
        self.wall_damage_counter = 0

        self.grid_size = grid_size
        self.offset_x = offset_x

        # Temporizador para el flash de daño
        self.flash_timer = 0.0
        self.is_flashing = False

        # Variables públicas para que main.py pueda calcular los empujones
        self.is_attacking = False
        self.dir_norm = pygame.math.Vector2(1, 0)

    def take_damage(self, amount):
        self.health -= amount
        self.is_flashing = True
        self.flash_timer = 0.1  # Duración del parpadeo
        self.image.fill((0, 0, 0, 0))
        pygame.draw.circle(self.image, "white", (self.radius, self.radius), self.radius)

    def update(self, dt, grid):
        # Control del parpadeo
        if self.is_flashing:
            self.flash_timer -= dt
            if self.flash_timer <= 0:
                self.is_flashing = False
                self.image.fill((0, 0, 0, 0))
                pygame.draw.circle(self.image, self.base_color, (self.radius, self.radius), self.radius)

        # 1. DIRECCIÓN AL CENTRO (Castillo: 640, 360)
        center_vec = pygame.math.Vector2(640, 360)
        direction = center_vec - self.pos

        if direction.length() == 0:
            return

        self.dir_norm = direction.normalize()

        # 2. DETECTAR SI ESTÁ TOCANDO OBSTÁCULO (Muro o Castillo)
        check_pos = self.pos + self.dir_norm * (self.radius + 4)
        grid_x = int((check_pos.x - self.offset_x) // self.grid_size)
        grid_y = int(check_pos.y // self.grid_size)

        self.is_attacking = False
        if 0 <= grid_x < 24 and 0 <= grid_y < 24:
            cell = grid[grid_y][grid_x]
            if cell in (2, 3):
                self.is_attacking = True
                self.attack_timer += dt
                if self.attack_timer >= self.attack_cooldown:
                    self.attack_timer = 0.0
                    if cell == 2:
                        self.wall_damage_counter += 1
                        if self.wall_damage_counter >= 3:
                            grid[grid_y][grid_x] = 0
                            self.wall_damage_counter = 0
                    elif cell == 3:
                        print("¡El castillo está sufriendo daños!")

        # 3. AVANZAR (El empuje se calcula ahora de forma global y eficiente en main.py)
        if not self.is_attacking:
            self.pos += self.dir_norm * self.speed * dt

        self.rect.center = (round(self.pos.x), round(self.pos.y))


# SUBCLASES DE ENEMIGOS

class Basic(Enemy):
    def __init__(self, pixel_x, pixel_y, grid_size, offset_x):
        super().__init__(pixel_x, pixel_y, grid_size, offset_x, 10, 60.0, "red", 8, gold_value=2, xp_value=5)

class Fast(Enemy):
    def __init__(self, pixel_x, pixel_y, grid_size, offset_x):
        super().__init__(pixel_x, pixel_y, grid_size, offset_x, 5, 120.0, "green", 6, gold_value=3, xp_value=8)

class Tank(Enemy):
    def __init__(self, pixel_x, pixel_y, grid_size, offset_x):
        super().__init__(pixel_x, pixel_y, grid_size, offset_x, 40, 30.0, "blue", 14, gold_value=10, xp_value=25)