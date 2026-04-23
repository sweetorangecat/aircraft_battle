"""
Sky Defender - 粒子特效系统
"""
import pygame
import random
import math
from config import *
from assets import ASSETS

class Particle:
    def __init__(self, x, y, vx, vy, life, color, size=2, glow=False, fade=True):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.life = life
        self.max_life = life
        self.color = color
        self.size = size
        self.glow = glow
        self.fade = fade
        self.rotation = random.uniform(0, 360)
        self.rot_speed = random.uniform(-5, 5)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.05  # 重力效果
        self.vx *= 0.98  # 空气阻力
        self.rotation += self.rot_speed
        self.life -= 1
        return self.life > 0

    def draw(self, surf):
        if self.fade:
            alpha = max(0, int(255 * self.life / self.max_life))
        else:
            alpha = 255
        col = (self.color[0], self.color[1], self.color[2], alpha)

        if self.glow and alpha > 100:
            # 发光效果
            glow_size = self.size * 3
            glow_surf = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
            for r in range(glow_size, 0, -2):
                glow_alpha = int(alpha * (1 - r / glow_size) * 0.3)
                pygame.draw.circle(glow_surf, (*self.color[:3], glow_alpha),
                                    (glow_size, glow_size), r)
            surf.blit(glow_surf, (int(self.x - glow_size), int(self.y - glow_size)))

        # 主粒子
        s = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, col, (self.size, self.size), self.size)
        surf.blit(s, (int(self.x - self.size), int(self.y - self.size)))

class ParticleManager:
    def __init__(self):
        self.particles = []

    def spawn(self, x, y, count, speed, life, color, size=2, glow=False):
        for _ in range(count):
            ang = random.uniform(0, math.pi * 2)
            spd = random.uniform(0.5, speed)
            vx = math.cos(ang) * spd
            vy = math.sin(ang) * spd
            self.particles.append(Particle(x, y, vx, vy, random.randint(life//2, life), color, size, glow))

    def spawn_explosion(self, x, y, intensity=1):
        """增强的爆炸效果"""
        colors = [COLOR_YELLOW, COLOR_ORANGE, COLOR_RED, COLOR_WHITE]

        # 核心爆炸 - 发光粒子
        self.spawn(x, y, 15 * intensity, 3 * intensity, 40, random.choice(colors), 4, glow=True)

        # 外围火花
        self.spawn(x, y, 20 * intensity, 5 * intensity, 30, COLOR_ORANGE, 2, glow=True)

        # 烟雾效果
        self.spawn(x, y, 10 * intensity, 1.5 * intensity, 60, (100, 100, 100), 3, glow=False)

        # 冲击波粒子（向外扩散）
        for i in range(8 * intensity):
            angle = (i / (8 * intensity)) * 2 * math.pi
            speed = 6 * intensity
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            life = random.randint(20, 35)
            size = random.randint(2, 4)
            self.particles.append(Particle(x, y, vx, vy, life, COLOR_YELLOW, size, glow=True))

    def spawn_hit_spark(self, x, y, color=COLOR_YELLOW):
        """命中火花效果"""
        self.spawn(x, y, 5, 3, 15, color, 2, glow=True)

    def spawn_enemy_death(self, x, y, enemy_type):
        """敌人死亡特效"""
        # 根据敌人类型调整爆炸
        intensity_map = {
            0: 1,  # small
            1: 1.5,  # medium
            2: 2,  # large
            3: 1.2,  # fast
            4: 1.5,  # shooter
            5: 2.5,  # tank
        }
        intensity = intensity_map.get(enemy_type, 1)
        self.spawn_explosion(x, y, intensity)

    def spawn_bullet_trail(self, x, y, color, is_player=True):
        """子弹尾迹"""
        if is_player:
            self.spawn(x, y, 1, 0.5, 8, color, 1)
        else:
            self.spawn(x, y, 1, 0.3, 10, color, 1)

    def spawn_trail(self, x, y, color):
        self.particles.append(Particle(x, y, random.uniform(-0.5, 0.5), random.uniform(1, 3),
                                       random.randint(10, 20), color, 2))

    def spawn_engine(self, x, y):
        self.particles.append(Particle(x, y, random.uniform(-0.3, 0.3), random.uniform(2, 5),
                                       random.randint(5, 15), COLOR_ORANGE, 2))
        self.particles.append(Particle(x, y, random.uniform(-0.2, 0.2), random.uniform(3, 6),
                                       random.randint(3, 10), COLOR_YELLOW, 1))

    def update(self):
        self.particles = [p for p in self.particles if p.update()]

    def draw(self, surf):
        for p in self.particles:
            p.draw(surf)

class Animation:
    def __init__(self, x, y, frames_prefix, frame_count, frame_delay):
        self.x = x
        self.y = y
        self.frames = [ASSETS.get(f"{frames_prefix}_{i}") for i in range(frame_count)]
        self.frame_delay = frame_delay
        self.timer = 0
        self.index = 0
        self.done = False
        self.rect = self.frames[0].get_rect(center=(x, y)) if self.frames else pygame.Rect(0,0,0,0)

    def update(self):
        self.timer += 1
        if self.timer >= self.frame_delay:
            self.timer = 0
            self.index += 1
            if self.index >= len(self.frames):
                self.done = True
            else:
                self.rect = self.frames[self.index].get_rect(center=(self.x, self.y))

    def draw(self, surf):
        if not self.done and self.index < len(self.frames) and self.frames[self.index]:
            surf.blit(self.frames[self.index], self.rect)

class AnimationManager:
    def __init__(self):
        self.anims = []

    def add_explosion(self, x, y):
        self.anims.append(Animation(x, y, "explosion", 8, 4))

    def update(self):
        for a in self.anims:
            a.update()
        self.anims = [a for a in self.anims if not a.done]

    def draw(self, surf):
        for a in self.anims:
            a.draw(surf)
