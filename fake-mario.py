"""
横スクロールアクションゲーム（マリオ風）- ゴール機能付き拡張版

Pygameを使用した2Dドット絵スタイルの横スクロールアクションゲームの
完全版です。以下の機能を備えています：
- シーン管理（タイトル、ゲーム本編、ゲームクリア、ゲームオーバー）
- プレイヤーの移動・ジャンプ・重力処理
- ブロックによるステージ構築
- 横スクロール（カメラワーク）機能
- ゴール機能（Goal クラス）
- 拡張性の高いオブジェクト指向設計
"""

import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import pygame
import sys
from typing import Tuple, List, Optional
from enum import Enum
from abc import ABC, abstractmethod

BlockConfig = Tuple[int, int, int, int, str]

# ==============================================================================
# 1. 定数・グローバル設定 (Config & Enums)
# ==============================================================================
class Config:
    """ゲーム全体の設定値を管理するクラス"""
    SCREEN_WIDTH: int = 800
    SCREEN_HEIGHT: int = 600
    FPS: int = 60
    
    # 色定義
    COLOR_BLACK: Tuple[int, int, int] = (0, 0, 0)
    COLOR_WHITE: Tuple[int, int, int] = (255, 255, 255)
    COLOR_BLUE: Tuple[int, int, int] = (0, 100, 255)
    COLOR_GREEN: Tuple[int, int, int] = (0, 200, 0)
    COLOR_RED: Tuple[int, int, int] = (255, 0, 0)
    COLOR_GRAY: Tuple[int, int, int] = (128, 128, 128)
    COLOR_LIGHT_BLUE: Tuple[int, int, int] = (135, 206, 235)
    COLOR_GOLD: Tuple[int, int, int] = (255, 215, 0)
    COLOR_DARK_YELLOW: Tuple[int, int, int] = (200, 200, 0)
    
    # プレイヤー設定
    PLAYER_WIDTH: int = 32
    PLAYER_HEIGHT: int = 48
    PLAYER_START_X: int = 100
    PLAYER_START_Y: int = 400
    PLAYER_MOVE_SPEED: int = 5
    PLAYER_JUMP_POWER: int = 15
    
    # 物理設定
    GRAVITY: float = 0.6
    MAX_FALL_SPEED: int = 20
    
    # オブジェクト設定
    BLOCK_WIDTH: int = 64
    BLOCK_HEIGHT: int = 64
    GOAL_WIDTH: int = 50
    GOAL_HEIGHT: int = 80
    GOAL_X: int = 3200
    GOAL_Y: int = 410
    STAGE_MAX_X: int = 3300

    # パス設定
    BACKGROUND_COLOR: Tuple[int, int, int] = COLOR_LIGHT_BLUE
    BACKGROUND_IMAGE_PATH: str = "背景.png"  
    GROUND_IMAGE_PATH: str = "地面.png"            
    BLOCK_IMAGE_PATH: str = "ブロック.png"
    GOAL_IMAGE_PATH: str = "ゴールお城.png"         
    PLAYER_IMAGE_PATH: str = "主人公.png"
    ITEM_MUSHROOM_IMAGE_PATH: str = "キノコ.png"
    
    TIME_LIMIT: float = 300.0
    
    # 敵設定
    ENEMY_WIDTH: int = 32
    ENEMY_HEIGHT: int = 32
    ENEMY_SPEED: float = 2.0


class SceneType(Enum):
    TITLE = 1
    GAME = 2
    GAME_OVER = 3
    GAME_CLEAR = 4

class ItemType(Enum):
    GROW = 1
    INVINCIBLE = 2
    FIRE = 3

class PlayerState(Enum):
    NORMAL = 1
    BIG = 2
    FIRE = 3


# ==============================================================================
# 2. ゲームオブジェクトクラス群 (Blocks, Goal, Fireball, Items, Enemies)
# ==============================================================================
class Block:
    """ステージの床や足場を表すクラス"""
    def __init__(self, x: int, y: int, width: int = Config.BLOCK_WIDTH,
                 height: int = Config.BLOCK_HEIGHT, 
                 kind: str = "ground",
                 color: Tuple[int, int, int] = Config.COLOR_GREEN,
                 image: Optional[pygame.Surface] = None) -> None:
        self.x: int = int(x)
        self.y: int = int(y)
        self.width: int = int(width)
        self.height: int = int(height)
        self.kind: str = kind
        self.color: Tuple[int, int, int] = color
        self.image: Optional[pygame.Surface] = image

        if self.image is None:
            try:
                current_dir = os.path.dirname(os.path.abspath(__file__))
                file_name = None
                if kind == "ground":
                    file_name = Config.GROUND_IMAGE_PATH
                elif kind in ("platform", "step"):
                    file_name = Config.BLOCK_IMAGE_PATH
                elif kind == "goal":
                    file_name = Config.GOAL_IMAGE_PATH

                if file_name is not None:
                    full_path = os.path.join(current_dir, file_name)
                    self.image = pygame.image.load(full_path).convert_alpha()
            except Exception as e:
                # print(f"ブロック画像（{kind}）の読み込みに失敗: {e}")
                self.image = None

        if self.image is not None:
            stretch_scale = 1.8
            self.height = int(self.height * stretch_scale)
            self.image = pygame.transform.scale(self.image, (self.width, self.height))
        else:
            self.color = self._get_color_for_kind(kind)

    def _get_color_for_kind(self, kind: str) -> Tuple[int, int, int]:
        kind_to_color = {
            "ground": Config.COLOR_GREEN,
            "platform": Config.COLOR_GRAY,
            "step": Config.COLOR_DARK_YELLOW,
            "goal": Config.COLOR_GOLD,
        }
        return kind_to_color.get(kind, self.color)

    def get_rect(self) -> pygame.Rect:
        sink_pixels = 65
        adjusted_y = self.y + sink_pixels
        adjusted_height = self.height - sink_pixels
        if adjusted_height <= 0:
            adjusted_height = 1
        return pygame.Rect(self.x, adjusted_y, self.width, adjusted_height)
    
    def draw(self, surface: pygame.Surface, camera_x: int) -> None:
        screen_x: int = self.x - int(camera_x)
        if screen_x + self.width < 0 or screen_x > Config.SCREEN_WIDTH:
            return
        
        if self.image is not None:
            surface.blit(self.image, (screen_x, self.y))
        else:
            rect = pygame.Rect(screen_x, self.y, self.width, self.height)
            pygame.draw.rect(surface, self.color, rect)
            pygame.draw.rect(surface, Config.COLOR_BLACK, rect, 2)


class Goal:
    """ステージのゴール（ゴール地点）を表すクラス"""
    def __init__(self, x: int = Config.GOAL_X, y: int = Config.GOAL_Y,
                 width: int = Config.GOAL_WIDTH, height: int = Config.GOAL_HEIGHT) -> None:
        self.x: int = int(x)
        self.y: int = int(y)
        self._original_width: int = int(width)
        self._original_height: int = int(height)
        self.color: Tuple[int, int, int] = Config.COLOR_GOLD
        self.image: Optional[pygame.Surface] = None

        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            full_path = os.path.join(current_dir, Config.GOAL_IMAGE_PATH)
            self.image = pygame.image.load(full_path).convert_alpha()
            
            scale_size = 4.0
            self.width = int(self._original_width * scale_size)
            self.height = int(self._original_height * scale_size)
            self.x = self.x - (self.width - self._original_width) - 64
            self.y = self.y - (self.height - self._original_height) + 40
            self.image = pygame.transform.scale(self.image, (self.width, self.height))
        except Exception:
            self.width = self._original_width
            self.height = self._original_height
    
    def get_rect(self) -> pygame.Rect:
        shrink_pixels_x = 90 
        adjusted_x = self.x + shrink_pixels_x
        adjusted_width = self.width - (shrink_pixels_x * 2)
        if adjusted_width <= 0:
            adjusted_width = 1
        return pygame.Rect(adjusted_x, self.y, adjusted_width, self.height)
    
    def check_collision(self, player_rect: pygame.Rect) -> bool:
        return player_rect.colliderect(self.get_rect())
    
    def draw(self, surface: pygame.Surface, camera_x: int) -> None:
        screen_x: int = self.x - int(camera_x)
        if screen_x + self.width < 0 or screen_x > Config.SCREEN_WIDTH:
            return
        if self.image is not None:
            surface.blit(self.image, (screen_x, self.y))
        else:
            goal_rect = pygame.Rect(screen_x, self.y, self.width, self.height)
            pygame.draw.rect(surface, self.color, goal_rect)
            pygame.draw.rect(surface, Config.COLOR_BLACK, goal_rect, 3)


class Fireball:
    """ファイア状態のプレイヤーが放つ火の玉クラス"""
    def __init__(self, x: float, y: float, facing_right: bool) -> None:
        self.x: float = x
        self.y: float = y
        self.width: int = 16
        self.height: int = 16
        self.vx: float = 8.0 if facing_right else -8.0
        self.vy: float = 0.0
        self.color: Tuple[int, int, int] = (255, 69, 0)
        self.is_alive: bool = True

    def get_rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), self.width, self.height)

    def update(self, blocks: List[Block]) -> None:
        self.vy += Config.GRAVITY
        if self.vy > Config.MAX_FALL_SPEED:
            self.vy = Config.MAX_FALL_SPEED
        self.x += self.vx
        self.y += self.vy

        fire_rect = self.get_rect()
        for block in blocks:
            block_rect = block.get_rect()
            if fire_rect.colliderect(block_rect):
                overlap_y_from_top = fire_rect.bottom - block_rect.top
                overlap_x_from_left = fire_rect.right - block_rect.left
                overlap_x_from_right = block_rect.right - fire_rect.left
                min_overlap = min(overlap_y_from_top, overlap_x_from_left, overlap_x_from_right)
                
                if min_overlap == overlap_y_from_top:
                    self.y = block_rect.top - self.height
                    self.vy = -6.0
                else:
                    self.is_alive = False
                    return

        if self.y > Config.SCREEN_HEIGHT or self.x < 0 or self.x > Config.STAGE_MAX_X:
            self.is_alive = False

    def draw(self, surface: pygame.Surface, camera_x: int) -> None:
        screen_x: int = int(self.x) - camera_x
        if screen_x + self.width < 0 or screen_x > Config.SCREEN_WIDTH:
            return
        rect = pygame.Rect(screen_x, int(self.y), self.width, self.height)
        pygame.draw.ellipse(surface, self.color, rect)
        pygame.draw.ellipse(surface, Config.COLOR_BLACK, rect, 1)


class Item:
    """ステージ上に配置されるアイテムクラス"""
    def __init__(self, x: int, y: int, item_type: ItemType) -> None:
        self.x: int = x
        self.y: int = y
        self.width: int = 32
        self.height: int = 32
        self.item_type: ItemType = item_type
        if self.item_type == ItemType.GROW:
            self.color = (255, 100, 100)
        elif self.item_type == ItemType.INVINCIBLE:
            self.color = Config.COLOR_GOLD
        elif self.item_type == ItemType.FIRE:
            self.color = (255, 140, 0)

    def get_rect(self) -> pygame.Rect:
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def draw(self, surface: pygame.Surface, camera_x: int) -> None:
        screen_x: int = self.x - camera_x
        if screen_x + self.width < 0 or screen_x > Config.SCREEN_WIDTH:
            return
        rect = pygame.Rect(screen_x, self.y, self.width, self.height)
        pygame.draw.rect(surface, self.color, rect)
        pygame.draw.rect(surface, Config.COLOR_BLACK, rect, 2)
        inner = pygame.Rect(screen_x + 8, self.y + 8, self.width - 16, self.height - 16)
        pygame.draw.rect(surface, Config.COLOR_WHITE, inner, 1)


class Enemy:
    """自動で歩き、壁で反転し、プレイヤーと接触判定を行うシンプルなザコ敵"""
    def __init__(self, x: int, y: int) -> None:
        self.x: float = x
        self.y: float = y
        self.width: int = Config.ENEMY_WIDTH
        self.height: int = Config.ENEMY_HEIGHT
        self.vx: float = -Config.ENEMY_SPEED
        self.vy: float = 0.0
        self.color: Tuple[int, int, int] = Config.COLOR_RED
        self.is_alive: bool = True
        
    def get_rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), self.width, self.height)
        
    def update(self, blocks: List[Block]) -> None:
        self.vy += Config.GRAVITY
        if self.vy > Config.MAX_FALL_SPEED:
            self.vy = Config.MAX_FALL_SPEED
            
        self.x += self.vx
        self.y += self.vy
        
        enemy_rect = self.get_rect()
        for block in blocks:
            block_rect = block.get_rect()
            if enemy_rect.colliderect(block_rect):
                overlap_x = min(enemy_rect.right - block_rect.left, block_rect.right - enemy_rect.left)
                overlap_y = min(enemy_rect.bottom - block_rect.top, block_rect.bottom - enemy_rect.top)
                
                if overlap_y < overlap_x:
                    if self.vy > 0: 
                        self.y = block_rect.top - self.height
                        self.vy = 0.0
                else: 
                    if self.vx > 0:
                        self.x = block_rect.left - self.width
                    else:
                        self.x = block_rect.right
                    self.vx *= -1
                    
        if self.y > Config.SCREEN_HEIGHT + 100:
            self.is_alive = False

    def draw(self, surface: pygame.Surface, camera_x: int) -> None:
        screen_x = int(self.x) - camera_x
        if screen_x + self.width < 0 or screen_x > Config.SCREEN_WIDTH:
            return
        rect = pygame.Rect(screen_x, int(self.y), self.width, self.height)
        pygame.draw.rect(surface, self.color, rect)
        pygame.draw.rect(surface, Config.COLOR_BLACK, rect, 2)


class Boss(Enemy):
    """3回踏まないと倒せない巨大なボスクラス"""
    def __init__(self, x: int, y: int) -> None:
        super().__init__(x, y)
        self.width = 80
        self.height = 96
        self.vx = -1.2
        self.color = (0, 150, 50) 
        self.hp: int = 3

    def take_damage(self) -> bool:
        self.hp -= 1
        if self.hp <= 0:
            self.is_alive = False
            return True
        self.vx *= 1.5
        return False


# ==============================================================================
# 3. プレイヤークラス (Player)
# ==============================================================================
class Player:
    """プレイヤーキャラクターを制御するメインクラス"""
    def __init__(self, x: int = Config.PLAYER_START_X,
                 y: int = Config.PLAYER_START_Y,
                 width: int = Config.PLAYER_WIDTH,
                 height: int = Config.PLAYER_HEIGHT) -> None:
        self.x: float = x
        self.y: float = y
        self.width: int = width
        self.height: int = height
        self.vx: float = 0.0
        self.vy: float = 0.0
        self.is_jumping: bool = False
        self.is_on_ground: bool = True
        self.color: Tuple[int, int, int] = Config.COLOR_BLUE
        self.facing_right: bool = True 

        # 特殊状態・タイマー関連
        self.state: PlayerState = PlayerState.NORMAL
        self.is_invincible: bool = False
        self.invincible_timer: int = 0
        self.damage_invincible_timer: int = 0
        self.fire_cooldown: int = 0
        self.pending_fireballs: List[Fireball] = []

        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            file_name = getattr(Config, "PLAYER_IMAGE_PATH", "主人公.png")
            full_path = os.path.join(current_dir, file_name)
            self.image_original = pygame.image.load(full_path).convert_alpha()
            self.image_original = pygame.transform.scale(self.image_original, (self.width, self.height))
        except Exception:
            self.image_original = None
    
    def get_rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), self.width, self.height)
    
    def change_state(self, new_state: PlayerState) -> None:
        old_height = self.height
        self.state = new_state
        
        if self.state == PlayerState.NORMAL:
            self.height = Config.PLAYER_HEIGHT
            self.color = Config.COLOR_BLUE
        elif self.state == PlayerState.BIG:
            self.height = int(Config.PLAYER_HEIGHT * 1.4)
            self.color = (0, 150, 255)
        elif self.state == PlayerState.FIRE:
            self.height = int(Config.PLAYER_HEIGHT * 1.4)
            self.color = Config.COLOR_RED
            
        self.y -= (self.height - old_height)
        if self.image_original:
            self.image_original = pygame.transform.scale(self.image_original, (self.width, self.height))

    def hit_enemy(self) -> Optional[SceneType]:
        if self.is_invincible or self.damage_invincible_timer > 0:
            return None
            
        if self.state == PlayerState.FIRE:
            self.change_state(PlayerState.BIG)
            self.damage_invincible_timer = 60
        elif self.state == PlayerState.BIG:
            self.change_state(PlayerState.NORMAL)
            self.damage_invincible_timer = 60
        else:
            return SceneType.GAME_OVER
        return None

    def handle_input(self, keys: 'pygame.key.ScancodeWrapper') -> bool:
        jumped = False
        if keys[pygame.K_LEFT]:
            self.vx = -Config.PLAYER_MOVE_SPEED
            self.facing_right = False
        elif keys[pygame.K_RIGHT]:
            self.vx = Config.PLAYER_MOVE_SPEED
            self.facing_right = True
        else:
            self.vx = 0.0
        
        if (keys[pygame.K_SPACE] or keys[pygame.K_RETURN]) and self.is_on_ground:
            self.vy = -Config.PLAYER_JUMP_POWER
            self.is_jumping = True
            self.is_on_ground = False
            jumped = True
            
        if keys[pygame.K_x] and self.state == PlayerState.FIRE and self.fire_cooldown == 0:
            fx = self.x + self.width if self.facing_right else self.x - 16
            fy = self.y + self.height // 3
            self.pending_fireballs.append(Fireball(fx, fy, self.facing_right))
            self.fire_cooldown = 15
            
        return jumped

    def update(self, blocks: List[Block]) -> None:
        if self.fire_cooldown > 0:
            self.fire_cooldown -= 1
        if self.is_invincible:
            self.invincible_timer -= 1
            if self.invincible_timer <= 0:
                self.is_invincible = False
        if self.damage_invincible_timer > 0:
            self.damage_invincible_timer -= 1

        self.apply_gravity(blocks)

    def apply_gravity(self, blocks: List[Block]) -> None:
        """重力を適用してY方向の速度を更新"""
        # 重力加速度を追加
        self.vy += Config.GRAVITY

        # 最大落下速度に制限
        if self.vy > Config.MAX_FALL_SPEED:
            self.vy = Config.MAX_FALL_SPEED
        
        self.x += self.vx
        self.y += self.vy
        
        self._check_block_collisions(blocks)
        
        if self.y > Config.SCREEN_HEIGHT + 100:
            self.reset()
    
    def _check_block_collisions(self, blocks: List[Block]) -> None:
        player_rect = self.get_rect()
        self.is_on_ground = False 
        
        for block in blocks:
            block_rect = block.get_rect()
            if not player_rect.colliderect(block_rect):
                continue
            
            overlap_y_from_top = player_rect.bottom - block_rect.top
            overlap_y_from_bottom = block_rect.bottom - player_rect.top
            overlap_x_from_left = player_rect.right - block_rect.left
            overlap_x_from_right = block_rect.right - player_rect.left
            
            min_overlap = min(overlap_y_from_top, overlap_y_from_bottom,
                                   overlap_x_from_left, overlap_x_from_right)
            
            if min_overlap == overlap_y_from_top and self.vy >= 0:
                self.y = block_rect.top - self.height
                self.vy = 0.0
                self.is_on_ground = True
                self.is_jumping = False
            elif min_overlap == overlap_y_from_bottom and self.vy < 0:
                self.y = block_rect.bottom
                self.vy = 0.0
            elif min_overlap == overlap_x_from_left:
                self.x = block_rect.left - self.width
            elif min_overlap == overlap_x_from_right:
                self.x = block_rect.right
    
    def draw(self, surface: pygame.Surface, camera_x: int) -> None:
        if self.damage_invincible_timer > 0 and (pygame.time.get_ticks() // 30) % 2 == 0:
            return
            
        screen_x: int = int(self.x) - camera_x
        screen_y: int = int(self.y)
        
        if self.is_invincible and (pygame.time.get_ticks() // 100) % 2 == 0:
            draw_color = Config.COLOR_GOLD
        else:
            draw_color = self.color

        if self.image_original is not None:
            img = self.image_original
            if not self.facing_right:
                img = pygame.transform.flip(self.image_original, True, False)
            surface.blit(img, (screen_x, screen_y))
        else:
            rect = pygame.Rect(screen_x, screen_y, self.width, self.height)
            pygame.draw.rect(surface, draw_color, rect)
            pygame.draw.rect(surface, Config.COLOR_BLACK, rect, 2)
            eye_offset: int = 8 if self.facing_right else (self.width - 14)
            pygame.draw.circle(surface, Config.COLOR_BLACK, (screen_x + eye_offset, screen_y + 12), 2)
    
    def reset(self) -> None:
        self.x = Config.PLAYER_START_X
        self.y = Config.PLAYER_START_Y
        self.vx = 0.0
        self.vy = 0.0
        self.is_jumping = False
        self.is_on_ground = True
        self.change_state(PlayerState.NORMAL)
        self.is_invincible = False
        self.invincible_timer = 0
        self.damage_invincible_timer = 0
        self.fire_cooldown = 0
        self.pending_fireballs = []


# ==============================================================================
# 4. シーン管理システム (Scene, Title, Game, Clear, GameOver)
# ==============================================================================
class Scene(ABC):
    @abstractmethod
    def handle_input(self, event: pygame.event.EventType) -> None:
        pass
    @abstractmethod
    def update(self) -> Optional[SceneType]:
        pass
    @abstractmethod
    def draw(self, surface: pygame.Surface) -> None:
        pass

class TitleScene(Scene):
    def __init__(self) -> None:
        self.title_font = pygame.font.Font(None, 80)
        self.instruction_font = pygame.font.Font(None, 40)
    
    def handle_input(self, event: pygame.event.EventType) -> None:
        pass
    
    def update(self) -> Optional[SceneType]:
        keys = pygame.key.get_pressed()
        if keys[pygame.K_RETURN]:
            return SceneType.GAME
        return None
    
    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(Config.COLOR_LIGHT_BLUE)
        title_text = self.title_font.render("FAKE MARIO", True, Config.COLOR_BLACK)
        surface.blit(title_text, title_text.get_rect(center=(Config.SCREEN_WIDTH // 2, 150)))
        
        inst_text = self.instruction_font.render("Press ENTER to Start", True, Config.COLOR_BLACK)
        surface.blit(inst_text, inst_text.get_rect(center=(Config.SCREEN_WIDTH // 2, 350)))
        
        control_font = pygame.font.Font(None, 30)
        controls = ["LEFT/RIGHT: Move", "ENTER/SPACE: Jump", "X: Shoot Fireball", "ESC: Return to Title"]
        for i, control in enumerate(controls):
            text = control_font.render(control, True, Config.COLOR_BLACK)
            surface.blit(text, text.get_rect(center=(Config.SCREEN_WIDTH // 2, 430 + i * 35)))


class GameScene(Scene):
    """ゲーム本編シーン"""
    def __init__(self, sound_player: Optional["SoundPlayer"] = None) -> None:
        """ゲーム本編シーンの初期化"""
        self.sound_player: "SoundPlayer" = sound_player if sound_player is not None else SoundPlayer()
        self.player: Player = Player()
        self.blocks: List[Block] = self._create_stage()
        self.goal: Goal = Goal()
        self.camera_x: int = 0  # カメラの X 座標（ワールド座標）
        self.score: int = 0
        self.font: pygame.font.Font = pygame.font.Font(None, 36)
        self.time_remaining = Config.TIME_LIMIT
        
        self.items = [
            Item(350, 330, ItemType.GROW),
            Item(750, 330, ItemType.INVINCIBLE),
            Item(2150, 330, ItemType.FIRE)
        ]
        self.fireballs: List[Fireball] = []
        self.enemies = [
            Enemy(500, 468),
            Enemy(1200, 200),
            Enemy(2000, 300)
        ]
        self.boss = Boss(3000, 200)

        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            bg_path = os.path.join(current_dir, Config.BACKGROUND_IMAGE_PATH)
            raw_bg = pygame.image.load(bg_path).convert()
            self.background_image = pygame.transform.scale(raw_bg, (Config.SCREEN_WIDTH, Config.SCREEN_HEIGHT))
        except Exception:
            self.background_image = None
            
    def _create_stage(self) -> List[Block]:
        stage_layout: List[BlockConfig] = [
            (0, 500, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "ground"),
            (64, 500, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "ground"),
            (128, 500, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "ground"),
            (192, 500, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "ground"),
            (256, 500, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "ground"),
            (320, 500, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "ground"),
            (384, 500, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "ground"),
            (448, 500, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "ground"),
            (512, 500, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "ground"),
            (576, 500, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "ground"),
            (640, 500, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "ground"),
            (704, 500, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "ground"),
            (768, 500, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "ground"),
            (832, 500, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "ground"),
            (896, 500, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "ground"),
            (960, 500, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "ground"),
            (1024, 500, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "ground"),
            (1088, 500, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "ground"),
            (1152, 500, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "ground"),
            
            (960, 436, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "step"),
            (1024, 372, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "step"),
            (1024, 436, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "step"),
            (1088, 436, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "step"),
            (1088, 372, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "step"),
            (1088, 308, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "step"),
            (1152, 436, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "step"),
            (1152, 372, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "step"),
            (1152, 308, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "step"),
            (1152, 244, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "step"),

            (1408, 436, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "step"),
            (1408, 372, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "step"),
            (1408, 308, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "step"),
            (1408, 244, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "step"),
            (1472, 436, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "step"),
            (1472, 372, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "step"),
            (1472, 308, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "step"),
            (1536, 436, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "step"),
            (1536, 372, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "step"),
            (1600, 436, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "step"),

            (1408, 500, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "ground"),
            (1472, 500, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "ground"),
            (1536, 500, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "ground"),
            (1600, 500, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "ground"),
            (1664, 500, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "ground"),
            (1728, 500, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "ground"),
            (1792, 500, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "ground"),
            (1856, 500, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "ground"),
            (1920, 500, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "ground"),

            (2176, 500, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "ground"),
            (2240, 500, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "ground"),
            (2304, 500, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "ground"),
            (2368, 500, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "ground"),
            (2432, 500, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "ground"),
            (2496, 500, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "ground"),
            (2560, 500, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "ground"),
            (2624, 500, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "ground"),
            (2688, 500, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "ground"),
            (2752, 500, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "ground"),
            (2816, 500, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "ground"),
            (2880, 500, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "ground"),
            (2944, 500, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "ground"),
            (3008, 500, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "ground"),
            (3072, 500, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "ground"),
            (3136, 500, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "ground"),
            (3200, 500, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "ground"),
            (3264, 500, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "ground"),

            (384, 350, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "platform"),
            (448, 350, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "platform"),
            (512, 350, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "platform"),
            (576, 350, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "platform"),
            (640, 350, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "platform"),
            (512, 200, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "platform"),

            (2368, 436, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "step"),
            (2432, 436, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "step"),
            (2432, 372, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "step"),
            (2496, 436, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "step"),
            (2496, 372, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "step"),
            (2496, 308, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "step"),
            (2560, 436, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "step"),
            (2560, 372, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "step"),
            (2560, 308, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "step"),
            (2560, 244, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "step"),
            (2624, 436, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "step"),
            (2624, 372, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "step"),
            (2624, 308, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "step"),
            (2624, 244, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "step"),
            (2624, 180, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "step"),
            (2688, 436, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "step"),
            (2688, 372, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "step"),
            (2688, 308, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "step"),
            (2688, 244, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "step"),
            (2688, 180, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "step"),
            (2688, 116, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "step"),
        ]
        return [Block(x, y, w, h, kind=k) for x, y, w, h, k in stage_layout]
    
    def handle_input(self, event: pygame.event.EventType) -> None:
        pass
    
    def update(self) -> Optional[SceneType]:
        """
        ゲーム状態の更新
        
        Returns:
            ゴール到達ならゲームクリアシーンに切り替え、
            ゲームオーバーならゲームオーバーシーンに切り替え、
            ESCキーでタイトルシーンに切り替え
        """
        # キー入力を処理
        keys = pygame.key.get_pressed()
        jumped = self.player.handle_input(keys)
        if jumped:
            self.sound_player.play_jump()
        
        if keys[pygame.K_ESCAPE]:
            return SceneType.TITLE
        
        self.player.update(self.blocks)
        
        if self.player.pending_fireballs:
            self.fireballs.extend(self.player.pending_fireballs)
            self.player.pending_fireballs.clear()
            
        for fireball in self.fireballs[:]:
            fireball.update(self.blocks)
            if not fireball.is_alive:
                self.fireballs.remove(fireball)
                
        # 火の玉と敵の衝突判定
        for fireball in self.fireballs[:]:
            for enemy in self.enemies[:]:
                if fireball.get_rect().colliderect(enemy.get_rect()):
                    fireball.is_alive = False
                    enemy.is_alive = False
                    if fireball in self.fireballs: self.fireballs.remove(fireball)
                    if enemy in self.enemies: self.enemies.remove(enemy)
                    self.score += 100
                    break
            if self.boss and fireball.is_alive and fireball.get_rect().colliderect(self.boss.get_rect()):
                fireball.is_alive = False
                if fireball in self.fireballs: self.fireballs.remove(fireball)
                if self.boss.take_damage():
                    self.boss = None
                    self.score += 1000

        # 敵の更新とプレイヤー衝突判定
        player_rect = self.player.get_rect()
        for enemy in self.enemies[:]:
            enemy.update(self.blocks)
            if enemy.x + enemy.width < self.camera_x or not enemy.is_alive:
                if enemy in self.enemies: self.enemies.remove(enemy)
                continue
                
            if player_rect.colliderect(enemy.get_rect()):
                if self.player.is_invincible:
                    self.enemies.remove(enemy)
                    self.score += 100
                elif self.player.vy > 0 and (player_rect.bottom - enemy.get_rect().top) < 20:
                    self.enemies.remove(enemy)
                    self.player.vy = -8.0
                    self.score += 100
                else:
                    if self.player.hit_enemy() == SceneType.GAME_OVER:
                        return SceneType.GAME_OVER

        # ボスの更新と衝突判定
        if self.boss:
            self.boss.update(self.blocks)
            if player_rect.colliderect(self.boss.get_rect()):
                if self.player.is_invincible:
                    if self.boss.take_damage():
                        self.boss = None
                        self.score += 1000
                elif self.player.vy > 0 and (player_rect.bottom - self.boss.get_rect().top) < 20:
                    self.player.vy = -Config.PLAYER_JUMP_POWER * 1.0
                    if self.boss.take_damage():
                        self.boss = None
                        self.score += 1000
                else:
                    if self.player.hit_enemy() == SceneType.GAME_OVER:
                        return SceneType.GAME_OVER

        # アイテムとの衝突判定
        for item in self.items[:]:
            if player_rect.colliderect(item.get_rect()):
                if item.item_type == ItemType.GROW:
                    self.player.change_state(PlayerState.BIG)
                elif item.item_type == ItemType.INVINCIBLE:
                    self.player.is_invincible = True
                    self.player.invincible_timer = 300
                elif item.item_type == ItemType.FIRE:
                    self.player.change_state(PlayerState.FIRE)
                
                self.items.remove(item)
                self.score += 200
        
        self._update_camera()
        
        if self.goal.check_collision(self.player.get_rect()):
            return SceneType.GAME_CLEAR
        
        if self.player.y > Config.SCREEN_HEIGHT + 100:
            self.sound_player.play_death()
            pygame.time.wait(1500)
            return SceneType.GAME_OVER

        self.time_remaining -= 1 / Config.FPS
        if self.time_remaining <= 0:
            return SceneType.GAME_OVER
            
        return None

    def _update_camera(self) -> None:
        target_camera_x = int(self.player.x) - Config.SCREEN_WIDTH // 4
        max_camera_x = Config.STAGE_MAX_X - Config.SCREEN_WIDTH
        
        if target_camera_x < 0:
            self.camera_x = 0
        elif target_camera_x > max_camera_x:
            self.camera_x = max_camera_x
        else:
            self.camera_x = target_camera_x
    
    def draw(self, surface: pygame.Surface) -> None:
        if self.background_image is not None:
            surface.blit(self.background_image, (0, 0))
        else:
            surface.fill(Config.BACKGROUND_COLOR)
            
        for block in self.blocks: block.draw(surface, self.camera_x)
        for item in self.items: item.draw(surface, self.camera_x)
        for fireball in self.fireballs: fireball.draw(surface, self.camera_x)
        for enemy in self.enemies: enemy.draw(surface, self.camera_x)
        self.goal.draw(surface, self.camera_x)
        
        if self.boss is not None:
            self.boss.draw(surface, self.camera_x)
            boss_screen_x = int(self.boss.x) - self.camera_x
            hp_text = self.font.render("HP: " + "★" * self.boss.hp, True, Config.COLOR_RED)
            surface.blit(hp_text, (boss_screen_x, int(self.boss.y) - 30))
        
        self.player.draw(surface, self.camera_x)
        
        state_str = self.player.state.name
        if self.player.is_invincible:
            state_str += " + INVINCIBLE"
        score_text = self.font.render(f"Score: {self.score} | TIME: {int(self.time_remaining)} | X: {int(self.player.x)} | {state_str}", True, Config.COLOR_BLACK)
        surface.blit(score_text, (10, 10))
        
        hint_font = pygame.font.Font(None, 20)
        hint_text = hint_font.render("ESC: Back to Title", True, Config.COLOR_BLACK)
        surface.blit(hint_text, (Config.SCREEN_WIDTH - 150, 10))


class GameClearScene(Scene):
    def __init__(self) -> None:
        self.title_font = pygame.font.Font(None, 80)
        self.instruction_font = pygame.font.Font(None, 40)
    def handle_input(self, event: pygame.event.EventType) -> None: pass
    def update(self) -> Optional[SceneType]:
        if pygame.key.get_pressed()[pygame.K_SPACE]: return SceneType.TITLE
        return None
    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(Config.COLOR_LIGHT_BLUE)
        c_txt = self.title_font.render("GAME CLEAR!", True, Config.COLOR_GREEN)
        surface.blit(c_txt, c_txt.get_rect(center=(Config.SCREEN_WIDTH // 2, 150)))
        i_txt = self.instruction_font.render("Press SPACE to Back to Title", True, Config.COLOR_BLACK)
        surface.blit(i_txt, i_txt.get_rect(center=(Config.SCREEN_WIDTH // 2, 450)))


class GameOverScene(Scene):
    def __init__(self) -> None:
        self.title_font = pygame.font.Font(None, 80)
        self.instruction_font = pygame.font.Font(None, 40)
    def handle_input(self, event: pygame.event.EventType) -> None: pass
    def update(self) -> Optional[SceneType]:
        keys = pygame.key.get_pressed()
        if keys[pygame.K_RETURN]: return SceneType.GAME
        elif keys[pygame.K_ESCAPE]: return SceneType.TITLE
        return None
    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(Config.COLOR_BLACK)
        go_txt = self.title_font.render("GAME OVER", True, Config.COLOR_RED)
        surface.blit(go_txt, go_txt.get_rect(center=(Config.SCREEN_WIDTH // 2, 200)))
        i_txt = self.instruction_font.render("Press ENTER to Retry", True, Config.COLOR_WHITE)
        surface.blit(i_txt, i_txt.get_rect(center=(Config.SCREEN_WIDTH // 2, 350)))
        b_txt = self.instruction_font.render("Press ESC to Back to Title", True, Config.COLOR_WHITE)
        surface.blit(b_txt, b_txt.get_rect(center=(Config.SCREEN_WIDTH // 2, 450)))


# ==============================================================================
# 5. 音声・ゲームメインクラス (Audio & Main Game Loop)
# ==============================================================================
class MusicPlayer:
    """アップロードされたSeven_Bells_Ringing.mp3を再生するクラス"""
    def __init__(self, filepath: str = "Seven_Bells_Ringing.mp3"):
        self.filepath = filepath
        self.playing = False

    @property
    def resolved_path(self) -> str:
        """音声ファイルのパスをスクリプトの位置基準で解決する"""
        if os.path.isabs(self.filepath):
            return self.filepath
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), self.filepath)

    def play(self):
        """BGMをループ再生する"""
        try:
            if not self.playing:
                pygame.mixer.music.load(self.resolved_path)
                pygame.mixer.music.play(-1)  # -1で無限ループ
                self.playing = True
        except pygame.error as e:
            # print(f"BGMの読み込みに失敗しました: {e}")
            pass

    def stop(self):
        """BGMを停止する"""
        if self.playing:
            pygame.mixer.music.stop()
            self.playing = False


class SoundPlayer:
    def __init__(self, filepath_map: Optional[dict[str, str]] = None) -> None:
        if not pygame.mixer.get_init():
            pygame.mixer.init()

        pygame.mixer.set_num_channels(16)

        self.filepath_map: dict[str, str] = filepath_map or {
            "jump": "和太鼓でドン.wav",      
            "death": "ちゃんちゃん_1.wav", 
            "fire": "ボヨン.wav",           
            "enemy": "会心の一撃2.wav",    
            "star": "シャキーン1.wav",     
        }
        self.sounds: dict[str, pygame.mixer.Sound] = {}

        for name, filename in self.filepath_map.items():
            resolved = self._resolve_path(filename)
            if not os.path.exists(resolved):
                # print(f"効果音ファイルが見つかりません: {resolved}")
                continue

            try:
                self.sounds[name] = pygame.mixer.Sound(resolved)
            except pygame.error as e:
                # print(f"{name}の読み込みに失敗しました: {e}")
                pass

    def _resolve_path(self, filepath: str) -> str:
        """効果音ファイルのパスをスクリプトの位置基準で解決する"""
        if os.path.isabs(filepath):
            return filepath
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), filepath)

    def play(self, sound_name: str) -> None:
        """指定した効果音を再生する"""
        sound = self.sounds.get(sound_name)
        if sound is None:
            return

        try:
            sound.set_volume(1.0)
            channel = sound.play()
            if channel is not None:
                channel.set_volume(1.0)
        except pygame.error as e:
            pass

    def play_jump(self) -> None:
        self.play("jump")

    def play_death(self) -> None:
        self.play("death")

    def play_fire(self) -> None:
        self.play("fire")

    def play_enemy(self) -> None:
        self.play("enemy")

    def play_star(self) -> None:
        self.play("star")


class Game:
    """
    ゲーム全体を管理するメインクラス
    """
    
    def __init__(self) -> None:
        """ゲームの初期化"""
        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.init()
        pygame.mixer.init()

        self.sound_player = SoundPlayer()

        # BGMプレイヤーのインスタンス作成
        self.music_player = MusicPlayer("Seven_Bells_Ringing.mp3")
        self.music_player.play()
        
        self.surface: pygame.Surface = pygame.display.set_mode(
            (Config.SCREEN_WIDTH, Config.SCREEN_HEIGHT))
        pygame.display.set_caption("Fake Mario - 2D Platformer")
        
        self.clock: pygame.time.Clock = pygame.time.Clock()
        
        self.current_scene_type: SceneType = SceneType.TITLE
        self.scenes: dict = {
            SceneType.TITLE: TitleScene(),
            SceneType.GAME: GameScene(self.sound_player),
            SceneType.GAME_OVER: GameOverScene(),
            SceneType.GAME_CLEAR: GameClearScene()
        }
        self.running = True
    
    def get_current_scene(self) -> Scene:
        return self.scenes[self.current_scene_type]
    
    def handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            else:
                self.get_current_scene().handle_input(event)
    
    def update(self) -> None:
        current_scene = self.get_current_scene()
        next_scene_type = current_scene.update()
        
        if next_scene_type is not None:
            self.current_scene_type = next_scene_type
            
            # シーン切り替え時に新しいインスタンスを作成（状態をリセット）
            if self.current_scene_type == SceneType.GAME:
                self.scenes[SceneType.GAME] = GameScene(self.sound_player)
            elif self.current_scene_type == SceneType.GAME_OVER:
                self.scenes[SceneType.GAME_OVER] = GameOverScene()
            elif self.current_scene_type == SceneType.GAME_CLEAR:
                self.scenes[SceneType.GAME_CLEAR] = GameClearScene()
    
    def draw(self) -> None:
        self.get_current_scene().draw(self.surface)
        pygame.display.flip()
    
    def run(self) -> None:
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(Config.FPS)
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()