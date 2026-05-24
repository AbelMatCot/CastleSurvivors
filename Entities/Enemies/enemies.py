import pygame
import random


class Enemy(pygame.sprite.Sprite):
    def __init__(self, pixel_x, pixel_y, grid_size, offset_x, health, speed, color, radius, xp_value, gold_value, base_damage):
        pygame.sprite.Sprite.__init__(self)
        self.base_damage = base_damage
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
        self.base_speed = speed
        self.slow_timer = 0.0
        self.health = health

        self.grid_size = grid_size
        self.offset_x = offset_x

        # Añadimos las torres (8) a los objetivos
        self.target_cells = (2, 3, 8)

        # --- AUTO-DETECCIÓN DE TÚNEL ARREGLADA ---
        # Usamos directamente las variables locales offset_x y grid_size
        grid_x_start = (self.pos.x - offset_x) / grid_size
        grid_y_start = self.pos.y / grid_size

        # Los enemigos nacen en el centro de la casilla (0.5 o 23.5)
        # Comprobamos con margen de 1.0 para que no falle la detección
        if grid_y_start < 1.0:
            self.tunnel_dir = pygame.math.Vector2(0, 1)  # Viene del Norte
        elif grid_y_start > 22.0:
            self.tunnel_dir = pygame.math.Vector2(0, -1)  # Viene del Sur
        elif grid_x_start < 1.0:
            self.tunnel_dir = pygame.math.Vector2(1, 0)  # Viene del Oeste
        else:
            self.tunnel_dir = pygame.math.Vector2(-1, 0)  # Viene del Este

        self.attack_timer = 0.0
        self.attack_cooldown = 1.0
        self.wall_damage_counter = 0

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

    def apply_slow(self, factor, duration):
        self.speed = self.base_speed * factor
        self.slow_timer = duration

    def update(self, dt, grid, enemy_group=None, structures_hp=None, passive_levels=None, thorns_values=None):

        if self.slow_timer > 0:
            self.slow_timer -= dt
            if self.slow_timer <= 0:
                self.speed = self.base_speed

        # 1. Control del parpadeo
        if self.is_flashing:
            self.flash_timer -= dt
            if self.flash_timer <= 0:
                self.is_flashing = False
                self.image.fill((0, 0, 0, 0))
                pygame.draw.circle(self.image, self.base_color, (self.radius, self.radius), self.radius)

        # 2. DIRECCIÓN (Lógica de Túnel + Centro)
        margin = 1
        grid_x_exact = (self.pos.x - self.offset_x) / self.grid_size
        grid_y_exact = self.pos.y / self.grid_size

        # Forzamos la dirección del túnel hasta que estén medio bloque dentro
        if self.tunnel_dir.y == 1 and grid_y_exact < margin + 0.5:
            self.dir_norm = self.tunnel_dir
        elif self.tunnel_dir.y == -1 and grid_y_exact > 24 - margin - 0.5:
            self.dir_norm = self.tunnel_dir
        elif self.tunnel_dir.x == 1 and grid_x_exact < margin + 0.5:
            self.dir_norm = self.tunnel_dir
        elif self.tunnel_dir.x == -1 and grid_x_exact > 24 - margin - 0.5:
            self.dir_norm = self.tunnel_dir
        else:
            # Una vez están a salvo, a por el castillo
            center_vec = pygame.math.Vector2(640, 360)
            direction = center_vec - self.pos
            if direction.length() != 0:
                self.dir_norm = direction.normalize()
            else:
                self.dir_norm = pygame.math.Vector2(0, 0)

        # 3. DETECTAR SI ESTÁ TOCANDO OBSTÁCULO Y DAÑAR ESTRUCTURAS
        check_pos = self.pos + self.dir_norm * (self.radius + 4)
        grid_x = int((check_pos.x - self.offset_x) // self.grid_size)
        grid_y = int(check_pos.y // self.grid_size)

        self.is_attacking = False
        if 0 <= grid_x < 24 and 0 <= grid_y < 24:
            cell = grid[grid_y][grid_x]
            if cell in self.target_cells:
                self.is_attacking = True
                self.attack_timer += dt
                if self.attack_timer >= self.attack_cooldown:
                    self.attack_timer = 0.0

                    # --- PASIVAS: Armadura ---
                    armor_lvl = passive_levels.get("armor", 0) if passive_levels else 0
                    damage_reduction = 1.0 - (armor_lvl * 0.05)
                    final_damage = max(1, int(self.base_damage * damage_reduction))

                    if cell in (2, 8) and structures_hp is not None:
                        coords = (grid_y, grid_x)
                        if coords in structures_hp:
                            structures_hp[coords] -= final_damage
                            if structures_hp[coords] <= 0:
                                grid[grid_y][grid_x] = 0  # Se destruye el muro/torre
                                del structures_hp[coords]

                    elif cell == 3:
                        # Aquí luego habrá que restar la vida al castillo en main.py
                        print(f"¡El castillo sufre {final_damage} de daño!")

                    # --- PASIVAS: Espinas ---
                    thorns_lvl = passive_levels.get("thorns", 0) if passive_levels else 0
                    if thorns_lvl > 0 and thorns_values:
                        self.take_damage(thorns_values[thorns_lvl])

        # 4. AVANZAR
        if not self.is_attacking:
            self.pos += self.dir_norm * self.speed * dt

        self.rect.center = (round(self.pos.x), round(self.pos.y))


# SUBCLASES DE ENEMIGOS

class Basic(Enemy):
    def __init__(self, pixel_x, pixel_y, grid_size, offset_x):
        # 15 HP: 3 flechas/kunais, 2 bolas de fuego o 3s de láser
        super().__init__(pixel_x, pixel_y, grid_size, offset_x, health=15, speed=30.0, color="red", radius=8, xp_value=3, gold_value=2, base_damage=10)

class Fast(Enemy):
    def __init__(self, pixel_x, pixel_y, grid_size, offset_x):
        # 6 HP: Cae de 2 flechas o 1 bola de fuego, pero va como una bala
        super().__init__(pixel_x, pixel_y, grid_size, offset_x, health=6, speed=60.0, color="green", radius=6, xp_value=2, gold_value=1, base_damage=15)

class Tank(Enemy):
    def __init__(self, pixel_x, pixel_y, grid_size, offset_x):
        # 45 HP: El triple de vida, aguanta 9 flechas
        super().__init__(pixel_x, pixel_y, grid_size, offset_x, health=45, speed=15.0, color="blue", radius=14, xp_value=15, gold_value=8, base_damage=30)


class Generator(Enemy):
    def __init__(self, pixel_x, pixel_y, grid_size, offset_x):
        # 60 HP: Esponja de daño lenta que hay que priorizar
        super().__init__(pixel_x, pixel_y, grid_size, offset_x, health=60, speed=10.0, color="purple", radius=16,
                         xp_value=25, gold_value=15, base_damage=5)
        self.spawn_timer = 0.0
        self.my_swarmers = []  # Lista para controlar a sus crías

    def update(self, dt, grid, enemy_group=None, structures_hp=None, passive_levels=None, thorns_values=None):
        super().update(dt, grid, enemy_group, structures_hp, passive_levels, thorns_values)

        if enemy_group is not None:
            # Limpiamos la lista quitando los swarmers que ya han muerto
            self.my_swarmers = [s for s in self.my_swarmers if s.alive()]

            self.spawn_timer += dt

            if self.spawn_timer >= 4.0:
                # Solo escupe si tiene menos de 5 huérfanos vivos
                if len(self.my_swarmers) < 5:
                    self.spawn_timer = 0.0  # Reseteamos el timer solo si consigue parir

                    for _ in range(3):
                        offset_x = self.pos.x + random.uniform(-10, 10)
                        offset_y = self.pos.y + random.uniform(-10, 10)

                        swarmer = Swarmer(offset_x, offset_y, self.grid_size, self.offset_x)
                        enemy_group.add(swarmer)
                        self.my_swarmers.append(swarmer)  # Lo metemos en la guardería

class Swarmer(Enemy):
    def __init__(self, pixel_x, pixel_y, grid_size, offset_x):
        # 2 HP: Muere de una sola caricia de cualquier torre
        super().__init__(pixel_x, pixel_y, grid_size, offset_x, health=3, speed=75.0, color="pink", radius=4, xp_value=0, gold_value=0, base_damage=3)

class Shooter(Enemy):
    def __init__(self, pixel_x, pixel_y, grid_size, offset_x):
        super().__init__(pixel_x, pixel_y, grid_size, offset_x, health=12, speed=30.0, color="cyan", radius=8, xp_value=4, gold_value=3, base_damage=10)

class Flyer(Enemy):
    def __init__(self, pixel_x, pixel_y, grid_size, offset_x):
        super().__init__(pixel_x, pixel_y, grid_size, offset_x, health=10, speed=40.0, color="yellow", radius=8, xp_value=3, gold_value=2, base_damage=15)
        self.target_cells = (3,)

class Boss(Enemy):
    def __init__(self, pixel_x, pixel_y, grid_size, offset_x):
        # 100 HP: Un verdadero dolor de muelas para el late-game
        super().__init__(pixel_x, pixel_y, grid_size, offset_x, health=100, speed=30.0, color="magenta", radius=28, xp_value=30, gold_value=100, base_damage=50)