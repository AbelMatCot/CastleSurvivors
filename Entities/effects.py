import pygame


class Effect(pygame.sprite.Sprite):
    def __init__(self, x, y, sheet, scale_size, fps=15, delay=0.0):
        super().__init__()
        self.frames = []
        h = sheet.get_height()
        w = sheet.get_width()
        num_frames = w // h

        for i in range(num_frames):
            frame = pygame.Surface((h, h), pygame.SRCALPHA)
            frame.blit(sheet, (0, 0), (i * h, 0, h, h))
            frame = pygame.transform.scale(frame, (scale_size, scale_size))
            self.frames.append(frame)

        self.current_frame = 0
        self.fps_time = 1.0 / fps
        self.timer = -delay  # Empezamos en negativo por el retraso

        # Imagen inicial vacía (transparente) para que no se vea antes de tiempo
        self.image = pygame.Surface((scale_size, scale_size), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(x, y))

    def update(self, dt):
        if self.timer < 0:
            self.timer += dt
            if self.timer >= 0:
                # El retraso acaba, mostramos el primer frame de humo
                self.image = self.frames[0]
            return

        self.timer += dt
        if self.timer >= self.fps_time:
            self.timer -= self.fps_time
            self.current_frame += 1
            if self.current_frame < len(self.frames):
                self.image = self.frames[self.current_frame]
            else:
                self.kill()