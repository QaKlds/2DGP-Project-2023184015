import math

from config import FROSTMAGE_RANGE, FROSTMAGE_CHARGE_TIME, FROSTMAGE_REST_TIME, ICE_ORB_SPEED
from enemies.projectile import Projectile
from enemies.shooter import Shooter


class FrostMage(Shooter):
    """서리 마법사: 제자리에 떠 있다가 플레이어가 보이면 지팡이에 마력을 모으고(예고)
    플레이어 쪽으로 느린 얼음 구슬을 쏨. 맞으면 넘어지지 않고 잠깐 미끄러워짐"""
    SHEET = 'asset/enemy/frostmage_right.png'
    FOOT_ROW = 84                # 로브 아래가 살짝 떠 있는 그림
    SHOOT_ORIGIN = (70, 47)
    HALF_W, HEIGHT = 16, 58
    AIM_TIME, REST_TIME = FROSTMAGE_CHARGE_TIME, FROSTMAGE_REST_TIME

    def notices(self, tilemap, player):
        tx, ty = self.player_center(player)
        if math.hypot(tx - self.x, ty - self.y) > FROSTMAGE_RANGE:
            return False
        self.face(player.x)
        ox, oy = self.origin()
        return self.clear_line(tilemap, ox, oy, tx, ty)

    def think(self, dt, tilemap, player):
        if self.act != 'shoot':
            self.face(player.x)              # 쏘는 순간 말고는 늘 플레이어 쪽을 바라봄
        super().think(dt, tilemap, player)

    def fire(self, player):
        ox, oy = self.origin()
        tx, ty = self.player_center(player)
        dist = max(1.0, math.hypot(tx - ox, ty - oy))
        self.shots.append(Projectile('ice', ox, oy, (tx - ox) / dist * ICE_ORB_SPEED,
                                     (ty - oy) / dist * ICE_ORB_SPEED))
