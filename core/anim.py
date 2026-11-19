from config import CELL, SCALE

STAND_FOOT_ROW = 83     # 서 있는 프레임에서 발바닥이 있는 줄 (셀 위에서부터, 원본 px)


class Anim:
    """시트 이미지에서 한 줄(row)을 애니메이션으로 사용"""
    def __init__(self, image, row, frames, fps, loop=True, feet=None):
        self.image = image
        self.row = row          # 위에서부터 몇 번째 줄인지 (0부터)
        self.frames = frames
        self.fps = fps
        self.loop = loop
        # 프레임별 발바닥 줄. 공중 동작 스프라이트는 그림 안에서 캐릭터가 위로 떠 있어서,
        # 그만큼 내려 그려야 보이는 발과 실제 충돌 박스 바닥이 일치함
        self.feet = feet or [STAND_FOOT_ROW] * frames

    @property
    def duration(self):
        return self.frames / self.fps

    def frame_at(self, t):
        f = int(t * self.fps)
        return f % self.frames if self.loop else min(f, self.frames - 1)

    def draw(self, frame, x, y, facing):
        bottom = self.image.h - (self.row + 1) * CELL     # pico2d는 좌하단이 원점
        flip = 'h' if facing < 0 else ''                  # 원본이 오른쪽을 보고 있음
        y -= (STAND_FOOT_ROW - self.feet[frame]) * SCALE  # 그림 속 발이 떠 있는 만큼 내려 그림
        self.image.clip_composite_draw(frame * CELL, bottom, CELL, CELL, 0, flip,
                                       x, y, CELL * SCALE, CELL * SCALE)
