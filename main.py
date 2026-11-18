from pico2d import *

from archer import Archer
from bat import Bat
from bullet import Bullet
from camera import Camera
from collision import overlap
from config import WIDTH, HEIGHT, FULLSCREEN, TILE, PLAYER_H
from frost_mage import FrostMage
from gargoyle import Gargoyle
from goblin import Goblin
from laser import Laser
from level_data import TEST_MAP, TEST_ZONES
from mine import Mine
from tower import Tower
from player import Player
from projectile import Projectile
from tilemap import TileMap

# ---------------------------------------------------------------
# 함정 + 적 테스트
#   ←→ : 이동          ↑ : 점프 (짧게 누르면 낮은 점프)      Z : 공격
#   TAB : 무기 교체 (칼 <-> 총)       X : 제자리 넘어지기
#   R   : 시작 위치로 돌아가기        ESC : 종료
#   1~4 : 각 구간(나무/벽돌/얼음/금) 첫 발판으로 순간이동 (테스트용)
# ---------------------------------------------------------------

BACKGROUNDS = ['asset/bg_low.png', 'asset/bg_mid.png', 'asset/bg_high.png']
STATE_NAMES = {'idle': '대기', 'walk': '이동', 'jump': '점프', 'land': '착지', 'attack': '공격',
               'jump_attack': '점프 공격', 'fall': '넘어짐', 'fall_height': '낙하 넘어짐', 'down': '쓰러짐', 'getup': '일어남', 'slide': '미끄러짐'}
TELEPORT_KEYS = {SDLK_1: 0, SDLK_2: 1, SDLK_3: 2, SDLK_4: 3}     # 숫자 키 → 구간 번호
SHOOTER_CLASSES = {'A': Archer, 'K': Gargoyle, 'F': FrostMage}  # 맵 글자 → 원거리 적


def draw_background(images, cam_y, map_height):
    # 올라간 높이에 따라 아래/중간/위 배경으로 바뀜. 320px 이미지를 화면 너비에 맞춰 늘려 그림
    progress = cam_y / max(1, map_height - HEIGHT)
    img = images[min(len(images) - 1, int(progress * len(images)))]
    img.draw(WIDTH / 2, HEIGHT / 2, WIDTH, WIDTH)


def main():
    open_canvas(WIDTH, HEIGHT, full=FULLSCREEN)
    hide_cursor()
    try:
        font = load_font('C:/Windows/Fonts/malgun.ttf', 24)
    except Exception:
        font = None

    tilemap = TileMap(TEST_MAP, TEST_ZONES)
    backgrounds = [load_image(p) for p in BACKGROUNDS]
    tower = Tower()
    player = Player(*tilemap.start)
    lasers = [Laser(tilemap, *info) for info in tilemap.lasers]
    mines = [Mine(*pos) for pos in tilemap.mines]
    shooters = [SHOOTER_CLASSES[ch](c, b, facing) for ch, c, b, facing in tilemap.shooters]
    enemies = [Goblin(*pos) for pos in tilemap.goblins] + [Bat(*info) for info in tilemap.bats] + shooters
    bullets = []
    projectiles = []          # 적이 쏜 화살·불덩이·얼음 구슬
    camera = Camera(tilemap.height)
    camera.snap(player.y)

    running = True
    last = get_time()
    while running:
        now = get_time()
        dt = min(now - last, 0.05)
        last = now

        for e in get_events():
            if e.type == SDL_QUIT or (e.type == SDL_KEYDOWN and e.key == SDLK_ESCAPE):
                running = False
            elif e.type == SDL_KEYDOWN and e.key == SDLK_r:
                player = Player(*tilemap.start)
                camera.snap(player.y)
            elif e.type == SDL_KEYDOWN and e.key in TELEPORT_KEYS:
                # 플레이어만 옮김 (함정·적은 그대로). 들고 있던 무기는 유지
                weapon = player.weapon
                player = Player(*tilemap.zone_start(TELEPORT_KEYS[e.key]))
                player.weapon = weapon
                camera.snap(player.y)
            else:
                player.handle_event(e)

        player.update(dt, tilemap)
        for laser in lasers:
            laser.update(dt, player)
        for mine in mines:
            mine.update(dt, player, camera.y)
        for enemy in enemies:
            enemy.update(dt, tilemap, player)
        # 원거리 적이 이번에 쏜 투사체를 가져와서 날림
        for shooter in shooters:
            projectiles += shooter.shots
            shooter.shots.clear()
        for proj in projectiles:
            proj.update(dt, tilemap, player)
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
            bullet.update(dt, tilemap, enemies, mines)
        bullets = [b for b in bullets if b.alive]
        camera.update(dt, player.y)

        clear_canvas()
        cam = int(camera.y)
        draw_background(backgrounds, cam, tilemap.height)
        tower.draw(cam)
        tilemap.draw(cam)
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

        if font:
            weapon = '칼' if player.weapon == 'sword' else '총'
            height_m = (player.y - tilemap.start[1]) / TILE
            info = f'무기: {weapon}   상태: {STATE_NAMES.get(player.state, player.state)}   높이: {height_m:.1f}칸'
            if player.on_ice:
                info += '   [얼음]'
            if player.frozen > 0:
                info += f'   [얼어붙음 {player.frozen:.1f}초]'
            if player.invincible > 0:
                info += f'   [무적 {player.invincible:.1f}초]'
            font.draw(70, HEIGHT - 30, info, (255, 255, 255))
            font.draw(70, HEIGHT - 65, '←→ 이동 / ↑ 점프 / Z 공격 / TAB 무기교체 / X 넘어짐 / R 처음으로 / 1~4 구간 이동 / ESC 종료',
                      (230, 230, 230))
        update_canvas()

    close_canvas()


if __name__ == '__main__':
    main()
