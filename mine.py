from pico2d import load_image

from collision import overlap
from config import CELL, SCALE, TILE, HEIGHT, MINE_KNOCK

SHEET = 'asset/trap/traps_right.png'
ROW_IDLE, ROW_BLINK, ROW_EXPLODE = 7, 8, 9
EXPLODE_FRAMES, EXPLODE_FPS = 8, 14
RESPAWN_TIME = 3.0           # 밟아서 터진 뒤 다시 생기기까지 (테스트용)
HALF_W, TRIGGER_H = 16, 18   # 밟았는지 / 칼·총알에 맞았는지 판정하는 범위
VIEW_MARGIN = CELL * SCALE   # 폭발 그림 크기만큼 여유를 두고 화면 밖인지 판단


class Mine:
    """밟으면 바로 폭발하면서 플레이어를 날려버리는 지뢰.
    칼이나 총알로 없앨 수 있고(터지지만 피해 없음), 없앤 지뢰는 화면 밖으로 벗어나면 다시 생김"""
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

    def is_armed(self):
        return self.state == 'armed'

    def defuse(self):
        """칼이나 총알에 맞음: 터지는 모습만 보이고 플레이어는 피해 없음"""
        if self.is_armed():
            self.state, self.t = 'defused', 0.0

    def on_screen(self, cam_y):
        return self.y + VIEW_MARGIN > cam_y and self.y - VIEW_MARGIN < cam_y + HEIGHT

    def update(self, dt, player, cam_y):
        self.t += dt
        if self.state == 'armed':
            if player.on_ground and overlap(self.rect(), player.hitbox()):
                self.state, self.t = 'explode', 0.0
                player.hit(*MINE_KNOCK, source_x=self.x)   # 보고 있는 방향 기준 뒤로 (넘어진 중이면 지뢰 반대쪽으로) 날아감
        elif self.state == 'explode' and self.t >= EXPLODE_FRAMES / EXPLODE_FPS:
            self.state, self.t = 'gone', 0.0
        elif self.state == 'gone' and self.t >= RESPAWN_TIME:
            self.state, self.t = 'armed', 0.0
        elif self.state == 'defused' and self.t >= EXPLODE_FRAMES / EXPLODE_FPS:
            self.state, self.t = 'removed', 0.0
        elif self.state == 'removed' and not self.on_screen(cam_y):
            self.state, self.t = 'armed', 0.0     # 없앤 지뢰는 화면 밖으로 벗어나면 다시 생김

    def draw(self, cam_y):
        if self.state in ('gone', 'removed'):
            return
        if self.state == 'armed':
            # 평소엔 어두운 모습, 가끔 빨간 불이 깜빡임
            row = ROW_BLINK if (self.t % 1.2) > 1.0 else ROW_IDLE
            frame = int(self.t * 2) % 2
        else:
            row, frame = ROW_EXPLODE, min(EXPLODE_FRAMES - 1, int(self.t * EXPLODE_FPS))
        # 셀 안에서 지뢰 바닥이 중심보다 37px 아래에 있음.
        # 2px 더 내려서 타일 위쪽 투명한 잔디 끝부분 속에 묻히게 (캐릭터 발과 같은 높이)
        Mine.sheet.clip_draw(frame * CELL, Mine.sheet.h - (row + 1) * CELL, CELL, CELL,
                             self.x, self.y + (37 - 2) * SCALE - cam_y, CELL * SCALE, CELL * SCALE)
