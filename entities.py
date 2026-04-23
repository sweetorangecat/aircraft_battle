"""
Sky Defender - 游戏实体
"""
import pygame
import math
import random
from config import *
from assets import ASSETS
from weapons import WeaponSystem, Bullet
from upgrades import UpgradeSystem
from effects import Particle

class Entity:
    def __init__(self, x, y, hp):
        self.x = x
        self.y = y
        self.hp = hp
        self.max_hp = hp
        self.alive = True
        self.radius = 10
        self.vx = 0
        self.vy = 0

    def take_damage(self, dmg):
        self.hp -= dmg
        if self.hp <= 0:
            self.hp = 0
            self.alive = False

    def update(self):
        self.x += self.vx
        self.y += self.vy

    def draw(self, surf):
        pass

class Player(Entity):
    def __init__(self):
        super().__init__(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100, PLAYER_BASE_HP)
        self.speed = PLAYER_BASE_SPEED
        self.radius = 20
        self.invincible = 0
        self.shield = 0
        self.max_shield = 0
        self.upgrades = UpgradeSystem(self)
        self.weapon = WeaponSystem(self)
        self.level = 1
        self.nukes = 0
        self.regen_timer = 0
        self.img = ASSETS.get('player_1')

        # 技能系统
        self.skill_energy = 0  # 当前能量值
        self.max_skill_energy = 100
        self.skill_cooldown = {SKILL_ENERGY_CANNON: 0, SKILL_SCREEN_CLEAR: 0}
        self.active_skills = []  # 当前激活的技能效果

    def update(self, keys, bullets):
        super().update()
        dx, dy = 0, 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx = -1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx = 1
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy = -1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy = 1

        if dx != 0 and dy != 0:
            dx *= 0.707
            dy *= 0.707

        self.vx = dx * self.speed
        self.vy = dy * self.speed

        # 边界
        self.x = max(self.radius, min(SCREEN_WIDTH - self.radius, self.x))
        self.y = max(self.radius, min(SCREEN_HEIGHT - self.radius, self.y))

        if self.invincible > 0:
            self.invincible -= 1

        # 自动回血
        regen_lv = self.upgrades.get_level(UPGRADE_REGEN)
        if regen_lv > 0 and self.hp < self.max_hp:
            self.regen_timer += 1
            if self.regen_timer >= 120:
                self.regen_timer = 0
                self.hp = min(self.max_hp, self.hp + regen_lv * 2)

        # 升级飞机外观
        new_level = min(5, 1 + (self.upgrades.get_level(UPGRADE_MAX_HP) + self.upgrades.get_level(UPGRADE_DAMAGE)) // 4)
        if new_level != self.level:
            self.level = new_level
            self.img = ASSETS.get(f'player_{self.level}')

        # 最大护盾
        shield_lv = self.upgrades.get_level(UPGRADE_SHIELD)
        self.max_shield = shield_lv * 25
        if self.shield > self.max_shield:
            self.shield = self.max_shield

    def draw(self, surf):
        # 绘制技能效果（在飞机下方）
        self._draw_skills(surf)

        if self.img:
            rect = self.img.get_rect(center=(self.x, self.y))
            if self.invincible > 0 and self.invincible % 6 < 3:
                return
            surf.blit(self.img, rect)
        else:
            pygame.draw.circle(surf, COLOR_CYAN, (int(self.x), int(self.y)), self.radius)

        # 护盾
        if self.shield > 0:
            shield_img = ASSETS.get('shield')
            if shield_img:
                r = shield_img.get_rect(center=(self.x, self.y))
                surf.blit(shield_img, r)

        # 血条
        bar_w = 40
        bar_h = 4
        bx = self.x - bar_w // 2
        by = self.y - self.radius - 10
        pygame.draw.rect(surf, COLOR_DARK_GRAY, (bx, by, bar_w, bar_h))
        hp_ratio = self.hp / self.max_hp
        pygame.draw.rect(surf, COLOR_GREEN, (bx, by, int(bar_w * hp_ratio), bar_h))

        # 绘制技能能量条
        self._draw_skill_bars(surf)

    def _draw_skills(self, surf):
        """绘制激活的技能效果"""
        for skill in self.active_skills:
            if skill['type'] == 'energy_cannon':
                # 绘制能量炮光束
                width = skill['width']
                intensity = skill['timer'] / 30  # 随时间减弱

                # 外层光晕
                for i in range(5, 0, -1):
                    alpha = int(100 * intensity * (6 - i) / 5)
                    w = width + i * 15
                    s = pygame.Surface((w, 600), pygame.SRCALPHA)
                    pygame.draw.ellipse(s, (50, 150, 255, alpha), (0, 0, w, 600))
                    surf.blit(s, (self.x - w // 2, self.y - 600))

                # 核心光束
                core_surf = pygame.Surface((width, 600), pygame.SRCALPHA)
                pygame.draw.ellipse(core_surf, (150, 220, 255, int(200 * intensity)), (0, 0, width, 600))
                pygame.draw.ellipse(core_surf, (255, 255, 255, int(255 * intensity)), (width * 0.2, 0, width * 0.6, 600))
                surf.blit(core_surf, (self.x - width // 2, self.y - 600))

                # 能量粒子
                for i in range(10):
                    px = self.x + random.uniform(-width/2, width/2)
                    py = self.y - random.uniform(0, 600)
                    pygame.draw.circle(surf, (200, 255, 255), (int(px), int(py)), random.randint(1, 3))

            elif skill['type'] == 'screen_flash':
                # 全屏闪光效果
                intensity = skill['timer'] / 10
                flash_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                flash_surf.fill((255, 255, 255, int(200 * intensity)))
                surf.blit(flash_surf, (0, 0))

    def _draw_skill_bars(self, surf):
        """绘制技能能量条和冷却 - 修复布局问题"""
        # 调整位置到左下角，避免与其他UI重叠
        bar_x = 20
        bar_y = SCREEN_HEIGHT - 60
        bar_width = 200
        bar_height = 25

        # 绘制背景面板
        panel = pygame.Surface((bar_width + 200, 70), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 100))
        surf.blit(panel, (bar_x - 10, bar_y - 10))

        # 能量条背景
        pygame.draw.rect(surf, COLOR_DARK_GRAY, (bar_x, bar_y, bar_width, bar_height))

        # 能量条填充
        energy_ratio = self.skill_energy / self.max_skill_energy
        energy_width = int(bar_width * energy_ratio)
        if energy_width > 0:
            # 渐变色 - 蓝到紫
            for i in range(energy_width):
                progress = i / bar_width
                r = int(100 + 155 * progress)
                g = int(200 + 55 * (1 - progress))
                b = 255
                pygame.draw.line(surf, (r, g, b), (bar_x + i, bar_y), (bar_x + i, bar_y + bar_height))

        # 能量条边框
        pygame.draw.rect(surf, COLOR_WHITE, (bar_x, bar_y, bar_width, bar_height), 2)

        # 能量文字
        energy_text = f"能量: {int(self.skill_energy)}/{self.max_skill_energy}"
        ASSETS.draw_text(surf, energy_text, 18, COLOR_WHITE, bar_x + bar_width // 2, bar_y + bar_height // 2)

        # 技能显示 - 放在能量条右侧
        skill_x = bar_x + bar_width + 20
        skill_y = bar_y + 5
        skill_spacing = 85

        for i, (skill_id, name) in enumerate(SKILL_NAMES.items()):
            icon_x = skill_x + i * skill_spacing
            icon_y = skill_y
            icon_w = 75
            icon_h = 40

            # 获取状态
            cooldown = self.skill_cooldown[skill_id]
            can_use = self.can_use_skill(skill_id)
            enough_energy = self.skill_energy >= (30 if skill_id == SKILL_ENERGY_CANNON else 60)

            # 确定背景色
            if can_use:
                icon_color = (50, 150, 50)  # 绿色 - 可用
            elif cooldown > 0:
                icon_color = (150, 50, 50)  # 红色 - 冷却中
            elif not enough_energy:
                icon_color = (100, 100, 100)  # 灰色 - 能量不足
            else:
                icon_color = COLOR_GRAY

            # 绘制背景
            pygame.draw.rect(surf, icon_color, (icon_x, icon_y, icon_w, icon_h), border_radius=5)
            pygame.draw.rect(surf, COLOR_WHITE, (icon_x, icon_y, icon_w, icon_h), 2, border_radius=5)

            # 技能名称
            name_color = COLOR_WHITE if can_use else (200, 200, 200)
            ASSETS.draw_text(surf, name, 16, name_color, icon_x + icon_w // 2, icon_y + 12)

            # 按键提示
            key_hint = "[E]" if skill_id == SKILL_ENERGY_CANNON else "[R]"
            hint_color = COLOR_YELLOW if can_use else COLOR_GRAY
            ASSETS.draw_text(surf, key_hint, 14, hint_color, icon_x + icon_w // 2, icon_y + 28)

            # 冷却遮罩（从下到上）
            if cooldown > 0:
                max_cd = SKILL_COOLDOWN[skill_id]
                cd_ratio = cooldown / max_cd
                overlay_height = int(icon_h * cd_ratio)
                if overlay_height > 0:
                    overlay = pygame.Surface((icon_w, overlay_height), pygame.SRCALPHA)
                    overlay.fill((0, 0, 0, 200))
                    surf.blit(overlay, (icon_x, icon_y + icon_h - overlay_height))

                # 冷却时间数字
                cd_seconds = cooldown // 60 + 1
                ASSETS.draw_text(surf, str(cd_seconds), 18, COLOR_YELLOW, icon_x + icon_w // 2, icon_y + icon_h // 2 + 2)

            # 能量不足提示（只显示文字，不显示方块）
            elif not enough_energy:
                energy_need = 30 if skill_id == SKILL_ENERGY_CANNON else 60
                # 只在技能图标内部显示小字
                small_font = pygame.font.SysFont(None, 12)
                need_text = f"需{energy_need}"
                text_surf = small_font.render(need_text, True, (255, 150, 150))
                text_rect = text_surf.get_rect(center=(icon_x + icon_w - 15, icon_y + 32))
                surf.blit(text_surf, text_rect)

    def take_damage(self, dmg):
        if self.invincible > 0:
            return
        if self.shield > 0:
            self.shield -= dmg
            if self.shield < 0:
                dmg = -self.shield
                self.shield = 0
            else:
                return
        super().take_damage(dmg)
        self.invincible = PLAYER_INVINCIBLE_TIME

    def heal(self, amount):
        self.hp = min(self.max_hp, self.hp + amount)

    def use_nuke(self, enemies, particles, anims):
        if self.nukes <= 0:
            return False
        self.nukes -= 1
        for e in enemies:
            if hasattr(e, 'is_boss') and e.is_boss:
                e.take_damage(e.max_hp * 0.3)
            else:
                e.take_damage(e.max_hp * 2)
        for _ in range(50):
            particles.spawn(random.randint(0, SCREEN_WIDTH), random.randint(0, SCREEN_HEIGHT),
                            5, 8, 40, COLOR_ORANGE, 4)
        return True

    def add_skill_energy(self, amount):
        """增加技能能量"""
        self.skill_energy = min(self.max_skill_energy, self.skill_energy + amount)

    def can_use_skill(self, skill_id):
        """检查是否可以使用技能"""
        if skill_id == SKILL_ENERGY_CANNON:
            return self.skill_energy >= 30 and self.skill_cooldown[skill_id] <= 0
        elif skill_id == SKILL_SCREEN_CLEAR:
            return self.skill_energy >= 60 and self.skill_cooldown[skill_id] <= 0
        return False

    def use_skill(self, skill_id, enemies, particles, anims):
        """使用技能"""
        if not self.can_use_skill(skill_id):
            return False

        if skill_id == SKILL_ENERGY_CANNON:
            # 能量炮 - 高伤害直线穿透
            self.skill_energy -= 30
            self.skill_cooldown[skill_id] = SKILL_COOLDOWN[SKILL_ENERGY_CANNON]

            # 创建能量炮效果
            damage = 200 + self.weapon.get_stats()['damage'] * 5
            self.active_skills.append({
                'type': 'energy_cannon',
                'timer': 30,  # 持续0.5秒
                'damage': damage,
                'width': 60,
            })

            # 视觉特效
            for i in range(20):
                particles.spawn(self.x, self.y - i * 20, 3, 5, 20, COLOR_CYAN, 4, glow=True)

            return True

        elif skill_id == SKILL_SCREEN_CLEAR:
            # 全屏清怪
            self.skill_energy -= 60
            self.skill_cooldown[skill_id] = SKILL_COOLDOWN[SKILL_SCREEN_CLEAR]

            # 对所有敌人造成伤害
            for e in enemies:
                if hasattr(e, 'is_boss') and e.is_boss:
                    e.take_damage(e.max_hp * 0.15)  # BOSS掉15%血
                else:
                    e.take_damage(e.max_hp * 2)  # 普通敌人直接秒杀

            # 全屏闪光特效
            self.active_skills.append({
                'type': 'screen_flash',
                'timer': 10,
                'color': COLOR_WHITE,
            })

            # 粒子特效
            for _ in range(100):
                x = random.randint(0, SCREEN_WIDTH)
                y = random.randint(0, SCREEN_HEIGHT)
                particles.spawn(x, y, 5, 8, 40, COLOR_YELLOW, 4, glow=True)

            return True

        return False

    def update_skills(self, enemies, particles, anims):
        """更新技能状态和效果"""
        # 更新冷却
        for skill_id in self.skill_cooldown:
            if self.skill_cooldown[skill_id] > 0:
                self.skill_cooldown[skill_id] -= 1

        # 更新激活的技能效果
        for skill in self.active_skills[:]:
            skill['timer'] -= 1

            if skill['type'] == 'energy_cannon':
                # 能量炮持续伤害
                # 获取玩家正前方的敌人
                for e in enemies:
                    if not e.alive:
                        continue
                    # 检查敌人是否在能量炮范围内（玩家前方扇形区域）
                    dy = e.y - (self.y - 100)  # 从玩家前方一点开始
                    dx = e.x - self.x
                    if dy < 0 and dy > -600:  # 前方600像素
                        if abs(dx) < skill['width'] / 2 + e.radius:
                            # 在范围内，造成伤害
                            e.take_damage(skill['damage'] / 30)  # 分摊到30帧
                            # 粒子效果
                            if random.random() < 0.3:
                                particles.spawn(e.x, e.y, 2, 3, 10, COLOR_CYAN, 3, glow=True)

            if skill['timer'] <= 0:
                self.active_skills.remove(skill)

class Enemy(Entity):
    def __init__(self, x, y, enemy_type, level=1):
        super().__init__(x, y, 10)
        self.enemy_type = enemy_type
        self.level = level
        self.score = 10
        self.coin_drop = 1
        self.shoot_timer = 0
        self.move_timer = 0
        self.pattern_phase = 0
        self.setup_type()
        self.img = ASSETS.get(f'enemy_{self.get_type_name()}')
        self.alive = True
        self._gave_energy = False  # 标记是否已经给予过能量

    def get_type_name(self):
        names = {ENEMY_SMALL: 'small', ENEMY_MEDIUM: 'medium', ENEMY_LARGE: 'large',
                 ENEMY_FAST: 'fast', ENEMY_SHOOTER: 'shooter', ENEMY_TANK: 'tank'}
        return names.get(self.enemy_type, 'small')

    def setup_type(self):
        mult = 1 + self.level * 0.1
        configs = {
            ENEMY_SMALL: {'hp': 15, 'speed': 2, 'score': 10, 'coin': 1},
            ENEMY_MEDIUM: {'hp': 40, 'speed': 1.5, 'score': 25, 'coin': 2},
            ENEMY_LARGE: {'hp': 80, 'speed': 1, 'score': 50, 'coin': 3},
            ENEMY_FAST: {'hp': 20, 'speed': 4.5, 'score': 30, 'coin': 2},
            ENEMY_SHOOTER: {'hp': 35, 'speed': 1.2, 'score': 35, 'coin': 3},
            ENEMY_TANK: {'hp': 150, 'speed': 0.8, 'score': 60, 'coin': 5},
        }
        cfg = configs.get(self.enemy_type, configs[ENEMY_SMALL])
        self.max_hp = int(cfg['hp'] * mult)
        self.hp = self.max_hp
        self.base_speed = cfg['speed'] * (1 + self.level * 0.05)
        self.score = cfg['score']
        self.coin_drop = cfg['coin']
        # 设置碰撞半径
        radius_map = {
            ENEMY_SMALL: 12, ENEMY_MEDIUM: 18, ENEMY_LARGE: 24,
            ENEMY_FAST: 14, ENEMY_SHOOTER: 16, ENEMY_TANK: 20,
        }
        self.radius = radius_map.get(self.enemy_type, 12)

    def update(self, player=None, enemy_bullets=None):
        super().update()
        self.move_timer += 1

        if self.enemy_type == ENEMY_SMALL:
            self.vx = math.sin(self.move_timer * 0.02) * 1
            self.vy = self.base_speed
        elif self.enemy_type == ENEMY_MEDIUM:
            self.vx = math.sin(self.move_timer * 0.03) * 1.5
            self.vy = self.base_speed * 0.8
        elif self.enemy_type == ENEMY_LARGE:
            self.vx = math.sin(self.move_timer * 0.015) * 0.8
            self.vy = self.base_speed * 0.6
        elif self.enemy_type == ENEMY_FAST:
            self.vy = self.base_speed
            if player:
                dx = player.x - self.x
                self.vx = max(-3, min(3, dx * 0.02))
        elif self.enemy_type == ENEMY_SHOOTER:
            self.vy = self.base_speed * 0.5
            self.shoot_timer += 1
            if self.shoot_timer > 90:
                self.shoot_timer = 0
                if enemy_bullets and player:
                    dx = player.x - self.x
                    dy = player.y - self.y
                    dist = math.hypot(dx, dy)
                    if dist > 0:
                        spd = 4
                        enemy_bullets.append(Bullet(self.x, self.y, dx/dist*spd, dy/dist*spd,
                                                    8 + self.level, is_player=False))
        elif self.enemy_type == ENEMY_TANK:
            self.vy = self.base_speed * 0.4
            self.vx = math.sin(self.move_timer * 0.01) * 0.5

        if self.y > SCREEN_HEIGHT + 50:
            self.alive = False

    def draw(self, surf):
        # 绘制发光轮廓使敌人更容易看见
        glow_colors = {
            ENEMY_SMALL: (255, 100, 100, 120),
            ENEMY_MEDIUM: (255, 150, 100, 120),
            ENEMY_LARGE: (255, 100, 150, 120),
            ENEMY_FAST: (100, 255, 255, 120),
            ENEMY_SHOOTER: (255, 200, 100, 120),
            ENEMY_TANK: (150, 255, 100, 120),
        }
        glow_color = glow_colors.get(self.enemy_type, (255, 100, 100, 120))

        # 绘制发光效果
        for i in range(3, 0, -1):
            glow_surf = pygame.Surface((self.radius * 2 + i * 6, self.radius * 2 + i * 6), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (*glow_color[:3], glow_color[3] // (4 - i)),
                              (glow_surf.get_width()//2, glow_surf.get_height()//2), self.radius + i * 3)
            surf.blit(glow_surf, (self.x - glow_surf.get_width()//2, self.y - glow_surf.get_height()//2))

        if self.img:
            rect = self.img.get_rect(center=(int(self.x), int(self.y)))
            surf.blit(self.img, rect)
        else:
            pygame.draw.circle(surf, COLOR_RED, (int(self.x), int(self.y)), self.radius)

        # 血条
        if self.hp < self.max_hp:
            bar_w = self.radius * 2
            bar_h = 3
            bx = self.x - bar_w // 2
            by = self.y - self.radius - 8
            pygame.draw.rect(surf, COLOR_DARK_GRAY, (bx, by, bar_w, bar_h))
            ratio = self.hp / self.max_hp
            pygame.draw.rect(surf, COLOR_RED, (bx, by, int(bar_w * ratio), bar_h))

    def take_damage(self, dmg):
        super().take_damage(dmg)

class Boss(Entity):
    def __init__(self, x, y, boss_type, level=1):
        super().__init__(x, y, 1000)
        self.boss_type = boss_type % 5
        self.is_boss = True
        self.level = level
        self.phase = 0
        self.max_phase = 3
        self.entering = True
        self.target_y = 120
        self.score = 500
        self.coin_drop = 50
        self.setup_boss()
        self.img = ASSETS.get(f'boss_{self.boss_type}')
        self.shoot_timer = 0
        self.move_timer = 0
        self.alive = True
        self._gave_energy = False

    def setup_boss(self):
        mult = 1 + self.level * 0.3
        configs = [
            {'hp': 800, 'speed': 2, 'name': '拦截者'},
            {'hp': 1200, 'speed': 1.5, 'name': '毁灭者'},
            {'hp': 2000, 'speed': 1, 'name': '母舰'},
            {'hp': 1000, 'speed': 2.5, 'name': '碾压者'},
            {'hp': 1500, 'speed': 1.8, 'name': '幻影'},
        ]
        cfg = configs[self.boss_type]
        self.max_hp = int(cfg['hp'] * mult)
        self.hp = self.max_hp
        self.base_speed = cfg['speed']
        self.name = cfg['name']
        self.radius = 40 if self.boss_type != 1 else 50

    def update(self, player, enemy_bullets):
        super().update()
        self.move_timer += 1
        self.shoot_timer += 1

        if self.entering:
            self.vy = 1.5
            if self.y >= self.target_y:
                self.entering = False
                self.y = self.target_y
                self.vy = 0
            return

        # 移动模式
        if self.boss_type == BOSS_INTERCEPTOR:
            self.vx = math.sin(self.move_timer * 0.02) * self.base_speed
            self.vy = math.sin(self.move_timer * 0.03) * 0.5
        elif self.boss_type == BOSS_DESTROYER:
            self.vx = math.sin(self.move_timer * 0.01) * self.base_speed * 0.5
            self.vy = 0
        elif self.boss_type == BOSS_MOTHERSHIP:
            self.vx = math.sin(self.move_timer * 0.008) * self.base_speed * 0.3
            self.vy = math.sin(self.move_timer * 0.015) * 0.3
        elif self.boss_type == BOSS_CRUSHER:
            self.vx = math.sin(self.move_timer * 0.025) * self.base_speed
            if abs(self.x - player.x) < 30:
                self.vy = 3
            else:
                self.vy = 0.2
            if self.y > 200:
                self.vy = -2
        else:
            self.vx = math.sin(self.move_timer * 0.03) * self.base_speed
            self.vy = math.cos(self.move_timer * 0.025) * 0.8

        # 射击模式
        phase_interval = 180
        phase = (self.move_timer // phase_interval) % 4
        self.phase = phase

        if self.shoot_timer > 30:
            self.shoot_timer = 0
            self._fire_pattern(player, enemy_bullets, phase)

        # 边界限制
        self.x = max(self.radius, min(SCREEN_WIDTH - self.radius, self.x))
        self.y = max(40, min(300, self.y))

    def _fire_pattern(self, player, enemy_bullets, phase):
        if self.boss_type == BOSS_INTERCEPTOR:
            if phase == 0:
                for i in range(-2, 3):
                    enemy_bullets.append(Bullet(self.x, self.y, i*1.5, 5, 10, is_player=False))
            elif phase == 1:
                for i in range(8):
                    ang = i * math.pi / 4
                    enemy_bullets.append(Bullet(self.x, self.y, math.cos(ang)*4, math.sin(ang)*4, 8, is_player=False))
            else:
                dx = player.x - self.x
                dy = player.y - self.y
                dist = math.hypot(dx, dy)
                if dist > 0:
                    enemy_bullets.append(Bullet(self.x, self.y, dx/dist*5, dy/dist*5, 12, is_player=False))
        elif self.boss_type == BOSS_DESTROYER:
            for i in range(-3, 4):
                enemy_bullets.append(Bullet(self.x + i*15, self.y, i*0.5, 3, 10, is_player=False))
            if phase == 2:
                for i in range(12):
                    ang = i * math.pi / 6
                    enemy_bullets.append(Bullet(self.x, self.y, math.cos(ang)*3, math.sin(ang)*3, 8, is_player=False))
        elif self.boss_type == BOSS_MOTHERSHIP:
            for i in range(5):
                ang = math.pi / 2 + (i - 2) * 0.3
                enemy_bullets.append(Bullet(self.x, self.y, math.cos(ang)*3, math.sin(ang)*3, 12, is_player=False))
        elif self.boss_type == BOSS_CRUSHER:
            for i in range(-2, 3):
                enemy_bullets.append(Bullet(self.x, self.y, i*2, 4, 10, is_player=False))
            enemy_bullets.append(Bullet(self.x, self.y, 0, 6, 15, is_player=False, bullet_type=1))
        else:
            for i in range(6):
                ang = self.move_timer * 0.1 + i * math.pi / 3
                enemy_bullets.append(Bullet(self.x, self.y, math.cos(ang)*3.5, math.sin(ang)*3.5, 8, is_player=False))

    def draw(self, surf):
        if self.img:
            rect = self.img.get_rect(center=(int(self.x), int(self.y)))
            surf.blit(self.img, rect)
        else:
            pygame.draw.circle(surf, COLOR_RED, (int(self.x), int(self.y)), self.radius)

        # BOSS 血条背景
        bar_w = 300
        bar_h = 12
        bx = SCREEN_WIDTH // 2 - bar_w // 2
        by = 20
        pygame.draw.rect(surf, COLOR_DARK_GRAY, (bx, by, bar_w, bar_h))
        ratio = self.hp / self.max_hp
        col = COLOR_RED if ratio > 0.5 else COLOR_ORANGE if ratio > 0.25 else COLOR_RED
        pygame.draw.rect(surf, col, (bx, by, int(bar_w * ratio), bar_h))
        pygame.draw.rect(surf, COLOR_WHITE, (bx, by, bar_w, bar_h), 2)

        name = f"BOSS - {self.name} (Lv.{self.level})"
        ASSETS.draw_text(surf, name, 20, COLOR_WHITE, SCREEN_WIDTH // 2, 50)

class Drop(Entity):
    def __init__(self, x, y, drop_type):
        super().__init__(x, y, 1)
        self.drop_type = drop_type
        self.vy = 2
        self.vx = random.uniform(-0.5, 0.5)
        self.alive = True
        self.radius = 12
        names = {DROP_COIN: 'drop_coin', DROP_HP: 'drop_hp', DROP_NUKE: 'drop_nuke', DROP_POWER: 'drop_power'}
        self.img = ASSETS.get(names.get(drop_type, 'drop_coin'))

    def update(self, player=None):
        super().update()
        if player:
            magnet = player.upgrades.get_level(UPGRADE_MAGNET)
            magnet_range = 80 + magnet * 40
            dx = player.x - self.x
            dy = player.y - self.y
            dist = math.hypot(dx, dy)
            if dist < magnet_range and dist > 0:
                self.vx += (dx / dist) * 0.8
                self.vy += (dy / dist) * 0.8
                if abs(self.vx) > 6:
                    self.vx *= 0.9
                if abs(self.vy) > 6:
                    self.vy *= 0.9

        if self.y > SCREEN_HEIGHT + 50:
            self.alive = False

    def apply(self, player):
        if self.drop_type == DROP_COIN:
            player.upgrades.add_coins(self.radius)
            player.upgrades.add_exp(5)
        elif self.drop_type == DROP_HP:
            player.heal(20 + player.upgrades.get_level(UPGRADE_MAX_HP) * 5)
        elif self.drop_type == DROP_NUKE:
            player.nukes += 1
        elif self.drop_type == DROP_POWER:
            player.upgrades.add_exp(20)
            player.upgrades.add_coins(5)
        self.alive = False

    def draw(self, surf):
        if self.img:
            rect = self.img.get_rect(center=(int(self.x), int(self.y)))
            surf.blit(self.img, rect)
        else:
            colors = {DROP_COIN: COLOR_YELLOW, DROP_HP: COLOR_RED, DROP_NUKE: COLOR_ORANGE, DROP_POWER: COLOR_CYAN}
            pygame.draw.circle(surf, colors.get(self.drop_type, COLOR_WHITE), (int(self.x), int(self.y)), 8)
