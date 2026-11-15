# 게임 전체에서 함께 쓰는 설정값

WIDTH, HEIGHT = 1920, 1080
FULLSCREEN = True

SCALE = 1.5           # 캐릭터/타일/함정을 그릴 배율 (원본 픽셀 x 1.5)
CELL = 100            # 캐릭터·함정 스프라이트 한 칸 크기 (100x100)
FOOT_IN_CELL = 18     # 캐릭터 셀 아래쪽에서 발바닥까지 16px + 잔디 위쪽 투명한 부분 2px (원본 기준)

TILE_SRC = 32                       # 타일 원본 크기
TILE = int(TILE_SRC * SCALE)        # 화면에 그려지는 타일 크기 (48px)

# 탑: 320px 조각을 5배(1600px)로 그려서 화면 가운데에 세우고, 플레이어는 탑 안쪽 28칸에서만 움직임
TOWER_DIR = 'asset/tower/tower_re'
TOWER_SCALE = 5
TOWER_PIECE = 320                   # 탑 조각 원본 크기 (양옆 기둥 24px + 안쪽 272px)
TOWER_PILLAR = 24                   # 기둥 원본 폭
TOWER_INNER_COL = 6                 # 탑 안쪽이 시작하는 맵 칸 (6~33칸이 안쪽 28칸)
TOWER_INNER_COLS = 28               # 안쪽 칸 수 (안쪽 1360px 중 1344px, 남는 8px씩은 기둥 옆 여백)
# 아래부터 쌓는 탑 조각 (테스트용으로 짧게: 맨 아래 → 구간 연결 조각들 → 꼭대기)
TOWER_PIECES = ['tower_bottom', 'tower_trans_wood_brick', 'tower_trans_brick_frozen',
                'tower_trans_frozen_gold', 'tower_top']

# 플레이어 충돌 박스 (발 중앙 기준)
PLAYER_HALF_W = 15
PLAYER_H = 66

# 이동 수치 (800x600 / 배율 1 에서 맞춘 값 x SCALE)
MOVE_SPEED = 300 * SCALE      # px/s
JUMP_SPEED = 600 * SCALE      # px/s  (꾹 누를 때 최대 점프)
JUMP_CUT_SPEED = 200 * SCALE  # px/s  (상승 중 키를 떼면 이 속도로 줄임 → 낮은 점프)
GRAVITY = 2200 * SCALE        # px/s^2
MAX_FALL_SPEED = 1500         # px/s  떨어지는 최고 속도 (가만히 떨어지기 시작해서 약 340px, 7칸이면 도달)

# 얼음
ICE_ACCEL = 900               # 얼음 위에서 원하는 속도까지 붙는 가속도 (px/s^2)
ICE_FRICTION = 500            # 얼음 위에서 키를 뗐을 때 감속 (작을수록 오래 미끄러짐)
ICE_EDGE_SPEED = 150          # 얼음 끝에 걸쳐 있으면 바깥으로 미끄러져 떨어지는 속도 (px/s)

# 경사면 (밟으면 조작할 수 없고 아래쪽으로 미끄러짐)
SLOPE_SPEED = MOVE_SPEED * 1.2    # 미끄러지는 최고 속도 (px/s)
SLOPE_ACCEL = 2000                # 미끄러지는 속도가 붙는 가속도 (px/s^2)
SLOPE_AIR_DECEL = 500             # 경사면 끝에서 날아갈 때 가로 속도가 줄어드는 감속도 (px/s^2, 작을수록 멀리 날아감)

# 피격
INVINCIBLE_TIME = 1.0         # 일어난 뒤 무적 시간 (초)
FALL_HEIGHT_SLIDE = 54        # 높은 곳에서 떨어져 넘어질 때 뒤로 미끄러지는 거리 (px)
                              # 누울 때 옮기는 27px와 합쳐 총 81px 밀림
MINE_KNOCK = (450, 800)       # 지뢰 폭발 시 (수평, 수직) 날아가는 속도
LASER_KNOCK = (400, 450)      # 레이저 피격 시 (수평, 수직) 밀려나는 속도

# 총 반동 (총을 쏘는 순간 보는 방향 뒤로 밀리면서 위로 살짝 뜸)
GUN_RECOIL_UP = PLAYER_H / 2      # 위로 뜨는 높이: 캐릭터 키의 절반 (33px)
GUN_RECOIL_BACK = PLAYER_H        # 뒤로 밀리는 거리: 캐릭터 키만큼 (66px)
BULLET_SPEED = 1500               # 총알 속도 (px/s). 블록이나 적에 닿으면 사라짐

# 적
ENEMY_SPEED = MOVE_SPEED / 2      # 고블린 좌우 / 박쥐 상하 이동 속도 (플레이어 걸음의 절반, 225px/s)
ENEMY_RESPAWN_TIME = 5.0          # 죽은 뒤 다시 나타나기까지 (초)
ENEMY_KNOCK = LASER_KNOCK         # 적에 닿았을 때 밀려나는 속도 (레이저와 같음)
