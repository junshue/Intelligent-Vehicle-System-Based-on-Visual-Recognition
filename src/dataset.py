"""
数据集加载模块
提供交通标志数据集的加载、预处理和数据增强功能
"""

import os
import cv2
import numpy as np
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
from PIL import Image
import random


class TurnSignDataset(Dataset):
    """
    转向标志数据集类
    
    支持以下类别:
    - left: 左转标志 (0)
    - right: 右转标志 (1)
    - straight: 直行标志 (2)
    - stop: 停止标志 (3)
    - background: 背景/无标志 (4)
    """
    
    def __init__(self, root_dir, img_size=(224, 224), augment=False):
        """
        初始化数据集
        
        Args:
            root_dir: 数据集根目录路径
            img_size: 图像大小，默认 224x224
            augment: 是否使用数据增强
        """
        self.root_dir = root_dir
        self.img_size = img_size
        self.augment = augment
        
        # 类别映射
        self.class_names = ['left', 'right', 'straight', 'stop', 'background']
        self.class_to_idx = {name: idx for idx, name in enumerate(self.class_names)}
        
        # 加载所有图像路径和标签
        self.images = []
        self.labels = []
        
        self._load_images()
        
        # 数据增强变换
        if augment:
            self.transform = transforms.Compose([
                transforms.RandomRotation(15),  # 随机旋转±15 度
                transforms.ColorJitter(brightness=0.3, contrast=0.3, saturation=0.3),  # 亮度、对比度、饱和度调整
                transforms.RandomHorizontalFlip(),  # 随机水平翻转
                transforms.Resize(img_size),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
            ])
        else:
            self.transform = transforms.Compose([
                transforms.Resize(img_size),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
            ])
    
    def _load_images(self):
        """加载所有图像文件"""
        for class_name in self.class_names:
            class_dir = os.path.join(self.root_dir, class_name)
            if not os.path.exists(class_dir):
                print(f"警告：目录 {class_dir} 不存在，跳过")
                continue
            
            for img_name in os.listdir(class_dir):
                if img_name.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')):
                    img_path = os.path.join(class_dir, img_name)
                    self.images.append(img_path)
                    self.labels.append(self.class_to_idx[class_name])
        
        print(f"数据集加载完成：共 {len(self.images)} 张图像")
    
    def __len__(self):
        """返回数据集大小"""
        return len(self.images)
    
    def __getitem__(self, idx):
        """
        获取指定索引的图像和标签
        
        Args:
            idx: 图像索引
            
        Returns:
            image: 变换后的图像张量
            label: 类别标签
        """
        img_path = self.images[idx]
        label = self.labels[idx]
        
        # 使用 PIL 打开图像（兼容各种格式）
        image = Image.open(img_path).convert('RGB')
        
        # 应用变换
        image = self.transform(image)
        
        return image, label
    
    def get_class_weights(self):
        """
        计算类别权重，用于处理类别不平衡
        
        Returns:
            class_weights: 每个类别的权重列表
        """
        class_counts = [0] * len(self.class_names)
        for label in self.labels:
            class_counts[label] += 1
        
        # 计算权重：总样本数 / (类别数 * 该类样本数)
        total = sum(class_counts)
        class_weights = [total / (len(self.class_names) * count) if count > 0 else 1.0 
                         for count in class_counts]
        
        return class_weights
    
    def get_class_names(self):
        """获取类别名称列表"""
        return self.class_names


def create_data_loaders(train_dir, val_dir, batch_size=32, img_size=(224, 224)):
    """
    创建训练和验证数据加载器
    
    Args:
        train_dir: 训练集目录
        val_dir: 验证集目录
        batch_size: 批次大小
        img_size: 图像大小
        
    Returns:
        train_loader: 训练数据加载器
        val_loader: 验证数据加载器
        class_names: 类别名称列表
    """
    # 创建数据集
    train_dataset = TurnSignDataset(train_dir, img_size=img_size, augment=True)
    val_dataset = TurnSignDataset(val_dir, img_size=img_size, augment=False)
    
    # 获取类别权重（用于处理类别不平衡）
    class_weights = train_dataset.get_class_weights()
    
    # 创建数据加载器
    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=0,  # Windows 上建议设为 0
        pin_memory=True
    )
    
    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=0,
        pin_memory=True
    )
    
    return train_loader, val_loader, train_dataset.get_class_names(), class_weights


def download_gtsrb_subset(output_dir, classes=['Left', 'Right', 'Ahead']):
    """
    下载 GTSRB 数据集的子集（左转、右转、直行标志）
    
    注意：此函数需要手动下载 GTSRB 数据集
    GTSRB 下载地址：https://benchmark.ini.rub.de/gtsrb_news.html
    
    Args:
        output_dir: 输出目录
        classes: 需要提取的类别列表
    """
    print("=" * 60)
    print("GTSRB 数据集下载指南")
    print("=" * 60)
    print("\n1. 访问 GTSRB 官网：https://benchmark.ini.rub.de/gtsrb_news.html")
    print("\n2. 下载训练数据集：GTSRB-Training_fixed.tar.gz")
    print("\n3. 解压后，提取以下类别:")
    print("   - 类别 1: Right turn (右转)")
    print("   - 类别 2: Left turn (左转)")
    print("   - 类别 3: Ahead only (直行)")
    print("\n4. 将提取的图像组织到以下目录结构:")
    print(f"   {output_dir}/train/left/")
    print(f"   {output_dir}/train/right/")
    print(f"   {output_dir}/train/straight/")
    print(f"   {output_dir}/val/left/")
    print(f"   {output_dir}/val/right/")
    print(f"   {output_dir}/val/straight/")
    print("\n5. 建议比例：训练集 70%, 验证集 20%, 测试集 10%")
    print("=" * 60)


if __name__ == "__main__":
    # 测试数据集加载
    import torch
    
    print("测试数据集加载...")
    
    # 假设数据集目录
    train_dir = "data/train"
    val_dir = "data/val"
    
    # 检查目录是否存在
    if not os.path.exists(train_dir):
        print(f"错误：训练集目录 {train_dir} 不存在")
        print("请先准备数据集，参考 data/README.md")
    else:
        # 创建数据加载器
        train_loader, val_loader, class_names, class_weights = create_data_loaders(
            train_dir, val_dir, batch_size=16
        )
        
        print(f"\n类别：{class_names}")
        print(f"类别权重：{class_weights}")
        print(f"\n训练集批次数量：{len(train_loader)}")
        print(f"验证集批次数量：{len(val_loader)}")
        
        # 测试获取一个批次
        images, labels = next(iter(train_loader))
        print(f"\n批次图像形状：{images.shape}")
        print(f"批次标签形状：{labels.shape}")
        print(f"批次标签：{labels}")
        
        print("\n数据集加载测试完成！")
