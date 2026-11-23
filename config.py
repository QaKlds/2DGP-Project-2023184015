# 게임 전체에서 함께 쓰는 설정값

WIDTH, HEIGHT = 1920, 1080
FULLSCREEN = True

# 게임 계산은 FPS와 상관없이 항상 1/120초 간격으로 함 (어느 컴퓨터에서든 점프 높이·거리가 똑같음).
# 화면은 컴퓨터가 낼 수 있는 만큼 그림
TICK_RATE = 120
TICK = 1 / TICK_RATE
MAX_FRAME_TIME = 0.05         # 한 프레임이 이보다 오래 걸리면 잘라냄 (20 FPS 미만이면 게임이 느려지는 대신 몰아서 계산하다 멈추지 않게)

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

# 화면 왼쪽 위 HUD (시간 / 높이 패널). 값은 원본 px (asset/hud/hud.json 참고)
HUD_SCALE = 2                 # 원본 패널 128x32 → 화면 256x64
HUD_MARGIN = 8                # 화면 왼쪽·위 끝에서 첫 패널까지
HUD_GAP = 4                   # 패널 사이 간격
HUD_MAX_TIME = 99 * 3600 + 59 * 60 + 59    # 시간 표시 최대값 (99:59:59)

# 일시정지 메뉴 (게임 중 ESC)
PAUSE_DIM = 0.6               # 메뉴 뒤 게임 화면을 덮는 검은색의 진하기 (0~1)

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
ICE_LANDING_SPEED = MOVE_SPEED / 3   # 얼음(미끄러운 상태)에 착지하는 순간 가로 속도를 이 값까지 줄임 → 다시 가속

# 경사면 (밟으면 조작할 수 없고 아래쪽으로 미끄러짐)
SLOPE_SPEED = MOVE_SPEED * 1.2    # 미끄러지는 최고 속도 (px/s)
SLOPE_ACCEL = 2000                # 미끄러지는 속도가 붙는 가속도 (px/s^2)
SLOPE_AIR_DECEL = 500             # 경사면·얼음 끝에서 미끄러져 떨어질 때 가로 속도가 줄어드는 감속도 (px/s^2, 작을수록 멀리 날아감)

# 부서지는 발판 (밟으면 흔들리다 부서지고, 시간이 지나면 다시 생김)
CRUMBLE_SHAKE_TIME = 0.4      # 밟은 뒤 흔들리는 시간 (초). 한 번 밟으면 바로 떠나도 부서짐
CRUMBLE_RESPAWN_TIME = 3.0    # 부서진 뒤 다시 생기기 시작할 때까지 (초)

# 움직이는 발판 (맵에 표시한 범위 안을 좌우 또는 위아래로 왕복, 올라탄 플레이어를 함께 옮김)
MOVING_SPEED = 120            # 이동 속도 (px/s)
MOVING_PAUSE = 0.5            # 범위 끝에서 멈춰 있는 시간 (초)

# 피격
FALL_HEIGHT_SLIDE = 54        # 높은 곳에서 떨어져 넘어질 때 뒤로 미끄러지는 거리 (px)
                              # 누울 때 옮기는 27px와 합쳐 총 81px 밀림
KNOCK_BOUNCE_UP = 24          # 넘어진 채로 다시 높이 떨어지면 누운 채 튀어 오르는 높이 (px, 반 칸)
KNOCK_SLIDE_DECEL = 1200      # 누운 채 바닥에서 미끄러질 때 감속 (px/s^2)
INVINCIBLE_TIME = 1.0         # 함정·적에 맞은 순간부터 다시 안 맞는 시간 (초)
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
ENEMY_HIT_INTERVAL = 0.5          # 적에 계속 닿아 있으면 이 간격(초)마다 다시 맞음

# 원거리 적 (몸에 닿아도 피해 없음, 투사체만 위험. 칼·총으로 한 방에 죽음)
# 고블린 궁수: 순찰하다가 바라보는 쪽 같은 높이에 플레이어가 보이면 멈춰서 활을 당긴 뒤 화살을 쏨
ARCHER_RANGE = TILE * 10          # 플레이어를 알아차리는 가로 거리 (px)
ARCHER_AIM_TIME = 0.8             # 활을 당기는 시간 (마지막 프레임이 번쩍임 = 예고)
ARCHER_REST_TIME = 1.2            # 쏜 뒤 다시 조준하기까지 서 있는 시간
ARROW_SPEED = 700                 # 화살 속도 (px/s, 직선)
ARROW_KNOCK = ENEMY_KNOCK         # 화살에 맞으면 넘어지며 날아가는 속도
# 가고일 석상: 움직이지 않다가 플레이어가 가까이 오면 플레이어 위치로 포물선 불덩이를 뱉음
GARGOYLE_RANGE_X = TILE * 12      # 깨어나는 가로 거리
GARGOYLE_RANGE_Y = TILE * 8       # 깨어나는 세로 거리
GARGOYLE_CHARGE_TIME = 0.9        # 입에 불을 모으는 시간 (예고)
GARGOYLE_REST_TIME = 2.0          # 뱉은 뒤 다음 충전까지
FIREBALL_GRAVITY = 1400           # 불덩이에 걸리는 중력 (px/s^2)
FIREBALL_SPEED_X = 400            # 날아가는 시간 = 가로 거리 / 이 값 (아래 범위로 제한)
FIREBALL_TIME = (0.6, 1.6)        # 불덩이가 목표까지 날아가는 최소·최대 시간 (초)
FIRE_KNOCK = ENEMY_KNOCK
# 서리 마법사: 서 있다가 보이는 플레이어에게 느린 얼음 구슬을 쏨. 맞으면 넘어지지 않고 잠깐 얼어붙음
FROSTMAGE_RANGE = TILE * 10       # 플레이어를 알아차리는 거리
FROSTMAGE_CHARGE_TIME = 1.0       # 지팡이에 마력을 모으는 시간
FROSTMAGE_REST_TIME = 2.0
ICE_ORB_SPEED = 220               # 얼음 구슬 속도 (px/s, 플레이어를 향해 직선)
FREEZE_TIME = 1.0                 # 얼음 구슬에 맞아 얼어붙는 시간 (초). 조작 불가, 맞은 순간 속도대로 미끄러지다 멈춤
PROJECTILE_LIFE = 6.0             # 투사체가 아무것도 안 맞고 사라지기까지 (초)
