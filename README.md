# EasyCulture - 智能微生物培养系统

## 📁 项目结构

```
EasyCulture/
├── 1_DataCrawlers/          # 数据爬取脚本
│   ├── DSMZ/                # DSMZ 数据库爬虫
│   ├── JCM/                 # JCM 数据库爬虫
│   ├── MediaDive/           # MediaDive 培养基信息爬虫
│   └── ATCC_CCM_NCIMB/      # 其他菌种库序列补充
│
├── 2_SequenceData/          # 序列数据存储
│   ├── DSMZ_sequences/      # DSMZ 菌株序列
│   ├── JCM_sequences/       # JCM 菌株序列
│   ├── ATCC_CCM_NCIMB/      # 补充序列
│   └── test_sequences/      # 测试序列
│
├── 3_PredictionModels/      # 预测模型
│   ├── GenomeSPOT/          # 生理特征预测模型
│   ├── MicroBoost/          # K-mer XGBoost 培养基预测
│   └── ARG_Database/        # 抗性基因数据库
│
├── 4_MainSystem/            # 主系统代码
│   ├── EasyCulture_Main.py # 主程序（整合版）
│   └── config.py            # 配置文件
│
├── 5_Database/              # 数据库文件
│   ├── dsmz_full_database.csv
│   ├── JCM数据库全部爬取.csv
│   ├── MediaDive培养基信息.xlsx
│   └── 菌株保藏机构统计.csv
│
├── 6_Tools/                 # 工具脚本
│   ├── sequence_counter.py  # 序列统计工具
│   ├── strain_statistics.py # 菌株统计工具
│   └── database_builder.py  # 数据库构建工具
│
└── 7_Results/               # 分析结果输出
    ├── predictions/         # 预测结果
    ├── reports/             # 分析报告
    └── logs/                # 运行日志
```

## 🚀 功能模块

### 1. 数据爬取模块 (1_DataCrawlers)
- **DSMZ 爬虫**: 爬取 DSMZ 菌株信息和培养条件
- **JCM 爬虫**: 爬取 JCM 数据库序列
- **MediaDive 爬虫**: 提取培养基成分信息
- **序列补充**: 从 NCBI 补充 ATCC/CCM/NCIMB 序列

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

### V1.0 (2025-12-20)
- 整合所有功能模块
- 统一项目结构
- 添加 MicroBoost XGBoost 模型
- 优化代码组织

## 👥 作者
JIYINZU Research Team

## 📄 许可证
MIT License
