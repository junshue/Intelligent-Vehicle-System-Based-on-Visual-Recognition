import os
import shutil
import random
import torchvision
from torchvision import transforms
from PIL import Image

# ==================== 配置参数 ====================
DATA_ROOT = "./data_raw"      # 临时存放原始GTSRB数据的位置
OUTPUT_DIR = "./data"         # 你已有的data目录，内含train/val/test子文件夹

# 筛选的目标类别：左转(34)、右转(33)、直行(35)、停止(14)
# 如果还需要其他类别（如让行、环岛），可以在这里添加对应ID
TARGET_CLASSES = {
    34: "left",
    33: "right",
    35: "straight",
    14: "stop",
    # # 添加"background"类别稍后单独处理，因为GTSRB中没有背景类
    # 0: "background",
    # 1: "unknown"

}

# 数据集划分比例
TRAIN_RATIO = 0.7
VAL_RATIO = 0.2
TEST_RATIO = 0.1

# 随机种子保证可复现
RANDOM_SEED = 42
random.seed(RANDOM_SEED)

# ==================== 辅助函数 ====================
def ensure_dir(path):
    """确保目录存在，不存在则创建"""
    os.makedirs(path, exist_ok=True)

def save_image(img_tensor, save_path):
    """
    将PyTorch Tensor图片保存为JPEG文件
    GTSRB原始图片尺寸不一，我们直接保存为JPEG格式
    """
    # 反归一化（GTSRB加载时用了ToTensor()，范围[0,1]）
    img_pil = transforms.ToPILImage()(img_tensor)
    img_pil.save(save_path)

def copy_to_split(data_samples, output_base, split_name):
    """
    将数据样本复制到目标文件夹
    data_samples: list of (img_tensor, class_name, original_idx)
    """
    for img_tensor, class_name, idx in data_samples:
        class_dir = os.path.join(output_base, split_name, class_name)
        ensure_dir(class_dir)
        save_path = os.path.join(class_dir, f"{class_name}_{idx:05d}.jpg")
        save_image(img_tensor, save_path)

# ==================== 主流程 ====================
def main():
    print("1. 下载 GTSRB 数据集（通过 torchvision）...")
    # 为了简单，不使用复杂数据增强，只转为Tensor
    transform = transforms.Compose([
        transforms.Resize((112, 112)),   # 统一尺寸便于后续训练
        transforms.ToTensor(),
    ])

    # 下载训练集和测试集（官方划分）
    train_dataset = torchvision.datasets.GTSRB(
        root=DATA_ROOT, split='train', download=True, transform=transform
    )
    test_dataset = torchvision.datasets.GTSRB(
        root=DATA_ROOT, split='test', download=True, transform=transform
    )

    print(f"   训练集样本总数: {len(train_dataset)}")
    print(f"   测试集样本总数: {len(test_dataset)}")

    # 2. 合并并筛选目标类别
    print("\n2. 筛选目标类别并合并数据...")
    all_samples = []   # 存储 (img_tensor, class_name, 原始索引)

    # 处理训练集部分
    for idx in range(len(train_dataset)):
        img, label = train_dataset[idx]
        if label in TARGET_CLASSES:
            class_name = TARGET_CLASSES[label]
            all_samples.append((img, class_name, idx))

    # 处理测试集部分
    for idx in range(len(test_dataset)):
        img, label = test_dataset[idx]
        if label in TARGET_CLASSES:
            class_name = TARGET_CLASSES[label]
            all_samples.append((img, class_name, idx + len(train_dataset)))  # 避免索引冲突

    print(f"   筛选后总样本数: {len(all_samples)}")
    for class_name in TARGET_CLASSES.values():
        count = sum(1 for s in all_samples if s[1] == class_name)
        print(f"      {class_name}: {count} 张")

    # 3. 打乱并划分数据集
    print("\n3. 划分训练集/验证集/测试集...")
    random.shuffle(all_samples)

    total = len(all_samples)
    train_end = int(total * TRAIN_RATIO)
    val_end = train_end + int(total * VAL_RATIO)

    train_samples = all_samples[:train_end]
    val_samples = all_samples[train_end:val_end]
    test_samples = all_samples[val_end:]

    print(f"   训练集: {len(train_samples)} 张")
    print(f"   验证集: {len(val_samples)} 张")
    print(f"   测试集: {len(test_samples)} 张")

    # 4. 将图片保存到你的目录结构中
    print("\n4. 正在将图片复制到 data/ 目录...")
    copy_to_split(train_samples, OUTPUT_DIR, "train")
    copy_to_split(val_samples, OUTPUT_DIR, "val")
    copy_to_split(test_samples, OUTPUT_DIR, "test")

    # 5. 处理背景类别（无标志的图片）
    # GTSRB不包含背景图片，这里我们创建一些空白或随机背景图片作为占位
    # 你可以后期自行添加真实的背景图片，这里先创建少量的空白背景样本，以免训练时报错
    print("\n5. 创建占位背景图片（后期请替换为真实背景图）...")
    for split in ["train", "val", "test"]:
        bg_dir = os.path.join(OUTPUT_DIR, split, "background")
        ensure_dir(bg_dir)
        # 为每个split创建5张纯黑色图片作为占位
        for i in range(5):
            bg_img = Image.new('RGB', (112, 112), color=(0, 0, 0))
            bg_path = os.path.join(bg_dir, f"background_{split}_{i:02d}.jpg")
            bg_img.save(bg_path)

    print("\n✅ 数据集准备完成！")
    print(f"   数据已保存在: {OUTPUT_DIR}")
    print("   - train/ : 用于模型训练")
    print("   - val/   : 用于训练过程中的验证")
    print("   - test/  : 用于最终测试评估")

    # 可选：删除原始下载数据以节省空间
    import shutil
    shutil.rmtree(DATA_ROOT)
    print("   已删除临时原始数据文件夹。")

if __name__ == "__main__":
    main()