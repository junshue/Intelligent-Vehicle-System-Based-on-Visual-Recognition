"""
主程序
集成摄像头、分类器、指令映射和控制器，实现完整的转向标志识别与车辆控制系统

运行模式:
1. 仿真模式：使用 Pygame 仿真小车
2. 串口模式：控制真实 Arduino 小车
3. 演示模式：仅显示识别结果
"""
# 314行镜像翻转（水平翻转）

import cv2
import time
import argparse
import sys
import os
# 改用 PIL 来渲染中文字符
from PIL import ImageFont, ImageDraw, Image
import numpy as np

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.camera import Camera
from src.classifier import Classifier
from src.controller import CommandMapper, Command
from src.sim_controller import SimController
from src.serial_controller import SerialController


   

# # 绘制中文字符
# def draw_chinese_text(img, text, position, font_path="C:/Windows/Fonts/simhei.ttf", 
#                   font_size=30, color=(0, 255, 0)):
#     # """
#     # 在 OpenCV 图像上绘制中文文本
#     # :param img: OpenCV 图像 (numpy array, BGR)
#     # :param text: 要绘制的文本（支持中文）
#     # :param position: 文本左上角坐标 (x, y)
#     # :param font_path: 中文字体文件路径
#     # :param font_size: 字体大小
#     # :param color: 颜色 (B, G, R)
#     # :return: 绘制后的图像
#     # """
#     # # 将 OpenCV 图像转换为 PIL 格式 (BGR -> RGB)
#     # img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
#     # draw = ImageDraw.Draw(img_pil)
    
#     # try:
#     #     font = ImageFont.truetype(font_path, font_size)
#     # except:
#     #     # 如果找不到字体，使用默认字体（可能不支持中文，但至少不会崩溃）
#     #     font = ImageFont.load_default()
    
#     # # 注意：PIL 的 color 参数是 RGB 顺序，而 OpenCV 是 BGR，所以需要反转
#     # pil_color = (color[2], color[1], color[0])
#     # draw.text(position, text, font=font, fill=pil_color)

#     # # 转回 OpenCV 格式
#     # return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
#     """
#     在图像上绘制识别结果（使用英文显示，避免字体问题）
#     """
#     # 获取中文类别并转换为英文简写
#     class_name_cn = prediction.get('class_name_cn', '未知')
#     en_label = {
#         '左转': 'Left',
#         '右转': 'Right',
#         '直行': 'Straight',
#         '停止': 'Stop',
#         '无标志': 'NoSign',
#         '未知': 'Unknown'
#     }.get(class_name_cn, class_name_cn)
#     confidence = prediction.get('confidence', 0)
#     # 根据置信度设置颜色
#     if confidence > 0.7:
#         color = (0, 255, 0)      # 绿色
#     elif confidence > 0.5:
#         color = (0, 255, 255)    # 黄色
#     else:
#         color = (0, 0, 255)      # 红色
#     height, width = frame.shape[:2]
#     # 绘制红框（保持原样）
#     cv2.rectangle(frame, (10, 10), (width - 10, 80), color, 2)
#     # 绘制英文类别（大号）
#     cv2.putText(frame, en_label, (20, 45),
#                 cv2.FONT_HERSHEY_SIMPLEX, 1.2, color, 2)
#     # 绘制置信度
#     cv2.putText(frame, f'{confidence:.2f}', (20, 75),
#                 cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
#     # 绘制控制指令（将中文"指令："替换为"Cmd:"）
#     cmd_text = f'Cmd: {command.to_string()}'
#     cv2.putText(frame, cmd_text, (20, height - 20),
#                 cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)
#     # 绘制 FPS
#     fps = self.camera.get_fps()
#     cv2.putText(frame, f'FPS: {fps:.1f}', (width - 120, 30),
#                 cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)



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
        self.command_mapper = CommandMapper(window_size=8, confidence_threshold=0.75, min_consensus=6)
        
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
        """
        在图像上绘制识别结果（纯英文，100% 可靠）
        """
        # 获取中文类别并转为英文
        class_name_cn = prediction.get('class_name_cn', '未知')
        en_map = {
            '左转': 'Left',
            '右转': 'Right',
            '直行': 'Straight',
            '停止': 'Stop',
            '无标志': 'No Sign',
            '未知': 'Unknown'
        }
        en_label = en_map.get(class_name_cn, class_name_cn)
        
        confidence = prediction.get('confidence', 0)
        
        # 根据置信度设置颜色
        if confidence > 0.7:
            color = (0, 255, 0)      # 绿色
        elif confidence > 0.5:
            color = (0, 255, 255)    # 黄色
        else:
            color = (0, 0, 255)      # 红色
        
        height, width = frame.shape[:2]
        
        # 绘制红框
        cv2.rectangle(frame, (10, 10), (width - 10, 80), color, 2)
        
        # 绘制英文类别
        cv2.putText(frame, en_label, (20, 45),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, color, 2)
        
        # 绘制置信度
        cv2.putText(frame, f'{confidence:.2f}', (20, 75),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
        
        # 绘制控制指令
        # cmd_text = f'Cmd: {command.to_string()}'
        # cv2.putText(frame, cmd_text, (20, height - 20),
        #             cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)
        cmd_cn = command.to_string()
        cmd_en_map = {
            '左转': 'Turn Left',
            '右转': 'Turn Right',
            '直行': 'Go Straight',
            '停止': 'Stop',
            '未知': 'Unknown'
        }
        cmd_en = cmd_en_map.get(cmd_cn, cmd_cn)
        cmd_text = f'Cmd: {cmd_en}'
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
            # 先处理 Pygame 事件，确保响应及时
            if self.mode == 'simulation' and self.sim_controller:
                if not self.sim_controller.handle_events():
                    break
            # 读取帧
            frame = self.camera.read()
            
            if frame is None:
                print("警告：无法读取摄像头帧")
                time.sleep(0.1)
                continue
            
            # 镜像翻转（水平翻转）参数 1 表示水平翻转，0 表示垂直翻转，-1 表示同时水平和垂直翻转。
            frame = cv2.flip(frame, 1)

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
