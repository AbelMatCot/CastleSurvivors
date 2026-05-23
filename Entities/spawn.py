import pygame
import random
# Importamos TODOS los enemigos ahora
from Entities.Enemies.enemies import Basic, Fast, Tank, Generator, Shooter, Flyer


class Spawn(pygame.sprite.Sprite):
    def __init__(self, spawn_x, spawn_y):
        super().__init__()
        self.spawn_x = spawn_x
        self.spawn_y = spawn_y

        self.image = pygame.Surface((30, 30), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self.rect.x = spawn_x
        self.rect.y = spawn_y

        self.timer = 0.0
        self.base_cooldown = 2.5  # Un poco más rápido que antes para mantener la presión

    def update(self, dt, enemy_group, grid, offset_x, grid_size,
               current_weight, population_cap, current_pool, cd_multiplier):

        self.timer += dt
        current_cd = self.base_cooldown * cd_multiplier

        if self.timer > current_cd:
            self.timer = 0.0

            # Si la pantalla ya está llena de amenaza, no spawneamos
            if current_weight >= population_cap:
                return

            px = offset_x + (self.spawn_x * grid_size) + (grid_size / 2)
            py = (self.spawn_y * grid_size) + (grid_size / 2)

            # Ruleta de la muerte según el minuto actual
            enemy_types = list(current_pool.keys())
            weights = list(current_pool.values())
            chosen_type = random.choices(enemy_types, weights=weights, k=1)[0]

            # Instanciamos el enemigo elegido
            if chosen_type == "Basic":
                new_enemy = Basic(px, py, grid_size, offset_x)
            elif chosen_type == "Fast":
                new_enemy = Fast(px, py, grid_size, offset_x)
            elif chosen_type == "Shooter":
                new_enemy = Shooter(px, py, grid_size, offset_x)
            elif chosen_type == "Tank":
                new_enemy = Tank(px, py, grid_size, offset_x)
            elif chosen_type == "Flyer":
                new_enemy = Flyer(px, py, grid_size, offset_x)
            elif chosen_type == "Generator":
                new_enemy = Generator(px, py, grid_size, offset_x)

            enemy_group.add(new_enemy)