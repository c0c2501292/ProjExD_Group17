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

import pygame
import sys
from typing import Tuple, List, Optional, Sequence
from enum import Enum
from abc import ABC, abstractmethod

BlockConfig = Tuple[int, int, int, int, str]


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
    GOAL_X: int = 3200  # ゴールのX座標（ワールド座標）
    GOAL_Y: int = 410   # ゴールのY座標（ワールド座標）
    
    # ステージ設定
    STAGE_MAX_X: int = 3300  # ステージの最大X座標

    # 背景設定（将来背景画像に差し替え可能）
    BACKGROUND_COLOR: Tuple[int, int, int] = COLOR_LIGHT_BLUE
    BACKGROUND_IMAGE: Optional[pygame.Surface] = None


class SceneType(Enum):
    """シーンの種類を定義する列挙型"""
    TITLE = 1
    GAME = 2
    GAME_OVER = 3
    GAME_CLEAR = 4


# ================== ブロッククラス ==================

class Block:
    """
    ステージの床や足場を表すクラス
    
    このクラスを継承することで、特殊なギミックブロックを
    簡単に実装できるように設計されています。
    """
    
    def __init__(self, x: int, y: int, width: int = Config.BLOCK_WIDTH,
                 height: int = Config.BLOCK_HEIGHT,
                 kind: str = "ground",
                 color: Tuple[int, int, int] = Config.COLOR_GREEN,
                 image: Optional[pygame.Surface] = None) -> None:
        """
        ブロックの初期化
        
        Args:
            x: X座標（ワールド座標）
            y: Y座標（ワールド座標）
            width: ブロックの幅（ピクセル）
            height: ブロックの高さ（ピクセル）
            kind: ブロックの種類（将来のテクスチャ差し替え用）
            color: ブロックの色（RGB）
            image: 画像アセット（pygame.Surface）
        """
        self.x: int = x
        self.y: int = y
        self.width: int = width
        self.height: int = height
        self.kind: str = kind
        self.image: Optional[pygame.Surface] = image
        self.color: Tuple[int, int, int] = color

        if self.image is not None and self.image.get_size() != (self.width, self.height):
            self.image = pygame.transform.scale(self.image, (self.width, self.height))

        if self.image is None:
            self.color = self._get_color_for_kind(kind)

    def _get_color_for_kind(self, kind: str) -> Tuple[int, int, int]:
        """
        ブロックの種類に応じたカラーを返す
        
        Args:
            kind: ブロックの種類
        Returns:
            表示色（RGB）
        """
        kind_to_color = {
            "ground": Config.COLOR_GREEN,
            "platform": Config.COLOR_GRAY,
            "step": Config.COLOR_DARK_YELLOW,
            "water": Config.COLOR_BLUE,
            "goal": Config.COLOR_GOLD,
        }
        return kind_to_color.get(kind, self.color)

    def get_rect(self) -> pygame.Rect:
        """
        ブロックの矩形判定オブジェクトを取得
        
        Returns:
            ブロックを表すpygame.Rectオブジェクト
        """
        return pygame.Rect(self.x, self.y, self.width, self.height)
    
    def draw(self, surface: pygame.Surface, camera_x: int) -> None:
        """
        ブロックを描画（カメラオフセット適用）
        
        Args:
            surface: 描画対象のサーフェス
            camera_x: カメラのX座標オフセット
        """
        # 画面内のX座標を計算
        screen_x: int = self.x - camera_x
        
        # 画面外の場合は描画しない
        if screen_x + self.width < 0 or screen_x > Config.SCREEN_WIDTH:
            return
        
        rect: pygame.Rect = pygame.Rect(screen_x, self.y, self.width, self.height)
        if self.image is not None:
            surface.blit(self.image, (screen_x, self.y))
        else:
            pygame.draw.rect(surface, self.color, rect)
            pygame.draw.rect(surface, Config.COLOR_BLACK, rect, 2)


# ================== ゴールクラス ==================

class Goal:
    """
    ステージのゴール（ゴール地点）を表すクラス
    
    プレイヤーがこのゴールに接触するとゲームクリアになります。
    """
    
    def __init__(self, x: int = Config.GOAL_X, y: int = Config.GOAL_Y,
                 width: int = Config.GOAL_WIDTH, height: int = Config.GOAL_HEIGHT) -> None:
        """
        ゴールの初期化
        
        Args:
            x: X座標（ワールド座標）
            y: Y座標（ワールド座標）
            width: ゴールの幅（ピクセル）
            height: ゴールの高さ（ピクセル）
        """
        self.x: int = x
        self.y: int = y
        self.width: int = width
        self.height: int = height
        self.color: Tuple[int, int, int] = Config.COLOR_GOLD
    
    def get_rect(self) -> pygame.Rect:
        """
        ゴールの矩形判定オブジェクトを取得
        
        Returns:
            ゴールを表すpygame.Rectオブジェクト
        """
        return pygame.Rect(self.x, self.y, self.width, self.height)
    
    def check_collision(self, player_rect: pygame.Rect) -> bool:
        """
        プレイヤーとゴールの衝突判定を確認
        
        Args:
            player_rect: プレイヤーの矩形判定オブジェクト
        
        Returns:
            衝突している場合True、していない場合False
        """
        goal_rect: pygame.Rect = self.get_rect()
        return player_rect.colliderect(goal_rect)
    
    def draw(self, surface: pygame.Surface, camera_x: int) -> None:
        """
        ゴールを描画（カメラオフセット適用）
        
        Args:
            surface: 描画対象のサーフェス
            camera_x: カメラのX座標オフセット
        """
        # 画面内のX座標を計算
        screen_x: int = self.x - camera_x
        
        # 画面外の場合は描画しない
        if screen_x + self.width < 0 or screen_x > Config.SCREEN_WIDTH:
            return
        
        # ゴールを描画（フラグポール風）
        goal_rect: pygame.Rect = pygame.Rect(screen_x, self.y, self.width, self.height)
        pygame.draw.rect(surface, self.color, goal_rect)
        pygame.draw.rect(surface, Config.COLOR_BLACK, goal_rect, 3)
        
        # ゴール内に装飾（星を描画）
        center_x: int = screen_x + self.width // 2
        center_y: int = self.y + self.height // 2
        pygame.draw.polygon(surface, Config.COLOR_YELLOW, [
            (center_x, center_y - 8),
            (center_x + 4, center_y - 2),
            (center_x + 8, center_y),
            (center_x + 4, center_y + 4),
            (center_x + 6, center_y + 8),
            (center_x, center_y + 5),
            (center_x - 6, center_y + 8),
            (center_x - 4, center_y + 4),
            (center_x - 8, center_y),
            (center_x - 4, center_y - 2)
        ])


# ================== プレイヤークラス ==================

class Player:
    """
    プレイヤーキャラクターを表すクラス
    
    移動、ジャンプ、重力処理、およびブロックとの当たり判定を
    担当します。このクラスを継承することで、様々なプレイヤーバリエーション
    を実装できます。
    """
    
    def __init__(self, x: int = Config.PLAYER_START_X,
                 y: int = Config.PLAYER_START_Y,
                 width: int = Config.PLAYER_WIDTH,
                 height: int = Config.PLAYER_HEIGHT) -> None:
        """
        プレイヤーの初期化
        
        Args:
            x: 初期X座標（ワールド座標）
            y: 初期Y座標（ワールド座標）
            width: プレイヤーの幅（ピクセル）
            height: プレイヤーの高さ（ピクセル）
        """
        self.x: float = x
        self.y: float = y
        self.width: int = width
        self.height: int = height
        
        # 速度
        self.vx: float = 0.0  # X方向の速度
        self.vy: float = 0.0  # Y方向の速度
        
        # 状態
        self.is_jumping: bool = False  # ジャンプ中フラグ
        self.is_on_ground: bool = True  # 地面に接地中フラグ
        self.color: Tuple[int, int, int] = Config.COLOR_BLUE
        self.facing_right: bool = True  # 向き（右：True、左：False）
    
    def get_rect(self) -> pygame.Rect:
        """
        プレイヤーの矩形判定オブジェクトを取得
        
        Returns:
            プレイヤーを表すpygame.Rectオブジェクト
        """
        return pygame.Rect(int(self.x), int(self.y), self.width, self.height)
    
    def handle_input(self, keys: pygame.key.ScancodeWrapper) -> None:
        """
        キー入力を処理してプレイヤーの動作を更新
        
        Args:
            keys: pygame.key.get_pressed()の戻り値
        """
        # 左右の移動処理
        if keys[pygame.K_LEFT]:
            self.vx = -Config.PLAYER_MOVE_SPEED
            self.facing_right = False
        elif keys[pygame.K_RIGHT]:
            self.vx = Config.PLAYER_MOVE_SPEED
            self.facing_right = True
        else:
            self.vx = 0.0
        
        # ジャンプ処理（地面に接地していて、スペースキーが押された）
        if keys[pygame.K_SPACE] and self.is_on_ground:
            self.vy = -Config.PLAYER_JUMP_POWER
            self.is_jumping = True
            self.is_on_ground = False
    
    def apply_gravity(self) -> None:
        """重力を適用してY方向の速度を更新"""
        # 重力加速度を追加
        self.vy += Config.GRAVITY
        
        # 最大落下速度に制限
        if self.vy > Config.MAX_FALL_SPEED:
            self.vy = Config.MAX_FALL_SPEED
    
    def update(self, blocks: List[Block]) -> None:
        """
        プレイヤーの状態を更新
        
        Args:
            blocks: ステージ上のすべてのブロックのリスト
        """
        # 重力を適用
        self.apply_gravity()
        
        # 位置を更新
        self.x += self.vx
        self.y += self.vy
        
        # 接地状態をリセット
        self.is_on_ground = False
        
        # ブロックとの当たり判定
        self._check_block_collisions(blocks)
        
        # 画面下部でゲームオーバー判定
        if self.y > Config.SCREEN_HEIGHT + 100:
            self.reset()
    
    def _check_block_collisions(self, blocks: List[Block]) -> None:
        """
        ブロックとの当たり判定を処理
        
        Args:
            blocks: 判定対象のブロックリスト
        """
        player_rect: pygame.Rect = self.get_rect()
        
        for block in blocks:
            block_rect: pygame.Rect = block.get_rect()
            
            # 矩形が交差しているかチェック
            if not player_rect.colliderect(block_rect):
                continue
            
            # 衝突時の処理
            # Y方向の衝突判定（上下からの衝突を区別）
            overlap_y_from_top: int = player_rect.bottom - block_rect.top
            overlap_y_from_bottom: int = block_rect.bottom - player_rect.top
            
            # X方向の衝突判定（左右からの衝突を区別）
            overlap_x_from_left: int = player_rect.right - block_rect.left
            overlap_x_from_right: int = block_rect.right - player_rect.left
            
            # 最小オーバーラップ方向に応じて対応
            min_overlap: int = min(overlap_y_from_top, overlap_y_from_bottom,
                                   overlap_x_from_left, overlap_x_from_right)
            
            if min_overlap == overlap_y_from_top:
                # プレイヤーがブロックの上から着地
                self.y = block_rect.top - self.height
                self.vy = 0.0
                self.is_on_ground = True
                self.is_jumping = False
            elif min_overlap == overlap_y_from_bottom:
                # プレイヤーがブロックの下に衝突（頭をぶつける）
                self.y = block_rect.bottom
                self.vy = 0.0
            elif min_overlap == overlap_x_from_left:
                # プレイヤーがブロックの左から衝突
                self.x = block_rect.left - self.width
            elif min_overlap == overlap_x_from_right:
                # プレイヤーがブロックの右から衝突
                self.x = block_rect.right
    
    def draw(self, surface: pygame.Surface, camera_x: int) -> None:
        """
        プレイヤーを描画（カメラオフセット適用）
        
        Args:
            surface: 描画対象のサーフェス
            camera_x: カメラのX座標オフセット
        """
        # 画面内のX座標を計算
        screen_x: int = int(self.x) - camera_x
        screen_y: int = int(self.y)
        
        # プレイヤーの矩形を描画
        rect: pygame.Rect = pygame.Rect(screen_x, screen_y, self.width, self.height)
        pygame.draw.rect(surface, self.color, rect)
        
        # 枠線を描画
        pygame.draw.rect(surface, Config.COLOR_BLACK, rect, 2)
        
        # 顔の簡単な表現（ドット絵風）
        eye_offset: int = 8 if self.facing_right else (self.width - 14)
        pygame.draw.circle(surface, Config.COLOR_BLACK, 
                         (screen_x + eye_offset, screen_y + 12), 2)
    
    def reset(self) -> None:
        """プレイヤーをリセット（ゲームオーバー時など）"""
        self.x = Config.PLAYER_START_X
        self.y = Config.PLAYER_START_Y
        self.vx = 0.0
        self.vy = 0.0
        self.is_jumping = False
        self.is_on_ground = True


# ================== シーン管理 ==================

class Scene(ABC):
    """
    シーンの基底クラス
    
    すべてのシーン（タイトル、ゲーム本編など）はこのクラスを
    継承して実装します。
    """
    
    @abstractmethod
    def handle_input(self, event: pygame.event.EventType) -> None:
        """
        イベント処理
        
        Args:
            event: pygame のイベントオブジェクト
        """
        pass
    
    @abstractmethod
    def update(self) -> Optional[SceneType]:
        """
        シーン状態の更新
        
        Returns:
            シーン切り替え時は対応するSceneType、継続時はNone
        """
        pass
    
    @abstractmethod
    def draw(self, surface: pygame.Surface) -> None:
        """
        シーンの描画
        
        Args:
            surface: 描画対象のサーフェス
        """
        pass


class TitleScene(Scene):
    """タイトル画面シーン"""
    
    def __init__(self) -> None:
        """タイトル画面の初期化"""
        self.title_font: pygame.font.Font = pygame.font.Font(None, 80)
        self.instruction_font: pygame.font.Font = pygame.font.Font(None, 40)
    
    def handle_input(self, event: pygame.event.EventType) -> None:
        """
        キー入力処理
        
        Args:
            event: pygame のイベントオブジェクト
        """
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                # スペースキーでゲーム開始
                return
    
    def update(self) -> Optional[SceneType]:
        """
        更新処理
        
        Returns:
            スペースキーが押されたらゲームシーンに切り替え
        """
        keys: pygame.key.ScancodeWrapper = pygame.key.get_pressed()
        if keys[pygame.K_SPACE]:
            return SceneType.GAME
        return None
    
    def draw(self, surface: pygame.Surface) -> None:
        """
        画面描画
        
        Args:
            surface: 描画対象のサーフェス
        """
        # 背景を描画
        surface.fill(Config.COLOR_LIGHT_BLUE)
        
        # タイトルテキストを描画
        title_text: pygame.Surface = self.title_font.render(
            "FAKE MARIO", True, Config.COLOR_BLACK)
        title_rect: pygame.Rect = title_text.get_rect(
            center=(Config.SCREEN_WIDTH // 2, 150))
        surface.blit(title_text, title_rect)
        
        # 説明テキストを描画
        instruction_text: pygame.Surface = self.instruction_font.render(
            "Press SPACE to Start", True, Config.COLOR_BLACK)
        instruction_rect: pygame.Rect = instruction_text.get_rect(
            center=(Config.SCREEN_WIDTH // 2, 350))
        surface.blit(instruction_text, instruction_rect)
        
        # 操作説明を描画
        control_font: pygame.font.Font = pygame.font.Font(None, 30)
        controls: List[str] = [
            "LEFT/RIGHT: Move",
            "SPACE: Jump",
            "ESC: Return to Title"
        ]
        for i, control in enumerate(controls):
            control_text: pygame.Surface = control_font.render(
                control, True, Config.COLOR_BLACK)
            control_rect: pygame.Rect = control_text.get_rect(
                center=(Config.SCREEN_WIDTH // 2, 450 + i * 35))
            surface.blit(control_text, control_rect)


class GameScene(Scene):
    """ゲーム本編シーン"""
    
    def __init__(self) -> None:
        """ゲーム本編シーンの初期化"""
        self.player: Player = Player()
        self.blocks: List[Block] = self._create_stage()
        self.goal: Goal = Goal()
        self.camera_x: int = 0  # カメラの X 座標（ワールド座標）
        self.score: int = 0
        self.font: pygame.font.Font = pygame.font.Font(None, 36)
        self.background_image: Optional[pygame.Surface] = Config.BACKGROUND_IMAGE
    
    def _create_stage(self) -> List[Block]:
        """
        ステージを作成する
        
        タプル形式のステージデータを元に、Block オブジェクトを
        自動生成します。これにより、配置やサイズ、種類を直感的に
        変更しやすくなります。
        
        Returns:
            ステージ上のすべてのブロックのリスト
        """
        stage_layout: List[BlockConfig] = [
            # 開始エリア：地面
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
            
            # 階段状の足場
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
            
            #穴
            #(1216, 500, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "ground"),
            #(1280, 500, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "ground"),

            # 逆階段状の足場
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

            #階段状の足場2
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




            # 中盤：穴と浮き足場
            #(512, 500, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "ground"),
            #(576, 500, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "ground"),
            # ここに穴
            

           #穴
           
            

            # 浮遊足場
            #(660, 380, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "platform"),
            #(740, 340, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "platform"),
            #(820, 300, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "platform"),

            # 階段状足場
            

            # 中盤後期：高低差のある足場
            #(1200, 420, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "platform"),
            #(1264, 380, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "platform"),
            #(1328, 340, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "platform"),
            #(1392, 300, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "platform"),
            #(1456, 260, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "platform"),

            # 地面への復帰
            
            # 後半：穴を挟んだ連続足場
            

            #(1840, 420, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "platform"),
            #(1900, 360, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "platform"),
            #(1960, 320, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "platform"),
            #(2020, 280, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "platform"),
            #(2080, 240, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "platform"),

            # 終盤：ゴール前の上昇ステージ
            

            #(2500, 420, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "platform"),
            #(2560, 380, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "platform"),
            #(2620, 340, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "platform"),
            #(2680, 300, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "platform"),
            #(2740, 260, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "platform"),
            #(2800, 300, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "platform"),
            #(2860, 340, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "platform"),
            #(2920, 380, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "platform"),
            #(2980, 420, Config.BLOCK_WIDTH, Config.BLOCK_HEIGHT, "platform"),
        ]

        return [Block(x, y, width, height, kind=kind) for x, y, width, height, kind in stage_layout]
    
    def handle_input(self, event: pygame.event.EventType) -> None:
        """
        イベント処理（シーン切り替え判定）
        
        Args:
            event: pygame のイベントオブジェクト
        """
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                # ESCキーでタイトルに戻る
                return
    
    def update(self) -> Optional[SceneType]:
        """
        ゲーム状態の更新
        
        Returns:
            ゴール到達ならゲームクリアシーンに切り替え、
            ゲームオーバーならゲームオーバーシーンに切り替え、
            ESCキーでタイトルシーンに切り替え
        """
        # キー入力を処理
        keys: pygame.key.ScancodeWrapper = pygame.key.get_pressed()
        self.player.handle_input(keys)
        
        # ESCキーでタイトルに戻る
        if keys[pygame.K_ESCAPE]:
            return SceneType.TITLE
        
        # プレイヤーを更新            
        self.player.update(self.blocks)
        
        # カメラを更新（プレイヤーを追従）
        self._update_camera()
        
        # ゴール判定（プレイヤーがゴールに接触したか）
        if self.goal.check_collision(self.player.get_rect()):
            return SceneType.GAME_CLEAR
        
        # ゲームオーバー判定（プレイヤーの Y 座標が画面外）
        if self.player.y > Config.SCREEN_HEIGHT + 100:
            return SceneType.GAME_OVER
        
        return None
    
    def _update_camera(self) -> None:
        """カメラの位置を更新（プレイヤーを追従）"""
        # プレイヤーが画面の中央（400px）を超えたらカメラをスクロール
        target_camera_x: int = int(self.player.x) - Config.SCREEN_WIDTH // 4
        
        # カメラの最小値は0（ステージの左端）
        # カメラの最大値を設定してステージ外を映さないようにする
        max_camera_x: int = Config.STAGE_MAX_X - Config.SCREEN_WIDTH
        
        if target_camera_x < 0:
            self.camera_x = 0
        elif target_camera_x > max_camera_x:
            self.camera_x = max_camera_x
        else:
            self.camera_x = target_camera_x
    
    def draw(self, surface: pygame.Surface) -> None:
        """
        ゲーム画面の描画
        
        Args:
            surface: 描画対象のサーフェス
        """
        # 背景を描画（背景画像が設定されていれば画像を優先）
        if self.background_image is not None:
            surface.blit(self.background_image, (0, 0))
        else:
            surface.fill(Config.BACKGROUND_COLOR)
        
        # ブロックを描画
        for block in self.blocks:
            block.draw(surface, self.camera_x)
        
        # ゴールを描画
        self.goal.draw(surface, self.camera_x)
        
        # プレイヤーを描画
        self.player.draw(surface, self.camera_x)
        
        # スコアと座標情報を描画（デバッグ用）
        score_text: pygame.Surface = self.font.render(
            f"Score: {self.score} | X: {int(self.player.x)}", True, Config.COLOR_BLACK)
        surface.blit(score_text, (10, 10))
        
        # 操作ヒント
        hint_font: pygame.font.Font = pygame.font.Font(None, 20)
        hint_text: pygame.Surface = hint_font.render(
            "ESC: Back to Title", True, Config.COLOR_BLACK)
        surface.blit(hint_text, (Config.SCREEN_WIDTH - 200, 10))


class GameClearScene(Scene):
    """ゲームクリア画面シーン"""
    
    def __init__(self) -> None:
        """ゲームクリア画面の初期化"""
        self.title_font: pygame.font.Font = pygame.font.Font(None, 80)
        self.instruction_font: pygame.font.Font = pygame.font.Font(None, 40)
    
    def handle_input(self, event: pygame.event.EventType) -> None:
        """
        イベント処理
        
        Args:
            event: pygame のイベントオブジェクト
        """
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                # スペースキーでタイトルに戻る
                return
    
    def update(self) -> Optional[SceneType]:
        """
        更新処理
        
        Returns:
            スペースキーでタイトルシーンに切り替え
        """
        keys: pygame.key.ScancodeWrapper = pygame.key.get_pressed()
        
        if keys[pygame.K_SPACE]:
            return SceneType.TITLE
        
        return None
    
    def draw(self, surface: pygame.Surface) -> None:
        """
        画面描画
        
        Args:
            surface: 描画対象のサーフェス
        """
        # 背景を描画
        surface.fill(Config.COLOR_LIGHT_BLUE)
        
        # ゲームクリアテキストを描画
        clear_text: pygame.Surface = self.title_font.render(
            "GAME CLEAR!", True, Config.COLOR_GREEN)
        clear_rect: pygame.Rect = clear_text.get_rect(
            center=(Config.SCREEN_WIDTH // 2, 150))
        surface.blit(clear_text, clear_rect)
        
        # 説明テキストを描画
        instruction_text: pygame.Surface = self.instruction_font.render(
            "Congratulations!", True, Config.COLOR_BLACK)
        instruction_rect: pygame.Rect = instruction_text.get_rect(
            center=(Config.SCREEN_WIDTH // 2, 300))
        surface.blit(instruction_text, instruction_rect)
        
        # 続行指示を描画
        continue_font: pygame.font.Font = pygame.font.Font(None, 40)
        continue_text: pygame.Surface = continue_font.render(
            "Press SPACE to Back to Title", True, Config.COLOR_BLACK)
        continue_rect: pygame.Rect = continue_text.get_rect(
            center=(Config.SCREEN_WIDTH // 2, 450))
        surface.blit(continue_text, continue_rect)


class GameOverScene(Scene):
    """ゲームオーバー画面シーン"""
    
    def __init__(self) -> None:
        """ゲームオーバー画面の初期化"""
        self.title_font: pygame.font.Font = pygame.font.Font(None, 80)
        self.instruction_font: pygame.font.Font = pygame.font.Font(None, 40)
        self.countdown: int = 0  # 自動リセットまでのカウント
    
    def handle_input(self, event: pygame.event.EventType) -> None:
        """
        イベント処理
        
        Args:
            event: pygame のイベントオブジェクト
        """
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                # スペースキーでリトライ
                return
            elif event.key == pygame.K_ESCAPE:
                # ESCキーでタイトルに戻る
                return
    
    def update(self) -> Optional[SceneType]:
        """
        更新処理
        
        Returns:
            スペースキーでゲーム再開、ESCキーでタイトルに戻る
        """
        keys: pygame.key.ScancodeWrapper = pygame.key.get_pressed()
        
        if keys[pygame.K_SPACE]:
            return SceneType.GAME
        elif keys[pygame.K_ESCAPE]:
            return SceneType.TITLE
        
        return None
    
    def draw(self, surface: pygame.Surface) -> None:
        """
        画面描画
        
        Args:
            surface: 描画対象のサーフェス
        """
        # 背景を描画
        surface.fill(Config.COLOR_BLACK)
        
        # ゲームオーバーテキストを描画
        game_over_text: pygame.Surface = self.title_font.render(
            "GAME OVER", True, Config.COLOR_RED)
        game_over_rect: pygame.Rect = game_over_text.get_rect(
            center=(Config.SCREEN_WIDTH // 2, 200))
        surface.blit(game_over_text, game_over_rect)
        
        # 説明テキストを描画
        instruction_text: pygame.Surface = self.instruction_font.render(
            "Press SPACE to Retry", True, Config.COLOR_WHITE)
        instruction_rect: pygame.Rect = instruction_text.get_rect(
            center=(Config.SCREEN_WIDTH // 2, 350))
        surface.blit(instruction_text, instruction_rect)
        
        # タイトルに戻るオプションを表示
        back_font: pygame.font.Font = pygame.font.Font(None, 30)
        back_text: pygame.Surface = back_font.render(
            "Press ESC to Back to Title", True, Config.COLOR_WHITE)
        back_rect: pygame.Rect = back_text.get_rect(
            center=(Config.SCREEN_WIDTH // 2, 450))
        surface.blit(back_text, back_rect)


# ================== ゲームメインクラス ==================

class Game:
    """
    ゲーム全体を管理するメインクラス
    
    メインループ、シーン管理、入力処理、描画を統括します。
    """
    
    def __init__(self) -> None:
        """ゲームの初期化"""
        # Pygame の初期化
        pygame.init()
        
        # ディスプレイの設定
        self.surface: pygame.Surface = pygame.display.set_mode(
            (Config.SCREEN_WIDTH, Config.SCREEN_HEIGHT))
        pygame.display.set_caption("Fake Mario - 2D Platformer")
        
        # クロックの設定（FPS制御用）
        self.clock: pygame.time.Clock = pygame.time.Clock()
        
        # シーン管理
        self.current_scene_type: SceneType = SceneType.TITLE
        self.scenes: dict = {
            SceneType.TITLE: TitleScene(),
            SceneType.GAME: GameScene(),
            SceneType.GAME_OVER: GameOverScene(),
            SceneType.GAME_CLEAR: GameClearScene()
        }
        
        self.running: bool = True
    
    def get_current_scene(self) -> Scene:
        """
        現在のシーンを取得
        
        Returns:
            現在のシーンオブジェクト
        """
        return self.scenes[self.current_scene_type]
    
    def handle_events(self) -> None:
        """イベント処理"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                # ウィンドウが閉じられた
                self.running = False
            else:
                # 現在のシーンにイベントを渡す
                self.get_current_scene().handle_input(event)
    
    def update(self) -> None:
        """ゲーム状態の更新"""
        current_scene: Scene = self.get_current_scene()
        next_scene_type: Optional[SceneType] = current_scene.update()
        
        # シーンの切り替え
        if next_scene_type is not None:
            self.current_scene_type = next_scene_type
            # シーン切り替え時に新しいインスタンスを作成（状態をリセット）
            if self.current_scene_type == SceneType.GAME:
                self.scenes[SceneType.GAME] = GameScene()
            elif self.current_scene_type == SceneType.GAME_OVER:
                self.scenes[SceneType.GAME_OVER] = GameOverScene()
            elif self.current_scene_type == SceneType.GAME_CLEAR:
                self.scenes[SceneType.GAME_CLEAR] = GameClearScene()
    
    def draw(self) -> None:
        """画面描画"""
        # 現在のシーンを描画
        self.get_current_scene().draw(self.surface)
        
        # 画面更新
        pygame.display.flip()
    
    def run(self) -> None:
        """
        ゲームのメインループを実行
        
        このメソッドがゲーム終了まで実行されます。
        """
        while self.running:
            # イベント処理
            self.handle_events()
            
            # 状態更新
            self.update()
            
            # 描画
            self.draw()
            
            # FPS制御
            self.clock.tick(Config.FPS)
        
        # クリーンアップ
        pygame.quit()
        sys.exit()


# ================== エントリーポイント ==================

if __name__ == "__main__":
    """
    ゲーム実行のエントリーポイント
    
    このスクリプトを直接実行することでゲームが起動します。
    """
    game: Game = Game()
    game.run() 