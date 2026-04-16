"""
仿真控制器模块
使用 Pygame 创建简易小车仿真环境
"""

import pygame
import math
import time
from src.controller import Command


class SimController:
    """
    仿真控制器
    使用 Pygame 显示小车状态和运动
    """
    
    def __init__(self, window_width=800, window_height=600):
        """
        初始化仿真控制器
        
        Args:
            window_width: 窗口宽度
            window_height: 窗口高度
        """
        self.window_width = window_width
        self.window_height = window_height
        
        # 小车状态
        self.x = window_width // 2
        self.y = window_height // 2
        self.angle = 0  # 角度（度）
        self.speed = 0
        self.max_speed = 5
        self.turn_speed = 3
        
        # 颜色定义
        self.COLOR_BG = (240, 240, 240)  # 浅灰色背景
        self.COLOR_CAR = (50, 100, 200)   # 蓝色小车
        self.COLOR_TEXT = (30, 30, 30)    # 深灰色文字
        
        # Pygame 初始化
        self.screen = None
        self.clock = None
        self.font = None
        self.running = False
        
        # 当前指令
        self.current_command = None
        self.command_timestamp = 0
        # 手动优先相关
        self.manual_timeout = 0.5  # 手动操作后 0.5 秒内忽略自动指令
        self.last_manual_time = 0
        # 手动按键状态
        self.key_left_pressed = False
        self.key_right_pressed = False
        self.key_up_pressed = False
        self.key_down_pressed = False
        # 加速/减速参数
        self.acceleration = 0.2          # 每帧加速度
        self.brake_deceleration = 0.3    # 刹车减速度（按下键时）
        self.friction = 0.02             # 无操作时的自然摩擦力
        self.max_forward_speed = 5.0     # 最大前进速度
        self.max_reverse_speed = -3.0    # 最大倒车速度（负值）
        # 转弯平滑参数
        self.turn_rate = 0.0                # 当前转弯速率（度/帧）
        self.max_turn_rate = 4.0            # 最大转弯速率
        self.turn_acceleration = 0.3        # 转弯加速度
        self.turn_friction = 0.1            # 转弯回正摩擦力
        # 目标状态（用于平滑自动控制）
        self.target_speed = 0.0
        self.target_turn_direction = 0   # -1:左, 0:直行, 1:右
    
    def init(self):
        """初始化 Pygame"""
        pygame.init()
        self.screen = pygame.display.set_mode((self.window_width, self.window_height))
        pygame.display.set_caption('车辆仿真 - Turn Sign Recognition Control')
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.running = True
        
        print("仿真环境已初始化")
    
    def execute(self, command, source='auto'):
        """
        执行控制指令
        
        Args:
            command: Command 枚举
            source: 'auto' 或 'manual'，表示指令来源
        """
        # 如果是自动指令，且距离上次手动操作未超时，则忽略
        if source == 'auto' and (time.time() - self.last_manual_time) < self.manual_timeout:
            return  # 手动优先，忽略自动指令
        
        self.current_command = command
        
        if command is None:
            return
        
        # 根据指令设置速度和转向
        if command.name == 'TURN_LEFT':
            self.speed = self.max_speed * 0.5
            self.angle -= self.turn_speed
        elif command.name == 'TURN_RIGHT':
            self.speed = self.max_speed * 0.5
            self.angle += self.turn_speed
        elif command.name == 'GO_STRAIGHT':
            self.speed = self.max_speed
            # 直行时保持当前方向
        elif command.name == 'STOP':
            self.speed = 0
        elif command.name == 'UNKNOWN':
            self.speed = 0
    
    def update(self):
        """更新小车位置（支持手动长按连续控制）"""
        # 手动加减速（长按持续生效）
        if self.key_up_pressed:
            self._mark_manual_control()
            self.speed = min(self.speed + self.acceleration, self.max_forward_speed)
        elif self.key_down_pressed:
            self._mark_manual_control()
            self.speed = max(self.speed - self.brake_deceleration, self.max_reverse_speed)
        else:
            # 自然摩擦力
            if self.speed > 0:
                self.speed = max(self.speed - self.friction, 0)
            elif self.speed < 0:
                self.speed = min(self.speed + self.friction, 0)

        # 根据按键决定目标转弯方向
        turn_direction = 0
        if self.key_left_pressed:
            turn_direction = -1
        if self.key_right_pressed:
            turn_direction = 1
    
        # 只有速度不为零时，才允许转弯（禁止原地转弯）
        if self.speed != 0 and turn_direction != 0:
            self._mark_manual_control()
            # 向目标方向加速转弯速率
            target_turn_rate = turn_direction * self.max_turn_rate
            if self.turn_rate < target_turn_rate:
                self.turn_rate = min(self.turn_rate + self.turn_acceleration, target_turn_rate)
            elif self.turn_rate > target_turn_rate:
                self.turn_rate = max(self.turn_rate - self.turn_acceleration, target_turn_rate)
        else:
            # 没有转向输入或速度为零时，转弯速率逐渐回零（模拟回正）
            if self.turn_rate > 0:
                self.turn_rate = max(self.turn_rate - self.turn_friction, 0)
            elif self.turn_rate < 0:
                self.turn_rate = min(self.turn_rate + self.turn_friction, 0)
    
        # 应用转弯速率到角度
        self.angle += self.turn_rate
    
        # 转弯时轻微减速（可选，保留）
        if self.speed != 0 and (self.key_left_pressed or self.key_right_pressed):
            if self.speed > 0:
                self.speed -= 0.05
            elif self.speed < 0:
                self.speed += 0.05

        # 边界检查与位置更新
        rad = math.radians(self.angle)
        self.x += math.cos(rad) * self.speed
        self.y -= math.sin(rad) * self.speed

        if self.x < 0:
            self.x = self.window_width
        elif self.x > self.window_width:
            self.x = 0
        if self.y < 0:
            self.y = self.window_height
        elif self.y > self.window_height:
            self.y = 0
    
    def render(self, recognition_result=None):
        """
        渲染仿真场景
        
        Args:
            recognition_result: 识别结果字典（可选）
        """
        # 清空屏幕
        self.screen.fill(self.COLOR_BG)
        
        # 绘制网格背景
        self._draw_grid()
        
        # 绘制小车
        self._draw_car()
        
        # 绘制信息面板
        self._draw_info_panel(recognition_result)
        
        # 更新显示
        pygame.display.flip()
    
    def _draw_grid(self, spacing=50):
        """绘制网格背景"""
        for x in range(0, self.window_width, spacing):
            pygame.draw.line(self.screen, (200, 200, 200), (x, 0), (x, self.window_height))
        for y in range(0, self.window_height, spacing):
            pygame.draw.line(self.screen, (200, 200, 200), (0, y), (self.window_width, y))
    
    def _draw_car(self):
        """绘制小车"""
        # 小车大小
        car_width = 40
        car_height = 20
        
        # 计算小车中心点
        center_x = int(self.x)
        center_y = int(self.y)
        
        # 计算四个角点（考虑旋转）
        rad = math.radians(self.angle)
        cos_a = math.cos(rad)
        sin_a = math.sin(rad)
        
        # 前部中心点（用于显示方向）
        front_x = center_x + cos_a * car_width
        front_y = center_y - sin_a * car_width
        
        # 绘制小车主体（矩形）
        points = [
            (center_x + cos_a * car_width - sin_a * car_height,
             center_y - sin_a * car_width - cos_a * car_height),
            (center_x + cos_a * car_width + sin_a * car_height,
             center_y - sin_a * car_width + cos_a * car_height),
            (center_x - cos_a * car_width + sin_a * car_height,
             center_y + sin_a * car_width + cos_a * car_height),
            (center_x - cos_a * car_width - sin_a * car_height,
             center_y + sin_a * car_width - cos_a * car_height),
        ]
        
        pygame.draw.polygon(self.screen, self.COLOR_CAR, points)
        
        # 绘制方向指示线
        pygame.draw.line(self.screen, (255, 0, 0), (center_x, center_y), (front_x, front_y), 2)
    
    def _draw_info_panel(self, recognition_result=None):
        """绘制信息面板"""
        # 小车状态
        status_text = [
            f'Pos: ({self.x:.0f}, {self.y:.0f})',
            f'Angle: {self.angle:.1f} deg',
            f'Speed: {self.speed:.1f}',
        ]
        
        # 当前指令
        if self.current_command:
            cmd_str = self.current_command.to_string()
            # 中文指令映射英文
            cmd_en_map = {
                '左转': 'Turn Left',
                '右转': 'Turn Right',
                '直行': 'Go Straight',
                '停止': 'Stop',
                '未知': 'Unknown'
            }
            cmd_en = cmd_en_map.get(cmd_str, cmd_str)
            status_text.append(f'Command: {cmd_en}')

        # 识别结果
        if recognition_result:
            class_cn = recognition_result.get("class_name_cn", "Unknown")
            # 中文类别映射英文
            en_map = {
                '左转': 'Left',
                '右转': 'Right',
                '直行': 'Straight',
                '停止': 'Stop',
                '无标志': 'No Sign',
                '未知': 'Unknown'
            }
            class_en = en_map.get(class_cn, class_cn)
            confidence = recognition_result.get('confidence', 0)
            status_text.append(f'Recog: {class_en}')
            status_text.append(f'Conf: {confidence:.2f}')
        
        # 绘制文本
        y_offset = 10
        for text in status_text:
            text_surface = self.font.render(text, True, self.COLOR_TEXT)
            self.screen.blit(text_surface, (10, y_offset))
            y_offset += 30
    
    def handle_events(self):
        # """处理 Pygame 事件"""
        # for event in pygame.event.get():
        #     if event.type == pygame.QUIT:
        #         self.running = False
        #         return False
        #     elif event.type == pygame.KEYDOWN:
        #         print(f"[调试] 按键按下: {event.key}")  # 临时添加
        #         if event.key == pygame.K_ESCAPE:
        #             self.running = False
        #             return False
        #         # ---------- 手动控制按键 ----------
        #         elif event.key == pygame.K_UP:
        #             self._mark_manual_control()
        #             self.execute(Command.GO_STRAIGHT, source='manual')
        #             print("[手动] 直行")
        #         elif event.key == pygame.K_DOWN:
        #             self._mark_manual_control()
        #             self.execute(Command.STOP, source='manual')
        #             print("[手动] 停止")
        #         elif event.key == pygame.K_LEFT:
        #             self._mark_manual_control()
        #             self.execute(Command.TURN_LEFT, source='manual')
        #             print("[手动] 左转")
        #         elif event.key == pygame.K_RIGHT:
        #             self._mark_manual_control()
        #             self.execute(Command.TURN_RIGHT, source='manual')
        #             print("[手动] 右转")
        #         elif event.key == pygame.K_SPACE:
        #             self._mark_manual_control()
        #             self.execute(Command.STOP, source='manual')
        #             print("[手动] 紧急停止")
        """处理 Pygame 事件（支持长按连续转向）"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                    return False
                # 记录按键按下
                elif event.key == pygame.K_UP:
                    self.key_up_pressed = True
                elif event.key == pygame.K_DOWN:
                    self.key_down_pressed = True
                elif event.key == pygame.K_LEFT:
                    self.key_left_pressed = True
                elif event.key == pygame.K_RIGHT:
                    self.key_right_pressed = True
            elif event.type == pygame.KEYUP:
                # 记录按键释放
                if event.key == pygame.K_UP:
                    self.key_up_pressed = False
                elif event.key == pygame.K_DOWN:
                    self.key_down_pressed = False
                elif event.key == pygame.K_LEFT:
                    self.key_left_pressed = False
                elif event.key == pygame.K_RIGHT:
                    self.key_right_pressed = False
        return True
    
    def tick(self, fps=30):
        """控制帧率"""
        if self.clock:
            self.clock.tick(fps)
    
    def close(self):
        """关闭仿真环境"""
        if self.running:
            self.running = False
        pygame.quit()
        print("仿真环境已关闭")
    
    def run_demo(self):
        """运行演示"""
        print("运行仿真演示...")
        print("按 ESC 键退出")
        
        self.init()
        
        # 演示指令序列
        from src.controller import Command
        
        demo_commands = [
            Command.GO_STRAIGHT,
            Command.GO_STRAIGHT,
            Command.TURN_LEFT,
            Command.TURN_LEFT,
            Command.TURN_LEFT,
            Command.GO_STRAIGHT,
            Command.GO_STRAIGHT,
            Command.TURN_RIGHT,
            Command.TURN_RIGHT,
            Command.TURN_RIGHT,
            Command.STOP,
        ]
        
        command_index = 0
        frame_count = 0
        
        while self.running:
            # 处理事件
            if not self.handle_events():
                break
            
            # 执行指令
            if command_index < len(demo_commands):
                command = demo_commands[command_index]
                self.execute(command)
                command_index += 1
            
            # 更新位置
            self.update()
            
            # 渲染
            self.render()
            
            # 控制帧率
            self.tick(30)
            
            frame_count += 1
        
        self.close()
        print(f"演示完成，共运行 {frame_count} 帧")

    def _mark_manual_control(self):
        """标记手动控制时间"""
        self.last_manual_time = time.time()

def test_sim_controller():
    """测试仿真控制器"""
    print("测试仿真控制器...")
    
    controller = SimController()
    controller.run_demo()


if __name__ == "__main__":
    test_sim_controller()
