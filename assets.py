import pygame
import os
import sys
from graphics import extract_sprite
from gamedata import wall_mask_map

class GameAssets:
    def __init__(self):
        # Declaramos todo vacío primero
        self.ui_font_large = None
        self.ui_font_medium = None
        self.ui_font_small = None

        self.ui_tower_icons = {}
        self.preview_towers = {}

        self.wall_sheet = None
        self.ruin_sheet = None
        self.ruin_sprites = {}
        self.wall_sprites = {}

        self.color2_sheet = None
        self.color4_sheet = None
        self.elevation_sheet = None

        self.explosion_sheet = None
        self.dust_sheet = None
        self.smoke_sheet = None
        self.wallsmoke_sheet = None

        self.btn_sheet = None
        self.ribbon_sheet = None
        self.special_paper_sheet = None
        self.big_bar_base = None
        self.big_bar_fill = None
        self.small_bar_base = None
        self.small_bar_fill = None
        self.big_ribbon_sheet = None

        self.btn_small_img = None
        self.btn_small_pressed_img = None
        self.btn_wide_img = None
        self.btn_wide_pressed_img = None

        self.keys_sheet = None
        self.cursor_img = None
        self.panel_bg = None
        self.bg_menu = None

        self.chests_sheet = None
        self.coins_sheet = None

    def load_all(self, use_legible_font):
        # 1. Fuentes
        if use_legible_font:
            self.ui_font_large = pygame.font.SysFont("Arial", 28, bold=True)
            self.ui_font_medium = pygame.font.SysFont("Arial", 20, bold=True)
            self.ui_font_small = pygame.font.SysFont("Arial", 14, bold=True)
        else:
            font_path = os.path.join("Assets", "alagard.ttf")
            try:
                self.ui_font_large = pygame.font.Font(font_path, 32)
                self.ui_font_medium = pygame.font.Font(font_path, 22)
                self.ui_font_small = pygame.font.Font(font_path, 16)
            except FileNotFoundError:
                print("Warning: Assets/alagard.ttf not found. Using Arial as fallback.")
                self.ui_font_large = pygame.font.SysFont("Arial", 28, bold=True)
                self.ui_font_medium = pygame.font.SysFont("Arial", 20, bold=True)
                self.ui_font_small = pygame.font.SysFont("Arial", 14, bold=True)

        # 2. Iconos y Torres UI
        for tower_name in ["arrow", "fireball", "kunai", "laser", "lightning", "thorns"]:
            img_path = os.path.join("Assets", "Sprites", "Player", f"{tower_name}tower.png")
            try:
                raw_img = pygame.image.load(img_path).convert_alpha()
            except FileNotFoundError:
                try:
                    raw_img = pygame.image.load(os.path.join("Assets", "Sprites", "Player", "fallbacktower.png")).convert_alpha()
                except FileNotFoundError:
                    raw_img = pygame.Surface((30, 60))
                    raw_img.fill("magenta")

            icon_surf = pygame.Surface((30, 40), pygame.SRCALPHA)
            icon_surf.blit(raw_img, (0, 0), (0, 0, 30, 40))
            self.ui_tower_icons[tower_name] = pygame.transform.scale(icon_surf, (27, 36))

            img_copy = raw_img.copy()
            img_copy.set_alpha(150)
            self.preview_towers[tower_name] = img_copy

        # 3. Tiles (Suelo y Montañas)
        try:
            self.color2_sheet = pygame.image.load(os.path.join("Assets", "Sprites", "Tiles", "Tilemap_color2.png")).convert_alpha()
            self.color4_sheet = pygame.image.load(os.path.join("Assets", "Sprites", "Tiles", "Tilemap_color4.png")).convert_alpha()
            self.elevation_sheet = pygame.image.load(os.path.join("Assets", "Sprites", "Tiles", "Tilemap_Elevation.png")).convert_alpha()
        except FileNotFoundError:
            print("ERROR: Missing terrain textures.")
            pygame.quit()
            sys.exit()

        # 4. Muros y Ruinas
        try:
            self.wall_sheet = pygame.image.load(os.path.join("Assets", "Sprites", "Tiles", "walls.png")).convert_alpha()
        except FileNotFoundError:
            self.wall_sheet = pygame.Surface((120, 120), pygame.SRCALPHA)
            self.wall_sheet.fill("brown")

        try:
            self.ruin_sheet = pygame.image.load(os.path.join("Assets", "Sprites", "Tiles", "ruins.png")).convert_alpha()
        except FileNotFoundError:
            self.ruin_sheet = pygame.Surface((120, 120), pygame.SRCALPHA)

        for mask, (c, r) in wall_mask_map.items():
            if mask != 0:
                self.ruin_sprites[mask] = extract_sprite(self.ruin_sheet, c, r, 4, 4, crop=False)
            self.wall_sprites[mask] = extract_sprite(self.wall_sheet, c, r, 4, 4, crop=False)

        self.ui_tower_icons["wall"] = pygame.transform.scale(self.wall_sprites[10], (30, 30))
        self.preview_towers["wall"] = self.wall_sprites[10].copy()
        self.preview_towers["wall"].set_alpha(150)

        # 5. Efectos Visuales
        self.explosion_sheet = pygame.image.load(os.path.join("Assets", "Sprites", "Effects", "Explosion_01.png")).convert_alpha()
        self.dust_sheet = pygame.image.load(os.path.join("Assets", "Sprites", "Effects", "breaksmoke.png")).convert_alpha()
        self.smoke_sheet = pygame.image.load(os.path.join("Assets", "Sprites", "Effects", "buildsmoke.png")).convert_alpha()
        self.wallsmoke_sheet = pygame.image.load(os.path.join("Assets", "Sprites", "Effects", "wallsmoke.png")).convert_alpha()
        self.chests_sheet = pygame.image.load(os.path.join("Assets", "Sprites", "Effects", "chests.png")).convert_alpha()
        self.coins_sheet = pygame.image.load(os.path.join("Assets", "Sprites", "Effects", "coins.png")).convert_alpha()

        # 6. UI General
        ui_path = os.path.join("Assets", "UI")
        try:
            self.btn_sheet = pygame.image.load(os.path.join(ui_path, "Button_Hover.png")).convert_alpha()
            self.ribbon_sheet = pygame.image.load(os.path.join(ui_path, "SmallRibbons.png")).convert_alpha()
            self.special_paper_sheet = pygame.image.load(os.path.join(ui_path, "SpecialPaper.png")).convert_alpha()
            self.big_bar_base = pygame.image.load(os.path.join(ui_path, "BigBar_Base.png")).convert_alpha()
            self.big_bar_fill = pygame.image.load(os.path.join(ui_path, "BigBar_Fill.png")).convert_alpha()
            self.small_bar_base = pygame.image.load(os.path.join(ui_path, "SmallBar_Base.png")).convert_alpha()
            self.small_bar_fill = pygame.image.load(os.path.join(ui_path, "SmallBar_Fill.png")).convert_alpha()
            self.big_ribbon_sheet = pygame.image.load(os.path.join(ui_path, "BigRibbons.png")).convert_alpha()
            speedup_sheet = pygame.image.load(os.path.join(ui_path, "speedup.png")).convert_alpha()
            self.ui_tower_icons["speed_z"] = pygame.transform.scale(speedup_sheet.subsurface((0, 0, 32, 32)), (26, 26))
            self.ui_tower_icons["speed_x"] = pygame.transform.scale(speedup_sheet.subsurface((32, 0, 32, 32)), (26, 26))
        except FileNotFoundError as e:
            print(f"UI ERROR: Image {e} not found.")
            pygame.quit()
            sys.exit()

        self.btn_small_img = extract_sprite(self.btn_sheet, 0, 0, 2, 3, crop=True)
        self.btn_small_pressed_img = extract_sprite(self.btn_sheet, 1, 0, 2, 3, crop=True)
        self.btn_wide_img = extract_sprite(self.btn_sheet, 0, 1, 2, 3, crop=True)
        self.btn_wide_pressed_img = extract_sprite(self.btn_sheet, 1, 1, 2, 3, crop=True)

        try:
            self.keys_sheet = pygame.image.load(os.path.join(ui_path, "Keyboard Letters and Symbols.png")).convert_alpha()
        except FileNotFoundError:
            self.keys_sheet = None

        try:
            cursor = pygame.image.load(os.path.join(ui_path, "Cursor.png")).convert_alpha()
            self.cursor_img = pygame.transform.scale(cursor, (32, 32))
        except FileNotFoundError:
            self.cursor_img = None

        try:
            panel_img = pygame.image.load(os.path.join(ui_path, "Panels.png")).convert()
            orig_w, orig_h = panel_img.get_size()
            new_w = 280
            new_h = int(orig_h * (new_w / orig_w))
            scaled_panel = pygame.transform.scale(panel_img, (new_w, new_h))
            self.panel_bg = pygame.Surface((280, 720))
            for y in range(0, 720, new_h):
                self.panel_bg.blit(scaled_panel, (0, y))
        except FileNotFoundError:
            self.panel_bg = None

        try:
            bg = pygame.image.load(os.path.join(ui_path, "landscape.png")).convert()
            self.bg_menu = pygame.transform.scale(bg, (1280, 720))
        except FileNotFoundError:
            self.bg_menu = pygame.Surface((1280, 720))
            self.bg_menu.fill("#222222")

            # --- BOTONES DE VELOCIDAD ---
            try:
                speed_sheet = pygame.image.load(os.path.join("Assets", "UI", "speedup.png")).convert_alpha()

                icon_z = pygame.Surface((32, 32), pygame.SRCALPHA)
                icon_z.blit(speed_sheet, (0, 0), (0, 0, 32, 32))

                icon_x = pygame.Surface((32, 32), pygame.SRCALPHA)
                icon_x.blit(speed_sheet, (0, 0), (32, 0, 32, 32))

                # Los metemos en el diccionario de torres para engañar a draw_slot
                self.ui_tower_icons["speed_z"] = pygame.transform.scale(icon_z, (28, 28))
                self.ui_tower_icons["speed_x"] = pygame.transform.scale(icon_x, (28, 28))
            except FileNotFoundError:
                print("Warning: speedup.png not found.")

core_assets = GameAssets()