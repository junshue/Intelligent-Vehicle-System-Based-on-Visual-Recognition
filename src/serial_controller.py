"""
串口控制器模块
通过 PySerial 发送控制指令到真实小车（如 Arduino）
"""

import serial
import serial.tools.list_ports
import time


class SerialController:
    """
    串口控制器
    用于向 Arduino 等微控制器发送控制指令
    """
    
    def __init__(self, port=None, baudrate=9600, timeout=1):
        """
        初始化串口控制器
        
        Args:
            port: 串口端口，如 'COM3' (Windows) 或 '/dev/ttyUSB0' (Linux)
                  如果为 None，将自动搜索
            baudrate: 波特率，默认 9600
            timeout: 超时时间（秒）
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        
        # 串口对象
        self.serial = None
        self.connected = False
        
        # 可用端口列表
        self.available_ports = []
    
    def list_ports(self):
        """
        列出所有可用的串口端口
        
        Returns:
            ports: 可用端口信息列表
        """
        self.available_ports = list(serial.tools.list_ports.comports())
        
        print("可用串口端口:")
        for i, port in enumerate(self.available_ports):
            print(f"  {i}: {port.device} - {port.description}")
        
        return self.available_ports
    
    def connect(self, port=None):
        """
        连接到串口
        
        Args:
            port: 指定端口，如果不指定则使用初始化时的 port 参数
            
        Returns:
            bool: 连接是否成功
        """
        if port:
            self.port = port
        
        if not self.port:
            print("错误：未指定串口端口")
            self.list_ports()
            return False
        
        try:
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout
            )
            self.connected = True
            print(f"已连接到串口：{self.port} @ {self.baudrate}")
            return True
            
        except serial.SerialException as e:
            print(f"连接失败：{e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """断开串口连接"""
        if self.serial and self.serial.is_open:
            self.serial.close()
            self.connected = False
            print("已断开串口连接")
    
    def send_command(self, command):
        """
        发送控制指令
        
        Args:
            command: Command 枚举
            
        Returns:
            bool: 发送是否成功
        """
        if not self.connected:
            print("错误：串口未连接")
            return False
        
        try:
            # 转换为字符并发送
            char = command.to_char()
            self.serial.write(char.encode())
            print(f"发送指令：{command.to_string()} ({char})")
            return True
            
        except serial.SerialException as e:
            print(f"发送失败：{e}")
            return False
    
    def send_custom(self, data):
        """
        发送自定义数据
        
        Args:
            data: 要发送的字符串或字节
            
        Returns:
            bool: 发送是否成功
        """
        if not self.connected:
            print("错误：串口未连接")
            return False
        
        try:
            if isinstance(data, str):
                self.serial.write(data.encode())
            else:
                self.serial.write(data)
            return True
            
        except serial.SerialException as e:
            print(f"发送失败：{e}")
            return False
    
    def read_response(self, size=1):
        """
        读取响应数据
        
        Args:
            size: 读取字节数
            
        Returns:
            data: 读取的数据，失败返回 None
        """
        if not self.connected:
            return None
        
        try:
            if self.serial.in_waiting > 0:
                data = self.serial.read(size)
                return data
            return None
            
        except serial.SerialException as e:
            print(f"读取失败：{e}")
            return None
    
    def is_connected(self):
        """检查是否已连接"""
        return self.connected and self.serial and self.serial.is_open
    
    def test_connection(self):
        """测试连接"""
        if not self.is_connected():
            print("串口未连接")
            return False
        
        # 发送测试字符
        self.send_custom("TEST\n")
        time.sleep(0.1)
        
        print("连接测试完成")
        return True


def test_serial_controller():
    """测试串口控制器"""
    print("测试串口控制器...")
    print("=" * 60)
    
    # 创建控制器
    controller = SerialController()
    
    # 列出可用端口
    print("\n步骤 1: 列出可用端口")
    controller.list_ports()
    
    # 提示用户
    print("\n" + "=" * 60)
    print("如果没有连接真实小车，此模块将跳过实际测试")
    print("\n要测试真实小车控制，请:")
    print("1. 连接 Arduino 小车到电脑")
    print("2. 记下端口号（如 COM3）")
    print("3. 运行以下代码:")
    print("\n   controller = SerialController()")
    print("   controller.connect('COM3')  # 替换为你的端口")
    print("   controller.send_command(Command.TURN_LEFT)")
    print("=" * 60)
    
    # 模拟发送指令（不实际连接）
    print("\n模拟指令发送:")
    from src.controller import Command
    
    test_commands = [
        Command.TURN_LEFT,
        Command.TURN_RIGHT,
        Command.GO_STRAIGHT,
        Command.STOP
    ]
    
    for cmd in test_commands:
        print(f"  指令：{cmd.to_string():6s} → 字符：{cmd.to_char()}")
    
    print("\n串口控制器测试完成！")


if __name__ == "__main__":
    test_serial_controller()
