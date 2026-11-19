from pico2d import load_image

from core.collision import overlap
from config import TILE, TILE_SRC, PLAYER_HALF_W, CRUMBLE_SHAKE_TIME, CRUMBLE_RESPAWN_TIME

SOLID_H = int(20 * TILE / TILE_SRC)     # 발판 그림은 칸 위쪽 20px(원본)만 차지하므로 충돌도 그만큼만
SHAKE_FPS, BREAK_FPS, RETURN_FPS = 12, 12, 10
BREAK_FRAMES = (4, 5, 6, 7)             # 부서져 떨어지는 프레임 (첫 프레임부터 충돌 없음)
RETURN_FRAMES = (8, 9, 10)              # 다시 생기는 프레임 (마지막 프레임 = 흰 번쩍임, 이때부터 충돌)


class CrumblePlatform:
    """부서지는 발판: 가로로 이어진 칸들이 한 덩어리.
    플레이어가 밟으면 다 같이 흔들리다 부서지고, CRUMBLE_RESPAWN_TIME 뒤 다시 생김"""
    sheets = {}

    def __init__(self, c0, c1, row, style, ice):
        if style not in CrumblePlatform.sheets:
            CrumblePlatform.sheets[style] = load_image(f'asset/tiles/tiles_crumble_{style}.png')
        self.sheet = CrumblePlatform.sheets[style]
        self.c0, self.c1, self.row = c0, c1, row
        self.ice = ice
        self.left, self.right = c0 * TILE, (c1 + 1) * TILE
        self.top = (row + 1) * TILE
        self.state, self.t = 'idle', 0.0

    def is_solid(self):
        return self.state in ('idle', 'shake')

    def solid_rects(self):
        """충돌 사각형들 [(rect, 얼음 여부)] - tilemap.solids_in 이 함께 확인함"""
        if not self.is_solid():
            return []
        return [((self.left, self.top - SOLID_H, self.right, self.top), self.ice)]

    def set_state(self, s):
        self.state, self.t = s, 0.0

    def update(self, dt, player):
        self.t += dt
        if self.state == 'idle':
            # 발이 발판 윗면에 닿아 서 있으면 흔들리기 시작
            if (player.on_ground and abs(player.y - self.top) < 1
                    and player.x + PLAYER_HALF_W > self.left and player.x - PLAYER_HALF_W < self.right):
                self.set_state('shake')
        elif self.state == 'shake' and self.t >= CRUMBLE_SHAKE_TIME:
            self.set_state('break')
        elif self.state == 'break' and self.t >= CRUMBLE_RESPAWN_TIME:
            # 플레이어가 발판 자리에 있으면 비켜줄 때까지 기다림
            if not overlap((self.left, self.top - SOLID_H, self.right, self.top), player.hitbox()):
                self.set_state('return')
        elif self.state == 'return' and self.t >= len(RETURN_FRAMES) / RETURN_FPS:
            self.set_state('idle')

    def frame(self):
        """지금 그릴 시트 열 번호 (None = 안 그림)"""
        if self.state == 'idle':
            return 0
        if self.state == 'shake':
            return 1 + int(self.t * SHAKE_FPS) % 3
        if self.state == 'break':
            i = int(self.t * BREAK_FPS)
            return BREAK_FRAMES[i] if i < len(BREAK_FRAMES) else None
        return RETURN_FRAMES[min(len(RETURN_FRAMES) - 1, int(self.t * RETURN_FPS))]

    def draw(self, cam_y):
        f = self.frame()
        if f is None:
            return
        # 시트 한 칸은 32x64: 위쪽 32px이 발판 칸, 아래 32px은 떨어지는 조각이 그려지는 자리
        cy = self.top - TILE - cam_y            # 칸 64px의 중심 = 발판 칸 아래 끝
        for c in range(self.c0, self.c1 + 1):
            if self.c0 == self.c1:
                kind = 1
            else:
                kind = 0 if c == self.c0 else 2 if c == self.c1 else 1   # 0 왼쪽 끝, 1 가운데, 2 오른쪽 끝
            self.sheet.clip_draw(f * TILE_SRC, self.sheet.h - (kind + 1) * TILE_SRC * 2, TILE_SRC, TILE_SRC * 2,
                                 (c + 0.5) * TILE, cy, TILE, TILE * 2)
