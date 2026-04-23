"""
Sky Defender - 美术资源管理器
加载网络下载并经过 Pillow 处理的精美素材
"""
import os
import pygame

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(BASE_DIR, 'images', 'processed')

pygame.init()
pygame.font.init()


def _has_real_pixels(surface):
    w, h = surface.get_size()
    for y in range(0, h, max(1, h // 4)):
        for x in range(0, w, max(1, w // 8)):
            r, g, b, a = surface.get_at((x, y))
            if a > 50 and (r > 50 or g > 50 or b > 50):
                return True
    return False


def _get_cjk_font(size):
    match_names = [
        'hiraginosansgb', 'stheitimedium', 'stheiti', 'pingfangsc', 'pingfang',
        'microsoftyahei', 'msyh', 'simhei', 'simsun',
        'notosanscjksc', 'notosanscjk', 'wqy-microhei', 'wenquanyimicrohei',
    ]
    for name in match_names:
        path = pygame.font.match_font(name)
        if path:
            try:
                font = pygame.font.Font(path, size)
                test = font.render('中文测试', True, (255, 255, 255))
                if test.get_width() > 40 and _has_real_pixels(test):
                    return font
            except Exception:
                continue

    file_paths = [
        '/System/Library/Fonts/Hiragino Sans GB.ttc',
        '/System/Library/Fonts/STHeiti Medium.ttc',
        '/System/Library/Fonts/STHeiti Light.ttc',
        '/System/Library/Fonts/PingFang.ttc',
        'C:/Windows/Fonts/msyh.ttc',
        'C:/Windows/Fonts/simhei.ttf',
        'C:/Windows/Fonts/simsun.ttc',
        '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',
        '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
        '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc',
    ]
    for path in file_paths:
        try:
            font = pygame.font.Font(path, size)
            test = font.render('中文测试', True, (255, 255, 255))
            if test.get_width() > 40 and _has_real_pixels(test):
                return font
        except Exception:
            continue
    return None


# 所有需要的图片名称列表
_ALL_IMAGE_NAMES = [
    'player_1', 'player_2', 'player_3', 'player_4', 'player_5', 'wingman',
    'enemy_small', 'enemy_medium', 'enemy_large', 'enemy_fast', 'enemy_shooter', 'enemy_tank',
    'boss_0', 'boss_1', 'boss_2', 'boss_3', 'boss_4',
    'bullet_player_0', 'bullet_player_1', 'bullet_player_2', 'bullet_player_3', 'bullet_player_4',
    'bullet_enemy_0', 'bullet_enemy_1', 'bullet_enemy_2', 'bullet_enemy_3', 'bullet_enemy_4',
    'missile', 'laser', 'plasma',
    'explosion_0', 'explosion_1', 'explosion_2', 'explosion_3',
    'explosion_4', 'explosion_5', 'explosion_6', 'explosion_7',
    'shield', 'star_0', 'star_1', 'star_2', 'nuke_flash',
    'drop_coin', 'drop_hp', 'drop_nuke', 'drop_power',
    'logo', 'btn_normal', 'btn_hover',
    'bg_space', 'bg_nebula',
]


class AssetManager:
    def __init__(self):
        self.images = {}
        self.fonts = {}
        self.cjk_available = False
        self._loaded = False
        # 启动时只扫描文件是否存在，缓存路径
        self._paths = {}
        for name in _ALL_IMAGE_NAMES:
            path = os.path.join(IMG_DIR, f'{name}.png')
            if os.path.exists(path):
                self._paths[name] = path
        # 字体不依赖显示模式，可以立即加载
        self._generate_fonts()

    def _ensure_loaded(self):
        """延迟加载：在 display.set_mode 之后的首次 get() 调用时真正加载所有图片"""
        if self._loaded:
            return
        self._loaded = True
        for name, path in self._paths.items():
            try:
                img = pygame.image.load(path).convert_alpha()
                self.images[name] = img
            except Exception as e:
                print(f'[Asset] 加载 {name} 失败: {e}')
        # 未找到文件的图片创建占位
        for name in _ALL_IMAGE_NAMES:
            if name not in self.images:
                self.images[name] = pygame.Surface((1, 1), pygame.SRCALPHA)

    def _generate_fonts(self):
        sizes = [16, 20, 24, 32, 48, 64]
        for size in sizes:
            font = _get_cjk_font(size)
            if font:
                self.fonts[size] = font
                self.cjk_available = True
            else:
                self.fonts[size] = pygame.font.SysFont(None, size)

    def get(self, name):
        self._ensure_loaded()
        return self.images.get(name)

    def font(self, size):
        return self.fonts.get(size, self.fonts[20])

    def draw_text(self, surf, text, size, color, x, y, center=True):
        font = self.font(size)
        img = font.render(text, True, color)
        rect = img.get_rect()
        if center:
            rect.center = (x, y)
        else:
            rect.topleft = (x, y)
        surf.blit(img, rect)
        return rect


# 全局实例 — 不再在导入时加载图片
ASSETS = AssetManager()
