"""
Sky Defender - 游戏引擎与主循环
"""
import pygame
import random
import math
from config import *
from assets import ASSETS
from entities import Player, Enemy, Boss, Drop
from weapons import Bullet
from effects import ParticleManager, AnimationManager, Particle
from levels import LevelManager

class GameEngine:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Sky Defender - 天空防线")
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = STATE_MENU
        self.reset_game()
        self.stars = [(random.randint(0, SCREEN_WIDTH), random.randint(0, SCREEN_HEIGHT), random.uniform(0.5, 2)) for _ in range(100)]
        self.menu_selection = 0
        self.upgrade_selection = 0
        self.game_over_timer = 0
        self.shop_selection = 0
        self.shop_scroll = 0

    def reset_game(self):
        self.player = Player()
        self.level_mgr = LevelManager()
        self.level_mgr.start_level(1)
        self.enemies = []
        self.player_bullets = []
        self.enemy_bullets = []
        self.drops = []
        self.particles = ParticleManager()
        self.anims = AnimationManager()
        self.score = 0
        self.bg_y = 0
        self.menu_selection = 0

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 16.67
            self._handle_events()

            if self.state == STATE_MENU:
                self._update_menu()
                self._draw_menu()
            elif self.state == STATE_PLAYING:
                self._update_playing(dt)
                self._draw_playing()
            elif self.state == STATE_PAUSED:
                self._draw_playing(paused=True)
                self._draw_pause_overlay()
            elif self.state == STATE_UPGRADE:
                self._update_upgrade()
                self._draw_upgrade()
            elif self.state == STATE_GAME_OVER:
                self._update_gameover()
                self._draw_gameover()
            elif self.state == STATE_VICTORY:
                self._update_victory()
                self._draw_victory()
            elif self.state == STATE_SHOP:
                self._update_shop()
                self._draw_shop()
            elif self.state == STATE_HELP:
                self._update_help()
                self._draw_help()

            pygame.display.flip()

        pygame.quit()

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.state == STATE_PLAYING:
                        self.state = STATE_PAUSED
                    elif self.state == STATE_PAUSED:
                        self.state = STATE_PLAYING
                    elif self.state == STATE_UPGRADE:
                        self.state = STATE_PLAYING
                        self.level_mgr.start_level(self.level_mgr.level + 1)
                        if self.level_mgr.level > MAX_LEVEL:
                            self.state = STATE_VICTORY
                    elif self.state == STATE_SHOP:
                        self.state = STATE_PLAYING
                    elif self.state == STATE_HELP:
                        self.state = STATE_MENU

                if event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                    if self.state == STATE_MENU:
                        self._menu_select()
                    elif self.state == STATE_GAME_OVER or self.state == STATE_VICTORY:
                        self.reset_game()
                        self.state = STATE_MENU
                    elif self.state == STATE_UPGRADE:
                        self._upgrade_select()
                    elif self.state == STATE_SHOP:
                        self._shop_buy()

                if event.key == pygame.K_b:
                    if self.state == STATE_PLAYING:
                        self.state = STATE_SHOP
                        self.shop_selection = 0
                        self.shop_scroll = 0
                    elif self.state == STATE_SHOP:
                        self.state = STATE_PLAYING

                if event.key == pygame.K_UP or event.key == pygame.K_w:
                    if self.state == STATE_MENU:
                        self.menu_selection = max(0, self.menu_selection - 1)
                    elif self.state == STATE_UPGRADE:
                        self.upgrade_selection = max(0, self.upgrade_selection - 1)
                    elif self.state == STATE_SHOP:
                        self.shop_selection = max(0, self.shop_selection - 1)
                        self._ensure_shop_visible()

                if event.key == pygame.K_DOWN or event.key == pygame.K_s:
                    if self.state == STATE_MENU:
                        self.menu_selection = min(2, self.menu_selection + 1)
                    elif self.state == STATE_UPGRADE:
                        self.upgrade_selection = min(len(self.upgrade_offers) - 1, self.upgrade_selection + 1)
                    elif self.state == STATE_SHOP:
                        shop_items = self._get_shop_items()
                        self.shop_selection = min(len(shop_items) - 1, self.shop_selection + 1)
                        self._ensure_shop_visible()

                # 数字键切武器
                if self.state == STATE_PLAYING:
                    for i, key in enumerate([pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5]):
                        if event.key == key:
                            self.player.weapon.switch_weapon(i)
                    if event.key == pygame.K_q:
                        self.player.use_nuke(self.enemies, self.particles, self.anims)

                    # 技能按键 E-能量炮 R-全屏清怪
                    if event.key == pygame.K_e:
                        self.player.use_skill(SKILL_ENERGY_CANNON, self.enemies, self.particles, self.anims)
                    if event.key == pygame.K_r:
                        self.player.use_skill(SKILL_SCREEN_CLEAR, self.enemies, self.particles, self.anims)

            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.state == STATE_MENU:
                    mx, my = pygame.mouse.get_pos()
                    for i in range(3):
                        rect = pygame.Rect(SCREEN_WIDTH//2 - 100, 350 + i*70, 200, 50)
                        if rect.collidepoint(mx, my):
                            self.menu_selection = i
                            self._menu_select()
                elif self.state == STATE_UPGRADE:
                    mx, my = pygame.mouse.get_pos()
                    for i in range(len(self.upgrade_offers)):
                        rect = pygame.Rect(SCREEN_WIDTH//2 - 200, 250 + i*100, 400, 80)
                        if rect.collidepoint(mx, my):
                            self.upgrade_selection = i
                            self._upgrade_select()
                elif self.state == STATE_SHOP:
                    mx, my = pygame.mouse.get_pos()
                    shop_items = self._get_shop_items()
                    start_y = 160
                    item_height = 70
                    scroll_offset = getattr(self, 'shop_scroll', 0)

                    for i, item in enumerate(shop_items):
                        y = start_y + i * item_height - scroll_offset
                        # 只检测可见项目
                        if y + item_height < start_y or y > start_y + 380:
                            continue

                        rect = pygame.Rect(SCREEN_WIDTH//2 - 250, y, 500, item_height - 10)
                        if rect.collidepoint(mx, my):
                            self.shop_selection = i
                            self._shop_buy()
                            break

    def _menu_select(self):
        if self.menu_selection == 0:
            self.reset_game()
            self.state = STATE_PLAYING
        elif self.menu_selection == 1:
            # 打开帮助页面
            self.state = STATE_HELP
        elif self.menu_selection == 2:
            self.running = False

    def _update_menu(self):
        pass

    def _draw_menu(self):
        self.screen.blit(ASSETS.get('bg_space'), (0, 0))
        self._draw_stars()

        # 标题
        ASSETS.draw_text(self.screen, "SKY DEFENDER", 64, COLOR_CYAN, SCREEN_WIDTH//2, 180)
        ASSETS.draw_text(self.screen, "天空防线", 48, COLOR_WHITE, SCREEN_WIDTH//2, 250)

        # 菜单按钮
        labels = ["开始游戏", "操作说明", "退出"]
        for i, label in enumerate(labels):
            rect = pygame.Rect(SCREEN_WIDTH//2 - 100, 350 + i*70, 200, 50)
            is_selected = i == self.menu_selection

            # 选中项绘制发光边框和背景
            if is_selected:
                # 外发光效果
                for glow in range(3, 0, -1):
                    glow_rect = rect.inflate(glow * 4, glow * 4)
                    alpha = 60 - glow * 15
                    s = pygame.Surface(glow_rect.size, pygame.SRCALPHA)
                    s.fill((100, 200, 255, alpha))
                    self.screen.blit(s, glow_rect)

                # 选中背景 - 渐变效果
                bg_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
                for y in range(rect.height):
                    progress = y / rect.height
                    r = int(50 + 100 * progress)
                    g = int(100 + 150 * progress)
                    b = int(200 + 55 * progress)
                    pygame.draw.line(bg_surf, (r, g, b, 200), (0, y), (rect.width, y))
                self.screen.blit(bg_surf, rect)

                # 边框
                pygame.draw.rect(self.screen, COLOR_CYAN, rect, 3)

                # 箭头指示器
                arrow_x = rect.left - 30
                arrow_y = rect.centery
                pygame.draw.polygon(self.screen, COLOR_YELLOW, [
                    (arrow_x, arrow_y - 8),
                    (arrow_x + 12, arrow_y),
                    (arrow_x, arrow_y + 8)
                ])

                text_color = COLOR_WHITE
                font_size = 30
            else:
                # 未选中项 - 半透明背景
                s = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
                s.fill((30, 30, 40, 150))
                self.screen.blit(s, rect)
                pygame.draw.rect(self.screen, (80, 80, 100), rect, 1)
                text_color = (180, 180, 200)
                font_size = 26

            ASSETS.draw_text(self.screen, label, font_size, text_color, rect.centerx, rect.centery)

        # 选中"操作说明"时的提示
        if self.menu_selection == 1:
            ASSETS.draw_text(self.screen, "按 空格/回车 查看详细操作说明", 20, COLOR_YELLOW, SCREEN_WIDTH//2, 580)

    def _update_playing(self, dt):
        keys = pygame.key.get_pressed()
        self.player.update(keys, self.player_bullets)
        self.player.weapon.fire(self.player_bullets)
        self.player.weapon.update_laser(self.enemies, self.particles.particles)

        # 更新技能系统
        self.player.update_skills(self.enemies, self.particles, self.anims)

        # 击杀敌人获得能量 - 修复逻辑
        for e in self.enemies:
            if not e.alive and not e._gave_energy:
                energy_gain = 5 if hasattr(e, 'is_boss') and e.is_boss else 2
                self.player.add_skill_energy(energy_gain)
                e._gave_energy = True

        # 关卡更新
        self.level_mgr.update(self.enemies, self.player.y)

        # 更新实体
        for b in self.player_bullets:
            b.update(self.enemies if any(b.homing for b in self.player_bullets) else None)
        for b in self.enemy_bullets:
            b.update()
        for e in self.enemies:
            e.update(self.player, self.enemy_bullets)
        for d in self.drops:
            d.update(self.player)

        self.particles.update()
        self.anims.update()

        # 清理死亡实体
        self.player_bullets = [b for b in self.player_bullets if b.alive]
        self.enemy_bullets = [b for b in self.enemy_bullets if b.alive]
        self.enemies = [e for e in self.enemies if e.alive]
        self.drops = [d for d in self.drops if d.alive]

        # 碰撞检测
        self._check_collisions()

        # 关卡完成
        if self.level_mgr.level_clear:
            self._on_level_complete()

        # 玩家死亡
        if self.player.hp <= 0:
            self.state = STATE_GAME_OVER
            self.game_over_timer = 0

        # 背景滚动
        self.bg_y += 1

        # 引擎粒子
        self.particles.spawn_engine(self.player.x, self.player.y + 15)

        # 100关通关
        if self.level_mgr.level > MAX_LEVEL:
            self.state = STATE_VICTORY

    def _check_collisions(self):
        # 玩家子弹 vs 敌人
        for b in self.player_bullets:
            if not b.alive:
                continue
            for e in self.enemies:
                if not e.alive:
                    continue
                # 避免同一颗穿透弹对同一敌人重复伤害
                if b.piercing and e in b.hit_enemies:
                    continue
                dist = math.hypot(b.x - e.x, b.y - e.y)
                if dist < b.radius + e.radius:
                    e.take_damage(b.damage)
                    if b.piercing:
                        b.hit_enemies.add(e)
                    else:
                        b.alive = False
                    self.particles.spawn(e.x, e.y, 3, 2, 10, COLOR_YELLOW, 2)
                    if e.hp <= 0:
                        self._on_enemy_kill(e)
                    if not b.alive:
                        break

        # 敌人子弹 vs 玩家
        for b in self.enemy_bullets:
            dist = math.hypot(b.x - self.player.x, b.y - self.player.y)
            if dist < b.radius + self.player.radius:
                self.player.take_damage(b.damage)
                b.alive = False
                self.particles.spawn(self.player.x, self.player.y, 5, 3, 15, COLOR_RED, 3)

        # 敌人撞击玩家
        for e in self.enemies:
            dist = math.hypot(e.x - self.player.x, e.y - self.player.y)
            if dist < e.radius + self.player.radius:
                self.player.take_damage(20)
                e.take_damage(e.max_hp)
                self.particles.spawn(e.x, e.y, 8, 4, 20, COLOR_ORANGE, 3)
                if e.hp <= 0:
                    self._on_enemy_kill(e)

        # 玩家拾取道具
        for d in self.drops:
            dist = math.hypot(d.x - self.player.x, d.y - self.player.y)
            if dist < d.radius + self.player.radius + 10:
                d.apply(self.player)
                self.particles.spawn(d.x, d.y, 5, 2, 15, COLOR_CYAN, 2)

    def _on_enemy_kill(self, enemy):
        self.score += enemy.score
        self.player.upgrades.add_exp(enemy.score // 2)
        self.anims.add_explosion(enemy.x, enemy.y)
        self.particles.spawn_explosion(enemy.x, enemy.y, 1 + (enemy.radius // 20))
        self.level_mgr.total_enemies_killed += 1

        # 掉落
        drop_roll = random.random()
        if drop_roll < 0.4:
            self.drops.append(Drop(enemy.x, enemy.y, DROP_COIN))
        elif drop_roll < 0.5:
            self.drops.append(Drop(enemy.x, enemy.y, DROP_HP))
        elif drop_roll < 0.55:
            self.drops.append(Drop(enemy.x, enemy.y, DROP_NUKE))
        elif drop_roll < 0.6:
            self.drops.append(Drop(enemy.x, enemy.y, DROP_POWER))

        # BOSS 额外掉落和解锁武器
        if hasattr(enemy, 'is_boss') and enemy.is_boss:
            for _ in range(10):
                self.drops.append(Drop(enemy.x + random.randint(-50, 50), enemy.y + random.randint(-50, 50), DROP_COIN))
            for _ in range(3):
                self.drops.append(Drop(enemy.x + random.randint(-50, 50), enemy.y + random.randint(-50, 50), DROP_HP))
            # 解锁新武器
            weapon_unlock = (enemy.boss_type + 1) % 5
            self.player.upgrades.unlock_weapon(weapon_unlock)
            if weapon_unlock == WEAPON_SHOTGUN and self.player.upgrades.current_weapon == WEAPON_MACHINE_GUN:
                self.player.weapon.switch_weapon(WEAPON_SHOTGUN)
            if weapon_unlock == WEAPON_LASER and self.player.upgrades.current_weapon == WEAPON_MACHINE_GUN:
                self.player.weapon.switch_weapon(WEAPON_LASER)

    def _on_level_complete(self):
        self.level_mgr.level_clear = False
        # 奖励金币
        bonus = 50 + self.level_mgr.level * 10
        self.player.upgrades.add_coins(bonus)
        self.upgrade_offers = self.player.upgrades.get_random_offers(3)
        if not self.upgrade_offers:
            self.upgrade_offers = [UPGRADE_FIRE_RATE, UPGRADE_DAMAGE, UPGRADE_MAX_HP]
        # 如果所有选项都已满级无法升级，直接进入下一关
        if not any(self.player.upgrades.can_upgrade(uid) for uid in self.upgrade_offers):
            self.level_mgr.start_level(self.level_mgr.level + 1)
            if self.level_mgr.level > MAX_LEVEL:
                self.state = STATE_VICTORY
            return
        self.upgrade_selection = 0
        self.state = STATE_UPGRADE

    def _draw_playing(self, paused=False):
        # 背景
        self.screen.blit(ASSETS.get('bg_space'), (0, 0))
        self.screen.blit(ASSETS.get('bg_nebula'), (0, (self.bg_y * 0.5) % SCREEN_HEIGHT - SCREEN_HEIGHT))
        self.screen.blit(ASSETS.get('bg_nebula'), (0, (self.bg_y * 0.5) % SCREEN_HEIGHT))
        self._draw_stars()

        # 实体
        for d in self.drops:
            d.draw(self.screen)
        self.player.weapon.draw_laser(self.screen)
        for b in self.player_bullets:
            b.draw(self.screen)
        for b in self.enemy_bullets:
            b.draw(self.screen)
        for e in self.enemies:
            e.draw(self.screen)
        self.player.draw(self.screen)
        self.particles.draw(self.screen)
        self.anims.draw(self.screen)

        # HUD
        ASSETS.draw_text(self.screen, self.level_mgr.get_level_text(), 24, COLOR_WHITE, SCREEN_WIDTH//2, 20)
        ASSETS.draw_text(self.screen, f"分数: {self.score}", 20, COLOR_YELLOW, 20, 20, center=False)
        ASSETS.draw_text(self.screen, f"金币: {int(self.player.upgrades.coins)}", 20, COLOR_YELLOW, 20, 50, center=False)
        ASSETS.draw_text(self.screen, f"生命: {int(self.player.hp)}/{self.player.max_hp}", 20, COLOR_GREEN, 20, 80, center=False)
        if self.player.shield > 0:
            ASSETS.draw_text(self.screen, f"护盾: {int(self.player.shield)}", 20, COLOR_CYAN, 20, 110, center=False)
        if self.player.nukes > 0:
            ASSETS.draw_text(self.screen, f"核弹: {self.player.nukes} (Q)", 20, COLOR_ORANGE, 20, 140, center=False)

        # 武器信息
        wname = WEAPON_NAMES.get(self.player.weapon.weapon_type, "未知")
        ASSETS.draw_text(self.screen, f"武器: {wname}", 20, COLOR_CYAN, SCREEN_WIDTH - 220, 20, center=False)
        ASSETS.draw_text(self.screen, f"升级项: {len(self.player.upgrades.get_summary())}项", 16, COLOR_GRAY, SCREEN_WIDTH - 220, 50, center=False)
        ASSETS.draw_text(self.screen, "按 B 打开商店", 16, COLOR_YELLOW, SCREEN_WIDTH - 220, 75, center=False)

        # 绘制技能HUD - 在左下角
        self.player._draw_skill_bars(self.screen)

    def _draw_stars(self):
        for sx, sy, spd in self.stars:
            y = (sy + self.bg_y * spd) % SCREEN_HEIGHT
            pygame.draw.circle(self.screen, COLOR_WHITE, (int(sx), int(y)), 1)

    def _draw_pause_overlay(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))
        ASSETS.draw_text(self.screen, "暂停", 48, COLOR_WHITE, SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 50)
        ASSETS.draw_text(self.screen, "按 ESC 继续", 24, COLOR_GRAY, SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 20)

    def _update_upgrade(self):
        pass

    def _upgrade_select(self):
        if self.upgrade_selection < len(self.upgrade_offers):
            uid = self.upgrade_offers[self.upgrade_selection]
            ok = self.player.upgrades.upgrade(uid)
            if ok:
                self.state = STATE_PLAYING
                self.level_mgr.start_level(self.level_mgr.level + 1)
                if self.level_mgr.level > MAX_LEVEL:
                    self.state = STATE_VICTORY

    def _draw_upgrade(self):
        self.screen.fill(COLOR_BLACK)
        self.screen.blit(ASSETS.get('bg_space'), (0, 0))

        ASSETS.draw_text(self.screen, f"第 {self.level_mgr.level} 关完成!", 40, COLOR_YELLOW, SCREEN_WIDTH//2, 80)
        ASSETS.draw_text(self.screen, f"当前金币: {int(self.player.upgrades.coins)}", 24, COLOR_WHITE, SCREEN_WIDTH//2, 140)
        ASSETS.draw_text(self.screen, "选择一个升级:", 24, COLOR_CYAN, SCREEN_WIDTH//2, 190)

        for i, uid in enumerate(self.upgrade_offers):
            rect = pygame.Rect(SCREEN_WIDTH//2 - 200, 250 + i*100, 400, 80)
            selected = i == self.upgrade_selection
            color = (0, 100, 180, 200) if selected else (30, 30, 60, 180)
            s = pygame.Surface((400, 80), pygame.SRCALPHA)
            s.fill(color)
            self.screen.blit(s, rect)
            pygame.draw.rect(self.screen, COLOR_WHITE if selected else COLOR_GRAY, rect, 2 if selected else 1)

            name = UPGRADE_NAMES[uid]
            lv = self.player.upgrades.get_level(uid)
            cost = self.player.upgrades.get_cost(uid)
            ASSETS.draw_text(self.screen, f"{name} (Lv.{lv+1})", 28, COLOR_WHITE, rect.centerx, rect.top + 25)
            ASSETS.draw_text(self.screen, f"{self.player.upgrades.get_upgrade_desc(uid)} - 花费: {cost}金币", 20, COLOR_GRAY, rect.centerx, rect.top + 55)

        ASSETS.draw_text(self.screen, "按 空格/点击 选择, ESC 跳过", 20, COLOR_GRAY, SCREEN_WIDTH//2, 600)

    def _update_help(self):
        pass

    def _draw_help(self):
        """绘制帮助页面"""
        self.screen.fill(COLOR_BLACK)
        self.screen.blit(ASSETS.get('bg_space'), (0, 0))
        self._draw_stars()

        # 标题
        ASSETS.draw_text(self.screen, "操作说明", 48, COLOR_YELLOW, SCREEN_WIDTH//2, 60)

        # 帮助内容分组
        helps = [
            ("移动控制", [
                "WASD / 方向键 : 移动",
            ]),
            ("武器系统", [
                "自动射击",
                "1-5 : 切换5种武器",
                "机关枪 - 快速射击",
                "散弹枪 - 扇形多发",
                "激光炮 - 持续穿透",
                "追踪导弹 - 自动索敌",
                "等离子球 - 穿透伤害",
            ]),
            ("技能系统", [
                "E : 能量炮 (消耗30能量)",
                "    前方高伤害穿透光束",
                "R : 全屏清怪 (消耗60能量)",
                "    秒杀普通敌人，BOSS掉15%血",
                "",
                "击杀敌人获得能量：普通+2，BOSS+5",
            ]),
            ("其他操作", [
                "Q : 使用核弹",
                "B : 打开商店",
                "ESC : 暂停/返回",
                "空格/回车 : 确认选择",
            ]),
        ]

        y = 130
        for group_title, items in helps:
            # 分组标题
            ASSETS.draw_text(self.screen, group_title, 22, COLOR_CYAN, SCREEN_WIDTH//2, y)
            y += 30

            # 内容
            for item in items:
                if item:  # 跳过空字符串
                    ASSETS.draw_text(self.screen, item, 18, COLOR_WHITE, SCREEN_WIDTH//2, y)
                y += 24
            y += 10  # 组间距

        # 返回提示
        ASSETS.draw_text(self.screen, "按 ESC 返回主菜单", 20, COLOR_GRAY, SCREEN_WIDTH//2, SCREEN_HEIGHT - 40)

    def _update_gameover(self):
        self.game_over_timer += 1

    def _draw_gameover(self):
        self._draw_playing()
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        ASSETS.draw_text(self.screen, "GAME OVER", 56, COLOR_RED, SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 60)
        ASSETS.draw_text(self.screen, f"最终得分: {self.score}", 28, COLOR_WHITE, SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 10)
        ASSETS.draw_text(self.screen, f"到达关卡: {self.level_mgr.level}", 24, COLOR_GRAY, SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 50)
        ASSETS.draw_text(self.screen, "按 空格 返回主菜单", 22, COLOR_YELLOW, SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 100)

    def _update_victory(self):
        self.game_over_timer += 1

    def _draw_victory(self):
        self.screen.fill(COLOR_BLACK)
        self.screen.blit(ASSETS.get('bg_space'), (0, 0))
        self._draw_stars()
        ASSETS.draw_text(self.screen, "VICTORY!", 64, COLOR_YELLOW, SCREEN_WIDTH//2, 200)
        ASSETS.draw_text(self.screen, "恭喜你通关了全部100关!", 32, COLOR_WHITE, SCREEN_WIDTH//2, 300)
        ASSETS.draw_text(self.screen, f"最终得分: {self.score}", 28, COLOR_CYAN, SCREEN_WIDTH//2, 380)
        ASSETS.draw_text(self.screen, f"击杀敌机: {self.level_mgr.total_enemies_killed}", 24, COLOR_GRAY, SCREEN_WIDTH//2, 430)
        ASSETS.draw_text(self.screen, "按 空格 返回主菜单", 22, COLOR_WHITE, SCREEN_WIDTH//2, 520)

    def _update_shop(self):
        pass

    def _draw_shop(self):
        # 背景
        self.screen.fill(COLOR_BLACK)
        self.screen.blit(ASSETS.get('bg_space'), (0, 0))
        self._draw_stars()

        # 标题
        ASSETS.draw_text(self.screen, "战机商店", 48, COLOR_YELLOW, SCREEN_WIDTH//2, 50)
        ASSETS.draw_text(self.screen, f"当前金币: {int(self.player.upgrades.coins)}", 24, COLOR_WHITE, SCREEN_WIDTH//2, 110)

        # 商店商品
        shop_items = self._get_shop_items()
        start_y = 160
        item_height = 70
        scroll_offset = getattr(self, 'shop_scroll', 0)

        # 裁剪区域
        clip_rect = pygame.Rect(SCREEN_WIDTH//2 - 260, start_y, 520, 380)

        for i, item in enumerate(shop_items):
            y = start_y + i * item_height - scroll_offset

            # 只绘制可见项目
            if y + item_height < start_y or y > start_y + 380:
                continue

            rect = pygame.Rect(SCREEN_WIDTH//2 - 250, y, 500, item_height - 10)

            # 选中效果
            selected = i == getattr(self, 'shop_selection', 0)
            if selected:
                s = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
                s.fill((100, 150, 255, 80))
                self.screen.blit(s, rect)
                pygame.draw.rect(self.screen, COLOR_CYAN, rect, 2)
            else:
                pygame.draw.rect(self.screen, (60, 60, 80), rect, 1)

            # 商品信息
            name_color = COLOR_GREEN if item['owned'] else (COLOR_GRAY if item['can_afford'] else COLOR_RED)
            ASSETS.draw_text(self.screen, item['name'], 24, name_color, rect.left + 15, rect.centery - 10, center=False)
            ASSETS.draw_text(self.screen, item['desc'], 16, COLOR_GRAY, rect.left + 15, rect.centery + 15, center=False)

            # 价格或已拥有
            if item['owned']:
                ASSETS.draw_text(self.screen, "已拥有", 20, COLOR_GREEN, rect.right - 80, rect.centery)
            else:
                price_color = COLOR_YELLOW if item['can_afford'] else COLOR_RED
                ASSETS.draw_text(self.screen, f"{item['price']}金币", 20, price_color, rect.right - 80, rect.centery)

        # 绘制滚动指示器
        if len(shop_items) > 5:
            pygame.draw.rect(self.screen, COLOR_DARK_GRAY, (SCREEN_WIDTH//2 + 270, start_y, 8, 380))
            scroll_ratio = getattr(self, 'shop_scroll', 0) / max(1, len(shop_items) * item_height - 380)
            indicator_y = start_y + scroll_ratio * 340
            pygame.draw.rect(self.screen, COLOR_GRAY, (SCREEN_WIDTH//2 + 270, indicator_y, 8, 40))

        # 操作提示
        ASSETS.draw_text(self.screen, "↑↓ 选择 | 空格/回车 购买 | B/ESC 关闭商店", 20, COLOR_GRAY, SCREEN_WIDTH//2, SCREEN_HEIGHT - 40)

    def _ensure_shop_visible(self):
        """确保选中的商店项在可视范围内"""
        item_height = 70
        visible_height = 400
        max_scroll = max(0, len(self._get_shop_items()) * item_height - visible_height)

        target_scroll = self.shop_selection * item_height - visible_height // 2
        self.shop_scroll = max(0, min(max_scroll, target_scroll))

    def _shop_buy(self):
        """购买商店中的商品"""
        shop_items = self._get_shop_items()
        if self.shop_selection >= len(shop_items):
            return

        item = shop_items[self.shop_selection]
        if item['owned'] or not item['can_afford']:
            return

        upgrades = self.player.upgrades

        if item['type'] == 'weapon':
            if upgrades.coins >= item['price']:
                upgrades.coins -= item['price']
                upgrades.unlock_weapon(item['id'])
        elif item['type'] == 'upgrade':
            if upgrades.coins >= item['price'] and upgrades.can_upgrade(item['id']):
                upgrades.coins -= item['price']
                upgrades.upgrade(item['id'])

    def _get_shop_items(self):
        """获取商店商品列表"""
        items = []
        upgrades = self.player.upgrades

        # 武器解锁
        weapon_prices = {WEAPON_SHOTGUN: 200, WEAPON_LASER: 400, WEAPON_MISSILE: 600, WEAPON_PLASMA: 800}
        for w_id, price in weapon_prices.items():
            owned = w_id in upgrades.available_weapons
            items.append({
                'type': 'weapon',
                'id': w_id,
                'name': f"解锁{WEAPON_NAMES[w_id]}",
                'desc': "新武器，可在战斗中按数字键切换",
                'price': price,
                'owned': owned,
                'can_afford': upgrades.coins >= price
            })

        # 升级项目购买
        upgrade_prices = {
            UPGRADE_FIRE_RATE: 100,
            UPGRADE_DAMAGE: 100,
            UPGRADE_BULLET_SPEED: 80,
            UPGRADE_MULTISHOT: 150,
            UPGRADE_MOVE_SPEED: 80,
            UPGRADE_MAX_HP: 100,
            UPGRADE_REGEN: 120,
            UPGRADE_CRIT_CHANCE: 150,
            UPGRADE_MAGNET: 100,
            UPGRADE_WINGMAN: 200,
            UPGRADE_SHIELD: 120,
            UPGRADE_BULLET_SIZE: 100,
        }

        for u_id, price in upgrade_prices.items():
            current_lv = upgrades.get_level(u_id)
            maxed = current_lv >= 10
            items.append({
                'type': 'upgrade',
                'id': u_id,
                'name': f"{UPGRADE_NAMES[u_id]} Lv.{current_lv+1}",
                'desc': upgrades.get_upgrade_desc(u_id) if not maxed else "已达最大等级",
                'price': price if not maxed else 0,
                'owned': maxed,
                'can_afford': upgrades.coins >= price and not maxed
            })

        return items
