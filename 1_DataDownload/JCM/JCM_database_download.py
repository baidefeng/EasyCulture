"""
脚本名称: JCM_Full_Crawler.py (JCM全量爬取生产版)
功能: 
1. 读取本地 dsmz_full_database.csv，筛选所有含 JCM 编号的菌株。
2. 自动去重，排除已经爬取过的菌株 (支持断点续传)。
3. 访问 JCM 官网 -> 跳转 BacDive -> 提取 16S/Genome 编号 -> 下载序列。
4. 结果保存至 "JCM_seq_Whole" 文件夹及 "JCM数据库全部爬取.csv"。
5. 内置浏览器重启机制，防止长期运行内存溢出。
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

# ================= 核心配置区域 (生产环境) =================
# 输入文件 (您之前的运行结果)
INPUT_CSV = r"F:\JIYINZU-test\dsmz_full_database.csv"

# 输出设置
BASE_WORK_DIR = r"F:\JIYINZU-test"
DOWNLOAD_FOLDER_NAME = "JCM_seq_Whole"        # <--- 全量序列文件夹
OUTPUT_CSV = "JCM数据库全部爬取.csv"           # <--- 全量结果表格

# 稳定性设置
RESTART_INTERVAL = 50  # 每处理50个菌株重启一次浏览器，防止内存泄漏
# ========================================================

# --- 0. 路径初始化 ---
abs_download_path = os.path.join(BASE_WORK_DIR, DOWNLOAD_FOLDER_NAME)
abs_csv_path = os.path.join(BASE_WORK_DIR, OUTPUT_CSV)

if not os.path.exists(abs_download_path): 
    os.makedirs(abs_download_path)
    print(f"✅ 序列保存目录已就绪: {abs_download_path}")

current_script_dir = os.path.dirname(os.path.abspath(__file__))

# --- 1. 网络与浏览器组件 ---
def get_requests_session():
    session = requests.Session()
    # 增加重试次数，提高网络波动抵抗力
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    })
    return session

http = get_requests_session()

def get_driver():
    print("🚗 正在启动/重启 Chrome...")
    driver_path = os.path.join(current_script_dir, "chromedriver.exe")
    if not os.path.exists(driver_path):
        if shutil.which("chromedriver"): driver_path = "chromedriver"
        else: print("❌ 未找到 chromedriver.exe"); sys.exit(1)

    opts = Options()
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    # opts.add_argument("--headless") # 生产环境如果想后台运行可取消注释
    
    try:
        service = Service(executable_path=driver_path)
        driver = webdriver.Chrome(service=service, options=opts)
        driver.set_page_load_timeout(60) # 设置页面加载超时
        return driver
    except Exception as e: 
        print(f"❌ 浏览器启动失败: {e}")
        time.sleep(5) # 失败等待后重试
        return None

# --- 2. 下载引擎 (保持不变) ---
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

# --- 3. JCM & BacDive 解析逻辑 (V71) ---
def get_bacdive_url_from_jcm(driver, jcm_num):
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
    ids = {"16s": "N/A", "wgs": "N/A"}
    try:
        driver.get(bacdive_url)
        time.sleep(2)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        s16_candidates = [] 
        wgs_candidates = [] 

        for table in soup.find_all("table"):
            headers = [th.get_text(strip=True).lower() for th in table.find_all("th")]
            
            def get_col_idx(name_part):
                for i, h in enumerate(headers):
                    if name_part in h: return i
                return -1

            acc_idx = get_col_idx("accession number")
            len_idx = get_col_idx("length")
            level_idx = get_col_idx("assembly level")

            if acc_idx == -1: continue

            prev_header = table.find_previous(["h3", "h4", "h2"])
            section_title = prev_header.get_text(strip=True).lower() if prev_header else ""
            
            is_16s_table = "16s" in section_title or "16s" in str(table).lower()
            is_genome_table = "genome" in section_title or "assembly" in str(headers)

            rows = table.find_all("tr")[1:]
            for row in rows:
                cols = row.find_all("td")
                if len(cols) <= acc_idx: continue
                
                raw_acc_text = cols[acc_idx].get_text(strip=True)
                if not raw_acc_text: continue 
                
                parts = raw_acc_text.split()
                if not parts: continue 
                
                acc_id = parts[0]

                if is_16s_table:
                    if not (re.match(r"^[A-Z]{1,2}\d{5,6}", acc_id) or re.match(r"^[A-Z]{4,6}\d{8,}", acc_id)):
                        continue
                    length = 0
                    if len_idx != -1 and len(cols) > len_idx:
                        try:
                            length = int(re.sub(r"\D", "", cols[len_idx].get_text(strip=True)))
                        except: length = 0
                    s16_candidates.append({"id": acc_id, "len": length})

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

        if s16_candidates:
            s16_candidates.sort(key=lambda x: x["len"], reverse=True)
            ids["16s"] = s16_candidates[0]["id"]
            best_len = s16_candidates[0]["len"]
            print(f" [16S:{best_len}bp]", end="")

        if wgs_candidates:
            wgs_candidates.sort(key=lambda x: x["prio"], reverse=True)
            ids["wgs"] = wgs_candidates[0]["id"]
            best_prio = wgs_candidates[0]["prio"]
            p_map = {3: "Complete", 2: "Scaffold", 1: "Contig", 0: "WGS"}
            print(f" [WGS:{p_map.get(best_prio, 'Auto')}]", end="")

    except Exception as e: 
        print(f" [BacDive解析异常:{e}]", end="")
    return ids

# ================= 主程序 (全量 + 断点续传) =================

def main():
    print(f"🚀 启动 JCM 全量爬取任务")
    print(f"📂 输入: {INPUT_CSV}")
    print(f"📂 输出: {abs_csv_path}")
    
    # 1. 读取 JCM 任务列表
    all_jcm_tasks = []
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
                all_jcm_tasks.append({
                    "page": page,
                    "name": name,
                    "jcm_num": jcm_num
                })
    except Exception as e:
        print(f"❌ 读取 CSV 失败: {e}")
        return

    print(f"📊 总任务数: {len(all_jcm_tasks)} 个")

    # 2. 读取已完成列表 (断点续传核心)
    processed_jcm = set()
    if os.path.exists(abs_csv_path):
        try:
            df_done = pd.read_csv(abs_csv_path, encoding='utf-8-sig')
            if 'JCM编号' in df_done.columns:
                processed_jcm = set(df_done['JCM编号'].astype(str))
                print(f"📂 检测到历史记录: 已完成 {len(processed_jcm)} 个，将自动跳过。")
        except: 
            pass # 文件可能为空或损坏，忽略

    # 3. 过滤出剩余任务
    tasks_to_do = [t for t in all_jcm_tasks if str(t['jcm_num']) not in processed_jcm]
    print(f"🔬 剩余待处理: {len(tasks_to_do)} 个")

    if not tasks_to_do:
        print("🎉 所有任务已完成！")
        return

    # 初始化输出文件 (如果不存在)
    if not os.path.exists(abs_csv_path):
        with open(abs_csv_path, mode='w', newline='', encoding='utf-8-sig') as f:
            csv.writer(f).writerow(['原页码', '菌株名称', 'JCM编号', 'BacDive链接', 'WGS_ID', 'WGS_状态', 'WGS_文件', '16S_ID', '16S_状态', '16S_文件'])

    driver = get_driver()
    processed_count = 0

    try:
        for item in tasks_to_do:
            # 内存保护机制
            if processed_count > 0 and processed_count % RESTART_INTERVAL == 0:
                print("\n♻️ 触发内存保护，正在重启浏览器...", end="")
                if driver: driver.quit()
                time.sleep(3)
                driver = get_driver()
                print(" 重启完成。")

            jcm_num = item['jcm_num']
            name = item['name']
            page = item['page']
            
            print(f"\n🔹 [{processed_count+1}/{len(tasks_to_do)}] 页{page} JCM {jcm_num}", end="")
            
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

            # 实时写入结果 (防止崩溃丢失)
            with open(abs_csv_path, mode='a', newline='', encoding='utf-8-sig') as f:
                csv.writer(f).writerow([
                    page, name, jcm_num, bacdive_url,
                    wgs_id, wgs_stat, wgs_file,
                    s16_id, s16_stat, s16_file
                ])
            
            processed_count += 1
                
    except KeyboardInterrupt: print("\n🛑 用户停止")
    except Exception as e: 
        print(f"\n❌ 严重错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if driver: driver.quit()
        print("\n👋 任务结束")

if __name__ == "__main__":
    main()