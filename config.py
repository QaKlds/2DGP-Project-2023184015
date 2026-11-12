# 게임 전체에서 함께 쓰는 설정값

WIDTH, HEIGHT = 1920, 1080
FULLSCREEN = True

SCALE = 1.5           # 캐릭터/타일/함정을 그릴 배율 (원본 픽셀 x 1.5)
CELL = 100            # 캐릭터·함정 스프라이트 한 칸 크기 (100x100)
FOOT_IN_CELL = 18     # 캐릭터 셀 아래쪽에서 발바닥까지 16px + 잔디 위쪽 투명한 부분 2px (원본 기준)

TILE_SRC = 32                       # 타일 원본 크기
TILE = int(TILE_SRC * SCALE)        # 화면에 그려지는 타일 크기 (48px)

# 플레이어 충돌 박스 (발 중앙 기준)
PLAYER_HALF_W = 15
PLAYER_H = 66

# 이동 수치 (800x600 / 배율 1 에서 맞춘 값 x SCALE)
MOVE_SPEED = 300 * SCALE      # px/s
JUMP_SPEED = 600 * SCALE      # px/s  (꾹 누를 때 최대 점프)
JUMP_CUT_SPEED = 200 * SCALE  # px/s  (상승 중 키를 떼면 이 속도로 줄임 → 낮은 점프)
GRAVITY = 2200 * SCALE        # px/s^2
MAX_FALL_SPEED = 1500         # px/s

# 얼음
ICE_ACCEL = 900               # 얼음 위에서 원하는 속도까지 붙는 가속도 (px/s^2)
ICE_FRICTION = 500            # 얼음 위에서 키를 뗐을 때 감속 (작을수록 오래 미끄러짐)

# 피격
INVINCIBLE_TIME = 2.0         # 일어난 뒤 무적 시간 (초)
MINE_KNOCK = (450, 800)       # 지뢰 폭발 시 (수평, 수직) 날아가는 속도
LASER_KNOCK = (400, 450)      # 레이저 피격 시 (수평, 수직) 밀려나는 속도
