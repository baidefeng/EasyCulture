# 🎉 欢迎使用 EasyCulture！

## 👋 你好！

欢迎来到 **EasyCulture** - 智能微生物培养系统！

这是一个整合了数据爬取、物种鉴定、AI预测和培养条件推荐的完整系统。

## 🚀 快速开始（3步）

### 1️⃣ 安装依赖
```bash
pip install -r requirements.txt
```

### 2️⃣ 配置环境
编辑 `4_MainSystem/config.py`，修改路径配置

### 3️⃣ 运行分析
```bash
python 4_MainSystem/EasyCulture_Main.py your_genome.fasta
```

## 📚 重要文档

请按顺序阅读以下文档：

1. **整理完成说明.txt** ⭐ 必读！
   - 了解项目整理情况
   - 文件位置对照
   - 注意事项

2. **README.md**
   - 项目完整介绍
   - 功能详解
   - 使用示例

3. **INSTALL.md**
   - 详细安装步骤
   - 环境配置
   - 常见问题

4. **QUICK_START.md**
   - 快速使用教程
   - 命令行示例
   - 批量处理

5. **PROJECT_SUMMARY.md**
   - 项目总结
   - 技术栈
   - 数据统计

## 📊 项目统计

- **总文件数**: 29,270 个
- **Python 脚本**: 37 个
- **文档**: 8 个
- **数据库**: 5 个 CSV/Excel
- **序列文件**: 29,111 个
- **项目大小**: 约 3.5 GB

## 🎯 核心功能

✅ **物种鉴定**
- FastANI（全基因组）
- BLAST（16S/部分序列）

✅ **培养预测**
- 数据库查询（Excel）
- AI 预测（GenomeSPOT）
- 机器学习（XGBoost）
- GC 代谢分析

✅ **抗生素筛选**
- ARG 基因检测
- 专家规则评分

## 📁 项目结构

```
EasyCulture/
├── 1_DataCrawlers/      # 数据爬取
├── 2_SequenceData/      # 序列存储
├── 3_PredictionModels/  # 预测模型
├── 4_MainSystem/        # 主程序 ⭐
├── 5_Database/          # 数据库
├── 6_Tools/             # 工具集
└── 7_Results/           # 结果输出
```

## ⚠️ 重要提示

1. **序列数据已就绪** ✅
   所有序列文件已复制完成，共 29,111 个文件

2. **配置文件需要修改**
   编辑 `4_MainSystem/config.py` 中的 WSL 工具路径

3. **WSL 工具需要安装**
   FastANI, BLAST+, Prodigal（参考 INSTALL.md）

## 🔧 测试安装

```bash
# 测试配置
python 4_MainSystem/config.py

# 测试主程序
python 4_MainSystem/EasyCulture_Main.py --help
```

## 💡 使用示例

### 基本分析
```bash
python 4_MainSystem/EasyCulture_Main.py genome.fasta
```

### 指定输出目录
```bash
python 4_MainSystem/EasyCulture_Main.py genome.fasta -o results/
```

### 禁用某些功能
```bash
python 4_MainSystem/EasyCulture_Main.py genome.fasta --no-xgboost --no-arg
```

## 📞 需要帮助？

1. 查看 **整理完成说明.txt**
2. 阅读各模块的 README
3. 检查 `7_Results/logs/` 日志
4. 参考原始代码（根目录保留）

## 🎓 学习路径

### 初学者
1. 阅读 README.md
2. 按照 INSTALL.md 安装
3. 运行 QUICK_START.md 中的示例

### 进阶用户
1. 查看 PROJECT_SUMMARY.md 了解架构
2. 阅读 `1_DataCrawlers/README.md` 学习数据采集
3. 研究 `4_MainSystem/` 中的代码

### 开发者
1. 理解 `config.py` 配置系统
2. 学习 `EasyCulture_Main.py` 主流程
3. 扩展新功能模块

## 🌟 特色功能

### 1. 多模型融合
- 传统数据库 + AI预测 + 机器学习
- 互补验证，提高准确性

### 2. 智能质量控制
- 文件大小验证
- 物种名称匹配
- 序列长度检查

### 3. 断点续传
- 所有爬虫支持续传
- 自动跳过已处理数据

### 4. K-mer 特征分析
- 3-mer 频率提取
- 高 GC 模式识别
- 特征重要性排序

## 📈 数据规模

- **DSMZ**: 47,377 条记录，17,216 个序列 (37.9 GB)
- **JCM**: 完整数据集，7,294 个序列 (9.5 GB)
- **ATCC/CCM/NCIMB**: 20,310 条记录，4,498 个序列 (17.6 GB)
- **test_sequences (demo)**: 103 个序列 (209 MB)
- **序列文件总计**: 29,111 个
- **总大小**: 约 65 GB

## 🎯 下一步

1. ✅ 阅读 **START_HERE.md**
2. ✅ 安装依赖 `pip install -r requirements.txt`
3. ✅ 配置环境（编辑 config.py 中的 WSL 工具路径）
4. ✅ 序列数据已就绪（29,111 个文件已复制完成）
5. ✅ 测试运行
6. ✅ 开始使用！

---

## 🎉 准备好了吗？

```bash
# 开始你的第一次分析！
python 4_MainSystem/EasyCulture_Main.py your_genome.fasta
```

**祝使用愉快！** 🚀

---

*如有问题，请先查看 整理完成说明.txt 和 INSTALL.md*
