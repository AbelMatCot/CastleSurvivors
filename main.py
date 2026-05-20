import pygame
import random

from Entities.Player.castle import Castle
from Entities.spawn import Spawn

# --- CONSTANTES ---
allow = 0
forbid = 1
wall = 2
castle = 3
margin = 4
spawn = 5
spawn_zone = 6
mountain = 7
turret = 8

# tamaño del tablero (24x24)
width_gameboard = 720
height_gameboard = 720
offsetX = 280  # (1280 - 720) / 2
grid_size = 30
col = 24
row = 24

# variables

current_tool = None

pygame.font.init()
ui_font = pygame.font.SysFont("Arial", 24, bold=True)

# --- LÓGICA DE SPAWNS AVANZADA Y CALENDARIO ---
spawn_counts = {"North": 0, "South": 0, "East": 0, "West": 0}
existing_spawns_pos = {"North": [], "South": [], "East": [], "West": []}

# Forzar los dos primeros en lados opuestos
opposite_pairs = [("North", "South"), ("East", "West")]
forced_initial_spawns = list(random.choice(opposite_pairs))
random.shuffle(forced_initial_spawns) # Aleatorizamos quién sale primero de los dos

# Pre-calculamos los tiempos (en segundos) y el tipo de spawn
spawn_schedule = [
    (90, "balanced"),   # Minuto 01:30
    (180, "balanced"),  # Minuto 03:00
    (270, "balanced"),  # Minuto 04:30
    (360, "balanced"),  # Minuto 06:00
    (450, "balanced"),  # Minuto 07:30
    (540, "balanced"),  # Minuto 09:00
    (630, "balanced"),  # Minuto 10:30
    (720, "balanced"),  # Minuto 12:00
    (810, "wildcard"),  # Minuto 13:30 (Primer comodín)
    (900, "wildcard"),  # Minuto 15:00 (Segundo comodín)
]

# Añadimos los 2 spawns balanceados aleatorios entre el 15:00 (900s) y 17:30 (1050s)
random_time_1 = random.uniform(910, 1040)
random_time_2 = random.uniform(910, 1040)
spawn_schedule.append((random_time_1, "balanced"))
spawn_schedule.append((random_time_2, "balanced"))

# Añadimos el último wildcard exacto en el 17:30 (1050s)
spawn_schedule.append((1050, "wildcard"))

# Ordenamos la lista cronológicamente para que el motor los procese en orden
spawn_schedule.sort(key=lambda x: x[0])

# --- FUNCIONES ---

def get_valid_border(spawn_type):
    if spawn_type == "wildcard":
        print("¡SPAWN COMODÍN ACTIVADO!")
        return random.choice(["North", "South", "East", "West"])
    else:
        min_count = min(spawn_counts.values())
        valid_borders = [b for b, c in spawn_counts.items() if c - min_count < 2]

        # Fallback por si la matemática se atasca
        if not valid_borders:
            valid_borders = ["North", "South", "East", "West"]
        return random.choice(valid_borders)


def setup_spawn_point(spawn_group, spawn_type="balanced"):
    side = get_valid_border(spawn_type)
    if not side:
        return

    valid_pos = False
    attempts = 0
    center = 0

    while not valid_pos and attempts < 50:
        center = random.randint(margin, col - margin - 1)
        conflict = False

        for pos in existing_spawns_pos[side]:
            if abs(center - pos) <= 1:
                conflict = True
                break

        if not conflict:
            valid_pos = True
        attempts += 1

    if not valid_pos:
        return

    existing_spawns_pos[side].append(center)
    spawn_counts[side] += 1

    if side == "North":
        grid[0][center] = spawn_zone
        new_spawn = Spawn(center, -1, side)
    elif side == "South":
        grid[23][center] = spawn_zone
        new_spawn = Spawn(center, 24, side)
    elif side == "West":
        grid[center][0] = spawn_zone
        new_spawn = Spawn(-1, center, side)
    elif side == "East":
        grid[center][23] = spawn_zone
        new_spawn = Spawn(24, center, side)

    spawn_group.add(new_spawn)

# --- INICIALIZACIÓN DE PYGAME ---
pygame.init()

# ventana y resolucion
screen = pygame.display.set_mode((1280, 720), pygame.RESIZABLE)
base_res = (1280, 720)
gameboard = pygame.Surface(base_res)
clock = pygame.time.Clock()
running = True

# --- MATRIZ Y TABLERO ---
grid = [[0 for _ in range(col)] for _ in range(row)]

# zonas del mapa
for y in range(row):
    for x in range(col):
        if x == 0 or x == col - 1 or y == 0 or y == row - 1:
            grid[y][x] = mountain
        elif x < margin or x >= col - margin or y < margin or y >= row - margin:
            grid[y][x] = spawn_zone
        else:
            grid[y][x] = allow

grid[11][11] = castle
grid[11][12] = castle
grid[12][11] = castle
grid[12][12] = castle

# cuadricula trans
grid_overlay = pygame.Surface((width_gameboard, height_gameboard), pygame.SRCALPHA)
white_grid = (255, 255, 255, 150)

for x in range(0, col):
    for y in range(0, row):
        # Solo dibujamos el cuadradito si es zona "allow"
        if grid[y][x] == allow:
            posX = x * grid_size
            posY = y * grid_size
            # Dibujar las 4 líneas del cuadrado o usar un rect con width=1
            pygame.draw.rect(grid_overlay, white_grid, (posX, posY, grid_size, grid_size), 1)

show_grid = True

# --- OBJETOS Y GRUPOS ---
player_group = pygame.sprite.Group()
enemy_group = pygame.sprite.Group()
bullet_group = pygame.sprite.Group()
spawn_group = pygame.sprite.Group()

# X = 280 + 360 = 640 | Y = 360
# Creamos el Reino que ahora dispara flechas de forma nativa
castle_obj = Castle(640, 360)
player_group.add(castle_obj)


###

for _ in range(2):
    setup_spawn_point(spawn_group)

# --- CONFIGURACIÓN DE CONTROLES REBINDABLES ---
controls = {
    "select_wall": pygame.K_1,
    "select_tower": pygame.K_2
}

# Estado de la herramienta actual: "wall" o "tower"
current_tool = "wall"

# --- RELOJ Y DIFICULTAD ---
game_time = 0.0
current_minute = 0
difficulty_multiplier = 1.0

# --- ECONOMÍA Y PROGRESIÓN ---
player_gold = 100  # Un poco de oro inicial para que puedas probar a construir
player_level = 1
player_xp = 0
xp_to_next_level = 10

# --- BUCLE PRINCIPAL ---
while running:
    # posicion mouse
    mouseX, mouseY = pygame.mouse.get_pos()

    enemy_zone_px = 4 * grid_size

# 16 * 16

    limitW = offsetX + (margin * grid_size)
    limitE = offsetX + (col - margin) * grid_size
    limitN = margin * grid_size
    limitS = (row - margin) * grid_size

    on_grid = limitW <= mouseX < limitE and limitN <= mouseY < limitS

    if on_grid:
        hoverCol = (mouseX - offsetX) // grid_size
        hoverRow = mouseY // grid_size

    # eventos
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

            # click del ratón
        if event.type == pygame.MOUSEBUTTONDOWN and on_grid:
            # Solo permitimos construir si la casilla está 100% libre
            if grid[hoverRow][hoverCol] == allow:

                if current_tool == "wall":
                    if player_gold >= 5:
                        player_gold -= 5
                        grid[hoverRow][hoverCol] = wall
                        print("Muro construido. Oro restante:", player_gold)
                    else:
                        print("¡No tienes oro suficiente para el muro!")

                elif current_tool == "tower":
                    if player_gold >= 20:
                        player_gold -= 20
                        grid[hoverRow][hoverCol] = turret

                        posX_px = offsetX + (hoverCol * grid_size) + (grid_size // 2)
                        posY_px = (hoverRow * grid_size) + (grid_size // 2)

                        from Entities.Player.towers import ArrowTower

                        new_tower = ArrowTower(posX_px, posY_px)
                        player_group.add(new_tower)
                        print("Torre construida. Oro restante:", player_gold)
                    else:
                        print("¡No tienes oro suficiente para la torre!")


        # teclas
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_g:
                show_grid = not show_grid

            # Deseleccionar todito con ESC
            elif event.key == pygame.K_ESCAPE:
                current_tool = None
                print("Herramienta deseleccionada")

            # Selección/Deselección de Muro
            elif event.key == controls["select_wall"]:
                if current_tool == "wall":
                    current_tool = None
                    print("Herramienta deseleccionada")
                else:
                    current_tool = "wall"
                    print("Herramienta activa: MURO")

            # Selección/Deselección de Torre
            elif event.key == controls["select_tower"]:
                if current_tool == "tower":
                    current_tool = None
                    print("Herramienta deseleccionada")
                else:
                    current_tool = "tower"
                    print("Herramienta activa: TORRE")

    # 1. Fondo de los laterales
    gameboard.fill("#222222")

    # 2. Tablero base negro
    pygame.draw.rect(gameboard, "#000000", (offsetX, 0, width_gameboard, height_gameboard))

    # 3. Dibujar casillas según matriz (Capa inferior)
    for y in range(24):
        for x in range(24):
            posY = y * grid_size
            posX = offsetX + (x * grid_size)

            if grid[y][x] == allow:
                pygame.draw.rect(gameboard, "green", (posX, posY, grid_size, grid_size))
            elif grid[y][x] == forbid:
                pygame.draw.rect(gameboard, "gray", (posX, posY, grid_size, grid_size))
            elif grid[y][x] == spawn_zone:
                pygame.draw.rect(gameboard, "darkgray", (posX, posY, grid_size, grid_size))
            elif grid[y][x] == castle:
                pygame.draw.rect(gameboard, "yellow", (posX, posY, grid_size, grid_size))
            elif grid[y][x] == wall:
                pygame.draw.rect(gameboard, "brown", (posX, posY, grid_size, grid_size))
            elif grid[y][x] == turret:
                pygame.draw.rect(gameboard, "blue", (posX, posY, grid_size, grid_size))
            elif grid[y][x] == spawn:
                pygame.draw.rect(gameboard, "purple", (posX, posY, grid_size, grid_size))
            elif grid[y][x] == mountain:
                pygame.draw.rect(gameboard, "orange", (posX, posY, grid_size, grid_size))

    # 4. Llamar a la cuadrícula (Por encima del suelo)
    if show_grid:
        gameboard.blit(grid_overlay, (offsetX, 0))

    # 5. Dibujar fantasma del hover (¡FUERA de la condición show_grid!)
    if on_grid:
        posX_trans = offsetX + (hoverCol * grid_size)
        posY_trans = hoverRow * grid_size

        surface_trans = pygame.Surface((grid_size, grid_size), pygame.SRCALPHA)
        current_cell = grid[hoverRow][hoverCol]

        if current_tool is not None and current_cell != allow:
            surface_trans.fill((255, 0, 0, 70))
            gameboard.blit(surface_trans, (posX_trans, posY_trans))
        elif current_tool == "wall":
            c = pygame.Color("brown")
            surface_trans.fill((c.r, c.g, c.b, 120))
            gameboard.blit(surface_trans, (posX_trans, posY_trans))
        elif current_tool == "tower":
            pygame.draw.circle(surface_trans, (0, 0, 255, 120), (grid_size // 2, grid_size // 2), 10)
            gameboard.blit(surface_trans, (posX_trans, posY_trans))
        else:
            surface_trans.fill((255, 255, 255, 40))
            gameboard.blit(surface_trans, (posX_trans, posY_trans))

    # 6. DIBUJAR ENTIDADES
    player_group.draw(gameboard)
    enemy_group.draw(gameboard)
    bullet_group.draw(gameboard)

    # 7. DIBUJAR INTERFAZ (UI)
    seconds = int(game_time % 60)
    time_str = f"{current_minute:02d}:{seconds:02d}"

    ui_text = ui_font.render(
        f"Tiempo: {time_str} | Dif: x{difficulty_multiplier} | Nvl: {player_level} | Oro: {player_gold}",
        True,
        "white"
    )
    gameboard.blit(ui_text, (20, 20))

    # 5. Escalado a pantalla completa
    screensize = screen.get_size()
    rescaled_gameboard = pygame.transform.scale(gameboard, screensize)
    screen.blit(rescaled_gameboard, (0, 0))

    # 5. Inicializar timer y updates de motores
    pygame.display.flip()
    dt = clock.tick(60) / 1000

    # --- ACTUALIZAR RELOJ ---
    game_time += dt
    current_minute = int(game_time // 60)

    difficulty_multiplier = round(1 + (current_minute / 8) ** 1.8, 2)

    # --- GESTOR DE NUEVOS SPAWNS (CRONJOB) ---
    if len(spawn_schedule) > 0:
        # Leemos la siguiente tarea de la lista
        next_spawn_time, next_spawn_type = spawn_schedule[0]

        if game_time >= next_spawn_time:
            setup_spawn_point(spawn_group, next_spawn_type)
            spawn_schedule.pop(0)  # Lo borramos de la lista para no repetirlo
            print(f"[{current_minute}:{int(game_time % 60):02d}] Nuevo túnel abierto. Faltan: {len(spawn_schedule)}")

    spawn_group.update(dt, enemy_group, grid, offsetX, grid_size)
    enemy_group.update(dt, grid)  # <--- ¡Ahora solo necesita dt y grid!

    # --- SEPARACIÓN GLOBAL OPTIMIZADA ULTRA RÁPIDA ---
    # Pygame filtra por C los rectángulos que se tocan, reduciendo drásticamente las operaciones
    collisions = pygame.sprite.groupcollide(enemy_group, enemy_group, False, False)
    for enemy, others in collisions.items():
        push_final = pygame.math.Vector2(0, 0)
        for other in others:
            if other == enemy:
                continue
            distance = enemy.pos.distance_to(other.pos)
            if distance < (enemy.radius + other.radius):
                if distance == 0:
                    enemy.pos += pygame.math.Vector2(random.uniform(-1, 1), random.uniform(-1, 1))
                    continue
                push_final += (enemy.pos - other.pos).normalize() * 60.0

        if push_final.length() > 0:
            if enemy.is_attacking:
                # Deslizamiento lateral fluido si está atascado en un muro
                tangent = pygame.math.Vector2(-enemy.dir_norm.y, enemy.dir_norm.x)
                dot_product = push_final.dot(tangent)
                if abs(dot_product) < 5:
                    dot_product += random.choice([-20.0, 20.0])
                enemy.pos += tangent * dot_product * dt
            else:
                # Empuje normal en carrera
                enemy.pos += push_final.normalize() * 40.0 * dt

        enemy.rect.center = (round(enemy.pos.x), round(enemy.pos.y))

    # Actualización de proyectiles
    player_group.update(dt, enemy_group, bullet_group)
    bullet_group.update(dt)

    # --- COLISIONES OPTIMIZADAS CON SISTEMA PIERCE ---
    # Ahora la clave es la flecha, y el valor es la lista de enemigos que atraviesa
    hits = pygame.sprite.groupcollide(bullet_group, enemy_group, False, False)

    for arrow, enemies_hit in hits.items():
        for enemy in enemies_hit:
            if enemy not in arrow.hit_enemies:
                arrow.hit_enemies.add(enemy)
                enemy.take_damage(arrow.damage)  # Aplica daño y activa el flash blanco

                # Destruir al enemigo si se queda sin vida
                if enemy.health <= 0:
                    player_gold += enemy.gold_value
                    player_xp += enemy.xp_value

                    # Subir de nivel
                    if player_xp >= xp_to_next_level:
                        player_xp -= xp_to_next_level
                        player_level += 1
                        print("¡SUBISTE DE NIVEL!")
                        xp_to_next_level = int(xp_to_next_level * 1.5)  # Cada nivel cuesta un poco más

                    enemy.kill()

                arrow.pierce -= 1
                if arrow.pierce <= 0:
                    arrow.kill()  # La flecha muere
                    break  # Frena esta flecha en seco para que no siga hiriendo a otros

        if enemy.health <= 0:
            enemy.kill()

pygame.quit()