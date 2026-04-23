"""
Sky Defender - 关卡系统（100关）
"""
import random
import math
from config import *
from entities import Enemy, Boss

class LevelManager:
    def __init__(self):
        self.level = 1
        self.wave = 0
        self.max_waves = 5
        self.wave_timer = 0
        self.spawn_timer = 0
        self.enemies_to_spawn = []
        self.boss_spawned = False
        self.level_clear = False
        self.level_start_timer = 120
        self.total_enemies_killed = 0

    def is_boss_level(self):
        return self.level % BOSS_LEVEL_INTERVAL == 0

    def start_level(self, level):
        self.level = level
        self.wave = 0
        self.wave_timer = 0
        self.spawn_timer = 0
        self.enemies_to_spawn = []
        self.boss_spawned = False
        self.level_clear = False
        self.level_start_timer = 120
        self.max_waves = min(10, 3 + level // 10)

    def update(self, enemies, player_y):
        if self.level_start_timer > 0:
            self.level_start_timer -= 1
            return

        if self.is_boss_level():
            if not self.boss_spawned and not any(hasattr(e, 'is_boss') for e in enemies):
                self.boss_spawned = True
                boss_type = (self.level // BOSS_LEVEL_INTERVAL - 1) % 5
                enemies.append(Boss(SCREEN_WIDTH // 2, -60, boss_type, self.level))
            # BOSS 关只有 BOSS，打完就过
            if self.boss_spawned and len(enemies) == 0:
                self.level_clear = True
            return

        # 普通关卡波次生成
        if len(self.enemies_to_spawn) == 0 and len(enemies) == 0:
            self.wave += 1
            if self.wave > self.max_waves:
                self.level_clear = True
                return
            self._prepare_wave()

        # 从待生成列表中定时生成敌人
        if len(self.enemies_to_spawn) > 0:
            self.spawn_timer -= 1
            if self.spawn_timer <= 0:
                self.spawn_timer = max(15, 45 - self.level * 2)
                etype = self.enemies_to_spawn.pop(0)
                x = random.randint(40, SCREEN_WIDTH - 40)
                y = -30
                enemies.append(Enemy(x, y, etype, self.level))

    def _prepare_wave(self):
        """根据当前关卡和波次准备敌人生成列表"""
        lv = self.level
        wave_size = 3 + lv // 5 + self.wave * 2

        # 可用敌人类型随关卡解锁
        available = [ENEMY_SMALL]
        if lv >= 3:
            available.append(ENEMY_MEDIUM)
        if lv >= 8:
            available.append(ENEMY_FAST)
        if lv >= 15:
            available.append(ENEMY_SHOOTER)
        if lv >= 25:
            available.append(ENEMY_LARGE)
        if lv >= 40:
            available.append(ENEMY_TANK)

        # 后期关卡敌人更多样
        weights = [max(1, 10 - lv)]
        if ENEMY_MEDIUM in available:
            weights.append(max(1, lv))
        if ENEMY_FAST in available:
            weights.append(max(1, lv - 5))
        if ENEMY_SHOOTER in available:
            weights.append(max(1, lv - 10))
        if ENEMY_LARGE in available:
            weights.append(max(1, lv - 20))
        if ENEMY_TANK in available:
            weights.append(max(1, lv - 35))

        self.enemies_to_spawn = []
        for _ in range(wave_size):
            etype = random.choices(available, weights=weights[:len(available)])[0]
            self.enemies_to_spawn.append(etype)

        random.shuffle(self.enemies_to_spawn)

    def get_level_text(self):
        if self.is_boss_level():
            return f"第 {self.level} 关 - BOSS 战"
        return f"第 {self.level} 关 - 波次 {self.wave}/{self.max_waves}"

    def get_difficulty_mult(self):
        return 1 + self.level * 0.1
