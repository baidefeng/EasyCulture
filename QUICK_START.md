# EasyCulture 快速开始指南

## 📦 安装依赖

### Python 包
```bash
pip install pandas numpy biopython xgboost scikit-learn psutil openpyxl selenium requests beautifulsoup4
```

### WSL 工具（Windows 用户）
```bash
# 在 WSL 中安装
sudo apt-get update
sudo apt-get install ncbi-blast+ prodigal

# 安装 FastANI
wget https://github.com/ParBLiSS/FastANI/releases/download/v1.34/FastANI-1.34.tar.gz
tar -xzf FastANI-1.34.tar.gz
cd FastANI-1.34
mkdir build && cd build
cmake ..
make
```

## 🚀 快速使用

### 1. 基本分析
```python
from EasyCulture.MainSystem import EasyCulture_Main

# 创建实例
ec = EasyCulture_Main.EasyCulture()

# 分析单个基因组
results = ec.analyze_genome("path/to/genome.fasta")
```

### 2. 命令行使用
```bash
# 基本分析
python EasyCulture_Main.py genome.fasta

# 指定输出目录
python EasyCulture_Main.py genome.fasta -o results/

# 禁用某些功能
python EasyCulture_Main.py genome.fasta --no-xgboost --no-arg
```

### 3. 批量分析
```python
import os
from EasyCulture.MainSystem.EasyCulture_Main import EasyCulture

ec = EasyCulture()

# 批量处理文件夹中的所有 FASTA 文件
genome_folder = "path/to/genomes/"
for filename in os.listdir(genome_folder):
    if filename.endswith(('.fasta', '.fna', '.fa')):
        filepath = os.path.join(genome_folder, filename)
        print(f"\n处理: {filename}")
        ec.analyze_genome(filepath)
```

## 📊 输出结果

分析完成后，会在 `7_Results/` 目录下生成：

1. **analysis_report.txt** - 文本格式的分析报告
2. **xgboost_predictions.csv** - XGBoost 培养基预测结果
3. **performance_log.csv** - 性能统计（如果启用）

## 🔧 配置修改

编辑 `4_MainSystem/config.py` 文件来修改：

```python
# 修改序列库路径
DSMZ_SEQ_DIR = "your/path/to/sequences"

# 修改 WSL 工具路径
FASTANI_EXE_WSL = "/your/path/to/fastANI"

# 修改阈值参数
SIZE_THRESHOLD_MB = 2  # 文件大小阈值
MIN_WGS_SIZE_KB = 500  # WGS 最小文件大小
```

## 📚 数据准备

### 1. 序列库
将参考基因组序列放入：
- `2_SequenceData/DSMZ_sequences/` - DSMZ 菌株序列
- `2_SequenceData/JCM_sequences/` - JCM 菌株序列
- `2_SequenceData/ATCC_CCM_NCIMB/` - 其他菌株序列

### 2. 培养基数据库
确保 `5_Database/MediaDive培养基信息.xlsx` 存在并包含：
- DSM编号
- 成分
- 培养温度
- 培养时间
- 环境条件

### 3. 模型文件
确保以下模型文件存在：
- `3_PredictionModels/GenomeSPOT/models/` - GenomeSPOT 模型
- `3_PredictionModels/MicroBoost/model/` - XGBoost 模型
- `3_PredictionModels/ARG_Database/arg_database.fasta` - 抗性基因数据库

## 🐛 常见问题

### Q1: 提示 "WSL 工具未找到"
**A:** 确保已安装 WSL 并配置好 FastANI、BLAST、Prodigal 的路径

### Q2: 提示 "模块未找到"
**A:** 检查 Python 包是否安装完整，运行 `pip install -r requirements.txt`

### Q3: 分析速度慢
**A:** 
- 对于小文件（<2MB），会自动使用 BLAST（较快）
- 对于大文件，使用 FastANI（较慢但准确）
- 可以禁用某些功能来加速：`--no-genomespot --no-arg`

### Q4: 内存不足
**A:** 
- 减少并行处理线程数（修改 config.py 中的 MAX_WORKERS）
- 分批处理大量文件

## 📞 技术支持

如有问题，请查看：
1. `README.md` - 完整项目文档
2. `7_Results/logs/` - 运行日志
3. 各模块的独立文档

## 🎯 下一步

- 查看 `README.md` 了解完整功能
- 查看 `4_MainSystem/config.py` 了解所有配置选项
- 查看 `1_DataCrawlers/` 了解如何爬取更多数据
- 查看 `3_PredictionModels/` 了解模型详情
