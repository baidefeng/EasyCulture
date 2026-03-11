"""
==============================================================================
V24-12-15 与 K-mer XGBoost 模型集成示例
展示如何在现有分析流程中添加 XGBoost 培养基预测
==============================================================================
"""

import sys
import os

# 添加路径以便导入模块
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
if PARENT_DIR not in sys.path:
    sys.path.append(PARENT_DIR)

# 导入 K-mer XGBoost 预测器
try:
    from MicroBoost.kmer_xgboost_predictor import predict_from_genome, save_predictions
    KMER_PREDICTOR_AVAILABLE = True
except ImportError:
    print("⚠️  K-mer XGBoost 预测器未找到")
    KMER_PREDICTOR_AVAILABLE = False

# ==============================================================================
# 集成函数：在 V24-12-15 的主流程中调用
# ==============================================================================

def run_xgboost_media_prediction(input_fasta_path, output_dir=None):
    """
    运行 XGBoost 培养基预测
    
    这个函数可以插入到 V24-12-15.py 的 run_smart_analysis() 函数中
    建议在以下位置调用：
    1. 物种鉴定完成后
    2. Excel 查询之前或之后（作为补充预测）
    3. AI 预测（GenomeSPOT）之前或之后
    
    参数:
        input_fasta_path: 基因组序列文件路径
        output_dir: 输出目录（可选）
    """
    if not KMER_PREDICTOR_AVAILABLE:
        print("⚠️  XGBoost 预测模块未加载，跳过")
        return None, None
    
    print("\n" + "="*80)
    print("🧪 [XGBoost 增强] K-mer 培养基预测")
    print("   (基于基因组序列特征的机器学习预测)")
    print("="*80)
    
    try:
        # 运行预测
        predictions, gc_analysis = predict_from_genome(
            input_fasta_path,
            analyze_importance=True  # 显示特征重要性
        )
        
        # 保存结果
        if predictions is not None and output_dir:
            output_file = os.path.join(output_dir, "xgboost_media_predictions.csv")
            save_predictions(predictions, output_file)
        
        return predictions, gc_analysis
        
    except Exception as e:
        print(f"❌ XGBoost 预测出错: {e}")
        import traceback
        traceback.print_exc()
        return None, None

# ==============================================================================
# 完整集成示例
# ==============================================================================

def enhanced_analysis_with_xgboost(input_file):
    """
    增强版分析流程，集成了 XGBoost 预测
    这是一个简化的示例，展示如何在 V24-12-15 中添加 XGBoost
    """
    print("🚀 [增强版] 启动分析...")
    print(f"📄 待测文件: {os.path.basename(input_file)}")
    
    if not os.path.exists(input_file):
        print("❌ 文件不存在")
        return
    
    # ========== 步骤 1: 物种鉴定 ==========
    # （这里省略，使用 V24-12-15 的 FastANI/BLAST 逻辑）
    print("\n[步骤 1] 物种鉴定...")
    print("   （使用 FastANI 或 BLAST）")
    
    # ========== 步骤 2: Excel 培养基查询 ==========
    # （这里省略，使用 V24-12-15 的 Excel 查询逻辑）
    print("\n[步骤 2] Excel 培养基查询...")
    print("   （查询已知培养条件）")
    
    found_in_excel = False  # 假设未找到
    
    # ========== 步骤 3: XGBoost 培养基预测（新增）==========
    # 🔥 关键集成点：无论 Excel 是否找到，都可以运行 XGBoost 预测
    # 作为补充或验证
    
    if not found_in_excel:
        print("\n⚠️ Excel 未找到培养方案，启动 XGBoost 预测...")
    else:
        print("\n💡 Excel 已找到方案，XGBoost 提供额外预测...")
    
    predictions, gc_analysis = run_xgboost_media_prediction(
        input_file,
        output_dir=os.path.dirname(input_file)
    )
    
    # ========== 步骤 4: AI 生理特征预测（GenomeSPOT）==========
    # （这里省略，使用 V24-12-15 的 GenomeSPOT 逻辑）
    if not found_in_excel:
        print("\n[步骤 4] GenomeSPOT 生理特征预测...")
        print("   （预测温度、pH、氧气需求等）")
    
    # ========== 步骤 5: GC 代谢预测 ==========
    # （这里省略，使用 V24-12-15 的 GC 预测逻辑）
    print("\n[步骤 5] GC 代谢预测...")
    print("   （碳氮源推荐）")
    
    # ========== 步骤 6: 抗性基因检测 ==========
    # （这里省略，使用 V24-12-15 的 ARG 检测逻辑）
    print("\n[步骤 6] 抗性基因检测...")
    print("   （抗生素筛选建议）")
    
    print("\n✅ 分析完成！")

# ==============================================================================
# 如何修改 V24-12-15.py
# ==============================================================================

"""
在 V24-12-15.py 的 run_smart_analysis() 函数中添加以下代码：

# ========== 在物种鉴定和 Excel 查询之后添加 ==========

# 导入 XGBoost 预测器（在文件顶部）
try:
    from MicroBoost.kmer_xgboost_predictor import predict_from_genome, save_predictions
    KMER_PREDICTOR_AVAILABLE = True
except ImportError:
    KMER_PREDICTOR_AVAILABLE = False

# 在 run_smart_analysis() 函数中，Excel 查询之后添加：

    # 4. [新增] XGBoost 培养基预测
    if KMER_PREDICTOR_AVAILABLE:
        print("\n" + "="*80)
        print("🧪 [XGBoost 增强] K-mer 培养基预测")
        print("="*80)
        
        try:
            predictions, gc_analysis = predict_from_genome(
                input_file,
                analyze_importance=True
            )
            
            if predictions is not None:
                output_file = os.path.join(GENOME_FOLDER_WIN, "xgboost_predictions.csv")
                save_predictions(predictions, output_file)
        except Exception as e:
            print(f"❌ XGBoost 预测出错: {e}")

# ========== 或者，作为 Excel 未找到时的补充 ==========

    if not found_in_excel:
        print("\n⚠️ Excel 未找到培养方案，启动多模型预测...")
        
        # GenomeSPOT 预测
        run_ai_prediction(input_file)
        
        # XGBoost 预测（新增）
        if KMER_PREDICTOR_AVAILABLE:
            try:
                predictions, gc_analysis = predict_from_genome(input_file)
                if predictions is not None:
                    output_file = os.path.join(GENOME_FOLDER_WIN, "xgboost_predictions.csv")
                    save_predictions(predictions, output_file)
            except Exception as e:
                print(f"❌ XGBoost 预测出错: {e}")
"""

# ==============================================================================
# 测试运行
# ==============================================================================

if __name__ == "__main__":
    # 测试文件路径
    test_file = r"F:\JIYINZU-test\test-query line\GCA_000005845.2_ASM584v2_genomic.fna"
    
    if os.path.exists(test_file):
        # 运行增强版分析
        enhanced_analysis_with_xgboost(test_file)
    else:
        print(f"❌ 测试文件不存在: {test_file}")
        print("\n请修改 test_file 变量为实际的基因组序列文件路径")
