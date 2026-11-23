from pico2d import *

from config import WIDTH, HEIGHT, FULLSCREEN, TILE, PLAYER_H, TICK, MAX_FRAME_TIME
from level_data import TEST_MAP, TEST_ZONES
from core.camera import Camera
from core.collision import overlap
from core.tilemap import TileMap
from core.tower import Tower
from player.player import Player
from player.bullet import Bullet
from enemies.goblin import Goblin
from enemies.bat import Bat
from enemies.archer import Archer
from enemies.gargoyle import Gargoyle
from enemies.frost_mage import FrostMage
from enemies.projectile import Projectile
from traps.laser import Laser
from traps.mine import Mine
from platforms.crumble_platform import CrumblePlatform
from platforms.moving_platform import MovingPlatform
from ui.hud import Hud
from ui.title import TitleScreen

# ---------------------------------------------------------------
# 시작화면: ↑↓ 또는 마우스로 고르고 Enter / Z / 클릭으로 결정 (START = 게임 시작, QUIT·ESC = 종료)
# 게임 (함정 + 적 테스트)
#   ←→ : 이동          ↑ : 점프 (짧게 누르면 낮은 점프)      Z : 공격
#   TAB : 무기 교체 (칼 <-> 총)       X : 제자리 넘어지기
#   R   : 시작 위치로 돌아가기        ESC : 종료
#   1~4 : 각 구간(나무/벽돌/얼음/금) 첫 발판으로 순간이동 (테스트용)
# ---------------------------------------------------------------

BACKGROUNDS = ['asset/bg_low.png', 'asset/bg_mid.png', 'asset/bg_high.png']
TELEPORT_KEYS = {SDLK_1: 0, SDLK_2: 1, SDLK_3: 2, SDLK_4: 3}     # 숫자 키 → 구간 번호
SHOOTER_CLASSES = {'A': Archer, 'K': Gargoyle, 'F': FrostMage}  # 맵 글자 → 원거리 적


def draw_background(images, cam_y, map_height):
    # 올라간 높이에 따라 아래/중간/위 배경으로 바뀜. 320px 이미지를 화면 너비에 맞춰 늘려 그림
    progress = cam_y / max(1, map_height - HEIGHT)
    img = images[min(len(images) - 1, int(progress * len(images)))]
    img.draw(WIDTH / 2, HEIGHT / 2, WIDTH, WIDTH)


def run_title():
    """시작화면을 보여주고 고른 메뉴('start' / 'quit')를 돌려줌"""
    title = TitleScreen()
    show_cursor()
    last = get_time()
    while True:
        now = get_time()
        dt = min(now - last, MAX_FRAME_TIME)
        last = now
        for e in get_events():
            if e.type == SDL_QUIT or (e.type == SDL_KEYDOWN and e.key == SDLK_ESCAPE):
                return 'quit'
            choice = title.handle_event(e)
            if choice:
                return choice
        title.update(dt)
        clear_canvas()
        title.draw()
        update_canvas()


def play(hud):
    """게임 한 판. ESC나 창 닫기로 끝남. hud는 최고기록을 이어서 기억하도록 밖에서 받음"""
    hide_cursor()
    tilemap = TileMap(TEST_MAP, TEST_ZONES)
    backgrounds = [load_image(p) for p in BACKGROUNDS]
    tower = Tower()
    player = Player(*tilemap.start)
    # 부서지는·움직이는 발판 (구역 무늬를 따르고, 얼음 구역에서는 미끄러움). 타일맵 충돌 확인에 함께 들어감
    crumbles = [CrumblePlatform(c0, c1, b, tilemap.zone_at(b), tilemap.zone_at(b) == 'frozen')
                for c0, c1, b in tilemap.crumbles]
    movers = [MovingPlatform(c0, c1, b, axis, lo, hi, tilemap.zone_at(b), tilemap.zone_at(b) == 'frozen')
              for c0, c1, b, axis, lo, hi in tilemap.movers]
    tilemap.platforms = crumbles + movers
    lasers = [Laser(tilemap, *info) for info in tilemap.lasers]
    mines = [Mine(*pos) for pos in tilemap.mines]
    shooters = [SHOOTER_CLASSES[ch](c, b, facing) for ch, c, b, facing in tilemap.shooters]
    enemies = [Goblin(*pos) for pos in tilemap.goblins] + [Bat(*info) for info in tilemap.bats] + shooters
    bullets = []
    projectiles = []          # 적이 쏜 화살·불덩이·얼음 구슬
    camera = Camera(tilemap.height)
    camera.snap(player.y)
    play_time = 0.0           # 게임 시작부터 흐른 시간 (R을 누르면 0으로)

    running = True
    last = get_time()
    lag = 0.0                 # 아직 계산하지 못한 시간 (TICK 만큼씩 꺼내서 계산)
    while running:
        now = get_time()
        lag += min(now - last, MAX_FRAME_TIME)
        last = now

        for e in get_events():
            if e.type == SDL_QUIT or (e.type == SDL_KEYDOWN and e.key == SDLK_ESCAPE):
                running = False
            elif e.type == SDL_KEYDOWN and e.key == SDLK_r:
                player = Player(*tilemap.start)
                camera.snap(player.y)
                play_time = 0.0
            elif e.type == SDL_KEYDOWN and e.key in TELEPORT_KEYS:
                # 플레이어만 옮김 (함정·적은 그대로). 들고 있던 무기는 유지
                weapon = player.weapon
                player = Player(*tilemap.zone_start(TELEPORT_KEYS[e.key]))
                player.weapon = weapon
                camera.snap(player.y)
            else:
                player.handle_event(e)

        # 게임 계산: 지난 프레임부터 흐른 시간만큼 TICK 간격으로 나눠서 (FPS가 높으면 0번, 낮으면 여러 번)
        while lag >= TICK:
            lag -= TICK
            play_time += TICK
            for mover in movers:
                mover.update(TICK, tilemap, player)      # 올라탄 플레이어를 먼저 옮긴 뒤 플레이어 이동
            player.update(TICK, tilemap)
            for crumble in crumbles:
                crumble.update(TICK, player)
            for laser in lasers:
                laser.update(TICK, player)
            for mine in mines:
                mine.update(TICK, player, camera.y)
            for enemy in enemies:
                enemy.update(TICK, tilemap, player)
            # 원거리 적이 이번에 쏜 투사체를 가져와서 날림
            for shooter in shooters:
                projectiles += shooter.shots
                shooter.shots.clear()
            for proj in projectiles:
                proj.update(TICK, tilemap, player)
            projectiles = [p for p in projectiles if p.alive]

            # 칼: 휘두르는 프레임에 칼 범위에 닿은 적은 죽음
            sword = player.sword_rect()
            if sword:
                for enemy in enemies:
                    if enemy.is_alive() and overlap(sword, enemy.hitbox()):
                        enemy.kill()
                for mine in mines:
                    if mine.is_armed() and overlap(sword, mine.rect()):
                        mine.defuse()                   # 칼로 벤 지뢰는 터지지만 피해 없음
                for proj in projectiles:
                    if proj.is_flying() and overlap(sword, proj.rect()):
                        proj.burst()                    # 칼로 벤 투사체는 터지며 사라짐
            # 총: 이번에 쏜 총알을 만들고, 날아가다 블록이나 적에 닿으면 사라짐
            bullets += [Bullet(*shot) for shot in player.shots]
            player.shots.clear()
            for bullet in bullets:
                bullet.update(TICK, tilemap, enemies, mines)
            bullets = [b for b in bullets if b.alive]
            camera.update(TICK, player.y)

        clear_canvas()
        cam = int(camera.y)
        draw_background(backgrounds, cam, tilemap.height)
        tower.draw(cam)
        tilemap.draw(cam)
        for platform in tilemap.platforms:
            platform.draw(cam)
        for trap in mines + lasers:
            trap.draw(cam)
        for enemy in enemies:
            enemy.draw(cam)
        for bullet in bullets:
            bullet.draw(cam)
        player.draw(cam)
        if player.frozen > 0:
            Projectile.draw_frost(player.x, player.y + PLAYER_H / 2, get_time(), cam)
        for proj in projectiles:
            proj.draw(cam)

        # 왼쪽 위 HUD: 경과 시간, 시작 바닥부터 지금 발 높이 (1칸 = 1m)
        height_m = (player.y - tilemap.start[1]) / TILE
        hud.record(height_m)
        hud.draw(play_time, height_m)
        update_canvas()


def main():
    open_canvas(WIDTH, HEIGHT, full=FULLSCREEN)
    hud = Hud()               # 최고기록은 게임을 켜 둔 동안 유지
    if run_title() == 'start':
        play(hud)
    close_canvas()


if __name__ == '__main__':
    main()
