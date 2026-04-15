"""
模型训练脚本
使用 MobileNetV2 进行转向标志分类训练

支持以下功能:
- 加载预训练 MobileNetV2 模型
- 自定义分类头
- 数据增强
- 训练过程可视化
- 模型保存与加载
"""

import os
import torch
import torch.nn as nn
import torch.optim as optim
from torch.optim.lr_scheduler import StepLR
import matplotlib.pyplot as plt
from tqdm import tqdm
import time
from datetime import datetime

from src.dataset import create_data_loaders


class TurnSignClassifier(nn.Module):
    """
    转向标志分类器
    基于预训练的 MobileNetV2 进行迁移学习
    """
    
    def __init__(self, num_classes=5, pretrained=True):
        """
        初始化分类器
        
        Args:
            num_classes: 分类类别数，默认 5 (left, right, straight, stop, background)
            pretrained: 是否使用预训练权重
        """
        super(TurnSignClassifier, self).__init__()
        
        # 加载预训练的 MobileNetV2
        self.mobilenet = torch.hub.load(
            'pytorch/vision:v0.10.0', 
            'mobilenet_v2', 
            pretrained=pretrained
        )
        
        # 替换最后一个全连接层
        # MobileNetV2 的 last_channel 默认为 1280
        num_features = self.mobilenet.classifier[1].in_features
        
        # 自定义分类头
        self.mobilenet.classifier = nn.Sequential(
            nn.Dropout(p=0.2),  # Dropout 防止过拟合
            nn.Linear(num_features, num_classes)
        )
        
        print(f"模型已初始化，类别数：{num_classes}")
    
    def forward(self, x):
        """前向传播"""
        return self.mobilenet(x)
    
    def freeze_backbone(self, freeze=True):
        """
        冻结/解冻骨干网络参数
        
        Args:
            freeze: True 为冻结，False 为解冻
        """
        for param in self.mobilenet.features.parameters():
            param.requires_grad = not freeze
        
        if freeze:
            print("骨干网络参数已冻结，仅训练分类头")
        else:
            print("骨干网络参数已解冻，训练整个网络")


def train_epoch(model, train_loader, criterion, optimizer, device):
    """
    训练一个 epoch
    
    Args:
        model: 模型
        train_loader: 训练数据加载器
        criterion: 损失函数
        optimizer: 优化器
        device: 计算设备
        
    Returns:
        avg_loss: 平均损失
        accuracy: 准确率
    """
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0
    
    progress_bar = tqdm(train_loader, desc='Training')
    
    for images, labels in progress_bar:
        images, labels = images.to(device), labels.to(device)
        
        # 前向传播
        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        
        # 反向传播
        loss.backward()
        optimizer.step()
        
        # 统计
        running_loss += loss.item()
        _, predicted = torch.max(outputs.data, 1)
        total += labels.size(0)
        correct += (predicted == labels).sum().item()
        
        # 更新进度条
        progress_bar.set_postfix({
            'loss': running_loss / total,
            'acc': 100.0 * correct / total
        })
    
    avg_loss = running_loss / len(train_loader)
    accuracy = 100.0 * correct / total
    
    return avg_loss, accuracy


def validate_epoch(model, val_loader, criterion, device):
    """
    验证一个 epoch
    
    Args:
        model: 模型
        val_loader: 验证数据加载器
        criterion: 损失函数
        device: 计算设备
        
    Returns:
        avg_loss: 平均损失
        accuracy: 准确率
    """
    model.eval()
    running_loss = 0.0
    correct = 0
    total = 0
    
    with torch.no_grad():
        progress_bar = tqdm(val_loader, desc='Validating')
        
        for images, labels in progress_bar:
            images, labels = images.to(device), labels.to(device)
            
            # 前向传播
            outputs = model(images)
            loss = criterion(outputs, labels)
            
            # 统计
            running_loss += loss.item()
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()
            
            # 更新进度条
            progress_bar.set_postfix({
                'loss': running_loss / total,
                'acc': 100.0 * correct / total
            })
    
    avg_loss = running_loss / len(val_loader)
    accuracy = 100.0 * correct / total
    
    return avg_loss, accuracy


def train_model(model, train_loader, val_loader, num_epochs=20, device='cuda', save_dir='checkpoints'):
    """
    训练模型
    
    Args:
        model: 模型
        train_loader: 训练数据加载器
        val_loader: 验证数据加载器
        num_epochs: 训练轮数
        device: 计算设备
        save_dir: 模型保存目录
        
    Returns:
        history: 训练历史记录
    """
    # 创建保存目录
    os.makedirs(save_dir, exist_ok=True)
    
    # 定义损失函数和优化器
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001, weight_decay=1e-4)
    scheduler = StepLR(optimizer, step_size=7, gamma=0.1)  # 每 7 个 epoch 学习率降为 1/10
    
    # 训练历史记录
    history = {
        'train_loss': [],
        'train_acc': [],
        'val_loss': [],
        'val_acc': []
    }
    
    best_acc = 0.0
    
    print(f"\n开始训练，设备：{device}")
    print("=" * 60)
    
    for epoch in range(num_epochs):
        start_time = time.time()
        
        # 训练
        train_loss, train_acc = train_epoch(model, train_loader, criterion, optimizer, device)
        
        # 验证
        val_loss, val_acc = validate_epoch(model, val_loader, criterion, device)
        
        # 学习率调整
        scheduler.step()
        
        # 记录历史
        history['train_loss'].append(train_loss)
        history['train_acc'].append(train_acc)
        history['val_loss'].append(val_loss)
        history['val_acc'].append(val_acc)
        
        # 保存最佳模型
        if val_acc > best_acc:
            best_acc = val_acc
            save_path = os.path.join(save_dir, 'best_model.pth')
            torch.save({
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'val_acc': val_acc,
                'class_names': train_loader.dataset.class_names
            }, save_path)
            print(f"✓ 保存最佳模型：{save_path} (验证准确率：{val_acc:.2f}%)")
        
        # 打印 epoch 总结
        epoch_time = time.time() - start_time
        print(f"Epoch {epoch+1}/{num_epochs} - "
              f"训练损失：{train_loss:.4f}, 训练准确率：{train_acc:.2f}% - "
              f"验证损失：{val_loss:.4f}, 验证准确率：{val_acc:.2f}% - "
              f"耗时：{epoch_time:.1f}s")
        
        print("-" * 60)
    
    # 保存训练历史
    history_path = os.path.join(save_dir, 'training_history.pth')
    torch.save(history, history_path)
    print(f"训练历史已保存到：{history_path}")
    
    return history


def plot_training_history(history, save_dir='checkpoints'):
    """
    绘制训练历史曲线
    
    Args:
        history: 训练历史记录
        save_dir: 图片保存目录
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
    
    # 损失曲线
    ax1.plot(history['train_loss'], label='Train Loss')
    ax1.plot(history['val_loss'], label='Val Loss')
    ax1.set_xlabel('Epoch')
    ax1.set_ylabel('Loss')
    ax1.set_title('Training and Validation Loss')
    ax1.legend()
    ax1.grid(True)
    
    # 准确率曲线
    ax2.plot(history['train_acc'], label='Train Acc')
    ax2.plot(history['val_acc'], label='Val Acc')
    ax2.set_xlabel('Epoch')
    ax2.set_ylabel('Accuracy (%)')
    ax2.set_title('Training and Validation Accuracy')
    ax2.legend()
    ax2.grid(True)
    
    plt.tight_layout()
    save_path = os.path.join(save_dir, 'training_history.png')
    plt.savefig(save_path, dpi=150)
    print(f"训练曲线已保存到：{save_path}")
    plt.close()


def main():
    """主函数"""
    # 配置参数
    DATA_DIR = 'data'
    TRAIN_DIR = os.path.join(DATA_DIR, 'train')
    VAL_DIR = os.path.join(DATA_DIR, 'val')
    SAVE_DIR = 'checkpoints'
    
    BATCH_SIZE = 32
    NUM_EPOCHS = 20
    IMG_SIZE = (224, 224)
    
    # 检测设备
    if torch.cuda.is_available():
        device = 'cuda'
        print(f"检测到 GPU: {torch.cuda.get_device_name(0)}")
    else:
        device = 'cpu'
        print("未检测到 GPU，使用 CPU 训练")
    
    print("=" * 60)
    print("转向标志识别系统 - 训练脚本")
    print("=" * 60)
    
    # 检查数据集目录
    if not os.path.exists(TRAIN_DIR):
        print(f"\n错误：训练集目录不存在：{TRAIN_DIR}")
        print("请先准备数据集，参考 data/README.md")
        return
    
    # 创建数据加载器
    print("\n加载数据集...")
    train_loader, val_loader, class_names, class_weights = create_data_loaders(
        TRAIN_DIR, VAL_DIR, batch_size=BATCH_SIZE, img_size=IMG_SIZE
    )
    
    print(f"类别：{class_names}")
    print(f"训练集批次数量：{len(train_loader)}")
    print(f"验证集批次数量：{len(val_loader)}")
    
    # 创建模型
    print("\n创建模型...")
    model = TurnSignClassifier(num_classes=len(class_names), pretrained=True)
    model = model.to(device)
    
    # 训练模型
    print("\n开始训练...")
    history = train_model(
        model, train_loader, val_loader,
        num_epochs=NUM_EPOCHS,
        device=device,
        save_dir=SAVE_DIR
    )
    
    # 绘制训练曲线
    print("\n生成训练曲线...")
    plot_training_history(history, save_dir=SAVE_DIR)
    
    print("\n" + "=" * 60)
    print("训练完成！")
    print("=" * 60)
    print(f"最佳验证准确率：{max(history['val_acc']):.2f}%")
    print(f"模型保存在：{SAVE_DIR}/")
    print("\n下一步:")
    print("1. 检查模型准确率是否达到 85% 以上")
    print("2. 使用 classifier.py 进行推理测试")
    print("3. 集成到实时系统中")


if __name__ == "__main__":
    main()
