# ==============================================================================
#  工具脚本：16S 参考数据库构建器 (KOMODO 专用)
#  功能：
#  1. 遍历文件夹，通过大小过滤掉全基因组，只抓取 16S 序列。
#  2. 读取 Excel，将菌株 ID 与 培养基 ID 关联。
#  3. 合并生成 ref_16s_media.fasta。
# ==============================================================================

import os
import pandas as pd
import re
import glob

# ===================== 核心配置 (请修改此处) =====================

# [1] 您的下载文件夹 (包含全基因组和 16S 的混合文件夹)
INPUT_FOLDER = r"F:\JIYINZU-test\fasta_downloads_test"

# [2] 您的 Excel 表格路径
EXCEL_PATH = r"F:\JIYINZU-test\20 pages Media composition information.xlsx"

# [3] 输出文件路径 (生成的数据库)
OUTPUT_DB_PATH = r"F:\JIYINZU-test\ref_16s_media.fasta"

# [4] Excel 列名设置
COL_DSM_ID = "DSM编号"   # 菌株编号列
COL_MEDIA_ID = "当前ID"  # 培养基编号列 (例如 104)

# [5] 16S 文件大小上限 (字节)
# 16S 序列通常 < 2KB，全基因组通常 > 2MB
# 我们设定 50KB 为界限，小于它的才会被认为是 16S 序列文件
SIZE_LIMIT_BYTES = 50 * 1024 

# =================================================================

def extract_dsm_number(filename):
    """从文件名提取纯数字 ID"""
    # 移除扩展名
    name = os.path.splitext(os.path.basename(filename))[0]
    # 匹配 DSM 12345 或 12345 格式
    match = re.search(r"(\d+)", name)
    if match:
        return match.group(1)
    return None

def build_database():
    print("🚀 [数据库构建工具] 启动...")
    
    # 1. 读取 Excel 建立映射字典
    print(f"📖 读取 Excel: {os.path.basename(EXCEL_PATH)}...")
    try:
        df = pd.read_excel(EXCEL_PATH)
        # 确保 ID 是字符串格式并去除空格
        df[COL_DSM_ID] = df[COL_DSM_ID].astype(str).str.strip()
        df[COL_MEDIA_ID] = df[COL_MEDIA_ID].astype(str).str.strip()
        
        # 创建字典: { '12345': '104', '5678': '78' }
        id_to_media = dict(zip(df[COL_DSM_ID], df[COL_MEDIA_ID]))
        print(f"   ✅ 加载了 {len(id_to_media)} 条菌株-培养基对应关系。")
    except Exception as e:
        print(f"❌ 读取 Excel 失败: {e}")
        return

    # 2. 遍历文件夹寻找 16S 文件
    print(f"📂 扫描文件夹: {INPUT_FOLDER}...")
    valid_sequences = []
    
    # 支持常见的序列文件后缀
    extensions = ['*.seq', '*.fasta', '*.fna', '*.fa', '*.txt']
    files = []
    for ext in extensions:
        files.extend(glob.glob(os.path.join(INPUT_FOLDER, ext)))
    
    count_genome_skipped = 0
    count_no_match = 0
    count_success = 0
    
    with open(OUTPUT_DB_PATH, 'w', encoding='utf-8') as out_f:
        for file_path in files:
            file_name = os.path.basename(file_path)
            
            # --- 过滤 1: 跳过大文件 (全基因组) ---
            file_size = os.path.getsize(file_path)
            if file_size > SIZE_LIMIT_BYTES:
                count_genome_skipped += 1
                continue # 跳过全基因组
            
            # --- 过滤 2: 提取 ID 并匹配 Excel ---
            strain_id = extract_dsm_number(file_name)
            if not strain_id:
                continue
                
            if strain_id in id_to_media:
                media_id = id_to_media[strain_id]
                
                # 读取序列内容
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read().strip()
                        
                        # 处理 FASTA 格式或纯序列格式
                        seq_body = ""
                        if content.startswith(">"):
                            # 如果是标准 FASTA，去掉第一行标题，保留序列
                            parts = content.split('\n', 1)
                            if len(parts) > 1:
                                seq_body = parts[1].replace('\n', '').strip()
                        else:
                            # 如果是纯序列文件 (.seq)
                            seq_body = content.replace('\n', '').strip()
                        
                        if seq_body:
                            # --- 写入新格式 ---
                            # 格式: >DSM_ID|Medium_ID|Original_Filename
                            header = f">DSM_{strain_id}|Medium_{media_id}|{file_name}"
                            out_f.write(f"{header}\n{seq_body}\n")
                            count_success += 1
                        
                except Exception as e:
                    print(f"⚠️ 读取文件出错 {file_name}: {e}")
            else:
                count_no_match += 1

    print("\n" + "="*50)
    print(f"🎉 数据库构建完成！")
    print(f"📂 输出文件: {OUTPUT_DB_PATH}")
    print(f"📊 统计:")
    print(f"   ✅ 成功提取并合并: {count_success} 个 16S 序列")
    print(f"   ⏩ 跳过全基因组(>50KB): {count_genome_skipped} 个")
    print(f"   ⚠️ 跳过(Excel中无对应ID): {count_no_match} 个")
    print("="*50)
    print("💡 下一步: 请在 V24 脚本中设置 REF_16S_DB_WIN 为上述输出路径。")

if __name__ == "__main__":
    build_database()