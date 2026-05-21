import pygame

class Effect(pygame.sprite.Sprite):
    def __init__(self, x, y, sheet, scale_size, fps=15):
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
        self.image = self.frames[self.current_frame]
        self.rect = self.image.get_rect(center=(x, y))
        self.timer = 0.0
        self.fps_time = 1.0 / fps

    def update(self, dt):
        self.timer += dt
        if self.timer >= self.fps_time:
            self.timer -= self.fps_time
            self.current_frame += 1
            if self.current_frame < len(self.frames):
                self.image = self.frames[self.current_frame]
            else:
                self.kill()