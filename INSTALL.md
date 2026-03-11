# EasyCulture 安装指南

## 📋 系统要求

### 操作系统
- Windows 10/11 (推荐)
- Linux (Ubuntu 18.04+)
- macOS (10.14+)

### 硬件要求
- **CPU**: 4核心以上
- **内存**: 8GB+ (推荐 16GB)
- **硬盘**: 100GB+ 可用空间
- **网络**: 稳定的互联网连接（用于数据爬取）

## 🔧 环境准备

### 1. Python 环境

#### 安装 Python 3.8+
```bash
# Windows: 从 python.org 下载安装包
# Linux/macOS:
sudo apt-get install python3.8 python3-pip  # Ubuntu
brew install python@3.8  # macOS
```

#### 验证安装
```bash
python --version  # 应显示 Python 3.8 或更高版本
pip --version
```

### 2. WSL 环境 (Windows 用户)

#### 安装 WSL
```powershell
# 以管理员身份运行 PowerShell
wsl --install
```

#### 安装 Ubuntu
```powershell
wsl --install -d Ubuntu-20.04
```

#### 配置 WSL
```bash
# 在 WSL 中运行
sudo apt-get update
sudo apt-get upgrade
```

### 3. 生物信息工具

#### 安装 BLAST+
```bash
# WSL/Linux
sudo apt-get install ncbi-blast+

# 验证
blastn -version
```

#### 安装 Prodigal
```bash
# WSL/Linux
sudo apt-get install prodigal

# 验证
prodigal -v
```

#### 安装 FastANI
```bash
# 下载源码
cd ~
wget https://github.com/ParBLiSS/FastANI/releases/download/v1.34/FastANI-1.34.tar.gz
tar -xzf FastANI-1.34.tar.gz
cd FastANI-1.34

# 编译
mkdir build && cd build
cmake ..
make

# 验证
./fastANI -h
```

## 📦 安装 EasyCulture

### 方法 1: 直接使用（推荐）

```bash
# 1. 进入项目目录
cd F:\JIYINZU-test\EasyCulture

# 2. 安装 Python 依赖
pip install -r requirements.txt

# 3. 验证安装
python 4_MainSystem/config.py
```

### 方法 2: 从头安装

```bash
# 1. 创建虚拟环境
python -m venv venv

# 2. 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# 3. 安装依赖
pip install pandas numpy biopython xgboost scikit-learn psutil openpyxl selenium requests beautifulsoup4

# 4. 下载 ChromeDriver
# 访问 https://chromedriver.chromium.org/
# 下载对应版本并放入 6_Tools/ 目录
```

## 📝 创建 requirements.txt

在 `EasyCulture/` 目录下创建 `requirements.txt`:

```txt
pandas>=1.3.0
numpy>=1.21.0
biopython>=1.79
xgboost>=1.5.0
scikit-learn>=1.0.0
psutil>=5.8.0
openpyxl>=3.0.9
selenium>=4.0.0
requests>=2.26.0
beautifulsoup4>=4.10.0
lxml>=4.6.0
```

安装:
```bash
pip install -r requirements.txt
```

## ⚙️ 配置

### 1. 修改配置文件

编辑 `4_MainSystem/config.py`:

```python
# 修改 WSL 工具路径
FASTANI_EXE_WSL = "/home/你的用户名/FastANI-1.34/build/fastANI"
PRODIGAL_EXE_WSL = "/usr/bin/prodigal"

# 修改 ChromeDriver 路径（如果需要）
CHROMEDRIVER_PATH = os.path.join(TOOLS_DIR, "chromedriver.exe")
```

### 2. 准备数据

#### 序列库
```bash
# 将参考序列放入对应目录
# 2_SequenceData/DSMZ_sequences/
# 2_SequenceData/JCM_sequences/
# 2_SequenceData/ATCC_CCM_NCIMB/
```

#### 数据库文件
确保以下文件存在:
- `5_Database/dsmz_full_database.csv`
- `5_Database/JCM数据库全部爬取.csv`
- `5_Database/MediaDive培养基信息.xlsx`
- `5_Database/ATCC_CCM_NCIMB序列补充结果.csv`

#### 模型文件
确保以下目录存在:
- `3_PredictionModels/GenomeSPOT/models/`
- `3_PredictionModels/MicroBoost/model/`
- `3_PredictionModels/ARG_Database/arg_database.fasta`

## ✅ 验证安装

### 1. 测试配置
```bash
cd 4_MainSystem
python config.py
```

应该看到:
```
✅ 配置文件加载完成
📁 项目根目录: ...
📁 数据库目录: ...
...
```

### 2. 测试主程序
```bash
python EasyCulture_Main.py --help
```

应该看到帮助信息。

### 3. 运行测试分析
```bash
# 准备一个测试序列文件
python EasyCulture_Main.py path/to/test_genome.fasta
```

## 🐛 常见问题

### Q1: 提示 "ModuleNotFoundError"
```bash
# 解决方案: 安装缺失的包
pip install 缺失的包名
```

### Q2: WSL 工具找不到
```bash
# 解决方案: 检查 WSL 是否正确安装
wsl --list --verbose

# 进入 WSL 验证工具
wsl
which blastn
which prodigal
```

### Q3: ChromeDriver 版本不匹配
```bash
# 解决方案: 
# 1. 查看 Chrome 版本: chrome://version/
# 2. 下载对应版本的 ChromeDriver
# 3. 替换 6_Tools/chromedriver.exe
```

### Q4: 权限错误
```bash
# Windows: 以管理员身份运行
# Linux/macOS:
chmod +x 6_Tools/chromedriver
```

### Q5: 内存不足
```python
# 修改 config.py
MAX_WORKERS = 2  # 减少并行线程数
```

## 🔄 更新

### 更新 Python 包
```bash
pip install --upgrade pandas numpy xgboost scikit-learn
```

### 更新数据库
```bash
# 运行爬虫更新数据
python 1_DataCrawlers/DSMZ/dsmz_crawler_v63.py
python 1_DataCrawlers/JCM/JCM数据库全部爬取.py
```

### 更新模型
```bash
# 下载最新模型文件并替换
# 3_PredictionModels/GenomeSPOT/models/
# 3_PredictionModels/MicroBoost/model/
```

## 📚 下一步

安装完成后，请查看:
1. **QUICK_START.md** - 快速开始指南
2. **README.md** - 完整功能文档
3. **PROJECT_SUMMARY.md** - 项目总结

## 💡 性能优化建议

### 1. 使用 SSD
- 将序列数据存储在 SSD 上
- 提高文件读写速度

### 2. 增加内存
- 推荐 16GB+ 内存
- 可以处理更大的基因组

### 3. 多核 CPU
- 启用并行处理
- 修改 `MAX_WORKERS` 参数

### 4. 网络优化
- 使用稳定的网络连接
- 考虑使用代理（如果需要）

## 🔐 安全建议

1. **不要在公共网络上运行爬虫**
2. **定期备份数据库和序列文件**
3. **使用虚拟环境隔离依赖**
4. **注意 API 访问频率限制**

## 📞 获取帮助

如果遇到问题:
1. 查看 `7_Results/logs/` 中的日志文件
2. 参考各模块的 README 文档
3. 检查配置文件是否正确
4. 验证所有依赖是否安装

---

**安装完成后，请运行测试以确保一切正常！**

```bash
python 4_MainSystem/EasyCulture_Main.py --help
```
