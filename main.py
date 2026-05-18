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

border_bag = ["North","South","West","East"]
random.shuffle(border_bag)
current_tool = None


# --- FUNCIONES ---

def get_spawn_pos():
    border = get_border()
    tunnel_random = random.randint(margin, col - margin - 1)

    if border == "North":
        grid[0][tunnel_random] = spawn_zone
        return tunnel_random, -1
    elif border == "South":
        grid[23][tunnel_random] = spawn_zone
        return tunnel_random, 24
    elif border == "West":
        grid[tunnel_random][0] = spawn_zone
        return -1, tunnel_random
    elif border == "East":
        grid[tunnel_random][23] = spawn_zone
        return 24, tunnel_random

def get_border():
    global border_bag

    if len(border_bag) == 0:
        border_bag = ["North", "South", "West", "East"]
        random.shuffle(border_bag)
    return border_bag.pop()

def setup_spawn_point(spawn_group):
    side = get_border()
    center = random.randint(margin, col - margin - 1)
    if side == "North":
        grid[0][center] = spawn_zone
        new_spawn = Spawn(center, -1, side)
    elif side == "South":
        grid[23][center] = spawn_zone
        new_spawn = Spawn(center, 24, side)
    elif side == "West":
        grid[center][0] = spawn_zone
        new_spawn = Spawn(-1 ,center, side)
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
spawn_group = pygame.sprite.Group()
enemy_group = pygame.sprite.Group()
bullet_group = pygame.sprite.Group()

# X = 280 + 360 = 640 | Y = 360
castle_obj = Castle(640, 360)
player_group.add(castle_obj)


###

for _ in range(3):
    setup_spawn_point(spawn_group)

# --- CONFIGURACIÓN DE CONTROLES REBINDABLES ---
controls = {
    "select_wall": pygame.K_1,
    "select_tower": pygame.K_2
}

# Estado de la herramienta actual: "wall" o "tower"
current_tool = "wall"

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
                    grid[hoverRow][hoverCol] = wall

                elif current_tool == "tower":
                    grid[hoverRow][hoverCol] = turret

                    posX_px = offsetX + (hoverCol * grid_size) + (grid_size // 2)
                    posY_px = (hoverRow * grid_size) + (grid_size // 2)

                    from Entities.Player.towers import ArrowTower

                    new_tower = ArrowTower(posX_px, posY_px)
                    player_group.add(new_tower)


        # teclas
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_g:
                show_grid = not show_grid

            # Deseleccionar todo con ESC
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

    # 5. Escalado a pantalla completa
    screensize = screen.get_size()
    rescaled_gameboard = pygame.transform.scale(gameboard, screensize)
    screen.blit(rescaled_gameboard, (0, 0))

    # 5. Inicializar timer y updates de motores
    pygame.display.flip()
    dt = clock.tick(60) / 1000

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
                    enemy.kill()

                arrow.pierce -= 1
                if arrow.pierce <= 0:
                    arrow.kill()  # La flecha muere
                    break  # Frena esta flecha en seco para que no siga hiriendo a otros

        if enemy.health <= 0:
            enemy.kill()

pygame.quit()