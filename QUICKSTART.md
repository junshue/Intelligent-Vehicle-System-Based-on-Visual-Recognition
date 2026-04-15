# 快速开始指南

## 5 分钟快速体验

### 第一步：激活环境 (1 分钟)

```bash
# Windows PowerShell
.\venv\Scripts\Activate.ps1

# 或 CMD
.\venv\Scripts\activate.bat
```

### 第二步：测试各个模块 (3 分钟)

无需训练模型，先测试各个模块是否正常工作：

```bash
# 1. 测试摄像头（按 q 退出）
python -m src.camera

# 2. 测试指令映射
python -m src.controller

# 3. 测试仿真控制器（Pygame 窗口）
python -m src.sim_controller

# 4. 测试串口控制器（查看可用端口）
python -m src.serial_controller
# 代码结果
测试串口控制器...
============================================================

步骤 1: 列出可用端口
可用串口端口:
  0: COM5 - 蓝牙链接上的标准串行 (COM5)
  1: COM3 - 蓝牙链接上的标准串行 (COM3)
  2: COM7 - 蓝牙链接上的标准串行 (COM7)
  3: COM1 - ELTIMA Virtual Serial Port (COM1->COM2)
  4: COM2 - ELTIMA Virtual Serial Port (COM2->COM1)
  5: COM6 - 蓝牙链接上的标准串行 (COM6)
  6: COM4 - 蓝牙链接上的标准串行 (COM4)
  7: COM8 - 蓝牙链接上的标准串行 (COM8)

============================================================
如果没有连接真实小车，此模块将跳过实际测试

要测试真实小车控制，请:
1. 连接 Arduino 小车到电脑
2. 记下端口号（如 COM3）
3. 运行以下代码:

   controller = SerialController()
   controller.connect('COM3')  # 替换为你的端口
   controller.send_command(Command.TURN_LEFT)
============================================================

模拟指令发送:
  指令：左转     → 字符：L
  指令：右转     → 字符：R
  指令：直行     → 字符：F
  指令：停止     → 字符：S

串口控制器测试完成！
```

### 第三步：准备简单数据集 (可选)

如果暂时没有 GTSRB 数据集，可以：

1. **使用网上图片**：收集一些转向标志图片
2. **自己拍摄**：用手机拍摄左转、右转、直行、停止标志
3. **使用现有数据**：任何包含交通标志的数据集

目录结构：

```
data/train/left/      # 放左转标志图片
data/train/right/     # 放右转标志图片
data/train/straight/  # 放直行标志图片
data/train/stop/      # 放停止标志图片
data/train/background/# 放背景图片（无标志）
```

### 第四步：训练模型 (需要 GPU 或等待)

```bash
# 本地训练（有 GPU 约 30 分钟，无 GPU 约 2 小时）
python train.py

# 或使用 Google Colab（推荐）
# 1. 将项目上传到 Google Drive
# 2. 在 Colab 中挂载 Drive
# 3. 运行 train.py
```

### 第五步：运行系统 (1 分钟)

训练完成后，运行完整系统：

```bash
# 演示模式（仅识别，无需模型也能测试摄像头）
python main.py --mode demo

# 仿真模式（需要训练好的模型）
python main.py --mode simulation

# 串口模式（连接 Arduino 小车）
python main.py --mode serial --port COM3
```

***

## 常见问题快速解决

### ❌ 摄像头打不开

**解决方法**：

```bash
# 查看可用摄像头
python -c "import cv2; print([i for i in range(10) if cv2.VideoCapture(i).isOpened()])"

# 尝试不同的摄像头 ID
python main.py --camera 1
```

### ❌ 模型文件不存在

**原因**：还没有训练模型

**解决方法**：

1. 运行 `python train.py` 训练模型
2. 或下载预训练模型放到 `checkpoints/best_model.pth`

### ❌ 准确率低

**快速提升方法**：

1. 增加训练数据（每类至少 50 张）
2. 增加训练轮数：编辑 `train.py`，修改 `NUM_EPOCHS = 50`
3. 检查数据质量（图片清晰、标志明显）

### ❌ 帧率低（卡顿）

**优化方法**：

1. 降低分辨率：编辑 `src/camera.py`，修改 `width=320, height=240`
2. 使用 GPU：确保已安装 CUDA 版本的 PyTorch
3. 关闭其他占用 CPU 的程序

***

## 下一步学习

完成快速体验后，建议：

1. **阅读完整文档**：查看 [README.md](README.md)
2. **理解代码**：阅读各模块的中文注释
3. **调整参数**：尝试修改超参数，观察效果
4. **扩展功能**：添加新的识别类别或控制方式

***

## 学习资源

- **PyTorch 教程**：<https://pytorch.org/tutorials/>
- **OpenCV 文档**：<https://docs.opencv.org/>
- **GTSRB 数据集**：<https://benchmark.ini.rub.de/gtsrb_news.html>
- **MobileNetV2 论文**：<https://arxiv.org/abs/1801.04381>

***

**祝你学习愉快！** 🚀
