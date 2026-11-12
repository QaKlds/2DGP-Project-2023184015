# 게임 전체에서 함께 쓰는 설정값

WIDTH, HEIGHT = 800, 600
CELL = 100            # 스프라이트 한 칸 크기 (100x100)
SCALE = 1             # 화면에 그릴 배율
GROUND_Y = 150        # 발이 닿는 바닥 높이
FOOT_IN_CELL = 12     # 셀 아래쪽에서 발까지의 거리(px)

MOVE_SPEED = 300      # px/s
JUMP_SPEED = 600      # px/s  (꾹 누를 때 최대 점프)
JUMP_CUT_SPEED = 200  # px/s  (상승 중 키를 떼면 이 속도로 줄임 → 낮은 점프)
GRAVITY = 2200        # px/s^2
