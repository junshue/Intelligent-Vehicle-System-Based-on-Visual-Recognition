"""
仿真控制器模块
使用 Pygame 创建简易小车仿真环境
"""

import pygame
import math


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
    
    def init(self):
        """初始化 Pygame"""
        pygame.init()
        self.screen = pygame.display.set_mode((self.window_width, self.window_height))
        pygame.display.set_caption('车辆仿真 - Turn Sign Recognition Control')
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.running = True
        
        print("仿真环境已初始化")
    
    def execute(self, command):
        """
        执行控制指令
        
        Args:
            command: Command 枚举
        """
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
        """更新小车位置"""
        # 将角度转换为弧度
        rad = math.radians(self.angle)
        
        # 更新位置
        self.x += math.cos(rad) * self.speed
        self.y -= math.sin(rad) * self.speed
        
        # 边界检查
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
            f'位置：({self.x:.0f}, {self.y:.0f})',
            f'方向：{self.angle:.1f}°',
            f'速度：{self.speed:.1f}',
        ]
        
        # 当前指令
        if self.current_command:
            status_text.append(f'指令：{self.current_command.to_string()}')
        
        # 识别结果
        if recognition_result:
            status_text.append(f'识别：{recognition_result.get("class_name_cn", "未知")}')
            confidence = recognition_result.get('confidence', 0)
            status_text.append(f'置信度：{confidence:.2f}')
        
        # 绘制文本
        y_offset = 10
        for text in status_text:
            text_surface = self.font.render(text, True, self.COLOR_TEXT)
            self.screen.blit(text_surface, (10, y_offset))
            y_offset += 30
    
    def handle_events(self):
        """处理 Pygame 事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                    return False
        
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


def test_sim_controller():
    """测试仿真控制器"""
    print("测试仿真控制器...")
    
    controller = SimController()
    controller.run_demo()


if __name__ == "__main__":
    test_sim_controller()
