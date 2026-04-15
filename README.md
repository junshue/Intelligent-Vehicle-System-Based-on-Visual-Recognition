# 转向标志识别与车辆控制系统

## Turn Sign Recognition and Real-Time Vehicle Control System

<div align="center">

**基于计算机视觉的实时转向标志识别与车辆控制闭环系统**

[![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![PyTorch](https://img.shields.io/badge/PyTorch-1.9+-ee4c2c.svg)](https://pytorch.org/)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.5+-5C3EE8.svg)](https://opencv.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

</div>

---

## 📋 目录

- [项目简介](#-项目简介)
- [系统特点](#-系统特点)
- [技术架构](#-技术架构)
- [快速开始](#-快速开始)
- [详细使用](#-详细使用)
- [项目结构](#-项目结构)
- [性能指标](#-性能指标)
- [常见问题](#-常见问题)
- [扩展开发](#-扩展开发)

---

## 🎯 项目简介

本项目是一个**学生课程/竞赛项目**，目标是构建一个基于视觉的转向路标识别系统，并能根据识别结果对车辆（真实小车或仿真环境）进行实时控制。

### 核心功能

1. **实时识别**：通过摄像头捕获视频流，实时识别转向标志（左转、右转、直行、停止）
2. **智能控制**：根据识别结果生成车辆控制指令，支持仿真和真实小车
3. **闭环演示**：完整的"识别→决策→控制"闭环系统

### 教育目标

- 掌握计算机视觉基本流程
- 理解深度学习模型训练与部署
- 学习实时控制系统设计
- 实践软硬件协同开发

---

## ✨ 系统特点

### 🎓 教育清晰性优先
- 代码包含详细中文注释
- 模块化设计，易于理解
- 避免过度优化，注重概念清晰

### 🎯 最小可行范围
- 聚焦核心功能：识别 → 控制
- 识别类别：左转、右转、直行、停止、无标志
- 控制方式：仿真环境 或 串口控制小车

### 💻 硬件亲和性
- 普通笔记本即可运行
- 无需昂贵边缘计算设备
- 可选低成本 Arduino 小车

### 📈 渐进式构建
- 4 个可演示的里程碑
- 逐步集成，降低风险
- 每个阶段都可独立测试

---

## 🏗️ 技术架构

### 技术栈

| 组件 | 技术选型 | 说明 |
| :--- | :--- | :--- |
| **编程语言** | Python 3.9+ | 易学易用，生态丰富 |
| **视觉库** | OpenCV | 摄像头捕获、图像处理 |
| **深度学习** | PyTorch | 灵活强大，社区支持好 |
| **模型架构** | MobileNetV2 | 轻量级，CPU 可运行 |
| **仿真环境** | Pygame | 简易小车模拟 |
| **硬件控制** | PySerial | 串口通信 |

### 系统架构

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌─────────────┐
│  摄像头捕获  │ ──→ │  图像分类器   │ ──→ │  指令映射器  │ ──→ │  车辆控制器  │
│   Camera    │     │  Classifier  │     │ CommandMapper│     │ Controller  │
└─────────────┘     └──────────────┘     └─────────────┘     └─────────────┘
       ↓                    ↓                    ↓                    ↓
   视频流              识别结果              控制指令            仿真/真实小车
```

### 识别类别

| 类别 ID | 类别名称 | 中文名称 | 控制指令 |
| :--- | :--- | :--- | :--- |
| 0 | left | 左转 | TURN_LEFT |
| 1 | right | 右转 | TURN_RIGHT |
| 2 | straight | 直行 | GO_STRAIGHT |
| 3 | stop | 停止 | STOP |
| 4 | background | 无标志 | STOP |

---

## 🚀 快速开始

### 1. 环境准备

#### 创建虚拟环境
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

#### 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 准备数据集

#### 下载 GTSRB 数据集

1. 访问 [GTSRB 官网](https://benchmark.ini.rub.de/gtsrb_news.html)
2. 下载训练数据集：`GTSRB-Training_fixed.tar.gz`
3. 解压并提取以下类别：
   - 类别 1: Right turn (右转)
   - 类别 2: Left turn (左转)
   - 类别 3: Ahead only (直行)

#### 组织目录结构

```
data/
├── train/
│   ├── left/          # 左转标志图片
│   ├── right/         # 右转标志图片
│   ├── straight/      # 直行标志图片
│   ├── stop/          # 停止标志图片
│   └── background/    # 背景图片
├── val/
│   ├── left/
│   ├── right/
│   ├── straight/
│   ├── stop/
│   └── background/
└── test/
    ├── left/
    ├── right/
    ├── straight/
    ├── stop/
    └── background/
```

**建议比例**：训练集 70%，验证集 20%，测试集 10%

### 3. 训练模型

```bash
python train.py
```

**训练参数**（可在 `train.py` 中修改）：
- `BATCH_SIZE`: 32
- `NUM_EPOCHS`: 20
- `IMG_SIZE`: 224x224

**预期输出**：
- 模型权重：`checkpoints/best_model.pth`
- 训练曲线：`checkpoints/training_history.png`
- 目标准确率：≥85%

### 4. 运行系统

#### 模式 1：演示模式（仅识别）
```bash
python main.py --mode demo
```

#### 模式 2：仿真模式（Pygame 小车）
```bash
python main.py --mode simulation
```

#### 模式 3：串口模式（真实小车）
```bash
python main.py --mode serial --port COM3
```

**快捷键**：
- `q`: 退出
- `l`: 切换日志记录

---

## 📖 详细使用

### 模块测试

#### 测试摄像头
```bash
python -m src.camera
```

#### 测试分类器
```bash
python -m src.classifier
```

#### 测试指令映射
```bash
python -m src.controller
```

#### 测试仿真控制器
```bash
python -m src.sim_controller
```

#### 测试串口控制器
```bash
python -m src.serial_controller
```

### 模型评估

```bash
python evaluate.py
```

输出：
- 测试集准确率
- 混淆矩阵图
- 性能分析

### 日志查看

运行系统时按 `l` 键开启日志记录，日志保存在 `logs/` 目录：

```bash
# 查看最新日志
tail -f logs/recognition_*.log
```

---

## 📁 项目结构

```
Intelligent-Vehicle-System-Based-on-Visual-Recognition/
├── main.py                     # 主程序
├── train.py                    # 训练脚本
├── evaluate.py                 # 评估脚本
├── requirements.txt            # 依赖列表
├── README.md                   # 项目文档
│
├── src/                        # 源代码目录
│   ├── __init__.py
│   ├── camera.py               # 摄像头捕获模块
│   ├── classifier.py           # 分类器推理模块
│   ├── controller.py           # 指令映射模块
│   ├── sim_controller.py       # 仿真控制器
│   └── serial_controller.py    # 串口控制器
│
├── data/                       # 数据集目录
│   ├── README.md               # 数据集说明
│   ├── train/                  # 训练集
│   ├── val/                    # 验证集
│   └── test/                   # 测试集
│
├── checkpoints/                # 模型文件（训练后生成）
│   ├── best_model.pth          # 最佳模型权重
│   ├── training_history.pth    # 训练历史
│   ├── training_history.png    # 训练曲线
│   └── confusion_matrix.png    # 混淆矩阵
│
├── logs/                       # 日志目录（运行时生成）
│   └── recognition_*.log       # 识别日志
│
└── .trae/                      # IDE 配置
    └── rules/
        ├── constitution.md     # 项目章程
        └── ...
```

---

## 📊 性能指标

### 学生级目标

| 指标 | 目标值 | 测量方式 |
| :--- | :--- | :--- |
| **分类准确率** | ≥ 85% | 测试集评估 |
| **实时推理帧率** | ≥ 10 FPS | 笔记本 CPU |
| **控制指令延迟** | < 200 ms | 图像捕获到指令发出 |
| **训练时间** | < 2 小时 | Google Colab 免费 GPU |

### 优化建议

如果性能未达标，可以尝试：

1. **提高准确率**：
   - 增加训练数据量
   - 调整数据增强参数
   - 增加训练轮数
   - 使用更复杂的模型（如 ResNet）

2. **提高帧率**：
   - 降低输入图像分辨率
   - 使用 CPU 优化（OpenVINO）
   - 多线程处理

3. **降低延迟**：
   - 减小滑动窗口大小
   - 优化模型推理速度
   - 使用异步处理

---

## ❓ 常见问题

### Q1: 摄像头无法打开
**A**: 检查以下几点：
1. 摄像头是否已正确连接
2. 摄像头驱动是否已安装
3. 是否有其他程序正在使用摄像头
4. 尝试修改 `--camera` 参数（如 1, 2 等）

### Q2: 模型文件不存在
**A**: 先运行训练脚本：
```bash
python train.py
```

### Q3: 准确率低于 85%
**A**: 可能原因：
1. 训练数据不足 → 增加数据量
2. 类别不平衡 → 使用类别权重
3. 过拟合 → 增加 Dropout 或数据增强
4. 训练轮数不足 → 增加 `NUM_EPOCHS`

### Q4: 帧率低于 10 FPS
**A**: 优化方法：
1. 降低图像分辨率（如 320x240）
2. 使用 GPU 推理
3. 减小模型输入尺寸

### Q5: 串口连接失败
**A**: 检查：
1. 小车是否已连接电脑
2. 端口号是否正确（`python -m src.serial_controller` 查看）
3. 波特率是否匹配（默认 9600）
4. 是否需要安装串口驱动

---

## 🔧 扩展开发

### 添加新的识别类别

1. 在 `data/` 目录下添加新类别的文件夹
2. 更新 `src/dataset.py` 中的 `class_names`
3. 重新训练模型

### 添加新的控制方式

1. 创建新的控制器类（参考 `src/sim_controller.py`）
2. 实现 `execute(command)` 方法
3. 在 `main.py` 中集成

### 改进模型架构

编辑 `src/classifier.py`，替换 MobileNetV2 为其他模型：

```python
# 使用 ResNet18
import torchvision.models as models
self.backbone = models.resnet18(pretrained=True)
```

### 添加更多功能

- [ ] 多标志检测（YOLO）
- [ ] 路径规划
- [ ] 多车协同
- [ ] Web 界面监控
- [ ] 云端训练部署

---

## 📝 更新日志

### v1.0.0 (2026-01-01)
- ✨ 初始版本发布
- ✅ 基础分类器训练与推理
- ✅ 实时视频流识别
- ✅ 仿真控制器
- ✅ 串口控制器
- ✅ 完整文档

---

## 👨‍💻 贡献指南

欢迎提交 Issue 和 Pull Request！

### 开发环境设置
```bash
git clone <repository-url>
cd Intelligent-Vehicle-System-Based-on-Visual-Recognition
python -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\activate
pip install -r requirements.txt
```

### 代码规范
- 遵循 PEP 8
- 使用中文注释
- 添加必要的文档字符串

---

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

## 🙏 致谢

- [GTSRB Dataset](https://benchmark.ini.rub.de/gtsrb_news.html)
- [PyTorch](https://pytorch.org/)
- [OpenCV](https://opencv.org/)
- [MobileNetV2](https://arxiv.org/abs/1801.04381)

---

## 📧 联系方式

如有问题或建议，请提交 Issue 或联系项目维护者。

---

<div align="center">

**祝学习愉快！🎓**

Made with ❤️ by Students

</div>
