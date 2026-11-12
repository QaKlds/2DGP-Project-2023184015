from pico2d import load_image

from collision import overlap
from config import CELL, SCALE, TILE, LASER_KNOCK

# 방향별 (포탑 시트 파일, 한 칸 이동량)
DIRS = {
    'right': ('asset/트랩/traps_right.png', (1, 0)),
    'left':  ('asset/트랩/traps_left.png', (-1, 0)),
    'up':    ('asset/트랩/laser_up.png', (0, 1)),
    'down':  ('asset/트랩/laser_down.png', (0, -1)),
}

# 상태별 시간(초)
PERIODIC = {'idle': 1.5, 'charge': 0.5, 'fire': 1.0}
DETECT = {'charge': 0.35, 'fire': 0.7, 'cooldown': 0.8}

BEAM_THICK = 14          # 피격 판정 두께(px)
BEAM_SRC = 32            # 빔 이미지 한 칸 크기


class Laser:
    """레이저 포탑. mode = 'periodic'(일정 주기 발사) / 'detect'(플레이어가 직선상에 있으면 발사)"""
    images = {}          # 이미지는 처음 쓸 때 한 번만 불러서 모든 포탑이 공유

    @classmethod
    def image(cls, path):
        if path not in cls.images:
            cls.images[path] = load_image(path)
        return cls.images[path]

    def __init__(self, tilemap, col, row, direction, mode):
        self.col, self.row = col, row
        self.direction, self.mode = direction, mode
        path, (self.dc, self.db) = DIRS[direction]
        self.sheet = Laser.image(path)
        self.beam_h = Laser.image('asset/트랩/laser_beam.png')
        self.beam_v = Laser.image('asset/트랩/laser_beam_vertical.png')
        self.row_base = 0 if mode == 'periodic' else 3      # 시트 위 3줄: 주기형, 아래 3줄: 감지형

        self.cx, self.cy = (col + 0.5) * TILE, (row + 0.5) * TILE
        self.cells = tilemap.ray_end(col, row, self.dc, self.db)
        self.beam_rect = self._lane_rect(BEAM_THICK)
        self.sense_rect = self._lane_rect(TILE)               # 감지 범위는 한 칸 두께

        self.state = 'idle'
        # 주기형 포탑끼리 박자가 겹치지 않게 시작 시간을 조금씩 어긋나게
        self.t = (col * 0.37 + row * 0.23) % PERIODIC['idle'] if mode == 'periodic' else 0.0

    def _lane_rect(self, thick):
        if not self.cells:
            return None
        xs = [c for c, _ in self.cells]
        ys = [b for _, b in self.cells]
        l, r = min(xs) * TILE, (max(xs) + 1) * TILE
        b, t = min(ys) * TILE, (max(ys) + 1) * TILE
        if self.dc:            # 가로 빔
            return l, self.cy - thick / 2, r, self.cy + thick / 2
        return self.cx - thick / 2, b, self.cx + thick / 2, t

    # ---------------- 갱신 ----------------
    def set_state(self, s):
        self.state, self.t = s, 0.0

    def update(self, dt, player):
        self.t += dt
        s = self.state
        if self.mode == 'periodic':
            if self.t >= PERIODIC[s]:
                self.set_state({'idle': 'charge', 'charge': 'fire', 'fire': 'idle'}[s])
        else:
            if s == 'idle' and self.sense_rect and overlap(self.sense_rect, player.hitbox()):
                self.set_state('charge')
            elif s in DETECT and self.t >= DETECT[s]:
                self.set_state({'charge': 'fire', 'fire': 'cooldown', 'cooldown': 'idle'}[s])

        if self.state == 'fire' and self.beam_rect and overlap(self.beam_rect, player.hitbox()):
            if self.dc:
                push = self.dc                  # 가로 레이저: 빔 방향으로 밀려남
            else:
                push = -player.facing           # 세로 레이저: 보는 방향 기준 뒤로 넘어짐
            player.hit(push, *LASER_KNOCK)

    # ---------------- 그리기 ----------------
    def draw(self, cam_y):
        frame_beam = int(self.t * 12) % 4
        if self.state == 'fire':
            self._draw_beam(cam_y, frame_beam, warn=False)
        elif self.state == 'charge':
            self._draw_beam(cam_y, int(self.t * 8) % 2, warn=True)

        # 포탑 (셀 안에서 포탑이 중심보다 18px 아래에 그려져 있음)
        if self.state == 'idle' or self.state == 'cooldown':
            r, f = 0, int(self.t * 3) % 2
        elif self.state == 'charge':
            dur = PERIODIC['charge'] if self.mode == 'periodic' else DETECT['charge']
            r, f = 1, min(3, int(self.t / dur * 4))
        else:
            r, f = 2, int(self.t * 15) % 3
        row = self.row_base + r
        self.sheet.clip_draw(f * CELL, self.sheet.h - (row + 1) * CELL, CELL, CELL,
                             self.cx, self.cy + 18 * SCALE - cam_y, CELL * SCALE, CELL * SCALE)

    def _draw_beam(self, cam_y, frame, warn):
        horizontal = self.dc != 0
        img = self.beam_h if horizontal else self.beam_v
        flip = 'h' if self.direction == 'left' else ('v' if self.direction == 'up' else '')
        for i, (c, b) in enumerate(self.cells):
            if warn:
                src_row = 2 if horizontal else 1                 # 점선 조준선
            elif horizontal and i == len(self.cells) - 1:
                src_row = 1                                      # 벽에 닿는 끝부분
            else:
                src_row = 0
            img.clip_composite_draw(frame * BEAM_SRC, img.h - (src_row + 1) * BEAM_SRC, BEAM_SRC, BEAM_SRC,
                                    0, flip, (c + 0.5) * TILE, (b + 0.5) * TILE - cam_y, TILE, TILE)
