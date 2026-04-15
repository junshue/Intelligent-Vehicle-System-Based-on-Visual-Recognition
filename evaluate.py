"""
模型评估脚本
评估训练好的模型在测试集上的准确率和性能
"""

import os
import torch
from tqdm import tqdm
import matplotlib.pyplot as plt
import numpy as np

from src.dataset import TurnSignDataset
from src.classifier import TurnSignClassifierModel


def evaluate_model(model_path, test_dir, batch_size=32):
    """
    评估模型性能
    
    Args:
        model_path: 模型权重文件路径
        test_dir: 测试集目录
        batch_size: 批次大小
        
    Returns:
        accuracy: 准确率
        confusion_matrix: 混淆矩阵
    """
    # 检查测试集
    if not os.path.exists(test_dir):
        print(f"错误：测试集目录不存在：{test_dir}")
        return None, None
    
    # 加载模型
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    checkpoint = torch.load(model_path, map_location=device)
    
    class_names = checkpoint.get('class_names', ['left', 'right', 'straight', 'stop', 'background'])
    num_classes = len(class_names)
    
    model = TurnSignClassifierModel(num_classes=num_classes)
    model.load_state_dict(checkpoint['model_state_dict'])
    model.to(device)
    model.eval()
    
    print(f"模型已加载：{model_path}")
    print(f"类别：{class_names}")
    
    # 加载测试数据集
    test_dataset = TurnSignDataset(test_dir, img_size=(224, 224), augment=False)
    
    if len(test_dataset) == 0:
        print("错误：测试集为空")
        return None, None
    
    print(f"测试集大小：{len(test_dataset)}")
    
    # 评估
    correct = 0
    total = 0
    predictions = []
    ground_truth = []
    
    from torch.utils.data import DataLoader
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)
    
    print("\n评估中...")
    with torch.no_grad():
        for images, labels in tqdm(test_loader, desc='Testing'):
            images, labels = images.to(device), labels.to(device)
            
            outputs = model(images)
            _, predicted = torch.max(outputs, 1)
            
            total += labels.size(0)
            correct += (predicted == labels).sum().item()
            
            predictions.extend(predicted.cpu().numpy())
            ground_truth.extend(labels.cpu().numpy())
    
    accuracy = 100.0 * correct / total
    
    print(f"\n测试结果:")
    print(f"  总样本数：{total}")
    print(f"  正确数：{correct}")
    print(f"  准确率：{accuracy:.2f}%")
    
    # 计算混淆矩阵
    confusion_matrix = np.zeros((num_classes, num_classes), dtype=int)
    for pred, truth in zip(predictions, ground_truth):
        confusion_matrix[truth, pred] += 1
    
    print(f"\n混淆矩阵:")
    print(confusion_matrix)
    
    # 绘制混淆矩阵
    plt.figure(figsize=(10, 8))
    plt.imshow(confusion_matrix, interpolation='nearest', cmap=plt.cm.Blues)
    plt.title('Confusion Matrix')
    plt.colorbar()
    
    # 添加标签
    tick_marks = np.arange(num_classes)
    plt.xticks(tick_marks, class_names, rotation=45)
    plt.yticks(tick_marks, class_names)
    
    # 添加数值
    thresh = confusion_matrix.max() / 2.
    for i in range(num_classes):
        for j in range(num_classes):
            plt.text(j, i, format(confusion_matrix[i, j], 'd'),
                    horizontalalignment="center",
                    color="white" if confusion_matrix[i, j] > thresh else "black")
    
    plt.tight_layout()
    plt.savefig('checkpoints/confusion_matrix.png', dpi=150)
    print(f"\n混淆矩阵已保存：checkpoints/confusion_matrix.png")
    
    return accuracy, confusion_matrix


def main():
    """主函数"""
    print("=" * 60)
    print("模型评估脚本")
    print("=" * 60)
    
    # 配置
    MODEL_PATH = 'checkpoints/best_model.pth'
    TEST_DIR = 'data/test'
    
    # 检查模型文件
    if not os.path.exists(MODEL_PATH):
        print(f"错误：模型文件不存在：{MODEL_PATH}")
        print("请先运行训练脚本：python train.py")
        return
    
    # 评估
    accuracy, confusion_matrix = evaluate_model(MODEL_PATH, TEST_DIR)
    
    if accuracy is not None:
        print("\n" + "=" * 60)
        if accuracy >= 85:
            print(f"✓ 模型准确率达到目标 (≥85%): {accuracy:.2f}%")
        else:
            print(f"✗ 模型准确率未达目标 (<85%): {accuracy:.2f}%")
            print("\n建议:")
            print("  1. 增加训练数据量")
            print("  2. 增加训练轮数")
            print("  3. 调整数据增强参数")
            print("  4. 检查数据集质量")
        print("=" * 60)


if __name__ == "__main__":
    main()
