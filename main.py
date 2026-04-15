"""
主程序
集成摄像头、分类器、指令映射和控制器，实现完整的转向标志识别与车辆控制系统

运行模式:
1. 仿真模式：使用 Pygame 仿真小车
2. 串口模式：控制真实 Arduino 小车
3. 演示模式：仅显示识别结果
"""

import cv2
import time
import argparse
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.camera import Camera
from src.classifier import Classifier
from src.controller import CommandMapper, Command
from src.sim_controller import SimController
from src.serial_controller import SerialController


class TurnSignSystem:
    """
    转向标志识别与车辆控制系统主类
    """
    
    def __init__(self, mode='simulation', model_path='checkpoints/best_model.pth', 
                 camera_id=0, serial_port=None):
        """
        初始化系统
        
        Args:
            mode: 运行模式 ('simulation', 'serial', 'demo')
            model_path: 模型文件路径
            camera_id: 摄像头 ID
            serial_port: 串口端口（仅在 serial 模式下使用）
        """
        self.mode = mode
        self.model_path = model_path
        self.camera_id = camera_id
        self.serial_port = serial_port
        
        # 组件
        self.camera = None
        self.classifier = None
        self.command_mapper = None
        self.sim_controller = None
        self.serial_controller = None
        
        # 系统状态
        self.running = False
        self.start_time = 0
        
        # 统计信息
        self.stats = {
            'total_frames': 0,
            'recognized_frames': 0,
            'command_changes': 0,
            'start_time': 0
        }
        
        # 日志记录
        self.log_enabled = False
        self.log_file = None
    
    def initialize(self):
        """初始化所有组件"""
        print("=" * 60)
        print("转向标志识别与车辆控制系统")
        print("=" * 60)
        print(f"运行模式：{self.mode}")
        print(f"模型路径：{self.model_path}")
        print(f"摄像头 ID: {self.camera_id}")
        print()
        
        # 初始化摄像头
        print("初始化摄像头...")
        self.camera = Camera(camera_id=self.camera_id, width=640, height=480)
        self.camera.start()
        time.sleep(0.5)  # 等待摄像头启动
        
        # 初始化分类器
        print("初始化分类器...")
        try:
            self.classifier = Classifier(model_path=self.model_path)
        except FileNotFoundError as e:
            print(f"错误：{e}")
            print("\n请先训练模型:")
            print("  python train.py")
            return False
        
        # 初始化指令映射器
        print("初始化指令映射器...")
        self.command_mapper = CommandMapper(window_size=5, confidence_threshold=0.5, min_consensus=3)
        
        # 根据模式初始化控制器
        if self.mode == 'simulation':
            print("初始化仿真控制器...")
            self.sim_controller = SimController()
            self.sim_controller.init()
        elif self.mode == 'serial':
            print("初始化串口控制器...")
            self.serial_controller = SerialController(port=self.serial_port)
            if not self.serial_controller.connect():
                print("警告：串口连接失败，将使用演示模式")
                self.mode = 'demo'
        
        # 日志记录
        if self.log_enabled:
            self._open_log_file()
        
        print("\n系统初始化完成")
        print("=" * 60)
        return True
    
    def _open_log_file(self):
        """打开日志文件"""
        log_dir = 'logs'
        os.makedirs(log_dir, exist_ok=True)
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        log_path = os.path.join(log_dir, f'recognition_{timestamp}.log')
        self.log_file = open(log_path, 'w', encoding='utf-8')
        print(f"日志文件：{log_path}")
    
    def _write_log(self, message):
        """写入日志"""
        if self.log_enabled and self.log_file:
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            self.log_file.write(f"[{timestamp}] {message}\n")
            self.log_file.flush()
    
    def process_frame(self, frame):
        """
        处理单帧图像
        
        Args:
            frame: 摄像头帧
            
        Returns:
            prediction: 识别结果
            command: 控制指令
        """
        # 识别
        prediction = self.classifier.predict(frame)
        
        # 映射指令
        command = self.command_mapper.map(prediction)
        
        # 更新统计
        self.stats['total_frames'] += 1
        if prediction['confidence'] > 0.5:
            self.stats['recognized_frames'] += 1
        
        return prediction, command
    
    def draw_results(self, frame, prediction, command):
        """
        在图像上绘制识别结果
        
        Args:
            frame: 摄像头帧
            prediction: 识别结果
            command: 控制指令
        """
        # 识别结果
        class_name_cn = prediction.get('class_name_cn', '未知')
        confidence = prediction.get('confidence', 0)
        
        # 根据置信度设置颜色
        if confidence > 0.7:
            color = (0, 255, 0)  # 绿色 - 高置信度
        elif confidence > 0.5:
            color = (0, 255, 255)  # 黄色 - 中等置信度
        else:
            color = (0, 0, 255)  # 红色 - 低置信度
        
        # 绘制识别结果框
        height, width = frame.shape[:2]
        cv2.rectangle(frame, (10, 10), (width - 10, 80), color, 2)
        
        # 绘制文字
        cv2.putText(frame, f'{class_name_cn}', (20, 40),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
        cv2.putText(frame, f'{confidence:.2f}', (20, 70),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        
        # 绘制控制指令
        cmd_text = f'指令：{command.to_string()}'
        cv2.putText(frame, cmd_text, (20, height - 20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)
        
        # 绘制 FPS
        fps = self.camera.get_fps()
        cv2.putText(frame, f'FPS: {fps:.1f}', (width - 120, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    
    def run(self):
        """运行系统主循环"""
        if not self.running:
            self.running = True
            self.start_time = time.time()
            self.stats['start_time'] = self.start_time
        
        print("\n系统运行中...")
        print("按 'q' 键退出")
        print("=" * 60)
        
        while self.running:
            # 读取帧
            frame = self.camera.read()
            
            if frame is None:
                print("警告：无法读取摄像头帧")
                time.sleep(0.1)
                continue
            
            # 处理帧
            prediction, command = self.process_frame(frame)
            
            # 绘制结果
            self.draw_results(frame, prediction, command)
            
            # 执行控制
            if self.mode == 'simulation':
                self.sim_controller.execute(command)
                self.sim_controller.update()
                self.sim_controller.render({
                    'class_name_cn': prediction.get('class_name_cn', '未知'),
                    'confidence': prediction.get('confidence', 0)
                })
                
                # 处理仿真器事件
                if not self.sim_controller.handle_events():
                    break
                    
            elif self.mode == 'serial':
                # 发送指令到串口
                if self.serial_controller and self.serial_controller.is_connected():
                    self.serial_controller.send_command(command)
            
            # 写入日志
            if self.log_enabled:
                self._write_log(f"识别：{prediction.get('class_name', 'unknown')}, "
                              f"置信度：{prediction.get('confidence', 0):.3f}, "
                              f"指令：{command.name}")
            
            # 显示图像
            cv2.imshow('Turn Sign Recognition', frame)
            
            # 检查按键
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('l'):
                # 切换日志记录
                self.log_enabled = not self.log_enabled
                if self.log_enabled:
                    self._open_log_file()
                else:
                    if self.log_file:
                        self.log_file.close()
                        self.log_file = None
        
        # 停止
        self.stop()
    
    def stop(self):
        """停止系统"""
        print("\n正在停止系统...")
        
        self.running = False
        
        # 打印统计信息
        elapsed_time = time.time() - self.start_time
        if elapsed_time > 0:
            print(f"\n运行统计:")
            print(f"  总帧数：{self.stats['total_frames']}")
            print(f"  识别帧数：{self.stats['recognized_frames']}")
            print(f"  识别率：{self.stats['recognized_frames']/self.stats['total_frames']*100:.1f}%")
            print(f"  运行时间：{elapsed_time:.1f}s")
            print(f"  平均 FPS: {self.stats['total_frames']/elapsed_time:.1f}")
        
        # 清理资源
        if self.camera:
            self.camera.stop()
        
        if self.sim_controller:
            self.sim_controller.close()
        
        if self.serial_controller:
            self.serial_controller.disconnect()
        
        if self.log_file:
            self.log_file.close()
        
        cv2.destroyAllWindows()
        
        print("\n系统已停止")


def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='转向标志识别与车辆控制系统')
    parser.add_argument('--mode', type=str, default='demo',
                       choices=['simulation', 'serial', 'demo'],
                       help='运行模式：simulation (仿真), serial (串口), demo (仅演示)')
    parser.add_argument('--model', type=str, default='checkpoints/best_model.pth',
                       help='模型文件路径')
    parser.add_argument('--camera', type=int, default=0,
                       help='摄像头 ID')
    parser.add_argument('--port', type=str, default=None,
                       help='串口端口 (如 COM3)')
    
    args = parser.parse_args()
    
    # 创建系统
    system = TurnSignSystem(
        mode=args.mode,
        model_path=args.model,
        camera_id=args.camera,
        serial_port=args.port
    )
    
    # 初始化
    if not system.initialize():
        return
    
    # 运行
    try:
        system.run()
    except KeyboardInterrupt:
        print("\n用户中断")
        system.stop()


if __name__ == "__main__":
    main()
