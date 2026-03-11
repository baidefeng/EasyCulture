"""
==============================================================================
EasyCulture 系统配置文件
所有路径和参数的统一配置
==============================================================================
"""

import os

# ==============================================================================
# 基础路径配置
# ==============================================================================

# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 数据库路径
DATABASE_DIR = os.path.join(PROJECT_ROOT, "5_Database")
DSMZ_DATABASE = os.path.join(DATABASE_DIR, "dsmz_full_database.csv")
JCM_DATABASE = os.path.join(DATABASE_DIR, "JCM数据库全部爬取.csv")
MEDIA_DATABASE = os.path.join(DATABASE_DIR, "MediaDive培养基信息.xlsx")
ATCC_DATABASE = os.path.join(DATABASE_DIR, "ATCC_CCM_NCIMB序列补充结果.csv")

# 序列数据路径
SEQUENCE_DIR = os.path.join(PROJECT_ROOT, "2_SequenceData")
DSMZ_SEQ_DIR = os.path.join(SEQUENCE_DIR, "DSMZ_sequences")
JCM_SEQ_DIR = os.path.join(SEQUENCE_DIR, "JCM_sequences")
ATCC_SEQ_DIR = os.path.join(SEQUENCE_DIR, "ATCC_CCM_NCIMB")
TEST_SEQ_DIR = os.path.join(SEQUENCE_DIR, "test_sequences")

# 模型路径
MODEL_DIR = os.path.join(PROJECT_ROOT, "3_PredictionModels")
GENOMESPOT_DIR = os.path.join(MODEL_DIR, "GenomeSPOT")
GENOMESPOT_MODELS = os.path.join(GENOMESPOT_DIR, "models")
MICROBOOST_DIR = os.path.join(MODEL_DIR, "MicroBoost")
MICROBOOST_MODELS = os.path.join(MICROBOOST_DIR, "model")
ARG_DATABASE_DIR = os.path.join(MODEL_DIR, "ARG_Database")
ARG_DATABASE_PATH = os.path.join(ARG_DATABASE_DIR, "arg_database.fasta")

# 工具路径
TOOLS_DIR = os.path.join(PROJECT_ROOT, "6_Tools")
CHROMEDRIVER_PATH = os.path.join(TOOLS_DIR, "chromedriver.exe")

# 结果输出路径
RESULTS_DIR = os.path.join(PROJECT_ROOT, "7_Results")
PREDICTIONS_DIR = os.path.join(RESULTS_DIR, "predictions")
REPORTS_DIR = os.path.join(RESULTS_DIR, "reports")
LOGS_DIR = os.path.join(RESULTS_DIR, "logs")

# ==============================================================================
# WSL 工具路径配置
# ==============================================================================

FASTANI_EXE_WSL = "/home/yuqiao/FastANI-1.34/build/fastANI"
PRODIGAL_EXE_WSL = "/usr/bin/prodigal"
BLAST_WSL = "blastn"
MAKEBLASTDB_WSL = "makeblastdb"

# ==============================================================================
# 分析参数配置
# ==============================================================================

# 文件大小阈值（用于选择 FastANI 或 BLAST）
SIZE_THRESHOLD_MB = 2  # 2MB
SIZE_THRESHOLD = SIZE_THRESHOLD_MB * 1024 * 1024

# FastANI 参数
FASTANI_MIN_FRACTION = 0.05
FASTANI_MIN_ANI = 75.0

# BLAST 参数
BLAST_MAX_TARGET_SEQS = 1
BLAST_EVALUE = 1e-5

# 质量控制阈值
MIN_WGS_SIZE_KB = 500   # WGS 最小文件大小 (KB)
MIN_16S_LENGTH = 1200   # 16S 最小长度 (bp)
MAX_16S_LENGTH = 1800   # 16S 最大长度 (bp)

# ARG 检测参数
ARG_MIN_IDENTITY = 90   # 最小相似度 (%)
ARG_MIN_COVERAGE = 80   # 最小覆盖度 (%)

# GC 含量阈值
GC_LOW_THRESHOLD = 45.0   # 低 GC 阈值
GC_HIGH_THRESHOLD = 55.0  # 高 GC 阈值

# K-mer 参数
KMER_LENGTH = 3

# ==============================================================================
# Excel 列名配置
# ==============================================================================

COL_ID = "DSM编号"
COL_MEDIA = "成分"
COL_CURRENT_ID = "当前ID"
COL_TEMP = "培养温度"
COL_TIME = "培养时间"
COL_ENV = "环境条件"

# ==============================================================================
# 输出格式配置
# ==============================================================================

# 日志格式
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# CSV 编码
CSV_ENCODING = "utf-8-sig"

# ==============================================================================
# 功能开关
# ==============================================================================

ENABLE_FASTANI = True
ENABLE_BLAST = True
ENABLE_GENOMESPOT = True
ENABLE_MICROBOOST = True
ENABLE_ARG_DETECTION = True
ENABLE_GC_ANALYSIS = True

# ==============================================================================
# 性能配置
# ==============================================================================

# 浏览器重启间隔（爬虫用）
BROWSER_RESTART_INTERVAL = 20

# 并行处理线程数
MAX_WORKERS = 4

# 超时设置（秒）
FASTANI_TIMEOUT = 300
BLAST_TIMEOUT = 300
DOWNLOAD_TIMEOUT = 180

# ==============================================================================
# 辅助函数
# ==============================================================================

def ensure_directories():
    """确保所有必要的目录存在"""
    dirs = [
        DATABASE_DIR, SEQUENCE_DIR, MODEL_DIR, TOOLS_DIR, RESULTS_DIR,
        PREDICTIONS_DIR, REPORTS_DIR, LOGS_DIR,
        DSMZ_SEQ_DIR, JCM_SEQ_DIR, ATCC_SEQ_DIR, TEST_SEQ_DIR
    ]
    for dir_path in dirs:
        os.makedirs(dir_path, exist_ok=True)

def to_wsl_path(win_path):
    """将 Windows 路径转换为 WSL 路径"""
    path = win_path.replace("\\", "/")
    if ":" in path:
        drive, rest = path.split(":", 1)
        return f"/mnt/{drive.lower()}{rest}"
    return path

def get_sequence_library_path():
    """
    获取序列库路径
    优先级: DSMZ > JCM > ATCC
    """
    if os.path.exists(DSMZ_SEQ_DIR) and os.listdir(DSMZ_SEQ_DIR):
        return DSMZ_SEQ_DIR
    elif os.path.exists(JCM_SEQ_DIR) and os.listdir(JCM_SEQ_DIR):
        return JCM_SEQ_DIR
    elif os.path.exists(ATCC_SEQ_DIR) and os.listdir(ATCC_SEQ_DIR):
        return ATCC_SEQ_DIR
    return TEST_SEQ_DIR

# ==============================================================================
# 初始化
# ==============================================================================

if __name__ == "__main__":
    # 创建必要的目录
    ensure_directories()
    print("✅ 配置文件加载完成")
    print(f"📁 项目根目录: {PROJECT_ROOT}")
    print(f"📁 数据库目录: {DATABASE_DIR}")
    print(f"📁 序列数据目录: {SEQUENCE_DIR}")
    print(f"📁 模型目录: {MODEL_DIR}")
    print(f"📁 结果目录: {RESULTS_DIR}")
