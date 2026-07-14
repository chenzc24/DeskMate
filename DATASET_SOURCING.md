# DeskMate Dataset Sourcing Decision

> 调研日期：2026-07-14
> 对应计划：`BASELINE_PLAN.md` v0.1
> 最终检测类别：`person / phone / bottle / cup / book / laptop`
> 具体下载步骤：见 `DATASET_DOWNLOAD_PLAN.md`

## 1. 最终结论

DeskMate 使用 COCO 预训练的 `yolo26n.pt` 进行迁移学习微调。`person`、`phone`、`bottle`、`cup`、`book` 和 `laptop` 都已有 COCO 预训练基础，因此无需下载完整 COCO、Open Images 或其他大规模通用数据集。

最终数据采用以下原则：

1. **720 张 DeskMate 自采图片是主体**，用于目标域适配和全部 Validation/Test；
2. **40 张 FPI-Det** 补充困难 phone 场景，但必须补齐六类标注；
3. **20 张 iCubWorld** 补充机器人视角的 bottle/cup；
4. **最多 20 张 Open Images** 仅针对第一轮真实视频中已经确认的失败场景；
5. 公开数据只进入 Train，绝不进入最终 Validation、Test 或 5 段系统回放视频。

如果预训练模型在 `laptop` 上表现正常，不专门下载大规模 laptop 数据；自采数据中仍须完整标注 laptop，因为六类微调会使用新的输出类别表。

## 2. 数据源取舍

| 优先级 | 数据源 | 与 DeskMate 的匹配 | 标注和规模 | 许可 | 最终决策 |
|---|---|---|---|---|---|
| A | DeskMate 自采视频帧 | 摄像头、桌面、人物、距离和光照完全匹配 | 自行标注六类 | 组内授权；涉及成员时记录同意 | 720 张，必须使用 |
| B+ | FPI-Det | phone 小目标、遮挡、手持和人物姿态丰富 | 项目称 22,879 图、10,255 个 phone 框；仓库检测配置为 `phone/face` | 仓库标为 MIT | 下载后只选 40 张困难样本并完整复核 |
| B | Open Images V7 | 六类均有对应类别，场景多样 | 约 1.9M 带框图片、16M boxes、600 类；支持按类下载 | 标注 CC BY 4.0；图片列为 CC BY 2.0，仍需逐图核验 | 第一轮失败后最多选 20 张 |
| B | iCubWorld Transformations | 机器人低清相机视角与桌面/地面物体 | Pascal VOC XML；小型序列包约 7.4 MB | Zenodo 记录为 CC BY 4.0 | 只选 20 张 bottle/cup 非相邻帧 |
| 初始化 | COCO 2017 | 六类全部覆盖 | 80 个检测类 | 图片许可随原图 | 已包含在 `yolo26n.pt`，不再下载整库 |
| 不采用 | Objectron | book/bottle/cup/laptop 多视角，但偏单物体和 3D 任务 | 15K 视频、4M 帧、3D box；原始数据约 1.9 TB | C-UDA-1.0 | Baseline 转换成本过高 |
| 不优先 | 随机 Kaggle/Roboflow 项目 | 可能含目标类 | 来源、重复、漏标和许可不统一 | 逐项目不同 | 本轮不使用 |

## 3. 已核验的公开数据

### 3.1 iCubWorld 小型序列

对官方小型场景包进行了解压和统计：

- 271 个 XML，其中 266 个能与图片匹配；
- 匹配画面中有 165 个 `sodabottle2` 框和 238 个 `mug1` 框；
- 画面为 640×480，包含遮挡、边缘目标和背景变化；
- 连续帧高度相关，不能随机抽取大量相邻帧；
- phone 是旧式功能机，不作为现代智能手机训练数据；
- 小型序列没有可直接用于本项目的 laptop 标注。

本项目只保留以下映射：

```yaml
sodabottle2: bottle
mug1: cup
```

不再使用 `pencilcase5`；也不把 `ringbinder` 自动映射为 `book`。

### 3.2 Open Images V7

允许的类别映射：

```yaml
Person: person
Mobile phone: phone
Bottle: bottle
Coffee cup: cup
Mug: cup
Book: book
Laptop: laptop
```

不要把 `Glass`、`Measuring cup` 或 `Corded phone` 自动并入当前类别。

对官方 Validation bounding-box CSV 的实测统计如下；这些数量只代表 Validation：

| Open Images 类别 | 图片数 | 框数 | 遮挡框 | 截断框 |
|---|---:|---:|---:|---:|
| Person | 6,772 | 15,895 | 7,899 | 3,759 |
| Mobile phone | 101 | 140 | 4 | 18 |
| Bottle | 198 | 485 | 207 | 127 |
| Coffee cup | 148 | 181 | 34 | 42 |
| Mug | 39 | 45 | 6 | 9 |
| Book | 90 | 672 | 113 | 115 |
| Laptop | 49 | 67 | 19 | 31 |

Open Images 并非对每张训练图的全部 600 类都完全标注。因此任何选中的图片都需要重新检查六个 DeskMate 类别，不能只转换下载到的单类框。

### 3.3 FPI-Det

FPI-Det 适合补手机较小、靠近脸部、被手遮挡和复杂人物姿态等失败情况。但其仓库检测配置只有：

```yaml
0: phone
1: face
```

如果直接把 `phone` 框并入六类数据，未标注的完整人物会被当成背景，可能损害 `person` 检测。最终选中的 40 张图必须：

1. 用 COCO 预训练模型生成 `person` 候选；
2. 人工修正 person 框；
3. 补齐所有可见的 phone、bottle、cup、book 和 laptop；
4. 删除只剩极小手机或无法判断是否为手机的图片。

FPI-Det 只增强 `phone` 检测，不创建单帧 `using_phone` 类别。`using_phone` 仍由追踪、手部关键点、空间关系和持续时间规则生成。

## 4. 最终 800 张组成

| 部分 | 数量 | split | 说明 |
|---|---:|---|---|
| DeskMate 本地 Train | 480 | Train | 按录制批次分组，覆盖六类和困难情况 |
| FPI-Det | 40 | Train | phone 困难样本，完整补标后使用 |
| iCubWorld | 20 | Train | bottle/cup 各约 10 张非相邻帧 |
| Open Images 或本地失败补采 | 20 | Train | 第一轮失败后决定；优先选择本地补采 |
| DeskMate 本地 Validation | 120 | Validation | 独立人物、光照或录制批次 |
| DeskMate 本地 Test | 120 | Test | 完全独立批次，训练期间不查看调参 |
| **总计** | **800** | Train 560 / Val 120 / Test 120 | 严格 70% / 15% / 15% |

Open Images 的 20 张是预算上限，不是强制配额。如果真实视频没有对应失败，使用 20 张本地困难样本替代。

## 5. 类别与场景覆盖门槛

图片可以同时包含多个类别。800 张数据至少达到：

| 类别 | 最少实例数 | 必须覆盖 |
|---|---:|---|
| `person` | 400 | 3 名组员、坐姿、离开画面、部分遮挡 |
| `phone` | 250 | 手持、桌面、口袋旁、正反面、部分遮挡 |
| `bottle` | 250 | 透明/不透明、不同标签、空瓶/装液、边缘目标 |
| `cup` | 120 | 有柄/无柄、不同颜色、被手或其他物体遮挡 |
| `book` | 120 | 打开/合上、薄本/厚书、不同封面 |
| `laptop` | 150 | 打开/合上、屏幕亮暗、局部遮挡、不同角度 |

同时满足：

- 至少 120 张不含搜索目标 bottle/cup；
- 至少 160 张包含遮挡、运动模糊或画面边缘目标；
- 至少 3 种照明和 4 个摄像头方向；
- 连续视频按录制片段去重并划分，不能跨 split。

## 6. 合并质量门

每张外部图片进入 Train 前必须通过：

1. 来源和许可可追溯；
2. 六个 DeskMate 类别中的所有可见实例均已标注；
3. 不把低于约 12 像素且不可可靠识别的物体作为正样本；
4. 类别边界符合项目规范；
5. 不与任何本地 Validation/Test 重复；
6. 相邻公开视频帧不重复进入训练集；
7. 在 `source_manifest.csv` 中记录来源、原始 ID、许可和转换状态。

## 7. 执行顺序

1. 下载 `yolo26n.pt` 和 iCubWorld 小型序列；
2. 通过 Google Drive 手动下载 FPI-Det，先放在候选区；
3. 录制两段真实 DeskMate 视频，运行原始模型基准；
4. 完成 720 张本地数据采集和按批次切分；
5. 从 FPI-Det 和 iCubWorld 各挑选固定数量并完整复核；
6. 只有出现明确失败时才下载 Open Images 图片；
7. 冻结 800 张 Dataset v0.1 清单和文件校验值。

## 8. 官方来源

- Ultralytics YOLO26（COCO 预训练）：https://docs.ultralytics.com/models/yolo26/
- COCO 2017 Detection：https://cocodataset.org/dataset/detection-2017.htm
- Open Images V7 说明与许可：https://storage.googleapis.com/openimages/web/factsfigures_v7.html
- Open Images V7 下载：https://storage.googleapis.com/openimages/web/download_v7.html
- iCubWorld：https://robotology.github.io/iCubWorld/
- iCubWorld Zenodo：https://zenodo.org/records/835510
- FPI-Det：https://github.com/KvCgRv/FPI-Det
- Objectron：https://github.com/google-research-datasets/Objectron
