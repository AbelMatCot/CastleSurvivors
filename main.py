import pygame
from Entities.Player import castle as cs
# Constantes
forbid = 0
allow = 1
wall = 2
castle = 3
turret = 4
spawn = 5

# iniciar el juego
pygame.init()

# ventana
screen = pygame.display.set_mode((1280, 720), pygame.RESIZABLE)

# 2. El gameboard lógico (donde ocurre la magia a 720p)
# Usaremos 'gameboard' para referirnos a este dibujo interno
base_res = (1280, 720)
gameboard = pygame.Surface(base_res)

# 3. Medidas del tablero cuadrado central
width_gameboard = 720
height_gameboard = 720
offsetX = 280 # (1280 - 720) / 2
grid_size = 30

clock = pygame.time.Clock()
running = True

# --- OBJETOS Y GRUPOS ---
player_group = pygame.sprite.Group()

# El centro del tablero cuadrado es OFFSET_X + (ANCHO_TABLERO / 2)
# X = 280 + 360 = 640 | Y = 360
castle_obj = cs.castle(640, 360)
player_group.add(castle_obj)

# Matriz
row = 24
col = 24
grid = [[0 for _ in range(col)] for _ in range(row)]

forbid = 0

# --- BUCLE PRINCIPAL ---
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # 1. Limpiar el gameboard (fondo de los menús laterales)
    gameboard.fill("#222222")

    # 2. Dibujar el fondo del tablero central (cuadrado negro)
    pygame.draw.rect(gameboard, "#000000", (offsetX, 0, width_gameboard, height_gameboard))

    # 3. Dibujar la cuadrícula (solo dentro del tablero)
    # Líneas verticales
    for x in range(offsetX, offsetX + width_gameboard + 1, grid_size):
        pygame.draw.line(gameboard, "#444444", (x, 0), (x, height_gameboard))
    # Líneas horizontales
    for y in range(0, height_gameboard + 1, grid_size):
        pygame.draw.line(gameboard, "#444444", (offsetX, y), (offsetX + width_gameboard, y))

    # 4. Dibujar entidades (Castillo, torres...)
    player_group.draw(gameboard)

    # 5. ESCALADO MÁGICO (De 1280x720 a lo que mida la ventana)
    screensize = screen.get_size()
    rescaled_gameboard = pygame.transform.scale(gameboard, screensize)
    screen.blit(rescaled_gameboard, (0, 0))

    # Actualizar pantalla
    pygame.display.flip()
    dt = clock.tick(60) / 1000

pygame.quit()