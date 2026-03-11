"""
EasyCulture 主程序测试脚本
简化版本，用于测试基本功能
"""

import os
import sys

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '4_MainSystem'))
sys.path.insert(0, os.path.dirname(__file__))

from config import *

print("="*80)
print("🧪 EasyCulture 测试脚本")
print("="*80)

# 测试输入文件
test_file = r"F:\JIYINZU-test\test-query line\GCA_000005845.2_ASM584v2_genomic.fna"

print(f"\n📄 测试文件: {os.path.basename(test_file)}")

if not os.path.exists(test_file):
    print(f"❌ 文件不存在: {test_file}")
    sys.exit(1)

file_size = os.path.getsize(test_file)
print(f"📊 文件大小: {file_size/1024/1024:.2f} MB")

# 检查序列库
print(f"\n📚 序列库检查:")
seq_lib = get_sequence_library_path()
print(f"   当前序列库: {seq_lib}")

if os.path.exists(seq_lib):
    seq_files = [f for f in os.listdir(seq_lib) if f.endswith(('.fasta', '.fna', '.fa'))]
    print(f"   序列文件数: {len(seq_files)}")
else:
    print(f"   ⚠️  序列库不存在")

# 检查数据库
print(f"\n📊 数据库检查:")
if os.path.exists(MEDIA_DATABASE):
    print(f"   ✅ 培养基数据库: {os.path.basename(MEDIA_DATABASE)}")
else:
    print(f"   ❌ 培养基数据库不存在")

if os.path.exists(DSMZ_DATABASE):
    print(f"   ✅ DSMZ 数据库: {os.path.basename(DSMZ_DATABASE)}")
else:
    print(f"   ❌ DSMZ 数据库不存在")

# 检查模型
print(f"\n🤖 模型检查:")
if os.path.exists(MICROBOOST_MODELS):
    model_files = [f for f in os.listdir(MICROBOOST_MODELS) if f.endswith('.pkl')]
    print(f"   ✅ MicroBoost 模型: {len(model_files)} 个")
else:
    print(f"   ⚠️  MicroBoost 模型目录不存在")

if os.path.exists(ARG_DATABASE_PATH):
    print(f"   ✅ ARG 数据库: {os.path.basename(ARG_DATABASE_PATH)}")
else:
    print(f"   ⚠️  ARG 数据库不存在")

# 测试 GC 含量计算
print(f"\n🧬 测试 GC 含量计算:")
try:
    total_bases = 0
    gc_bases = 0
    with open(test_file, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('>'):
                continue
            seq = line.upper()
            total_bases += len(seq)
            gc_bases += seq.count('G') + seq.count('C')
    
    if total_bases > 0:
        gc_content = (gc_bases / total_bases) * 100
        print(f"   GC 含量: {gc_content:.2f}%")
        
        # GC 代谢预测
        if gc_content <= 45.0:
            metabolic_type = "Sugar Specialist (糖类专食者)"
            recommendation = "推荐碳源: 葡萄糖、麦芽糖"
        elif gc_content >= 55.0:
            metabolic_type = "Acid Specialist (酸类专食者)"
            recommendation = "推荐碳源: 氨基酸、有机酸"
        else:
            metabolic_type = "Generalist (广谱型)"
            recommendation = "推荐: 混合碳源或复杂培养基"
        
        print(f"   代谢类型: {metabolic_type}")
        print(f"   {recommendation}")
    else:
        print(f"   ❌ 无法计算 GC 含量")
except Exception as e:
    print(f"   ❌ 计算出错: {e}")

# 测试 MicroBoost 预测
print(f"\n🧪 测试 MicroBoost K-mer 预测:")
try:
    sys.path.insert(0, MICROBOOST_DIR)
    from kmer_xgboost_predictor import extract_kmer_features, analyze_gc_content
    
    print("   正在提取 k-mer 特征...")
    feature_vector = extract_kmer_features(test_file, k=3)
    
    if feature_vector is not None:
        print(f"   ✅ 特征提取成功 (64 维)")
        
        gc_analysis = analyze_gc_content(feature_vector.to_dict())
        print(f"   GC 含量: {gc_analysis['gc_content']:.2f}%")
        print(f"   高GC k-mer 比例: {gc_analysis['high_gc_kmer_ratio']:.2f}%")
        print(f"   类型: {'高GC菌株' if gc_analysis['is_high_gc'] else '低/中GC菌株'}")
    else:
        print(f"   ❌ 特征提取失败")
        
except ImportError as e:
    print(f"   ⚠️  MicroBoost 模块未找到: {e}")
except Exception as e:
    print(f"   ❌ 预测出错: {e}")

# 测试 WSL 工具
print(f"\n🔧 WSL 工具检查:")
print(f"   FastANI: {FASTANI_EXE_WSL}")
print(f"   Prodigal: {PRODIGAL_EXE_WSL}")

try:
    import subprocess
    result = subprocess.run("wsl which blastn", shell=True, capture_output=True, text=True, timeout=5)
    if result.returncode == 0:
        print(f"   ✅ BLAST: {result.stdout.strip()}")
    else:
        print(f"   ⚠️  BLAST 未找到")
except Exception as e:
    print(f"   ⚠️  WSL 检查失败: {e}")

print("\n" + "="*80)
print("✅ 测试完成！")
print("="*80)

print("\n💡 下一步:")
print("   1. 确保 WSL 工具已安装 (FastANI, BLAST+, Prodigal)")
print("   2. 修改 config.py 中的 WSL 工具路径")
print("   3. 运行完整分析:")
print(f"      python 4_MainSystem/EasyCulture_Main.py \"{test_file}\"")
