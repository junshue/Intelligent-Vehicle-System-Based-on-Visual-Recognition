"""
分类器推理模块
提供训练好的模型的推理功能
"""

import os
import cv2
import numpy as np
import torch
import torch.nn as nn
from torchvision import transforms
from PIL import Image


class TurnSignClassifierModel(nn.Module):
    """
    转向标志分类模型
    基于 MobileNetV2
    """
    
    def __init__(self, num_classes=5):
        """
        初始化模型
        
        Args:
            num_classes: 分类类别数
        """
        super(TurnSignClassifierModel, self).__init__()
        
        # 加载 MobileNetV2（不使用预训练权重）
        self.mobilenet = torch.hub.load(
            'pytorch/vision:v0.10.0',
            'mobilenet_v2',
            pretrained=False
        )
        
        # 替换分类头
        num_features = self.mobilenet.classifier[1].in_features
        self.mobilenet.classifier = nn.Sequential(
            nn.Dropout(p=0.2),
            nn.Linear(num_features, num_classes)
        )
    
    def forward(self, x):
        """前向传播"""
        return self.mobilenet(x)


class Classifier:
    """
    分类器推理类
    提供简单易用的预测接口
    """
    
    def __init__(self, model_path='checkpoints/best_model.pth', device=None):
        """
        初始化分类器
        
        Args:
            model_path: 模型权重文件路径
            device: 计算设备，默认自动选择
        """
        self.model_path = model_path
        
        # 自动选择设备
        if device is None:
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        else:
            self.device = device
        
        # 加载模型
        self.model = None
        self.class_names = None
        self._load_model()
        
        # 图像预处理
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        
        print(f"分类器已初始化，设备：{self.device}")
    
    def _load_model(self):
        """加载模型权重"""
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"模型文件不存在：{self.model_path}")
        
        # 加载检查点
        checkpoint = torch.load(self.model_path, map_location=self.device)
        
        # 获取类别数
        class_names = checkpoint.get('class_names', ['left', 'right', 'straight', 'stop', 'background'])
        num_classes = len(class_names)
        
        # 创建模型
        self.model = TurnSignClassifierModel(num_classes=num_classes)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.model.to(self.device)
        self.model.eval()
        
        self.class_names = class_names
        
        print(f"模型已加载：{self.model_path}")
        print(f"类别：{self.class_names}")
    
    def predict(self, frame):
        """
        对单帧图像进行预测
        
        Args:
            frame: OpenCV 格式的图像帧 (BGR 格式)
            
        Returns:
            prediction: 字典，包含以下字段:
                - class_id: 类别 ID
                - class_name: 类别名称（中文）
                - confidence: 置信度
        """
        # BGR 转 RGB
        if len(frame.shape) == 3 and frame.shape[2] == 3:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        else:
            frame_rgb = frame
        
        # OpenCV 转 PIL
        image = Image.fromarray(frame_rgb)
        
        # 预处理
        image_tensor = self.transform(image).unsqueeze(0).to(self.device)
        
        # 推理
        with torch.no_grad():
            outputs = self.model(image_tensor)
            probabilities = torch.nn.functional.softmax(outputs, dim=1)
            confidence, predicted = torch.max(probabilities, 1)
        
        # 获取结果
        class_id = predicted.item()
        confidence = confidence.item()
        class_name = self.class_names[class_id] if class_id < len(self.class_names) else 'unknown'
        
        # 中文映射
        class_name_cn = {
            'left': '左转',
            'right': '右转',
            'straight': '直行',
            'stop': '停止',
            'background': '无标志',
            'unknown': '未知'
        }.get(class_name, class_name)
        
        return {
            'class_id': class_id,
            'class_name': class_name,
            'class_name_cn': class_name_cn,
            'confidence': confidence
        }
    
    def predict_batch(self, frames):
        """
        对一批图像进行预测
        
        Args:
            frames: 图像帧列表
            
        Returns:
            predictions: 预测结果列表
        """
        predictions = []
        for frame in frames:
            pred = self.predict(frame)
            predictions.append(pred)
        return predictions
    
    def get_class_names(self):
        """获取类别名称列表"""
        return self.class_names


def test_classifier():
    """测试分类器"""
    print("测试分类器...")
    
    # 检查模型文件
    model_path = 'checkpoints/best_model.pth'
    if not os.path.exists(model_path):
        print(f"错误：模型文件不存在：{model_path}")
        print("请先运行训练脚本 train.py")
        return
    
    # 创建分类器
    classifier = Classifier(model_path=model_path)
    
    # 测试图像
    test_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    
    # 预测
    prediction = classifier.predict(test_image)
    
    print(f"\n预测结果:")
    print(f"  类别 ID: {prediction['class_id']}")
    print(f"  类别名称：{prediction['class_name']}")
    print(f"  中文名称：{prediction['class_name_cn']}")
    print(f"  置信度：{prediction['confidence']:.4f}")
    
    print("\n分类器测试完成！")


if __name__ == "__main__":
    test_classifier()
