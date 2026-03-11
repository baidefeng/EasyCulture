"""
==============================================================================
EasyCulture - 智能微生物培养系统 主程序
整合版本 V1.0

功能模块:
1. 智能物种鉴定 (FastANI + BLAST)
2. 培养基数据库查询 (Excel)
3. AI 生理特征预测 (GenomeSPOT)
4. 机器学习培养基推荐 (MicroBoost XGBoost)
5. GC 含量代谢分析
6. 抗生素抗性基因检测 (ARG)
==============================================================================
"""

import os
import sys
import time
import warnings
warnings.filterwarnings("ignore")

# 添加项目路径
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

# 导入配置
from config import *

# 导入核心模块
try:
    # 尝试导入 V24-12-15 的核心功能
    sys.path.append(os.path.dirname(PROJECT_ROOT))
    from V24_12_15_core import (
        run_fastani, run_blast, check_antibiotic_resistance,
        calculate_gc_content, predict_carbon_nitrogen_preference,
        extract_id_number, cleanup_temp_files
    )
    V24_CORE_AVAILABLE = True
except ImportError:
    print("⚠️  V24 核心模块未找到，部分功能将不可用")
    V24_CORE_AVAILABLE = False

# 导入 GenomeSPOT
try:
    sys.path.append(GENOMESPOT_DIR)
    from genome_spot.genome_spot import GenomeSPOT
    from genome_spot.bioinformatics.genome import measure_genome_features
    GENOMESPOT_AVAILABLE = True
except ImportError:
    print("⚠️  GenomeSPOT 模块未找到")
    GENOMESPOT_AVAILABLE = False

# 导入 MicroBoost
try:
    sys.path.append(MICROBOOST_DIR)
    from kmer_xgboost_predictor import predict_from_genome, save_predictions
    MICROBOOST_AVAILABLE = True
except ImportError:
    print("⚠️  MicroBoost 模块未找到")
    MICROBOOST_AVAILABLE = False

import pandas as pd
import subprocess

# ==============================================================================
# 主分析流程
# ==============================================================================

class EasyCulture:
    """EasyCulture 主类"""
    
    def __init__(self, config_override=None):
        """
        初始化 EasyCulture 系统
        
        参数:
            config_override: 配置覆盖字典（可选）
        """
        self.config = self._load_config(config_override)
        self.results = {}
        
        # 确保目录存在
        ensure_directories()
        
        print("="*80)
        print("🚀 EasyCulture - 智能微生物培养系统")
        print("="*80)
        print(f"📦 GenomeSPOT: {'✅' if GENOMESPOT_AVAILABLE else '❌'}")
        print(f"📦 MicroBoost: {'✅' if MICROBOOST_AVAILABLE else '❌'}")
        print(f"📦 V24 Core: {'✅' if V24_CORE_AVAILABLE else '❌'}")
        print("="*80 + "\n")
    
    def _load_config(self, override=None):
        """加载配置"""
        config = {
            'database_dir': DATABASE_DIR,
            'sequence_dir': get_sequence_library_path(),
            'model_dir': MODEL_DIR,
            'results_dir': RESULTS_DIR,
            'enable_fastani': ENABLE_FASTANI,
            'enable_blast': ENABLE_BLAST,
            'enable_genomespot': ENABLE_GENOMESPOT,
            'enable_microboost': ENABLE_MICROBOOST,
            'enable_arg': ENABLE_ARG_DETECTION,
            'enable_gc': ENABLE_GC_ANALYSIS,
        }
        
        if override:
            config.update(override)
        
        return config
    
    def analyze_genome(self, input_fasta, output_dir=None):
        """
        分析单个基因组
        
        参数:
            input_fasta: 输入基因组文件路径
            output_dir: 输出目录（可选）
        
        返回:
            results: 分析结果字典
        """
        if not os.path.exists(input_fasta):
            print(f"❌ 文件不存在: {input_fasta}")
            return None
        
        if output_dir is None:
            output_dir = PREDICTIONS_DIR
        
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"\n📄 分析文件: {os.path.basename(input_fasta)}")
        print(f"📊 文件大小: {os.path.getsize(input_fasta)/1024/1024:.2f} MB")
        
        start_time = time.time()
        self.results = {
            'input_file': input_fasta,
            'file_size': os.path.getsize(input_fasta),
            'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # 步骤 1: 物种鉴定
        self._step1_identification(input_fasta)
        
        # 步骤 2: 培养基查询
        self._step2_media_query()
        
        # 步骤 3: AI 预测（如果需要）
        if not self.results.get('found_in_excel', False):
            self._step3_ai_prediction(input_fasta)
        
        # 步骤 4: XGBoost 培养基预测
        if self.config['enable_microboost'] and MICROBOOST_AVAILABLE:
            self._step4_xgboost_prediction(input_fasta, output_dir)
        
        # 步骤 5: GC 代谢分析
        if self.config['enable_gc']:
            self._step5_gc_analysis(input_fasta)
        
        # 步骤 6: 抗性基因检测
        if self.config['enable_arg'] and self.results.get('is_whole_genome', False):
            self._step6_arg_detection(input_fasta)
        
        # 生成报告
        elapsed_time = time.time() - start_time
        self.results['elapsed_time'] = elapsed_time
        
        self._generate_report(output_dir)
        
        print(f"\n⏱️  总耗时: {elapsed_time:.2f} 秒")
        print(f"📁 结果保存至: {output_dir}")
        
        return self.results
    
    def _step1_identification(self, input_fasta):
        """步骤 1: 物种鉴定"""
        print("\n" + "="*80)
        print("🔍 [步骤 1] 物种鉴定")
        print("="*80)
        
        if not V24_CORE_AVAILABLE:
            print("❌ V24 核心模块不可用，跳过物种鉴定")
            return
        
        file_size = os.path.getsize(input_fasta)
        query_wsl = to_wsl_path(input_fasta)
        seq_library = self.config['sequence_dir']
        
        result = None
        is_whole_genome = False
        
        if file_size < SIZE_THRESHOLD:
            print(f"📊 短序列 ({file_size/1024:.1f} KB) -> 使用 BLAST")
            if self.config['enable_blast']:
                result = run_blast(query_wsl, seq_library)
        else:
            print(f"📊 全基因组 ({file_size/1024/1024:.1f} MB) -> 使用 FastANI")
            is_whole_genome = True
            if self.config['enable_fastani']:
                result = run_fastani(query_wsl, seq_library)
        
        self.results['is_whole_genome'] = is_whole_genome
        self.results['identification'] = result
        
        if result:
            print(f"✅ 鉴定结果: {result['filename']}")
            print(f"   相似度: {result['score']:.2f}% ({result['type']})")
        else:
            print("❌ 未找到匹配菌株")
    
    def _step2_media_query(self):
        """步骤 2: 培养基数据库查询"""
        print("\n" + "="*80)
        print("📚 [步骤 2] 培养基数据库查询")
        print("="*80)
        
        result = self.results.get('identification')
        if not result:
            print("⚠️  无鉴定结果，跳过数据库查询")
            self.results['found_in_excel'] = False
            return
        
        if not os.path.exists(MEDIA_DATABASE):
            print(f"❌ 培养基数据库不存在: {MEDIA_DATABASE}")
            self.results['found_in_excel'] = False
            return
        
        try:
            search_id = extract_id_number(result['filename'])
            df_excel = pd.read_excel(MEDIA_DATABASE)
            df_excel[COL_ID] = df_excel[COL_ID].astype(str).str.strip()
            
            target_rows = df_excel[df_excel[COL_ID] == str(search_id)].drop_duplicates(subset=[COL_CURRENT_ID])
            
            if not target_rows.empty:
                print(f"✅ 找到 {len(target_rows)} 个培养方案")
                self.results['found_in_excel'] = True
                self.results['media_recipes'] = target_rows.to_dict('records')
                
                for idx, row in enumerate(target_rows.iterrows(), 1):
                    _, data = row
                    print(f"\n   方案 {idx}:")
                    print(f"   🌡️  温度: {data.get(COL_TEMP, 'N/A')}")
                    print(f"   ⏱️  时间: {data.get(COL_TIME, 'N/A')}")
                    print(f"   🧪 成分: {str(data.get(COL_MEDIA, 'N/A'))[:100]}...")
            else:
                print(f"⚠️  未找到编号 [{search_id}] 的培养方案")
                self.results['found_in_excel'] = False
        
        except Exception as e:
            print(f"❌ 查询出错: {e}")
            self.results['found_in_excel'] = False
    
    def _step3_ai_prediction(self, input_fasta):
        """步骤 3: GenomeSPOT AI 预测"""
        print("\n" + "="*80)
        print("🤖 [步骤 3] GenomeSPOT AI 生理特征预测")
        print("="*80)
        
        if not self.config['enable_genomespot'] or not GENOMESPOT_AVAILABLE:
            print("⚠️  GenomeSPOT 不可用，跳过 AI 预测")
            return
        
        # 这里需要实现 GenomeSPOT 预测逻辑
        # 参考 V24-12-15.py 的 run_ai_prediction 函数
        print("💡 GenomeSPOT 预测功能待实现")
        print("   （需要 Prodigal 基因预测 + GenomeSPOT 模型推理）")
    
    def _step4_xgboost_prediction(self, input_fasta, output_dir):
        """步骤 4: XGBoost 培养基预测"""
        print("\n" + "="*80)
        print("🧪 [步骤 4] MicroBoost XGBoost 培养基预测")
        print("="*80)
        
        try:
            predictions, gc_analysis = predict_from_genome(
                input_fasta,
                model_dir=MICROBOOST_MODELS,
                analyze_importance=True
            )
            
            self.results['xgboost_predictions'] = predictions
            self.results['xgboost_gc_analysis'] = gc_analysis
            
            if predictions is not None:
                output_file = os.path.join(output_dir, "xgboost_predictions.csv")
                save_predictions(predictions, output_file)
        
        except Exception as e:
            print(f"❌ XGBoost 预测出错: {e}")
    
    def _step5_gc_analysis(self, input_fasta):
        """步骤 5: GC 含量代谢分析"""
        print("\n" + "="*80)
        print("🧬 [步骤 5] GC 含量代谢分析")
        print("="*80)
        
        if not V24_CORE_AVAILABLE:
            print("❌ V24 核心模块不可用，跳过 GC 分析")
            return
        
        gc_content = calculate_gc_content(input_fasta)
        if gc_content > 0:
            metabolic_pred = predict_carbon_nitrogen_preference(gc_content)
            
            self.results['gc_content'] = gc_content
            self.results['metabolic_prediction'] = metabolic_pred
            
            print(f"   GC 含量: {gc_content:.2f}%")
            print(f"   {metabolic_pred['color']} 类型: {metabolic_pred['type']}")
            print(f"   {metabolic_pred['recommendation']}")
    
    def _step6_arg_detection(self, input_fasta):
        """步骤 6: 抗性基因检测"""
        print("\n" + "="*80)
        print("💊 [步骤 6] 抗生素抗性基因检测")
        print("="*80)
        
        if not V24_CORE_AVAILABLE:
            print("❌ V24 核心模块不可用，跳过 ARG 检测")
            return
        
        query_wsl = to_wsl_path(input_fasta)
        output_dir = os.path.dirname(input_fasta)
        
        recs = check_antibiotic_resistance(query_wsl, output_dir)
        
        if recs:
            self.results['arg_recommendations'] = recs
            print(f"✅ 检测到 {len(recs)} 个抗性基因")
            for idx, item in enumerate(recs[:5], 1):
                print(f"   {idx}. {item['drug']:<20} | Score: {item['score']}")
        else:
            print("⚠️  未检测到抗性基因")
    
    def _generate_report(self, output_dir):
        """生成分析报告"""
        report_file = os.path.join(output_dir, "analysis_report.txt")
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write("EasyCulture 分析报告\n")
            f.write("="*80 + "\n\n")
            
            f.write(f"分析时间: {self.results.get('timestamp', 'N/A')}\n")
            f.write(f"输入文件: {os.path.basename(self.results.get('input_file', 'N/A'))}\n")
            f.write(f"文件大小: {self.results.get('file_size', 0)/1024/1024:.2f} MB\n")
            f.write(f"总耗时: {self.results.get('elapsed_time', 0):.2f} 秒\n\n")
            
            # 物种鉴定结果
            if 'identification' in self.results and self.results['identification']:
                f.write("-"*80 + "\n")
                f.write("物种鉴定结果\n")
                f.write("-"*80 + "\n")
                result = self.results['identification']
                f.write(f"匹配菌株: {result['filename']}\n")
                f.write(f"相似度: {result['score']:.2f}% ({result['type']})\n\n")
            
            # 培养基方案
            if self.results.get('found_in_excel', False):
                f.write("-"*80 + "\n")
                f.write("培养基方案\n")
                f.write("-"*80 + "\n")
                for idx, recipe in enumerate(self.results.get('media_recipes', []), 1):
                    f.write(f"\n方案 {idx}:\n")
                    f.write(f"  温度: {recipe.get(COL_TEMP, 'N/A')}\n")
                    f.write(f"  时间: {recipe.get(COL_TIME, 'N/A')}\n")
                    f.write(f"  成分: {recipe.get(COL_MEDIA, 'N/A')}\n")
                f.write("\n")
            
            # GC 分析
            if 'gc_content' in self.results:
                f.write("-"*80 + "\n")
                f.write("GC 含量分析\n")
                f.write("-"*80 + "\n")
                f.write(f"GC 含量: {self.results['gc_content']:.2f}%\n")
                if 'metabolic_prediction' in self.results:
                    pred = self.results['metabolic_prediction']
                    f.write(f"代谢类型: {pred['type']}\n")
                    f.write(f"推荐: {pred['recommendation']}\n\n")
            
            # ARG 检测
            if 'arg_recommendations' in self.results:
                f.write("-"*80 + "\n")
                f.write("抗生素筛选建议\n")
                f.write("-"*80 + "\n")
                for idx, item in enumerate(self.results['arg_recommendations'], 1):
                    f.write(f"{idx}. {item['drug']}\n")
                    f.write(f"   基因: {item['gene']}\n")
                    f.write(f"   评分: {item['score']}\n")
                    f.write(f"   原因: {item['reason']}\n")
                    f.write(f"   警告: {item['warning']}\n\n")
        
        print(f"\n📄 报告已保存: {report_file}")

# ==============================================================================
# 命令行接口
# ==============================================================================

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="EasyCulture - 智能微生物培养系统")
    parser.add_argument("input", help="输入基因组文件 (FASTA格式)")
    parser.add_argument("-o", "--output", help="输出目录", default=None)
    parser.add_argument("--no-genomespot", action="store_true", help="禁用 GenomeSPOT")
    parser.add_argument("--no-xgboost", action="store_true", help="禁用 XGBoost")
    parser.add_argument("--no-arg", action="store_true", help="禁用 ARG 检测")
    
    args = parser.parse_args()
    
    # 配置覆盖
    config_override = {
        'enable_genomespot': not args.no_genomespot,
        'enable_microboost': not args.no_xgboost,
        'enable_arg': not args.no_arg,
    }
    
    # 创建实例并分析
    ec = EasyCulture(config_override=config_override)
    results = ec.analyze_genome(args.input, args.output)
    
    if results:
        print("\n✅ 分析完成！")
    else:
        print("\n❌ 分析失败")
        sys.exit(1)

if __name__ == "__main__":
    # 如果没有命令行参数，使用默认测试文件
    if len(sys.argv) == 1:
        test_file = os.path.join(TEST_SEQ_DIR, "test_genome.fasta")
        if not os.path.exists(test_file):
            print("请提供输入文件:")
            print("  python EasyCulture_Main.py <genome.fasta>")
            sys.exit(1)
        sys.argv.append(test_file)
    
    main()
