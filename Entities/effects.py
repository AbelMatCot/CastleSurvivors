import pygame

class Effect(pygame.sprite.Sprite):
    def __init__(self, x, y, sheet, scale_size, fps=15, delay=0.0, num_frames=None):
        super().__init__()
        self.frames = []
        h = sheet.get_height()
        w = sheet.get_width()

        if num_frames is None:
            num_frames = max(1, w // max(1, h))

        # Magia anti-deslizamiento con decimales
        exact_w = w / num_frames

        for i in range(num_frames):
            start_x = int(i * exact_w)
            end_x = int((i + 1) * exact_w)
            current_w = end_x - start_x

            frame = pygame.Surface((current_w, h), pygame.SRCALPHA)
            frame.blit(sheet, (0, 0), (start_x, 0, current_w, h))

            aspect_ratio = h / max(1, current_w)
            new_h = int(scale_size * aspect_ratio)

            frame = pygame.transform.scale(frame, (scale_size, new_h))
            self.frames.append(frame)

        self.current_frame = 0
        self.fps_time = 1.0 / fps
        self.timer = -delay

        self.image = pygame.Surface((scale_size, scale_size), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(x, y))

    def update(self, dt):
        if self.timer < 0:
            self.timer += dt
            if self.timer >= 0:
                self.image = self.frames[0]
                self.rect = self.image.get_rect(center=self.rect.center)
            return

        self.timer += dt
        if self.timer >= self.fps_time:
            self.timer -= self.fps_time
            self.current_frame += 1
            if self.current_frame < len(self.frames):
                self.image = self.frames[self.current_frame]
                self.rect = self.image.get_rect(center=self.rect.center)
            else:
                self.kill()

class TowerSmoke(pygame.sprite.Sprite):
    def __init__(self, x, y, smoke_sheet, goes_right=False):
        super().__init__()
        self.frames = []
        if smoke_sheet:
            w = smoke_sheet.get_width()
            h = smoke_sheet.get_height()
            num_frames = 9
            frame_w = w // num_frames

            for i in range(num_frames):
                frame = pygame.Surface((frame_w, h), pygame.SRCALPHA)
                frame.blit(smoke_sheet, (0, 0), (i * frame_w, 0, frame_w, h))

                if goes_right:
                    frame = pygame.transform.flip(frame, True, False)

                frame = pygame.transform.scale(frame, (frame_w * 2, h * 2))
                self.frames.append(frame)
        else:
            self.frames.append(pygame.Surface((0, 0)))

        self.current_frame = 0
        self.image = self.frames[0]
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


class Chest(pygame.sprite.Sprite):
    def __init__(self, x, y, assets):
        super().__init__()
        self.assets = assets

        self.chest_frames = []
        w, h = 32, 32
        scale = 1.0  # Pon aquí la escala que estabas usando

        for row in range(4):
            frame = pygame.Surface((w, h), pygame.SRCALPHA)
            frame.blit(assets.chests_sheet, (0, 0), (6 * w, row * h, w, h))
            self.chest_frames.append(pygame.transform.scale(frame, (int(w * scale), int(h * scale))))

        self.coin_frames = []
        cw, ch = 64, 64
        num_coin_frames = assets.coins_sheet.get_width() // max(1, cw)
        for i in range(num_coin_frames):
            frame = pygame.Surface((cw, ch), pygame.SRCALPHA)
            frame.blit(assets.coins_sheet, (0, 0), (i * cw, 0, cw, ch))
            self.coin_frames.append(pygame.transform.scale(frame, (48, 48)))

        self.image = self.chest_frames[0]
        self.rect = self.image.get_rect(center=(x, y))

        # GUARDAMOS EL ANCLA: Así el cofre no pegará saltos cuando la caja crezca
        self.original_midbottom = self.rect.midbottom

        self.state = "closed"
        self.anim_timer = 0.0
        self.frame_idx = 0
        self.trigger_level_up = False
        self.base_chest = None
        self.base_white_chest = None

    def click(self):
        if self.state == "closed":
            self.state = "opening"
            self.anim_timer = 0.0
            self.frame_idx = 0

    def update(self, dt):
        if self.state == "opening":
            self.anim_timer += dt
            if self.anim_timer >= 0.15:
                self.anim_timer = 0.0
                self.frame_idx += 1
                if self.frame_idx < len(self.chest_frames):
                    self.image = self.chest_frames[self.frame_idx]
                    self.rect = self.image.get_rect(midbottom=self.original_midbottom)
                else:
                    self.state = "coins"
                    self.frame_idx = 0
                    self.base_chest = self.chest_frames[3].copy()

        elif self.state == "coins":
            self.anim_timer += dt
            if self.anim_timer >= 0.04:
                self.anim_timer = 0.0
                self.frame_idx += 1
                if self.frame_idx < len(self.coin_frames):
                    c_img = self.coin_frames[self.frame_idx]

                    # FIX: Creamos un lienzo enorme para que las monedas vuelen libres
                    canvas_w = max(self.base_chest.get_width(), c_img.get_width()) + 40
                    canvas_h = self.base_chest.get_height() + c_img.get_height() + 40

                    combined = pygame.Surface((canvas_w, canvas_h), pygame.SRCALPHA)

                    # Colocamos el cofre abajo del todo y en el centro
                    cx_chest = (canvas_w - self.base_chest.get_width()) // 2
                    cy_chest = canvas_h - self.base_chest.get_height()
                    combined.blit(self.base_chest, (cx_chest, cy_chest))

                    # Y las monedas las disparamos hacia arriba (cy_chest - 35)
                    cx_coin = (canvas_w - c_img.get_width()) // 2
                    cy_coin = cy_chest - 35
                    combined.blit(c_img, (cx_coin, cy_coin))

                    self.image = combined
                    # Restauramos el ancla al suelo para que la caja gigante no desplace el cofre
                    self.rect = self.image.get_rect(midbottom=self.original_midbottom)
                else:
                    self.image = self.base_chest.copy()
                    self.rect = self.image.get_rect(midbottom=self.original_midbottom)
                    self.state = "waiting"
                    self.trigger_level_up = True

        elif self.state == "fading_white":
            self.anim_timer += dt
            ratio = min(1.0, self.anim_timer / 0.2)
            white_surf = pygame.Surface(self.image.get_size(), pygame.SRCALPHA)
            white_surf.fill((255, 255, 255, int(255 * ratio)))

            self.image = self.base_chest.copy()
            self.image.blit(white_surf, (0, 0), special_flags=pygame.BLEND_RGB_ADD)

            if ratio == 1.0:
                self.state = "fading_out"
                self.anim_timer = 0.0
                self.base_white_chest = self.image.copy()

        elif self.state == "fading_out":
            self.anim_timer += dt
            ratio = max(0.0, 1.0 - (self.anim_timer / 0.3))
            self.image = self.base_white_chest.copy()
            self.image.set_alpha(int(255 * ratio))

            if ratio == 0.0:
                self.kill()

