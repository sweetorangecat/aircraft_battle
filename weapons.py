"""
Sky Defender - 武器系统
"""
import pygame
import math
from config import *
from assets import ASSETS

class Bullet:
    def __init__(self, x, y, vx, vy, damage, is_player=True, bullet_type=0, piercing=False, homing=False):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.damage = damage
        self.is_player = is_player
        self.bullet_type = bullet_type
        self.piercing = piercing
        self.homing = homing
        self.alive = True
        self.hit_enemies = set()

        # 设置外观
        if is_player:
            if bullet_type == WEAPON_MISSILE:
                self.image = ASSETS.get('missile')
            elif bullet_type == WEAPON_LASER:
                self.image = ASSETS.get('laser')
            elif bullet_type == WEAPON_PLASMA:
                self.image = ASSETS.get('plasma')
            else:
                self.image = ASSETS.get(f'bullet_player_{bullet_type % 5}')
        else:
            self.image = ASSETS.get(f'bullet_enemy_{bullet_type % 5}')

        if self.image:
            self.rect = self.image.get_rect(center=(x, y))
            self.radius = max(self.rect.width, self.rect.height) // 2
        else:
            self.rect = pygame.Rect(x-4, y-4, 8, 8)
            self.radius = 4

    def update(self, enemies=None):
        if self.homing and enemies:
            target = None
            min_dist = float('inf')
            for e in enemies:
                if e.alive:
                    d = math.hypot(e.x - self.x, e.y - self.y)
                    if d < min_dist and d < 300:
                        min_dist = d
                        target = e
            if target:
                dx = target.x - self.x
                dy = target.y - self.y
                ang = math.atan2(dy, dx)
                speed = math.hypot(self.vx, self.vy)
                self.vx = math.cos(ang) * speed
                self.vy = math.sin(ang) * speed

        self.x += self.vx
        self.y += self.vy
        self.rect.center = (self.x, self.y)

        if (self.x < -50 or self.x > SCREEN_WIDTH + 50 or
            self.y < -50 or self.y > SCREEN_HEIGHT + 50):
            self.alive = False

    def draw(self, surf):
        if self.image:
            # 导弹旋转
            if self.bullet_type == WEAPON_MISSILE and (self.vx != 0 or self.vy != 0):
                angle = -math.degrees(math.atan2(self.vx, self.vy)) + 90
                img = pygame.transform.rotate(self.image, angle)
                rect = img.get_rect(center=(self.x, self.y))
                surf.blit(img, rect)
            else:
                surf.blit(self.image, self.rect)
        else:
            pygame.draw.circle(surf, COLOR_YELLOW, (int(self.x), int(self.y)), 4)

class WeaponSystem:
    def __init__(self, owner):
        self.owner = owner
        self.weapon_type = WEAPON_MACHINE_GUN
        self.level = 1
        self.fire_timer = 0
        self.laser_active = False
        self.laser_timer = 0
        self.wingmen = []  # 僚机角度偏移

    def get_stats(self):
        # 基础属性，会被升级系统覆盖增强
        base = {
            WEAPON_MACHINE_GUN: {'damage': 10, 'speed': 8, 'cooldown': 8, 'spread': 0},
            WEAPON_SHOTGUN: {'damage': 8, 'speed': 7, 'cooldown': 25, 'spread': 0.3},
            WEAPON_LASER: {'damage': 3, 'speed': 0, 'cooldown': 2, 'spread': 0},
            WEAPON_MISSILE: {'damage': 25, 'speed': 4, 'cooldown': 40, 'spread': 0},
            WEAPON_PLASMA: {'damage': 15, 'speed': 5, 'cooldown': 20, 'spread': 0},
        }
        stats = base.get(self.weapon_type, base[WEAPON_MACHINE_GUN]).copy()

        # 应用升级
        fire_rate_bonus = self.owner.upgrades.get_level(UPGRADE_FIRE_RATE) * 0.15
        stats['cooldown'] = max(2, int(stats['cooldown'] * (1 - fire_rate_bonus)))

        damage_bonus = 1 + self.owner.upgrades.get_level(UPGRADE_DAMAGE) * 0.25
        stats['damage'] *= damage_bonus

        bullet_speed_bonus = 1 + self.owner.upgrades.get_level(UPGRADE_BULLET_SPEED) * 0.15
        stats['speed'] *= bullet_speed_bonus

        multishot = self.owner.upgrades.get_level(UPGRADE_MULTISHOT)
        stats['multishot'] = multishot

        bullet_size_bonus = 1 + self.owner.upgrades.get_level(UPGRADE_BULLET_SIZE) * 0.2
        stats['size_bonus'] = bullet_size_bonus

        # 暴击
        crit_chance = min(0.5, self.owner.upgrades.get_level(UPGRADE_CRIT_CHANCE) * 0.08)
        stats['crit_chance'] = crit_chance

        return stats

    def fire(self, bullets_group):
        stats = self.get_stats()
        if self.fire_timer > 0:
            self.fire_timer -= 1
            return

        self.fire_timer = stats['cooldown']
        x, y = self.owner.x, self.owner.y - self.owner.radius
        dmg = stats['damage']

        # 暴击
        import random
        if random.random() < stats.get('crit_chance', 0):
            dmg *= 2

        spd = stats['speed']
        multi = stats.get('multishot', 0)

        if self.weapon_type == WEAPON_MACHINE_GUN:
            self._spawn_bullet(bullets_group, x, y, 0, -spd, dmg)
            for i in range(1, multi + 1):
                spread = 0.15 * i
                self._spawn_bullet(bullets_group, x, y, -spd * math.sin(spread), -spd * math.cos(spread), dmg)
                self._spawn_bullet(bullets_group, x, y, spd * math.sin(spread), -spd * math.cos(spread), dmg)

        elif self.weapon_type == WEAPON_SHOTGUN:
            base_spread = stats['spread']
            count = 3 + multi * 2
            for i in range(count):
                ang = -base_spread + (2 * base_spread * i / max(1, count - 1))
                self._spawn_bullet(bullets_group, x, y, spd * math.sin(ang), -spd * math.cos(ang), dmg)

        elif self.weapon_type == WEAPON_LASER:
            # 激光为持续伤害，在 update 中处理
            if not self.laser_active:
                self.laser_active = True
                self.laser_timer = 10

        elif self.weapon_type == WEAPON_MISSILE:
            self._spawn_bullet(bullets_group, x, y, 0, -spd, dmg, homing=True)
            for i in range(1, multi + 1):
                self._spawn_bullet(bullets_group, x - i*10, y, -0.5, -spd, dmg, homing=True)
                self._spawn_bullet(bullets_group, x + i*10, y, 0.5, -spd, dmg, homing=True)

        elif self.weapon_type == WEAPON_PLASMA:
            self._spawn_bullet(bullets_group, x, y, 0, -spd, dmg, piercing=True)
            for i in range(1, multi + 1):
                self._spawn_bullet(bullets_group, x - i*12, y, 0, -spd, dmg, piercing=True)
                self._spawn_bullet(bullets_group, x + i*12, y, 0, -spd, dmg, piercing=True)

        # 僚机射击
        wingman_count = self.owner.upgrades.get_level(UPGRADE_WINGMAN)
        for i in range(wingman_count):
            offset = 30 + i * 20
            side = -1 if i % 2 == 0 else 1
            wx = x + side * offset
            wy = y + 10
            self._spawn_bullet(bullets_group, wx, wy, 0, -spd * 0.9, dmg * 0.5)

    def _spawn_bullet(self, group, x, y, vx, vy, dmg, piercing=False, homing=False):
        b = Bullet(x, y, vx, vy, dmg, is_player=True, bullet_type=self.weapon_type,
                   piercing=piercing, homing=homing)
        group.append(b)

    def update_laser(self, enemies, particles):
        if self.laser_active:
            self.laser_timer -= 1
            if self.laser_timer <= 0:
                self.laser_active = False
                return
            stats = self.get_stats()
            x = self.owner.x
            y1 = self.owner.y - self.owner.radius
            y2 = 0
            # 持续伤害激光线上的敌人
            for e in enemies:
                if e.alive and abs(e.x - x) < e.radius + 10 and e.y < y1 and e.y > y2:
                    e.take_damage(stats['damage'] * 0.3)
            # 激光粒子
            for yy in range(int(y2), int(y1), 10):
                particles.append(Particle(x + random.uniform(-4, 4), yy,
                                          random.uniform(-0.5, 0.5), random.uniform(-2, 2),
                                          random.randint(5, 12), COLOR_CYAN, 2))

    def draw_laser(self, surf):
        if self.laser_active:
            x = self.owner.x
            y = self.owner.y - self.owner.radius
            pts = [(x-6, y), (x+6, y), (x+3, 0), (x-3, 0)]
            pygame.draw.polygon(surf, (100, 255, 255, 100), pts)
            pygame.draw.polygon(surf, (200, 255, 255, 150), [(x-3, y), (x+3, y), (x+1, 0), (x-1, 0)])

from effects import Particle
