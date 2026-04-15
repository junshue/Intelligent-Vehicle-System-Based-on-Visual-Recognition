"""
摄像头捕获模块
支持多线程读取摄像头帧，减少主线程阻塞
"""

import cv2
import threading
import time
from collections import deque


class Camera:
    """
    摄像头捕获类
    使用独立线程读取摄像头帧，提高实时性能
    """
    
    def __init__(self, camera_id=0, width=640, height=480, fps=30):
        """
        初始化摄像头
        
        Args:
            camera_id: 摄像头 ID，默认 0（内置摄像头）
            width: 帧宽度，默认 640
            height: 帧高度，默认 480
            fps: 帧率，默认 30
        """
        self.camera_id = camera_id
        self.width = width
        self.height = height
        self.fps = fps
        
        # 摄像头对象
        self.cap = None
        
        # 最新帧
        self.frame = None
        self.frame_timestamp = 0
        
        # 线程控制
        self.running = False
        self.thread = None
        
        # 帧率统计
        self.frame_count = 0
        self.start_time = 0
        self.current_fps = 0
        
        # 帧队列（用于平滑处理）
        self.frame_queue = deque(maxlen=5)
    
    def start(self):
        """启动摄像头读取线程"""
        if self.running:
            print("摄像头已经在运行")
            return
        
        # 打开摄像头
        self.cap = cv2.VideoCapture(self.camera_id)
        
        if not self.cap.isOpened():
            raise RuntimeError(f"无法打开摄像头：{self.camera_id}")
        
        # 设置参数
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self.cap.set(cv2.CAP_PROP_FPS, self.fps)
        
        # 获取实际参数
        actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        actual_fps = int(self.cap.get(cv2.CAP_PROP_FPS))
        
        print(f"摄像头已打开:")
        print(f"  分辨率：{actual_width}x{actual_height}")
        print(f"  帧率：{actual_fps}")
        
        # 启动线程
        self.running = True
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()
        
        # 等待第一帧
        time.sleep(0.1)
        
        print("摄像头读取线程已启动")
    
    def _capture_loop(self):
        """摄像头读取循环（在独立线程中运行）"""
        self.start_time = time.time()
        
        while self.running:
            ret, frame = self.cap.read()
            
            if not ret:
                print("警告：无法读取摄像头帧")
                time.sleep(0.01)
                continue
            
            # 更新帧
            self.frame = frame
            self.frame_timestamp = time.time()
            self.frame_count += 1
            
            # 添加到队列
            self.frame_queue.append(frame)
            
            # 计算 FPS
            elapsed = time.time() - self.start_time
            if elapsed > 1.0:
                self.current_fps = self.frame_count / elapsed
                self.frame_count = 0
                self.start_time = time.time()
            
            # 短暂休眠，避免过度占用 CPU
            time.sleep(0.001)
    
    def read(self):
        """
        读取最新帧
        
        Returns:
            frame: 摄像头帧，如果未启动则返回 None
        """
        if not self.running:
            return None
        return self.frame
    
    def read_with_timestamp(self):
        """
        读取最新帧及时间戳
        
        Returns:
            frame: 摄像头帧
            timestamp: 时间戳
        """
        if not self.running:
            return None, 0
        return self.frame, self.frame_timestamp
    
    def get_fps(self):
        """获取当前帧率"""
        return self.current_fps
    
    def is_opened(self):
        """检查摄像头是否已打开"""
        return self.running and self.cap is not None and self.cap.isOpened()
    
    def stop(self):
        """停止摄像头读取线程"""
        if not self.running:
            return
        
        print("正在停止摄像头...")
        self.running = False
        
        if self.thread:
            self.thread.join(timeout=1.0)
        
        if self.cap:
            self.cap.release()
        
        print("摄像头已停止")
    
    def __enter__(self):
        """上下文管理器入口"""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.stop()


def test_camera():
    """测试摄像头"""
    print("测试摄像头...")
    
    try:
        # 创建摄像头对象
        camera = Camera(camera_id=0, width=640, height=480)
        
        # 启动摄像头
        camera.start()
        
        print("\n按 'q' 键退出测试...")
        
        # 显示帧
        while True:
            frame = camera.read()
            
            if frame is not None:
                # 显示 FPS
                fps = camera.get_fps()
                cv2.putText(frame, f'FPS: {fps:.1f}', (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                
                # 显示
                cv2.imshow('Camera Test', frame)
            
            # 检查按键
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        # 清理
        camera.stop()
        cv2.destroyAllWindows()
        
        print("摄像头测试完成！")
        
    except Exception as e:
        print(f"错误：{e}")
        print("\n如果摄像头无法打开，请检查:")
        print("1. 摄像头是否已连接")
        print("2. 摄像头驱动是否已安装")
        print("3. 是否有其他程序正在使用摄像头")
        print("4. 可以尝试修改 camera_id 参数（如 1, 2 等）")


if __name__ == "__main__":
    test_camera()
