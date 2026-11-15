import os

from pico2d import load_image

from collision import overlap
from config import CELL, SCALE, TILE, LASER_KNOCK

# 방향별 한 칸 이동량
DIRS = {'right': (1, 0), 'left': (-1, 0), 'up': (0, 1), 'down': (0, -1)}

# 땅 속에 박히는 장치 그림: 무늬(주변 타일)별로 '오른쪽', '위쪽' 시트가 있고 왼쪽·아래쪽은 뒤집어서 씀
DEVICE_SHEET = 'asset/trap/laser_{style}_{base}.png'
DEVICE_BASE = {'right': ('right', ''), 'left': ('right', 'h'), 'up': ('up', ''), 'down': ('up', 'v')}
# 땅 윗면(위 칸이 비어 있음)에 박힌 장치는 잔디·눈이 덮인 그림을 씀. 없으면 반대 방향 그림을 뒤집어 쓰고, 그것도 없으면 위 그림
TOP_SHEET = 'asset/trap/laser_{style}_top_{direction}.png'
DEVICE_OFFSET = 18       # 시트 칸 안에서 장치가 칸 중심보다 18px(원본) 아래에 그려져 있음

OPPOSITE = {'right': 'left', 'left': 'right', 'up': 'down', 'down': 'up'}

# 상태별 시간(초)
PERIODIC = {'idle': 1.5, 'charge': 0.5, 'fire': 1.0}
DETECT = {'charge': 0.35, 'fire': 0.7, 'cooldown': 0.8}

BEAM_THICK = 14          # 피격 판정 두께(px)
BEAM_SRC = 32            # 빔 이미지 한 칸 크기


class Laser:
    """레이저 발사 장치 + 마주 보는 받는 장치 한 쌍.
    mode = 'periodic'(일정 주기 발사) / 'detect'(플레이어가 직선상에 있으면 발사)"""
    images = {}          # 이미지는 처음 쓸 때 한 번만 불러서 모든 포탑이 공유

    @classmethod
    def image(cls, path):
        if path not in cls.images:
            cls.images[path] = load_image(path)
        return cls.images[path]

    def __init__(self, tilemap, col, row, direction, mode):
        self.col, self.row = col, row
        self.direction, self.mode = direction, mode
        self.dc, self.db = DIRS[direction]
        self.device = self._device(direction, tilemap.style_at(col, row), tilemap.is_surface(col, row))
        self.beam_h = Laser.image('asset/trap/laser_beam.png')
        self.beam_v = Laser.image('asset/trap/laser_beam_vertical.png')
        self.row_base = 0 if mode == 'periodic' else 3      # 시트 위 3줄: 주기형, 아래 3줄: 감지형

        self.cx, self.cy = (col + 0.5) * TILE, (row + 0.5) * TILE
        self.cells, end = tilemap.ray(col, row, self.dc, self.db)
        # 빔이 끝나는 칸에 받는 장치(*)가 있으면 발사 장치를 마주 보게 그림
        self.receiver = end if end in tilemap.receivers else None
        if self.receiver:
            self.receiver_device = self._device(OPPOSITE[direction], tilemap.style_at(*end), tilemap.is_surface(*end))
        else:
            print(f'[경고] ({col}, {row}) 레이저의 빔 끝에 받는 장치(*)가 없습니다')
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
            player.hit(*LASER_KNOCK)            # 보고 있는 방향 기준 뒤로 넘어짐

    # ---------------- 그리기 ----------------
    def draw(self, cam_y):
        if self.state == 'fire':
            self._draw_beam(cam_y, int(self.t * 12) % 4)

        # 발사 장치와 받는 장치는 같은 상태로 움직임
        if self.state == 'idle' or self.state == 'cooldown':
            r, f = 0, int(self.t * 3) % 2
        elif self.state == 'charge':
            dur = PERIODIC['charge'] if self.mode == 'periodic' else DETECT['charge']
            r, f = 1, min(3, int(self.t / dur * 4))
        else:
            r, f = 2, int(self.t * 15) % 3
        row = self.row_base + r
        self._draw_device(self.device, row, f, self.cx, self.cy, cam_y)
        if self.receiver:
            rc, rb = self.receiver
            self._draw_device(self.receiver_device, row, f, (rc + 0.5) * TILE, (rb + 0.5) * TILE, cam_y)

    @staticmethod
    def _device(direction, style, on_surface):
        """방향·무늬·위치에 맞는 (시트, 뒤집기) - 장치는 타일 한 칸을 꽉 채워서 땅 속에 박힌 것처럼 보임"""
        if on_surface:
            path = TOP_SHEET.format(style=style, direction=direction)
            if os.path.exists(path):
                return Laser.image(path), ''
            mirror = {'left': 'right', 'right': 'left'}.get(direction)
            if mirror:
                path = TOP_SHEET.format(style=style, direction=mirror)
                if os.path.exists(path):
                    return Laser.image(path), 'h'
        base, flip = DEVICE_BASE[direction]
        return Laser.image(DEVICE_SHEET.format(style=style, base=base)), flip

    def _draw_device(self, device, row, frame, x, y, cam_y):
        sheet, flip = device
        # 장치가 칸 중심보다 아래에 있으므로 그만큼 올려 그림 (위아래로 뒤집으면 반대로)
        offset = DEVICE_OFFSET * SCALE * (-1 if flip == 'v' else 1)
        sheet.clip_composite_draw(frame * CELL, sheet.h - (row + 1) * CELL, CELL, CELL, 0, flip,
                                  x, y + offset - cam_y, CELL * SCALE, CELL * SCALE)

    def _draw_beam(self, cam_y, frame):
        horizontal = self.dc != 0
        img = self.beam_h if horizontal else self.beam_v
        flip = 'h' if self.direction == 'left' else ('v' if self.direction == 'up' else '')
        for i, (c, b) in enumerate(self.cells):
            if horizontal and i == len(self.cells) - 1 and not self.receiver:
                src_row = 1                                      # 받는 장치 없이 벽에 닿는 끝부분
            else:
                src_row = 0
            img.clip_composite_draw(frame * BEAM_SRC, img.h - (src_row + 1) * BEAM_SRC, BEAM_SRC, BEAM_SRC,
                                    0, flip, (c + 0.5) * TILE, (b + 0.5) * TILE - cam_y, TILE, TILE)
