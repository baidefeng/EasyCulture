# 数据爬取模块说明

## 📁 目录结构

```
1_DataCrawlers/
├── DSMZ/                    # DSMZ 数据库爬虫
│   ├── dsmz_crawler_v63.py  # 菌株信息爬取
│   ├── dsmz_v31_菌株培养条件爬取.py
│   └── dsmz_seq_full.py     # 序列下载
│
├── JCM/                     # JCM 数据库爬虫
│   ├── JCM数据库全部爬取.py
│   ├── JCM数据库全部爬取1.1.py
│   ├── JCM数据库全部爬取-后半1.2.py
│   └── JCM库补充测试.py
│
├── MediaDive/               # MediaDive 培养基信息爬虫
│   └── (相关脚本)
│
└── ATCC_CCM_NCIMB/          # 其他菌种库序列补充
    ├── ATCC_CCM_NCIMB序列补充爬取_V3_优化版.py
    └── ATCC_CCM_NCIMB序列补充爬取_V4_严谨版.py
```

## 🔧 各模块功能

### 1. DSMZ 爬虫

#### dsmz_crawler_v63.py
- **功能**: 爬取 DSMZ 数据库的菌株基本信息
- **输出**: `dsmz_full_database.csv`
- **包含字段**: 
  - 菌株名称
  - DSM 编号
  - 分类信息
  - 培养条件
  - 序列信息

#### dsmz_v31_菌株培养条件爬取.py
- **功能**: 专门爬取培养条件详细信息
- **输出**: 培养温度、时间、环境条件等

#### dsmz_seq_full.py
- **功能**: 下载 DSMZ 菌株的基因组序列
- **输出**: FASTA 格式序列文件

### 2. JCM 爬虫

#### JCM数据库全部爬取.py
- **功能**: 爬取 JCM 数据库的菌株信息和序列
- **输出**: `JCM数据库全部爬取.csv` + 序列文件
- **特点**: 
  - 支持断点续传
  - 自动重试机制
  - 浏览器定期重启（防止崩溃）

#### JCM数据库全部爬取1.1.py / 后半1.2.py
- **功能**: 分段爬取（用于大规模数据）
- **用途**: 当数据量太大时，分批处理

### 3. ATCC/CCM/NCIMB 序列补充

#### ATCC_CCM_NCIMB序列补充爬取_V3_优化版.py
- **功能**: 从 NCBI 补充 ATCC/CCM/NCIMB 菌株序列
- **特点**:
  - 严格物种名称验证
  - 文件大小质量控制（WGS ≥500KB, 16S: 1200-1800bp）
  - 同义词处理（避免错杀相关属）
  - 断点续传支持
  - 每 20 个菌株重启浏览器

#### ATCC_CCM_NCIMB序列补充爬取_V4_严谨版.py
- **功能**: 更严格的质量控制版本
- **改进**: 
  - 更完善的错误处理
  - 更详细的日志记录
  - 更严格的序列验证

## 🚀 使用方法

### DSMZ 数据爬取

```bash
# 1. 爬取菌株信息
python DSMZ/dsmz_crawler_v63.py

# 2. 爬取培养条件
python DSMZ/dsmz_v31_菌株培养条件爬取.py

# 3. 下载序列
python DSMZ/dsmz_seq_full.py
```

### JCM 数据爬取

```bash
# 完整爬取
python JCM/JCM数据库全部爬取.py

# 或分段爬取
python JCM/JCM数据库全部爬取1.1.py
python JCM/JCM数据库全部爬取-后半1.2.py
```

### ATCC/CCM/NCIMB 序列补充

```bash
# 使用优化版（推荐）
python ATCC_CCM_NCIMB/ATCC_CCM_NCIMB序列补充爬取_V3_优化版.py

# 或使用严谨版
python ATCC_CCM_NCIMB/ATCC_CCM_NCIMB序列补充爬取_V4_严谨版.py
```

## ⚙️ 配置说明

### 通用配置

所有爬虫脚本都需要配置：

1. **ChromeDriver 路径**
   ```python
   CHROMEDRIVER_PATH = "path/to/chromedriver.exe"
   ```

2. **输出目录**
   ```python
   OUTPUT_DIR = "path/to/output"
   ```

3. **测试模式**
   ```python
   TEST_MODE = True   # 测试模式（少量数据）
   TEST_LIMIT = 20    # 测试数量
   ```

### ATCC/CCM/NCIMB 特殊配置

```python
# 质量控制阈值
MIN_WGS_SIZE_KB = 500   # WGS 最小文件大小
MIN_16S_LEN = 1200      # 16S 最小长度
MAX_16S_LEN = 1800      # 16S 最大长度

# 浏览器重启间隔
RESTART_INTERVAL = 20   # 每 20 个菌株重启
```

## 📊 输出数据

### CSV 文件格式

#### DSMZ 数据库
```csv
页码,菌株名称,DSM编号,WGS_ID,16S_ID,培养温度,培养时间,...
```

#### JCM 数据库
```csv
页码,菌株名称,JCM编号,WGS_ID,16S_ID,培养条件,...
```

#### ATCC/CCM/NCIMB 补充
```csv
原页码,菌株名称,DSM编号,提取的编号,WGS_ID,WGS_状态,WGS_文件,16S_ID,16S_状态,16S_文件
```

### 序列文件命名

```
{保藏编号}_{菌株名称}_{序列类型}_{登录号}.fasta

示例:
DSM_Bacillus_subtilis_WGS_GCF_000009045.1.fasta
ATCC_Escherichia_coli_16S_NR_024570.fasta
```

## 🔍 质量控制

### 序列质量标准

1. **WGS（全基因组）**
   - 文件大小 ≥ 500KB
   - 物种名称严格匹配
   - 优先选择 Complete Genome

2. **16S rRNA**
   - 序列长度 1200-1800 bp
   - 物种名称验证
   - 优先选择较长序列

### 物种名称验证

```python
# 严格校验：目标属名必须出现在结果中
validate_organism_match(target_genus, result_organism)

# 同义词处理
synonyms = {
    "bacillus": ["metabacillus", "paenibacillus"],
    "clostridium": ["clostridioides", "paraclostridium"],
    ...
}
```

## 🐛 常见问题

### Q1: 浏览器崩溃
**A:** 
- 启用定期重启：`RESTART_INTERVAL = 20`
- 使用无头模式：`--headless`
- 减少并发数

### Q2: 下载的序列物种不对
**A:** 
- 使用 V3_优化版或 V4_严谨版
- 这些版本有严格的物种名称验证
- 会自动删除不匹配的序列

### Q3: 断点续传不工作
**A:** 
- 确保 CSV 文件存在且格式正确
- 检查 `processed_strains` 集合是否正确读取
- 查看日志中的 "已完成" 数量

### Q4: 内存占用过高
**A:** 
- 定期重启浏览器
- 清理临时文件
- 分批处理数据

## 📝 最佳实践

1. **先测试后运行**
   ```python
   TEST_MODE = True
   TEST_LIMIT = 10
   ```

2. **启用断点续传**
   - 保留 CSV 结果文件
   - 脚本会自动跳过已处理的菌株

3. **监控运行状态**
   - 查看控制台输出
   - 定期检查输出文件
   - 注意错误信息

4. **数据备份**
   - 定期备份 CSV 文件
   - 备份已下载的序列
   - 保存运行日志

## 🔄 数据更新流程

1. **定期更新数据库**
   ```bash
   # 每月运行一次
   python DSMZ/dsmz_crawler_v63.py
   python JCM/JCM数据库全部爬取.py
   ```

2. **补充缺失序列**
   ```bash
   # 针对新增菌株
   python ATCC_CCM_NCIMB/ATCC_CCM_NCIMB序列补充爬取_V3_优化版.py
   ```

3. **验证数据质量**
   ```bash
   # 使用工具脚本检查
   python ../6_Tools/sequence_counter.py
   python ../6_Tools/strain_statistics.py
   ```

## 📞 技术支持

如遇问题，请：
1. 查看脚本内的注释说明
2. 检查配置是否正确
3. 查看运行日志
4. 参考 `../README.md` 主文档
