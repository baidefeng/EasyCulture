"""
脚本名称: JCM库补充测试.py
功能: 
1. 读取本地 dsmz_full_database.csv，筛选含 JCM 编号的菌株。
2. 根据 JCM 编号访问 JCM 官网 -> 跳转 BacDive 数据库。
3. 在 BacDive 中提取 Sequence information (16S 和 Genome) 中的 Genbank 编号。
4. 调用下载引擎获取 FASTA 序列。
5. 测试限制：前 10 个 JCM 菌株。
"""

import os
import sys
import time
import random
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
from selenium.webdriver.common.by import By
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ================= 核心配置区域 =================
# 输入文件 (您之前的运行结果)
INPUT_CSV = r"F:\JIYINZU-test\dsmz_full_database.csv"

# 输出设置
BASE_WORK_DIR = r"F:\JIYINZU-test"
DOWNLOAD_FOLDER_NAME = "jcm_sequences_test"
OUTPUT_CSV = "JCM库补充测试.csv"  # <--- 修改为与代码同名

# 测试限制
MAX_TEST_COUNT = 10  # <--- 修改为前 10 个
# ===============================================

# --- 0. 路径初始化 ---
abs_download_path = os.path.join(BASE_WORK_DIR, DOWNLOAD_FOLDER_NAME)
abs_csv_path = os.path.join(BASE_WORK_DIR, OUTPUT_CSV)

if not os.path.exists(abs_download_path): os.makedirs(abs_download_path)
current_script_dir = os.path.dirname(os.path.abspath(__file__))

# --- 1. 网络与浏览器组件 ---
def get_requests_session():
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
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
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    
    try:
        service = Service(executable_path=driver_path)
        driver = webdriver.Chrome(service=service, options=opts)
        driver.set_page_load_timeout(90)
        return driver
    except Exception as e: print(f"❌ 浏览器失败: {e}"); sys.exit(1)

# --- 2. 下载引擎 ---
def resolve_wgs_to_assembly(wgs_acc):
    try:
        url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        resp = http.get(url, params={"db": "assembly", "term": wgs_acc, "retmode": "json"}, timeout=15)
        ids = resp.json()["esearchresult"]["idlist"]
        if ids:
            r2 = http.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi", 
                          params={"db": "assembly", "id": ids[0], "retmode": "json"}, timeout=15)
            return r2.json()["result"][ids[0]]["assemblyaccession"]
    except: pass
    return None

def download_assembly_https(assembly_acc, save_path):
    try:
        search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        resp = http.get(search_url, params={"db": "assembly", "term": assembly_acc, "retmode": "json"}, timeout=15)
        data = resp.json()
        if not data["esearchresult"]["idlist"]: return False
        uid = data["esearchresult"]["idlist"][0]
        sum_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
        resp = http.get(sum_url, params={"db": "assembly", "id": uid, "retmode": "json"}, timeout=15)
        result = resp.json()["result"][uid]
        ftp_url = result.get("ftppath_refseq") or result.get("ftppath_genbank")
        if not ftp_url: return False
        dl_link = ftp_url.replace("ftp://", "https://") + f"/{ftp_url.split('/')[-1]}_genomic.fna.gz"
        print(f" (NCBI)...", end="")
        with http.get(dl_link, stream=True, timeout=180) as r:
            if r.status_code == 200:
                with open(save_path, 'wb') as f_out:
                    with gzip.open(r.raw, 'rb') as f_in: shutil.copyfileobj(f_in, f_out)
                return True
    except: return False
    return False

def download_nucleotide_api(accession_id, save_path):
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    try:
        print(f" (NCBI-API)...", end="")
        with http.get(url, params={"db": "nuccore", "id": accession_id, "rettype": "fasta", "retmode": "text"}, stream=True, timeout=60) as r:
            if r.status_code == 200:
                with open(save_path, "wb") as f:
                    for chunk in r.iter_content(8192): f.write(chunk)
                if os.path.getsize(save_path) > 50: return True
    except: pass
    return False

def download_from_ena(accession_id, save_path):
    url = f"https://www.ebi.ac.uk/ena/browser/api/fasta/{accession_id}?download=true"
    try:
        print(f" (🔄ENA)...", end="")
        with http.get(url, stream=True, timeout=60) as r:
            if r.status_code == 200:
                content_sample = next(r.iter_content(100))
                if not content_sample.startswith(b">"): return False
                with open(save_path, "wb") as f:
                    f.write(content_sample)
                    for chunk in r.iter_content(8192): f.write(chunk)
                if os.path.getsize(save_path) > 50: 
                    print(" ✅[ENA]", end="")
                    return True
    except: pass
    return False

def download_sequence(accession_id, strain_name, type_suffix):
    if not accession_id or "N/A" in accession_id: return "N/A", ""
    safe_name = re.sub(r'[\\/*?:"<>|]', "_", strain_name)
    file_name = f"{safe_name}_{type_suffix}_{accession_id}.fasta"
    file_path = os.path.join(abs_download_path, file_name)
    if os.path.exists(file_path) and os.path.getsize(file_path) > 100: return "已存在", file_name
    print(f"\n    ⬇️ [{type_suffix}] {accession_id}", end="")
    success = False
    if re.search(r"0000+$", accession_id):
        acc = resolve_wgs_to_assembly(accession_id)
        if acc: success = download_assembly_https(acc, file_path)
        else: success = download_nucleotide_api(accession_id, file_path)
    elif accession_id.startswith("GC"): success = download_assembly_https(accession_id, file_path)
    else: success = download_nucleotide_api(accession_id, file_path)
    if not success: success = download_from_ena(accession_id, file_path)
    if success: return "成功", file_name
    print(" ❌ 失败", end="")
    return "失败", ""

# ============================================================
# 3. JCM & BacDive 解析逻辑 (修复空值报错 + 优选策略)
# ============================================================

def get_bacdive_url_from_jcm(driver, jcm_num):
    """访问 JCM 详情页，获取 BacDive 链接"""
    url = f"https://www.jcm.riken.jp/cgi-bin/jcm/jcm_number?JCM={jcm_num}"
    try:
        driver.get(url)
        time.sleep(1.5)
        try:
            link_elem = driver.find_element(By.XPATH, "//a[contains(@href, 'bacdive.dsmz.de')]")
            return link_elem.get_attribute('href')
        except:
            return None
    except: return None

def parse_bacdive_page(driver, bacdive_url):
    """
    解析 BacDive 页面，提取最优质的 16S 和 WGS 编号
    """
    ids = {"16s": "N/A", "wgs": "N/A"}
    try:
        driver.get(bacdive_url)
        time.sleep(2) # 等待动态加载
        
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        # 候选池
        s16_candidates = [] 
        wgs_candidates = [] 

        # 遍历所有表格，寻找目标
        for table in soup.find_all("table"):
            # 获取表头文本，用于判断列索引
            headers = [th.get_text(strip=True).lower() for th in table.find_all("th")]
            
            def get_col_idx(name_part):
                for i, h in enumerate(headers):
                    if name_part in h: return i
                return -1

            acc_idx = get_col_idx("accession number")
            len_idx = get_col_idx("length")
            level_idx = get_col_idx("assembly level")

            if acc_idx == -1: continue # 不是序列表

            # 判断表格类型 (16S 还是 Genome)
            prev_header = table.find_previous(["h3", "h4", "h2"])
            section_title = prev_header.get_text(strip=True).lower() if prev_header else ""
            
            is_16s_table = "16s" in section_title or "16s" in str(table).lower()
            is_genome_table = "genome" in section_title or "assembly" in str(headers)

            rows = table.find_all("tr")[1:] # 跳过表头
            for row in rows:
                cols = row.find_all("td")
                if len(cols) <= acc_idx: continue
                
                raw_acc_text = cols[acc_idx].get_text(strip=True)
                
                # --- ⚠️ 关键修复：防止空值 split 报错 ---
                if not raw_acc_text: continue 
                
                parts = raw_acc_text.split()
                if not parts: continue 
                
                acc_id = parts[0]
                # ------------------------------------

                # --- 16S 提取逻辑 ---
                if is_16s_table:
                    if not (re.match(r"^[A-Z]{1,2}\d{5,6}", acc_id) or re.match(r"^[A-Z]{4,6}\d{8,}", acc_id)):
                        continue
                        
                    length = 0
                    if len_idx != -1 and len(cols) > len_idx:
                        try:
                            length = int(re.sub(r"\D", "", cols[len_idx].get_text(strip=True)))
                        except: length = 0
                    
                    s16_candidates.append({"id": acc_id, "len": length})

                # --- WGS 提取逻辑 ---
                if is_genome_table:
                    priority = 0
                    if level_idx != -1 and len(cols) > level_idx:
                        lvl = cols[level_idx].get_text(strip=True).lower()
                        if "complete" in lvl: priority = 3
                        elif "scaffold" in lvl: priority = 2
                        elif "contig" in lvl: priority = 1
                    
                    is_valid_genome_id = acc_id.startswith("GC") or re.search(r"[A-Z]{4,6}\d{2}0{6,}", acc_id)
                    
                    if is_valid_genome_id:
                        wgs_candidates.append({"id": acc_id, "prio": priority})

        # --- 优选逻辑 ---
        if s16_candidates:
            # 16S 选最长的
            s16_candidates.sort(key=lambda x: x["len"], reverse=True)
            ids["16s"] = s16_candidates[0]["id"]
            best_len = s16_candidates[0]["len"]
            print(f" [16S选长:{best_len}bp]", end="")

        if wgs_candidates:
            # WGS 选完成度最高的
            wgs_candidates.sort(key=lambda x: x["prio"], reverse=True)
            ids["wgs"] = wgs_candidates[0]["id"]
            best_prio = wgs_candidates[0]["prio"]
            p_map = {3: "Complete", 2: "Scaffold", 1: "Contig", 0: "WGS"}
            print(f" [WGS选:{p_map.get(best_prio, 'Auto')}]", end="")

    except Exception as e: 
        print(f" [BacDive解析异常:{e}]", end="")
    return ids

# ================= 主程序 =================

def main():
    print(f"🚀 启动 JCM 补充测试 (目标: 前 {MAX_TEST_COUNT} 个 JCM 菌株)")
    print(f"📂 读取数据: {INPUT_CSV}")
    print(f"📂 保存序列: {abs_download_path}")
    
    # 1. 读取并筛选 JCM 菌株
    jcm_targets = []
    try:
        try:
            df = pd.read_csv(INPUT_CSV, encoding='utf-8-sig')
        except:
            df = pd.read_csv(INPUT_CSV, encoding='gbk')
            
        for index, row in df.iterrows():
            name = str(row.get('菌株名称', ''))
            page = row.get('页码', 'N/A')
            
            match = re.search(r"JCM\s+(\d+)", name, re.IGNORECASE)
            if match:
                jcm_num = match.group(1)
                jcm_targets.append({
                    "page": page,
                    "name": name,
                    "jcm_num": jcm_num
                })
    except Exception as e:
        print(f"❌ 读取 CSV 失败: {e}")
        return

    print(f"📊 共发现 {len(jcm_targets)} 个含 JCM 编号的菌株。")
    if len(jcm_targets) == 0: return

    # 截取前 N 个
    targets = jcm_targets[:MAX_TEST_COUNT]
    print(f"🔬 开始处理前 {len(targets)} 个任务...")

    if not os.path.exists(abs_csv_path):
        with open(abs_csv_path, mode='w', newline='', encoding='utf-8-sig') as f:
            csv.writer(f).writerow(['原页码', '菌株名称', 'JCM编号', 'BacDive链接', 'WGS_ID', 'WGS_状态', 'WGS_文件', '16S_ID', '16S_状态', '16S_文件'])

    driver = get_driver()

    try:
        for item in targets:
            jcm_num = item['jcm_num']
            name = item['name']
            page = item['page']
            
            print(f"\n🔹 [页{page}] JCM {jcm_num} ({name[:20]}...)", end="")
            
            # 1. JCM 官网 -> BacDive
            bacdive_url = get_bacdive_url_from_jcm(driver, jcm_num)
            
            wgs_id=wgs_stat=wgs_file=s16_id=s16_stat=s16_file="N/A"
            wgs_file = ""; s16_file = ""

            if bacdive_url:
                print(" -> BacDive", end="")
                # 2. BacDive -> IDs
                ids = parse_bacdive_page(driver, bacdive_url)
                
                if ids["wgs"] != "N/A":
                    wgs_id = ids["wgs"]
                    wgs_stat, wgs_file = download_sequence(wgs_id, name, "WGS")
                
                if ids["16s"] != "N/A":
                    s16_id = ids["16s"]
                    s16_stat, s16_file = download_sequence(s16_id, name, "16S")
                
                if ids["wgs"] == "N/A" and ids["16s"] == "N/A":
                    print(" [无序列信息]", end="")
            else:
                print(" [未找到BacDive链接]", end="")
                bacdive_url = "N/A"

            with open(abs_csv_path, mode='a', newline='', encoding='utf-8-sig') as f:
                csv.writer(f).writerow([
                    page, name, jcm_num, bacdive_url,
                    wgs_id, wgs_stat, wgs_file,
                    s16_id, s16_stat, s16_file
                ])
                
    except KeyboardInterrupt: print("\n🛑 停止")
    except Exception as e: print(f"\n❌ 错误: {e}")
    finally:
        if driver: driver.quit()
        print("\n👋 测试结束")

if __name__ == "__main__":
    main()