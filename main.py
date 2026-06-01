import pygame
import random
import configparser
import os
import sys

from Entities.Player.towers import ArrowTower, FireballTower, KunaiTower, LaserTower, LightningTower, ThornsTower, \
    TOWER_STATS
from Entities.spawn import Spawn
from Entities.effects import Effect

# =====================================================================
# CAPÍTULO 1: CONSTANTES Y CONFIGURACIÓN BÁSICA
# =====================================================================
allow = 0
forbid = 1
wall = 2
castle = 3
margin = 4
spawn = 5
spawn_zone = 6
mountain = 7
turret = 8

width_gameboard = 720
height_gameboard = 720
offsetX = 280
grid_size = 30
col = 24
row = 24
time_scale = 1.0

config = configparser.ConfigParser()
config_file = "config.ini"

config = configparser.ConfigParser()
config_file = "config.ini"

if not os.path.exists(config_file):
    config["Keybinds"] = {
        "slot_1": "1", "slot_2": "2", "slot_3": "3", "slot_4": "4",
        "wall": "w", "sell": "q", "repair": "e", "repair_all": "r",
        "toggle_hp": "v"
    }
    config["Settings"] = {
        "legible_font": "False",
        "health_bars_mode": "0"
    }
    with open(config_file, "w") as f:
        config.write(f)
else:
    config.read(config_file)
    if "Settings" not in config:
        config["Settings"] = {"legible_font": "False", "health_bars_mode": "0"}
        with open(config_file, "w") as f:
            config.write(f)
    if "toggle_hp" not in config["Keybinds"]:
        config["Keybinds"]["toggle_hp"] = "v"
        with open(config_file, "w") as f:
            config.write(f)

use_legible_font = config.getboolean("Settings", "legible_font", fallback=False)
health_bars_mode = config.getint("Settings", "health_bars_mode", fallback=0)

def get_key(key_str):
    return getattr(pygame, f"K_{key_str.lower()}")

controls = {
    "slot_1": get_key(config["Keybinds"]["slot_1"]),
    "slot_2": get_key(config["Keybinds"]["slot_2"]),
    "slot_3": get_key(config["Keybinds"]["slot_3"]),
    "slot_4": get_key(config["Keybinds"]["slot_4"]),
    "wall": get_key(config["Keybinds"]["wall"]),
    "sell": get_key(config["Keybinds"]["sell"]),
    "repair": get_key(config["Keybinds"]["repair"]),
    "repair_all": get_key(config["Keybinds"]["repair_all"]),
    "toggle_hp": get_key(config["Keybinds"]["toggle_hp"])
}

# =====================================================================
# CAPÍTULO 2: INICIALIZACIÓN DEL MOTOR
# =====================================================================
pygame.init()
pygame.font.init()
screen = pygame.display.set_mode((1280, 720), pygame.RESIZABLE)
base_res = (1280, 720)
gameboard = pygame.Surface(base_res)
clock = pygame.time.Clock()
running = True


# =====================================================================
# CAPÍTULO 3: FUNCIONES DE UTILIDAD (ASSETS Y UI)
# =====================================================================
def extract_sprite(sheet, column, rw, cols_total, rows_total, crop=True, crop_x_only=False):
    w = sheet.get_width() // cols_total
    h = sheet.get_height() // rows_total
    sub = sheet.subsurface((column * w, rw * h, w, h))
    if crop:
        bounding = sub.get_bounding_rect()
        if bounding.width > 0 and bounding.height > 0:
            if crop_x_only:
                # Recorta solo a lo ancho, mantiene el alto original
                return sub.subsurface((bounding.x, 0, bounding.width, h))
            else:
                return sub.subsurface(bounding)
    return sub

def get_smart_slices(sheet, cols_total, rows_total):
    w = sheet.get_width() // cols_total
    h = sheet.get_height() // rows_total

    bounds = []
    for r in range(rows_total):
        row_bounds = []
        for c in range(cols_total):
            sub = sheet.subsurface((c * w, r * h, w, h))
            row_bounds.append(sub.get_bounding_rect())
        bounds.append(row_bounds)

    # Ajustamos el ancho (X) unificando los márgenes de cada columna
    col_rects = []
    for c in range(cols_total):
        valid_x = [bounds[r][c].x for r in range(rows_total) if bounds[r][c].width > 0]
        valid_right = [bounds[r][c].right for r in range(rows_total) if bounds[r][c].width > 0]
        min_x = min(valid_x) if valid_x else 0
        max_r = max(valid_right) if valid_right else w
        col_rects.append((min_x, max_r - min_x))

    # Ajustamos el alto (Y) unificando los márgenes de cada fila
    row_rects = []
    for r in range(rows_total):
        valid_y = [bounds[r][c].y for c in range(cols_total) if bounds[r][c].height > 0]
        valid_bottom = [bounds[r][c].bottom for c in range(cols_total) if bounds[r][c].height > 0]
        min_y = min(valid_y) if valid_y else 0
        max_b = max(valid_bottom) if valid_bottom else h
        row_rects.append((min_y, max_b - min_y))

    parts = []
    for r in range(rows_total):
        for c in range(cols_total):
            cx, cw = col_rects[c]
            cy, ch = row_rects[r]
            if cw > 0 and ch > 0:
                parts.append(sheet.subsurface((c * w + cx, r * h + cy, cw, ch)))
            else:
                parts.append(pygame.Surface((1, 1), pygame.SRCALPHA))
    return parts

def load_ui_icons():
    icons = {}
    for tower_name in ["arrow", "fireball", "kunai", "laser", "lightning", "thorns"]:
        img_path = os.path.join("Assets", "Sprites", "Player", f"{tower_name}tower.png")
        try:
            raw_img = pygame.image.load(img_path).convert_alpha()
        except FileNotFoundError:
            try:
                raw_img = pygame.image.load(
                    os.path.join("Assets", "Sprites", "Player", "fallbacktower.png")).convert_alpha()
            except FileNotFoundError:
                raw_img = pygame.Surface((30, 60))
                raw_img.fill("magenta")

        icon_surf = pygame.Surface((30, 40), pygame.SRCALPHA)
        icon_surf.blit(raw_img, (0, 0), (0, 0, 30, 40))
        icons[tower_name] = pygame.transform.scale(icon_surf, (27, 36))
    return icons


def get_tile(sheet, x, y, width, height, scale_size):
    image = pygame.Surface((width, height), pygame.SRCALPHA)
    image.blit(sheet, (0, 0), (x, y, width, height))
    return pygame.transform.scale(image, (scale_size, scale_size))


def draw_text_wrapped(surface, text, font, color, rect):
    words = text.split(" ")
    lines = []
    current_line = []
    for word in words:
        test_line = " ".join(current_line + [word])
        if font.size(test_line)[0] < rect.width:
            current_line.append(word)
        else:
            lines.append(" ".join(current_line))
            current_line = [word]
    if current_line:
        lines.append(" ".join(current_line))

    y_offset = rect.y
    for line in lines:
        surf = font.render(line, True, color)
        surface.blit(surf, (rect.x, y_offset))
        y_offset += font.get_linesize()

def draw_9_slice_button(surface, image, rect, edge_px=8):
    w, h = image.get_size()
    e_x = min(edge_px, w // 2 - 1, rect.width // 2)
    e_y = min(edge_px, h // 2 - 1, rect.height // 2)

    src_parts = [
        (0, 0, e_x, e_y), (e_x, 0, w - e_x * 2, e_y), (w - e_x, 0, e_x, e_y),
        (0, e_y, e_x, h - e_y * 2), (e_x, e_y, w - e_x * 2, h - e_y * 2), (w - e_x, e_y, e_x, h - e_y * 2),
        (0, h - e_y, e_x, e_y), (e_x, h - e_y, w - e_x * 2, e_y), (w - e_x, h - e_y, e_x, e_y)
    ]
    o_x, o_y = e_x, e_y
    dst_parts = [
        (rect.x, rect.y, o_x, o_y),
        (rect.x + o_x, rect.y, rect.width - o_x * 2, o_y),
        (rect.right - o_x, rect.y, o_x, o_y),
        (rect.x, rect.y + o_y, o_x, rect.height - o_y * 2),
        (rect.x + o_x, rect.y + o_y, rect.width - o_x * 2, rect.height - o_y * 2),
        (rect.right - o_x, rect.y + o_y, o_x, rect.height - o_y * 2),
        (rect.x, rect.bottom - o_y, o_x, o_y),
        (rect.x + o_x, rect.bottom - o_y, rect.width - o_x * 2, o_y),
        (rect.right - o_x, rect.bottom - o_y, o_x, o_y)
    ]

    for src, dst in zip(src_parts, dst_parts):
        if src[2] > 0 and src[3] > 0 and dst[2] > 0 and dst[3] > 0:
            surface.blit(pygame.transform.scale(image.subsurface(src), (int(dst[2]), int(dst[3]))),
                         (int(dst[0]), int(dst[1])))


def draw_bar(surface, x, y, w, h, ratio, base_sheet, fill_sheet):
    left = extract_sprite(base_sheet, 0, 0, 3, 1)
    mid = extract_sprite(base_sheet, 1, 0, 3, 1)
    right = extract_sprite(base_sheet, 2, 0, 3, 1)

    edge_w = min(w // 2, int(h * (left.get_width() / left.get_height())))
    mid_w = max(0, w - (edge_w * 2))

    surface.blit(pygame.transform.scale(left, (edge_w, h)), (x, y))
    if mid_w > 0:
        surface.blit(pygame.transform.scale(mid, (mid_w, h)), (x + edge_w, y))
    surface.blit(pygame.transform.scale(right, (edge_w, h)), (x + edge_w + mid_w, y))

    if ratio > 0:
        fill_crop = extract_sprite(fill_sheet, 0, 0, 1, 1)
        pad_x = int(edge_w * 0.45)
        pad_y = int(h * 0.25)
        inner_w = max(1, w - (pad_x * 2))
        inner_h = max(1, h - (pad_y * 2))
        fill_w = max(1, int(inner_w * ratio))
        surface.blit(pygame.transform.scale(fill_crop, (fill_w, inner_h)), (x + pad_x, y + pad_y))


def draw_paper(surface, sheet, rect):
    parts = get_smart_slices(sheet, 3, 3)
    scale = 2

    # Escalamos las piezas base primero sin deformarlas
    def s(img):
        if img.get_width() <= 0 or img.get_height() <= 0: return img
        return pygame.transform.scale(img, (img.get_width() * scale, img.get_height() * scale))

    tl, tc, tr = s(parts[0]), s(parts[1]), s(parts[2])
    ml, mc, mr = s(parts[3]), s(parts[4]), s(parts[5])
    bl, bc, br = s(parts[6]), s(parts[7]), s(parts[8])

    # Protegemos que las esquinas no se solapen si el rect es muy pequeño
    cw_l, cw_r = min(tl.get_width(), rect.width // 2), min(tr.get_width(), rect.width // 2)
    ch_t, ch_b = min(tl.get_height(), rect.height // 2), min(bl.get_height(), rect.height // 2)

    mid_w = max(0, rect.width - cw_l - cw_r)
    mid_h = max(0, rect.height - ch_t - ch_b)

    # 1. ESQUINAS INTACTAS
    if cw_l > 0 and ch_t > 0: surface.blit(pygame.transform.scale(tl, (cw_l, ch_t)), (rect.x, rect.y))
    if cw_r > 0 and ch_t > 0: surface.blit(pygame.transform.scale(tr, (cw_r, ch_t)), (rect.right - cw_r, rect.y))
    if cw_l > 0 and ch_b > 0: surface.blit(pygame.transform.scale(bl, (cw_l, ch_b)), (rect.x, rect.bottom - ch_b))
    if cw_r > 0 and ch_b > 0: surface.blit(pygame.transform.scale(br, (cw_r, ch_b)),
                                           (rect.right - cw_r, rect.bottom - ch_b))

    # 2. BORDES HORIZONTALES (Tiling horizontal)
    if mid_w > 0:
        tc_w = max(1, tc.get_width())
        reps_x = max(1, int((mid_w / tc_w) + 0.5))
        chunk_w, rem_x = divmod(mid_w, reps_x)

        curr_x = rect.x + cw_l
        for i in range(reps_x):
            w = chunk_w + (1 if i < rem_x else 0)
            if w > 0:
                if ch_t > 0: surface.blit(pygame.transform.scale(tc, (w, ch_t)), (curr_x, rect.y))
                if ch_b > 0: surface.blit(pygame.transform.scale(bc, (w, ch_b)), (curr_x, rect.bottom - ch_b))
                curr_x += w

    # 3. BORDES VERTICALES (Tiling vertical)
    if mid_h > 0:
        ml_h = max(1, ml.get_height())
        reps_y = max(1, int((mid_h / ml_h) + 0.5))
        chunk_h, rem_y = divmod(mid_h, reps_y)

        curr_y = rect.y + ch_t
        for i in range(reps_y):
            h = chunk_h + (1 if i < rem_y else 0)
            if h > 0:
                if cw_l > 0: surface.blit(pygame.transform.scale(ml, (cw_l, h)), (rect.x, curr_y))
                if cw_r > 0: surface.blit(pygame.transform.scale(mr, (cw_r, h)), (rect.right - cw_r, curr_y))
                curr_y += h

    # 4. CENTRO (Tiling en cuadrícula bidimensional)
    if mid_w > 0 and mid_h > 0:
        mc_w, mc_h = max(1, mc.get_width()), max(1, mc.get_height())
        reps_x = max(1, int((mid_w / mc_w) + 0.5))
        reps_y = max(1, int((mid_h / mc_h) + 0.5))
        chunk_w, rem_x = divmod(mid_w, reps_x)
        chunk_h, rem_y = divmod(mid_h, reps_y)

        curr_y = rect.y + ch_t
        for y_idx in range(reps_y):
            h = chunk_h + (1 if y_idx < rem_y else 0)
            curr_x = rect.x + cw_l
            for x_idx in range(reps_x):
                w = chunk_w + (1 if x_idx < rem_x else 0)
                if w > 0 and h > 0:
                    surface.blit(pygame.transform.scale(mc, (w, h)), (curr_x, curr_y))
                curr_x += w
            curr_y += h

def draw_ribbon(surface, x, y, w, h, sheet, rw=0, rows_total=2):
    # Usamos el recorte inteligente en cuadrícula 3xN
    parts = get_smart_slices(sheet, 3, rows_total)
    left = parts[rw * 3 + 0]
    mid = parts[rw * 3 + 1]
    right = parts[rw * 3 + 2]

    edge_w_l = int(h * (left.get_width() / max(1, left.get_height())))
    edge_w_r = int(h * (right.get_width() / max(1, right.get_height())))
    mid_w = max(0, w - (edge_w_l + edge_w_r))

    surface.blit(pygame.transform.scale(left, (edge_w_l, h)), (x, y))

    if mid_w > 0:
        mid_base_w = max(1, int(h * (mid.get_width() / max(1, mid.get_height()))))
        reps = max(1, int((mid_w / mid_base_w) + 0.5))

        chunk_w = mid_w // reps
        remainder = mid_w % reps

        curr_x = x + edge_w_l
        for i in range(reps):
            cw = chunk_w + (1 if i < remainder else 0)
            if cw > 0:
                surface.blit(pygame.transform.scale(mid, (cw, h)), (curr_x, y))
                curr_x += cw

    surface.blit(pygame.transform.scale(right, (edge_w_r, h)), (x + edge_w_l + mid_w, y))

def draw_slot(x, y, size, key_text, cost=None, is_pressed=False, t_id=None):
    img = btn_small_pressed_img if is_pressed else btn_small_img
    btn_y = y + 4 if is_pressed else y
    btn_h = size - 4 if is_pressed else size
    gameboard.blit(pygame.transform.scale(img, (size, btn_h)), (x, btn_y))

    y_off = 4 if is_pressed else 0
    pygame.draw.rect(gameboard, "#3b2f2f", (x - 8, y - 8 + y_off, 22, 22), border_radius=4)
    pygame.draw.rect(gameboard, "#d2b48c", (x - 8, y - 8 + y_off, 22, 22), 2, border_radius=4)

    if t_id and t_id in ui_tower_icons:
        icon = ui_tower_icons[t_id]
        ix = x + (size // 2) - (icon.get_width() // 2)
        iy = y + (size // 2) - (icon.get_height() // 2) + y_off - 4
        gameboard.blit(icon, (ix, iy))

    if keys_sheet:
        k = key_text.lower()
        col_idx, row_idx = KEYMAP_COORDS.get(k, (7, 6))
        key_img = extract_sprite(keys_sheet, col_idx, row_idx, 8, 8)
        if key_img:
            key_img = pygame.transform.scale(key_img, (18, 18))
            gameboard.blit(key_img, (x - 6, y - 6 + y_off))
    else:
        key_surf = ui_font_small.render(key_text.upper(), True, "white")
        gameboard.blit(key_surf, (x - 1, y - 5 + y_off))

    draw_ribbon(gameboard, x - 5, y + size + 2, 60, 25, ribbon_sheet, rw=1)
    if cost is not None:
        cost_surf = ui_font_small.render(f"{cost} G", True, "black")
        gameboard.blit(cost_surf, (x + 25 - cost_surf.get_width() // 2, y + size + 7))


def draw_action_btn(x, y, w, h, key_text, label, cost=None, is_pressed=False):
    img = btn_wide_pressed_img if is_pressed else btn_wide_img
    btn_y = y + 4 if is_pressed else y
    btn_h = h - 4 if is_pressed else h
    draw_9_slice_button(gameboard, img, pygame.Rect(x, btn_y, w, btn_h), edge_px=14)

    y_off = 4 if is_pressed else 0
    pygame.draw.rect(gameboard, "#3b2f2f", (x - 10, y - 10 + y_off, 26, 26), border_radius=4)
    pygame.draw.rect(gameboard, "#d2b48c", (x - 10, y - 10 + y_off, 26, 26), 2, border_radius=4)

    if keys_sheet:
        k = key_text.lower()
        col_idx, row_idx = KEYMAP_COORDS.get(k, (7, 6))
        key_img = extract_sprite(keys_sheet, col_idx, row_idx, 8, 8)
        if key_img:
            key_img = pygame.transform.scale(key_img, (22, 22))
            gameboard.blit(key_img, (x - 8, y - 8 + y_off))
    else:
        key_surf = ui_font_medium.render(key_text.upper(), True, "white")
        gameboard.blit(key_surf, (x - 3, y - 8 + y_off))

    label_surf = ui_font_medium.render(label, True, "black")
    gameboard.blit(label_surf, (x + (w // 2) - (label_surf.get_width() // 2),
                                y + (h // 2) - (label_surf.get_height() // 2) - 4 + y_off))

    if cost is not None:
        ry = y + h + 2
        rw_btn = 80
        rh_btn = 28
        rx_ribbon = x + (w // 2) - (rw_btn // 2)
        draw_ribbon(gameboard, rx_ribbon, ry, rw_btn, rh_btn, ribbon_sheet, rw=0)
        cost_surf = ui_font_small.render(f"{cost} G", True, "black")
        gameboard.blit(cost_surf, (rx_ribbon + (rw_btn // 2) - (cost_surf.get_width() // 2), ry + 6))


# =====================================================================
# CAPÍTULO 4: CARGA DE RECURSOS (ASSETS Y FUENTES)
# =====================================================================

class TowerSmoke(pygame.sprite.Sprite):
    def __init__(self, x, y, goes_right=False):
        super().__init__()
        self.frames = []
        if smoke_sheet:
            w = smoke_sheet.get_width()
            h = smoke_sheet.get_height()

            # Ajuste mágico: dividimos el ancho total entre los fotogramas.
            # A ojo parecen 9, pero si ves que parpadea algo, cámbialo a 8 o 10.
            num_frames = 9
            frame_w = w // num_frames

            for i in range(num_frames):
                frame = pygame.Surface((frame_w, h), pygame.SRCALPHA)
                frame.blit(smoke_sheet, (0, 0), (i * frame_w, 0, frame_w, h))

                # Si queremos que vaya a la derecha, lo volteamos
                if goes_right:
                    frame = pygame.transform.flip(frame, True, False)

                frame = pygame.transform.scale(frame, (frame_w * 2, h * 2))
                self.frames.append(frame)
        else:
            self.frames.append(pygame.Surface((0, 0)))

        self.current_frame = 0
        self.image = self.frames[0]

        # Separamos la onda expansiva del centro
        offset_x = 20 if goes_right else -20
        self.rect = self.image.get_rect(midbottom=(x + offset_x, y))
        self.timer = 0.0

    def update(self, dt):
        self.timer += dt
        if self.timer >= 0.05:
            self.timer = 0.0
            self.current_frame += 1
            if self.current_frame < len(self.frames):
                self.image = self.frames[self.current_frame]
            else:
                self.kill()

ui_font_large = None
ui_font_medium = None
ui_font_small = None

if use_legible_font:
    ui_font_large = pygame.font.SysFont("Arial", 28, bold=True)
    ui_font_medium = pygame.font.SysFont("Arial", 20, bold=True)
    ui_font_small = pygame.font.SysFont("Arial", 14, bold=True)
else:
    font_path = os.path.join("Assets", "alagard.ttf")
    try:
        ui_font_large = pygame.font.Font(font_path, 32)
        ui_font_medium = pygame.font.Font(font_path, 22)
        ui_font_small = pygame.font.Font(font_path, 16)
    except FileNotFoundError:
        print("Warning: Assets/alagard.ttf not found. Using Arial as fallback.")
        ui_font_large = pygame.font.SysFont("Arial", 28, bold=True)
        ui_font_medium = pygame.font.SysFont("Arial", 20, bold=True)
        ui_font_small = pygame.font.SysFont("Arial", 14, bold=True)

ui_tower_icons = load_ui_icons()

# --- NUEVO: PRECARGAR LAS TORRES TRANSPARENTES PARA EL HOVER ---
preview_towers = {}
for t_name in ["arrow", "fireball", "kunai", "laser", "lightning", "thorns"]:
    try:
        img = pygame.image.load(os.path.join("Assets", "Sprites", "Player", f"{t_name}tower.png")).convert_alpha()
    except FileNotFoundError:
        try:
            img = pygame.image.load(os.path.join("Assets", "Sprites", "Player", "fallbacktower.png")).convert_alpha()
        except FileNotFoundError:
            img = pygame.Surface((30, 60))
            img.fill("magenta")

    img_copy = img.copy()
    img_copy.set_alpha(150)  # Hacemos la torre semitransparente
    preview_towers[t_name] = img_copy

# --- CARGA DEL TILESET DE MUROS Y BITMASKING ---
try:
    wall_sheet = pygame.image.load(os.path.join("Assets", "Sprites", "Tiles", "walls.png")).convert_alpha()
except FileNotFoundError:
    wall_sheet = pygame.Surface((120, 120), pygame.SRCALPHA)
    wall_sheet.fill("brown")

# PRIMERO DECLARAMOS EL DICCIONARIO MATEMÁTICO
wall_mask_map = {
    10: (0, 0), 5: (1, 0), 15: (2, 0), 0: (3, 0),
    3: (0, 1), 6: (1, 1), 12: (2, 1), 9: (3, 1),
    1: (0, 2), 4: (1, 2), 8: (2, 2), 2: (3, 2),
    11: (0, 3), 7: (1, 3), 14: (2, 3), 13: (3, 3)
}

# --- CARGA DE MUROS DESTRUIDOS (RUINAS) ---
try:
    ruin_sheet = pygame.image.load(os.path.join("Assets", "Sprites", "Tiles", "ruins.png")).convert_alpha()
except FileNotFoundError:
    ruin_sheet = pygame.Surface((120, 120), pygame.SRCALPHA)

ruin_sprites = {}
for mask, (c, r) in wall_mask_map.items():
    if mask != 0:  # El 0 no lo guardamos porque las ruinas aisladas desaparecen
        ruin_sprites[mask] = extract_sprite(ruin_sheet, c, r, 4, 4, crop=False)

wall_sprites = {}
for mask, (c, r) in wall_mask_map.items():
    wall_sprites[mask] = extract_sprite(wall_sheet, c, r, 4, 4, crop=False)

# Añadimos el muro horizontal a la interfaz y al fantasma
ui_tower_icons["wall"] = pygame.transform.scale(wall_sprites[10], (30, 30))
preview_towers["wall"] = wall_sprites[10].copy()
preview_towers["wall"].set_alpha(150)

effects_group = pygame.sprite.Group()

path_color2 = os.path.join("Assets", "Sprites", "Tiles", "Tilemap_color2.png")
path_color4 = os.path.join("Assets", "Sprites", "Tiles", "Tilemap_color4.png")
path_elevation = os.path.join("Assets", "Sprites", "Tiles", "Tilemap_Elevation.png")

try:
    color2_sheet = pygame.image.load(path_color2).convert_alpha()
    color4_sheet = pygame.image.load(path_color4).convert_alpha()
    elevation_sheet = pygame.image.load(path_elevation).convert_alpha()
except FileNotFoundError:
    print("ERROR: Missing terrain textures.")
    pygame.quit()
    sys.exit()

explosion_sheet = pygame.image.load(os.path.join("Assets", "Sprites", "Effects", "Explosion_01.png")).convert_alpha()
dust_sheet = pygame.image.load(os.path.join("Assets", "Sprites", "Effects", "breaksmoke.png")).convert_alpha()
smoke_sheet = pygame.image.load(os.path.join("Assets", "Sprites", "Effects", "buildsmoke.png")).convert_alpha()
wallsmoke_sheet = pygame.image.load(os.path.join("Assets", "Sprites", "Effects", "wallsmoke.png")).convert_alpha()

ui_path = os.path.join("Assets", "UI")
try:
    btn_sheet = pygame.image.load(os.path.join(ui_path, "Button_Hover.png")).convert_alpha()
    ribbon_sheet = pygame.image.load(os.path.join(ui_path, "SmallRibbons.png")).convert_alpha()
    special_paper_sheet = pygame.image.load(os.path.join(ui_path, "SpecialPaper.png")).convert_alpha()
    big_bar_base = pygame.image.load(os.path.join(ui_path, "BigBar_Base.png")).convert_alpha()
    big_bar_fill = pygame.image.load(os.path.join(ui_path, "BigBar_Fill.png")).convert_alpha()
    small_bar_base = pygame.image.load(os.path.join(ui_path, "SmallBar_Base.png")).convert_alpha()
    small_bar_fill = pygame.image.load(os.path.join(ui_path, "SmallBar_Fill.png")).convert_alpha()
    big_ribbon_sheet = pygame.image.load(os.path.join(ui_path, "BigRibbons.png")).convert_alpha()
except FileNotFoundError as e:
    print(f"UI ERROR: Image {e} not found.")
    pygame.quit()
    sys.exit()

btn_small_img = extract_sprite(btn_sheet, 0, 0, 2, 3, crop=True)
btn_small_pressed_img = extract_sprite(btn_sheet, 1, 0, 2, 3, crop=True)
btn_wide_img = extract_sprite(btn_sheet, 0, 1, 2, 3, crop=True)
btn_wide_pressed_img = extract_sprite(btn_sheet, 1, 1, 2, 3, crop=True)

try:
    keys_sheet = pygame.image.load(os.path.join(ui_path, "Keyboard Letters and Symbols.png")).convert_alpha()
except FileNotFoundError:
    keys_sheet = None

KEYMAP_COORDS = {
    "a": (0, 2), "b": (1, 2), "c": (2, 2), "d": (3, 2), "e": (4, 2), "f": (5, 2), "g": (6, 2), "h": (7, 2),
    "i": (0, 3), "j": (1, 3), "k": (2, 3), "l": (3, 3), "m": (4, 3), "n": (5, 3), "o": (6, 3), "p": (7, 3),
    "q": (0, 4), "r": (1, 4), "s": (2, 4), "t": (3, 4), "u": (4, 4), "v": (5, 4), "w": (6, 4), "x": (7, 4),
    "y": (0, 5), "z": (1, 5),
    "1": (0, 7), "2": (1, 7), "3": (2, 7), "4": (3, 7), "5": (2, 4), "6": (4, 7), "7": (5, 7), "8": (6, 7), "9": (7, 7),
    "0": (6, 3), "esc": (5, 6),
    "up": (0, 0), "down": (1, 0), "left": (2, 0), "right": (3, 0),
    "f1": (4, 0), "f2": (5, 0), "f3": (6, 0), "f4": (7, 0),
    "f5": (0, 1), "f6": (1, 1), "f7": (2, 1), "f8": (3, 1), "f9": (4, 1), "f10": (5, 1), "f11": (6, 1), "f12": (7, 1),
    ".": (2, 5), ",": (3, 5), "?": (4, 5), "/": (5, 5), "\\": (6, 5), "=": (7, 5),
    "'": (0, 6), "[": (1, 6), "]": (2, 6), "+": (3, 6), "-": (4, 6), ";": (6, 6)
}

# =====================================================================
# CAPÍTULO 5: VARIABLES DE ESTADO Y DICCIONARIOS
# =====================================================================
current_tool = None
game_state = "PLAYING"
unlocked_towers = ["arrow"]
active_towers = ["arrow", None, None, None]
level_up_options = []
card_rects = []
pause_rects = []
TOWER_BASE_HP = [0, 50, 55, 65, 80, 100, 125, 150, 200]
meta_health = 0

UI_TOWER_NAMES = {
    "arrow": "Archer Tower", "fireball": "Fireball", "kunai": "Kunai Volley",
    "laser": "Ice Beam", "lightning": "Chain Lightning", "thorns": "Thorns Ground"
}

TOWER_DESCRIPTIONS = {
    "arrow": {
        1: "High range and firerate. Arrows can penetrate enemies at higher levels.",
        2: "Damage increased.", 3: "Firerate increased. Tower limit increased.",
        4: "Now arrows can penetrate one enemy.", 5: "Damage increased. Tower limit increased.",
        6: "Firerate increased.", 7: "Arrows can penetrate two enemies. Tower limit increased.",
        8: "Range, damage and firerate greatly increased."
    },
    "fireball": {
        1: "High damage, low firerate. Projectiles explode dealing damage in an area.",
        2: "Damage increased.", 3: "Firerate increased. Area increased.",
        4: "Damage increased. Tower limit increased.", 5: "Range increased. Firerate increased.",
        6: "Damage increased. Area increased.", 7: "Tower limit increased.",
        8: "Range, damage, firerate and area greatly increased."
    },
    "kunai": {
        1: "High firerate. Shoots multiple projectiles at higher levels.",
        2: "Firerate increased.", 3: "Number of projectiles increased.",
        4: "Damage increased. Tower limit increased.", 5: "Number of projectiles increased.",
        6: "Range increased. Firerate increased.", 7: "Tower limit increased.",
        8: "Range, damage, firerate and number of projectiles greatly increased."
    },
    "laser": {
        1: "Low damage, but slows enemies down.",
        2: "Damage increased.", 3: "Range increased. Slow increased.",
        4: "Damage increased. Tower limit increased.", 5: "Range increased. Slow increased.",
        6: "Damage increased.", 7: "Tower limit increased.",
        8: "Range, damage and slow greatly increased."
    },
    "lightning": {
        1: "High firerate, low damage. Projectiles bounce between enemies.",
        2: "Damage increased.", 3: "Firerate increased. Bounce range increased.",
        4: "Bounces increased. Tower limit increased.", 5: "Damage increased.",
        6: "Bounces increased. Firerate increased.", 7: "Tower limit increased.",
        8: "Range, damage, firerate and bounces greatly increased."
    },
    "thorns": {
        1: "Spawns a thorny patch under enemies that deals damage over time.",
        2: "Damage increased.", 3: "Patch area and maximum target limit increased.",
        4: "Damage and tower limit increased. Range slightly increased.",
        5: "Patch attack speed increased. Max target limit increased.",
        6: "Damage and patch area increased.", 7: "Range and tower limit increased. Max target limit increased.",
        8: "High damage, large area and extremely fast tick rate."
    }
}

PASSIVE_DESCRIPTIONS = {
    "damage": "Increases the damage of all your towers by 5% per level.",
    "firerate": "Increases the attack speed of all your towers by 5% per level.",
    "range": "Increases the range and area of effect of your towers by 5% per level.",
    "health": "Increases Castle and Wall maximum health by 5% per level.",
    "regen": "Regenerates 1% of Castle health per second per level.",
    "armor": "Reduces incoming damage to Castle and Walls by 5% per level.",
    "thorns": "Enemies taking damage from walls or castle take damage back.",
    "gold": "Increases gold earned from enemies by 5% per level.",
    "xp": "Increases experience earned from enemies by 5% per level.",
    "crit": "10% chance per level to deal 150% damage."
}

ENEMY_WEIGHTS = {
    "Basic": 1.0, "Fast": 1.0, "Swarmer": 0.5,
    "Shooter": 2.0, "Flyer": 2.0, "Tank": 4.0, "Generator": 15.0
}

WAVE_POOLS = {
    0: {"Basic": 100},
    2: {"Basic": 70, "Fast": 30},
    5: {"Basic": 50, "Fast": 30, "Shooter": 20},
    8: {"Basic": 40, "Fast": 20, "Shooter": 20, "Tank": 20},
    12: {"Basic": 30, "Fast": 15, "Shooter": 20, "Tank": 20, "Flyer": 15},
    15: {"Basic": 20, "Fast": 15, "Shooter": 15, "Tank": 25, "Flyer": 15, "Generator": 10}
}

player_gold = 100
player_gems = 0
player_level = 1
player_xp = 0
xp_to_next_level = 50
selected_card_idx = None

castle_max_hp = 100
castle_hp = castle_max_hp
structures_hp = {}
wall_masks = {}
ruin_masks = {}

previous_structures_hp = {}
damage_timers = {}
previous_structures_types = {}

tower_levels = {"arrow": 1, "fireball": 0, "kunai": 0, "laser": 0, "lightning": 0, "thorns": 0}

active_passives = []
passive_levels = {
    "damage": 0, "firerate": 0, "range": 0, "health": 0, "regen": 0,
    "armor": 0, "thorns": 0, "gold": 0, "xp": 0, "crit": 0
}

THORNS_VALUES = [0, 2, 4, 7, 10]

spawn_counts = {"North": 0, "South": 0, "East": 0, "West": 0}
existing_spawns_pos = {"North": [], "South": [], "East": [], "West": []}

forced_initial_spawns = random.choice([["North", "South"], ["East", "West"]])
random.shuffle(forced_initial_spawns)

spawn_schedule = [
    (90, "balanced"), (180, "balanced"), (270, "balanced"), (360, "balanced"),
    (450, "balanced"), (540, "balanced"), (630, "balanced"), (720, "balanced"),
    (810, "wildcard"), (900, "wildcard"),
]
random_time_1 = random.uniform(910, 1040)
random_time_2 = random.uniform(910, 1040)
spawn_schedule.extend([(random_time_1, "balanced"), (random_time_2, "balanced"), (1050, "wildcard")])
spawn_schedule.sort(key=lambda x: x[0])

last_built_cell = None

# =====================================================================
# CAPÍTULO 6: FUNCIONES DE LÓGICA DE JUEGO
# =====================================================================
def get_valid_border(spawn_type):
    if spawn_type == "wildcard":
        return random.choice(["North", "South", "East", "West"])
    else:
        if len(forced_initial_spawns) > 0:
            return forced_initial_spawns.pop(0)
        min_count = min(spawn_counts.values())
        valid_borders = [b for b, c in spawn_counts.items() if c - min_count < 2]
        if not valid_borders:
            valid_borders = ["North", "South", "East", "West"]
        return random.choice(valid_borders)


def setup_spawn_point(spwn_grp, spawn_type="balanced"):
    side = get_valid_border(spawn_type)
    if not side: return

    valid_pos = False
    attempts = 0
    center = 0

    while not valid_pos and attempts < 50:
        center = random.randint(2, col - 3)
        conflict = False
        for pos in existing_spawns_pos[side]:
            if abs(center - pos) <= 2:
                conflict = True
                break
        if not conflict:
            valid_pos = True
        attempts += 1

    if not valid_pos: return

    existing_spawns_pos[side].append(center)
    spawn_counts[side] += 1

    if side == "North":
        spawn_x, spawn_y = center, -1
        grid[0][center] = margin
        fx_base = offsetX + (center * grid_size) + 15
        fy_base = 0 * grid_size + 15
    elif side == "South":
        spawn_x, spawn_y = center, row
        grid[row - 1][center] = margin
        fx_base = offsetX + (center * grid_size) + 15
        fy_base = (row - 1) * grid_size + 15
    elif side == "West":
        spawn_x, spawn_y = -1, center
        grid[center][0] = margin
        fx_base = offsetX + 0 * grid_size + 15
        fy_base = (center * grid_size) + 15
    elif side == "East":
        spawn_x, spawn_y = col, center
        grid[center][col - 1] = margin
        fx_base = offsetX + (col - 1) * grid_size + 15
        fy_base = (center * grid_size) + 15

    new_spawn = Spawn(spawn_x, spawn_y)
    spwn_grp.add(new_spawn)

    offsets = [(0, 0, 0.0), (-14, 8, 0.15), (14, 18, 0.3)]
    for ox, oy, dly in offsets:
        dust = Effect(fx_base + ox, fy_base + oy, dust_sheet, scale_size=70, fps=11, delay=dly)
        effects_group.add(dust)


def get_level_up_cards():
    if player_level > 50:
        return [
            {"title": "Heal Castle 20%", "desc": "Restores a large amount of lost health.", "type": "heal_20"},
            {"title": "Gold Bag (+100)", "desc": "A big boost for your economy.", "type": "gold_100"},
            {"title": "Gems (+5)", "desc": "Useful for meta-progression.", "type": "gems_5"}
        ]
    pool = []
    has_free_slot = None in active_towers

    for t_id in ["arrow", "fireball", "kunai", "laser", "lightning", "thorns"]:
        lvl = tower_levels[t_id]
        name = UI_TOWER_NAMES[t_id]
        if lvl == 0:
            if has_free_slot:
                pool.append({"title": f"Unlock {name}", "desc": TOWER_DESCRIPTIONS[t_id][1], "type": "upgrade_tower",
                             "id": t_id})
        elif lvl < 8:
            pool.append({"title": f"Upgrade {name} (Lvl{lvl + 1})", "desc": TOWER_DESCRIPTIONS[t_id][lvl + 1],
                         "type": "upgrade_tower", "id": t_id})

    passive_names = {
        "damage": "Damage", "firerate": "Firerate", "range": "Range/Area",
        "health": "Max Health", "regen": "Health Regen", "armor": "Armor",
        "thorns": "Thorns", "gold": "Extra Gold", "xp": "Extra XP", "crit": "Critical"
    }

    for p_id, lvl in passive_levels.items():
        if lvl == 0:
            if len(active_passives) < 6:
                pool.append({"title": f"Passive: {passive_names[p_id]}", "desc": PASSIVE_DESCRIPTIONS[p_id],
                             "type": "unlock_passive", "id": p_id})
        elif lvl < 4:
            pool.append({"title": f"Upgrade: {passive_names[p_id]} (Lvl{lvl + 1})", "desc": PASSIVE_DESCRIPTIONS[p_id],
                         "type": "upgrade_passive", "id": p_id})

    random.shuffle(pool)
    cards = pool[:3]

    fallbacks = [{"title": "Gold Bag (+50)", "type": "gold"}, {"title": "Heal Castle 50%", "type": "heal"}]
    while len(cards) < 3:
        cards.append(random.choice(fallbacks))
    return cards


def get_tile_for_cell(col_idx, row_idx, target_types, tile_dict, oob_is_target=True):
    N = (row_idx == 0 and oob_is_target) or (row_idx > 0 and grid[row_idx - 1][col_idx] in target_types)
    S = (row_idx == row - 1 and oob_is_target) or (row_idx < row - 1 and grid[row_idx + 1][col_idx] in target_types)
    W = (col_idx == 0 and oob_is_target) or (col_idx > 0 and grid[row_idx][col_idx - 1] in target_types)
    E = (col_idx == col - 1 and oob_is_target) or (col_idx < col - 1 and grid[row_idx][col_idx + 1] in target_types)
    key = (int(N), int(S), int(W), int(E))
    return tile_dict.get(key, tile_dict.get((1, 1, 1, 1)))


def update_ruin_masks(r, c):
    mask = 0
    if r > 0 and grid[r - 1][c] == wall: mask += 1
    if c < col - 1 and grid[r][c + 1] == wall: mask += 2
    if r < row - 1 and grid[r + 1][c] == wall: mask += 4
    if c > 0 and grid[r][c - 1] == wall: mask += 8

    if mask == 0:
        if (r, c) in ruin_masks:
            del ruin_masks[(r, c)]
    else:
        ruin_masks[(r, c)] = mask


def update_wall_masks(r, c):
    mask = 0
    # Comprobamos si hay un muro sano O una ruina en cada dirección
    if r > 0 and (grid[r - 1][c] == wall or (r - 1, c) in ruin_masks): mask += 1  # Norte
    if c < col - 1 and (grid[r][c + 1] == wall or (r, c + 1) in ruin_masks): mask += 2  # Este
    if r < row - 1 and (grid[r + 1][c] == wall or (r + 1, c) in ruin_masks): mask += 4  # Sur
    if c > 0 and (grid[r][c - 1] == wall or (r, c - 1) in ruin_masks): mask += 8  # Oeste
    wall_masks[(r, c)] = mask


def update_neighbors_walls(r, c):
    for nr, nc in [(r, c), (r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)]:
        if 0 <= nr < row and 0 <= nc < col:
            if grid[nr][nc] == wall:
                update_wall_masks(nr, nc)
            if (nr, nc) in ruin_masks:
                update_ruin_masks(nr, nc)

# =====================================================================
# CAPÍTULO 7: PREPARACIÓN DEL MAPA Y GRUPOS
# =====================================================================
background_tile = get_tile(color4_sheet, 64, 64, 64, 64, grid_size)
buildable_tiles = {
    (1, 1, 1, 1): get_tile(color2_sheet, 64, 64, 64, 64, grid_size),
    (0, 1, 1, 1): get_tile(color2_sheet, 64, 0, 64, 64, grid_size),
    (1, 0, 1, 1): get_tile(color2_sheet, 64, 128, 64, 64, grid_size),
    (1, 1, 0, 1): get_tile(color2_sheet, 0, 64, 64, 64, grid_size),
    (1, 1, 1, 0): get_tile(color2_sheet, 128, 64, 64, 64, grid_size),
    (0, 1, 0, 1): get_tile(color2_sheet, 0, 0, 64, 64, grid_size),
    (0, 1, 1, 0): get_tile(color2_sheet, 128, 0, 64, 64, grid_size),
    (1, 0, 0, 1): get_tile(color2_sheet, 0, 128, 64, 64, grid_size),
    (1, 0, 1, 0): get_tile(color2_sheet, 128, 128, 64, 64, grid_size),
}

mountain_tiles = {
    (1, 0, 1, 1): get_tile(elevation_sheet, 64, 192, 64, 64, grid_size),
    (0, 1, 1, 1): get_tile(elevation_sheet, 64, 0, 64, 64, grid_size),
    (1, 1, 0, 1): get_tile(elevation_sheet, 0, 64, 64, 64, grid_size),
    (1, 1, 1, 0): get_tile(elevation_sheet, 128, 64, 64, 64, grid_size),
    (1, 0, 0, 1): get_tile(elevation_sheet, 0, 192, 64, 64, grid_size),
    (1, 0, 1, 0): get_tile(elevation_sheet, 128, 192, 64, 64, grid_size),
    (0, 1, 0, 1): get_tile(elevation_sheet, 0, 0, 64, 64, grid_size),
    (0, 1, 1, 0): get_tile(elevation_sheet, 128, 0, 64, 64, grid_size),
    (1, 1, 1, 1): get_tile(elevation_sheet, 64, 64, 64, 64, grid_size),
}

grid = [[0 for _ in range(col)] for _ in range(row)]
for y in range(row):
    for x in range(col):
        if x == 0 or x == col - 1 or y == 0 or y == row - 1:
            grid[y][x] = mountain
        elif x < margin or x >= col - margin or y < margin or y >= row - margin:
            grid[y][x] = forbid
        else:
            grid[y][x] = allow

grid[11][11] = castle
grid[11][12] = castle
grid[12][11] = castle
grid[12][12] = castle

grid_overlay = pygame.Surface((width_gameboard, height_gameboard), pygame.SRCALPHA)
white_grid = (255, 255, 255, 150)
for x in range(0, col):
    for y in range(0, row):
        if grid[y][x] == allow:
            pygame.draw.rect(grid_overlay, white_grid, (x * grid_size, y * grid_size, grid_size, grid_size), 1)

show_grid = False
player_group = pygame.sprite.Group()
enemy_group = pygame.sprite.Group()
bullet_group = pygame.sprite.Group()
spawn_group = pygame.sprite.Group()

castle_obj = ArrowTower(640, 360, is_castle=True)
player_group.add(castle_obj)

for _ in range(2):
    setup_spawn_point(spawn_group, "balanced")

game_time = 0.0
current_minute = 0
difficulty_multiplier = 1.0

# =====================================================================
# CAPÍTULO 8: BUCLE PRINCIPAL
# =====================================================================
while running:
    keys = pygame.key.get_pressed()
    time_scale = 1.0
    if keys[pygame.K_x]:
        time_scale = 4.0
    elif keys[pygame.K_z]:
        time_scale = 2.0

    mouseX, mouseY = pygame.mouse.get_pos()
    limitW = offsetX + (margin * grid_size)
    limitE = offsetX + (col - margin) * grid_size
    limitN = margin * grid_size
    limitS = (row - margin) * grid_size

    on_grid = limitW <= mouseX < limitE and limitN <= mouseY < limitS

    if on_grid:
        hoverCol = (mouseX - offsetX) // grid_size
        hoverRow = mouseY // grid_size
        if last_built_cell and last_built_cell != (hoverRow, hoverCol):
            last_built_cell = None

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.MOUSEBUTTONDOWN:
            if game_state == "PLAYING":
                if not on_grid:
                    if "menu_btn_rect" in locals() and menu_btn_rect.collidepoint(mouseX, mouseY):
                        game_state = "PAUSED"

                    rx_click = 1000
                    for i in range(4):
                        t_id = active_towers[i]
                        if t_id:
                            slot_rect = pygame.Rect(rx_click + 25 + (i * 60), 50, 50, 50)
                            if slot_rect.collidepoint(mouseX, mouseY):
                                current_tool = t_id if current_tool != t_id else None

                    wall_rect = pygame.Rect(rx_click + 25, 200, 50, 50)
                    if wall_rect.collidepoint(mouseX, mouseY):
                        current_tool = "wall" if current_tool != "wall" else None

                    sell_rect = pygame.Rect(rx_click + 40, 420, 200, 50)
                    if sell_rect.collidepoint(mouseX, mouseY):
                        current_tool = "sell" if current_tool != "sell" else None

                    rep_rect = pygame.Rect(rx_click + 40, 510, 200, 50)
                    if rep_rect.collidepoint(mouseX, mouseY):
                        current_tool = "repair" if current_tool != "repair" else None

            if game_state == "LEVEL_UP":
                for i, rect in enumerate(card_rects):
                    if rect.collidepoint(mouseX, mouseY):
                        if selected_card_idx == i:
                            chosen = level_up_options[i]

                            if chosen["type"] == "upgrade_tower":
                                t_id = chosen["id"]
                                old_lvl = tower_levels[t_id]
                                tower_levels[t_id] += 1
                                if old_lvl > 0:
                                    hp_buff = 1.0 + (passive_levels.get("health", 0) * 0.05) + meta_health
                                    old_max = int(TOWER_BASE_HP[old_lvl] * hp_buff)
                                    new_max = int(TOWER_BASE_HP[tower_levels[t_id]] * hp_buff)
                                    hp_delta = new_max - old_max
                                    for t in player_group:
                                        if type(t).__name__.lower().startswith(t_id) and "castle" not in type(
                                                t).__name__.lower():
                                            t_col = int((t.x - offsetX) // grid_size)
                                            t_row = int(t.y // grid_size)
                                            if (t_row, t_col) in structures_hp:
                                                structures_hp[(t_row, t_col)] += hp_delta
                                if tower_levels[t_id] == 1 and t_id not in unlocked_towers:
                                    unlocked_towers.append(t_id)
                                    for idx in range(4):
                                        if active_towers[idx] is None:
                                            active_towers[idx] = t_id
                                            break

                            elif chosen["type"] in ["unlock_passive", "upgrade_passive"]:
                                p_id = chosen["id"]

                                # Guardamos el multiplicador antiguo antes de tocar nada
                                old_hp_buff = 1.0 + (passive_levels.get("health", 0) * 0.05) + meta_health

                                if chosen["type"] == "unlock_passive":
                                    active_passives.append(p_id)
                                    passive_levels[p_id] = 1
                                else:
                                    passive_levels[p_id] += 1

                                # Solo recalculamos vidas si la carta era de salud
                                if p_id == "health":
                                    new_hp_buff = 1.0 + (passive_levels["health"] * 0.05) + meta_health

                                    # 1. Ajuste perfecto para el Castillo
                                    old_castle_max = int((100 + (player_level * 18)) * old_hp_buff)
                                    new_castle_max = int((100 + (player_level * 18)) * new_hp_buff)
                                    castle_max_hp = new_castle_max
                                    castle_hp += (new_castle_max - old_castle_max)

                                    # 2. Rellenar la "vida vacía" de Muros y Torres
                                    for coords in list(structures_hp.keys()):
                                        r, c = coords
                                        cell = grid[r][c]

                                        if cell == wall:
                                            old_max = int((25 + (player_level * 1.5)) * old_hp_buff)
                                            new_max = int((25 + (player_level * 1.5)) * new_hp_buff)
                                            structures_hp[coords] += (new_max - old_max)

                                        elif cell == turret:
                                            # Buscamos la torre exacta para saber su nivel actual
                                            t_obj = next((t for t in player_group if not getattr(t, "is_castle", False) and int((t.x - offsetX) // grid_size) == c and int(t.y // grid_size) == r), None)
                                            if t_obj:
                                                t_id = t_obj.tower_id
                                                lvl = max(1, tower_levels.get(t_id, 1))
                                                old_max = int(TOWER_BASE_HP[lvl] * old_hp_buff)
                                                new_max = int(TOWER_BASE_HP[lvl] * new_hp_buff)
                                                structures_hp[coords] += (new_max - old_max)

                            elif chosen["type"] == "heal":
                                castle_hp = min(castle_max_hp, castle_hp + (castle_max_hp // 2))
                            elif chosen["type"] == "gold":
                                player_gold += 50
                            elif chosen["type"] == "heal_20":
                                castle_hp = min(castle_max_hp, castle_hp + int(castle_max_hp * 0.2))
                            elif chosen["type"] == "gold_100":
                                player_gold += 100
                            elif chosen["type"] == "gems_5":
                                player_gems += 5

                            selected_card_idx = None
                            game_state = "PLAYING"
                        else:
                            selected_card_idx = i
                        break

            elif game_state == "PLAYING" and on_grid:
                if current_tool == "sell":
                    if grid[hoverRow][hoverCol] in [wall, turret]:
                        cell_type = grid[hoverRow][hoverCol]
                        coords = (hoverRow, hoverCol)
                        if coords in structures_hp:
                            current_hp = structures_hp[coords]
                            hp_buff = 1.0 + (passive_levels.get("health", 0) * 0.05) + meta_health

                            if cell_type == wall:
                                max_hp = int((25 + (player_level * 1.5)) * hp_buff)
                                total_value = min(50, 10 + int(player_level * 0.8))
                                target_obj = None
                            else:
                                target_obj = next((t for t in player_group if
                                                   not getattr(t, "is_castle", False) and int(
                                                       (t.x - offsetX) // grid_size) == hoverCol and int(
                                                       t.y // grid_size) == hoverRow), None)
                                if target_obj:
                                    t_id = target_obj.tower_id
                                    max_hp = int(TOWER_BASE_HP[max(1, tower_levels[t_id])] * hp_buff)
                                    total_value = TOWER_STATS[t_id][max(1, tower_levels[t_id])]["cost"]
                                else:
                                    max_hp = 1;
                                    total_value = 0

                            # Mates de Wall Street: Depreciación por daño y reembolso del 25%
                            current_value = total_value * (current_hp / max_hp)
                            player_gold += int(current_value * 0.25)

                            grid[hoverRow][hoverCol] = allow
                            del structures_hp[coords]

                            if cell_type == wall:
                                if coords in wall_masks: del wall_masks[coords]
                                update_neighbors_walls(hoverRow, hoverCol)
                            elif cell_type == turret and target_obj:
                                target_obj.kill()

                    elif (hoverRow, hoverCol) in ruin_masks:
                        del ruin_masks[(hoverRow, hoverCol)]
                        update_neighbors_walls(hoverRow, hoverCol)

                        fx_x = offsetX + (hoverCol * grid_size) + (grid_size // 2)
                        fx_y = (hoverRow * grid_size) + (grid_size // 2)
                        effects_group.add(Effect(fx_x, fx_y, wallsmoke_sheet, scale_size=60, fps=15, num_frames=7))

                elif current_tool == "repair":
                    if grid[hoverRow][hoverCol] in [wall, turret]:
                        cell_type = grid[hoverRow][hoverCol]
                        coords = (hoverRow, hoverCol)
                        if coords in structures_hp:
                            current_hp = structures_hp[coords]
                            hp_buff = 1.0 + (passive_levels.get("health", 0) * 0.05) + meta_health

                            if cell_type == wall:
                                max_hp = int((25 + (player_level * 1.5)) * hp_buff)
                                total_value = min(50, 10 + int(player_level * 0.8))
                            else:
                                target_obj = next((t for t in player_group if
                                                   not getattr(t, "is_castle", False) and int(
                                                       (t.x - offsetX) // grid_size) == hoverCol and int(
                                                       t.y // grid_size) == hoverRow), None)
                                if target_obj:
                                    t_id = target_obj.tower_id
                                    max_hp = int(TOWER_BASE_HP[max(1, tower_levels[t_id])] * hp_buff)
                                    total_value = TOWER_STATS[t_id][max(1, tower_levels[t_id])]["cost"]
                                else:
                                    max_hp = 1;
                                    total_value = 0

                            if current_hp < max_hp:
                                # Coste de reparación dinámico (75% del valor perdido)
                                current_value = total_value * (current_hp / max_hp)
                                repair_price = int((total_value - current_value) * 0.75)
                                if player_gold >= repair_price:
                                    player_gold -= repair_price
                                    structures_hp[coords] = max_hp

                elif grid[hoverRow][hoverCol] == allow:
                    hp_buff = 1.0 + (passive_levels.get("health", 0) * 0.05) + meta_health

                    if current_tool == "wall":
                        current_wall_cost = min(50, 10 + int(player_level * 0.8))
                        if player_gold >= current_wall_cost:
                            player_gold -= current_wall_cost
                            grid[hoverRow][hoverCol] = wall
                            structures_hp[(hoverRow, hoverCol)] = int((25 + (player_level * 1.5)) * hp_buff)

                            if (hoverRow, hoverCol) in ruin_masks:
                                del ruin_masks[(hoverRow, hoverCol)]

                            update_neighbors_walls(hoverRow, hoverCol)

                            posX_px = offsetX + (hoverCol * grid_size) + (grid_size // 2)
                            posY_px = (hoverRow * grid_size) + (grid_size // 2)
                            effects_group.add(Effect(posX_px, posY_px, dust_sheet, scale_size=55, fps=11))

                    elif current_tool in ["arrow", "fireball", "kunai", "laser", "lightning", "thorns"]:
                        lvl = tower_levels[current_tool]
                        stats = TOWER_STATS[current_tool][max(1, lvl)]
                        current_count = sum(1 for t in player_group if
                                            getattr(t, "tower_id", None) == current_tool and not getattr(t, "is_castle",
                                                                                                         False))

                        if current_count < stats["limit"]:
                            cost = stats["cost"]
                            if player_gold >= cost:
                                player_gold -= cost
                                grid[hoverRow][hoverCol] = turret
                                structures_hp[(hoverRow, hoverCol)] = int(TOWER_BASE_HP[max(1, lvl)] * hp_buff)

                                posX_px = offsetX + (hoverCol * grid_size) + (grid_size // 2)
                                posY_px = (hoverRow * grid_size) + (grid_size // 2)

                                if current_tool == "arrow":
                                    player_group.add(ArrowTower(posX_px, posY_px))
                                elif current_tool == "fireball":
                                    player_group.add(FireballTower(posX_px, posY_px))
                                elif current_tool == "kunai":
                                    player_group.add(KunaiTower(posX_px, posY_px))
                                elif current_tool == "laser":
                                    player_group.add(LaserTower(posX_px, posY_px))
                                elif current_tool == "lightning":
                                    player_group.add(LightningTower(posX_px, posY_px))
                                elif current_tool == "thorns":
                                    player_group.add(ThornsTower(posX_px, posY_px))

                                # --- CREAR LA ONDA EXPANSIVA ---
                                base_y = (hoverRow * grid_size) + grid_size
                                effects_group.add(TowerSmoke(posX_px, base_y, goes_right=False))  # Humo izquierdo
                                effects_group.add(TowerSmoke(posX_px, base_y, goes_right=True))  # Humo derecho

                                last_built_cell = (hoverRow, hoverCol)

        if event.type == pygame.MOUSEBUTTONUP:
            if game_state == "PAUSED":
                if "pause_rects" in globals() or "pause_rects" in locals():
                    for rect, opt in pause_rects:
                        if rect.collidepoint(mouseX, mouseY):
                            if opt == "Resume":
                                game_state = "PLAYING"
                            else:
                                print(f"You clicked {opt}. It's still a work in progress, patience.")

        if event.type == pygame.KEYDOWN:
            if game_state == "PLAYING":
                if event.key == pygame.K_g:
                    show_grid = not show_grid
                elif event.key == pygame.K_ESCAPE:
                    if current_tool is not None:
                        current_tool = None
                    else:
                        game_state = "PAUSED"
                elif event.key == controls["sell"]:
                    current_tool = "sell" if current_tool != "sell" else None
                elif event.key == controls["repair"]:
                    current_tool = "repair" if current_tool != "repair" else None
                elif event.key == controls["wall"]:
                    current_tool = "wall" if current_tool != "wall" else None
                elif event.key == controls["slot_1"] and active_towers[0]:
                    t = active_towers[0]
                    current_tool = t if current_tool != t else None
                elif event.key == controls["slot_2"] and active_towers[1]:
                    t = active_towers[1]
                    current_tool = t if current_tool != t else None
                elif event.key == controls["slot_3"] and active_towers[2]:
                    t = active_towers[2]
                    current_tool = t if current_tool != t else None
                elif event.key == controls["slot_4"] and active_towers[3]:
                    t = active_towers[3]
                    current_tool = t if current_tool != t else None
                elif event.key == controls["toggle_hp"]:
                    health_bars_mode = (health_bars_mode + 1) % 4
                    config["Settings"]["health_bars_mode"] = str(health_bars_mode)
                    with open(config_file, "w") as f:
                        config.write(f)
            elif game_state == "PAUSED":
                if event.key == pygame.K_ESCAPE:
                    game_state = "PLAYING"

    gameboard.fill("#222222")
    pygame.draw.rect(gameboard, "#000000", (offsetX, 0, width_gameboard, height_gameboard))

    for y in range(row):
        for x in range(col):
            posX = offsetX + (x * grid_size)
            posY = y * grid_size
            gameboard.blit(background_tile, (posX, posY))

    buildable_targets = [allow, castle, wall, turret]

    for y in range(row):
        for x in range(col):
            posX = offsetX + (x * grid_size)
            posY = y * grid_size
            cell = grid[y][x]

            if cell in buildable_targets:
                tile = get_tile_for_cell(x, y, buildable_targets, buildable_tiles, False)
                gameboard.blit(tile, (posX, posY))

                # --- PINTAMOS RUINAS SI EXISTEN (incluso debajo de torres) ---
                if (y, x) in ruin_masks:
                    mask = ruin_masks[(y, x)]
                    gameboard.blit(ruin_sprites[mask], (posX, posY))

                # --- PINTAMOS LOS MUROS SANOS ---
                if cell == wall:
                    mask = wall_masks.get((y, x), 0)
                    gameboard.blit(wall_sprites[mask], (posX, posY))

            elif cell == mountain:
                tile = get_tile_for_cell(x, y, [mountain], mountain_tiles, True)
                gameboard.blit(tile, (posX, posY))

    if show_grid:
        gameboard.blit(grid_overlay, (offsetX, 0))

    # === 1. PINTAMOS EL SUELO (SOLO SI EL RATÓN ESTÁ EN EL MAPA) ===
    if on_grid and game_state == "PLAYING":
        posX_trans = offsetX + (hoverCol * grid_size)
        posY_trans = hoverRow * grid_size
        current_cell = grid[hoverRow][hoverCol]

        if current_cell != castle:
            surface_trans = pygame.Surface((grid_size, grid_size), pygame.SRCALPHA)
            if current_tool == "sell":
                if current_cell in [wall, turret] or (hoverRow, hoverCol) in ruin_masks:
                    surface_trans.fill((255, 0, 0, 150))
                else:
                    surface_trans.fill((255, 0, 0, 40))
            elif current_tool is not None and current_cell != allow:
                surface_trans.fill((255, 0, 0, 70))
            else:
                surface_trans.fill((255, 255, 255, 40))
            gameboard.blit(surface_trans, (posX_trans, posY_trans))

    # === 2. PINTAMOS ENTIDADES ===
    for bullet in bullet_group:
        if type(bullet).__name__ == "ThornsArea":
            gameboard.blit(bullet.image, bullet.rect)

    living_entities = list(player_group) + list(enemy_group)
    for bullet in bullet_group:
        if type(bullet).__name__ in ["IceBeamVisual", "LightningVisual"]:
            living_entities.append(bullet)

    living_entities.sort(key=lambda entity: entity.rect.bottom)

    for entity in living_entities:
        gameboard.blit(entity.image, entity.rect)

    for bullet in bullet_group:
        if type(bullet).__name__ not in ["ThornsArea", "IceBeamVisual", "LightningVisual"]:
            gameboard.blit(bullet.image, bullet.rect)

    effects_group.draw(gameboard)

    # === 3. PINTAMOS LA TORRE/MURO FANTASMA Y TEXTO LÍMITE ===
    if on_grid and game_state == "PLAYING" and last_built_cell != (hoverRow, hoverCol):
        posX_trans = offsetX + (hoverCol * grid_size)
        posY_trans = hoverRow * grid_size
        current_cell = grid[hoverRow][hoverCol]

        if current_tool in preview_towers:
            tower_img = preview_towers[current_tool].copy()

            if current_tool == "wall":
                can_build = (current_cell == allow) and (player_gold >= min(50, 10 + int(player_level * 0.8)))
                shift_y = 0  # El muro no necesita elevarse
                limit_text = None
            else:
                lvl = max(1, tower_levels[current_tool])
                stats = TOWER_STATS[current_tool][lvl]
                limit = stats["limit"]
                cost = stats["cost"]
                current_count = sum(1 for t in player_group if
                                    getattr(t, "tower_id", None) == current_tool and not getattr(t, "is_castle", False))
                can_build = (current_cell == allow) and (current_count < limit) and (player_gold >= cost)
                shift_y = 30  # Las torres sí
                limit_text = f"{current_count}/{limit}"

            if not can_build:
                # El trucazo del rojo puro
                tower_img.fill((0, 255, 255, 0), special_flags=pygame.BLEND_RGB_SUB)

            gameboard.blit(tower_img, (posX_trans, posY_trans - shift_y))

            # Dibujamos el texto solo si es una torre
            if limit_text:
                text_color = "white" if current_count < limit else "red"
                outline_surf = ui_font_medium.render(limit_text, True, "black")
                for dx, dy in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
                    gameboard.blit(outline_surf, (mouseX + 15 + dx, mouseY + 15 + dy))

                text_surf = ui_font_medium.render(limit_text, True, text_color)
                gameboard.blit(text_surf, (mouseX + 15, mouseY + 15))

    # === 4. BARRAS DE VIDA Y PRECIO EN EL CURSOR (SELL/REPAIR) ===
    hp_cells_to_draw = set()
    hovered_struct = None

    if on_grid and game_state == "PLAYING":
        if grid[hoverRow][hoverCol] in [wall, turret] and (hoverRow, hoverCol) in structures_hp:
            # Siempre se muestra si pasamos el ratón sin herramienta, con "sell" o "repair"
            if current_tool in [None, "sell", "repair"]:
                hovered_struct = (hoverRow, hoverCol)
                hp_cells_to_draw.add(hovered_struct)

        # Rellenar lista según el modo del config
        for r in range(row):
            for c in range(col):
                if grid[r][c] in [wall, turret] and (r, c) in structures_hp:
                    is_tower = (grid[r][c] == turret)
                    recently_damaged = (r, c) in damage_timers

                    if health_bars_mode == 0 and is_tower and recently_damaged:
                        hp_cells_to_draw.add((r, c))
                    elif health_bars_mode == 1 and recently_damaged:
                        hp_cells_to_draw.add((r, c))
                    elif health_bars_mode == 2 and is_tower:
                        hp_cells_to_draw.add((r, c))

    for (r, c) in hp_cells_to_draw:
        current_hp = structures_hp[(r, c)]
        hp_buff = 1.0 + (passive_levels.get("health", 0) * 0.05) + meta_health
        max_hp = 1
        cell = grid[r][c]
        t_obj = None  # Salvavidas para que no falle luego

        if cell == wall:
            max_hp = int((25 + (player_level * 1.5)) * hp_buff)
        elif cell == turret:
            t_obj = next((t for t in player_group if
                          not getattr(t, "is_castle", False) and int((t.x - offsetX) // grid_size) == c and int(
                              t.y // grid_size) == r), None)
            if t_obj:
                max_hp = int(TOWER_BASE_HP[max(1, tower_levels.get(t_obj.tower_id, 1))] * hp_buff)

        bar_w = 40
        bx = offsetX + (c * grid_size) + (grid_size // 2) - (bar_w // 2)

        # Movemos la barra a la parte inferior de la casilla (grid_size es 30, barra mide 6)
        by = (r * grid_size) + grid_size - 15

        # Efecto de desvanecimiento suave si la barra va a desaparecer
        alpha = 255
        if health_bars_mode in [0, 1] and (r, c) != hovered_struct and (r, c) in damage_timers:
            timer = damage_timers[(r, c)]
            if timer < 1.0:
                alpha = int(255 * timer)

        if alpha < 255:
            hp_surf_bar = pygame.Surface((bar_w, 6), pygame.SRCALPHA)
            pygame.draw.rect(hp_surf_bar, (255, 0, 0, alpha), (0, 0, bar_w, 6))
            pygame.draw.rect(hp_surf_bar, (0, 255, 0, alpha),
                             (0, 0, max(0, min(bar_w, int((current_hp / max_hp) * bar_w))), 6))
            pygame.draw.rect(hp_surf_bar, (0, 0, 0, alpha), (0, 0, bar_w, 6), 1)
            gameboard.blit(hp_surf_bar, (bx, by))
        else:
            pygame.draw.rect(gameboard, "red", (bx, by, bar_w, 6))
            pygame.draw.rect(gameboard, "green",
                             (bx, by, max(0, min(bar_w, int((current_hp / max_hp) * bar_w))), 6))
            pygame.draw.rect(gameboard, "black", (bx, by, bar_w, 6), 1)

        # Si tenemos el ratón encima, dibujamos el texto "93/100" y los costes
        if (r, c) == hovered_struct:
            hp_str = f"{int(current_hp)}/{int(max_hp)}"
            hp_surf = ui_font_small.render(hp_str, True, "white")

            text_y = by - 14
            text_x = bx + (bar_w // 2) - (hp_surf.get_width() // 2)

            for dx, dy in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
                gameboard.blit(ui_font_small.render(hp_str, True, "black"), (text_x + dx, text_y + dy))
            gameboard.blit(hp_surf, (text_x, text_y))

            # --- NUEVO: CÁLCULO DE VALORES DE MERCADO ---
            total_value = 0
            if cell == wall:
                total_value = min(50, 10 + int(player_level * 0.8))
            elif cell == turret and t_obj:
                total_value = TOWER_STATS[t_obj.tower_id][max(1, tower_levels.get(t_obj.tower_id, 1))]["cost"]

            current_value = total_value * (current_hp / max_hp)
            sell_price = int(current_value * 0.25)
            repair_price = int((total_value - current_value) * 0.75)

            action_text = ""
            color_text = "white"
            if current_tool == "sell":
                action_text = f"+{sell_price} G"
                color_text = "yellow"
            elif current_tool == "repair":
                action_text = "Max HP" if current_hp >= max_hp else f"-{repair_price} G"
                color_text = "gray" if current_hp >= max_hp else "red"

            if action_text:
                for dx, dy in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
                    gameboard.blit(ui_font_medium.render(action_text, True, "black"),
                                   (mouseX + 15 + dx, mouseY + 15 + dy))
                gameboard.blit(ui_font_medium.render(action_text, True, color_text), (mouseX + 15, mouseY + 15))

    pygame.draw.rect(gameboard, "#222222", (0, 0, offsetX, 720))
    pygame.draw.rect(gameboard, "#222222", (offsetX + width_gameboard, 0, 1280 - (offsetX + width_gameboard), 720))

    clock_rect = pygame.Rect(75, 35, 120, 75)
    draw_paper(gameboard, special_paper_sheet, clock_rect)

    time_str = f"{current_minute:02d}:{int(game_time % 60):02d}"
    time_surf = ui_font_large.render(time_str, True, "white")
    text_x = clock_rect.centerx - time_surf.get_width() // 2
    text_y = (clock_rect.centery - time_surf.get_height() // 2) + 4

    gameboard.blit(time_surf, (text_x, text_y))

    hp_ratio = max(0, castle_hp / castle_max_hp)
    draw_bar(gameboard, 25, 140, 220, 35, hp_ratio, big_bar_base, big_bar_fill)
    hp_text = ui_font_medium.render(f"HP: {int(castle_hp)}/{castle_max_hp}", True, "white")
    gameboard.blit(hp_text, (135 - hp_text.get_width() // 2, 147))

    xp_ratio = min(1, player_xp / xp_to_next_level)
    draw_bar(gameboard, 40, 190, 190, 25, xp_ratio, small_bar_base, small_bar_fill)
    xp_text = ui_font_small.render(f"Lvl: {player_level}", True, "white")
    gameboard.blit(xp_text, (135 - xp_text.get_width() // 2, 195))

    menu_btn_rect = pygame.Rect(40, 600, 200, 50)
    is_menu_pressed = keys[pygame.K_ESCAPE] or (
                pygame.mouse.get_pressed()[0] and menu_btn_rect.collidepoint(mouseX, mouseY))
    draw_action_btn(40, 600, 200, 50, "esc", "Menu", is_pressed=is_menu_pressed)

    rx = 1000
    for i in range(4):
        slot_x = rx + 25 + (i * 60)
        slot_y = 50
        key_str = pygame.key.name(controls[f"slot_{i + 1}"])
        t_id = active_towers[i]

        if t_id:
            is_pressed = (current_tool == t_id)
            lvl = max(1, tower_levels[t_id])
            cost = TOWER_STATS[t_id][lvl]["cost"]
            draw_slot(slot_x, slot_y, 50, key_str, cost, is_pressed=is_pressed, t_id=t_id)
        else:
            draw_slot(slot_x, slot_y, 50, key_str, None, is_pressed=False)

        p_size = 36
        p_spacing = 6
        start_px = rx + 15
        for i in range(6):
            slot_x = start_px + (i * (p_size + p_spacing))
            gameboard.blit(pygame.transform.scale(btn_small_img, (p_size, p_size)), (slot_x, 140))
            if i < len(active_passives):
                p_id = active_passives[i]
                lvl = passive_levels[p_id]
                pygame.draw.rect(gameboard, "#3b2f2f", (slot_x + 4, 144, p_size - 8, p_size - 8), border_radius=4)
                initial = p_id[0].upper()
                txt_surf = ui_font_small.render(f"{initial}{lvl}", True, "yellow")
                txt_x = slot_x + (p_size // 2) - (txt_surf.get_width() // 2)
                txt_y = 140 + (p_size // 2) - (txt_surf.get_height() // 2)
                gameboard.blit(txt_surf, (txt_x, txt_y))

        current_wall_cost = min(50, 10 + int(player_level * 0.8))
        wall_key = pygame.key.name(controls["wall"])
        is_wall_pressed = (current_tool == "wall") or keys[controls["wall"]]
        draw_slot(rx + 25, 200, 50, wall_key, current_wall_cost, is_pressed=is_wall_pressed, t_id="wall")

        draw_ribbon(gameboard, rx + 100, 210, 140, 40, ribbon_sheet, rw=0)
        gold_surf = ui_font_large.render(f"{player_gold} G", True, "black")
        gameboard.blit(gold_surf, (rx + 170 - gold_surf.get_width() // 2, 215))

        repair_all_cost = int((castle_max_hp - castle_hp) * 2)
        sell_key = pygame.key.name(controls["sell"])
        rep_key = pygame.key.name(controls["repair"])
        rep_all_key = pygame.key.name(controls["repair_all"])

        is_sell_pressed = (current_tool == "sell")
        draw_action_btn(rx + 40, 420, 200, 50, sell_key, "Demolish", is_pressed=is_sell_pressed)

        is_rep_pressed = (current_tool == "repair")
        draw_action_btn(rx + 40, 510, 200, 50, rep_key, "Repair", is_pressed=is_rep_pressed)

        rep_all_rect = pygame.Rect(rx + 40, 600, 200, 50)
        is_rep_all_pressed = keys[controls["repair_all"]] or (
                    rep_all_rect.collidepoint(mouseX, mouseY) and pygame.mouse.get_pressed()[0])
        draw_action_btn(rx + 40, 600, 200, 50, rep_all_key, "Repair All", repair_all_cost,
                        is_pressed=is_rep_all_pressed)

    if game_state == "GAME_OVER":
        overlay = pygame.Surface((1280, 720), pygame.SRCALPHA)
        overlay.fill((50, 0, 0, 200))
        gameboard.blit(overlay, (0, 0))

        title_text = ui_font_large.render("DEFEAT!", True, "red")
        gameboard.blit(title_text, (640 - title_text.get_width() // 2, 250))
        info_text = ui_font_medium.render(f"You survived for {current_minute} minutes and {int(game_time % 60)} seconds.",
                                          True, "white")
        gameboard.blit(info_text, (640 - info_text.get_width() // 2, 320))
        exit_text = ui_font_small.render("Close the window to exit.", True, "gray")
        gameboard.blit(exit_text, (640 - exit_text.get_width() // 2, 400))

    elif game_state == "LEVEL_UP":
        overlay = pygame.Surface((1280, 720), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        gameboard.blit(overlay, (0, 0))

        card_width = 220
        card_height = 300
        spacing = 40
        start_x = offsetX + (width_gameboard - (card_width * 3 + spacing * 2)) // 2
        start_y = 200

        card_rects = []
        title_text = ui_font_large.render("LEVEL UP! CHOOSE A REWARD", True, "yellow")
        gameboard.blit(title_text, (640 - title_text.get_width() // 2, 100))

        for i, card in enumerate(level_up_options):
            cx = start_x + i * (card_width + spacing)
            cy = start_y
            rect = pygame.Rect(cx, cy, card_width, card_height)
            card_rects.append(rect)

            pygame.draw.rect(gameboard, "#112233", rect)
            if selected_card_idx == i:
                pygame.draw.rect(gameboard, "white", rect, 5)
            else:
                pygame.draw.rect(gameboard, "#445566", rect, 2)

            text_surf = ui_font_medium.render(card["title"], True, "white")
            gameboard.blit(text_surf, (cx + 10, cy + 20))

            if "desc" in card:
                desc_rect = pygame.Rect(cx + 10, cy + 60, card_width - 20, card_height - 80)
                draw_text_wrapped(gameboard, card["desc"], ui_font_small, "lightgray", desc_rect)

    elif game_state == "PAUSED":
        overlay = pygame.Surface((1280, 720), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        gameboard.blit(overlay, (0, 0))

        draw_ribbon(gameboard, 640 - 150, 120, 300, 80, big_ribbon_sheet, rw=0, rows_total=5)
        title_text = ui_font_large.render("MENU", True, "white")
        gameboard.blit(title_text, (640 - title_text.get_width() // 2, 145))

        menu_opts = ["Resume", "Restart", "Settings", "Quit"]
        pause_rects = []
        for i, opt in enumerate(menu_opts):
            btn_y = 250 + i * 80
            btn_rect = pygame.Rect(640 - 100, btn_y, 200, 60)
            pause_rects.append((btn_rect, opt))

            is_hover = btn_rect.collidepoint(mouseX, mouseY) and pygame.mouse.get_pressed()[0]
            current_y = btn_rect.y + 4 if is_hover else btn_rect.y
            current_h = btn_rect.height - 4 if is_hover else btn_rect.height
            img = btn_wide_pressed_img if is_hover else btn_wide_img

            draw_9_slice_button(gameboard, img, pygame.Rect(btn_rect.x, current_y, btn_rect.width, current_h),
                                edge_px=14)
            y_off = 4 if is_hover else 0
            opt_surf = ui_font_medium.render(opt, True, "black")
            gameboard.blit(opt_surf,
                           (640 - opt_surf.get_width() // 2, btn_y + 30 - opt_surf.get_height() // 2 - 4 + y_off))

    screensize = screen.get_size()
    rescaled_gameboard = pygame.transform.scale(gameboard, screensize)
    screen.blit(rescaled_gameboard, (0, 0))

    pygame.display.flip()
    dt = clock.tick(60) / 1000

    if game_state == "PLAYING":
        game_time += dt * time_scale
        current_minute = int(game_time // 60)
        difficulty_multiplier = round(1 + (current_minute / 8) ** 1.8, 2)

        regen_lvl = passive_levels.get("regen", 0)
        if regen_lvl > 0:
            castle_hp = min(castle_max_hp, castle_hp + (castle_max_hp * (0.01 * regen_lvl) * dt * time_scale))

        if len(spawn_schedule) > 0:
            next_spawn_time, next_spawn_type = spawn_schedule[0]
            if game_time >= next_spawn_time:
                setup_spawn_point(spawn_group, next_spawn_type)
                spawn_schedule.pop(0)

        current_weight = sum(ENEMY_WEIGHTS.get(type(e).__name__, 1.0) for e in enemy_group)
        active_portals = len(spawn_group)

        if game_time >= 1050:
            population_cap = 9999
            spawn_cooldown_multiplier = 0.3
        else:
            population_cap = (15 + (current_minute * 2.0)) * max(1, active_portals)
            spawn_cooldown_multiplier = 1.0

        current_pool_key = max(k for k in WAVE_POOLS.keys() if k <= current_minute)
        current_pool = WAVE_POOLS[current_pool_key]

        spawn_group.update(dt * time_scale, enemy_group, grid, offsetX, grid_size, current_weight, population_cap,
                           current_pool, spawn_cooldown_multiplier)
        enemy_group.update(dt * time_scale, grid, enemy_group=enemy_group, structures_hp=structures_hp,
                           passive_levels=passive_levels, thorns_values=THORNS_VALUES)

        # --- DETECTOR DE DAÑO PARA MOSTRAR BARRAS ---
        for coords, hp in structures_hp.items():
            if coords in previous_structures_hp and hp < previous_structures_hp[coords]:
                damage_timers[coords] = 4

        for coords in list(damage_timers.keys()):
            damage_timers[coords] -= dt * time_scale
            if damage_timers[coords] <= 0:
                del damage_timers[coords]

        # --- DETECTOR DE ESTRUCTURAS ROTAS O VENDIDAS ---
        for coords in previous_structures_hp.keys():
            if coords not in structures_hp:
                fx_x = offsetX + (coords[1] * grid_size) + (grid_size // 2)
                fx_y = (coords[0] * grid_size) + (grid_size // 2)

                # Comprobamos qué era antes de ser borrado
                if previous_structures_types.get(coords) == wall:
                    # Humo de muro (dust_sheet es tu breaksmoke)
                    effects_group.add(Effect(fx_x, fx_y, dust_sheet, scale_size=55, fps=15))
                else:
                    # Humo de torre
                    effects_group.add(Effect(fx_x, fx_y, dust_sheet, scale_size=100, fps=15))

        # Actualizamos las memorias para el siguiente frame
        previous_structures_hp = structures_hp.copy()
        previous_structures_types = {coords: grid[coords[0]][coords[1]] for coords in structures_hp.keys()}

        # --- LIMPIEZA DE MUROS DESTRUIDOS Y CREACIÓN DE RUINAS ---
        broken_walls = []
        for (r, c) in list(wall_masks.keys()):
            if grid[r][c] != wall:
                broken_walls.append((r, c))

        for (r, c) in broken_walls:
            del wall_masks[(r, c)]
            ruin_masks[(r, c)] = 0  # Valor temporal para que se registre
            update_ruin_masks(r, c)  # Calcula su forma real o la borra si da 0
            update_neighbors_walls(r, c)

        for enemy in enemy_group:
            if enemy.rect.colliderect(castle_obj.rect):
                if not hasattr(enemy, "castle_attack_timer"):
                    enemy.castle_attack_timer = 1.0
                enemy.castle_attack_timer += dt * time_scale
                if enemy.castle_attack_timer >= 1.0:
                    castle_hp -= getattr(enemy, "base_damage", 5)
                    enemy.castle_attack_timer = 0.0

        if castle_hp <= 0:
            castle_hp = 0
            game_state = "GAME_OVER"

        collisions = pygame.sprite.groupcollide(enemy_group, enemy_group, False, False)
        for enemy, others in collisions.items():
            push_margin = margin - 2
            e_col = int((enemy.pos.x - offsetX) // grid_size)
            e_row = int(enemy.pos.y // grid_size)

            if e_col < push_margin or e_col >= col - push_margin or e_row < push_margin or e_row >= row - push_margin:
                continue

            push_final = pygame.math.Vector2(0, 0)
            for other in others:
                if other == enemy: continue
                distance = enemy.pos.distance_to(other.pos)
                if distance < (enemy.radius + other.radius):
                    if distance == 0:
                        enemy.pos += pygame.math.Vector2(random.uniform(-1, 1), random.uniform(-1, 1))
                        continue
                    push_final += (enemy.pos - other.pos).normalize() * 60.0

            if push_final.length() > 0:
                if enemy.is_attacking:
                    tangent = pygame.math.Vector2(-enemy.dir_norm.y, enemy.dir_norm.x)
                    dot_product = push_final.dot(tangent)
                    if abs(dot_product) < 5:
                        dot_product += random.choice([-20.0, 20.0])
                    enemy.pos += tangent * dot_product * dt
                else:
                    enemy.pos += push_final.normalize() * 40.0 * dt
            enemy.rect.center = (round(enemy.pos.x), round(enemy.pos.y))

        for t in player_group:
            if not getattr(t, "is_castle", False) and hasattr(t, "x"):
                t_col = int((t.x - offsetX) // grid_size)
                t_row = int(t.y // grid_size)
                if grid[t_row][t_col] != turret:
                    t.kill()

        player_group.update(dt * time_scale, enemy_group, bullet_group, tower_levels, passive_levels)
        bullet_group.update(dt * time_scale)
        effects_group.update(dt * time_scale)

        for bullet in bullet_group:
            if not hasattr(bullet, "pierce"):
                continue
            bx = int((bullet.pos.x - offsetX) // grid_size)
            by = int(bullet.pos.y // grid_size)
            if 0 <= bx < col and 0 <= by < row:
                if grid[by][bx] == mountain:
                    if hasattr(bullet, "aoe_radius"):
                        exp = Effect(bullet.rect.centerx, bullet.rect.centery, explosion_sheet,
                                     int(bullet.aoe_radius * 3.5), fps=20)
                        effects_group.add(exp)
                    bullet.kill()

        hits = pygame.sprite.groupcollide(bullet_group, enemy_group, False, False)
        for arrow, enemies_hit in hits.items():
            if not hasattr(arrow, "pierce"):
                continue

            for enemy in enemies_hit:
                if enemy not in getattr(arrow, "hit_enemies", set()):
                    arrow.hit_enemies.add(enemy)
                    dmg_buff = 1.0 + (passive_levels.get("damage", 0) * 0.05)
                    final_damage = arrow.damage * dmg_buff

                    if random.random() < (passive_levels.get("crit", 0) * 0.10):
                        final_damage *= 1.5

                    if hasattr(arrow, "aoe_radius"):
                        exp = Effect(arrow.rect.centerx, arrow.rect.centery, explosion_sheet,
                                     int(arrow.aoe_radius * 3.5), fps=20)
                        effects_group.add(exp)
                        for e in enemy_group:
                            if pygame.math.Vector2(arrow.rect.center).distance_to(e.pos) <= arrow.aoe_radius:
                                e.take_damage(final_damage)
                    else:
                        enemy.take_damage(final_damage)

                    arrow.pierce -= 1
                    if arrow.pierce <= 0:
                        arrow.kill()
                        break

        for enemy in list(enemy_group):
            if enemy.health <= 0:
                gold_buff = 1.0 + (passive_levels.get("gold", 0) * 0.05)
                xp_buff = 1.0 + (passive_levels.get("xp", 0) * 0.05)
                player_gold += int(enemy.gold_value * gold_buff)
                player_xp += int(enemy.xp_value * xp_buff * difficulty_multiplier)
                enemy.kill()

                if player_xp >= xp_to_next_level:
                    player_xp -= xp_to_next_level
                    player_level += 1
                    hp_buff = 1.0 + (passive_levels.get("health", 0) * 0.05) + meta_health
                    new_castle_max = int((100 + (player_level * 18)) * hp_buff)
                    castle_hp += (new_castle_max - castle_max_hp)
                    castle_max_hp = new_castle_max

                    old_wall_max = int((25 + ((player_level - 1) * 1.5)) * hp_buff)
                    new_wall_max = int((25 + (player_level * 1.5)) * hp_buff)
                    wall_delta = new_wall_max - old_wall_max

                    for r in range(row):
                        for c in range(col):
                            if grid[r][c] == wall and (r, c) in structures_hp:
                                structures_hp[(r, c)] += wall_delta

                    if player_level < 51:
                        xp_to_next_level += 15 + (player_level * 2)
                    else:
                        xp_to_next_level = int(xp_to_next_level * 2.5)

                    game_state = "LEVEL_UP"
                    level_up_options = get_level_up_cards()

pygame.quit()