import pandas as pd
import re
import os

# ================= 配置区域 =================
# 您的 CSV 文件路径
csv_path = r"F:\JIYINZU-test\dsmz_full_database - 副本.csv"

# ===========================================

def analyze_collections(file_path):
    print(f"🚀 正在读取文件: {os.path.basename(file_path)} ...")
    
    try:
        # 读取 CSV (尝试 utf-8-sig 以兼容 Excel 保存的格式)
        try:
            df = pd.read_csv(file_path, encoding='utf-8-sig')
        except UnicodeDecodeError:
            df = pd.read_csv(file_path, encoding='gbk') # 备用编码

        # 获取第二列数据 (索引为1，因为索引从0开始)
        # 假设第二列是 "菌株名称"
        strain_names = df.iloc[:, 1].dropna().astype(str)
        
        print(f"✅ 成功加载 {len(strain_names)} 条数据，开始分析...")
        print("-" * 50)

        # 用于存储提取到的保藏中心名称
        collections = []
        
        # 正则表达式逻辑 (V2.0 增强版)：
        # 1. \b([A-Z]{2,})       -> 匹配单词边界开始的至少2个大写字母 (捕获组，如 DSM, ATCC, CCAP)
        # 2. \s* -> 中间允许有空格，也允许没有空格 (兼容 CCAP3/1)
        # 3. [0-9]+              -> 后面必须紧跟着数字
        # 4. (?:[\/-][0-9]+)* -> 数字后面可以跟 / 或 - 以及更多数字 (处理 3/1 这种格式)
        # 这样可以排除掉前面的属名(首字母大写)和种名(小写)，只抓取全大写的机构名
        pattern = re.compile(r'\b([A-Z]{2,})\s*[0-9]+(?:[\/-][0-9]+)*')

        # 遍历每一行
        for name in strain_names:
            # 在名字中搜索匹配项
            match = pattern.search(name)
            if match:
                # 提取第一个捕获组 (即机构名称)
                col_name = match.group(1)
                collections.append(col_name)
            else:
                # 没匹配到的情况 (用于调试)
                # print(f"未识别: {name}") 
                pass

        # 统计频率
        counts = pd.Series(collections).value_counts()

        # === 输出结果 ===
        print(f"🏆 发现 {len(counts)} 种不同的保藏机构命名格式")
        print("-" * 50)
        print(f"{'机构缩写':<10} | {'出现次数':<10} | {'占比'}")
        print("-" * 50)
        
        for name, count in counts.items():
            percent = (count / len(collections)) * 100
            print(f"{name:<10} | {count:<10} | {percent:.1f}%")
            
        print("-" * 50)
        
        # 额外建议
        top_collections = counts.head(5).index.tolist()
        print("\n💡 分析建议:")
        print(f"绝大多数数据集中在: {', '.join(top_collections)}")
        print("如果在 V67 爬虫中需要反向搜索，请重点关注这些前缀。")

    except FileNotFoundError:
        print(f"❌ 错误: 找不到文件 {file_path}")
    except Exception as e:
        print(f"❌ 发生错误: {e}")

if __name__ == "__main__":
    analyze_collections(csv_path)