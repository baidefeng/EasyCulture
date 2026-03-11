"""
DSMZ 菌株全量爬虫脚本 (V64 - 强力反搜修复版)
核心修复:
1. 彻底重写 "Other collection no." 的抓取逻辑，不再依赖 HTML 表格结构，改用文本流暴力匹配。
2. 增加调试打印，一旦发现同义编号立即显示，确保您知道代码在干什么。
3. 优化 NCBI 搜索参数，提高命中率。
"""

import os
import sys
import time
import random
import csv
import re
import gzip
import shutil
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ================= 核心配置区域 =================
start_page = 1
end_page = 2378  # 全量模式
BASE_WORK_DIR = r"F:\JIYINZU-test"
DOWNLOAD_FOLDER_NAME = "dsmz_sequences_all"
CSV_FILENAME = "dsmz_full_database.csv"
restart_interval = 50
# ===============================================

# --- 0. 路径初始化 ---
if not os.path.exists(BASE_WORK_DIR):
    try:
        os.makedirs(BASE_WORK_DIR)
    except:
        print(f"❌ 无法创建目录: {BASE_WORK_DIR}"); sys.exit(1)

abs_download_path = os.path.join(BASE_WORK_DIR, DOWNLOAD_FOLDER_NAME)
abs_csv_path = os.path.join(BASE_WORK_DIR, CSV_FILENAME)
if not os.path.exists(abs_download_path): os.makedirs(abs_download_path)
current_script_dir = os.path.dirname(os.path.abspath(__file__))

# --- 1. 网络组件 ---
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
    # opts.add_argument("--headless") 
    
    try:
        service = Service(executable_path=driver_path)
        driver = webdriver.Chrome(service=service, options=opts)
        driver.set_page_load_timeout(90)
        return driver
    except Exception as e: print(f"❌ 浏览器失败: {e}"); sys.exit(1)

def get_soup_via_selenium(driver, url):
    for i in range(3):
        try:
            full_url = "https://mediadive.dsmz.de" + url if url.startswith("/") else url
            driver.get(full_url)
            time.sleep(random.uniform(1.0, 2.0))
            return BeautifulSoup(driver.page_source, "html.parser")
        except: time.sleep(3)
    return None

# ============================================================
# 2. 下载模块 (NCBI + ENA)
# ============================================================

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
    
    if os.path.exists(file_path) and os.path.getsize(file_path) > 100:
        return "已存在", file_name

    print(f"\n    ⬇️ [{type_suffix}] {accession_id}", end="")
    
    success = False
    if re.search(r"0000+$", accession_id):
        acc = resolve_wgs_to_assembly(accession_id)
        if acc: success = download_assembly_https(acc, file_path)
        else: success = download_nucleotide_api(accession_id, file_path)
    elif accession_id.startswith("GC"):
        success = download_assembly_https(accession_id, file_path)
    else:
        success = download_nucleotide_api(accession_id, file_path)

    if not success:
        success = download_from_ena(accession_id, file_path)

    if success: return "成功", file_name
    print(" ❌ 失败", end="")
    return "失败", ""

# ============================================================
# 3. 增强解析逻辑 (官网 + 反向搜索)
# ============================================================

def search_ncbi_by_synonym(collection_id):
    """去 NCBI 搜索同义编号"""
    try:
        # 1. 搜 Assembly (WGS)
        url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        term = f'"{collection_id}"' # 放宽搜索条件，去掉[Strain]以增加命中率
        
        resp = http.get(url, params={"db": "assembly", "term": term, "retmode": "json"}, timeout=10)
        ids = resp.json().get("esearchresult", {}).get("idlist", [])
        
        if ids:
            sum_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
            r2 = http.get(sum_url, params={"db": "assembly", "id": ids[0], "retmode": "json"}, timeout=10)
            acc = r2.json()["result"][ids[0]]["assemblyaccession"]
            return {"type": "WGS", "id": acc}
            
        # 2. 搜 16S (Nucleotide)
        term_16s = f'"{collection_id}" AND 16S rRNA'
        resp = http.get(url, params={"db": "nuccore", "term": term_16s, "retmode": "json", "retmax": 1}, timeout=10)
        ids = resp.json().get("esearchresult", {}).get("idlist", [])
        
        if ids:
            sum_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
            r2 = http.get(sum_url, params={"db": "nuccore", "id": ids[0], "retmode": "json"}, timeout=10)
            acc = r2.json()["result"][ids[0]]["caption"]
            return {"type": "16S", "id": acc}
    except: pass
    return None

def get_all_ncbi_ids_from_dsmz(catalog_url, driver=None):
    results = {"wgs": "N/A", "16s": "N/A", "complete": "N/A", "found_any": False}
    soup = None
    
    # 获取 Soup
    if driver:
        soup = BeautifulSoup(driver.page_source, "html.parser")
    elif catalog_url.startswith("http"):
        try:
            resp = http.get(catalog_url, timeout=15)
            soup = BeautifulSoup(resp.text, "html.parser")
        except: return results
    else: return results

    # --- A. 官方链接 ---
    try:
        wgs = soup.find(string=re.compile("whole genome shotgun", re.IGNORECASE))
        if wgs: results["wgs"] = wgs.find_next("a").get_text(strip=True); results["found_any"]=True
        
        rrna = soup.find(string=re.compile("16S rRNA gene", re.IGNORECASE))
        if rrna: results["16s"] = rrna.find_next("a").get_text(strip=True); results["found_any"]=True
        
        comp = soup.find(string=re.compile("complete genome", re.IGNORECASE))
        if comp: results["complete"] = comp.find_next("a").get_text(strip=True); results["found_any"]=True
    except: pass

    # --- B. 强力反向搜索 (当官方无数据时) ---
    if not results["found_any"]:
        # 🛠️【关键修改】不依赖表格结构，直接在全文中搜索关键词
        # 获取页面所有文本，移除多余空格
        page_text = soup.get_text(" ", strip=True)
        
        # 正则查找 "Other collection no... ATCC 12345" 这种模式
        # 匹配模式：找到关键词，然后向后取 200 个字符，尝试从中提取 ATCC/CCM 编号
        # 这种方法能无视 HTML 结构的变动
        
        hit_text = ""
        match_pos = re.search(r"Other collection no|WDCM no", page_text, re.IGNORECASE)
        if match_pos:
            start = match_pos.end()
            hit_text = page_text[start : start + 200] # 向后截取200字符
        
        if hit_text:
            # 提取 ATCC, CCM, NCTC, NCIMB
            potential_ids = re.findall(r"(ATCC|CCM|NCTC|NCIMB)\s+(\d+)", hit_text)
            
            if potential_ids:
                # 去重
                potential_ids = list(set(potential_ids))
                print(f" [🧐提取到:{potential_ids[0][0]} {potential_ids[0][1]}...]", end="")
                
                for collection, num in potential_ids:
                    search_query = f"{collection} {num}"
                    print(f".", end="") 
                    
                    found = search_ncbi_by_synonym(search_query)
                    if found:
                        print(f"✅", end="")
                        if found['type'] == "WGS":
                            results["wgs"] = found["id"]
                            results["found_any"] = True
                        elif found['type'] == "16S":
                            results["16s"] = found["id"]
                            results["found_any"] = True
                        break # 找到一个就收手，避免请求过多被封
    return results

def find_catalog_link(soup, name):
    try:
        match = re.search(r"DSM\s+(\d+)", name)
        if not match: return None
        dsm_num = match.group(1)
        target = soup.find(string=re.compile(r"^Synonyms:?", re.IGNORECASE))
        if target and target.parent.parent:
            links = target.parent.parent.find_all("a")
            for link in links:
                if re.search(rf"DSM\s+{dsm_num}(?!\d)", link.get_text()): return link['href']
    except: pass
    return None

def get_start_page():
    if not os.path.exists(abs_csv_path): return 1
    try:
        with open(abs_csv_path, 'r', encoding='utf-8-sig') as f:
            lines = f.readlines()
            if len(lines) < 2: return 1
            last_line = lines[-1]
            parts = last_line.split(',')
            if parts[0].isdigit():
                last_page = int(parts[0])
                print(f"📂 从第 {last_page} 页继续...")
                return last_page 
    except: pass
    return 1

def main():
    driver = None
    try:
        print(f"🚀 启动 V64 强力反搜版 | 目标: {end_page} 页")
        print(f"📂 保存: {abs_download_path}")
        
        current_page = get_start_page()
        if current_page == 1 and not os.path.exists(abs_csv_path):
            with open(abs_csv_path, mode='w', newline='', encoding='utf-8-sig') as f:
                csv.writer(f).writerow(['页码', '菌株名称', 'DSM编号', 'WGS_ID', 'WGS_状态', 'WGS_文件', '16S_ID', '16S_状态', '16S_文件', 'Complete_ID', 'Complete_状态', 'Complete_文件'])

        driver = get_driver()

        for page in range(current_page, end_page + 1):
            if (page - current_page) > 0 and (page - current_page) % restart_interval == 0:
                print("\n♻️ 重启浏览器..."); driver.quit(); time.sleep(5); driver = get_driver()

            print(f"\n=== 第 {page} / {end_page} 页 ===")
            soup = get_soup_via_selenium(driver, f"/strains?p={page}")
            
            if soup and soup.find("table"):
                rows = soup.find("table").find("tbody").find_all("tr")
                th = [t.get_text(strip=True) for t in soup.find("table").find_all("th")]
                name_idx = -1
                for i, t in enumerate(th):
                    if "Name" in t: name_idx = i
                
                if name_idx == -1: continue

                for row in rows:
                    cols = row.find_all("td")
                    if len(cols) > name_idx:
                        name_text = cols[name_idx].get_text(strip=True)
                        dsm_id_match = re.search(r"DSM\s+(\d+)", name_text)
                        dsm_id = f"DSM {dsm_id_match.group(1)}" if dsm_id_match else "N/A"
                        print(f"\n🦠 {name_text[:30]}...", end="")
                        
                        link_tag = cols[name_idx].find("a")
                        strain_url = link_tag['href'] if link_tag else ""
                        
                        wgs_id=wgs_stat=wgs_file=s16_id=s16_stat=s16_file=comp_id=comp_stat=comp_file="N/A"; wgs_file=""; s16_file=""; comp_file=""
                        
                        if strain_url:
                            sub_soup = get_soup_via_selenium(driver, strain_url)
                            if sub_soup:
                                cat_link = find_catalog_link(sub_soup, name_text)
                                if cat_link:
                                    try:
                                        # 进入详情页以获取完整信息
                                        driver.get("https://mediadive.dsmz.de" + cat_link if cat_link.startswith("/") else cat_link)
                                        time.sleep(1)
                                        ids = get_all_ncbi_ids_from_dsmz(cat_link, driver)
                                        
                                        if ids["found_any"]:
                                            print(" [📥ID]", end="")
                                            if ids["wgs"]!="N/A": wgs_id=ids["wgs"]; wgs_stat,wgs_file=download_sequence(wgs_id,name_text,"WGS")
                                            if ids["16s"]!="N/A": s16_id=ids["16s"]; s16_stat,s16_file=download_sequence(s16_id,name_text,"16S")
                                            if ids["complete"]!="N/A": comp_id=ids["complete"]; comp_stat,comp_file=download_sequence(comp_id,name_text,"Complete")
                                        else: print(" [无序列]", end="")
                                    except: print(" [超时]", end="")
                                else: print(" [无Link]", end="")
                        
                        with open(abs_csv_path, mode='a', newline='', encoding='utf-8-sig') as f:
                            csv.writer(f).writerow([page, name_text, dsm_id, wgs_id, wgs_stat, wgs_file, s16_id, s16_stat, s16_file, comp_id, comp_stat, comp_file])
            else:
                print("⚠️ 页面异常，重试..."); time.sleep(10)

    except KeyboardInterrupt: print("\n🛑 停止")
    except Exception as e: print(f"\n❌ 错误: {e}")
    finally:
        if driver: driver.quit()

if __name__ == "__main__":
    main()