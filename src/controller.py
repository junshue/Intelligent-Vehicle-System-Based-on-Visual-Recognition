"""
控制指令模块
定义控制指令枚举和指令映射器
"""

from enum import Enum
from collections import deque
import numpy as np


class Command(Enum):
    """
    车辆控制指令枚举
    """
    TURN_LEFT = 0      # 左转
    TURN_RIGHT = 1     # 右转
    GO_STRAIGHT = 2    # 直行
    STOP = 3          # 停止
    UNKNOWN = 4       # 未知/等待
    
    @staticmethod
    def from_class_name(class_name):
        """
        从识别类别名称转换为控制指令
        
        Args:
            class_name: 识别类别名称 (left, right, straight, stop, background)
            
        Returns:
            Command: 对应的控制指令
        """
        mapping = {
            'left': Command.TURN_LEFT,
            'right': Command.TURN_RIGHT,
            'straight': Command.GO_STRAIGHT,
            'stop': Command.STOP,
            'background': Command.STOP,  # 无标志时停车
            'unknown': Command.UNKNOWN
        }
        return mapping.get(class_name, Command.UNKNOWN)
    
    def to_string(self):
        """转换为中文字符串"""
        names = {
            Command.TURN_LEFT: '左转',
            Command.TURN_RIGHT: '右转',
            Command.GO_STRAIGHT: '直行',
            Command.STOP: '停止',
            Command.UNKNOWN: '未知'
        }
        return names.get(self, '未知')
    
    def to_char(self):
        """
        转换为串口发送字符
        用于真实小车控制
        """
        chars = {
            Command.TURN_LEFT: 'L',
            Command.TURN_RIGHT: 'R',
            Command.GO_STRAIGHT: 'F',
            Command.STOP: 'S',
            Command.UNKNOWN: 'U'
        }
        return chars.get(self, 'U')


class CommandMapper:
    """
    指令映射器
    将识别结果映射为控制指令，并实现滑动窗口平滑滤波
    """
    
    def __init__(self, window_size=5, confidence_threshold=0.5, min_consensus=3):
        """
        初始化指令映射器
        
        Args:
            window_size: 滑动窗口大小（帧数）
            confidence_threshold: 置信度阈值，低于此值视为不可靠
            min_consensus: 最小一致帧数，窗口内至少有多少帧一致才输出指令
        """
        self.window_size = window_size
        self.confidence_threshold = confidence_threshold
        self.min_consensus = min_consensus
        
        # 滑动窗口
        self.prediction_window = deque(maxlen=window_size)
        
        # 当前指令
        self.current_command = Command.UNKNOWN
        
        # 统计信息
        self.total_frames = 0
        self.command_changes = 0
    
    def map(self, prediction):
        """
        将识别结果映射为控制指令
        
        Args:
            prediction: 分类器预测结果字典，包含:
                - class_id: 类别 ID
                - class_name: 类别名称
                - confidence: 置信度
                
        Returns:
            Command: 映射后的控制指令
        """
        self.total_frames += 1
        
        # 检查置信度
        if prediction['confidence'] < self.confidence_threshold:
            # 置信度太低，使用未知指令
            self.prediction_window.append({
                'command': Command.UNKNOWN,
                'confidence': prediction['confidence']
            })
        else:
            # 转换为控制指令
            command = Command.from_class_name(prediction['class_name'])
            self.prediction_window.append({
                'command': command,
                'confidence': prediction['confidence']
            })
        
        # 滑动窗口投票
        command = self._vote()
        
        # 记录指令变化
        if command != self.current_command:
            self.command_changes += 1
            self.current_command = command
        
        return command
    
    def _vote(self):
        """
        滑动窗口投票机制
        
        Returns:
            Command: 投票结果
        """
        if len(self.prediction_window) == 0:
            return Command.UNKNOWN
        
        # 统计各指令出现次数
        command_counts = {}
        for item in self.prediction_window:
            cmd = item['command']
            if cmd not in command_counts:
                command_counts[cmd] = 0
            command_counts[cmd] += 1
        
        # 找到出现次数最多的指令
        max_count = 0
        max_command = Command.UNKNOWN
        
        for cmd, count in command_counts.items():
            if count > max_count:
                max_count = count
                max_command = cmd
        
        # 检查是否达到最小一致帧数
        if max_count >= self.min_consensus:
            return max_command
        else:
            # 未达到一致，保持上一个可靠指令或返回未知
            return self.current_command if self.current_command != Command.UNKNOWN else Command.UNKNOWN
    
    def get_current_command(self):
        """获取当前指令"""
        return self.current_command
    
    def reset(self):
        """重置映射器状态"""
        self.prediction_window.clear()
        self.current_command = Command.UNKNOWN
        self.total_frames = 0
        self.command_changes = 0
    
    def get_stats(self):
        """
        获取统计信息
        
        Returns:
            stats: 统计信息字典
        """
        return {
            'total_frames': self.total_frames,
            'command_changes': self.command_changes,
            'window_size': self.window_size,
            'current_command': self.current_command
        }


def test_command_mapper():
    """测试指令映射器"""
    print("测试指令映射器...")
    
    # 创建映射器
    mapper = CommandMapper(window_size=5, confidence_threshold=0.5, min_consensus=3)
    
    # 模拟预测结果
    test_predictions = [
        {'class_name': 'left', 'confidence': 0.9},
        {'class_name': 'left', 'confidence': 0.85},
        {'class_name': 'right', 'confidence': 0.6},  # 误识别
        {'class_name': 'left', 'confidence': 0.88},
        {'class_name': 'left', 'confidence': 0.92},
        {'class_name': 'straight', 'confidence': 0.7},
        {'class_name': 'left', 'confidence': 0.87},
    ]
    
    print("\n模拟识别结果序列:")
    print("-" * 60)
    
    for i, pred in enumerate(test_predictions):
        command = mapper.map(pred)
        print(f"帧 {i+1}: {pred['class_name']:10s} (置信度：{pred['confidence']:.2f}) "
              f"→ 指令：{command.to_string()}")
    
    print("-" * 60)
    print(f"\n统计信息：{mapper.get_stats()}")
    
    print("\n指令映射器测试完成！")


if __name__ == "__main__":
    test_command_mapper()
