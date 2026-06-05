import pygame
import random
import os

basic_sheet = None
fast_sheet = None
tank_sheet = None
flyer_sheet = None
generator_sheet = None
swarmer_sheet = None
shooter_sheet = None
shooter_fx_sheet = None
boss_sheet = None

def get_enemy_frames(sheet, row, num_frames, scale=1.0):
    frames = []
    for i in range(num_frames):
        frame = pygame.Surface((24, 24), pygame.SRCALPHA)
        frame.blit(sheet, (0, 0), (i * 32 + 4, row * 32 + 8, 24, 24))
        if scale != 1.0:
            new_size = int(24 * scale)
            frame = pygame.transform.scale(frame, (new_size, new_size))
        frames.append(frame)
    return frames

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

        self.target_cells = (2, 3, 8)

        # --- AUTO-DETECCIÓN DE TÚNEL ---
        grid_x_start = (self.pos.x - offset_x) / grid_size
        grid_y_start = self.pos.y / grid_size

        if grid_y_start < 1.0:
            self.tunnel_dir = pygame.math.Vector2(0, 1)
        elif grid_y_start > 22.0:
            self.tunnel_dir = pygame.math.Vector2(0, -1)
        elif grid_x_start < 1.0:
            self.tunnel_dir = pygame.math.Vector2(1, 0)
        else:
            self.tunnel_dir = pygame.math.Vector2(-1, 0)

        self.attack_timer = 0.0
        self.attack_cooldown = 1.0
        self.wall_damage_counter = 0

        self.flash_timer = 0.0
        self.is_flashing = False

        self.is_attacking = False
        self.dir_norm = pygame.math.Vector2(1, 0)

        self.state = "walk"
        self.current_frame = 0
        self.anim_timer = 0.0
        self.facing_right = True
        self.is_dying = False

    def take_damage(self, amount):
        if getattr(self, "is_dying", False) or getattr(self, "is_untargetable", False):
            return
        self.health -= amount
        self.is_flashing = True
        self.flash_timer = 0.1

    def apply_slow(self, factor, duration):
        self.speed = self.base_speed * factor
        self.slow_timer = duration

    def update(self, dt, grid, enemy_group=None, effects_group=None, structures_hp=None, passive_levels=None, thorns_values=None):

        if self.slow_timer > 0:
            self.slow_timer -= dt
            if self.slow_timer <= 0:
                self.speed = self.base_speed

        # 1. SI ESTÁ MURIENDO (Lógica global de muerte)
        if self.is_dying:
            if hasattr(self, "animations") and "death" in self.animations:
                self.anim_timer += dt
                if self.anim_timer >= 0.1:
                    self.anim_timer = 0.0
                    self.current_frame += 1

                if self.current_frame < len(self.animations["death"]):
                    frame_img = self.animations["death"][self.current_frame]
                    if not self.facing_right:
                        frame_img = pygame.transform.flip(frame_img, True, False)
                    self.image = frame_img.copy()

                    if self.is_flashing:
                        self.flash_timer -= dt
                        if self.flash_timer > 0:
                            self.image.fill((150, 150, 150), special_flags=pygame.BLEND_RGB_ADD)
                        else:
                            self.is_flashing = False
                else:
                    self.kill()
            else:
                self.kill()
            return

        # 2. DIRECCIÓN Y MOVIMIENTO BÁSICO
        margin = 1
        grid_x_exact = (self.pos.x - self.offset_x) / self.grid_size
        grid_y_exact = self.pos.y / self.grid_size

        if self.tunnel_dir.y == 1 and grid_y_exact < margin + 0.5:
            self.dir_norm = self.tunnel_dir
        elif self.tunnel_dir.y == -1 and grid_y_exact > 24 - margin - 0.5:
            self.dir_norm = self.tunnel_dir
        elif self.tunnel_dir.x == 1 and grid_x_exact < margin + 0.5:
            self.dir_norm = self.tunnel_dir
        elif self.tunnel_dir.x == -1 and grid_x_exact > 24 - margin - 0.5:
            self.dir_norm = self.tunnel_dir
        else:
            center_vec = pygame.math.Vector2(640, 360)
            direction = center_vec - self.pos
            if direction.length() != 0:
                self.dir_norm = direction.normalize()
            else:
                self.dir_norm = pygame.math.Vector2(0, 0)

        # 3. DETECTAR OBSTÁCULOS
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
                    armor_lvl = passive_levels.get("armor", 0) if passive_levels else 0
                    damage_reduction = 1.0 - (armor_lvl * 0.05)
                    final_damage = max(1, int(self.base_damage * damage_reduction))

                    if cell in (2, 8) and structures_hp is not None:
                        coords = (grid_y, grid_x)
                        if coords in structures_hp:
                            structures_hp[coords] -= final_damage
                            if structures_hp[coords] <= 0:
                                grid[grid_y][grid_x] = 0
                                del structures_hp[coords]
                    elif cell == 3:
                        pass

                    thorns_lvl = passive_levels.get("thorns", 0) if passive_levels else 0
                    if thorns_lvl > 0 and thorns_values:
                        self.take_damage(thorns_values[thorns_lvl])

        if not self.is_attacking:
            self.pos += self.dir_norm * self.speed * dt

        # 4. MÁQUINA DE ESTADOS VISUAL
        if self.dir_norm.x > 0.1:
            self.facing_right = True
        elif self.dir_norm.x < -0.1:
            self.facing_right = False

        new_state = getattr(self, "custom_state", "attack" if self.is_attacking else "walk")

        if self.state != new_state:
            self.state = new_state
            self.current_frame = 0

        # 5. RENDERIZADO VISUAL
        if hasattr(self, "animations") and self.state in self.animations:
            self.anim_timer += dt
            if self.anim_timer >= 0.1:
                self.anim_timer = 0.0
                self.current_frame = (self.current_frame + 1) % len(self.animations[self.state])

            frame_img = self.animations[self.state][self.current_frame]
            if not self.facing_right:
                frame_img = pygame.transform.flip(frame_img, True, False)
            self.image = frame_img.copy()

            self.rect = self.image.get_rect()

            if self.is_flashing:
                self.flash_timer -= dt
                if self.flash_timer > 0:
                    self.image.fill((150, 150, 150), special_flags=pygame.BLEND_RGB_ADD)
                else:
                    self.is_flashing = False
        else:
            if self.is_flashing:
                self.flash_timer -= dt
                if self.flash_timer > 0:
                    self.image.fill((0, 0, 0, 0))
                    pygame.draw.circle(self.image, "white", (self.radius, self.radius), self.radius)
                else:
                    self.is_flashing = False
                    self.image.fill((0, 0, 0, 0))
                    pygame.draw.circle(self.image, self.base_color, (self.radius, self.radius), self.radius)

        self.rect.center = (round(self.pos.x), round(self.pos.y))


class Basic(Enemy):
    def __init__(self, pixel_x, pixel_y, grid_size, offset_x):
        super().__init__(pixel_x, pixel_y, grid_size, offset_x, health=15, speed=30.0, color="red", radius=8,
                         xp_value=3, gold_value=2, base_damage=10)

        global basic_sheet
        if basic_sheet is None:
            basic_sheet = pygame.image.load(os.path.join("Assets", "Sprites", "Enemies", "basic.png")).convert_alpha()

        self.animations = {
            "walk": get_enemy_frames(basic_sheet, 1, 8),
            "attack": get_enemy_frames(basic_sheet, 2, 6),
            "death": get_enemy_frames(basic_sheet, 5, 5)
        }
        self.image = self.animations[self.state][self.current_frame]

class Fast(Enemy):
    def __init__(self, pixel_x, pixel_y, grid_size, offset_x):
        super().__init__(pixel_x, pixel_y, grid_size, offset_x, health=6, speed=60.0, color="green", radius=6,
                         xp_value=2, gold_value=1, base_damage=15)

        global fast_sheet
        if fast_sheet is None:
            fast_sheet = pygame.image.load(os.path.join("Assets", "Sprites", "Enemies", "fast.png")).convert_alpha()

        self.animations = {
            "walk": get_enemy_frames(fast_sheet, 1, 8),
            "attack": get_enemy_frames(fast_sheet, 2, 4),
            "death": get_enemy_frames(fast_sheet, 5, 8)
        }
        self.image = self.animations[self.state][self.current_frame]

class Tank(Enemy):
    def __init__(self, pixel_x, pixel_y, grid_size, offset_x):
        super().__init__(pixel_x, pixel_y, grid_size, offset_x, health=45, speed=15.0, color="blue", radius=14,
                         xp_value=15, gold_value=8, base_damage=30)

        global tank_sheet
        if tank_sheet is None:
            tank_sheet = pygame.image.load(os.path.join("Assets", "Sprites", "Enemies", "tank.png")).convert_alpha()

        self.animations = {
            "walk": get_enemy_frames(tank_sheet, 1, 8),
            "attack": get_enemy_frames(tank_sheet, 2, 6),
            "death": get_enemy_frames(tank_sheet, 4, 6)
        }
        self.image = self.animations[self.state][self.current_frame]

class Flyer(Enemy):
    def __init__(self, pixel_x, pixel_y, grid_size, offset_x):
        super().__init__(pixel_x, pixel_y, grid_size, offset_x, health=10, speed=40.0, color="yellow", radius=8,
                         xp_value=3, gold_value=2, base_damage=15)
        self.target_cells = (3,)

        global flyer_sheet
        if flyer_sheet is None:
            flyer_sheet = pygame.image.load(os.path.join("Assets", "Sprites", "Enemies", "flyer.png")).convert_alpha()

        self.animations = {
            "walk": get_enemy_frames(flyer_sheet, 0, 4),
            "attack": get_enemy_frames(flyer_sheet, 2, 4),
            "death": get_enemy_frames(flyer_sheet, 3, 6)
        }
        self.image = self.animations[self.state][self.current_frame]

class AttachedLeaf(pygame.sprite.Sprite):
    def __init__(self, trent):
        super().__init__()
        self.trent = trent
        self.scale = 0.0

        global swarmer_sheet
        if swarmer_sheet is None:
            swarmer_sheet = pygame.image.load(os.path.join("Assets", "Sprites", "Enemies", "swarmer.png")).convert_alpha()

        self.base_img = get_enemy_frames(swarmer_sheet, 0, 1)[0]
        self.image = pygame.Surface((1, 1), pygame.SRCALPHA)
        self.rect = self.image.get_rect()

    def update(self, dt):
        if not self.trent.alive() or getattr(self.trent, "is_dying", False):
            self.kill()
            return

        self.scale = min(1.0, self.scale + dt * 1.4)
        size = max(1, int(24 * self.scale))

        img = pygame.transform.scale(self.base_img, (size, size))
        if not self.trent.facing_right:
            img = pygame.transform.flip(img, True, False)

        self.image = img
        self.rect = self.image.get_rect(midbottom=self.rect.midbottom)
        self.y_sort = self.trent.rect.bottom + 1

class Swarmer(Enemy):
    def __init__(self, pixel_x, pixel_y, grid_size, offset_x, fall_start_pos=None):
        super().__init__(pixel_x, pixel_y, grid_size, offset_x, health=3, speed=75.0, color="pink", radius=4,
                         xp_value=0, gold_value=0, base_damage=3)

        global swarmer_sheet
        if swarmer_sheet is None:
            swarmer_sheet = pygame.image.load(os.path.join("Assets", "Sprites", "Enemies", "swarmer.png")).convert_alpha()

        self.animations = {
            "idle": get_enemy_frames(swarmer_sheet, 0, 4),
            "walk": get_enemy_frames(swarmer_sheet, 1, 4),
            "attack": get_enemy_frames(swarmer_sheet, 5, 4),
            "death": get_enemy_frames(swarmer_sheet, 4, 6)
        }

        if fall_start_pos:
            self.pos = pygame.math.Vector2(fall_start_pos)
            self.ground_y = pixel_y
            self.is_falling = True
            self.is_untargetable = True
            self.custom_state = "idle"
        else:
            self.is_falling = False
            self.is_untargetable = False
            self.custom_state = "walk"

        self.image = self.animations[getattr(self, "custom_state", "walk")][self.current_frame]

    def update(self, dt, grid, enemy_group=None, effects_group=None, structures_hp=None, passive_levels=None, thorns_values=None):
        if getattr(self, "is_falling", False):
            self.pos.y += 50.0 * dt

            self.anim_timer += dt
            if self.anim_timer >= 0.1:
                self.anim_timer = 0.0
                self.current_frame = (self.current_frame + 1) % len(self.animations["idle"])

            frame_img = self.animations["idle"][self.current_frame]
            if not self.facing_right:
                frame_img = pygame.transform.flip(frame_img, True, False)
            self.image = frame_img.copy()

            self.rect = self.image.get_rect()
            self.rect.center = (round(self.pos.x), round(self.pos.y))

            if self.pos.y >= self.ground_y:
                self.is_falling = False
                self.is_untargetable = False
                self.custom_state = "walk"
                if hasattr(self, "y_sort"): del self.y_sort
            return

        super().update(dt, grid, enemy_group, effects_group, structures_hp, passive_levels, thorns_values)


class Generator(Enemy):
    def __init__(self, pixel_x, pixel_y, grid_size, offset_x):
        super().__init__(pixel_x, pixel_y, grid_size, offset_x, health=60, speed=25.0, color="purple", radius=16,
                         xp_value=25, gold_value=15, base_damage=5)

        self.my_leaves = []
        self.spawn_timer = 0.0
        self.jump_cooldown = 1.2
        self.is_waiting = True

        global generator_sheet
        if generator_sheet is None:
            generator_sheet = pygame.image.load(os.path.join("Assets", "Sprites", "Enemies", "generator.png")).convert_alpha()

        self.animations = {
            "walk": get_enemy_frames(generator_sheet, 1, 8, scale=2.0),
            "attack": get_enemy_frames(generator_sheet, 2, 6, scale=2.0),
            "idle_spawn": get_enemy_frames(generator_sheet, 3, 4, scale=2.0),
            "death": get_enemy_frames(generator_sheet, 4, 8, scale=2.0)
        }

        self.image = self.animations[self.state][self.current_frame]

    def update(self, dt, grid, enemy_group=None, effects_group=None, structures_hp=None, passive_levels=None, thorns_values=None):
        min_dist = float("inf")
        if structures_hp:
            for (r, c) in structures_hp.keys():
                struct_pos = pygame.math.Vector2(self.offset_x + c * self.grid_size + self.grid_size / 2,
                                                 r * self.grid_size + self.grid_size / 2)
                d = self.pos.distance_to(struct_pos)
                if d < min_dist: min_dist = d

        in_dash = (self.state in ["walk", "idle_spawn"]) and (self.current_frame in [1, 2, 3, 5, 6, 7])

        if min_dist <= 80 and not in_dash:
            self.custom_state = "attack" if self.is_attacking else "idle_spawn"
        else:
            self.custom_state = "walk"

        if self.state in ["walk", "idle_spawn"] and self.current_frame in [0, 4]:
            self.is_waiting = True
        else:
            self.is_waiting = False

        if self.is_waiting:
            self.speed = 0.0
            self.spawn_timer += dt
            if self.spawn_timer >= self.jump_cooldown:
                self.spawn_timer = 0.0
                self.anim_timer = 0.1
            else:
                self.anim_timer = -dt
        else:
            self.speed = 35.0
            self.anim_timer -= dt * 0.65

        old_frame = self.current_frame
        super().update(dt, grid, enemy_group, effects_group, structures_hp, passive_levels, thorns_values)
        new_frame = self.current_frame

        if self.state in ["walk", "idle_spawn"] and not getattr(self, "is_dying", False):
            is_jump_start = (new_frame in [1, 5] and old_frame not in [1, 5])
            is_landing = (new_frame in [0, 4] and old_frame not in [0, 4])

            if is_jump_start and len(self.my_leaves) == 0:
                for _ in range(3):
                    leaf = AttachedLeaf(self)
                    if effects_group is not None:
                        effects_group.add(leaf)
                    self.my_leaves.append(leaf)

            if len(self.my_leaves) > 0:
                offsets = [(-8, 2), (0, -2), (8, 0)]
                for i, leaf in enumerate(self.my_leaves):
                    ox, oy = offsets[i]
                    if not self.facing_right:
                        ox = -ox

                    shift_y = 0
                    if self.current_frame in [1, 2, 3, 5, 6, 7]:
                        shift_y = -6

                    final_x = self.pos.x + ox
                    final_y = self.pos.y + oy + shift_y

                    leaf.rect.midbottom = (round(final_x), round(final_y))

            if is_landing and len(self.my_leaves) > 0:
                for leaf in self.my_leaves:
                    leaf.kill()
                    sx = leaf.rect.centerx
                    sy = leaf.rect.centery
                    gx = self.pos.x + random.uniform(-10, 10)
                    gy = self.pos.y + random.uniform(5, 15)
                    swarmer = Swarmer(gx, gy, self.grid_size, self.offset_x, fall_start_pos=(sx, sy))

                    swarmer.facing_right = self.facing_right
                    swarmer.y_sort = self.rect.bottom + 1

                    if enemy_group is not None:
                        enemy_group.add(swarmer)
                self.my_leaves.clear()


class MuzzleFlashEffect(pygame.sprite.Sprite):
    def __init__(self, x, y, flip):
        super().__init__()
        global shooter_sheet

        # Extraemos los 32x32 píxeles enteros de la fila 6 (índice 5)
        self.frames = []
        for i in range(4):
            frame = pygame.Surface((32, 32), pygame.SRCALPHA)
            frame.blit(shooter_sheet, (0, 0), (i * 32, 5 * 32, 32, 32))
            if flip:
                frame = pygame.transform.flip(frame, True, False)
            self.frames.append(frame)

        self.current_frame = 0
        self.anim_timer = 0.0
        self.image = self.frames[0]
        self.rect = self.image.get_rect(center=(x, y))

    def update(self, dt):
        self.anim_timer += dt
        if self.anim_timer >= 0.08:
            self.anim_timer = 0.0
            self.current_frame += 1
            if self.current_frame < len(self.frames):
                self.image = self.frames[self.current_frame]
            else:
                self.kill()


class TargetHitEffect(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        global shooter_fx_sheet

        w = shooter_fx_sheet.get_width() // 6
        h = shooter_fx_sheet.get_height()

        self.frames = []
        for i in range(6):
            frame = pygame.Surface((w, h), pygame.SRCALPHA)
            # CORREGIDO: Ya usa su propia sprite sheet
            frame.blit(shooter_fx_sheet, (0, 0), (i * w, 0, w, h))
            # Ajustado a 20x20 píxeles fijos para que no sea gigantesco
            frame = pygame.transform.scale(frame, (20, 20))
            self.frames.append(frame)

        self.current_frame = 0
        self.anim_timer = 0.0
        self.image = self.frames[0]
        self.rect = self.image.get_rect(center=(x, y))

    def update(self, dt):
        self.anim_timer += dt
        if self.anim_timer >= 0.08:
            self.anim_timer = 0.0
            self.current_frame += 1
            if self.current_frame < len(self.frames):
                self.image = self.frames[self.current_frame]
            else:
                self.kill()


class Shooter(Enemy):
    def __init__(self, pixel_x, pixel_y, grid_size, offset_x):
        super().__init__(pixel_x, pixel_y, grid_size, offset_x, health=12, speed=30.0,
                         color="cyan", radius=8, xp_value=4, gold_value=3, base_damage=10)

        self.range = 60
        self.attack_cooldown = 1.2
        self.shot_castle = 0
        self.target_cells = ()
        self.has_shot_this_cycle = False

        global shooter_sheet, shooter_fx_sheet
        if shooter_sheet is None:
            shooter_sheet = pygame.image.load(
                os.path.join("Assets", "Sprites", "Enemies", "shooter.png")).convert_alpha()
        if shooter_fx_sheet is None:
            shooter_fx_sheet = pygame.image.load(
                os.path.join("Assets", "Sprites", "Enemies", "shooter_fx.png")).convert_alpha()

        self.animations = {
            "idle": get_enemy_frames(shooter_sheet, 0, 4),  # NUEVO: Cargamos la fila 0
            "walk": get_enemy_frames(shooter_sheet, 1, 8),
            "attack": get_enemy_frames(shooter_sheet, 2, 6),
            "death": get_enemy_frames(shooter_sheet, 4, 6)
        }
        self.image = self.animations["walk"][0]

    def update(self, dt, grid, enemy_group=None, effects_group=None, structures_hp=None, passive_levels=None,
               thorns_values=None):
        if getattr(self, "is_dying", False):
            super().update(dt, grid, enemy_group, effects_group, structures_hp, passive_levels, thorns_values)
            return

        target_pos = None
        target_coords = None
        is_castle_target = False

        castle_center = pygame.math.Vector2(640, 360)
        if self.pos.distance_to(castle_center) <= self.range:
            target_pos = castle_center
            is_castle_target = True

        if not target_pos and structures_hp:
            for (r, c) in structures_hp.keys():
                s_pos = pygame.math.Vector2(self.offset_x + c * self.grid_size + 15, r * self.grid_size + 15)
                if self.pos.distance_to(s_pos) <= self.range:
                    target_pos = s_pos
                    target_coords = (r, c)
                    break

        old_pos = pygame.math.Vector2(self.pos)

        if target_pos:
            dir_vec = target_pos - self.pos
            if dir_vec.length() > 0:
                self.dir_norm = dir_vec.normalize()

            self.attack_timer += dt

            # MAGIA DEL TIMING: Si falta medio segundo para el ataque, iniciamos la animación.
            # Si no, se queda respirando en idle.
            if self.attack_timer >= (self.attack_cooldown - 0.6):
                self.custom_state = "attack"
            else:
                self.custom_state = "idle"
        else:
            self.custom_state = "walk"

        # La clase base se encarga de cambiar los frames por nosotros
        super().update(dt, grid, enemy_group, effects_group, structures_hp, passive_levels, thorns_values)

        if target_pos:
            self.pos = old_pos
            self.rect.center = (round(self.pos.x), round(self.pos.y))

            # Disparamos JUSTO en el frame 3 de la animación de ataque
            if self.state == "attack" and self.current_frame == 3:
                if not self.has_shot_this_cycle:
                    self.has_shot_this_cycle = True

                    fx_offset = 20 if self.facing_right else -20
                    muzzle = MuzzleFlashEffect(self.pos.x + fx_offset, self.pos.y - 8, not self.facing_right)
                    hit = TargetHitEffect(target_pos.x, target_pos.y)

                    if effects_group is not None:
                        effects_group.add(muzzle)
                        effects_group.add(hit)

                    armor_lvl = passive_levels.get("armor", 0) if passive_levels else 0
                    damage_reduction = 1.0 - (armor_lvl * 0.05)
                    final_damage = max(1, int(self.base_damage * damage_reduction))

                    if is_castle_target:
                        self.shot_castle = final_damage
                    elif target_coords and structures_hp:
                        structures_hp[target_coords] -= final_damage
                        if structures_hp[target_coords] <= 0:
                            grid[target_coords[0]][target_coords[1]] = 0
                            del structures_hp[target_coords]

            # Reseteo limpio al terminar los 1.2 segundos
            if self.attack_timer >= self.attack_cooldown:
                self.attack_timer -= self.attack_cooldown
                self.has_shot_this_cycle = False
        else:
            self.attack_timer = max(0.0, self.attack_timer - dt)
            self.has_shot_this_cycle = False


class Boss(Enemy):
    def __init__(self, pixel_x, pixel_y, grid_size, offset_x):
        super().__init__(pixel_x, pixel_y, grid_size, offset_x, health=150, speed=15, color="magenta", radius=28, xp_value=0, gold_value=0, base_damage=35)

        self.target_cells = ()
        self.attack_cooldown = 1.8
        self.range = 75
        self.has_hit_this_cycle = False
        self.current_attack = "attack1"
        self.castle_attack_timer = -99999.0  # Antifallos de main.py

        global boss_sheet
        if boss_sheet is None:
            boss_sheet = pygame.image.load(
                os.path.join("Assets", "Sprites", "Enemies", "boss_minotaur.png")).convert_alpha()

        self.animations = {
            "idle": self._get_boss_frames(boss_sheet, 0, 5),
            "walk": self._get_boss_frames(boss_sheet, 1, 8),
            "attack1": self._get_boss_frames(boss_sheet, 3, 9),
            "attack2": self._get_boss_frames(boss_sheet, 6, 9),
            "death": self._get_boss_frames(boss_sheet, 9, 6)
        }
        self.image = self.animations["walk"][0]

    def _get_boss_frames(self, sheet, row, num_frames, scale=1.5):
        frames = []
        h = sheet.get_height() // 10
        w = h
        for i in range(num_frames):
            frame = pygame.Surface((w, h), pygame.SRCALPHA)
            frame.blit(sheet, (0, 0), (i * w, row * h, w, h))
            scaled = pygame.transform.scale(frame, (int(w * scale), int(h * scale)))
            frames.append(scaled)
        return frames

    def update(self, dt, grid, enemy_group=None, effects_group=None, structures_hp=None, passive_levels=None, thorns_values=None):
        if getattr(self, "is_dying", False):
            super().update(dt, grid, enemy_group, effects_group, structures_hp, passive_levels, thorns_values)
            self.rect = self.image.get_rect()
            self.rect.center = (round(self.pos.x), round(self.pos.y) - 10)
            return

        target_pos = None
        target_coords = None
        is_castle_target = False

        castle_center = pygame.math.Vector2(640, 360)

        # Detectar el Castillo primero
        if self.pos.distance_to(castle_center) <= self.range:
            target_pos = castle_center
            is_castle_target = True

        # Detectar Muros/Torres si no hay castillo a tiro
        if not target_pos and structures_hp:
            for (r, c) in structures_hp.keys():
                s_pos = pygame.math.Vector2(self.offset_x + c * self.grid_size + 15, r * self.grid_size + 15)
                if self.pos.distance_to(s_pos) <= self.range:
                    target_pos = s_pos
                    target_coords = (r, c)
                    break

        old_pos = pygame.math.Vector2(self.pos)

        if target_pos:
            dir_vec = target_pos - self.pos
            if dir_vec.length() > 0:
                self.dir_norm = dir_vec.normalize()

            self.attack_timer += dt

            if self.attack_timer >= (self.attack_cooldown - 0.9):
                self.custom_state = self.current_attack
            else:
                self.custom_state = "idle"
        else:
            self.custom_state = "walk"
            self.attack_timer = max(0.0, self.attack_timer - dt)

        super().update(dt, grid, enemy_group, effects_group, structures_hp, passive_levels, thorns_values)

        if target_pos:
            self.pos = old_pos

            if self.state in ["attack1", "attack2"] and self.current_frame == 5:
                if not self.has_hit_this_cycle:
                    self.has_hit_this_cycle = True

                    armor_lvl = passive_levels.get("armor", 0) if passive_levels else 0
                    damage_reduction = 1.0 - (armor_lvl * 0.05)
                    final_damage = max(1, int(self.base_damage * damage_reduction))

                    hit_castle = False
                    center_r, center_c = None, None

                    if is_castle_target:
                        self.shot_castle = final_damage
                        hit_castle = True
                        center_r = int(360 // self.grid_size)
                        center_c = int((640 - self.offset_x) // self.grid_size)
                    elif target_coords:
                        center_r, center_c = target_coords

                    # AREA DE DAÑO 3x3
                    if center_r is not None and center_c is not None and structures_hp is not None:
                        for dr in [-1, 0, 1]:
                            for dc in [-1, 0, 1]:
                                r_aoe = center_r + dr
                                c_aoe = center_c + dc
                                coords = (r_aoe, c_aoe)

                                # Si hay muro o torre, lo reventamos
                                if coords in structures_hp:
                                    structures_hp[coords] -= final_damage
                                    if structures_hp[coords] <= 0:
                                        grid[r_aoe][c_aoe] = 0
                                        del structures_hp[coords]

                                # Si el área 3x3 roza el castillo y no le habíamos pegado ya...
                                if not hit_castle:
                                    cell_px = pygame.math.Vector2(self.offset_x + c_aoe * self.grid_size + self.grid_size / 2,
                                                                  r_aoe * self.grid_size + self.grid_size / 2)
                                    if cell_px.distance_to(castle_center) < 60:
                                        self.shot_castle = final_damage
                                        hit_castle = True

                    # Daño devuelto por espinas (solo 1 vez por hachazo)
                    thorns_lvl = passive_levels.get("thorns", 0) if passive_levels else 0
                    if thorns_lvl > 0 and thorns_values:
                        self.take_damage(thorns_values[thorns_lvl])

            if self.attack_timer >= self.attack_cooldown:
                self.attack_timer -= self.attack_cooldown
                self.has_hit_this_cycle = False
                self.current_attack = random.choice(["attack1", "attack2"])
        else:
            self.has_hit_this_cycle = False

        self.rect = self.image.get_rect()
        self.rect.center = (round(self.pos.x), round(self.pos.y) - 10)
