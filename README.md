# EasyCulture - Intelligent prediction system for microbial culture conditions
- EasyCulture is an intelligent platform designed for microbial cultivation research. By analyzing genome sequences, it automatically infers cultivation clues, helping researchers design media, predict physiological traits, and generate actionable culture recommendations. The platform integrates gene prediction, functional annotation, media recommendation, GenomeSPOT-based physiological inference, BacDive-AI phenotype prediction, and resistance/nutrient preference analysis to support the cultivation of difficult-to-culture microbes and newly isolated strains.
  
- Whether you are exploring cultivation conditions directly from whole-genome data or optimizing carbon sources, nitrogen sources, and electron acceptors based on functional genes, EasyCulture transforms complex bioinformatics outputs into clear and practical experimental guidance—helping you move faster from sequence to culture.

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

## 🌐 Online prediction platform
- We have developed and released the online prediction platform EasyCulture, which is available for free to everyone.
https://bic.ac.cn/EasyCulture/#/Easyanalysis

## 🚀 Functional modules

### 1. Data download module (1_DataDownload)
- **DSMZ download**: Download information on DSMZ strains and culture conditions.
- **JCM download**: Download JCM database sequence
- **MediaDive download**: Extracting information on culture medium composition
- **Sequence completion**: Supplement ATCC/CCM/NCIMB sequences from NCBI

### 2. Sequence data management (2_SequenceData)
- Unified storage of genome sequences from various databases
- Supports FASTA/FNA formats
- Automatic deduplication and quality control

### 3. Predictive model (3_PredictionModels)
- **GenomeSPOT**: AI-powered prediction of physiological characteristics (temperature, pH, salinity, oxygen requirements).
- **MicroBoost**: K-mer XGBoost medium prediction
- **ARG detection**: Antibiotic resistance gene screening

### 4. Main system (4_MainSystem)
- The main program that integrates all functions
- Intelligent Species Identification (FastANI + BLAST)
- Multi-model culture condition prediction
- GC content metabolic analysis
- Antibiotic screening recommendations

### 5. Database (5_Database)
- Strains information database
- Culture medium composition database
- Sequence index database

### 6. Toolset (6_Tools)
- Sequence statistical analysis
- Database maintenance tools
- Batch processing script

### 7. Output results (7_Results)
- Prediction results CSV
- Analysis report
- Run log

## 📊 Core functions

1. **Intelligent species identification**
   - FastANI（Whole genome）
   - BLAST（16S/partial sequence）
   - Automatic selection of the optimal algorithm

2. **Multidimensional cultivation prediction**
   - Excel database query (Known strains)
   - GenomeSPOT AI prediction (Physiological characteristics)
   - XGBoost machine learning (culture medium recommendation)
   - GC content metabolic analysis (carbon and nitrogen sources)

3. **Antibiotic screening**
   - ARG gene screening
   - Expert rule scoring
   - Usage advice and warnings

## 🔧 Environment dependency

### Python packages
```bash
pip install pandas numpy biopython xgboost scikit-learn psutil openpyxl
```

### External tools（WSL）
- FastANI
- BLAST+
- Prodigal

### Browser driver
- ChromeDriver (For data download)

## 📖 How to use？

### Quick start
```python
from EasyCulture.MainSystem import EasyCulture_Main

# Analyzing a single genome
EasyCulture_Main.analyze_genome("your_genome.fasta")
```

### Batch analysis
```python
EasyCulture_Main.batch_analyze("genome_folder/")
```

## 📝 Update log

### V1.1 (2026-3-11)
- Integrate all functional modules
- Unified project structure
- Add MicroBoost and XGBoost models
- Optimize code organization

## 👥 Author
Defeng Bai (baidefeng@caas.cn), Yu qiao, Yong-Xin Liu (liuyongxin@caas.cn)






