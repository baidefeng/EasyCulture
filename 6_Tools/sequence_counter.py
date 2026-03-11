import os

def analyze_sequence_folder(folder_path):
    # 1. 初始化计数器
    stats = {
        "16s": 0,
        "genome": 0,
        "unknown": 0,
        "total": 0
    }
    
    # 定义判断关键词 (根据你实际的文件命名习惯调整)
    keywords_16s = ['16s', 'rRNA', 'ssu']
    keywords_genome = ['genome', 'wgs', 'assembly', 'complete']

    # 检查路径是否存在
    if not os.path.exists(folder_path):
        print(f"❌ 错误：找不到路径 {folder_path}")
        return

    print(f"正在扫描文件夹: {folder_path} ...")
    print("-" * 30)

    # 2. 遍历文件夹
    file_list = os.listdir(folder_path)
    
    for filename in file_list:
        # 获取文件的完整路径
        filepath = os.path.join(folder_path, filename)
        
        # 跳过文件夹，只处理文件
        if not os.path.isfile(filepath):
            continue
            
        # 忽略非序列文件 (可选，根据需要添加后缀)
        if filename.startswith('.'): # 跳过隐藏文件
            continue

        stats["total"] += 1
        name_lower = filename.lower()
        
        # --- 核心判断逻辑 ---
        
        # 方式 A: 基于文件名的关键词判断
        is_identified = False
        
        # 检查是否是 16S
        for kw in keywords_16s:
            if kw in name_lower:
                stats["16s"] += 1
                is_identified = True
                break
        
        # 检查是否是 基因组 (如果还没被识别为16S)
        if not is_identified:
            for kw in keywords_genome:
                if kw in name_lower:
                    stats["genome"] += 1
                    is_identified = True
                    break
        
        # 方式 B: 基于文件大小的“兜底”判断 (如果文件名看不出来)
        # 16S 序列通常很短 (< 10KB), 基因组很大 (> 100KB)
        if not is_identified:
            try:
                size_bytes = os.path.getsize(filepath)
                if size_bytes < 20 * 1024:  # 小于 20KB 认为是 16S
                    stats["16s"] += 1
                else:  # 大于 20KB 认为是 基因组
                    stats["genome"] += 1
            except Exception as e:
                stats["unknown"] += 1
                print(f"无法读取文件大小: {filename}")

    # 3. 计算占比并输出结果
    if stats["total"] == 0:
        print("文件夹为空或没有找到文件。")
        return

    percent_16s = (stats["16s"] / stats["total"]) * 100
    percent_genome = (stats["genome"] / stats["total"]) * 100
    percent_unknown = (stats["unknown"] / stats["total"]) * 100

    print("\n📊 统计结果报告")
    print("=" * 30)
    print(f"📂 总文件数量: {stats['total']}")
    print("-" * 30)
    print(f"🧬 16S 序列:     {stats['16s']:<5} (占比: {percent_16s:.2f}%)")
    print(f"🌍 全基因组序列: {stats['genome']:<5} (占比: {percent_genome:.2f}%)")
    
    if stats["unknown"] > 0:
        print(f"❓ 未知类型:     {stats['unknown']:<5} (占比: {percent_unknown:.2f}%)")
    print("=" * 30)

# --- 执行配置 ---
# 你的目标文件夹路径
target_folder = r"F:\JIYINZU-test\ATCC_CCM_NCIMB序列补充"

# 运行函数
analyze_sequence_folder(target_folder)