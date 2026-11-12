from pico2d import load_image

from collision import overlap
from config import CELL, SCALE, TILE, MINE_KNOCK

SHEET = 'asset/트랩/traps_right.png'
ROW_IDLE, ROW_BLINK, ROW_EXPLODE = 7, 8, 9
EXPLODE_FRAMES, EXPLODE_FPS = 8, 14
RESPAWN_TIME = 3.0           # 폭발 후 다시 생기기까지 (테스트용)
HALF_W, TRIGGER_H = 16, 18   # 밟았는지 판정하는 범위


class Mine:
    """밟으면 바로 폭발하면서 플레이어를 날려버리는 지뢰"""
    sheet = None

    def __init__(self, col, row):
        if Mine.sheet is None:
            Mine.sheet = load_image(SHEET)
        self.x = (col + 0.5) * TILE
        self.y = row * TILE              # 아래 칸 바닥의 윗면
        self.state = 'armed'
        self.t = 0.0

    def rect(self):
        return self.x - HALF_W, self.y, self.x + HALF_W, self.y + TRIGGER_H

    def update(self, dt, player):
        self.t += dt
        if self.state == 'armed':
            if player.on_ground and overlap(self.rect(), player.hitbox()):
                self.state, self.t = 'explode', 0.0
                player.hit(*MINE_KNOCK)          # 보고 있는 방향 기준 뒤로 날아감
        elif self.state == 'explode' and self.t >= EXPLODE_FRAMES / EXPLODE_FPS:
            self.state, self.t = 'gone', 0.0
        elif self.state == 'gone' and self.t >= RESPAWN_TIME:
            self.state, self.t = 'armed', 0.0

    def draw(self, cam_y):
        if self.state == 'gone':
            return
        if self.state == 'armed':
            # 평소엔 어두운 모습, 가끔 빨간 불이 깜빡임
            row = ROW_BLINK if (self.t % 1.2) > 1.0 else ROW_IDLE
            frame = int(self.t * 2) % 2
        else:
            row, frame = ROW_EXPLODE, min(EXPLODE_FRAMES - 1, int(self.t * EXPLODE_FPS))
        # 셀 안에서 지뢰 바닥이 중심보다 37px 아래에 있음 (+2px는 잔디 속에 살짝 묻히게)
        Mine.sheet.clip_draw(frame * CELL, Mine.sheet.h - (row + 1) * CELL, CELL, CELL,
                             self.x, self.y + 39 * SCALE - cam_y, CELL * SCALE, CELL * SCALE)
