import pygame
from Entities.Enemies.enemies import Basic  # <--- Importación nueva

class Spawn(pygame.sprite.Sprite):
    def __init__(self, spawn_x, spawn_y, border):
        super().__init__()
        self.spawn_x = spawn_x
        self.spawn_y = spawn_y
        self.border = border

        self.timer = 0.0
        self.spawn_cooldown = 3.0

    def update(self, dt, enemy_group, grid, offset_x, grid_size):
        self.timer += dt
        if self.timer > self.spawn_cooldown:
            self.timer = 0.0

            px = offset_x + (self.spawn_x * grid_size) + (grid_size / 2)
            py = (self.spawn_y * grid_size) + (grid_size / 2)

            # Instanciación directa y limpia sin rutas
            new_enemy = Basic(px, py, grid_size, offset_x)
            enemy_group.add(new_enemy)
            print("¡Enemigo instanciado!")