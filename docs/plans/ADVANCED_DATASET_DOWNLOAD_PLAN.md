# DeskMate Advanced Dataset Download Plan

> 阶段：仅用于正式猫分类 Baseline 通过后的 DeskMate Advanced。
> 目标：生成 Dataset v0.1，共 800 张；Train 560 / Validation 120 / Test 120。
> 类别顺序：`person / phone / bottle / cup / book / laptop`。
> 原始数据和大文件不提交 Git，只提交清单、下载说明、许可和校验值。

## 1. 最终目录

```text
data/
├── external/
│   ├── icubworld/
│   │   ├── downloads/
│   │   └── extracted/
│   ├── fpi_det/
│   │   ├── downloads/
│   │   └── extracted/
│   └── openimages/
│       ├── metadata/
│       └── candidate_pool/
├── local/
│   ├── videos/
│   └── extracted_frames/
├── staging/
│   ├── images/
│   └── labels/
├── splits/
│   ├── train.txt
│   ├── val.txt
│   └── test.txt
└── manifests/
    ├── source_manifest.csv
    └── dataset_v0.1.sha256
```

## 2. 立即下载

在项目根目录执行：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\data\download_dataset_sources.ps1
```

脚本只下载约 30 MB 的可自动获取内容，不会下载大型数据集：

### 2.1 iCubWorld 小型序列

| 文件 | 大小 | SHA-256 |
|---|---:|---|
| `Sequences_images.tar.gz` | 7,361,868 bytes | `834543A8F8A40E0974520628F506A0B5C67485F17025696ED878FCE977749343` |
| `Sequences_annotations.tar.gz` | 45,794 bytes | `60F38FADDA2DF462FF05991A467A8DA324D6B2CF703CB8385976FA2F01E5C03D` |

下载后：

1. 解压图片和 Pascal VOC XML；
2. 只保留约 10 张 `sodabottle2 → bottle` 和 10 张 `mug1 → cup`；
3. 从 TABLE、FLOOR、SHELF 等不同场景选择；
4. 不选相邻帧，优先遮挡、边缘、尺度变化和背景变化；
5. 不使用旧式 `cellphone1`，也不使用 `pencilcase5`。

最终进入 Train：**20 张**。

### 2.2 Open Images 元数据

脚本只下载类别表和 Validation 框 CSV，不下载图片：

| 文件 | 大小约 | SHA-256 |
|---|---:|---|
| `oidv7-class-descriptions-boxable.csv` | 很小 | `1839E0E7E84130AE281F7F67413768601B031581C0C42E7FC17527B8E2A99AA9` |
| `validation-annotations-bbox.csv` | 25,105,048 bytes | `D8BBD59410AF14835D7733165A7BB8A3F0213981B22DD5077B0B9F7878991FF2` |

元数据用于确认候选图片 ID 和类别映射。实际图片等第一轮模型失败分析后再下载。

## 3. 手动下载 FPI-Det

官方入口：

- Google Drive：https://drive.google.com/file/d/1Heb2N4hRcJH2s9tLdpTzacSj0APbUDdD/view?usp=sharing
- Baidu Netdisk：https://pan.baidu.com/s/1_xjDuK9FvhguqoMwjAIlIA?pwd=Mofo
- 百度提取码：`Mofo`

Google Drive 页面可能要求登录，因此不放进自动脚本。下载步骤：

1. 将官方原始压缩包保存到 `data/external/fpi_det/downloads/`；
2. 不修改原始文件名；
3. 立即记录校验值：

```powershell
Get-FileHash -Algorithm SHA256 .\data\external\fpi_det\downloads\* |
  Format-Table Path, Hash -AutoSize
```

4. 解压到 `data/external/fpi_det/extracted/`；
5. 按以下四组各选 10 张：
   - phone 很小；
   - phone 被手或脸遮挡；
   - 侧面、暗光或模糊；
   - phone 靠近脸/手但姿态变化明显；
6. 用 COCO 预训练模型生成 `person` 候选，再人工补齐六类标注；
7. 只有完整复核后的 40 张才能进入 Train。

最终进入 Train：**40 张**。

仓库中的 `phone_train_yolo.rar` 约 3.25 MB，主要是训练代码副本，不是完整 FPI-Det 图片数据，不能把它当作数据集下载包。

## 4. 条件下载 Open Images 图片

第一次下载阶段不取 Open Images 图片。完成原始 `yolo26n.pt` 真实视频基准后，只有以下情形才触发下载：

- laptop 在合上、暗屏或边缘位置持续漏检；
- phone 小目标或遮挡失败，而 FPI-Det 仍未覆盖；
- book 与 laptop、cup 与 bottle 出现稳定混淆；
- 需要明确的困难负样本。

允许查询的类别：

```text
Person
Mobile phone
Bottle
Coffee cup
Mug
Book
Laptop
```

可使用 Open Images 官方页面推荐的 FiftyOne 子集下载方式，先下载不超过 60 张候选池：

```python
import fiftyone.zoo as foz

dataset = foz.load_zoo_dataset(
    "open-images-v7",
    split="validation",
    label_types=["detections"],
    classes=[
        "Person",
        "Mobile phone",
        "Bottle",
        "Coffee cup",
        "Mug",
        "Book",
        "Laptop",
    ],
    max_samples=60,
)
```

从候选池最终选择不超过 20 张，并将 `Coffee cup` 和 `Mug` 统一映射到 `cup`。每张图片都要重新检查六类标注和图片许可。

最终进入 Train：**0–20 张**。若不需要，则用相同数量的本地失败补采图片替代。

## 5. 不下载的内容

| 数据 | 原因 |
|---|---|
| 完整 COCO 2017 | 六类能力已通过 `yolo26n.pt` 迁移；整库约数十 GB，重复收益低 |
| 完整 Open Images | 规模过大且存在部分标注语义问题，只按失败类型取子集 |
| 完整 iCubWorld | 完整 640×480 分包超过 20 GB；小型序列已足够补机器人视角 |
| Objectron | 原始数据约 1.9 TB，主要是 3D 框，Advanced 转换成本过高 |
| 随机 Kaggle/Roboflow 合集 | 来源、许可、重复和漏标不可统一核验 |

## 6. 本地采集计划

本地采集不是“下载”，但它构成最终数据集的 90%。目标为 720 张：

| 本地部分 | 数量 | 规则 |
|---|---:|---|
| Train | 480 | 覆盖所有人物、光照、视角和困难情况 |
| Validation | 120 | 使用独立录制片段，不能与 Train 相邻 |
| Test | 120 | 完全独立批次，训练期间不用于选阈值 |

建议录制 12–16 段视频，每段 20–45 秒，覆盖：

- 3 名组员；
- 3 种照明；
- 4 个摄像头方向；
- phone 手持/桌面/遮挡；
- bottle/cup 多位置搜索；
- book 打开/合上；
- laptop 打开/合上、亮屏/暗屏；
- 没有 bottle/cup 的负样本；
- 小车转动造成的运动模糊。

抽帧后执行感知哈希或相似度去重，按“整段视频”分配 Train/Val/Test。

## 7. 最终 800 张冻结

```text
Train       560
  local     480
  FPI-Det    40
  iCubWorld  20
  OI/local   20

Validation  120  # 全部本地
Test        120  # 全部本地
----------------
Total       800
```

冻结前生成 `source_manifest.csv`，至少包含：

```text
final_image_id,split,source,source_id,recording_batch,license,
person_count,phone_count,bottle_count,cup_count,book_count,laptop_count,
annotation_reviewer,sha256
```

最终只把 manifest、split 清单、转换脚本、许可说明和校验文件提交 Git；图片与原始压缩包保持在 `data/` 并由 `.gitignore` 排除。
