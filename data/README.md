# 数据集目录

## 目录结构

```
data/
├── train/
│   ├── left/
│   ├── right/
│   ├── straight/
│   ├── stop/
│   └── background/
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

## 数据集来源

- **GTSRB (German Traffic Sign Recognition Benchmark)**: 包含左转、右转、直行标志
- **停止标志**: 从公开数据集中收集
- **背景图片**: 自采街景图片（无交通标志）

## 类别说明

1. **left (0)**: 左转标志
2. **right (1)**: 右转标志
3. **straight (2)**: 直行标志
4. **stop (3)**: 停止标志
5. **background (4)**: 背景/无标志

## 数据准备步骤

1. 下载 GTSRB 数据集
2. 提取类别 1, 2, 3 (左转、右转、直行)
3. 收集停止标志图片
4. 采集背景图片
5. 按照上述结构组织 train/val/test 文件夹
6. 建议比例：train 70%, val 20%, test 10%
