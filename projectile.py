import math

from pico2d import load_image

from collision import overlap
from config import SCALE, PROJECTILE_LIFE, ARROW_KNOCK, FIRE_KNOCK, CHILL_TIME

SRC = 32                     # 시트 한 칸 크기 (원본 px). 날아가는 그림은 오른쪽을 보고 중심이 (16, 16)
SIZE = SRC * SCALE           # 화면에 그리는 크기
MAX_STEP = 8                 # 한 번에 움직이는 최대 거리 (얇은 발판·플레이어를 뚫고 지나가지 않게)
HIT_FPS = 14

# 종류별: 날아가는 (줄, 프레임 수), 터지는 (줄, 프레임 수), 충돌 박스 (반폭, 반높이)
KINDS = {
    'arrow': dict(fly=(0, 2), hit=(3, 3), half=(14, 4)),
    'fire':  dict(fly=(1, 4), hit=(4, 4), half=(10, 10)),
    'ice':   dict(fly=(2, 4), hit=(5, 4), half=(12, 12)),
}


class Projectile:
    """적이 쏘는 투사체 (화살·불덩이·얼음 구슬).
    블록에 닿거나 플레이어에 맞거나 칼에 베이면 터지는 그림을 보여주고 사라짐"""
    sheets = None

    def __init__(self, kind, x, y, vx, vy, gravity=0.0):
        if Projectile.sheets is None:
            Projectile.sheets = (load_image('asset/enemy/projectiles_right.png'),
                                 load_image('asset/enemy/projectiles_left.png'))
        self.kind = kind
        self.info = KINDS[kind]
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.gravity = gravity
        self.state, self.t = 'fly', 0.0
        self.alive = True                 # False가 되면 게임 루프가 목록에서 뺌

    def rect(self):
        hw, hh = self.info['half']
        return self.x - hw, self.y - hh, self.x + hw, self.y + hh

    def is_flying(self):
        return self.state == 'fly'

    def burst(self):
        """터지는 그림으로 바꿈 (더 이상 피해 없음)"""
        if self.is_flying():
            self.state, self.t = 'hit', 0.0

    def strike(self, player):
        """플레이어에 맞음: 화살·불덩이는 넘어지며 날아가고, 얼음 구슬은 잠깐 미끄러워짐"""
        if self.kind == 'ice':
            player.chill(CHILL_TIME)
        else:
            knock = ARROW_KNOCK if self.kind == 'arrow' else FIRE_KNOCK
            player.hit(*knock, source_x=self.x)
        self.burst()

    # ---------------- 갱신 ----------------
    def update(self, dt, tilemap, player):
        self.t += dt
        if self.state == 'hit':
            if self.t >= self.info['hit'][1] / HIT_FPS:
                self.alive = False
            return
        if self.t >= PROJECTILE_LIFE:
            self.alive = False
            return

        remaining = dt
        while remaining > 0 and self.is_flying():
            step = min(remaining, MAX_STEP / max(1.0, math.hypot(self.vx, self.vy)))
            remaining -= step
            self.vy -= self.gravity * step
            self.x += self.vx * step
            self.y += self.vy * step
            if (tilemap.solids_in(*self.rect()) or tilemap.point_in_slope(self.x, self.y)
                    or not (0 <= self.x <= tilemap.width) or self.y < 0):
                self.burst()
            elif overlap(self.rect(), player.hitbox()):
                self.strike(player)

    # ---------------- 그리기 ----------------
    def draw(self, cam_y):
        if self.state == 'fly':
            row, frames = self.info['fly']
            frame = int(self.t * 12) % frames
            # 날아가는 방향으로 돌려 그림. 왼쪽으로 가면 왼쪽 시트를 써서 위아래가 뒤집히지 않게
            if self.vx >= 0:
                sheet, angle = Projectile.sheets[0], math.atan2(self.vy, self.vx)
            else:
                sheet, angle = Projectile.sheets[1], math.atan2(-self.vy, -self.vx)
        else:
            row, frames = self.info['hit']
            frame = min(frames - 1, int(self.t * HIT_FPS))
            sheet, angle = Projectile.sheets[0], 0.0
        sheet.clip_composite_draw(frame * SRC, sheet.h - (row + 1) * SRC, SRC, SRC, angle, '',
                                  self.x, self.y - cam_y, SIZE, SIZE)

    @staticmethod
    def draw_frost(x, y, t, cam_y):
        """얼음 구슬에 맞아 미끄러운 동안 플레이어 발밑에 반짝이는 얼음 조각"""
        if Projectile.sheets is None:
            return
        sheet = Projectile.sheets[0]
        row, frames = KINDS['ice']['hit']
        frame = 1 + int(t * 8) % (frames - 1)
        sheet.clip_draw(frame * SRC, sheet.h - (row + 1) * SRC, SRC, SRC, x, y - cam_y, SIZE, SIZE)
