"""
素材处理脚本 - 将下载的网络素材裁剪/缩放/调色后保存为游戏可用格式
"""
import os
import math
from PIL import Image, ImageFilter, ImageEnhance, ImageDraw

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC = {
    'tasdik': os.path.join(BASE_DIR, 'images', 'from_tasdik'),
    'pygalaxian': os.path.join(BASE_DIR, 'images', 'from_pygalaxian'),
    'ssg': os.path.join(BASE_DIR, 'images', 'from_spaceshootergame'),
}
OUT_DIR = os.path.join(BASE_DIR, 'images', 'processed')
os.makedirs(OUT_DIR, exist_ok=True)


def load(name, sub='tasdik'):
    path = os.path.join(SRC[sub], name)
    if os.path.exists(path):
        return Image.open(path).convert('RGBA')
    return None


def save(img, name):
    img.save(os.path.join(OUT_DIR, f'{name}.png'))
    print(f'Saved: {name}.png ({img.size})')


def tint(img, color, intensity=0.5):
    """给图片着色"""
    r, g, b = color
    tint_layer = Image.new('RGBA', img.size, (r, g, b, int(255 * intensity)))
    return Image.alpha_composite(img.copy(), tint_layer)


def glow(img, color, radius=6):
    """添加外发光效果"""
    r, g, b = color
    # 创建发光层
    alpha = img.split()[3]
    glow = Image.new('RGBA', img.size, (r, g, b, 0))
    glow.putalpha(alpha)
    glow = glow.filter(ImageFilter.GaussianBlur(radius))
    # 合并
    result = Image.new('RGBA', img.size, (0, 0, 0, 0))
    result = Image.alpha_composite(result, glow)
    result = Image.alpha_composite(result, img)
    return result


def resize(img, target_size, method=Image.LANCZOS):
    """缩放到目标尺寸，保持纵横比"""
    if isinstance(target_size, int):
        # target_size 是最大边
        w, h = img.size
        scale = target_size / max(w, h)
        new_w, new_h = int(w * scale), int(h * scale)
    else:
        new_w, new_h = target_size
    return img.resize((new_w, new_h), method)


def fit_canvas(img, size, center=True):
    """将图片放入固定尺寸画布中"""
    canvas = Image.new('RGBA', size, (0, 0, 0, 0))
    w, h = img.size
    if center:
        x = (size[0] - w) // 2
        y = (size[1] - h) // 2
    else:
        x, y = 0, 0
    canvas.paste(img, (x, y), img)
    return canvas


def extract_sprite_sheet(img, frame_size, count=None):
    """从精灵表中提取帧"""
    w, h = img.size
    fw, fh = frame_size
    cols = w // fw
    rows = h // fh
    frames = []
    for r in range(rows):
        for c in range(cols):
            x = c * fw
            y = r * fh
            frame = img.crop((x, y, x + fw, y + fh))
            frames.append(frame)
            if count and len(frames) >= count:
                return frames
    return frames


def process_player_ships():
    print('\n=== 处理玩家飞船 ===')
    # 基础飞船
    ship1 = load('playerShip1_orange.png', 'tasdik')
    ship2 = load('player.png', 'ssg')
    ship3 = load('fighter1.png', 'pygalaxian')

    if ship1:
        # player_1: 原始橙色飞船，缩小
        s = resize(ship1, 48)
        save(s, 'player_1')
        # player_2: 更大一点，加青色发光
        s2 = resize(ship1, 52)
        s2 = tint(s2, (0, 200, 255), 0.15)
        s2 = glow(s2, (0, 200, 255), 4)
        save(s2, 'player_2')
        # player_5: 紫色高级版
        s5 = resize(ship1, 64)
        s5 = tint(s5, (180, 100, 255), 0.25)
        s5 = glow(s5, (180, 100, 255), 6)
        save(s5, 'player_5')

    if ship2:
        # player_3: 白色飞船
        s3 = resize(ship2, 56)
        s3 = tint(s3, (100, 255, 200), 0.1)
        s3 = glow(s3, (100, 255, 200), 3)
        save(s3, 'player_3')

    if ship3:
        # player_4: 战斗机风格，蓝色调
        s4 = resize(ship3, 60)
        s4 = tint(s4, (80, 150, 255), 0.2)
        s4 = glow(s4, (80, 150, 255), 5)
        save(s4, 'player_4')

    # 僚机 - 用 fighter1 缩小
    if ship3:
        wing = resize(ship3, 28)
        wing = tint(wing, (255, 220, 80), 0.2)
        save(wing, 'wingman')


def process_enemies():
    print('\n=== 处理敌人 ===')
    # enemy_small: 小陨石
    m = load('meteorBrown_small1.png', 'tasdik')
    if m:
        save(resize(m, 28), 'enemy_small')

    # enemy_medium: 中型陨石
    m = load('meteorBrown_med1.png', 'tasdik')
    if m:
        save(resize(m, 40), 'enemy_medium')

    # enemy_large: 大陨石
    m = load('meteorBrown_big1.png', 'tasdik')
    if m:
        save(resize(m, 52), 'enemy_large')

    # enemy_fast: 高速飞船 (从 enemy_saucer 精灵表取一帧)
    saucer = load('enemy_saucer.png', 'pygalaxian')
    if saucer:
        frames = extract_sprite_sheet(saucer, (96, 96))
        if frames:
            fast = resize(frames[0], 32)
            fast = tint(fast, (255, 150, 50), 0.15)
            save(fast, 'enemy_fast')

    # enemy_shooter: 射手敌机
    es = load('enemyShip.png', 'ssg')
    if es:
        shooter = resize(es, 36)
        shooter = tint(shooter, (255, 100, 100), 0.1)
        save(shooter, 'enemy_shooter')

    # enemy_tank: 坦克型 (用 enemy2 或 大陨石)
    e2 = load('enemy2.png', 'pygalaxian')
    if e2:
        tank = resize(e2, 48)
        tank = tint(tank, (150, 150, 150), 0.15)
        save(tank, 'enemy_tank')
    else:
        m = load('meteorBrown_big2.png', 'tasdik')
        if m:
            save(resize(m, 48), 'enemy_tank')


def process_bosses():
    print('\n=== 处理BOSS ===')
    boss = load('boss.png', 'pygalaxian')
    station = load('spacestation.png', 'pygalaxian')
    ufo = load('enemyUFO.png', 'ssg')

    if boss:
        # boss_0: 红色拦截机风格
        b0 = resize(boss, 100)
        b0 = tint(b0, (255, 80, 80), 0.1)
        b0 = glow(b0, (255, 80, 80), 6)
        save(b0, 'boss_0')

        # boss_1: 紫色毁灭者
        b1 = resize(boss, 120)
        b1 = tint(b1, (180, 80, 255), 0.2)
        b1 = glow(b1, (180, 80, 255), 8)
        save(b1, 'boss_1')

    if station:
        # boss_2: 绿色母舰
        b2 = resize(station, 110)
        b2 = tint(b2, (80, 255, 120), 0.2)
        b2 = glow(b2, (80, 255, 120), 7)
        save(b2, 'boss_2')

    if ufo:
        # boss_3: 黄色粉碎者
        b3 = resize(ufo, 100)
        b3 = tint(b3, (255, 220, 60), 0.2)
        b3 = glow(b3, (255, 220, 60), 8)
        save(b3, 'boss_3')

    # boss_4: 蓝色幻影 (用boss图调色)
    if boss:
        b4 = resize(boss, 105)
        b4 = tint(b4, (80, 180, 255), 0.2)
        b4 = glow(b4, (80, 180, 255), 8)
        save(b4, 'boss_4')


def process_bullets():
    print('\n=== 处理子弹 ===')
    # 玩家子弹
    lr16 = load('laserRed16.png', 'tasdik')
    lg = load('laserGreen.png', 'ssg')
    lz = load('lazer.png', 'pygalaxian')
    missile = load('missile.png', 'tasdik')
    lr = load('laserRed.png', 'ssg')

    if lr16:
        bp0 = resize(lr16, (10, 20))
        save(bp0, 'bullet_player_0')
    if lg:
        bp1 = resize(lg, (10, 20))
        bp1 = tint(bp1, (100, 255, 100), 0.1)
        save(bp1, 'bullet_player_1')
    if lz:
        bp2 = resize(lz, (10, 20))
        bp2 = tint(bp2, (255, 200, 50), 0.1)
        save(bp2, 'bullet_player_2')
    if missile:
        bp3 = resize(missile, (14, 26))
        save(bp3, 'bullet_player_3')
    if lr:
        bp4 = resize(lr, (10, 20))
        bp4 = tint(bp4, (255, 100, 100), 0.1)
        save(bp4, 'bullet_player_4')

    # 敌人子弹 - 红色圆球风格
    for i in range(5):
        be = load('laserRed.png', 'ssg')
        if be:
            be = resize(be, (10, 10))
            # 不同颜色
            colors = [(255, 80, 80), (255, 150, 50), (255, 255, 80), (255, 80, 255), (80, 255, 255)]
            be = tint(be, colors[i], 0.2)
            save(be, f'bullet_enemy_{i}')

    # missile
    if missile:
        save(resize(missile, (16, 28)), 'missile')

    # laser - 用 laserRed16 拉伸
    if lr16:
        laser = lr16.resize((14, 40), Image.LANCZOS)
        laser = tint(laser, (100, 255, 255), 0.2)
        save(laser, 'laser')

    # plasma - 程序生成一个发光绿球
    size = 24
    plasma = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(plasma)
    cx, cy = size // 2, size // 2
    for r in range(size // 2, 0, -2):
        ratio = r / (size // 2)
        a = int(200 * (1 - ratio))
        color = (int(80 + 175 * ratio), 255, int(80 + 175 * ratio), a)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)
    plasma = plasma.filter(ImageFilter.GaussianBlur(1))
    save(plasma, 'plasma')


def process_explosions():
    print('\n=== 处理爆炸动画 ===')
    # 使用 regularExplosion 系列
    for i in range(8):
        img = load(f'regularExplosion0{i}.png', 'tasdik')
        if img:
            size = 24 + i * 10
            save(resize(img, size), f'explosion_{i}')


def process_effects():
    print('\n=== 处理特效 ===')
    # shield
    sh = load('shield.png', 'ssg')
    if sh:
        save(resize(sh, 80), 'shield')
    else:
        sh = load('shield_gold.png', 'tasdik')
        if sh:
            save(resize(sh, 80), 'shield')

    # nuke_flash - 程序生成
    from config import SCREEN_WIDTH, SCREEN_HEIGHT
    flash = Image.new('RGBA', (SCREEN_WIDTH, SCREEN_HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(flash)
    draw.ellipse([
        SCREEN_WIDTH//2 - SCREEN_HEIGHT,
        SCREEN_HEIGHT//2 - SCREEN_HEIGHT,
        SCREEN_WIDTH//2 + SCREEN_HEIGHT,
        SCREEN_HEIGHT//2 + SCREEN_HEIGHT
    ], fill=(255, 255, 200, 40))
    flash = flash.filter(ImageFilter.GaussianBlur(30))
    save(flash, 'nuke_flash')

    # stars
    for i, color in enumerate([(255, 255, 255), (100, 255, 255), (255, 255, 100)]):
        star = Image.new('RGBA', (4, 4), (0, 0, 0, 0))
        draw = ImageDraw.Draw(star)
        draw.ellipse([0, 0, 4, 4], fill=(*color, 255))
        save(star, f'star_{i}')


def process_drops():
    print('\n=== 处理掉落物 ===')
    # drop_coin: bolt_gold
    bolt = load('bolt_gold.png', 'tasdik')
    if bolt:
        save(resize(bolt, 22), 'drop_coin')

    # drop_hp: life.png
    life = load('life.png', 'ssg')
    if life:
        hp = resize(life, 22)
        hp = tint(hp, (255, 80, 80), 0.1)
        save(hp, 'drop_hp')

    # drop_nuke: 程序生成
    size = 24
    nuke = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(nuke)
    cx, cy = size // 2, size // 2
    # 外圈
    draw.ellipse([2, 2, size-2, size-2], fill=(255, 150, 50, 200), outline=(255, 80, 0, 255), width=2)
    # 十字
    draw.line([(cx, 4), (cx, size-4)], fill=(255, 0, 0, 255), width=3)
    draw.line([(4, cy), (size-4, cy)], fill=(255, 0, 0, 255), width=3)
    save(nuke, 'drop_nuke')

    # drop_power: 程序生成
    size = 22
    power = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(power)
    pts = [(size//2, 0), (size, size//2), (size//2, size), (0, size//2)]
    draw.polygon(pts, fill=(0, 200, 255, 200), outline=(255, 255, 255, 255))
    save(power, 'drop_power')


def process_ui():
    print('\n=== 处理UI ===')
    # logo
    logo = load('gamelogo.png', 'pygalaxian')
    if logo:
        save(resize(logo, 400), 'logo')
    else:
        # 程序生成简单logo
        logo = Image.new('RGBA', (400, 80), (0, 0, 0, 0))
        save(logo, 'logo')

    # buttons
    for name, bg_color, border_color in [
        ('btn_normal', (0, 100, 200, 180), (100, 200, 255, 200)),
        ('btn_hover', (0, 150, 255, 220), (200, 240, 255, 255)),
    ]:
        btn = Image.new('RGBA', (200, 50), (0, 0, 0, 0))
        draw = ImageDraw.Draw(btn)
        draw.rounded_rectangle([0, 0, 200, 50], radius=8, fill=bg_color, outline=border_color, width=2)
        # 添加微妙渐变效果
        for y in range(50):
            alpha = int(bg_color[3] * (1 - y / 50) * 0.3)
            draw.line([(0, y), (200, y)], fill=(*bg_color[:3], alpha))
        save(btn, name)


def process_backgrounds():
    print('\n=== 处理背景 ===')
    from config import SCREEN_WIDTH, SCREEN_HEIGHT

    # bg_space: 用 Starscape 或 starfield
    bg = load('Starscape.png', 'ssg')
    if bg:
        bg = bg.resize((SCREEN_WIDTH, SCREEN_HEIGHT), Image.LANCZOS)
        save(bg, 'bg_space')
    else:
        bg = load('starfield.png', 'tasdik')
        if bg:
            bg = bg.resize((SCREEN_WIDTH, SCREEN_HEIGHT), Image.LANCZOS)
            save(bg, 'bg_space')

    # bg_nebula: 用 bg1 加上模糊处理
    neb = load('bg1.png', 'pygalaxian')
    if neb:
        neb = neb.resize((SCREEN_WIDTH, SCREEN_HEIGHT), Image.LANCZOS)
        neb = neb.filter(ImageFilter.GaussianBlur(2))
        # 增强对比度
        enhancer = ImageEnhance.Contrast(neb)
        neb = enhancer.enhance(1.2)
        save(neb, 'bg_nebula')
    else:
        # 程序生成星云
        neb = Image.new('RGBA', (SCREEN_WIDTH, SCREEN_HEIGHT), (0, 0, 0, 0))
        import random
        rng = random.Random(42)
        draw = ImageDraw.Draw(neb)
        for _ in range(8):
            x = rng.randint(0, SCREEN_WIDTH)
            y = rng.randint(0, SCREEN_HEIGHT)
            r = rng.randint(80, 250)
            color = rng.choice([
                (20, 20, 60, 40),
                (40, 10, 50, 40),
                (10, 30, 60, 40),
                (60, 20, 40, 30),
            ])
            draw.ellipse([x-r, y-r, x+r, y+r], fill=color)
        neb = neb.filter(ImageFilter.GaussianBlur(20))
        save(neb, 'bg_nebula')


def main():
    print('开始处理素材...')
    process_player_ships()
    process_enemies()
    process_bosses()
    process_bullets()
    process_explosions()
    process_effects()
    process_drops()
    process_ui()
    process_backgrounds()
    print('\n素材处理完成！')


if __name__ == '__main__':
    main()
