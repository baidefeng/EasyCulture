import os
import sys
import time
import random
import csv
import re
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

# ================= 配置区域 =================
total_pages = 2738      # <--- 已更新为 2738 页
filename = "dsmz_full_2738pages.csv" 
restart_interval = 100  # 每跑 100 页重启一次浏览器 (释放内存)
# ===========================================

media_cache = {} 

def get_driver():
    # print("🚗 启动 Chrome...")
    current_dir = os.path.dirname(os.path.abspath(__file__))
    driver_path = os.path.join(current_dir, "chromedriver.exe")
    
    if not os.path.exists(driver_path):
        driver_path = r"C:\Program Files\Python313\chromedriver.exe"

    chrome_options = Options()
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    # chrome_options.add_argument("--headless") # 建议保留界面监控
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    service = Service(executable_path=driver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.set_page_load_timeout(60)
    return driver

# --- 核心抓取函数 (保持 V25/V30 的最佳逻辑) ---

def get_soup(driver, url):
    full_url = "https://mediadive.dsmz.de" + url if url.startswith("/") else url
    try:
        driver.get(full_url)
        time.sleep(random.uniform(0.8, 1.5)) # 稍微加快一点点节奏
        return BeautifulSoup(driver.page_source, "html.parser")
    except: return None

def get_taxonomy_smart(driver, tax_url, detail_soup):
    # 1. 优先找详情页
    if detail_soup:
        try:
            bac = detail_soup.find("a", string=re.compile("Bacteria|Archaea"))
            if bac:
                text = bac.parent.parent.get_text(" > ", strip=True)
                if ">" in text and len(text) < 500: return text
        except: pass
    # 2. 备用去 Tax 页
    if tax_url:
        soup = get_soup(driver, tax_url)
        if soup:
            header = soup.find(string=re.compile("Taxonomic tree", re.IGNORECASE))
            if header:
                lines = header.parent.parent.get_text("\n", strip=True).split('\n')
                clean = []
                for line in lines:
                    if re.search(r"\d+\s*media", line): continue
                    if "Taxonomic" in line: continue
                    l = line.replace("▼","").replace("►","").strip()
                    if len(l)>2: clean.append(l)
                if clean: return " > ".join(clean)
    return "N/A"

def get_clean_ingredients(driver, media_id):
    clean_id = str(media_id).replace('*', '').strip()
    if clean_id in media_cache: return media_cache[clean_id]
    
    soup = get_soup(driver, f"/medium/{clean_id}")
    if soup:
        target_table = None
        for t in soup.find_all("table"):
            headers = [th.get_text(strip=True).lower() for th in t.find_all("th")]
            if any(k in headers for k in ["compound", "amount", "substance"]):
                target_table = t; break
        
        if target_table:
            res = []
            for r in target_table.find_all("tr"):
                d = [x.get_text(strip=True) for x in r.find_all("td")]
                if any(d): res.append(" ".join(d))
            txt = " + ".join(res)
            media_cache[clean_id] = txt
            return txt
    return "PDF/No Table"

def get_growth_info(soup):
    info = {}
    links = soup.find_all("a", href=re.compile(r"/medium/"))
    for l in links:
        txt = l.get_text(strip=True)
        m = re.match(r"^([A-Z0-9]+):", txt)
        if m:
            mid = m.group(1)
            info[mid] = {'temp':'N/A','time':'N/A','cond':'N/A'}
            box = l.find_parent("div", class_="box")
            if not box:
                for p in l.parents:
                    if p.name=="div" and "Growth" in p.get_text(): box=p; break
            if box:
                badges = box.find_all("span", class_=re.compile("badge"))
                conds = []
                for b in badges:
                    val = b.get_text(strip=True)
                    if "°C" in val: info[mid]['temp'] = val
                    elif any(x in val for x in ["day","hour","week"]): info[mid]['time'] = val
                    else: conds.append(val)
                if conds: info[mid]['cond'] = ", ".join(conds)
    return info

def get_synonyms(soup):
    try:
        t = soup.find(string=re.compile(r"^Synonyms:?", re.IGNORECASE))
        if t: return re.sub(r"^Synonyms:?\s*", "", t.parent.parent.get_text(" ", strip=True), flags=re.IGNORECASE).strip()
    except: pass
    return "N/A"

# ================= 主程序 =================

def get_start_page():
    """检查断点"""
    if not os.path.exists(filename): return 1
    try:
        with open(filename, 'r', encoding='utf-8-sig') as f:
            lines = f.readlines()
            if len(lines) < 2: return 1 # 只有表头
            last_line = lines[-1]
            parts = last_line.split(',')
            if parts[0].isdigit():
                last_page = int(parts[0])
                print(f"📂 发现旧记录，从第 {last_page} 页继续...")
                return last_page # 重新跑最后一页防止数据不全，或者 last_page + 1
    except: pass
    return 1

def main():
    current_page = get_start_page()
    
    # 新建文件写表头
    if current_page == 1 and not os.path.exists(filename):
        with open(filename, mode='w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow([
                '页码', '菌株名称', 'DSM编号', 
                '其他编号 (Synonyms)', '分类学 (Taxonomy)', 
                '原始培养基列', '当前ID', 
                '培养温度', '培养时间', '环境条件', '成分'
            ])

    print(f"🚀 启动全量抓取！目标: {total_pages} 页")
    print("-" * 50)

    driver = get_driver()
    
    try:
        for page in range(current_page, total_pages + 1):
            
            # 内存释放重启
            if (page - current_page) > 0 and page % restart_interval == 0:
                print(f"\n🔄 正在重启浏览器 (释放内存)...")
                driver.quit()
                time.sleep(5)
                driver = get_driver()
                print("✅ 重启完毕")

            print(f"\n=== 正在处理第 {page}/{total_pages} 页 ===")
            
            try:
                soup = get_soup(driver, f"/strains?p={page}")
                
                if soup and soup.find("table"):
                    rows = soup.find("table").find("tbody").find_all("tr")
                    th = [t.get_text(strip=True) for t in soup.find("table").find_all("th")]
                    
                    idx = {'Name':-1, 'Growth':-1, 'Tax':-1}
                    for i, t in enumerate(th):
                        if "Name" in t: idx['Name']=i
                        if "Growth" in t: idx['Growth']=i
                        if "Tax" in t: idx['Tax']=i

                    # 追加写入模式
                    with open(filename, mode='a', newline='', encoding='utf-8-sig') as f:
                        writer = csv.writer(f)
                        
                        total_rows = len(rows)
                        for i, row in enumerate(rows):
                            cols = row.find_all("td")
                            if len(cols) > max(idx.values()):
                                name_tag = cols[idx['Name']]
                                name = name_tag.get_text(strip=True)
                                
                                # 使用 separator=" " 防止连体婴
                                media_raw = cols[idx['Growth']].get_text(separator=" ", strip=True)
                                
                                strain_url = name_tag.find("a")['href'] if name_tag.find("a") else ""
                                tax_url = cols[idx['Tax']].find("a")['href'] if cols[idx['Tax']].find("a") else ""
                                
                                if strain_url:
                                    print(f"[{i+1}/{total_rows}] 页{page} - {name[:20]}...", end="", flush=True)
                                    
                                    sub_soup = get_soup(driver, strain_url)
                                    if sub_soup:
                                        syn = get_synonyms(sub_soup)
                                        tax = get_taxonomy_smart(driver, tax_url, sub_soup)
                                        growth = get_growth_info(sub_soup)
                                        dsm_id = re.search(r"DSM\s+(\d+)", name).group(1) if "DSM" in name else "N/A"
                                        
                                        # 拆分培养基
                                        media_list = media_raw.split()
                                        if not media_list: media_list = ["N/A"] # 防止空列表
                                        
                                        for mid in media_list:
                                            clean_mid = mid.replace('*', '').strip()
                                            if not clean_mid: continue
                                            
                                            ing = get_clean_ingredients(driver, clean_mid)
                                            inf = growth.get(mid, growth.get(clean_mid, {'temp':'N/A','time':'N/A','cond':'N/A'}))
                                            
                                            writer.writerow([
                                                page, name, dsm_id, 
                                                syn, tax, 
                                                media_raw, mid, 
                                                inf['temp'], inf['time'], inf['cond'], ing
                                            ])
                                        print(" ✅")
                                    else:
                                        print(" ❌ [详情页跳过]")
                else:
                    print("⚠️ 本页无数据 (或加载失败)")
                    time.sleep(5) # 休息一下重试下一页

            except Exception as e:
                print(f"❌ 页面错误: {e}")
            
    except KeyboardInterrupt:
        print("\n🛑 已暂停！下次运行将自动继续。")
    
    finally:
        if 'driver' in locals():
            driver.quit()
            print("👋 结束")

if __name__ == "__main__":
    main()