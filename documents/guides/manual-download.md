# SenseVoice 模型手动下载指南

## 方案：大文件手动下，小文件脚本下

### 第 1 步：手动下载最大的文件

**model.pt** (~900MB) - 模型权重文件

**下载链接（选一个）：**

1. **ModelScope 直链（推荐，支持迅雷/IDM）：**
   ```
   https://www.modelscope.cn/models/iic/SenseVoiceSmall/resolve/master/model.pt
   ```

2. **ModelScope 备用（浏览器下载）：**
   - 访问: https://modelscope.cn/models/iic/SenseVoiceSmall/files
   - 找到 `model.pt` → 点击下载

3. **Git LFS 直链：**
   ```
   https://www.modelscope.cn/api/v1/models/iic/SenseVoiceSmall/repo?Revision=master&FilePath=model.pt
   ```

**下载到：** `D:\models\funasr\SenseVoiceSmall\model.pt`

---

### 第 2 步：脚本下载其他小文件

运行 `scripts/download_sensevoice_small_files.py`，会下载：
- config.yaml (~5KB) - 配置文件
- configuration.json (~1KB)
- chn_jpn_yue_eng_ko_spectok.bpe.model (~360KB) - 分词模型
- tokens.json (~360KB)
- am.mvn (~100B) - 归一化参数
- README.md

**总大小**: ~1MB (很快)

---

### 第 3 步：验证

目录结构应该是：
```
D:\models\funasr\
└── SenseVoiceSmall\
    ├── model.pt              <-- 900MB，手动下载
    ├── config.yaml           <-- 脚本下载
    ├── configuration.json
    ├── chn_jpn_yue_eng_ko_spectok.bpe.model
    ├── tokens.json
    ├── am.mvn
    └── README.md
```

---

### 其他模型也一样

**fsmn-vad** 最大文件：
- `model.pb` (~5MB) 
- 直链: https://www.modelscope.cn/models/iic/speech_fsmn_vad_zh-cn-16k-common-pytorch/resolve/master/model.pb

**ct-punc** 最大文件：
- `model.pt` (~40MB)
- 直链: https://www.modelscope.cn/models/iic/punc_ct-transformer_zh-cn-common-vocab272727-pytorch/resolve/master/model.pt

**paraformer-zh** 最大文件：
- `model.pt` (~1.2GB)
- 直链: https://www.modelscope.cn/models/iic/speech_seaco_paraformer_large_asr_nat-zh-cn-16k-common-vocab8404-pytorch/resolve/master/model.pt

---

## 使用下载工具

### IDM (Internet Download Manager)
- 复制直链 → IDM 自动捕获 → 支持断点续传

### 迅雷
- 新建任务 → 粘贴直链 → 选择保存位置

### aria2c (命令行)
```powershell
aria2c -x 16 -s 16 -k 1M `
  -d "D:\models\funasr\SenseVoiceSmall" `
  -o "model.pt" `
  "https://www.modelscope.cn/models/iic/SenseVoiceSmall/resolve/master/model.pt"
```

参数说明：
- `-x 16`: 16 线程
- `-s 16`: 从 16 个源下载
- `-k 1M`: 断点续传，每 1MB 保存一次
- `-d`: 保存目录
- `-o`: 文件名
