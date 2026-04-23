"""
Sky Defender - 升级系统
"""
import random
from config import *

class UpgradeSystem:
    def __init__(self, player):
        self.player = player
        self.levels = {key: 0 for key in UPGRADE_NAMES.keys()}
        self.max_level = 10
        self.available_weapons = [WEAPON_MACHINE_GUN]
        self.current_weapon = WEAPON_MACHINE_GUN
        self.coins = 0
        self.exp = 0
        self.exp_to_next = 100

    def get_level(self, upgrade_id):
        return self.levels.get(upgrade_id, 0)

    def add_exp(self, amount):
        self.exp += amount
        leveled_up = False
        while self.exp >= self.exp_to_next:
            self.exp -= self.exp_to_next
            self.exp_to_next = int(self.exp_to_next * 1.2) + 50
            leveled_up = True
        return leveled_up

    def add_coins(self, amount):
        self.coins += amount

    def can_upgrade(self, upgrade_id):
        return self.levels[upgrade_id] < self.max_level

    def upgrade(self, upgrade_id):
        if not self.can_upgrade(upgrade_id):
            return False
        cost = self.get_cost(upgrade_id)
        if self.coins < cost:
            return False
        self.coins -= cost
        self.levels[upgrade_id] += 1

        # 应用即时效果
        if upgrade_id == UPGRADE_MAX_HP:
            self.player.max_hp += 20
            self.player.hp += 20
        if upgrade_id == UPGRADE_MOVE_SPEED:
            self.player.speed += 0.3
        if upgrade_id == UPGRADE_SHIELD:
            self.player.shield = min(self.player.shield + 30, 100 + self.levels[upgrade_id] * 20)

        return True

    def get_cost(self, upgrade_id):
        base = 50
        lv = self.levels[upgrade_id]
        return int(base * (1 + lv * 0.5))

    def unlock_weapon(self, weapon_id):
        if weapon_id not in self.available_weapons:
            self.available_weapons.append(weapon_id)

    def switch_weapon(self, weapon_id):
        if weapon_id in self.available_weapons:
            self.current_weapon = weapon_id
            self.player.weapon.weapon_type = weapon_id
            return True
        return False

    def get_upgrade_desc(self, upgrade_id):
        descs = {
            UPGRADE_FIRE_RATE: "减少射击间隔",
            UPGRADE_DAMAGE: "提升子弹伤害",
            UPGRADE_BULLET_SPEED: "子弹飞得更快",
            UPGRADE_MULTISHOT: "增加子弹数量",
            UPGRADE_MOVE_SPEED: "提升移动速度",
            UPGRADE_MAX_HP: "增加最大生命值",
            UPGRADE_REGEN: "缓慢恢复生命",
            UPGRADE_CRIT_CHANCE: "增加暴击概率",
            UPGRADE_MAGNET: "扩大吸宝范围",
            UPGRADE_WINGMAN: "增加僚机数量",
            UPGRADE_SHIELD: "增加护盾容量",
            UPGRADE_BULLET_SIZE: "增大子弹体积",
        }
        return descs.get(upgrade_id, "")

    def get_random_offers(self, count=3):
        """返回随机升级选项（用于过关奖励）"""
        candidates = []
        for uid in self.levels.keys():
            if self.can_upgrade(uid):
                candidates.append(uid)
        if not candidates:
            return []
        random.shuffle(candidates)
        return candidates[:min(count, len(candidates))]

    def get_summary(self):
        lines = []
        for uid, lv in self.levels.items():
            if lv > 0:
                lines.append(f"{UPGRADE_NAMES[uid]}: Lv.{lv}")
        return lines
