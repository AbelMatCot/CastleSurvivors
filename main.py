import pygame
import random
from Entities.Player import castle as cs

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


border_bag = ["North","South","West","East"]
random.shuffle(border_bag)

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

# X = 280 + 360 = 640 | Y = 360
castle_obj = cs.castle(640, 360)
player_group.add(castle_obj)

###
for _ in range(3):
    spawnX, spawnY = get_spawn_pos()

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
        # click
        if event.type == pygame.MOUSEBUTTONDOWN and on_grid:
            grid[hoverRow][hoverCol] = wall

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_g:
                show_grid = not show_grid

    # 1. Laterales
    gameboard.fill("#222222")

    # 2. Tablero base
    pygame.draw.rect(gameboard, "#000000", (offsetX, 0, width_gameboard, height_gameboard))

    # 3. Dibujar casillas según matriz
    for x in range(24):
        for y in range(24):
            # posicion en pixeles
            posX = offsetX + (x * grid_size)
            posY = y * grid_size

            if grid[y][x] == allow:
                pygame.draw.rect(gameboard, "green", (posX, posY, grid_size, grid_size))
            elif grid[y][x] == forbid:
                pygame.draw.rect(gameboard, "gray", (posX, posY, grid_size, grid_size))
            elif grid[y][x] == spawn_zone:
                pygame.draw.rect(gameboard, "darkgray",(posX, posY, grid_size, grid_size))  # Añadido para que veas el borde
            elif grid[y][x] == castle:
                pygame.draw.rect(gameboard, "yellow", (posX, posY, grid_size, grid_size))
            elif grid[y][x] == wall:
                pygame.draw.rect(gameboard, "brown", (posX, posY, grid_size, grid_size))
            elif grid[y][x] == turret:
                pygame.draw.rect(gameboard, "blue", (posX, posY, grid_size, grid_size))
            elif grid[y][x] == spawn:
                pygame.draw.rect(gameboard, "purple", (posX, posY, grid_size, grid_size))

    # llamar a la cuadricula
    if show_grid:
        gameboard.blit(grid_overlay, (offsetX, 0))

    # 4. Dibujar entidades
    player_group.draw(gameboard)

    # Dibujar fantasma del hover
    if on_grid:
        posX_trans = offsetX + (hoverCol * grid_size)
        posY_trans = hoverRow * grid_size

        surface_trans = pygame.Surface((grid_size, grid_size), pygame.SRCALPHA)
        surface_trans.fill((255, 255, 255, 100))
        gameboard.blit(surface_trans, (posX_trans, posY_trans))

    # 5. escalado
    screensize = screen.get_size()
    rescaled_gameboard = pygame.transform.scale(gameboard, screensize)
    screen.blit(rescaled_gameboard, (0, 0))

    # pantalla y fps
    pygame.display.flip()
    dt = clock.tick(60) / 1000

pygame.quit()