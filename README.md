# EasyCulture - Intelligent prediction system for microbial culture conditions

## 📁 Project Structure

```
EasyCulture/
├── 1_DataDownload/          # Data download script
│   ├── DSMZ/                # DSMZ database download
│   ├── JCM/                 # JCM database download
│   ├── MediaDive/           # MediaDive culture medium information download
│   └── ATCC_CCM_NCIMB/      # Other strains and sequences supplemented
│
├── 2_SequenceData/          # Sequence data storage
│   ├── DSMZ_sequences/      # DSMZ strain sequence
│   ├── JCM_sequences/       # JCM strain sequence
│   ├── ATCC_CCM_NCIMB/      # Supplementary sequence
│   └── test_sequences/      # Test sequence
│
├── 3_PredictionModels/      # Predictive Model
│   ├── GenomeSPOT/          # Physiological feature prediction model
│   ├── MicroBoost/          # K-mer XGBoost culture medium prediction
│   └── ARG_Database/        # Resistance gene database
│
├── 4_MainSystem/            # Main system code
│   ├── EasyCulture_Main.py  # Main program (integrated version)
│   └── config.py            # Configuration file
│
├── 5_Database/              # Database file
│   ├── dsmz_full_database.csv
│   ├── JCM_database_download.csv
│   ├── MediaDive_medium_info.xlsx
│   └── ATCC_CCM_NCIMB_sequence_completion_results.csv
│
├── 6_Tools/                 # Tool script
│   ├── sequence_counter.py  # Sequence statistics tools
│   ├── strain_statistics.py # Strains statistics tools
│   └── database_builder.py  # Database building tools
│
└── 7_Results/               # Analysis results output
    ├── predictions/         # Prediction results
    ├── reports/             # Analysis report
    └── logs/                # Run log
```

## 🚀 Functional modules

### 1. Data download module (1_DataDownload)
- **DSMZ download**: Download information on DSMZ strains and culture conditions.
- **JCM download**: Download JCM database sequence
- **MediaDive download**: Extracting information on culture medium composition
- **Sequence completion**: Supplement ATCC/CCM/NCIMB sequences from NCBI

### 2. 序列数据管理 (2_SequenceData)
- 统一存储各数据库的基因组序列
- 支持 FASTA/FNA 格式
- 自动去重和质量控制

### 3. 预测模型 (3_PredictionModels)
- **GenomeSPOT**: AI 生理特征预测（温度、pH、盐度、氧气需求）
- **MicroBoost**: K-mer XGBoost 培养基预测
- **ARG 检测**: 抗生素抗性基因筛选

### 4. 主系统 (4_MainSystem)
- 整合所有功能的主程序
- 智能物种鉴定（FastANI + BLAST）
- 多模型培养条件预测
- GC 含量代谢分析
- 抗生素筛选建议

### 5. 数据库 (5_Database)
- 菌株信息数据库
- 培养基成分数据库
- 序列索引数据库

### 6. 工具集 (6_Tools)
- 序列统计分析
- 数据库维护工具
- 批量处理脚本

### 7. 结果输出 (7_Results)
- 预测结果 CSV
- 分析报告
- 运行日志

## 📊 核心功能

1. **智能物种鉴定**
   - FastANI（全基因组）
   - BLAST（16S/部分序列）
   - 自动选择最优算法

2. **多维度培养预测**
   - Excel 数据库查询（已知菌株）
   - GenomeSPOT AI 预测（生理特征）
   - XGBoost 机器学习（培养基推荐）
   - GC 含量代谢分析（碳氮源）

3. **抗生素筛选**
   - ARG 基因检测
   - 专家规则评分
   - 使用建议和警告

## 🔧 依赖环境

### Python 包
```bash
pip install pandas numpy biopython xgboost scikit-learn psutil openpyxl
```

### 外部工具（WSL）
- FastANI
- BLAST+
- Prodigal

### 浏览器驱动
- ChromeDriver（用于数据爬取）

## 📖 使用方法

### 快速开始
```python
from EasyCulture.MainSystem import EasyCulture_Main

# 分析单个基因组
EasyCulture_Main.analyze_genome("your_genome.fasta")
```

### 批量分析
```python
EasyCulture_Main.batch_analyze("genome_folder/")
```

## 📝 更新日志

### V1.1 (2026-3-11)
- 整合所有功能模块
- 统一项目结构
- 添加 MicroBoost XGBoost 模型
- 优化代码组织

## 👥 作者
JIYINZU Research Team

## 📄 许可证
MIT License







