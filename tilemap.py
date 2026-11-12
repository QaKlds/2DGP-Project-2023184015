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
ICE = 'I~'             # 미끄러운 타일
TURRET = 'T'           # 레이저 포탑 자리 (충돌만 하고 그림은 Laser가 그림)
LASER_CHARS = {
    'R': ('right', 'periodic'), 'L': ('left', 'periodic'),
    'U': ('up', 'periodic'),    'D': ('down', 'periodic'),
    'r': ('right', 'detect'),   'l': ('left', 'detect'),
    'u': ('up', 'detect'),      'd': ('down', 'detect'),
}


class TileMap:
    """글자 맵을 읽어서 타일을 그리고, 충돌 정보를 제공"""
    def __init__(self, rows):
        width = len(rows[0])
        for i, row in enumerate(rows):
            assert len(row) == width, f'맵 {i}번째 줄 길이가 다릅니다 ({len(row)} != {width})'

        self.cols, self.rows = width, len(rows)
        self.width, self.height = self.cols * TILE, self.rows * TILE
        self.start = (TILE * 2, TILE * 2)
        self.mines = []        # (col, row)
        self.lasers = []       # (col, row, direction, mode)

        # grid[row][col], row 0 = 맨 아래 줄
        self.grid = []
        for b, line in enumerate(reversed(rows)):
            out = []
            for c, ch in enumerate(line):
                if ch == 'P':
                    self.start = ((c + 0.5) * TILE, b * TILE)
                    ch = '.'
                elif ch == 'M':
                    self.mines.append((c, b))
                    ch = '.'
                elif ch in LASER_CHARS:
                    self.lasers.append((c, b) + LASER_CHARS[ch])
                    ch = TURRET
                out.append(ch)
            self.grid.append(out)

        self.brick = load_image('asset/tiles/tiles_brick.png')
        self.frozen = load_image('asset/tiles/tiles_frozen.png')

    # ---------------- 조회 ----------------
    def at(self, c, b):
        if 0 <= c < self.cols and 0 <= b < self.rows:
            return self.grid[b][c]
        return '#'           # 맵 밖은 벽 취급

    def is_solid(self, c, b):
        return self.at(c, b) != '.'

    def tile_rect(self, c, b):
        """타일의 충돌 사각형 (left, bottom, right, top) 또는 None"""
        ch = self.at(c, b)
        if ch == '.':
            return None
        l, bt = c * TILE, b * TILE
        if ch in FLOATS:
            return l, bt + TILE - FLOAT_SOLID_H, l + TILE, bt + TILE
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

    def ray_end(self, c, b, dc, db):
        """(c, b) 다음 칸부터 (dc, db) 방향으로 막히기 직전 칸까지 진행. 레이저 길이 계산용"""
        cells = []
        c, b = c + dc, b + db
        while not self.is_solid(c, b):
            cells.append((c, b))
            c, b = c + dc, b + db
        return cells

    # ---------------- 그리기 ----------------
    def _pick(self, c, b, ch):
        same = lambda cc, bb: self.at(cc, bb) == ch
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
                    img = self.frozen if ch in ICE else self.brick
                    img.clip_draw(col * TILE_SRC, img.h - (row + 1) * TILE_SRC, TILE_SRC, TILE_SRC,
                                  c * TILE + TILE / 2, sy, TILE, TILE)
