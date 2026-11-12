from config import CELL, SCALE


class Anim:
    """시트 이미지에서 한 줄(row)을 애니메이션으로 사용"""
    def __init__(self, image, row, frames, fps, loop=True):
        self.image = image
        self.row = row          # 위에서부터 몇 번째 줄인지 (0부터)
        self.frames = frames
        self.fps = fps
        self.loop = loop

    @property
    def duration(self):
        return self.frames / self.fps

    def frame_at(self, t):
        f = int(t * self.fps)
        return f % self.frames if self.loop else min(f, self.frames - 1)

    def draw(self, frame, x, y, facing):
        bottom = self.image.h - (self.row + 1) * CELL     # pico2d는 좌하단이 원점
        flip = 'h' if facing < 0 else ''                  # 원본이 오른쪽을 보고 있음
        self.image.clip_composite_draw(frame * CELL, bottom, CELL, CELL, 0, flip,
                                       x, y, CELL * SCALE, CELL * SCALE)
