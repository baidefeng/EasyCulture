"""
DSMZ 菌株全量爬虫脚本 (V60 - 稳定终极版)
目标: 爬取 1-2378 页
路径: F:\JIYINZU-test
功能: 自动断点续传、防封延时、内存自动释放
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

# ================= 核心配置区域 (已修改) =================

# 1. 爬取范围
start_page = 1
end_page = 2378  # <--- 全量爬取

# 2. 路径设置 (硬编码为 F 盘指定位置)
# 主工作目录
BASE_WORK_DIR = r"F:\JIYINZU-test" 
# 序列下载文件夹名称
DOWNLOAD_FOLDER_NAME = "dsmz_sequences_all"
# 结果汇总表格名称
CSV_FILENAME = "dsmz_full_database.csv"

# 3. 稳定性设置
# 每爬取 50 页重启一次浏览器 (防止内存溢出/卡顿)
restart_interval = 50 

# ========================================================

# --- 0. 路径初始化与检查 ---
# 确保 F 盘目录存在
if not os.path.exists(BASE_WORK_DIR):
    try:
        os.makedirs(BASE_WORK_DIR)
        print(f"✅ 已创建主目录: {BASE_WORK_DIR}")
    except Exception as e:
        print(f"❌ 无法创建 F 盘目录: {e}")
        print("请检查 F 盘是否存在或是否有写入权限。")
        sys.exit(1)

# 拼接绝对路径
abs_download_path = os.path.join(BASE_WORK_DIR, DOWNLOAD_FOLDER_NAME)
abs_csv_path = os.path.join(BASE_WORK_DIR, CSV_FILENAME)

# 创建下载文件夹
if not os.path.exists(abs_download_path):
    os.makedirs(abs_download_path)

# 获取脚本所在目录 (用于查找 chromedriver)
current_script_dir = os.path.dirname(os.path.abspath(__file__))

# --- 1. 网络组件 ---
def get_requests_session():
    session = requests.Session()
    # 增加重试次数到 5 次，应对网络波动
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
    print("🚗 正在启动 Chrome 浏览器...")
    # 优先在脚本同目录下找驱动
    driver_path = os.path.join(current_script_dir, "chromedriver.exe")
    
    if not os.path.exists(driver_path):
        if shutil.which("chromedriver"):
            driver_path = "chromedriver"
        else:
            print(f"❌ 错误：在 {current_script_dir} 未找到 chromedriver.exe")
            print("请确保驱动文件与本脚本在同一文件夹！")
            sys.exit(1)

    chrome_options = Options()
    # 屏蔽自动化特征
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    # 屏蔽沙盒模式 (增强稳定性)
    chrome_options.add_argument("--no-sandbox") 
    chrome_options.add_argument("--disable-dev-shm-usage")
    # 如果想后台静默运行，取消下面这行的注释
    # chrome_options.add_argument("--headless") 
    
    try:
        service = Service(executable_path=driver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_page_load_timeout(90) # 延长超时时间到 90秒
        return driver
    except Exception as e:
        print(f"❌ 浏览器启动失败: {e}")
        sys.exit(1)

def get_soup_via_selenium(driver, url):
    """使用 Selenium 获取页面源码并转为 Soup"""
    max_retries = 3
    for i in range(max_retries):
        try:
            full_url = "https://mediadive.dsmz.de" + url if url.startswith("/") else url
            driver.get(full_url)
            # 随机延时，模拟人类操作
            time.sleep(random.uniform(1.0, 2.0)) 
            return BeautifulSoup(driver.page_source, "html.parser")
        except Exception as e:
            print(f"⚠️ 页面加载超时 (第 {i+1} 次重试): {e}")
            time.sleep(3)
    return None

# ============================================================
# 2. 下载模块 (核心逻辑)
# ============================================================

def resolve_wgs_to_assembly(wgs_acc):
    """将 WGS 编号 (如 ABCD00000000) 解析为 Assembly 编号 (如 GCA_...)"""
    try:
        url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        params = {"db": "assembly", "term": wgs_acc, "retmode": "json"}
        resp = http.get(url, params=params, timeout=15)
        id_list = resp.json()["esearchresult"]["idlist"]
        if id_list:
            uid = id_list[0]
            sum_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
            r2 = http.get(sum_url, params={"db": "assembly", "id": uid, "retmode": "json"}, timeout=15)
            data = r2.json()["result"][uid]
            return data["assemblyaccession"]
    except: pass
    return None

def download_assembly_https(assembly_acc, save_path):
    """通过 NCBI FTP 的 HTTPS 镜像下载 Assembly"""
    try:
        search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        params = {"db": "assembly", "term": assembly_acc, "retmode": "json"}
        resp = http.get(search_url, params=params, timeout=15)
        data = resp.json()
        
        if "esearchresult" not in data or not data["esearchresult"]["idlist"]:
            return False
            
        uid_list = data["esearchresult"]["idlist"]
        
        sum_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
        params = {"db": "assembly", "id": uid_list[0], "retmode": "json"}
        resp = http.get(sum_url, params=params, timeout=15)
        result = resp.json()["result"][uid_list[0]]
        
        ftp_url = result.get("ftppath_refseq") or result.get("ftppath_genbank")
        if not ftp_url: return False
        
        # 转换为 HTTPS
        https_base = ftp_url.replace("ftp://", "https://")
        file_prefix = https_base.split("/")[-1]
        target_file = f"{file_prefix}_genomic.fna.gz"
        download_link = f"{https_base}/{target_file}"
        
        print(f" (⬇️HTTPS)...", end="")
        with http.get(download_link, stream=True, timeout=180) as r:
            if r.status_code == 200:
                with open(save_path, 'wb') as f_out:
                    with gzip.open(r.raw, 'rb') as f_in:
                        shutil.copyfileobj(f_in, f_out)
                return True
    except: return False
    return False

def download_nucleotide_api(accession_id, save_path):
    """通过 API 下载普通序列"""
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    params = {"db": "nuccore", "id": accession_id, "rettype": "fasta", "retmode": "text"}
    try:
        with http.get(url, params=params, stream=True, timeout=90) as r:
            if r.status_code == 200:
                with open(save_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk: f.write(chunk)
                # 简单校验文件是否有效
                if os.path.exists(save_path) and os.path.getsize(save_path) > 50:
                    with open(save_path, "r", encoding="utf-8", errors="ignore") as f_check:
                        if f_check.readline().startswith(">"): return True
    except: pass
    return False

def download_sequence(accession_id, strain_name, type_suffix):
    """下载调度中心"""
    if not accession_id or "N/A" in accession_id: return "N/A", ""

    # 清理文件名中的非法字符
    safe_name = re.sub(r'[\\/*?:"<>|]', "_", strain_name)
    file_name = f"{safe_name}_{type_suffix}_{accession_id}.fasta"
    file_path = os.path.join(abs_download_path, file_name)
    
    # 检查是否已存在
    if os.path.exists(file_path) and os.path.getsize(file_path) > 100:
        return "已存在", file_name

    print(f"\n    ⬇️ [{type_suffix}] {accession_id}", end="")
    success = False

    # 策略选择
    if re.search(r"0000+$", accession_id): # 类似 ABCD00000000 的 WGS
        print(" -> 解析WGS...", end="")
        assembly_acc = resolve_wgs_to_assembly(accession_id)
        if assembly_acc:
            print(f"[{assembly_acc}]", end="")
            success = download_assembly_https(assembly_acc, file_path)
        else:
            print(" 解析失败, 尝试API直连...", end="")
            success = download_nucleotide_api(accession_id, file_path)
    elif accession_id.startswith("GC"): # 直接是 Assembly ID
        success = download_assembly_https(accession_id, file_path)
    else: # 普通 16S 或其他
        success = download_nucleotide_api(accession_id, file_path)

    if success:
        print(" ✅ OK", end="")
        return "成功", file_name
    
    print(" ❌ Fail", end="")
    # 失败也返回文件名以便记录，但在 CSV 中状态会是"失败"
    # 这里逻辑修改为：如果失败，状态为失败，文件名留空或保留
    return "失败", ""

# ============================================================
# 3. 解析逻辑
# ============================================================

def get_all_ncbi_ids_from_dsmz(catalog_url):
    results = {"wgs": "N/A", "16s": "N/A", "complete": "N/A", "found_any": False}
    if not catalog_url.startswith("http"): return results
    try:
        # 请求 DSMZ 详情页
        time.sleep(random.uniform(0.5, 1.0))
        resp = http.get(catalog_url, timeout=20)
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # 解析 WGS
        wgs = soup.find(string=re.compile("whole genome shotgun", re.IGNORECASE))
        if wgs: 
            link = wgs.find_next("a")
            if link: results["wgs"] = link.get_text(strip=True); results["found_any"]=True
        
        # 解析 16S
        rrna = soup.find(string=re.compile("16S rRNA gene", re.IGNORECASE))
        if rrna: 
            link = rrna.find_next("a")
            if link: results["16s"] = link.get_text(strip=True); results["found_any"]=True
        
        # 解析 Complete Genome
        comp = soup.find(string=re.compile("complete genome", re.IGNORECASE))
        if comp: 
            link = comp.find_next("a")
            if link: results["complete"] = link.get_text(strip=True); results["found_any"]=True
    except: pass
    return results

def find_catalog_link(soup, name):
    """在子页面查找跳转到 catalogue.dsmz.de 的链接"""
    try:
        # 提取 DSM 数字
        match = re.search(r"DSM\s+(\d+)", name)
        if not match: return None
        dsm_num = match.group(1)
        
        # 查找 Synonyms 区域的链接
        target = soup.find(string=re.compile(r"^Synonyms:?", re.IGNORECASE))
        if target and target.parent.parent:
            links = target.parent.parent.find_all("a")
            for link in links:
                # 链接文本必须包含 DSM 编号
                if re.search(rf"DSM\s+{dsm_num}(?!\d)", link.get_text()): 
                    return link['href']
    except: pass
    return None

def get_start_page():
    """断点续传逻辑：读取 CSV 最后一行，决定从哪一页开始"""
    if not os.path.exists(abs_csv_path): return 1
    try:
        with open(abs_csv_path, 'r', encoding='utf-8-sig') as f:
            lines = f.readlines()
            if len(lines) < 2: return 1 # 只有表头
            
            last_line = lines[-1]
            parts = last_line.split(',')
            if parts[0].isdigit():
                last_page = int(parts[0])
                # 检查该页是否爬完（简单策略：直接从下一页开始，或者重爬最后一页）
                # 为了稳妥，建议从最后一页的下一页开始
                print(f"📂 历史记录检测: 上次停在第 {last_page} 页")
                
                # 这里有个小逻辑：如果上次最后一页没跑完怎么办？
                # 实际上如果 CSV 是追加写入的，重复跑一页问题不大，因为有文件存在检测
                # 但为了数据整洁，我们从 last_page 开始跑（覆盖这页可能缺失的后续数据）
                print(f"🔄 将从第 {last_page} 页重新开始检查...")
                return last_page 
    except: pass
    return 1

# ================= 主程序 =================

def main():
    driver = None
    try:
        print(f"🎯 目标路径: {BASE_WORK_DIR}")
        print(f"📂 序列存放: {abs_download_path}")
        print(f"📄 数据表格: {abs_csv_path}")
        print(f"⏱️ 任务范围: 第 {start_page} 页 -> 第 {end_page} 页")
        print("-" * 50)

        current_page = get_start_page()
        
        # 如果是新文件，写入表头
        if current_page == 1 and not os.path.exists(abs_csv_path):
            with open(abs_csv_path, mode='w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow([
                    '页码', '菌株名称', 'DSM编号', 
                    'WGS_ID', 'WGS_状态', 'WGS_文件',
                    '16S_ID', '16S_状态', '16S_文件',
                    'Complete_ID', 'Complete_状态', 'Complete_文件'
                ])

        driver = get_driver()

        # 开始循环
        for page in range(current_page, end_page + 1):
            # 内存保护机制：每隔一定页数重启浏览器
            if (page - current_page) > 0 and (page - current_page) % restart_interval == 0:
                print("\n♻️ 触发内存保护，重启浏览器...")
                driver.quit()
                time.sleep(5)
                driver = get_driver()

            url = f"/strains?p={page}"
            print(f"\n=== 正在处理第 {page} / {end_page} 页 ===")
            
            soup = get_soup_via_selenium(driver, url)
            
            if soup and soup.find("table"):
                rows = soup.find("table").find("tbody").find_all("tr")
                
                # 动态定位 Name 列
                th = [t.get_text(strip=True) for t in soup.find("table").find_all("th")]
                name_idx = -1
                for i, t in enumerate(th):
                    if "Name" in t: name_idx = i
                
                if name_idx == -1:
                    print("❌ 无法定位 Name 列，跳过此页")
                    continue

                # 逐行处理
                for row in rows:
                    cols = row.find_all("td")
                    if len(cols) > name_idx:
                        name_text = cols[name_idx].get_text(strip=True)
                        
                        # 提取 DSM 编号
                        dsm_id_match = re.search(r"DSM\s+(\d+)", name_text)
                        dsm_id = f"DSM {dsm_id_match.group(1)}" if dsm_id_match else "N/A"
                        
                        print(f"\n🦠 {name_text[:30]}...", end="")
                        
                        # 获取详情页链接
                        link_tag = cols[name_idx].find("a")
                        strain_url = link_tag['href'] if link_tag else ""
                        
                        # 初始化变量
                        wgs_id, wgs_stat, wgs_file = "N/A", "", ""
                        s16_id, s16_stat, s16_file = "N/A", "", ""
                        comp_id, comp_stat, comp_file = "N/A", "", ""
                        
                        if strain_url:
                            # 进入详情页
                            sub_soup = get_soup_via_selenium(driver, strain_url)
                            if sub_soup:
                                # 查找跳转 DSMZ 官网的链接
                                cat_link = find_catalog_link(sub_soup, name_text)
                                
                                if cat_link:
                                    # 去官网爬取 ID
                                    ids_map = get_all_ncbi_ids_from_dsmz(cat_link)
                                    if ids_map["found_any"]:
                                        print(" [🔍发现ID]", end="")
                                        # 下载 WGS
                                        if ids_map["wgs"] != "N/A":
                                            wgs_id = ids_map["wgs"]
                                            wgs_stat, wgs_file = download_sequence(wgs_id, name_text, "WGS")
                                        # 下载 16S
                                        if ids_map["16s"] != "N/A":
                                            s16_id = ids_map["16s"]
                                            s16_stat, s16_file = download_sequence(s16_id, name_text, "16S")
                                        # 下载 Complete
                                        if ids_map["complete"] != "N/A":
                                            comp_id = ids_map["complete"]
                                            comp_stat, comp_file = download_sequence(comp_id, name_text, "Complete")
                                    else:
                                        print(" [无序列信息]", end="")
                                else:
                                    print(" [无Catalog链接]", end="")
                        
                        # 实时写入 CSV (防止程序崩溃数据丢失)
                        with open(abs_csv_path, mode='a', newline='', encoding='utf-8-sig') as f:
                            writer = csv.writer(f)
                            writer.writerow([
                                page, name_text, dsm_id,
                                wgs_id, wgs_stat, wgs_file,
                                s16_id, s16_stat, s16_file,
                                comp_id, comp_stat, comp_file
                            ])
            else:
                print("⚠️ 页面结构异常或网络错误，稍后重试...")
                time.sleep(10)

    except KeyboardInterrupt:
        print("\n🛑 用户手动停止任务！")
        print(f"您可以随时重新运行脚本，将从第 {page} 页继续。")
    except Exception as e:
        print(f"\n❌ 发生未预期的严重错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if driver: driver.quit()
        print("\n👋 程序结束")

if __name__ == "__main__":
    main()