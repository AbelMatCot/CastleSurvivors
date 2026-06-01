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