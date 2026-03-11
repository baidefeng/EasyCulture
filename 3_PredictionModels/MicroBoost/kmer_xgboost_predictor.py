"""
==============================================================================
K-mer XGBoost 培养基预测模型
功能：
1. 从基因组序列提取 k-mer 特征（3-mer 频率）
2. 使用 XGBoost 模型预测在不同培养基上的生长能力
3. 分析特定 k-mer 组合（如高 GC 相关片段）与培养基的关系
4. 提供特征重要性分析，发现关键 k-mer 模式
==============================================================================
"""

import os
import sys
import pickle
import pandas as pd
import numpy as np
from collections import Counter
import warnings
warnings.filterwarnings("ignore")

# 尝试导入 XGBoost
try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    print("⚠️  XGBoost 未安装，请运行: pip install xgboost")
    XGBOOST_AVAILABLE = False

# ==============================================================================
# 配置区域
# ==============================================================================

# MicroBoost 模型文件夹路径
MODEL_DIR = r"F:\JIYINZU-test\MicroBoost\model"

# K-mer 长度（默认使用 3-mer，与训练数据一致）
KMER_LENGTH = 3

# 所有可能的 3-mer 组合（64种）
ALL_KMERS = [
    'AAA', 'AAC', 'AAG', 'AAT', 'ACA', 'ACC', 'ACG', 'ACT',
    'AGA', 'AGC', 'AGG', 'AGT', 'ATA', 'ATC', 'ATG', 'ATT',
    'CAA', 'CAC', 'CAG', 'CAT', 'CCA', 'CCC', 'CCG', 'CCT',
    'CGA', 'CGC', 'CGG', 'CGT', 'CTA', 'CTC', 'CTG', 'CTT',
    'GAA', 'GAC', 'GAG', 'GAT', 'GCA', 'GCC', 'GCG', 'GCT',
    'GGA', 'GGC', 'GGG', 'GGT', 'GTA', 'GTC', 'GTG', 'GTT',
    'TAA', 'TAC', 'TAG', 'TAT', 'TCA', 'TCC', 'TCG', 'TCT',
    'TGA', 'TGC', 'TGG', 'TGT', 'TTA', 'TTC', 'TTG', 'TTT'
]

# 高 GC 相关的 k-mer（GC含量 >= 66.7%，即3个碱基中至少2个是G或C）
HIGH_GC_KMERS = [
    'ACC', 'ACG', 'AGC', 'AGG', 'CAC', 'CAG', 'CCA', 'CCC', 
    'CCG', 'CCT', 'CGA', 'CGC', 'CGG', 'CGT', 'CTA', 'CTC', 
    'CTG', 'GAC', 'GAG', 'GCA', 'GCC', 'GCG', 'GCT', 'GGA', 
    'GGC', 'GGG', 'GGT', 'GTC', 'GTG', 'TCC', 'TCG', 'TGC', 'TGG'
]

# ==============================================================================
# K-mer 特征提取
# ==============================================================================

def extract_sequence_from_fasta(fasta_path):
    """从 FASTA 文件中提取序列"""
    sequence = []
    try:
        with open(fasta_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('>'):
                    continue
                sequence.append(line.upper())
        return ''.join(sequence)
    except Exception as e:
        print(f"❌ 读取序列文件失败: {e}")
        return ""

def calculate_kmer_frequency(sequence, k=3):
    """
    计算 k-mer 频率
    返回归一化的频率字典
    """
    if len(sequence) < k:
        return {kmer: 0.0 for kmer in ALL_KMERS}
    
    # 统计 k-mer 出现次数
    kmer_counts = Counter()
    total_kmers = len(sequence) - k + 1
    
    for i in range(total_kmers):
        kmer = sequence[i:i+k]
        # 只统计标准碱基
        if all(base in 'ATCG' for base in kmer):
            kmer_counts[kmer] += 1
    
    # 归一化为频率
    kmer_freq = {}
    for kmer in ALL_KMERS:
        kmer_freq[kmer] = kmer_counts.get(kmer, 0) / total_kmers if total_kmers > 0 else 0.0
    
    return kmer_freq

def extract_kmer_features(fasta_path, k=3):
    """
    从 FASTA 文件提取 k-mer 特征向量
    返回 pandas Series，列名与训练数据一致
    """
    print(f"🧬 正在提取 {k}-mer 特征...")
    
    sequence = extract_sequence_from_fasta(fasta_path)
    if not sequence:
        return None
    
    kmer_freq = calculate_kmer_frequency(sequence, k)
    
    # 转换为 pandas Series，保持列顺序与训练数据一致
    feature_vector = pd.Series(kmer_freq, index=ALL_KMERS)
    
    print(f"   ✅ 序列长度: {len(sequence):,} bp")
    print(f"   ✅ 提取了 {len(ALL_KMERS)} 个 {k}-mer 特征")
    
    return feature_vector

# ==============================================================================
# GC 含量分析
# ==============================================================================

def analyze_gc_content(kmer_freq):
    """
    分析 GC 含量和高 GC k-mer 的比例
    """
    # 计算高 GC k-mer 的总频率
    high_gc_freq = sum(kmer_freq.get(kmer, 0) for kmer in HIGH_GC_KMERS)
    
    # 计算整体 GC 含量（基于 k-mer 频率估算）
    gc_content = 0
    for kmer, freq in kmer_freq.items():
        gc_count = kmer.count('G') + kmer.count('C')
        gc_content += (gc_count / 3) * freq
    
    gc_content *= 100  # 转换为百分比
    
    return {
        'gc_content': gc_content,
        'high_gc_kmer_ratio': high_gc_freq * 100,
        'is_high_gc': gc_content >= 55.0
    }

# ==============================================================================
# 模型预测
# ==============================================================================

def load_models(model_dir):
    """加载所有培养基模型"""
    models = {}
    
    if not os.path.exists(model_dir):
        print(f"❌ 模型文件夹不存在: {model_dir}")
        return models
    
    print(f"📦 正在加载模型...")
    
    for model_file in os.listdir(model_dir):
        if model_file.endswith('.pkl'):
            model_path = os.path.join(model_dir, model_file)
            try:
                with open(model_path, 'rb') as f:
                    model = pickle.load(f)
                    media_name = model_file[:-4]  # 移除 .pkl 后缀
                    models[media_name] = model
            except Exception as e:
                print(f"   ⚠️ 加载模型 {model_file} 失败: {e}")
    
    print(f"   ✅ 成功加载 {len(models)} 个培养基模型")
    return models

def predict_media_growth(feature_vector, models):
    """
    使用所有模型预测生长能力
    返回预测结果 DataFrame
    """
    if feature_vector is None or len(models) == 0:
        return None
    
    print(f"\n🔮 正在预测 {len(models)} 种培养基的生长能力...")
    
    # 将特征向量转换为 DataFrame（单行）
    X = pd.DataFrame([feature_vector])
    
    predictions = {}
    for media_name, model in models.items():
        try:
            pred = model.predict(X)[0]
            predictions[media_name] = pred
        except Exception as e:
            print(f"   ⚠️ 预测 {media_name} 失败: {e}")
            predictions[media_name] = None
    
    # 转换为 DataFrame 并排序
    result_df = pd.DataFrame([predictions])
    
    return result_df

# ==============================================================================
# 特征重要性分析（针对 XGBoost 模型）
# ==============================================================================

def analyze_feature_importance(models, top_n=10):
    """
    分析模型的特征重要性
    找出对培养基生长最重要的 k-mer
    """
    if not XGBOOST_AVAILABLE:
        print("⚠️  XGBoost 未安装，无法进行特征重要性分析")
        return None
    
    print(f"\n📊 分析特征重要性（Top {top_n} k-mers）...")
    
    importance_summary = {}
    
    for media_name, model in models.items():
        # 检查是否是 XGBoost 模型
        if hasattr(model, 'get_booster'):
            try:
                # 获取特征重要性
                importance = model.get_booster().get_score(importance_type='gain')
                
                # 转换特征名（f0 -> AAA, f1 -> AAC, ...）
                importance_named = {}
                for feat_idx, score in importance.items():
                    idx = int(feat_idx.replace('f', ''))
                    if idx < len(ALL_KMERS):
                        kmer = ALL_KMERS[idx]
                        importance_named[kmer] = score
                
                # 排序并取 Top N
                sorted_importance = sorted(importance_named.items(), 
                                          key=lambda x: x[1], reverse=True)[:top_n]
                
                importance_summary[media_name] = sorted_importance
                
            except Exception as e:
                print(f"   ⚠️ 分析 {media_name} 失败: {e}")
    
    return importance_summary

def print_feature_importance(importance_summary):
    """打印特征重要性分析结果"""
    if not importance_summary:
        return
    
    print("\n" + "="*80)
    print("🔬 关键 K-mer 特征分析")
    print("="*80)
    
    for media_name, importance_list in importance_summary.items():
        print(f"\n📌 培养基: {media_name}")
        print("   " + "-"*60)
        
        # 统计高 GC k-mer 的数量
        high_gc_count = sum(1 for kmer, _ in importance_list if kmer in HIGH_GC_KMERS)
        
        for rank, (kmer, score) in enumerate(importance_list, 1):
            gc_tag = " [高GC]" if kmer in HIGH_GC_KMERS else ""
            print(f"   {rank:2d}. {kmer}{gc_tag:<8} | 重要性: {score:>10.2f}")
        
        print(f"\n   💡 高GC k-mer 占比: {high_gc_count}/{len(importance_list)} "
              f"({high_gc_count/len(importance_list)*100:.1f}%)")

# ==============================================================================
# 结果展示
# ==============================================================================

def display_predictions(predictions, gc_analysis):
    """展示预测结果"""
    if predictions is None or predictions.empty:
        print("❌ 无预测结果")
        return
    
    print("\n" + "="*80)
    print("🎯 培养基生长预测结果")
    print("="*80)
    
    # GC 含量信息
    print(f"\n🧬 基因组特征:")
    print(f"   • GC 含量: {gc_analysis['gc_content']:.2f}%")
    print(f"   • 高GC k-mer 比例: {gc_analysis['high_gc_kmer_ratio']:.2f}%")
    print(f"   • 类型: {'高GC菌株 (≥55%)' if gc_analysis['is_high_gc'] else '低/中GC菌株 (<55%)'}")
    
    # 预测结果
    print(f"\n📊 预测结果（共 {len(predictions.columns)} 种培养基）:")
    print("   " + "-"*60)
    
    # 转换为列表并排序
    results = []
    for media_name in predictions.columns:
        pred_value = predictions[media_name].iloc[0]
        if pred_value is not None:
            results.append((media_name, pred_value))
    
    # 按预测值排序（假设值越大越好）
    results.sort(key=lambda x: x[1], reverse=True)
    
    # 显示 Top 10
    print("\n   ✅ Top 10 推荐培养基:")
    for rank, (media_name, pred_value) in enumerate(results[:10], 1):
        # 简单的评级
        if pred_value >= 0.7:
            rating = "⭐⭐⭐ 强烈推荐"
        elif pred_value >= 0.5:
            rating = "⭐⭐ 推荐"
        elif pred_value >= 0.3:
            rating = "⭐ 可尝试"
        else:
            rating = "❓ 不确定"
        
        print(f"   {rank:2d}. {media_name:<15} | 预测值: {pred_value:>6.3f} | {rating}")
    
    # 显示 Bottom 5
    if len(results) > 10:
        print("\n   ⚠️  不推荐的培养基 (Bottom 5):")
        for rank, (media_name, pred_value) in enumerate(results[-5:], 1):
            print(f"   {rank:2d}. {media_name:<15} | 预测值: {pred_value:>6.3f}")

# ==============================================================================
# 主函数
# ==============================================================================

def predict_from_genome(fasta_path, model_dir=MODEL_DIR, analyze_importance=True):
    """
    从基因组序列预测培养基生长能力
    
    参数:
        fasta_path: 基因组序列文件路径（FASTA格式）
        model_dir: 模型文件夹路径
        analyze_importance: 是否进行特征重要性分析
    
    返回:
        predictions: 预测结果 DataFrame
        gc_analysis: GC 含量分析结果
    """
    print("\n" + "="*80)
    print("🚀 K-mer XGBoost 培养基预测系统")
    print("="*80)
    print(f"📄 输入文件: {os.path.basename(fasta_path)}")
    
    # 1. 提取 k-mer 特征
    feature_vector = extract_kmer_features(fasta_path, k=KMER_LENGTH)
    if feature_vector is None:
        return None, None
    
    # 2. GC 含量分析
    gc_analysis = analyze_gc_content(feature_vector.to_dict())
    
    # 3. 加载模型
    models = load_models(model_dir)
    if not models:
        return None, gc_analysis
    
    # 4. 预测
    predictions = predict_media_growth(feature_vector, models)
    
    # 5. 展示结果
    display_predictions(predictions, gc_analysis)
    
    # 6. 特征重要性分析（可选）
    if analyze_importance and XGBOOST_AVAILABLE:
        importance_summary = analyze_feature_importance(models, top_n=10)
        print_feature_importance(importance_summary)
    
    return predictions, gc_analysis

def save_predictions(predictions, output_path):
    """保存预测结果到 CSV"""
    if predictions is not None:
        predictions.to_csv(output_path, index=False)
        print(f"\n💾 预测结果已保存到: {output_path}")

# ==============================================================================
# 命令行接口
# ==============================================================================

if __name__ == "__main__":
    # 示例用法
    if len(sys.argv) > 1:
        input_fasta = sys.argv[1]
    else:
        # 默认测试文件
        input_fasta = r"F:\JIYINZU-test\test-query line\GCA_000005845.2_ASM584v2_genomic.fna"
    
    if not os.path.exists(input_fasta):
        print(f"❌ 文件不存在: {input_fasta}")
        print("\n使用方法:")
        print("  python kmer_xgboost_predictor.py <基因组序列文件.fasta>")
        sys.exit(1)
    
    # 运行预测
    predictions, gc_analysis = predict_from_genome(
        input_fasta, 
        model_dir=MODEL_DIR,
        analyze_importance=True
    )
    
    # 保存结果
    if predictions is not None:
        output_dir = os.path.dirname(input_fasta)
        output_file = os.path.join(output_dir, "kmer_predictions.csv")
        save_predictions(predictions, output_file)
    
    print("\n" + "="*80)
    print("✅ 分析完成！")
    print("="*80)
