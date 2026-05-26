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
    BACKGROUND_IMAGE_PATH: str = "背景.png"  

    # ステージ・システム
    GROUND_IMAGE_PATH: str = "地面.png"            
    BLOCK_IMAGE_PATH: str = "ブロック.png"
    GOAL_IMAGE_PATH: str = "ゴールお城.png"         
    # 主人公（プレイヤー）の状態
    PLAYER_IMAGE_PATH: str = "主人公.png"                    # 通常スライム
    PLAYER_FIRE_IMAGE_PATH: str = "ファイヤー.png"            # ファイヤースライム
    PLAYER_FIRE_ATTACK_IMAGE_PATH: str = "ファイヤーの火を吐く-removebg-preview.png" # 攻撃モーション
    PLAYER_STAR_IMAGE_PATH: str = "スター状態.png"            # 無敵スライム

    # アイテム・エフェクト
    ITEM_MUSHROOM_IMAGE_PATH: str = "キノコ.png"
    EFFECT_FIREBALL_IMAGE_PATH: str = "火単体.png"           # 飛ばす火の玉

    # 敵キャラクター
    ENEMY_ZAKO_IMAGE_PATH: str = "雑魚的.png"
    ENEMY_BOSS_IMAGE_PATH: str = "ラスボス.png" 

    TIME_LIMIT: float = 300.0
    
    ENEMY_WIDTH: int = 32      # ザコ敵の横幅
    ENEMY_HEIGHT: int = 32     # ザコ敵の縦幅
    ENEMY_SPEED: float = 2.0   # ザコ敵の歩くスピード
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
    
    【これまでのすべての修正を反映した完全版】
    ・画像を縦長（1.8倍）に引き伸ばし
    ・主人公が深く（45ピクセル）めり込んで歩けるように判定を調整
    ・draw関数の引数エラーを100%回避する安全設計
    """
    
    def __init__(self, x: int, y: int, width: int = Config.BLOCK_WIDTH,
                 height: int = Config.BLOCK_HEIGHT,
                 kind: str = "ground",
                 color: Tuple[int, int, int] = Config.COLOR_GREEN,
                 image: Optional[pygame.Surface] = None) -> None:
        """
        ブロックの初期化
        """
        # すべての値を確実に整数（int）にして保存
        self.x: int = int(x)
        self.y: int = int(y)
        self.width: int = int(width)
        self.height: int = int(height)
        self.kind: str = kind
        self.color: Tuple[int, int, int] = color
        self.image: Optional[pygame.Surface] = image

        # 1. 画像が設定されていない場合、種類に合わせて自動読み込み
        if self.image is None:
            import os
            try:
                current_dir = os.path.dirname(os.path.abspath(__file__))
                file_name = None

                if kind == "ground":
                    file_name = Config.GROUND_IMAGE_PATH       # "地面.png"
                elif kind == "platform" or kind == "step":
                    file_name = Config.BLOCK_IMAGE_PATH        # "ブロック.png"
                elif kind == "goal":
                    file_name = Config.GOAL_IMAGE_PATH         # "ゴールお城.png"

                if file_name is not None:
                    full_path = os.path.join(current_dir, file_name)
                    self.image = pygame.image.load(full_path).convert_alpha()
                    
            except Exception as e:
                print(f"ブロック画像（{kind}）の読み込みに失敗しました: {e}")
                self.image = None

        # 2. 画像の引き伸ばし処理（1.8倍）
        if self.image is not None:
            stretch_scale = 1.8
            self.height = int(self.height * stretch_scale)
            
            # 縦長になったサイズに画像を変換
            self.image = pygame.transform.scale(self.image, (self.width, self.height))
        else:
            self.color = self._get_color_for_kind(kind)

    def _get_color_for_kind(self, kind: str) -> Tuple[int, int, int]:
        """画像がないとき用の色分け"""
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
        ブロックの矩形判定オブジェクトを取得（衝突判定用）
        
        判定の天井を45ピクセル下げることで、主人公を深くめり込ませます。
        """
        sink_pixels = 65
        
        adjusted_y = self.y + sink_pixels
        adjusted_height = self.height - sink_pixels
        
        if adjusted_height <= 0:
            adjusted_height = 1
            
        return pygame.Rect(self.x, adjusted_y, self.width, adjusted_height)
    
    def draw(self, *args, **kwargs) -> None:
        """
        ブロックを描画（エラー完全回避版）
        
        メイン側の呼び出し方が引数をどう渡してきても、
        自動で判別してエラーを出さずに安全に描画します。
        """
        surface = None
        camera_x = 0

        # 位置引数 (*args) からデータを取り出す
        if len(args) >= 1:
            surface = args[0]
        if len(args) >= 2:
            camera_x = args[1]

        # キーワード引数 (**kwargs) からデータを取り出す
        if "surface" in kwargs:
            surface = kwargs["surface"]
        if "camera_x" in kwargs:
            camera_x = kwargs["camera_x"]

        # 画面が正常に渡されていなければ処理をスキップ
        if surface is None:
            return

        # 画面内のX座標を計算
        screen_x: int = self.x - int(camera_x)
        
        # 画面外の場合は描画しない（軽量化）
        if screen_x + self.width < 0 or screen_x > Config.SCREEN_WIDTH:
            return
        
        # 1.8倍に引き伸ばされた画像を正しい位置に描画
        if self.image is not None:
            surface.blit(self.image, (screen_x, self.y))
        else:
            # 画像がない場合の予備表示
            rect: pygame.Rect = pygame.Rect(screen_x, self.y, self.width, self.height)
            pygame.draw.rect(surface, self.color, rect)
            pygame.draw.rect(surface, Config.COLOR_BLACK, rect, 2)

# ================== ゴールクラス ==================

class Goal:
    """
    ステージのゴール（ゴール地点）を表すクラス
    
    4倍の超巨大お城が画面の右端で見切れないように、
    X座標を自動で左側に回り込ませて全体を映すコードです。
    """
    
    def __init__(self, x: int = Config.GOAL_X, y: int = Config.GOAL_Y,
                 width: int = Config.GOAL_WIDTH, height: int = Config.GOAL_HEIGHT) -> None:
        """
        ゴールの初期化
        """
        # ワールド座標を整数（int）にして保存
        self.x: int = int(x)
        self.y: int = int(y)
        self._original_width: int = int(width)
        self._original_height: int = int(height)
        
        self.color: Tuple[int, int, int] = Config.COLOR_GOLD
        self.image: Optional[pygame.Surface] = None

        # 1. 「ゴールお城.png」の画像を自動で読み込む
        import os
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            file_name = Config.GOAL_IMAGE_PATH 
            
            full_path = os.path.join(current_dir, file_name)
            self.image = pygame.image.load(full_path).convert_alpha()
            
            # 4.0倍にスケールアップ
            scale_size = 4.0
            self.width = int(self._original_width * scale_size)
            self.height = int(self._original_height * scale_size)
            
            # 💡 【今回のメイン修正：左側へずらす】
            # お城が横に大きくなった分（self.width - self._original_width）、
            # そのままだと右にはみ出るので、その差分の「約半分〜8割」くらいを左側に引っ張ります。
            # 最後の「- 64」の数字を大きくするほど、お城がさらに左側に移動します。
            self.x = self.x - (self.width - self._original_width) - 64
            
            # 【高さの調整】下端を地面に合わせる（前回の設定を維持）
            self.y = self.y - (self.height - self._original_height) + 40
            
            # 4倍サイズに画像を変換
            self.image = pygame.transform.scale(self.image, (self.width, self.height))
            
        except Exception as e:
            print(f"ゴールお城画像の読み込みに失敗しました: {e}")
            self.image = None
            self.width = self._original_width
            self.height = self._original_height
    
    def get_rect(self) -> pygame.Rect:
        """
        ゴールの矩形判定オブジェクトを取得（衝突判定用）
        """
        # お城の位置（self.x）が左にずれたので、当たり判定の門の位置も自動で連動します。
        # 左右の余白を削って、中央の門だけに判定を絞ります。
        shrink_pixels_x = 90 
        
        adjusted_x = self.x + shrink_pixels_x
        adjusted_width = self.width - (shrink_pixels_x * 2)
        
        adjusted_y = self.y 
        adjusted_height = self.height
        
        if adjusted_width <= 0:
            adjusted_width = 1
            
        return pygame.Rect(adjusted_x, adjusted_y, adjusted_width, adjusted_height)
    
    def check_collision(self, player_rect: pygame.Rect) -> bool:
        """
        プレイヤーとゴールの衝突判定を確認
        """
        goal_rect: pygame.Rect = self.get_rect()
        return player_rect.colliderect(goal_rect)
    
    def draw(self, surface: pygame.Surface, camera_x: int) -> None:
        """
        ゴールを描画（カメラオフセット適用）
        """
        screen_x: int = self.x - int(camera_x)
        
        if screen_x + self.width < 0 or screen_x > Config.SCREEN_WIDTH:
            return
        
        if self.image is not None:
            surface.blit(self.image, (screen_x, self.y))
        else:
            goal_rect: pygame.Rect = pygame.Rect(screen_x, self.y, self.width, self.height)
            pygame.draw.rect(surface, self.color, goal_rect)
            pygame.draw.rect(surface, Config.COLOR_BLACK, goal_rect, 3)


# ================== プレイヤークラス ==================

class Player:
    """
    プレイヤーキャラクターを表すクラス
    
    「主人公.png」の画像を読み込み、移動、ジャンプ、重力処理、
    および左右の反転描画に対応したコードです。
    """
    
    def __init__(self, x: int = Config.PLAYER_START_X,
                 y: int = Config.PLAYER_START_Y,
                 width: int = Config.PLAYER_WIDTH,
                 height: int = Config.PLAYER_HEIGHT) -> None:
        """
        プレイヤーの初期化
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

        # 💡 「主人公.png」の画像を読み込む
        import os
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            # Configに PLAYER_IMAGE_PATH = "主人公.png" があればそれを使い、
            # なければ直接文字列で指定して読み込みます。
            file_name = getattr(Config, "PLAYER_IMAGE_PATH", "主人公.png")
            
            full_path = os.path.join(current_dir, file_name)
            self.image_original = pygame.image.load(full_path).convert_alpha()
            
            # 設定されたプレイヤーのサイズ（width, height）に画像をリサイズ
            self.image_original = pygame.transform.scale(self.image_original, (self.width, self.height))
        except Exception as e:
            print(f"プレイヤー画像の読み込みに失敗しました（予備の四角表示にします）: {e}")
            self.image_original = None
    
    def get_rect(self) -> pygame.Rect:
        """
        プレイヤーの矩形判定オブジェクトを取得
        """
        return pygame.Rect(int(self.x), int(self.y), self.width, self.height)
    
    def handle_input(self, keys: pygame.key.ScancodeWrapper) -> None:
        """
        キー入力を処理してプレイヤーの動作を更新
        """
        # 左右の移動処理
        if keys[pygame.K_LEFT]:
            self.vx = -Config.PLAYER_MOVE_SPEED
            self.facing_right = False  # 左を向く
        elif keys[pygame.K_RIGHT]:
            self.vx = Config.PLAYER_MOVE_SPEED
            self.facing_right = True   # 右を向く
        else:
            self.vx = 0.0
        
        # ジャンプ処理
        if keys[pygame.K_SPACE] and self.is_on_ground:
            self.vy = -Config.PLAYER_JUMP_POWER
            self.is_jumping = True
            self.is_on_ground = False
            # print(f"self.is_jumping:{self.is_jumping}")
            # print(f"self.is_on_ground:{self.is_on_ground}")
    
    def apply_gravity(self) -> None:
        """重力を適用してY方向の速度を更新"""
        self.vy += Config.GRAVITY
        if self.vy > Config.MAX_FALL_SPEED:
            self.vy = Config.MAX_FALL_SPEED
    
    def update(self, blocks: List[Block]) -> None:
        """
        プレイヤーの状態を更新
        """
        self.apply_gravity()
        
        self.x += self.vx
        self.y += self.vy
        
        self.is_on_ground = True #無限ジャンプ原因
        self._check_block_collisions(blocks)
        
        # 画面下部でゲームオーバー判定
        if self.y > Config.SCREEN_HEIGHT + 100:
            self.reset()
    
    def _check_block_collisions(self, blocks: List[Block]) -> None:
        """
        ブロックとの当たり判定を処理
        """
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
            
            if min_overlap == overlap_y_from_top and self.vy >= 0:  # 上から着地
                self.y = block_rect.top - self.height
                self.vy = 0.0
                self.is_on_ground = True
                self.is_jumping = False
            elif min_overlap == overlap_y_from_bottom and self.vy < 0:
                self.y = block_rect.bottom
                self.vy = 0.0
                self.is_on_ground = True
                self.is_jumping = False
            elif min_overlap == overlap_x_from_left:
                self.x = block_rect.left - self.width
            elif min_overlap == overlap_x_from_right:
                self.x = block_rect.right
    
    def draw(self, surface: pygame.Surface, camera_x: int) -> None:
        """
        プレイヤーを描画（カメラオフセット適用）
        """
        screen_x: int = int(self.x) - camera_x
        screen_y: int = int(self.y)
        
        if self.image_original is not None:
            # 💡 【向きの自動反転】
            # 右向きならそのまま、左向きなら画像を左右反転（横反転：True、縦反転：False）させて描画します
            if self.facing_right:
                surface.blit(self.image_original, (screen_x, screen_y))
            else:
                flipped_image = pygame.transform.flip(self.image_original, True, False)
                surface.blit(flipped_image, (screen_x, screen_y))
        else:
            # 【予備】画像がない場合は元の青い四角形と目を描画
            rect: pygame.Rect = pygame.Rect(screen_x, screen_y, self.width, self.height)
            pygame.draw.rect(surface, self.color, rect)
            pygame.draw.rect(surface, Config.COLOR_BLACK, rect, 2)
            
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

# ================== 敵（通常ザコ＆ボス）システム ==================

class Enemy:
    """自動で歩き、壁で反転し、プレイヤーと接触判定を行うシンプルなザコ敵"""
    
    def __init__(self, x: int, y: int) -> None:
        self.x: float = x
        self.y: float = y
        # 後でデザインを当てやすい標準的なサイズ
        self.width: int = Config.ENEMY_WIDTH
        self.height: int = Config.ENEMY_HEIGHT
        self.vx: float = -Config.ENEMY_SPEED  # 最初は左に進む
        self.vy: float = 0.0
        # 仮のデザイン：通常のザコ敵は「赤色の四角」
        self.color: Tuple[int, int, int] = Config.COLOR_RED
        
    def get_rect(self) -> pygame.Rect:
        """衝突判定用の四角形データを返す"""
        return pygame.Rect(int(self.x), int(self.y), self.width, self.height)
        
    def update(self, blocks: List[Block]) -> None:
        """物理演算とブロック（床・壁）との当たり判定"""
        # 重力の適用
        self.vy += Config.GRAVITY
        if self.vy > Config.MAX_FALL_SPEED:
            self.vy = Config.MAX_FALL_SPEED
            
        self.x += self.vx
        self.y += self.vy
        
        # 地形との衝突判定＆壁での反転
        enemy_rect = self.get_rect()
        for block in blocks:
            block_rect = block.get_rect()
            if enemy_rect.colliderect(block_rect):
                overlap_x = min(enemy_rect.right - block_rect.left, block_rect.right - enemy_rect.left)
                overlap_y = min(enemy_rect.bottom - block_rect.top, block_rect.bottom - enemy_rect.top)
                
                if overlap_y < overlap_x:
                    if self.vy > 0:  # 床に着地
                        self.y = block_rect.top - self.height
                        self.vy = 0.0
                else:  # 壁にぶつかったら反転
                    if self.vx > 0:
                        self.x = block_rect.left - self.width
                    else:
                        self.x = block_rect.right
                    self.vx *= -1
                    
    def draw(self, surface: pygame.Surface, camera_x: int) -> None:
        """仮の姿（シンプルな四角形）として描画"""
        screen_x = int(self.x) - camera_x
        # 画面外なら描画をスキップ
        if screen_x + self.width < 0 or screen_x > Config.SCREEN_WIDTH:
            return
            
        rect = pygame.Rect(screen_x, int(self.y), self.width, self.height)
        pygame.draw.rect(surface, self.color, rect)
        pygame.draw.rect(surface, Config.COLOR_BLACK, rect, 2)  # 輪郭線


class Boss(Enemy):
    """3回踏まないと倒せない、システム確認用の巨大なボスクラス"""
    
    def __init__(self, x: int, y: int) -> None:
        super().__init__(x, y)
        # ラスボスらしく、ザコ敵よりもサイズを大きく設定
        self.width = 80
        self.height = 96
        # 移動スピードはどっしり遅め
        self.vx = -1.2
        # 仮のデザイン：ラスボスは「緑色の大きな四角」
        self.color = (0, 150, 50) 
        
        # ボスの固有システム：体力（HP）
        self.hp: int = 3

    def take_damage(self) -> bool:
        """ダメージを受けた（踏まれた）時の処理"""
        self.hp -= 1
        if self.hp <= 0:
            return True  # 撃破フラグ（消滅）
            
        # ダメージを受けると怒ってスピードが1.5倍になるギミック
        self.vx *= 1.5
        return False  # まだ生きてる
    
# === ここまで追加 ===
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
            print("s")
            if event.key == pygame.K_RETURN:
                # スペースキーでゲーム開始
                return
    
    def update(self) -> Optional[SceneType]:
        """
        更新処理
        
        Returns:
            スペースキーが押されたらゲームシーンに切り替え
        """
        keys: pygame.key.ScancodeWrapper = pygame.key.get_pressed()
        if keys[pygame.K_RETURN]:
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
            "Press ENTER to Start", True, Config.COLOR_BLACK)
        instruction_rect: pygame.Rect = instruction_text.get_rect(
            center=(Config.SCREEN_WIDTH // 2, 350))
        surface.blit(instruction_text, instruction_rect)
        
        # 操作説明を描画
        control_font: pygame.font.Font = pygame.font.Font(None, 30)
        controls: List[str] = [
            "LEFT/RIGHT: Move",
            "ENTER: Jump",
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
        self.time_remaining: float = Config.TIME_LIMIT
        
        # self.enemies = []
        # 道中の通常ザコ敵のみ（テスト用に目の前に配置）
        self.enemies: List[Enemy] = [
            Enemy(500, 300),
            Enemy(1200, 200),
            Enemy(2000, 300)
        ]
        
        # ボスをゴール手前に配置（テスト用に目の前に配置）
        self.boss: Optional[Boss] = Boss(3000, 200)
        try:
            import os
            # プログラムがあるフォルダの場所を絶対パスで取得
            current_dir = os.path.dirname(os.path.abspath(__file__))
            # 「背景.png」の正確なフルパス（住所）を作る
            bg_path = os.path.join(current_dir, "背景.png")
            
            # 画像を読み込んで画面サイズ（800x600）にリサイズ
            raw_bg = pygame.image.load(bg_path).convert()
            self.background_image = pygame.transform.scale(raw_bg, (Config.SCREEN_WIDTH, Config.SCREEN_HEIGHT))
            print("背景画像の読み込みに成功しました！")
            
        except Exception as e:
            print(f"背景画像の読み込みに失敗しました（予備の水色背景を使用します）: {e}")
            # 万が一画像が見つからなくても、ゲームが落ちないように水色で塗りつぶす
            self.background_image = pygame.Surface((Config.SCREEN_WIDTH, Config.SCREEN_HEIGHT))
            self.background_image.fill((135, 206, 235))    
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
        """イベント処理（シーン切り替え判定）"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return
    
    def update(self) -> Optional[SceneType]:
        """ゲーム状態の更新"""
        keys: pygame.key.ScancodeWrapper = pygame.key.get_pressed()
        self.player.handle_input(keys)
        
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
        # 制限時間のカウントダウン
        self.time_remaining -= 1 / Config.FPS
        if self.time_remaining <= 0:
            self.time_remaining = 0
            return SceneType.GAME_OVER
        
        self.player.update(self.blocks)
        player_rect = self.player.get_rect()
        
        # --- ① 通常ザコ敵のループ（衝突＆画面外消滅処理） ---
        enemies_to_remove = []
        for enemy in self.enemies:
            enemy.update(self.blocks)
            
            # カメラの左外に完全に見えなくなったら消滅
            if enemy.x + enemy.width < self.camera_x:
                enemies_to_remove.append(enemy)
                continue
            
            # 通常敵との衝突判定
            if player_rect.colliderect(enemy.get_rect()):
                if player_rect.bottom <= enemy.get_rect().top + 15 and self.player.vy >= 0:
                    self.player.vy = -Config.PLAYER_JUMP_POWER * 0.8
                    enemies_to_remove.append(enemy)
                    self.score += 100
                else:
                    return SceneType.GAME_OVER
                    
        for enemy in enemies_to_remove:
            self.enemies.remove(enemy)
            
        # --- ② ボスの計算と衝突処理 ---
        if self.boss is not None:
            self.boss.update(self.blocks)
            if player_rect.colliderect(self.boss.get_rect()):
                if player_rect.bottom <= self.boss.get_rect().top + 20 and self.player.vy >= 0:
                    self.player.vy = -Config.PLAYER_JUMP_POWER * 1.0  # ボスを踏むと大ジャンプ
                    if self.boss.take_damage():
                        self.boss = None
                        self.score += 1000
                else:
                    return SceneType.GAME_OVER
        
        self._update_camera()
        
        if self.goal.check_collision(self.player.get_rect()): 
            return SceneType.GAME_CLEAR
        if self.player.y > Config.SCREEN_HEIGHT + 100: 
            return SceneType.GAME_OVER
            
        return None

    def _update_camera(self) -> None:
        """カメラの位置を更新（プレイヤーを追従）"""
        target_camera_x: int = int(self.player.x) - Config.SCREEN_WIDTH // 4
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
        # """ゲーム画面の描画"""
        # # 背景を描画
        # surface.fill(Config.COLOR_LIGHT_BLUE)
        
        # ブロックを描画
        for block in self.blocks:
            block.draw(surface, self.camera_x)
        
        # ゴールを描画
        self.goal.draw(surface, self.camera_x)
        
        # --- 通常ザコ敵の描画 ---
        for enemy in self.enemies: 
            enemy.draw(surface, self.camera_x)
            
        # --- ボスの描画と残りHP表示 ---
        if self.boss is not None:
            self.boss.draw(surface, self.camera_x)
            boss_screen_x = int(self.boss.x) - self.camera_x
            hp_text = self.font.render("HP: " + "★" * self.boss.hp, True, Config.COLOR_RED)
            surface.blit(hp_text, (boss_screen_x, int(self.boss.y) - 30))
        
        # プレイヤーを描画
        self.player.draw(surface, self.camera_x)
        
        # 情報UI（タイムとスコア、座標）の描画
        seconds = max(0, int(self.time_remaining))
        score_text = self.font.render(f"Score: {self.score} | TIME: {seconds} | X: {int(self.player.x)}", True, Config.COLOR_BLACK)
        surface.blit(score_text, (10, 10))
        
        # 操作ヒント
        hint_font: pygame.font.Font = pygame.font.Font(None, 20)
        hint_text: pygame.Surface = hint_font.render("ESC: Back to Title", True, Config.COLOR_BLACK)
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
            if event.key == pygame.K_RETURN:
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
        
        if keys[pygame.K_RETURN]:
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
            
            print(self.scenes[SceneType.GAME].player.is_on_ground)
            
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