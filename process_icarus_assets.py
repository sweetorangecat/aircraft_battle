"""
ICARUS 素材处理脚本
从 ICARUS 游戏素材提取并处理为游戏可用格式
"""
import os
import math
from PIL import Image, ImageFilter, ImageEnhance, ImageDraw

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ICARUS_DIR = "/Users/daweibamao/AI-Project/竖版飞机科幻科技未来射击飞行战争背景场景/ICARUS"
OUT_DIR = os.path.join(BASE_DIR, 'images', 'processed')
os.makedirs(OUT_DIR, exist_ok=True)


def load_icarus(subdir, filename):
    """加载ICARUS素材"""
    path = os.path.join(ICARUS_DIR, subdir, filename)
    if os.path.exists(path):
        return Image.open(path).convert('RGBA')
    return None


def save(img, name):
    """保存处理后的图片"""
    img.save(os.path.join(OUT_DIR, f'{name}.png'))
    print(f'Saved: {name}.png ({img.size})')


def resize(img, target_size, method=Image.LANCZOS):
    """缩放到目标尺寸"""
    if isinstance(target_size, int):
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


def extract_sprite(img, frame_size, frame_index):
    """从精灵表中提取单个帧"""
    fw, fh = frame_size
    cols = img.width // fw
    row = frame_index // cols
    col = frame_index % cols
    x = col * fw
    y = row * fh
    return img.crop((x, y, x + fw, y + fh))


def tint(img, color, intensity=0.5):
    """给图片着色"""
    r, g, b = color
    tint_layer = Image.new('RGBA', img.size, (r, g, b, int(255 * intensity)))
    return Image.alpha_composite(img.copy(), tint_layer)


def glow(img, color, radius=6):
    """添加外发光效果"""
    r, g, b = color
    alpha = img.split()[3]
    glow_layer = Image.new('RGBA', img.size, (r, g, b, 0))
    glow_layer.putalpha(alpha)
    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(radius))
    result = Image.new('RGBA', img.size, (0, 0, 0, 0))
    result = Image.alpha_composite(result, glow_layer)
    result = Image.alpha_composite(result, img)
    return result


def process_player_ships():
    """处理玩家飞船"""
    print('\n=== 处理玩家飞船 ===')

    # 从 plane_01_img.png 提取玩家飞机 (194x194, 2x2布局)
    plane1 = load_icarus('Plane', 'plane_01_img.png')
    if plane1:
        # 2x2布局，每帧97x97
        frame_size = 97
        # 提取4个不同姿态/火力等级的飞机
        for i, name in enumerate(['player_1', 'player_2', 'player_3', 'wingman']):
            frame = extract_sprite(plane1, (frame_size, frame_size), i)
            if name == 'wingman':
                frame = resize(frame, 40)
            else:
                frame = resize(frame, 56)
            save(frame, name)

    # 从 plane_02_img.png 提取 (194x194)
    plane2 = load_icarus('Plane', 'plane_02_img.png')
    if plane2:
        frame_size = 97
        for i, name in enumerate(['player_4', 'player_5']):
            if i < 2:
                frame = extract_sprite(plane2, (frame_size, frame_size), i)
                frame = resize(frame, 60)
                # 添加发光效果
                if i == 0:
                    frame = glow(frame, (255, 200, 50), 4)
                else:
                    frame = glow(frame, (180, 100, 255), 5)
                save(frame, name)


def process_enemies():
    """处理敌人"""
    print('\n=== 处理敌人 ===')

    # 使用 ic_enemy01.png 到 ic_enemy09.png
    enemy_configs = [
        ('ic_enemy01.png', 'enemy_small', 32),
        ('ic_enemy02.png', 'enemy_medium', 40),
        ('ic_enemy03.png', 'enemy_large', 48),
        ('ic_enemy04.png', 'enemy_fast', 36),
        ('ic_enemy05.png', 'enemy_shooter', 44),
        ('ic_enemy06.png', 'enemy_tank', 52),
    ]

    for filename, name, size in enemy_configs:
        img = load_icarus('Enemy', filename)
        if img:
            # 512x1024, 每帧128x128, 共4列8行=32帧
            frame_size = 128
            frame = extract_sprite(img, (frame_size, frame_size), 0)
            frame = resize(frame, size)
            save(frame, name)


def process_bosses():
    """处理BOSS"""
    print('\n=== 处理BOSS ===')

    boss_files = [
        ('ic_enemy07.png', 'boss_0', 100, (255, 80, 80)),
        ('ic_enemy08.png', 'boss_1', 120, (180, 80, 255)),
        ('ic_enemy09.png', 'boss_2', 110, (80, 255, 120)),
    ]

    for filename, name, size, glow_color in boss_files:
        img = load_icarus('Enemy', filename)
        if img:
            frame_size = 128
            frame = extract_sprite(img, (frame_size, frame_size), 0)
            frame = resize(frame, size)
            frame = glow(frame, glow_color, 8)
            save(frame, name)

    # 使用敌人精灵做另外两个BOSS
    for i, (filename, name, size, glow_color) in enumerate([
        ('ic_enemy04.png', 'boss_3', 100, (255, 220, 60)),
        ('ic_enemy05.png', 'boss_4', 105, (80, 180, 255)),
    ]):
        img = load_icarus('Enemy', filename)
        if img:
            frame_size = 128
            frame = extract_sprite(img, (frame_size, frame_size), 0)
            frame = resize(frame, size)
            frame = glow(frame, glow_color, 8)
            save(frame, name)


def process_bullets():
    """处理子弹"""
    print('\n=== 处理子弹 ===')

    img = load_icarus('Bullet', 'ic_bullet.png')
    if img:
        # 512x1024, 每帧约64x64, 共8列16行=128帧
        frame_size = 64

        # 提取玩家子弹
        bullet_indices = [0, 8, 16, 24, 32]  # 不同的子弹样式
        for i, idx in enumerate(bullet_indices):
            if i < 5:
                frame = extract_sprite(img, (frame_size, frame_size), idx)
                frame = resize(frame, (12, 24))
                save(frame, f'bullet_player_{i}')

        # 提取敌人子弹
        enemy_bullet_indices = [4, 12, 20, 28, 36]
        colors = [(255, 80, 80), (255, 150, 50), (255, 255, 80), (255, 80, 255), (80, 255, 255)]
        for i, idx in enumerate(enemy_bullet_indices):
            if i < 5:
                frame = extract_sprite(img, (frame_size, frame_size), idx)
                frame = resize(frame, (10, 10))
                frame = tint(frame, colors[i], 0.2)
                save(frame, f'bullet_enemy_{i}')

        # 导弹
        missile = extract_sprite(img, (frame_size, frame_size), 40)
        missile = resize(missile, (16, 28))
        save(missile, 'missile')

        # 激光
        laser = extract_sprite(img, (frame_size, frame_size), 48)
        laser = laser.resize((14, 40), Image.LANCZOS)
        laser = tint(laser, (100, 255, 255), 0.2)
        save(laser, 'laser')

        # 等离子球
        plasma = extract_sprite(img, (frame_size, frame_size), 56)
        plasma = resize(plasma, 24)
        plasma = glow(plasma, (50, 255, 50), 4)
        save(plasma, 'plasma')


def process_explosions():
    """处理爆炸动画"""
    print('\n=== 处理爆炸动画 ===')

    # 从 ic_spfx.png 提取爆炸帧
    img = load_icarus('Effect', 'ic_spfx.png')
    if img:
        # 1024x1024，每帧128x128，共8x8=64帧
        frame_size = 128
        # 提取8个爆炸帧，间隔分布
        indices = [0, 8, 16, 24, 32, 40, 48, 56]
        for i, idx in enumerate(indices):
            frame = extract_sprite(img, (frame_size, frame_size), idx)
            frame = resize(frame, 32 + i * 8)
            save(frame, f'explosion_{i}')

    # 从 ic_fx.png 提取更多爆炸效果
    img = load_icarus('Effect', 'ic_fx.png')
    if img:
        # 1024x1024，每帧64x64，共16x16=256帧
        # 已经有8个爆炸了，可以生成一些特效
        pass


def process_effects():
    """处理特效"""
    print('\n=== 处理特效 ===')

    # 护盾效果
    img = load_icarus('Effect', 'ic_effect.png')
    if img:
        # 256x256，可能是单张或2x2布局
        frame_size = 128
        frame = extract_sprite(img, (frame_size, frame_size), 0)
        frame = resize(frame, 80)
        save(frame, 'shield')

    # 核弹闪光
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

    # 星星
    for i, color in enumerate([(255, 255, 255), (100, 255, 255), (255, 255, 100)]):
        star = Image.new('RGBA', (4, 4), (0, 0, 0, 0))
        draw = ImageDraw.Draw(star)
        draw.ellipse([0, 0, 4, 4], fill=(*color, 255))
        save(star, f'star_{i}')


def process_drops():
    """处理掉落物"""
    print('\n=== 处理掉落物 ===')

    # 金币
    coin = load_icarus('Fx', 'coin.png')
    if coin:
        coin = resize(coin, 24)
        save(coin, 'drop_coin')

    # 生命/HP
    img = load_icarus('Effect', 'ic_effect.png')
    if img:
        frame = extract_sprite(img, (128, 128), 1)
        frame = resize(frame, 24)
        frame = tint(frame, (255, 80, 80), 0.2)
        save(frame, 'drop_hp')

    # 核弹
    nuke = load_icarus('Object', 'wing_star.png')
    if nuke:
        nuke = resize(nuke, 24)
        nuke = tint(nuke, (255, 150, 50), 0.3)
        save(nuke, 'drop_nuke')

    # 能量/强化
    power = load_icarus('Effect', 'ic_fire_weapon.png')
    if power:
        power = resize(power, 24)
        power = tint(power, (100, 200, 255), 0.3)
        save(power, 'drop_power')


def process_ui():
    """处理UI"""
    print('\n=== 处理UI ===')

    # Logo使用ICARUS的Logo
    logo = Image.new('RGBA', (400, 80), (0, 0, 0, 0))
    save(logo, 'logo')

    # 按钮
    for name, bg_color, border_color in [
        ('btn_normal', (0, 100, 200, 180), (100, 200, 255, 200)),
        ('btn_hover', (0, 150, 255, 220), (200, 240, 255, 255)),
    ]:
        btn = Image.new('RGBA', (200, 50), (0, 0, 0, 0))
        draw = ImageDraw.Draw(btn)
        draw.rounded_rectangle([0, 0, 200, 50], radius=8, fill=bg_color, outline=border_color, width=2)
        for y in range(50):
            alpha = int(bg_color[3] * (1 - y / 50) * 0.3)
            draw.line([(0, y), (200, y)], fill=(*bg_color[:3], alpha))
        save(btn, name)


def create_procedural_background(name):
    """创建程序生成的星空背景"""
    from config import SCREEN_WIDTH, SCREEN_HEIGHT
    import random

    # 深空背景色
    bg = Image.new('RGBA', (SCREEN_WIDTH, SCREEN_HEIGHT), (5, 5, 15, 255))
    draw = ImageDraw.Draw(bg)

    # 随机星星
    random.seed(42)
    for _ in range(200):
        x = random.randint(0, SCREEN_WIDTH)
        y = random.randint(0, SCREEN_HEIGHT)
        size = random.choice([1, 1, 1, 2, 2, 3])
        brightness = random.randint(150, 255)
        color = (brightness, brightness, brightness + random.randint(0, 50))
        draw.ellipse([x, y, x+size, y+size], fill=color)

    # 星云效果（较大的模糊光斑）
    for _ in range(5):
        x = random.randint(0, SCREEN_WIDTH)
        y = random.randint(0, SCREEN_HEIGHT)
        r = random.randint(50, 150)
        # 紫色或蓝色调的星云
        hue = random.choice([
            (30, 20, 60, 60),   # 深紫
            (20, 30, 80, 50),   # 深蓝
            (60, 20, 60, 40),   # 紫红
        ])
        draw.ellipse([x-r, y-r, x+r, y+r], fill=hue)

    # 应用模糊使星云更自然
    bg = bg.filter(ImageFilter.GaussianBlur(2))

    # 再次添加一些清晰的星星在前景
    draw = ImageDraw.Draw(bg)
    for _ in range(50):
        x = random.randint(0, SCREEN_WIDTH)
        y = random.randint(0, SCREEN_HEIGHT)
        size = random.choice([1, 2])
        brightness = random.randint(200, 255)
        draw.ellipse([x, y, x+size, y+size], fill=(brightness, brightness, 255))

    save(bg, name)


def process_backgrounds():
    """处理背景"""
    print('\n=== 处理背景 ===')
    from config import SCREEN_WIDTH, SCREEN_HEIGHT

    # 使用 ICARUS Stage 背景
    bg_files = [
        ('Stage', 'ic_stage01_back_01.png', 'bg_space'),
        ('Stage', 'ic_stage01_back_02.png', 'bg_nebula'),
    ]

    for subdir, filename, outname in bg_files:
        img = load_icarus(subdir, filename)
        if img:
            # 有些背景是512x512或512x1024，需要平铺或拉伸
            if img.size == (512, 512):
                # 创建平铺背景
                bg = Image.new('RGBA', (SCREEN_WIDTH, SCREEN_HEIGHT), (0, 0, 0, 255))
                img_rgba = img.convert('RGBA')
                for y in range(0, SCREEN_HEIGHT, 512):
                    for x in range(0, SCREEN_WIDTH, 512):
                        bg.paste(img_rgba, (x, y))
                save(bg, outname)
            else:
                # 直接拉伸
                img_resized = img.resize((SCREEN_WIDTH, SCREEN_HEIGHT), Image.LANCZOS)
                save(img_resized.convert('RGBA'), outname)
            print(f'  Saved {outname}')
        else:
            # 如果找不到图片，创建程序生成的背景
            print(f'  Creating procedural background for {outname}')
            create_procedural_background(outname)


def main():
    print('开始处理 ICARUS 素材...')
    process_player_ships()
    process_enemies()
    process_bosses()
    process_bullets()
    process_explosions()
    process_effects()
    process_drops()
    process_ui()
    process_backgrounds()
    print('\nICARUS 素材处理完成！')


if __name__ == '__main__':
    main()
