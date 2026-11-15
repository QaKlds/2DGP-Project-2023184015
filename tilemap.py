from pico2d import load_image

from config import TILE, TILE_SRC, SCALE, HEIGHT

# 타일 시트 안의 위치 (열, 행) - asset/tiles/tiles.json 참고
TOP = [(0, 0), (1, 0), (2, 0)]
TOP_LEFT_END, TOP_RIGHT_END = (3, 0), (4, 0)
FILL = [(5, 0), (6, 0), (5, 0), (6, 0), (7, 0)]
WALL_LEFT, WALL_RIGHT = (2, 1), (3, 1)
UNDER, UNDER_LEFT, UNDER_RIGHT = (4, 1), (5, 1), (6, 1)
FLOAT_LEFT, FLOAT_MID, FLOAT_RIGHT, FLOAT_SINGLE = (0, 2), (1, 2), (3, 2), (4, 2)
FLOAT_MID_B = (2, 2)

FLOAT_SOLID_H = int(20 * SCALE)     # 발판 그림은 타일 위쪽 20px만 차지하므로 충돌도 그만큼만

BLOCKS = '#I'          # 꽉 찬 블록
FLOATS = '=~'          # 얇은 발판
HALF = '-'             # 반 칸 발판 (칸 가운데 24px만 있음)
HALF_SRC_END = 8       # 반 칸 발판 그림: 1칸 발판 그림의 왼쪽 끝 8px + 오른쪽 끝 8px을 이어 붙임
HALF_W = HALF_SRC_END * 2 * SCALE      # 화면에서 반 칸 발판 폭 (24px)
ICE = 'I~'             # 미끄러운 타일
TURRET = 'T'           # 레이저 장치 자리 (충돌만 하고 그림은 Laser가 그림)
RECEIVER = '*'         # 레이저 받는 장치
BAT_RANGE = ':'        # 박쥐가 날아다니는 범위 표시 (빈 칸 취급)
WALL = '|'             # 보이지 않는 벽 (탑 돌기둥 안쪽 경계. 막히기만 하고 그리지 않음)
# 45도 경사면 (asset/tiles/tiles_diag_*.png, 칸 번호 = 꽉 찬 모서리)
#   /  바닥 경사: 오른쪽이 높음 (오른쪽 아래가 꽉 참)     \  바닥 경사: 왼쪽이 높음 (왼쪽 아래가 꽉 참)
#   [  천장 경사: 오른쪽 아래가 비어 있음                  ]  천장 경사: 왼쪽 아래가 비어 있음
FLOOR_SLOPES = {'/': 1, '\\': -1}       # 값 = 경사면이 올라가는 방향 (미끄러지는 방향은 반대)
CEIL_SLOPES = '[]'
SLOPES = '/\\[]'
DIAG_INDEX = {'\\': 0, '/': 1, '[': 2, ']': 3}
LASER_CHARS = {
    'R': ('right', 'periodic'), 'L': ('left', 'periodic'),
    'U': ('up', 'periodic'),    'D': ('down', 'periodic'),
    'r': ('right', 'detect'),   'l': ('left', 'detect'),
    'u': ('up', 'detect'),      'd': ('down', 'detect'),
}


class TileMap:
    """글자 맵을 읽어서 타일을 그리고, 충돌 정보를 제공"""
    def __init__(self, rows, zones=((0, 'brick'),)):
        width = len(rows[0])
        for i, row in enumerate(rows):
            assert len(row) == width, f'맵 {i}번째 줄 길이가 다릅니다 ({len(row)} != {width})'

        self.cols, self.rows = width, len(rows)
        self.width, self.height = self.cols * TILE, self.rows * TILE
        self.start = (TILE * 2, TILE * 2)
        self.mines = []        # (col, row)
        self.lasers = []       # (col, row, direction, mode)
        self.receivers = set() # (col, row)
        self.goblins = []      # (col, row)
        self.bats = []         # (col, row, 범위 아래 줄, 범위 위 줄)

        # grid[row][col], row 0 = 맨 아래 줄
        lines = list(reversed(rows))
        self.grid = []
        for b, line in enumerate(lines):
            out = []
            for c, ch in enumerate(line):
                if ch == 'P':
                    self.start = ((c + 0.5) * TILE, b * TILE)
                    ch = '.'
                elif ch == 'M':
                    self.mines.append((c, b))
                    ch = '.'
                elif ch == 'G':
                    self.goblins.append((c, b))
                    ch = '.'
                elif ch == 'B':
                    # B 위아래로 이어진 ':' 칸까지가 박쥐가 날아다니는 범위
                    low = high = b
                    while low - 1 >= 0 and lines[low - 1][c] == BAT_RANGE:
                        low -= 1
                    while high + 1 < len(lines) and lines[high + 1][c] == BAT_RANGE:
                        high += 1
                    self.bats.append((c, b, low, high))
                    ch = '.'
                elif ch == BAT_RANGE:
                    ch = '.'
                elif ch in LASER_CHARS:
                    self.lasers.append((c, b) + LASER_CHARS[ch])
                    ch = TURRET
                elif ch == RECEIVER:
                    self.receivers.add((c, b))
                    ch = TURRET
                out.append(ch)
            self.grid.append(out)

        # 구간별 타일 무늬: zones = [(시작 줄, 무늬), ...]  무늬 = wood / brick / frozen / gold
        self.zones = sorted(zones)
        self.sheets = {style: load_image(f'asset/tiles/tiles_{style}.png')
                       for style in ('wood', 'brick', 'frozen', 'gold')}
        self.diag_sheets = {style: load_image(f'asset/tiles/tiles_diag_{style}.png')
                            for style in ('wood', 'brick', 'frozen', 'gold')}

    # ---------------- 조회 ----------------
    def at(self, c, b):
        if 0 <= c < self.cols and 0 <= b < self.rows:
            return self.grid[b][c]
        return '#'           # 맵 밖은 벽 취급

    def is_solid(self, c, b):
        return self.at(c, b) != '.'

    def tile_rect(self, c, b):
        """타일의 충돌 사각형 (left, bottom, right, top) 또는 None. 경사면은 사각형이 아니라서 None"""
        ch = self.at(c, b)
        if ch == '.' or ch in SLOPES:
            return None
        l, bt = c * TILE, b * TILE
        if ch in FLOATS:
            return l, bt + TILE - FLOAT_SOLID_H, l + TILE, bt + TILE
        if ch == HALF:
            hl = l + (TILE - HALF_W) / 2
            return hl, bt + TILE - FLOAT_SOLID_H, hl + HALF_W, bt + TILE
        return l, bt, l + TILE, bt + TILE

    def solids_in(self, l, b, r, t):
        """주어진 사각형과 겹치는 충돌 사각형들: [(rect, 얼음 여부)]"""
        out = []
        for row in range(int(b // TILE), int(t // TILE) + 1):
            for col in range(int(l // TILE), int(r // TILE) + 1):
                rect = self.tile_rect(col, row)
                if rect and l < rect[2] and r > rect[0] and b < rect[3] and t > rect[1]:
                    out.append((rect, self.at(col, row) in ICE))
        return out

    # ---------------- 경사면 ----------------
    def slope_height(self, c, b, x):
        """바닥 경사 칸 (c, b)에서 x 위치의 경사면 높이 (칸 밖의 x는 칸 끝으로 맞춤)"""
        rel = min(max(x - c * TILE, 0), TILE)
        if FLOOR_SLOPES[self.at(c, b)] > 0:
            return b * TILE + rel
        return b * TILE + TILE - rel

    def floor_slope(self, x, y, below, above=0.0):
        """x 위치에서 높이가 y-below ~ y+above 사이인 바닥 경사면 중 가장 높은 것: (높이, 올라가는 방향) 또는 None"""
        c = int(x // TILE)
        best = None
        for b in range(int((y + above) // TILE), int((y - below) // TILE) - 1, -1):
            if self.at(c, b) in FLOOR_SLOPES:
                h = self.slope_height(c, b, x)
                if y - below <= h <= y + above and (best is None or h > best[0]):
                    best = (h, FLOOR_SLOPES[self.at(c, b)])
        return best

    def slopes_in(self, l, b, r, t):
        """사각형과 겹치는 칸 중 경사면 칸들: [(c, row, 글자)]"""
        out = []
        for row in range(int(b // TILE), int(t // TILE) + 1):
            for col in range(int(l // TILE), int(r // TILE) + 1):
                ch = self.at(col, row)
                if ch in SLOPES and l < (col + 1) * TILE and r > col * TILE and b < (row + 1) * TILE and t > row * TILE:
                    out.append((col, row, ch))
        return out

    def point_in_slope(self, x, y):
        """점 (x, y)가 경사면 칸의 꽉 찬 부분 안에 있는지 (총알용)"""
        c, b = int(x // TILE), int(y // TILE)
        ch = self.at(c, b)
        if ch not in SLOPES:
            return False
        rx, ry = x - c * TILE, y - b * TILE
        if ch == '/':
            return ry < rx
        if ch == '\\':
            return ry < TILE - rx
        if ch == '[':
            return ry > rx
        return rx + ry > TILE

    def is_surface(self, c, b):
        """(c, b) 바로 위 칸이 비어 있으면 땅 윗면 (잔디·눈이 덮인 타일이 보이는 자리)"""
        return not self.is_solid(c, b + 1)

    def zone_at(self, b):
        """b줄이 속한 탑 구간의 무늬"""
        style = self.zones[0][1]
        for start, s in self.zones:
            if b >= start:
                style = s
        return style

    def zone_start(self, index):
        """index번째 구간(0부터)의 첫 발판 위 발 위치 (x, y). 첫 구간은 시작 위치.
        구간 시작 줄 이상에서 가장 낮은 평평한 땅(경사면 제외, 위 2칸이 빈 곳)의 가운데"""
        if index == 0:
            return self.start
        first = self.zones[index][0]
        for b in range(first, self.rows):
            run = [c for c in range(self.cols)
                   if self.at(c, b) in BLOCKS + FLOATS + HALF
                   and not self.is_solid(c, b + 1) and not self.is_solid(c, b + 2)]
            if run:
                # 같은 줄에 발판이 여러 개면 맨 왼쪽 발판의 가운데
                end = 0
                while end + 1 < len(run) and run[end + 1] == run[end] + 1:
                    end += 1
                c = (run[0] + run[end]) / 2
                return (c + 0.5) * TILE, (b + 1) * TILE
        return self.start

    def style_at(self, c, b):
        """(c, b) 주변 8칸에 얼음이 있으면 'frozen', 아니면 그 줄의 구간 무늬 - 레이저 장치 무늬를 주변 땅에 맞추는 용도"""
        for dc in (-1, 0, 1):
            for db in (-1, 0, 1):
                if self.at(c + dc, b + db) in ICE:
                    return 'frozen'
        return self.zone_at(b)

    def ray(self, c, b, dc, db):
        """(c, b) 다음 칸부터 (dc, db) 방향으로 진행. (지나간 빈 칸들, 막힌 칸) 반환. 레이저 길이 계산용"""
        cells = []
        c, b = c + dc, b + db
        while not self.is_solid(c, b):
            cells.append((c, b))
            c, b = c + dc, b + db
        return cells, (c, b)

    # ---------------- 그리기 ----------------
    def _pick(self, c, b, ch):
        # 블록 사이에 박힌 레이저 장치는 같은 블록으로 보고 이어지게 그림 (장치 주변에 끊긴 모서리가 안 생기게)
        same = lambda cc, bb: self.at(cc, bb) == ch or (ch in BLOCKS and self.at(cc, bb) in TURRET + SLOPES)
        up, down, left, right = same(c, b + 1), same(c, b - 1), same(c - 1, b), same(c + 1, b)
        if ch in FLOATS:
            if not left and not right:
                return FLOAT_SINGLE
            if not left:
                return FLOAT_LEFT
            if not right:
                return FLOAT_RIGHT
            return FLOAT_MID if c % 2 else FLOAT_MID_B
        if not up:
            if not left and right:
                return TOP_LEFT_END
            if not right and left:
                return TOP_RIGHT_END
            return TOP[c % 3]
        if not down:
            if not left:
                return UNDER_LEFT
            if not right:
                return UNDER_RIGHT
            return UNDER
        if not left:
            return WALL_LEFT
        if not right:
            return WALL_RIGHT
        return FILL[(c * 7 + b * 13) % len(FILL)]

    def draw(self, cam_y):
        first = max(0, int(cam_y // TILE))
        last = min(self.rows - 1, int((cam_y + HEIGHT) // TILE) + 1)
        for b in range(first, last + 1):
            sy = b * TILE + TILE / 2 - cam_y
            for c in range(self.cols):
                ch = self.grid[b][c]
                if ch in BLOCKS or ch in FLOATS:
                    col, row = self._pick(c, b, ch)
                    img = self.sheets['frozen' if ch in ICE else self.zone_at(b)]
                    img.clip_draw(col * TILE_SRC, img.h - (row + 1) * TILE_SRC, TILE_SRC, TILE_SRC,
                                  c * TILE + TILE / 2, sy, TILE, TILE)
                elif ch == HALF:
                    self._draw_half(c * TILE + TILE / 2, sy, self.sheets[self.zone_at(b)])
                elif ch in SLOPES:
                    img = self.diag_sheets[self.style_at(c, b)]
                    img.clip_draw(DIAG_INDEX[ch] * TILE_SRC, 0, TILE_SRC, TILE_SRC,
                                  c * TILE + TILE / 2, sy, TILE, TILE)

    def _draw_half(self, cx, cy, img):
        """1칸 발판 그림의 양쪽 끝만 이어 붙여서 반 칸 발판으로 그림"""
        col, row = FLOAT_SINGLE
        bottom = img.h - (row + 1) * TILE_SRC
        part = HALF_SRC_END * SCALE                     # 화면에서 한쪽 조각 폭 (12px)
        img.clip_draw(col * TILE_SRC, bottom, HALF_SRC_END, TILE_SRC,
                      cx - part / 2, cy, part, TILE)
        img.clip_draw(col * TILE_SRC + TILE_SRC - HALF_SRC_END, bottom, HALF_SRC_END, TILE_SRC,
                      cx + part / 2, cy, part, TILE)
