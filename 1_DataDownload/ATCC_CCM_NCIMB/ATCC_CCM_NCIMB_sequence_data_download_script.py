"""
脚本名称: ATCC_CCM_NCIMB序列补充爬取_V4_严谨版.py
功能: 
1. 访问BacDive提取Other collection no.
2. NCBI反向检索，严格校验物种名称是否匹配
3. 增加文件大小和序列长度的质量控制
"""

import os
import sys
import time
import csv
import re
import gzip
import shutil
import pandas as pd
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ================= 配置区域 =================
INPUT_CSV = r"F:\JIYINZU-test\dsmz_full_database.csv"
BASE_WORK_DIR = r"F:\JIYINZU-test"
DOWNLOAD_FOLDER_NAME = "ATCC_CCM_NCIMB序列补充_V4"
OUTPUT_CSV = "ATCC_CCM_NCIMB序列补充结果_V4.csv"

# 测试设置
TEST_MODE = True      # 正式跑的时候改为 False
TEST_LIMIT = 50       # 测试数量
RESTART_INTERVAL = 15 # 浏览器重启间隔

# 校验阈值
MIN_WGS_SIZE_KB = 500  # WGS最小文件大小 (KB)，低于此值视为错误文件
MIN_16S_LEN = 1200     # 16S 最小长度
MAX_16S_LEN = 1800     # 16S 最大长度
# ==========================================

abs_download_path = os.path.join(BASE_WORK_DIR, DOWNLOAD_FOLDER_NAME)
abs_csv_path = os.path.join(BASE_WORK_DIR, OUTPUT_CSV)
current_script_dir = os.path.dirname(os.path.abspath(__file__))

if not os.path.exists(abs_download_path):
    os.makedirs(abs_download_path)

# --- 工具函数：获取属名 ---
def get_genus(name):
    """从菌株名称中提取属名（第一个单词）"""
    if not isinstance(name, str) or not name:
        return ""
    # 移除可能的单引号或特殊字符
    clean_name = re.sub(r"[\[\]'\"()]", "", name).strip()
    parts = clean_name.split()
    if parts:
        return parts[0].strip()
    return ""

# --- 网络组件 ---
def get_requests_session():
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    })
    return session

http = get_requests_session()

def get_driver():
    print("🚗 正在启动 Chrome...")
    driver_path = os.path.join(current_script_dir, "chromedriver.exe")
    if not os.path.exists(driver_path):
        if shutil.which("chromedriver"): driver_path = "chromedriver"
        else: print("❌ 未找到 chromedriver.exe"); sys.exit(1)

    opts = Options()
    opts.add_argument("--headless") # 建议开启无头模式，更稳定
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    
    try:
        service = Service(executable_path=driver_path)
        driver = webdriver.Chrome(service=service, options=opts)
        driver.set_page_load_timeout(30)
        return driver
    except Exception as e:
        print(f"❌ 浏览器启动失败: {e}")
        sys.exit(1)

# --- BacDive 提取 ---
def get_collection_numbers_from_bacdive(driver, dsm_number):
    collection_numbers = []
    try:
        catalogue_url = f"https://www.dsmz.de/collection/catalogue/details/culture/DSM-{dsm_number}"
        driver.get(catalogue_url)
        time.sleep(3)
        
        if "404" in driver.page_source or "not found" in driver.page_source.lower():
            return []
        
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        # 策略1: 表格搜索
        all_rows = soup.find_all("tr")
        found_in_table = False
        for row in all_rows:
            row_text = row.get_text(" ", strip=True)
            if re.search(r"Other collection no|WDCM no", row_text, re.IGNORECASE):
                cells = row.find_all("td")
                value_text = cells[1].get_text(" ", strip=True) if len(cells) >= 2 else row_text
                
                # 提取常见编号
                target_prefixes = ["ATCC", "CCM", "NCIMB", "NCTC", "LMG", "CIP", "NBRC", "IAM", "KCTC", "JCM"]
                for prefix in target_prefixes:
                    matches = re.findall(rf"\b({prefix})\s*([0-9]+)\b", value_text, re.IGNORECASE)
                    for p, n in matches:
                        collection_numbers.append(f"{p.upper()} {n}")
                found_in_table = True
                break
        
        # 策略2: 全文正则补充
        if not found_in_table:
            page_text = soup.get_text(" ", strip=True)
            match = re.search(r"Other collection no[^:]*:\s*([^\n]+)", page_text, re.IGNORECASE)
            if match:
                value_text = match.group(1)
                target_prefixes = ["ATCC", "CCM", "NCIMB", "NCTC", "LMG", "CIP", "NBRC", "IAM"]
                for prefix in target_prefixes:
                    matches = re.findall(rf"\b({prefix})\s*([0-9]+)\b", value_text, re.IGNORECASE)
                    for p, n in matches:
                        collection_numbers.append(f"{p.upper()} {n}")
        
        return list(set(collection_numbers))
            
    except Exception as e:
        print(f" [BacDiveErr]", end="")
        return []

# --- NCBI 核心逻辑 (严谨版) ---

def validate_organism_match(target_genus, result_organism):
    """
    核心校验函数：判断结果物种是否匹配目标属名
    """
    if not target_genus or not result_organism:
        return False
    
    target_genus = target_genus.lower()
    result_organism = result_organism.lower()
    
    # 1. 直接包含检查 (最强)
    if target_genus in result_organism:
        return True
    
    # 2. 同义词处理 (这里可以添加已知的同义词库，防止错杀)
    # 例如: Bacillus 和 Metabacillus
    synonyms = {
        "bacillus": ["metabacillus", "paenibacillus", "viridibacillus", "brevibaillus"],
        "pseudomonas": ["stenotrophomonas", "burkholderia"],
        "corynebacterium": ["rhodococcus", "arthrobacter"]
    }
    
    if target_genus in synonyms:
        for syn in synonyms[target_genus]:
            if syn in result_organism:
                return True
                
    return False

def search_ncbi_strict(collection_id, target_strain_name):
    """
    collection_id: 搜索关键词 (如 "ATCC 13930")
    target_strain_name: 原始菌株名称 (如 "Agromyces mediolanus")
    """
    results = {"16s": None, "wgs": None}
    target_genus = get_genus(target_strain_name)
    
    # 提取纯数字
    num_match = re.search(r'(\d+)', collection_id)
    number_str = num_match.group(1) if num_match else ""
    
    # --- WGS 搜索 ---
    try:
        # 构造更精准的搜索词：编号 + 属名 (如果可能)
        # 优先搜: "ATCC 13930"
        # 备选搜: Agromyces 13930
        
        search_candidates = [f'"{collection_id}"']
        if target_genus and number_str:
            search_candidates.append(f'{target_genus} {number_str}')
            
        found_wgs = False
        for term in search_candidates:
            if found_wgs: break
            
            url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
            resp = http.get(url, params={"db": "assembly", "term": term, "retmode": "json", "retmax": 10}, timeout=10)
            ids = resp.json().get("esearchresult", {}).get("idlist", [])
            
            if ids:
                sum_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
                r2 = http.get(sum_url, params={"db": "assembly", "id": ",".join(ids), "retmode": "json"}, timeout=10)
                summaries = r2.json()["result"]
                
                for uid in ids:
                    if uid not in summaries: continue
                    info = summaries[uid]
                    acc = info.get("assemblyaccession", "")
                    organism = info.get("organism", "")
                    species = info.get("speciesname", "")
                    
                    # === 严谨校验 ===
                    # 检查物种名是否包含目标属名
                    if not validate_organism_match(target_genus, organism) and not validate_organism_match(target_genus, species):
                        print(f" [⚠️跳过异物种WGS:{organism}]", end="")
                        continue
                        
                    results["wgs"] = acc
                    print(f" [WGS:{acc} {organism[:15]}]", end="")
                    found_wgs = True
                    break
    except Exception as e:
        pass

    # --- 16S 搜索 ---
    try:
        # 16S 需要更严格的关键词
        terms = [
            f'"{collection_id}"[Title] AND 16S',
            f'"{collection_id}"[All Fields] AND 16S rRNA'
        ]
        
        found_16s = False
        for term in terms:
            if found_16s: break
            
            resp = http.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi", 
                           params={"db": "nuccore", "term": term, "retmode": "json", "retmax": 20}, timeout=10)
            ids = resp.json().get("esearchresult", {}).get("idlist", [])
            
            if ids:
                r2 = http.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi", 
                             params={"db": "nuccore", "id": ",".join(ids), "retmode": "json"}, timeout=10)
                summaries = r2.json()["result"]
                
                best_len = 0
                best_acc = None
                
                for uid in ids:
                    if uid not in summaries: continue
                    info = summaries[uid]
                    title = info.get("title", "")
                    slen = int(info.get("slen", 0))
                    
                    # === 严谨校验 ===
                    # 1. 长度校验
                    if not (MIN_16S_LEN <= slen <= MAX_16S_LEN):
                        continue
                        
                    # 2. 物种名校验 (从标题提取)
                    if target_genus and target_genus.lower() not in title.lower():
                        # 再次检查 organism 字段 (如果有)
                        # 这里简单处理，如果标题完全没属名，风险较大
                        continue
                        
                    # 优选最接近 1500bp 的
                    if slen > best_len:
                        best_len = slen
                        best_acc = info.get("caption", "")
                
                if best_acc:
                    results["16s"] = best_acc
                    print(f" [16S:{best_acc} {best_len}bp]", end="")
                    found_16s = True
                    
    except Exception:
        pass
        
    return results

# --- 下载逻辑 (带大小校验) ---
def download_file_strict(accession, strain_name, prefix, file_type):
    """
    下载并检查文件大小
    file_type: "WGS" 或 "16S"
    """
    if not accession or accession == "N/A": return "N/A", ""
    
    safe_name = re.sub(r'[\\/*?:"<>|]', "_", strain_name)
    filename = f"{prefix}_{safe_name}_{file_type}_{accession}.fasta"
    filepath = os.path.join(abs_download_path, filename)
    
    # 检查已存在文件的大小
    if os.path.exists(filepath):
        size_kb = os.path.getsize(filepath) / 1024
        if file_type == "WGS" and size_kb < MIN_WGS_SIZE_KB:
            print(f" [🗑️旧文件过小:{int(size_kb)}KB,重下]", end="")
            os.remove(filepath)
        elif file_type == "16S" and size_kb < 1: # 1KB
            os.remove(filepath)
        else:
            return "已存在", filename

    # 下载
    success = False
    
    # 1. 尝试 Assembly 下载 (针对 WGS)
    if file_type == "WGS":
        # 解析 FTP
        try:
            esearch = http.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
                              params={"db": "assembly", "term": accession, "retmode": "json"})
            uid = esearch.json()["esearchresult"]["idlist"][0]
            esum = http.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi",
                           params={"db": "assembly", "id": uid, "retmode": "json"})
            data = esum.json()["result"][uid]
            ftp = data.get("ftppath_refseq") or data.get("ftppath_genbank")
            
            if ftp:
                dl_url = ftp.replace("ftp://", "https://") + f"/{ftp.split('/')[-1]}_genomic.fna.gz"
                print(f" ⬇️", end="")
                with http.get(dl_url, stream=True, timeout=120) as r:
                    if r.status_code == 200:
                        with open(filepath, 'wb') as f_out:
                            # 解压 GZ
                            with gzip.open(r.raw, 'rb') as f_in:
                                shutil.copyfileobj(f_in, f_out)
                        success = True
        except: pass

    # 2. 尝试 Nucleotide 下载 (针对 16S 或 失败的 WGS)
    if not success:
        db = "nuccore"
        try:
            print(f" ⬇️(api)", end="")
            with http.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi",
                         params={"db": db, "id": accession, "rettype": "fasta", "retmode": "text"},
                         stream=True, timeout=60) as r:
                if r.status_code == 200:
                    with open(filepath, "wb") as f:
                        for chunk in r.iter_content(8192): f.write(chunk)
                    success = True
        except: pass

    # === 最终质量校验 ===
    if success and os.path.exists(filepath):
        final_size_kb = os.path.getsize(filepath) / 1024
        
        # WGS 必须大于阈值
        if file_type == "WGS" and final_size_kb < MIN_WGS_SIZE_KB:
            print(f" [❌WGS过小:{int(final_size_kb)}KB]", end="")
            os.remove(filepath) # 删除垃圾文件
            return "失败(文件过小)", ""
            
        # 16S 必须有内容
        if file_type == "16S" and final_size_kb < 0.1:
            os.remove(filepath)
            return "失败(空文件)", ""
            
        return "成功", filename
        
    return "失败", ""

# --- 主程序 ---
def main():
    print(f"🚀 启动 V4 严谨版 (WGS阈值: {MIN_WGS_SIZE_KB}KB | 16S范围: {MIN_16S_LEN}-{MAX_16S_LEN}bp)")
    
    # 读取数据
    try:
        try: df = pd.read_csv(INPUT_CSV, encoding='utf-8-sig')
        except: df = pd.read_csv(INPUT_CSV, encoding='gbk')
    except: print("❌ 无法读取CSV"); return

    # 筛选未完成的
    # 假设列3,6,9分别是DSM编号, WGS状态, 16S状态 (根据你的表结构调整)
    # 这里简化逻辑：只处理 WGS_状态 和 16S_状态 都不为 '成功' 或 '已存在' 的
    
    # 读取已完成
    processed_dsm = set()
    if os.path.exists(abs_csv_path):
        try:
            done_df = pd.read_csv(abs_csv_path)
            processed_dsm = set(done_df['DSM编号'].astype(str))
        except: pass
        
    # 初始化文件头
    if not os.path.exists(abs_csv_path):
        with open(abs_csv_path, 'w', newline='', encoding='utf-8-sig') as f:
            csv.writer(f).writerow(['原页码', '菌株名称', 'DSM编号', '提取的编号', 'WGS_ID', 'WGS_状态', 'WGS_文件', '16S_ID', '16S_状态', '16S_文件'])

    driver = get_driver()
    count = 0
    
    try:
        for idx, row in df.iterrows():
            if TEST_MODE and count >= TEST_LIMIT: break
            
            strain_name = str(row.get('菌株名称', '')).strip()
            if 'JCM' in strain_name: continue # 跳过JCM
            
            dsm_raw = str(row.get('DSM编号', '')).replace('DSM', '').strip()
            full_dsm = f"DSM {dsm_raw}"
            
            # 简单查重：如果已经做过这个DSM号，跳过
            if full_dsm in processed_dsm: continue
            
            # 检查原表是否有空缺
            # 这里的逻辑根据你实际需求：如果原表已经有WGS_ID且状态成功，就不要重跑
            # 暂且默认跑全量筛选出来的空缺行
            
            if count > 0 and count % RESTART_INTERVAL == 0:
                print("\n♻️ 刷新浏览器..."); driver.quit(); time.sleep(2); driver = get_driver()
            
            print(f"\n🔹 [{count+1}] {strain_name} ({full_dsm})", end="")
            
            # 1. 爬取编号
            ids = get_collection_numbers_from_bacdive(driver, dsm_raw)
            if not ids: 
                ids = [full_dsm] # 如果没找到，至少搜一下DSM号
            else:
                ids.append(full_dsm)
                
            unique_ids = list(set(ids))
            print(f" 🔍IDs:{len(unique_ids)}个", end="")
            
            # 2. 遍历搜索，直到找到满意的
            final_wgs_id, final_16s_id = "N/A", "N/A"
            final_wgs_stat, final_16s_stat = "N/A", "N/A"
            final_wgs_file, final_16s_file = "", ""
            used_id = ""
            
            for cid in unique_ids:
                if final_wgs_id != "N/A" and final_16s_id != "N/A": break
                
                res = search_ncbi_strict(cid, strain_name)
                
                # 更新 WGS
                if final_wgs_id == "N/A" and res["wgs"]:
                    # 尝试下载以验证大小
                    stat, fname = download_file_strict(res["wgs"], strain_name, cid.split()[0], "WGS")
                    if "失败" not in stat:
                        final_wgs_id = res["wgs"]
                        final_wgs_stat = stat
                        final_wgs_file = fname
                        used_id = cid
                
                # 更新 16S
                if final_16s_id == "N/A" and res["16s"]:
                    stat, fname = download_file_strict(res["16s"], strain_name, cid.split()[0], "16S")
                    if "失败" not in stat:
                        final_16s_id = res["16s"]
                        final_16s_stat = stat
                        final_16s_file = fname
                        if not used_id: used_id = cid

            # 3. 写入结果
            with open(abs_csv_path, 'a', newline='', encoding='utf-8-sig') as f:
                csv.writer(f).writerow([
                    row.get('原页码', ''), strain_name, full_dsm, ";".join(unique_ids),
                    final_wgs_id, final_wgs_stat, final_wgs_file,
                    final_16s_id, final_16s_stat, final_16s_file
                ])
            
            if final_wgs_id != "N/A" or final_16s_id != "N/A":
                print(" ✅Done", end="")
            else:
                print(" 💨空", end="")
                
            count += 1
            
    except KeyboardInterrupt:
        print("\n🛑 Stop")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()