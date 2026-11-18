from config import (GARGOYLE_RANGE_X, GARGOYLE_RANGE_Y, GARGOYLE_CHARGE_TIME, GARGOYLE_REST_TIME,
                    FIREBALL_GRAVITY, FIREBALL_SPEED_X, FIREBALL_TIME)
from projectile import Projectile
from shooter import Shooter


class Gargoyle(Shooter):
    """가고일 석상: 제자리에서 움직이지 않음. 플레이어가 멀면 그냥 석상처럼 가만히 있다가
    가까이 오면 입에 불을 모으고(예고) 플레이어가 있던 자리로 포물선 불덩이를 뱉음"""
    SHEET = 'asset/enemy/gargoyle_right.png'
    FOOT_ROW = 86
    SHOOT_ORIGIN = (64, 62)
    HALF_W, HEIGHT = 24, 58
    AIM_TIME, REST_TIME = GARGOYLE_CHARGE_TIME, GARGOYLE_REST_TIME

    def notices(self, tilemap, player):
        return abs(player.x - self.x) < GARGOYLE_RANGE_X and abs(player.y - self.y) < GARGOYLE_RANGE_Y

    def fire(self, player):
        # 정한 시간 T 동안 날아가서 플레이어 몸 가운데에 떨어지는 포물선
        self.face(player.x)
        ox, oy = self.origin()
        tx, ty = self.player_center(player)
        dx, dy = tx - ox, ty - oy
        lo, hi = FIREBALL_TIME
        t = min(hi, max(lo, abs(dx) / FIREBALL_SPEED_X))
        vx = dx / t
        vy = dy / t + 0.5 * FIREBALL_GRAVITY * t
        self.shots.append(Projectile('fire', ox, oy, vx, vy, FIREBALL_GRAVITY))

    def alive_frame(self):
        if self.act == 'idle' or self.act == 'rest':
            return self.ROW_IDLE, 0              # 평소엔 움직이지 않는 석상
        return super().alive_frame()
