#!/usr/bin/env python3
"""
Sky Defender - 天空防线
一个完整的 100 关纵向卷轴射击游戏

运行方式:
    python main.py

操作:
    WASD / 方向键 : 移动
    1-5           : 切换武器
    Q             : 使用核弹
    ESC           : 暂停 / 跳过升级界面
    空格 / 鼠标   : 菜单选择
"""
import sys
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))

from engine import GameEngine

def main():
    game = GameEngine()
    game.run()

if __name__ == "__main__":
    main()
