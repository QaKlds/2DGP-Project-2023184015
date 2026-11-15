from pico2d import draw_rectangle

from collision import overlap
from config import BULLET_SPEED

HALF_LEN, HALF_THICK = 8, 2      # 노란 막대 크기 (px)
MAX_STEP = 8                     # 한 번에 움직이는 최대 거리 (적을 뚫고 지나가지 않게)


class Bullet:
    """총알: 앞으로 날아가다 블록이나 적에 닿으면 사라짐. 적은 한 방에 죽음"""
    def __init__(self, x, y, direction):
        self.x, self.y = x, y
        self.dir = direction
        self.alive = True

    def rect(self):
        return self.x - HALF_LEN, self.y - HALF_THICK, self.x + HALF_LEN, self.y + HALF_THICK

    def update(self, dt, tilemap, enemies):
        distance = BULLET_SPEED * dt
        while distance > 0 and self.alive:
            step = min(MAX_STEP, distance)
            distance -= step
            self.x += self.dir * step
            if tilemap.solids_in(*self.rect()) or not (0 <= self.x <= tilemap.width):
                self.alive = False
                return
            for enemy in enemies:
                if enemy.is_alive() and overlap(self.rect(), enemy.hitbox()):
                    enemy.kill()
                    self.alive = False
                    return

    def draw(self, cam_y):
        l, b, r, t = self.rect()
        draw_rectangle(l, b - cam_y, r, t - cam_y, 255, 220, 60, 255, filled=True)
