import pygame
import os
from gamedata import KEYMAP_COORDS

def extract_sprite(sheet, column, rw, cols_total, rows_total, crop=True, crop_x_only=False):
    w = sheet.get_width() // cols_total
    h = sheet.get_height() // rows_total
    sub = sheet.subsurface((column * w, rw * h, w, h))
    if crop:
        bounding = sub.get_bounding_rect()
        if bounding.width > 0 and bounding.height > 0:
            if crop_x_only:
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

    col_rects = []
    for c in range(cols_total):
        valid_x = [bounds[r][c].x for r in range(rows_total) if bounds[r][c].width > 0]
        valid_right = [bounds[r][c].right for r in range(rows_total) if bounds[r][c].width > 0]
        min_x = min(valid_x) if valid_x else 0
        max_r = max(valid_right) if valid_right else w
        col_rects.append((min_x, max_r - min_x))

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

def get_tile(sheet, x, y, width, height, scale_size):
    image = pygame.Surface((width, height), pygame.SRCALPHA)
    image.blit(sheet, (0, 0), (x, y, width, height))
    return pygame.transform.scale(image, (scale_size, scale_size))

def draw_text_wrapped(surface, text, font, color, rect):
    words = text.split()
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

    line_height = font.get_linesize()
    total_height = line_height * len(lines)
    temp_surf = pygame.Surface((rect.width, max(total_height, 1)), pygame.SRCALPHA)

    y_offset = 0
    for line in lines:
        # ¡MAGIA AQUÍ! El 'False' apaga el difuminado. Pixel art perfecto.
        line_surf = font.render(line, False, color)
        temp_surf.blit(line_surf, (0, y_offset))
        y_offset += line_height

    if total_height > rect.height:
        scale = rect.height / total_height
        new_w = int(rect.width * scale)
        new_h = rect.height
        # Usamos scale normal, nada de smoothscale
        fitted_surf = pygame.transform.scale(temp_surf, (max(1, new_w), max(1, new_h)))
        surface.blit(fitted_surf, (rect.x + (rect.width - new_w) // 2, rect.y))
    else:
        surface.blit(temp_surf, (rect.x, rect.y))

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

    def s(img):
        if img.get_width() <= 0 or img.get_height() <= 0: return img
        return pygame.transform.scale(img, (img.get_width() * scale, img.get_height() * scale))

    tl, tc, tr = s(parts[0]), s(parts[1]), s(parts[2])
    ml, mc, mr = s(parts[3]), s(parts[4]), s(parts[5])
    bl, bc, br = s(parts[6]), s(parts[7]), s(parts[8])

    cw_l, cw_r = min(tl.get_width(), rect.width // 2), min(tr.get_width(), rect.width // 2)
    ch_t, ch_b = min(tl.get_height(), rect.height // 2), min(bl.get_height(), rect.height // 2)

    mid_w = max(0, rect.width - cw_l - cw_r)
    mid_h = max(0, rect.height - ch_t - ch_b)

    if cw_l > 0 and ch_t > 0: surface.blit(pygame.transform.scale(tl, (cw_l, ch_t)), (rect.x, rect.y))
    if cw_r > 0 and ch_t > 0: surface.blit(pygame.transform.scale(tr, (cw_r, ch_t)), (rect.right - cw_r, rect.y))
    if cw_l > 0 and ch_b > 0: surface.blit(pygame.transform.scale(bl, (cw_l, ch_b)), (rect.x, rect.bottom - ch_b))
    if cw_r > 0 and ch_b > 0: surface.blit(pygame.transform.scale(br, (cw_r, ch_b)),
                                           (rect.right - cw_r, rect.bottom - ch_b))

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

# Fíjate en el nuevo parámetro al final
def draw_slot(surface, assets, x, y, size, key_text, cost=None, is_pressed=False, t_id=None, show_ribbon=True, tier_lvl=None):
    img = assets.btn_small_pressed_img if is_pressed else assets.btn_small_img
    btn_y = y + 4 if is_pressed else y
    btn_h = size - 4 if is_pressed else size
    surface.blit(pygame.transform.scale(img, (size, btn_h)), (x, btn_y))

    y_off = 4 if is_pressed else 0
    pygame.draw.rect(surface, "#3b2f2f", (x - 8, y - 8 + y_off, 22, 22), border_radius=4)
    pygame.draw.rect(surface, "#d2b48c", (x - 8, y - 8 + y_off, 22, 22), 2, border_radius=4)

    if t_id and t_id in assets.ui_tower_icons:
        icon = assets.ui_tower_icons[t_id]
        ix = x + (size // 2) - (icon.get_width() // 2)
        iy = y + (size // 2) - (icon.get_height() // 2) + y_off - 4
        surface.blit(icon, (ix, iy))

    if assets.keys_sheet:
        k = key_text.lower()
        col_idx, row_idx = KEYMAP_COORDS.get(k, (7, 6))
        key_img = extract_sprite(assets.keys_sheet, col_idx, row_idx, 8, 8)
        if key_img:
            key_img = pygame.transform.scale(key_img, (18, 18))
            surface.blit(key_img, (x - 6, y - 6 + y_off))
    else:
        key_surf = assets.ui_font_small.render(key_text.upper(), True, "white")
        surface.blit(key_surf, (x - 1, y - 5 + y_off))

        # --- NUEVO: BANDERÍN DE NIVEL (Debajo de la tecla) ---
    if tier_lvl is not None and assets.tierframe and assets.tiers_sheet:
        bx = x - 5
        by = y + 14 + y_off
        surface.blit(assets.tierframe, (bx, by))

        # Calculamos la posición en la sheet y lo pegamos a x0 y3 del banderín
        tier_idx = min(7, max(0, tier_lvl - 1))
        t_col, t_row = tier_idx % 4, tier_idx // 4
        surface.blit(assets.tiers_sheet, (bx, by + 3), (t_col * 16, t_row * 16, 16, 16))

    if show_ribbon:
        draw_ribbon(surface, x - 5, y + size + 2, 60, 25, assets.ribbon_sheet, rw=1)
        if cost is not None:
            cost_surf = assets.ui_font_small.render(f"{cost} G", True, "black")
            surface.blit(cost_surf, (x + 25 - cost_surf.get_width() // 2, y + size + 7))

def draw_action_btn(surface, assets, x, y, w, h, key_text, label, cost=None, is_pressed=False):
    img = assets.btn_wide_pressed_img if is_pressed else assets.btn_wide_img
    btn_y = y + 4 if is_pressed else y
    btn_h = h - 4 if is_pressed else h
    draw_9_slice_button(surface, img, pygame.Rect(x, btn_y, w, btn_h), edge_px=14)

    y_off = 4 if is_pressed else 0

    if key_text:
        pygame.draw.rect(surface, "#3b2f2f", (x - 10, y - 10 + y_off, 26, 26), border_radius=4)
        pygame.draw.rect(surface, "#d2b48c", (x - 10, y - 10 + y_off, 26, 26), 2, border_radius=4)

        if assets.keys_sheet:
            k = key_text.lower()
            col_idx, row_idx = KEYMAP_COORDS.get(k, (7, 6))
            key_img = extract_sprite(assets.keys_sheet, col_idx, row_idx, 8, 8)
            if key_img:
                key_img = pygame.transform.scale(key_img, (22, 22))
                surface.blit(key_img, (x - 8, y - 8 + y_off))
        else:
            key_surf = assets.ui_font_medium.render(key_text.upper(), True, "white")
            surface.blit(key_surf, (x - 3, y - 8 + y_off))

    label_surf = assets.ui_font_medium.render(label, True, "black")
    surface.blit(label_surf, (x + (w // 2) - (label_surf.get_width() // 2),
                                y + (h // 2) - (label_surf.get_height() // 2) - 4 + y_off))

    if cost is not None:
        ry = y + h + 2
        rw_btn = 80
        rh_btn = 28
        rx_ribbon = x + (w // 2) - (rw_btn // 2)
        draw_ribbon(surface, rx_ribbon, ry, rw_btn, rh_btn, assets.ribbon_sheet, rw=0)
        cost_surf = assets.ui_font_small.render(f"{cost} G", True, "black")
        surface.blit(cost_surf, (rx_ribbon + (rw_btn // 2) - (cost_surf.get_width() // 2), ry + 6))


def draw_game_over_menu(surface, assets, current_minute, game_time):
    overlay = pygame.Surface((1280, 720), pygame.SRCALPHA)
    overlay.fill((50, 0, 0, 200))
    surface.blit(overlay, (0, 0))

    title_text = assets.ui_font_large.render("DEFEAT!", True, "red")
    surface.blit(title_text, (640 - title_text.get_width() // 2, 250))
    info_text = assets.ui_font_medium.render(
        f"You survived for {current_minute} minutes and {int(game_time % 60)} seconds.", True, "white")
    surface.blit(info_text, (640 - info_text.get_width() // 2, 320))
    exit_text = assets.ui_font_small.render("Close the window to exit.", True, "gray")
    surface.blit(exit_text, (640 - exit_text.get_width() // 2, 400))


def draw_level_up_menu(surface, assets, level_up_options, selected_card_idx, offsetX, width_gameboard):

    overlay = pygame.Surface((1280, 720), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 200))
    surface.blit(overlay, (0, 0))

    # Escalamos el arte de 100x140 x2 exacto para mantener pixel-perfect
    card_width = 200
    card_height = 280
    spacing = 30

    cols = 3
    rows = (len(level_up_options) + cols - 1) // cols

    # Subimos el inicio si hay más de una fila
    start_y = 40 if rows > 1 else 200

    card_rects = []
    is_castle_select = len(level_up_options) > 0 and level_up_options[
        0].get("type") in ["arrow", "fireball", "lightning", "kunai", "laser", "thorns"]

    if is_castle_select:
        title_text = assets.ui_font_large.render("CHOOSE YOUR CASTLE", True, "yellow")
        surface.blit(title_text, (640 - title_text.get_width() // 2, 10))
    else:
        title_text = assets.ui_font_large.render("LEVEL UP! CHOOSE A REWARD", True, "yellow")
        surface.blit(title_text, (640 - title_text.get_width() // 2, 100))

    for i, card in enumerate(level_up_options):
        r = i // cols
        c = i % cols

        # Centramos la fila actual dinámicamente
        cards_in_this_row = len(level_up_options) - r * cols if (r == rows - 1) else cols
        row_w = cards_in_this_row * card_width + (cards_in_this_row - 1) * spacing
        cx = offsetX + (width_gameboard - row_w) // 2 + c * (card_width + spacing)
        cy = start_y + r * (card_height + 25)

        rect = pygame.Rect(cx, cy, card_width, card_height)
        card_rects.append(rect)

        # 1. Construimos la tarjeta a su resolución nativa de pixel art (100x140)
        base_card = pygame.Surface((100, 140), pygame.SRCALPHA)
        if assets.lvlcard:
            base_card.blit(assets.lvlcard, (0, 0))
        else:
            base_card.fill("#112233")  # Fallback por si la lías con las rutas

        c_type = card.get("type", "")
        c_id = card.get("id", c_type)  # En castle_select 'type' es la torre directamente

        # Leemos el nivel directamente de la lógica
        lvl = card.get("lvl", 1)

        # 2. Iconos centrales
        if c_type == "upgrade_tower" or is_castle_select:
            if c_id in assets.raw_tower_icons:
                base_card.blit(assets.raw_tower_icons[c_id], (35, 12))
        elif c_type in ["unlock_passive", "upgrade_passive"]:
            if c_id in assets.stat_icons:
                base_card.blit(assets.stat_icons[c_id], (34, 18))
        # Recompensas planas de nivel > 50 que reutilizan iconos de stats
        elif c_type == "heal":
            if "heal" in assets.stat_icons: base_card.blit(assets.stat_icons["heal"], (34, 18))
        elif c_type == "gold_100":
            if "gold_100" in assets.stat_icons: base_card.blit(assets.stat_icons["gold_100"], (34, 18))
        elif c_type == "gems_5":
            if "gems" in assets.stat_icons: base_card.blit(assets.stat_icons["gems"], (34, 18))

        # 3. Tiers (Sprite sheet de 4 columnas x 2 filas)
        if assets.tiers_sheet:
            tier_idx = min(7, max(0, lvl - 1))
            t_col, t_row = tier_idx % 4, tier_idx // 4
            base_card.blit(assets.tiers_sheet, (6, 17), (t_col * 16, t_row * 16, 16, 16))

        # 4. Marco superior embellecedor
        if assets.cardframe:
            base_card.blit(assets.cardframe, (0, 0))

        # 5. Escalar x2
        scaled_card = pygame.transform.scale(base_card, (card_width, card_height))

        # Bordecito de selección inteligente (Silueta perfecta)
        if selected_card_idx == i:
            mask = pygame.mask.from_surface(scaled_card)
            mask_surf = mask.to_surface(setcolor=(255, 255, 255, 255), unsetcolor=(0, 0, 0, 0))

            # Dibujamos la silueta blanca desplazada para crear el contorno
            grosor = 3
            for dx in [-grosor, 0, grosor]:
                for dy in [-grosor, 0, grosor]:
                    if dx != 0 or dy != 0:
                        surface.blit(mask_surf, (cx + dx, cy + dy))

        # 5.5 Pintar la carta real ENCIMA del borde blanco
        surface.blit(scaled_card, (cx, cy))

        # 6. Textos nítidos SOBRE el escalado
        title_str = card.get("title", "")

        # ¡FALSO al Anti-Aliasing para que las letras no engorden!
        t_surf = assets.ui_font_small.render(title_str, False, "white")
        t_shadow = assets.ui_font_small.render(title_str, False, "black")

        # Hemos quitado la basura de re-escalar. Dejamos el texto a su tamaño puro.
        # Y subimos la Y a 128 para que quede centrado de lujo.
        tx = cx + 100 - (t_surf.get_width() // 2)
        ty = cy + 128 - (t_surf.get_height() // 2)

        surface.blit(t_shadow, (tx + 1, ty + 1))
        surface.blit(t_surf, (tx, ty))

        # Descripción envuelta
        if "desc" in card:
            desc_rect = pygame.Rect(cx + 38, cy + 152, 122, 80)
            draw_text_wrapped(surface, card["desc"], assets.ui_font_small, "#2b2b2b", desc_rect)

    return card_rects

def draw_pause_menu(surface, assets, mouseX, mouseY):
    overlay = pygame.Surface((1280, 720), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    surface.blit(overlay, (0, 0))

    draw_ribbon(surface, 640 - 150, 120, 300, 80, assets.big_ribbon_sheet, rw=0, rows_total=5)
    title_text = assets.ui_font_large.render("MENU", True, "white")
    surface.blit(title_text, (640 - title_text.get_width() // 2, 145))

    menu_opts = ["Resume", "Restart", "Settings", "Quit"]
    pause_rects = []
    for i, opt in enumerate(menu_opts):
        btn_y = 250 + i * 80
        btn_rect = pygame.Rect(640 - 100, btn_y, 200, 60)
        pause_rects.append((btn_rect, opt))

        is_hover = btn_rect.collidepoint(mouseX, mouseY) and pygame.mouse.get_pressed()[0]
        current_y = btn_rect.y + 4 if is_hover else btn_rect.y
        current_h = btn_rect.height - 4 if is_hover else btn_rect.height
        img = assets.btn_wide_pressed_img if is_hover else assets.btn_wide_img

        draw_9_slice_button(surface, img, pygame.Rect(btn_rect.x, current_y, btn_rect.width, current_h), edge_px=14)
        y_off = 4 if is_hover else 0
        opt_surf = assets.ui_font_medium.render(opt, True, "black")
        surface.blit(opt_surf, (640 - opt_surf.get_width() // 2, btn_y + 30 - opt_surf.get_height() // 2 - 4 + y_off))

    return pause_rects


def draw_main_menu(surface, assets, mouseX, mouseY, offset_y=0):

    surface.blit(assets.bg_menu, (0, 0))
    draw_ribbon(surface, 640 - 250, 100 + offset_y, 500, 100, assets.big_ribbon_sheet, rw=1, rows_total=5)

    title_text = assets.ui_font_large.render("CASTLE SURVIVORS", True, (255, 235, 0))
    surface.blit(title_text, (640 - title_text.get_width() // 2, 130 + offset_y))

    menu_opts = ["Play", "Upgrades", "Settings", "Exit"]
    main_menu_rects = []
    for i, opt in enumerate(menu_opts):
        btn_y = 280 + i * 80 + offset_y
        btn_rect = pygame.Rect(640 - 100, btn_y, 200, 60)
        main_menu_rects.append((btn_rect, opt))

        is_hover = btn_rect.collidepoint(mouseX, mouseY) and pygame.mouse.get_pressed()[0]
        current_y = btn_rect.y + 4 if is_hover else btn_rect.y
        current_h = btn_rect.height - 4 if is_hover else btn_rect.height
        img = assets.btn_wide_pressed_img if is_hover else assets.btn_wide_img

        draw_9_slice_button(surface, img, pygame.Rect(btn_rect.x, current_y, btn_rect.width, current_h), edge_px=14)
        y_off = 4 if is_hover else 0
        opt_surf = assets.ui_font_medium.render(opt, True, "black")
        surface.blit(opt_surf, (640 - opt_surf.get_width() // 2, btn_y + 30 - opt_surf.get_height() // 2 - 4 + y_off))

    return main_menu_rects