import pygame
import sys
from typing import Tuple, List, Optional, Sequence
from enum import Enum
from abc import ABC, abstractmethod


# ================== 定数・グローバル設定 ==================

class Config:
    """ゲーム全体の設定値を管理するクラス"""
    
    # 画面設定
    SCREEN_WIDTH: int = 800
    SCREEN_HEIGHT: int = 600
    FPS: int = 60
    
    # 色定義（RGB）
    COLOR_BLACK: Tuple[int, int, int] = (0, 0, 0)
    COLOR_WHITE: Tuple[int, int, int] = (255, 255, 255)
    COLOR_BLUE: Tuple[int, int, int] = (0, 100, 255)
    COLOR_GREEN: Tuple[int, int, int] = (0, 200, 0)
    COLOR_RED: Tuple[int, int, int] = (255, 0, 0)
    COLOR_GRAY: Tuple[int, int, int] = (128, 128, 128)
    COLOR_LIGHT_BLUE: Tuple[int, int, int] = (135, 206, 235)
    COLOR_GOLD: Tuple[int, int, int] = (255, 215, 0)
    COLOR_YELLOW: Tuple[int, int, int] = (255, 255, 0)
    COLOR_DARK_YELLOW: Tuple[int, int, int] = (200, 200, 0)
    
    # プレイヤー設定
    PLAYER_WIDTH: int = 32
    PLAYER_HEIGHT: int = 48
    PLAYER_START_X: int = 100
    PLAYER_START_Y: int = 400
    PLAYER_MOVE_SPEED: int = 5
    PLAYER_JUMP_POWER: int = 15
    
    # 重力設定
    GRAVITY: float = 0.6
    MAX_FALL_SPEED: int = 20
    
    # ブロック設定
    BLOCK_WIDTH: int = 64
    BLOCK_HEIGHT: int = 64
    
    # ゴール設定
    GOAL_WIDTH: int = 50
    GOAL_HEIGHT: int = 80
    GOAL_X: int = 3000  # ゴールのX座標（ワールド座標）
    GOAL_Y: int = 350   # ゴールのY座標（ワールド座標）
    
    # ステージ設定
    STAGE_MAX_X: int = 3100  # ステージの最大X座標


class SceneType(Enum):
    """シーンの種類を定義する列挙型"""
    TITLE = 1
    GAME = 2
    GAME_OVER = 3
    GAME_CLEAR = 4


class ItemType(Enum):
    """アイテムの種類を定義する列挙型"""
    GROW = 1        # 体が大きくなる（キノコ風）
    INVINCIBLE = 2  # 無敵状態（スター風）
    FIRE = 3        # 火の玉を出せる状態（フラワー風）


class PlayerState(Enum):
    """プレイヤーの状態を定義する列挙型"""
    NORMAL = 1
    BIG = 2
    FIRE = 3


# ================== ブロッククラス ==================

class Block:
    """ステージの床や足場を表すクラス"""
    
    def __init__(self, x: int, y: int, width: int = Config.BLOCK_WIDTH,
                 height: int = Config.BLOCK_HEIGHT, color: Tuple[int, int, int] = Config.COLOR_GREEN) -> None:
        self.x: int = x
        self.y: int = y
        self.width: int = width
        self.height: int = height
        self.color: Tuple[int, int, int] = color
    
    def get_rect(self) -> pygame.Rect:
        return pygame.Rect(self.x, self.y, self.width, self.height)
    
    def draw(self, surface: pygame.Surface, camera_x: int) -> None:
        screen_x: int = self.x - camera_x
        if screen_x + self.width < 0 or screen_x > Config.SCREEN_WIDTH:
            return
        
        rect: pygame.Rect = pygame.Rect(screen_x, self.y, self.width, self.height)
        pygame.draw.rect(surface, self.color, rect)
        pygame.draw.rect(surface, Config.COLOR_BLACK, rect, 2)


# ================== ゴールクラス ==================

class Goal:
    """ステージのゴール（ゴール地点）を表すクラス"""
    
    def __init__(self, x: int = Config.GOAL_X, y: int = Config.GOAL_Y,
                 width: int = Config.GOAL_WIDTH, height: int = Config.GOAL_HEIGHT) -> None:
        self.x: int = x
        self.y: int = y
        self.width: int = width
        self.height: int = height
        self.color: Tuple[int, int, int] = Config.COLOR_GOLD
    
    def get_rect(self) -> pygame.Rect:
        return pygame.Rect(self.x, self.y, self.width, self.height)
    
    def check_collision(self, player_rect: pygame.Rect) -> bool:
        return player_rect.colliderect(self.get_rect())
    
    def draw(self, surface: pygame.Surface, camera_x: int) -> None:
        screen_x: int = self.x - camera_x
        if screen_x + self.width < 0 or screen_x > Config.SCREEN_WIDTH:
            return
        
        goal_rect: pygame.Rect = pygame.Rect(screen_x, self.y, self.width, self.height)
        pygame.draw.rect(surface, self.color, goal_rect)
        pygame.draw.rect(surface, Config.COLOR_BLACK, goal_rect, 3)
        
        center_x: int = screen_x + self.width // 2
        center_y: int = self.y + self.height // 2
        pygame.draw.polygon(surface, Config.COLOR_YELLOW, [
            (center_x, center_y - 8), (center_x + 4, center_y - 2),
            (center_x + 8, center_y), (center_x + 4, center_y + 4),
            (center_x + 6, center_y + 8), (center_x, center_y + 5),
            (center_x - 6, center_y + 8), (center_x - 4, center_y + 4),
            (center_x - 8, center_y), (center_x - 4, center_y - 2)
        ])


# ================== 火の玉クラス（新規追加） ==================

class Fireball:
    """ファイア状態のプレイヤーが放つ火の玉クラス"""
    
    def __init__(self, x: float, y: float, facing_right: bool) -> None:
        self.x: float = x
        self.y: float = y
        self.width: int = 16
        self.height: int = 16
        self.vx: float = 8.0 if facing_right else -8.0
        self.vy: float = 0.0
        self.color: Tuple[int, int, int] = (255, 69, 0)  # 赤オレンジ
        self.is_alive: bool = True

    def get_rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), self.width, self.height)

    def update(self, blocks: List[Block]) -> None:
        # 重力適用
        self.vy += Config.GRAVITY
        if self.vy > Config.MAX_FALL_SPEED:
            self.vy = Config.MAX_FALL_SPEED

        self.x += self.vx
        self.y += self.vy

        fire_rect = self.get_rect()
        
        # ブロックとの当たり判定（床ならバウンド、壁なら消滅）
        for block in blocks:
            block_rect = block.get_rect()
            if fire_rect.colliderect(block_rect):
                overlap_y_from_top = fire_rect.bottom - block_rect.top
                overlap_x_from_left = fire_rect.right - block_rect.left
                overlap_x_from_right = block_rect.right - fire_rect.left
                
                min_overlap = min(overlap_y_from_top, overlap_x_from_left, overlap_x_from_right)
                
                if min_overlap == overlap_y_from_top:
                    self.y = block_rect.top - self.height
                    self.vy = -6.0  # 上に弾む
                else:
                    self.is_alive = False  # 壁に当たったら消える
                    return

        # 画面外またはステージ外に出たら消滅
        if self.y > Config.SCREEN_HEIGHT or self.x < 0 or self.x > Config.STAGE_MAX_X:
            self.is_alive = False

    def draw(self, surface: pygame.Surface, camera_x: int) -> None:
        screen_x: int = int(self.x) - camera_x
        if screen_x + self.width < 0 or screen_x > Config.SCREEN_WIDTH:
            return
        rect: pygame.Rect = pygame.Rect(screen_x, int(self.y), self.width, self.height)
        pygame.draw.ellipse(surface, self.color, rect)
        pygame.draw.ellipse(surface, Config.COLOR_BLACK, rect, 1)


# ================== アイテムクラス（新規追加） ==================

class Item:
    """ステージ上に配置されるアイテムクラス"""
    
    def __init__(self, x: int, y: int, item_type: ItemType) -> None:
        self.x: int = x
        self.y: int = y
        self.width: int = 32
        self.height: int = 32
        self.item_type: ItemType = item_type
        
        # アイテムの種類に応じた色設定
        if self.item_type == ItemType.GROW:
            self.color: Tuple[int, int, int] = (255, 100, 100)   # 赤（キノコ風）
        elif self.item_type == ItemType.INVINCIBLE:
            self.color: Tuple[int, int, int] = Config.COLOR_GOLD # 金（スター風）
        elif self.item_type == ItemType.FIRE:
            self.color: Tuple[int, int, int] = (255, 140, 0)     # オレンジ（フラワー風）

    def get_rect(self) -> pygame.Rect:
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def draw(self, surface: pygame.Surface, camera_x: int) -> None:
        screen_x: int = self.x - camera_x
        if screen_x + self.width < 0 or screen_x > Config.SCREEN_WIDTH:
            return

        rect: pygame.Rect = pygame.Rect(screen_x, self.y, self.width, self.height)
        pygame.draw.rect(surface, self.color, rect)
        pygame.draw.rect(surface, Config.COLOR_BLACK, rect, 2)
        
        # 内側の簡易模様
        inner: pygame.Rect = pygame.Rect(screen_x + 8, self.y + 8, self.width - 16, self.height - 16)
        pygame.draw.rect(surface, Config.COLOR_WHITE, inner, 1)


# ================== プレイヤークラス ==================

class Player:
    """プレイヤーキャラクターを表すクラス"""
    
    def __init__(self, x: int = Config.PLAYER_START_X,
                 y: int = Config.PLAYER_START_Y,
                 width: int = Config.PLAYER_WIDTH,
                 height: int = Config.PLAYER_HEIGHT) -> None:
        self.x: float = x
        self.y: float = y
        self.width: int = width
        self.height: int = height
        
        # 速度
        self.vx: float = 0.0
        self.vy: float = 0.0
        
        # 状態
        self.is_jumping: bool = False
        self.is_on_ground: bool = True
        self.color: Tuple[int, int, int] = Config.COLOR_BLUE
        self.facing_right: bool = True
        
        # アイテムによる拡張状態
        self.state: PlayerState = PlayerState.NORMAL
        self.is_invincible: bool = False
        self.invincible_timer: int = 0
        self.fire_cooldown: int = 0
        self.pending_fireballs: List[Fireball] = []  # 生成された火の玉の一時保管用
    
    def get_rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), self.width, self.height)
    
    def change_state(self, new_state: PlayerState) -> None:
        """プレイヤーの状態（サイズ・カラー）を変更する"""
        old_height = self.height
        self.state = new_state
        
        if self.state == PlayerState.NORMAL:
            self.height = Config.PLAYER_HEIGHT
            self.color = Config.COLOR_BLUE
        elif self.state == PlayerState.BIG:
            self.height = int(Config.PLAYER_HEIGHT * 1.4)  # 1.4倍の大きさに変更
            self.color = (0, 150, 255)
        elif self.state == PlayerState.FIRE:
            self.height = int(Config.PLAYER_HEIGHT * 1.4)
            self.color = Config.COLOR_RED  # ファイア状態は赤色化
            
        # サイズ変更時に地面に埋まったり浮いたりするのを防ぐ調整
        self.y -= (self.height - old_height)

    def handle_input(self, keys: pygame.key.ScancodeWrapper) -> None:
        # 左右の移動処理
        if keys[pygame.K_LEFT]:
            self.vx = -Config.PLAYER_MOVE_SPEED
            self.facing_right = False
        elif keys[pygame.K_RIGHT]:
            self.vx = Config.PLAYER_MOVE_SPEED
            self.facing_right = True
        else:
            self.vx = 0.0
        
        # ジャンプ処理
        if keys[pygame.K_SPACE] and self.is_on_ground:
            self.vy = -Config.PLAYER_JUMP_POWER
            self.is_jumping = True
            self.is_on_ground = False
            
        # 火の玉発射処理（FIRE状態かつXキー入力かつクールダウン終了時）
        if keys[pygame.K_x] and self.state == PlayerState.FIRE and self.fire_cooldown == 0:
            fx = self.x + self.width if self.facing_right else self.x - 16
            fy = self.y + self.height // 3
            self.pending_fireballs.append(Fireball(fx, fy, self.facing_right))
            self.fire_cooldown = 15  # 次の発射まで15フレーム制限
    
    def apply_gravity(self) -> None:
        self.vy += Config.GRAVITY
        if self.vy > Config.MAX_FALL_SPEED:
            self.vy = Config.MAX_FALL_SPEED
    
    def update(self, blocks: List[Block]) -> None:
        # 各種タイマーの更新
        if self.fire_cooldown > 0:
            self.fire_cooldown -= 1
        if self.is_invincible:
            self.invincible_timer -= 1
            if self.invincible_timer <= 0:
                self.is_invincible = False

        self.apply_gravity()
        
        self.x += self.vx
        self.y += self.vy
        
        self.is_on_ground = False
        self._check_block_collisions(blocks)
        
        if self.y > Config.SCREEN_HEIGHT + 100:
            self.reset()
    
    def _check_block_collisions(self, blocks: List[Block]) -> None:
        player_rect: pygame.Rect = self.get_rect()
        
        for block in blocks:
            block_rect: pygame.Rect = block.get_rect()
            if not player_rect.colliderect(block_rect):
                continue
            
            overlap_y_from_top: int = player_rect.bottom - block_rect.top
            overlap_y_from_bottom: int = block_rect.bottom - player_rect.top
            overlap_x_from_left: int = player_rect.right - block_rect.left
            overlap_x_from_right: int = block_rect.right - player_rect.left
            
            min_overlap: int = min(overlap_y_from_top, overlap_y_from_bottom,
                                   overlap_x_from_left, overlap_x_from_right)
            
            if min_overlap == overlap_y_from_top:
                self.y = block_rect.top - self.height
                self.vy = 0.0
                self.is_on_ground = True
                self.is_jumping = False
            elif min_overlap == overlap_y_from_bottom:
                self.y = block_rect.bottom
                self.vy = 0.0
            elif min_overlap == overlap_x_from_left:
                self.x = block_rect.left - self.width
            elif min_overlap == overlap_x_from_right:
                self.x = block_rect.right
    
    def draw(self, surface: pygame.Surface, camera_x: int) -> None:
        screen_x: int = int(self.x) - camera_x
        screen_y: int = int(self.y)
        
        # 無敵状態時はゴールドに点滅させる演出
        if self.is_invincible and (pygame.time.get_ticks() // 100) % 2 == 0:
            draw_color = Config.COLOR_GOLD
        else:
            draw_color = self.color
        
        rect: pygame.Rect = pygame.Rect(screen_x, screen_y, self.width, self.height)
        pygame.draw.rect(surface, draw_color, rect)
        pygame.draw.rect(surface, Config.COLOR_BLACK, rect, 2)
        
        eye_offset: int = 8 if self.facing_right else (self.width - 14)
        pygame.draw.circle(surface, Config.COLOR_BLACK, 
                           (screen_x + eye_offset, screen_y + 12), 2)
    
    def reset(self) -> None:
        self.x = Config.PLAYER_START_X
        self.y = Config.PLAYER_START_Y
        self.vx = 0.0
        self.vy = 0.0
        self.is_jumping = False
        self.is_on_ground = True
        
        # アイテム状態のリセット
        self.change_state(PlayerState.NORMAL)
        self.is_invincible = False
        self.invincible_timer = 0
        self.fire_cooldown = 0
        self.pending_fireballs = []


# ================== シーン管理 ==================

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
        self.title_font: pygame.font.Font = pygame.font.Font(None, 80)
        self.instruction_font: pygame.font.Font = pygame.font.Font(None, 40)
    
    def handle_input(self, event: pygame.event.EventType) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                return
    
    def update(self) -> Optional[SceneType]:
        keys: pygame.key.ScancodeWrapper = pygame.key.get_pressed()
        if keys[pygame.K_SPACE]:
            return SceneType.GAME
        return None
    
    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(Config.COLOR_LIGHT_BLUE)
        
        title_text: pygame.Surface = self.title_font.render("FAKE MARIO", True, Config.COLOR_BLACK)
        title_rect: pygame.Rect = title_text.get_rect(center=(Config.SCREEN_WIDTH // 2, 150))
        surface.blit(title_text, title_rect)
        
        instruction_text: pygame.Surface = self.instruction_font.render("Press SPACE to Start", True, Config.COLOR_BLACK)
        instruction_rect: pygame.Rect = instruction_text.get_rect(center=(Config.SCREEN_WIDTH // 2, 350))
        surface.blit(instruction_text, instruction_rect)
        
        control_font: pygame.font.Font = pygame.font.Font(None, 30)
        controls: List[str] = [
            "LEFT/RIGHT: Move",
            "SPACE: Jump",
            "X: Shoot Fireball (Fire State)",
            "ESC: Return to Title"
        ]
        for i, control in enumerate(controls):
            control_text: pygame.Surface = control_font.render(control, True, Config.COLOR_BLACK)
            control_rect: pygame.Rect = control_text.get_rect(center=(Config.SCREEN_WIDTH // 2, 430 + i * 35))
            surface.blit(control_text, control_rect)


class GameScene(Scene):
    """ゲーム本編シーン"""
    
    def __init__(self) -> None:
        self.player: Player = Player()
        self.blocks: List[Block] = self._create_stage()
        self.goal: Goal = Goal()
        self.camera_x: int = 0
        self.score: int = 0
        self.font: pygame.font.Font = pygame.font.Font(None, 36)
        
        # アイテムと火の玉の管理リスト
        self.items: List[Item] = self._create_items()
        self.fireballs: List[Fireball] = []
    
    def _create_items(self) -> List[Item]:
        """ステージ上に各種アイテムを配置"""
        items: List[Item] = []
        # 第1セクションの足場の上（大きくなるアイテム）
        items.append(Item(350, 330, ItemType.GROW))
        # 第2セクションの浮き足場の上（無敵アイテム）
        items.append(Item(750, 330, ItemType.INVINCIBLE))
        # 第4セクションの複雑な足場（ファイアアイテム）
        items.append(Item(2150, 250, ItemType.FIRE))
        return items

    def _create_stage(self) -> List[Block]:
        blocks: List[Block] = []
        # 第1セクション：初期エリア
        for i in range(7):
            blocks.append(Block(i * Config.BLOCK_WIDTH, 500))
        blocks.append(Block(300, 420))
        blocks.append(Block(350, 380))
        blocks.append(Block(400, 340))
        
        # 第2セクション：中盤エリア
        for i in range(7, 15):
            blocks.append(Block(i * Config.BLOCK_WIDTH, 500))
        for i in range(6):
            if i % 2 == 0:
                blocks.append(Block(450 + i * 100, 380))
        for i in range(4):
            blocks.append(Block(850 + i * Config.BLOCK_WIDTH, 450 - i * Config.BLOCK_HEIGHT))
        
        # 第3セクション
        blocks.append(Block(1100, 350))
        blocks.append(Block(1200, 350))
        blocks.append(Block(1300, 300))
        blocks.append(Block(1400, 300))
        blocks.append(Block(1500, 250))
        blocks.append(Block(1600, 250))
        for i in range(3):
            blocks.append(Block(1700 + i * Config.BLOCK_WIDTH, 450 + i * Config.BLOCK_HEIGHT // 2))
        
        # 第4セクション
        for i in range(20, 27):
            blocks.append(Block(i * Config.BLOCK_WIDTH, 500))
        blocks.append(Block(2000, 400))
        blocks.append(Block(2100, 350))
        blocks.append(Block(2150, 350))
        blocks.append(Block(2200, 300))
        blocks.append(Block(2250, 300))
        blocks.append(Block(2300, 350))
        blocks.append(Block(2350, 350))
        blocks.append(Block(2400, 400))
        
        # 第5セクション
        for i in range(27, 35):
            blocks.append(Block(i * Config.BLOCK_WIDTH, 500))
        blocks.append(Block(2600, 420))
        blocks.append(Block(2700, 380))
        blocks.append(Block(2800, 350))
        blocks.append(Block(2900, 350))
        
        return blocks
    
    def handle_input(self, event: pygame.event.EventType) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return
    
    def update(self) -> Optional[SceneType]:
        keys: pygame.key.ScancodeWrapper = pygame.key.get_pressed()
        self.player.handle_input(keys)
        
        if keys[pygame.K_ESCAPE]:
            return SceneType.TITLE
        
        self.player.update(self.blocks)
        
        # プレイヤー側で生成された火の玉をGameScene側で引き取って管理する
        if self.player.pending_fireballs:
            self.fireballs.extend(self.player.pending_fireballs)
            self.player.pending_fireballs.clear()
            
        # 火の玉の更新と削除処理
        for fireball in self.fireballs[:]:
            fireball.update(self.blocks)
            if not fireball.is_alive:
                self.fireballs.remove(fireball)
                
        # プレイヤーとアイテムの衝突（取得）判定
        player_rect = self.player.get_rect()
        for item in self.items[:]:
            if player_rect.colliderect(item.get_rect()):
                if item.item_type == ItemType.GROW:
                    self.player.change_state(PlayerState.BIG)
                elif item.item_type == ItemType.INVINCIBLE:
                    self.player.is_invincible = True
                    self.player.invincible_timer = 300  # 5秒間無敵効果
                elif item.item_type == ItemType.FIRE:
                    self.player.change_state(PlayerState.FIRE)
                
                self.items.remove(item)
                self.score += 200  # アイテム取得スコア
        
        self._update_camera()
        
        if self.goal.check_collision(self.player.get_rect()):
            return SceneType.GAME_CLEAR
        
        if self.player.y > Config.SCREEN_HEIGHT + 100:
            return SceneType.GAME_OVER
        
        return None
    
    def _update_camera(self) -> None:
        target_camera_x: int = int(self.player.x) - Config.SCREEN_WIDTH // 4
        max_camera_x: int = Config.STAGE_MAX_X - Config.SCREEN_WIDTH
        
        if target_camera_x < 0:
            self.camera_x = 0
        elif target_camera_x > max_camera_x:
            self.camera_x = max_camera_x
        else:
            self.camera_x = target_camera_x
    
    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(Config.COLOR_LIGHT_BLUE)
        
        # ブロック描画
        for block in self.blocks:
            block.draw(surface, self.camera_x)
            
        # アイテム描画
        for item in self.items:
            item.draw(surface, self.camera_x)
            
        # 火の玉描画
        for fireball in self.fireballs:
            fireball.draw(surface, self.camera_x)
        
        # ゴール・プレイヤー描画
        self.goal.draw(surface, self.camera_x)
        self.player.draw(surface, self.camera_x)
        
        # ステータス情報の描画
        state_str = self.player.state.name
        if self.player.is_invincible:
            state_str += " + INVINCIBLE"
        score_text: pygame.Surface = self.font.render(
            f"Score: {self.score} | X: {int(self.player.x)} | Status: {state_str}", True, Config.COLOR_BLACK)
        surface.blit(score_text, (10, 10))
        
        hint_font: pygame.font.Font = pygame.font.Font(None, 20)
        hint_text: pygame.Surface = hint_font.render("ESC: Back to Title", True, Config.COLOR_BLACK)
        surface.blit(hint_text, (Config.SCREEN_WIDTH - 150, 10))


class GameClearScene(Scene):
    def __init__(self) -> None:
        self.title_font: pygame.font.Font = pygame.font.Font(None, 80)
        self.instruction_font: pygame.font.Font = pygame.font.Font(None, 40)
    
    def handle_input(self, event: pygame.event.EventType) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                return
    
    def update(self) -> Optional[SceneType]:
        keys: pygame.key.ScancodeWrapper = pygame.key.get_pressed()
        if keys[pygame.K_SPACE]:
            return SceneType.TITLE
        return None
    
    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(Config.COLOR_LIGHT_BLUE)
        
        clear_text: pygame.Surface = self.title_font.render("GAME CLEAR!", True, Config.COLOR_GREEN)
        clear_rect: pygame.Rect = clear_text.get_rect(center=(Config.SCREEN_WIDTH // 2, 150))
        surface.blit(clear_text, clear_rect)
        
        instruction_text: pygame.Surface = self.instruction_font.render("Congratulations!", True, Config.COLOR_BLACK)
        instruction_rect: pygame.Rect = instruction_text.get_rect(center=(Config.SCREEN_WIDTH // 2, 300))
        surface.blit(instruction_text, instruction_rect)
        
        continue_text: pygame.Surface = self.instruction_font.render("Press SPACE to Back to Title", True, Config.COLOR_BLACK)
        continue_rect: pygame.Rect = continue_text.get_rect(center=(Config.SCREEN_WIDTH // 2, 450))
        surface.blit(continue_text, continue_rect)


class GameOverScene(Scene):
    def __init__(self) -> None:
        self.title_font: pygame.font.Font = pygame.font.Font(None, 80)
        self.instruction_font: pygame.font.Font = pygame.font.Font(None, 40)
    
    def handle_input(self, event: pygame.event.EventType) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE or event.key == pygame.K_ESCAPE:
                return
    
    def update(self) -> Optional[SceneType]:
        keys: pygame.key.ScancodeWrapper = pygame.key.get_pressed()
        if keys[pygame.K_SPACE]:
            return SceneType.GAME
        elif keys[pygame.K_ESCAPE]:
            return SceneType.TITLE
        return None
    
    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(Config.COLOR_BLACK)
        
        game_over_text: pygame.Surface = self.title_font.render("GAME OVER", True, Config.COLOR_RED)
        game_over_rect: pygame.Rect = game_over_text.get_rect(center=(Config.SCREEN_WIDTH // 2, 200))
        surface.blit(game_over_text, game_over_rect)
        
        instruction_text: pygame.Surface = self.instruction_font.render("Press SPACE to Retry", True, Config.COLOR_WHITE)
        instruction_rect: pygame.Rect = instruction_text.get_rect(center=(Config.SCREEN_WIDTH // 2, 350))
        surface.blit(instruction_text, instruction_rect)
        
        back_font: pygame.font.Font = pygame.font.Font(None, 30)
        back_text: pygame.Surface = back_font.render("Press ESC to Back to Title", True, Config.COLOR_WHITE)
        back_rect: pygame.Rect = back_text.get_rect(center=(Config.SCREEN_WIDTH // 2, 450))
        surface.blit(back_text, back_rect)


# ================== ゲームメインクラス ==================

class Game:
    def __init__(self) -> None:
        pygame.init()
        self.surface: pygame.Surface = pygame.display.set_mode((Config.SCREEN_WIDTH, Config.SCREEN_HEIGHT))
        pygame.display.set_caption("Fake Mario - Items Expansion")
        self.clock: pygame.time.Clock = pygame.time.Clock()
        
        self.current_scene_type: SceneType = SceneType.TITLE
        self.scenes: dict = {
            SceneType.TITLE: TitleScene(),
            SceneType.GAME: GameScene(),
            SceneType.GAME_OVER: GameOverScene(),
            SceneType.GAME_CLEAR: GameClearScene()
        }
        self.running: bool = True
    
    def get_current_scene(self) -> Scene:
        return self.scenes[self.current_scene_type]
    
    def handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            else:
                self.get_current_scene().handle_input(event)
    
    def update(self) -> None:
        current_scene: Scene = self.get_current_scene()
        next_scene_type: Optional[SceneType] = current_scene.update()
        
        if next_scene_type is not None:
            self.current_scene_type = next_scene_type
            if self.current_scene_type == SceneType.GAME:
                self.scenes[SceneType.GAME] = GameScene()
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
    game: Game = Game()
    game.run()