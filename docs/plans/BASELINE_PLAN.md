# SWS3009A 正式 Baseline：五种猫识别与机器人集成计划

> 版本：v1.2（Official Cat Census Baseline，架构与模型选择加固）
> 计划日期：2026-07-14
> 评测日期：2026-07-17
> 报告截止：2026-07-17 23:59（Canvas）
> 计算资源：本地 NVIDIA RTX 4070；不租云算力
> 当前原则：Baseline 通过以前，Advanced DeskMate 功能全部暂停

---

## 1. 最终决策

正式 Baseline 是 **The Great Cat Census**，不是桌宠行为识别。Deep Learning
部分只完成一条最短、可重复、可在真实机器人视频上运行的链路：

```text
robot live video
    -> frame capture and reconnect
    -> operator-aligned multi-scale centre ROIs
    -> B-M01 YOLO26 five-breed classifier
    -> confidence margin + spatial/temporal consensus
    -> visible UI overlay + mandatory console print
    -> census record
```

机器人由团队 **远程控制**；Baseline 不需要自主导航，也不让 DL 代码发送电机命令。
操作员通过机器人摄像头寻找八张猫图，将目标置于中央 ROI，模型实时识别并在控制台
打印物种，最后把机器人开回起点。

Advanced 的 YOLO detection、多专家、语义融合、FSM 和自主动作均不进入 Baseline 关键路径。
这些工作保存在 [`ADVANCED_PLAN.md`](ADVANCED_PLAN.md)，只有本文件 Gate B4 通过后
才启动。

---

## 2. 正式要求与内部验收

### 2.1 正式要求

以下内容来自四份本地正式材料：

- [Assignment announcement](<../../References/The requirement/Assignment announcement.md>)
- [Baseline SOP](<../../References/The requirement/Baseline SOP.md>)
- [SWS3009A assignment](<../../References/The requirement/SWS3009A_Assg.md>)
- [Assignment answer book](<../../References/The requirement/SWS3009A_AssgAnsBk.md>)

| 项目 | 正式要求 |
| --- | --- |
| 类别 | Ragdoll、Singapura、Persian、Sphynx、Pallas cat，共五类 |
| 数据 | 网络收集，尽量均衡，总量建议超过 1,000 张 |
| 切分 | 85% Training / 15% Validation |
| 方法 | CNN 或 YOLO；使用预训练网络做 transfer learning，并说明理由 |
| 实时链路 | 机器人机载摄像头直播，训练模型运行在直播画面上 |
| 可见输出 | 预测 species 必须显示在 console 或 UI；评委看不到则该猫不得分 |
| 任务 | 遥控寻找并识别八张猫图，之后返回起点 |
| 时限 | 每组 15 分钟；超时立即终止 |
| 导航 | 远程控制；不要求 autonomous control；操作者看不到机器人和场地 |
| 到场 | 全体成员必须出席，迟到或错过时段无补测 |
| 计分 | 猫 40 分、速度最高 20 分、创意 10 分，总分 70 |
| 报告 | 填写每类图像数、架构与理由、训练/验证准确率、过拟合/欠拟合分析；转 PDF 上传 Canvas |

团队编号和具体 reporting time 尚未写入本项目。负责人必须在周四冻结清单时从
Baseline SOP 填入，所有成员按 reporting time 至少提前 15 分钟到达指定地点。

### 2.2 自设工程验收线

以下不是课程硬性分数线，而是为了降低现场失败概率设置的 release gate：

| 指标 | Release gate |
| --- | ---: |
| 五类目标猫图像 | Release floor `>= 1,200`；目标 `2,000`；时间允许冲刺 `3,000` |
| 每类图像数 | Floor `>= 220`；目标 `>= 400`；最大/最小类数量比 `<= 1.15` |
| `not_target` 负样本 | `300–600` 张，按场景/来源分组，不计入五类猫报告数量 |
| 五类 target-only 合并 15% validation accuracy | `>= 90%` |
| Validation macro F1 | `>= 0.88` |
| Validation 每类 recall | `>= 0.80` |
| Calibration | 校准后 ECE 不高于校准前，目标 `<= 0.10`；阈值只用 calibration 数据 |
| 未参与调参的最终打印图测试 | 至少 `46/50` 正确，且每类至少 `9/10` |
| 最终负场景拒识 | 至少 `45/50` 正确拒绝，不向 console 打印猫品种 |
| 端到端预览速度 | `>= 8 FPS` |
| 单帧推理 P95（RTX 4070） | `<= 100 ms`，不含网络传输 |
| 完整机器人联排 | 连续 3 次：8/8 有可见输出、无崩溃、15 分钟内返回 |

如模型指标和机器人联排冲突，优先修复端到端联排。高离线准确率不能替代真实摄像头
可用性。

---

## 3. 范围冻结

### 3.1 Baseline P0 优先级：周五评测前必须完成

本节的 `P0` 表示“必须交付”的优先级；第 9 节的 `Phase 0–4` 表示执行阶段，两者不要
混用。任何 Phase 内都先完成 Baseline P0 项，再处理低成本加分。

1. 五类猫数据集、来源清单、去重、85/15 固定切分；
2. `yolo26s-cls.pt` 六输出迁移学习：五种目标猫加内部 `not_target` 拒识类；
3. 机器人直播读取、断线提示和重连；
4. 多尺度中央 ROI、实时 top-3、置信度差值、时空共识和大字体物种显示；
5. 每次确认都向 console 打印物种、置信度和时间戳；
6. 八个目标的 census counter，避免漏记和重复记录；
7. 真实机器人/同款摄像头的打印图片测试；
8. 三次完整 15 分钟联排与离线启动检查；
9. Answer Book 所需图像数、架构说明、曲线和结果表。

### 3.2 P0 完成后才允许的低成本加分

- 清晰的 mission-control UI：`FOUND 3/8`、类别、置信度、FPS；
- 确认识别时播放提示音或显示简短动画；
- 保存带时间戳的八条 census 记录供评委查看；
- 一键导出本次 run 的 CSV。

总投入上限为 2 小时；任何影响稳定性的效果立即移除。

### 3.3 Baseline 明确不做

- YOLO object detection 和 bounding-box 标注；Baseline 只使用 YOLO classify；
- 多模型同帧推理；
- 眼部、手部、姿态或工作行为识别；
- LLM/VLM、语义规划或自然语言交互；
- 自主导航、自动追踪、FSM 驱动底盘；
- ROS、微服务、云端推理或租用 GPU；
- 为 Advanced 采集桌面物体数据；
- 在 Gate B4 之前重构为复杂通用框架。

---

## 4. 模型选择

### 4.1 主模型 `B-M01`

| 字段 | 决策 |
| --- | --- |
| 架构 | Ultralytics YOLO26s Classify |
| 初始化 | ImageNet 预训练 `yolo26s-cls.pt` |
| 任务 | 六输出分类：五个目标 breed + 内部 `not_target` 拒识类 |
| 输入 | RGB `224 x 224` |
| 输出 | Ultralytics `Results.probs`：整张 ROI 的类别概率，不产生检测框 |
| 参数量 | 官方表约 6.7M |
| 官方来源 | [Ultralytics image classification documentation](https://docs.ultralytics.com/tasks/classify/) |
| 部署 | Ultralytics + PyTorch CUDA；CPU 仅作应急兼容测试 |

选择 YOLO26 **classification** 而不是 YOLO detection：现场目标是由操作员遥控寻找并
对准的单张猫图片，输出要求是整图 breed classification，不需要定位多个实例，也不
需要 bounding-box 标注。`yolo26s-cls.pt` 与 Advanced 的 `yolo26n.pt` detection 共用
Ultralytics/PyTorch 环境、模型加载、train/val/predict/export 命令和离线打包流程，
但两者的 head、输出 schema、标注格式和任务权重不互相复用。

保存模型时必须同时冻结：

- Ultralytics、PyTorch、Torchvision 和 CUDA 版本；
- `yolo26s-cls.pt` 来源、下载文件 SHA-256 和许可；
- 五类 `class_to_idx` 的确切顺序；
- 训练配置、随机种子、best epoch 和 checkpoint SHA-256；
- 推理 resize、crop、normalization 和阈值。

内部 label 与评委可见名称固定映射如下。前五类进入正式报告与 census；`not_target`
只用于拒绝导航背景、其他猫、模糊帧和不完整目标，绝不作为猫 species 打印：

| Internal label | Display label |
| --- | --- |
| `ragdoll` | `Ragdoll` |
| `singapura` | `Singapura` |
| `persian` | `Persian` |
| `sphynx` | `Sphynx` |
| `pallas` | `Pallas cat` |
| `not_target` | `NO TARGET`（不登记、不打印 species） |

### 4.2 重复训练、后备与可选共识

1. 先用一个 `B-M01` seed 打通真实直播；只有 Gate B2 主链路可用后，才补足 3 个固定
   seed。全部使用同一冻结 split，按 `val_select` macro F1 选择候选。
2. 主链路可用后允许训练 `yolo26m-cls.pt` challenger；只在 `val_select` 与机器人
   calibration 同时改善、且 RTX 4070 实测延迟仍过 Gate 时替换 `s`，不能依据 ImageNet
   指标直接换型。
3. 现场第一回退是上一版通过 Gate 的 `B-M01` checkpoint，不是重新训练。
4. `B-M01F` 使用 Torchvision EfficientNet-B0
   (`EfficientNet_B0_Weights.IMAGENET1K_V1`)。只有主模型已接入真实直播，或主模型在
   数据清洗后仍未达到 Gate B2 时，才训练这个独立后备。
5. 默认现场只运行 `B-M01`。只有 `B-M01 + B-M01F` 在机器人 calibration 上比单模型
   多答对至少 2 个 base image、每类 recall 均不下降且确认延迟仍合格，才允许把双模型用于
   **确认阶段**；实时预览始终只跑 `B-M01`。

报告必须说明最终实际启用的是单模型还是有证据支持的确认阶段共识，不能把未启用的
后备描述成正式架构。

---

## 5. 数据计划

### 5.1 数量和目录

Release floor 为 1,200 张清洗、去重后的独立图片；正式目标为每类约 400 张、总计
2,000 张；只有在不延误机器人集成和人工复核时才冲刺每类约 600 张、总计 3,000 张。
augmentation、同图不同压缩版本和相邻机器人视频帧不计作新的独立图片。

此外收集 300–600 张 `not_target`：真实机器人背景、墙面/地面、手和机器人结构、其他
猫品种、严重模糊/过曝/欠曝、局部海报及无猫打印纸。负样本同样按来源和录制 session
分组切分，不能让相邻帧跨 split。

```text
data/cat_census/
├── source_manifest.csv
├── split_manifest.csv
├── train/
│   ├── ragdoll/
│   ├── singapura/
│   ├── persian/
│   ├── sphynx/
│   ├── pallas/
│   └── not_target/
├── val_select/
│   └── <same six internal outputs>/
├── val_cal/
│   └── <same six internal outputs>/
└── integration_test/
    ├── calibration/
    └── final/
```

`data/`、原图、打印扫描、视频、checkpoint 和训练输出均不提交 Git。Git 只保存脚本、
配置、去除私人路径的 manifest 模板和聚合指标。

### 5.2 数据来源决策与覆盖矩阵

数据策略冻结为 **现成权威数据集优先、可追溯 API 补齐、Selenium 只填缺口**。目前没有
发现一个同时覆盖五类、标签可信、逐图来源与许可清楚的单一数据集，因此不把随机的
Kaggle/Hugging Face 社区合集直接当作主数据源。社区数据集只有在 dataset card 能证明
类别定义、原始来源、许可和去重状态后，才能作为候选二级来源。

| 类别 | P0 主来源 | 二级来源 | 预期缺口处理 |
| --- | --- | --- | --- |
| `persian` | [Oxford-IIIT Pet](https://www.robots.ox.ac.uk/~vgg/data/pets/) | [Wikimedia Commons API](https://www.mediawiki.org/wiki/API:Categorymembers) | 去重后不足 400 才定向检索 |
| `ragdoll` | [Oxford-IIIT Pet](https://www.robots.ox.ac.uk/~vgg/data/pets/) | Wikimedia Commons API | 去重后不足 400 才定向检索 |
| `sphynx` | [Oxford-IIIT Pet](https://www.robots.ox.ac.uk/~vgg/data/pets/) | Wikimedia Commons API | 去重后不足 400 才定向检索 |
| `singapura` | Wikimedia Commons 的 Singapura 类别及子类别 | 经逐图审计的社区来源 | 预计需要定向检索，并做双人标签复核 |
| `pallas` | [iNaturalist `Otocolobus manul`](https://www.inaturalist.org/taxa/42029/taxonomy_details) 的 research-grade、许可合格照片 | Wikimedia Commons 的 `Otocolobus manul` 类别 | 仍不足 400 时才定向检索 |

Oxford-IIIT Pet 官方页面说明该数据集有 37 类、每类约 200 张，并明确包含 Persian、
Ragdoll 和 Sphynx；它不能覆盖 Singapura 或 Pallas。iNaturalist 适合按物种检索 Pallas，
但不把其分类系统用于家猫品种标签。Wikimedia/iNaturalist 的数量和许可可能变化，计划中
不预先承诺可用张数；只有实际下载、许可筛选、人工审查和去重后的 `accepted_unique`
才计入 1,200/2,000/3,000 gate。

每张候选图进入 staging 时至少记录：

- `image_id`、canonical `label`、`source_kind`、`source_dataset`；
- `source_page_url`、`original_url`、作者、许可名称与许可 URL、下载时间；
- `source_group_id`、`exact_sha256`、`perceptual_hash`、尺寸；
- `review_status`、复核人、`duplicate_cluster_id` 和最终 `split`。

缺少来源页、原图 URL 或使用状态不清的图片可以暂存在隔离区，但不得进入冻结数据集。

### 5.3 Phase 0 来源审计与 Selenium go/no-go

Phase 0 不做无边界的批量 Google 图片爬取，只完成来源冻结和小规模下载 pilot：每个
source/class 组合抽取 10–20 张，验证标签、原图解析、许可元数据、失败重试和 manifest。
Phase 1 先批量获取通过 pilot 的 Oxford、Wikimedia 和 iNaturalist 候选，然后按以下顺序
决定是否启用 Selenium：

1. 删除损坏、错误类别和许可不合格项；
2. 做 SHA-256 精确去重和感知哈希近重复聚类；
3. 按类生成 `accepted_unique` 覆盖报告；
4. 某类 `< 400` 时，只为该类抓取 `400 - accepted_unique + 25%` 的候选缓冲；
5. 新抓取内容进入 `staging/scraped/<class>/`，再次经过同一许可、复核和去重流程，不能
   直接写入 `train/` 或 `validation/`；
6. 若整体工期受阻，先保证每类 `>= 220` 且总数 `>= 1,200` 的 release floor，再继续补齐
   400/类，不能用重复图虚增数量。

用户准备的 [Selenium 教程](https://medium.com/@nithishreddy0627/a-beginners-guide-to-image-scraping-with-python-and-selenium-38ec419be5ff)
保留为 gap-fill 参考，但不直接复制其中的 Google CSS selector、固定 ChromeDriver 路径或
只保存 `img src` 的做法。selector 会变化，搜索缩略图也不等于可授权的原图；爬取前须
检查目标站点条款，并把搜索结果当作“发现入口”，继续记录真实来源页面和许可。当前
[Selenium Python 文档](https://www.selenium.dev/selenium/docs/api/py/) 支持由 Selenium
Manager 处理常见 driver 配置；安装后先验证最小 `webdriver.Chrome()`，仅在自动管理失败
时才使用手工 driver 路径。Phase 0 文档修订本身不安装包、不启动浏览器，也不下载图片。

### 5.4 收集和清洗

1. 五个类别分别检索，优先收集不同个体、姿态、年龄、背景和光照；
2. 每张图记录类别、来源 URL、下载日期和许可/使用说明；
3. 删除非猫、类别不确定、严重水印、极低分辨率和相同图片；
4. 用文件 SHA-256 做精确去重，再用感知哈希检查裁剪、压缩和镜像近重复；
5. 由第二名成员复核 Singapura/Pallas/Persian 等容易混淆的样本；
6. 课程提供的五张 example 只用于 smoke test，不进入 train/validation；
7. 冻结数据后才生成 split，不手工把难图移出 validation。

### 5.5 85/15 切分与泄漏控制

- 固定随机种子 `20260714`；
- 五类目标猫严格保持 85% train / 15% validation；内部把 validation 固定拆为
  `10% val_select + 5% val_cal`，二者合计仍为作业要求的 15%；
- `val_select` 只选 epoch/seed/architecture；`val_cal` 只拟合 temperature 和候选阈值；
- 同一来源页面、同一个体或近重复簇必须整体进入同一 split；
- `not_target` 也按来源/session 分组为 85/10/5，不与目标猫数量混报；
- validation 不参与 augmentation 导出；最终报告同时给出合并 15% 的未增强指标，并
  清楚说明 select/cal 两部分用途；
- `integration_test` 是额外工程测试集，不计入作业 85/15 指标。

### 5.6 打印图与机器人域测试

准备两个互斥的机器人域集合：

- `robot_calibration`：每类 5 张目标图，共 25 个 base image，另加至少 25 个
  `not_target` 场景；用于 ROI、画质门、全局/每类阈值的域检查，不报告为 final test；
- `robot_final`：每类 10 张目标图，共 50 个从未用于选择或调参的 base image，另加
  50 个独立负场景；模型和阈值冻结后只运行一次。

所有目标图均使用与现场相近的尺寸打印。每张至少录制：

- 正对、轻微左右倾斜；
- 明亮和偏暗两种条件；
- 近、中两个距离；
- 机器人真实视频编码和网络传输后的画面。

所有派生拍摄帧按原始 base image 或负场景 session 分组。不得因为每张海报录制了多个
角度或多帧，就把它们算成独立测试图片；最终打印图准确率以 50 个 target base image
为统计单位，负场景拒识率以 50 个独立 scene 为单位。

如果打印图表现明显低于网络原图，先增加与打印/屏摄相关的轻度 augmentation，不能把
integration-test 图片直接塞回训练集后再报告同一测试结果。

---

## 6. 训练方案

### 6.1 可复现配置初值

```yaml
task: classify
seed: 20260714
model: yolo26s-cls.pt
data: data/cat_census
imgsz: 224
epochs: 30
batch: 64
optimizer: AdamW
lr0: 0.001
weight_decay: 0.0001
cos_lr: true
patience: 6
amp: true
deterministic: true
workers: 8
selection_metric: val_select_target_macro_f1
```

Ultralytics 原生记录 top-1/top-5；本项目另用固定 validation prediction 计算 macro F1、
per-class recall 和 confusion matrix。Batch 如显存或 DataLoader 不稳定可降至 32；其他
超参数不因单次结果随意改变。

### 6.2 Augmentation

训练集使用适度的：

- random resized crop；
- horizontal flip；
- `±10°` rotation 和轻微 perspective；
- brightness/contrast/color jitter；
- 轻度 blur、JPEG compression 和噪声；
- 小概率遮挡。

避免过强裁剪、垂直翻转和严重颜色变化，以免抹掉品种特征。Ultralytics classify 默认
crop-based transform 可能裁掉极端宽高比图片中的关键信息，因此数据审查必须检查变换
后的训练预览；必要时使用保持宽高比的 resize/pad 自定义 transform。Validation 使用
冻结的确定性 transform，不做随机增强。

### 6.3 概率校准与阈值

模型、seed 和 epoch 冻结后，使用 `val_cal` logits 拟合单一 temperature；不得返回训练
集或 `val_select` 重选架构。记录校准前后 NLL、ECE、target macro F1 和
`not_target` recall。然后只用 `robot_calibration` 检查域偏移并冻结：

- 每类最低 calibrated confidence；
- top-1/top-2 margin；
- blur、亮度、过曝、frame age 和 ROI coverage 门槛；
- 三尺度概率权重和时间 EMA 系数。

如果 calibration 样本不足以支持稳定的 per-class threshold，就使用一个全局阈值并在
报告中记录限制，不能为追求 50 张 final test 成绩反复手调。`robot_final` 在所有配置
冻结后只运行一次。

### 6.4 每次 run 必须产出

- train/validation loss 与 accuracy 曲线；
- validation macro F1、每类 precision/recall/F1；
- confusion matrix；
- target-only 指标、`not_target` recall/false-target rate、校准前后 NLL/ECE；
- best 和 last checkpoint；
- 实际训练时长、峰值显存和 best epoch；
- 配置、数据 manifest hash、代码 commit 和 checkpoint hash；
- 对 overfitting/underfitting 的两三句话事实判断。

过拟合判断：train accuracy 继续上升而 validation loss 上升或 validation accuracy/F1
持续下降。欠拟合判断：train 和 validation 指标都低且同时停滞。Answer Book 只写实际
曲线支持的结论，不预先声称“没有过拟合”。

---

## 7. 实时推理与 UI

### 7.1 可复用生命周期与任务专属输出

Baseline 与 Advanced 共享 runner 生命周期和 `FramePacket`，不强迫 classification 与
detection 共用同一个业务输出 schema：

```python
OutputT = TypeVar("OutputT")

@dataclass(frozen=True)
class FramePacket:
    frame_id: int
    captured_at_ns: int
    image_bgr: "np.ndarray"
    source: str

class ModelRunner(Protocol, Generic[OutputT]):
    def load(self) -> None: ...
    def warmup(self) -> None: ...
    def infer(self, frame: FramePacket, roi: "ROI") -> OutputT: ...
    def health(self) -> "ModelHealth": ...
    def close(self) -> None: ...

@dataclass(frozen=True)
class ClassificationObservation:
    task: str                 # "cat_breed"
    label: str                # five target labels or "not_target"
    probabilities: tuple[float, ...]
    calibrated_confidence: float
    margin: float
    topk: tuple[tuple[str, float], ...]
    model_id: str             # "B-M01"
    roi_scale: str            # "tight" / "medium" / "wide"
    frame_id: int
    captured_at_ns: int
    inferred_at_ns: int
    valid: bool
    reason: str | None
```

Baseline runner 将 Ultralytics `Results.probs` 转成 `ClassificationObservation`；UI、
日志和调度器不得直接读取 Torch tensor 或 Ultralytics result。Advanced runner 将
`Results.boxes` 转成 `ExpertObservation`。两者复用 `ModelRunner[OutputT]`、
`FramePacket`、设备选择、健康状态、telemetry 和 fixture tests，但不复用任务输出类型。

### 7.2 Worker 与队列

```text
Capture worker -> latest-frame ring buffer -> display
                         |                  -> Preview jobs (low priority)
                         +-----------------> Confirmation job (high priority)
GPU runner -> ClassificationObservation -> Aggregator -> UI/console/logger
```

- Capture worker 永不等待模型，只写入有界 latest-frame ring buffer；
- UI 始终显示最新 capture frame，而不是等待推理完成的旧画面；
- Preview 只取最新帧，队列最多 1 个 pending job，旧 preview 自动丢弃；
- Confirmation job 固定快照最近 5 个新鲜帧并获得 GPU 优先级，但不能阻塞 capture、遥控
  或 UI event loop；确认期间可以降低 preview 推理频率；
- Aggregator 和 logger 只接收标准 observation/event；所有队列有长度、超时和 dropped
  counter，禁止无限积压。

### 7.3 画质门、预览与确认

1. 视频连续预览，中央叠加 `wide / medium / tight` 三个引导框和“align cat image”提示；
2. 推理前计算 blur、平均亮度、过曝/欠曝比例、frame age 和 ROI coverage；画质不过门时
   UI 直接提示 `MOVE CLOSER / HOLD STILL / ADJUST LIGHT`，不让分类器猜；
3. 实时 preview 只处理 `medium` ROI，使用 calibrated probability，UI 显示 top-3、
   margin、quality、FPS、延迟和 stream 状态；preview 不写 species console 行；
4. 最近 7 个有效 preview 经时间 EMA 后为目标 breed 且超过 calibration 冻结的
   confidence/margin 才在 UI 大字显示 `STABLE: <species>`；若 top-1 为 `not_target`，显示
   `SEARCHING / NO TARGET`；
5. 操作员按 Space 后，对最近 5 个新鲜帧的三个 ROI scale 运行分类并先应用 temperature；
   每帧按 calibration 权重融合三个尺度概率，再对 5 个帧级概率做时间 EMA。尺度/帧是
   相关证据，日志不得称为 15 个独立投票；
6. 只有聚合 top-1 是目标 breed、至少 2/3 scale 在至少 4/5 帧同意该 breed、quality、
   calibrated confidence 和 margin 全过门时才确认；`not_target` 或共识不足时显示
   `UNCERTAIN — MOVE CLOSER/REALIGN`，不登记；
7. 确认成功后 UI 与 console 同时显示 species 并刷新 `FOUND n/8`；Backspace 可撤销最后
   一条误登记，但日志保留 correction 事件；
8. 视频过期、模型异常或 calibration 配置不匹配时显示 `UNKNOWN/NOT READY`，不登记。

console 最低输出格式：

```text
2026-07-17T09:42:18+08:00 CONFIRMED species=Ragdoll confidence=0.934 margin=0.281 found=3/8 model=B-M01
```

### 7.4 稳定性要求

- capture、GPU runner、aggregator 和 UI 解耦，所有队列均有界并记录 dropped jobs；
- 断流超过 500 ms 时清空 temporal window，禁止沿用旧预测；
- 自动重连并在 UI 显示重连次数；
- GPU 推理失败时显示明确错误，不静默输出旧类别；
- 所有权重、字体和配置提前离线缓存；
- release 前验证 Windows 路径、中文路径和摄像头 URL 配置。

---

## 8. 与 Robotics 组的接口

DL 组今天需要 Robotics 组确认：

| 项目 | 必须得到的答案 |
| --- | --- |
| 视频协议 | USB index、RTSP、HTTP/MJPEG 或自定义 socket |
| 分辨率/FPS | 实际稳定值，不是摄像头标称值 |
| 色彩格式 | BGR/RGB/YUV 及旋转方向 |
| 网络 | 机器人 IP、端口、断线恢复和评测现场网络方式 |
| 控制 UI | DL 窗口是否与遥控窗口同机，如何避免键位冲突 |
| 显示 | 评委从哪块屏幕看到 console/UI |
| 录制 | 是否允许本地保存开发回放，磁盘路径和开关 |
| 应急 | 视频失败时的重启顺序和负责人 |

职责边界：

```text
Robotics: remote driving + onboard stream + reconnect support
DL: stream consumer + classifier + visible prediction + census log
```

Baseline DL 进程不发送 `MOVE/STOP`。遥控安全、底盘电量和返回起点由 Robotics 组负责，
但完整 15 分钟联排由全组共同负责。

---

## 9. 五阶段冲刺排期

阶段按依赖关系推进，日期是最晚完成时间。后续阶段可以在不争用人员和 GPU 的前提下做
准备，但不得绕过前一 Gate 冻结关键输入。

### Phase 0 — Foundation 与来源审计（7 月 14 日）

- 冻结五类 reportable label、内部 `not_target`、显示名称、目录和 source manifest schema；
- 冻结第 5.2 节来源矩阵，对每个 source/class 做 10–20 张下载 pilot；
- 产出 pilot 的成功率、错误标签、许可缺失和近重复风险记录；
- 向 Robotics 组取得一段真实视频及直播连接方式；
- 完成 `FrameSource -> placeholder backend -> UI/console` 骨架；
- 从机器人流或录制视频保存至少一帧并在 UI/console 骨架中显示；
- 定义真实背景、其他猫、模糊/曝光异常和局部海报的 `not_target` 收集规则；
- 写明 Phase 1 的下载负责人、复核人、每类缺口与 Selenium go/no-go 规则。

**Gate B0：** 五类映射、manifest schema、来源 pilot、真实机器人帧和端到端假模型 UI
均有可复查证据。B0 不要求已经爬满数据，也不允许因为爬虫未完成而阻塞软件骨架。

### Phase 1 — Acquisition、清洗与冻结（7 月 15 日 12:00 前）

- 先获取 Oxford、Wikimedia 与 iNaturalist 候选，生成去重后覆盖报告；
- 仅对 `< 400` 的类别启动定向 Selenium gap-fill；
- 双人复核易混淆类，完成 exact/near-duplicate 聚类和 source-group 标记；
- 先达到每类 `>= 220`、总计 `>= 1,200` 的 release floor，再补到每类约 400、总计
  2,000；
- `not_target` 达到至少 300 张，并按来源/录制 session 分组；
- 冻结 85% train / 10% val_select / 5% val_cal 和 manifest；不得为了等待 3,000 张而
  推迟训练。

**Gate B1：** `>= 1,200` 张 clean unique target images、每类不低于 220、`>= 300`
张 grouped `not_target`、来源可追溯、85/10/5 split 冻结且训练可复现；正式目标仍为
2,000 张目标猫。

### Phase 2 — 训练与首次机器人集成（7 月 15 日 17:00 前）

- 先用一个 `yolo26s-cls` seed 完成训练并记录曲线、混淆矩阵、target-only 与拒识指标；
- 只针对有证据的主要混淆类补数据，不重开无边界收集；
- 最迟 17:00 把 best checkpoint 接到真实直播；先过直播 Gate，再补其他 seed、
  `yolo26m-cls` challenger 或 EfficientNet 后备；
- 晚上只使用 `robot_calibration` 做第一轮 target/negative 测试和 15 分钟机器人联排；
- 在 09:00–12:00 或 14:00–17:00 带实际问题参加 Makers@SoC consultation。

**Gate B2：** 单个 `yolo26s-cls` 已在真实直播中区分 target/not_target，UI 可见
species，只有 confirmation 向 console 打印；worker 队列无阻塞增长。

### Phase 3 — 域适配、可靠性与冻结（7 月 16 日 18:00 前）

- 修复打印图/直播域差，不再扩展功能；
- 用 `val_cal + robot_calibration` 拟合 temperature 并冻结 quality、confidence、margin、
  ROI 权重、EMA、checkpoint、class mapping 和依赖；
- 冻结后只运行一次 `robot_final`：50 张 target base image 和 50 个独立负场景；
- 完成至少三次计时全流程，记录 8/8、返回时间和故障；
- 模拟断流、GPU 不可用、窗口误关闭和重启；
- 准备 Answer Book 的图像数、架构一页、指标和曲线；
- 再次利用 consultation 解决尚未闭合的集成问题；
- 18:00 code/model freeze，之后只修复阻断性问题。

- **Gate B3：** final target `>= 46/50`、每类 `>= 9/10`；负场景拒识 `>= 45/50`；
  calibration 无泄漏，断流不产生旧预测。
- **Gate B4：** 连续三次完整联排通过，release 包可离线启动。

### Phase 4 — 评测与提交（7 月 17 日）

- 按 SOP reporting time 提前至少 15 分钟到场，全员签到；
- 开机后只运行 smoke test，不训练、不升级依赖；
- 检查电源、网络、机器人电量、视频、模型 hash、console 可见性；
- 完成 15 分钟评测；
- 使用冻结 run 的真实结果完成 Answer Book，补齐成员姓名，导出 PDF；
- 23:59 前由两人交叉检查后上传 Canvas。

---

## 10. 分工与每日同步

按四人设计，可按实际人数合并：

| 角色 | 主责 | 不得成为单点故障的内容 |
| --- | --- | --- |
| Data/Report | 收集、清洗、去重、manifest、Answer Book | 数据目录和类别映射 |
| Training/Eval | 训练配置、指标、checkpoint、混淆矩阵 | 训练与导出命令 |
| Inference/UI | 视频、ROI、推理、平滑、console/UI | 启动与重连流程 |
| Integration/Operator | Robotics 对接、打印测试、联排、现场操作 | IP/端口、遥控和恢复清单 |

每天 09:00、14:00、20:00 只同步四项：当前 Gate、阻塞项、最新可运行版本、下一次
集成时间。所有人至少独立启动一次 release。

---

## 11. 测试矩阵

| 层级 | 测试 | 通过条件 |
| --- | --- | --- |
| 数据 | 六输出、坏图、hash/感知去重、source/session 泄漏 | 五类目标完整，负样本分组，无跨 split 近重复簇 |
| 模型 | val_select、val_cal、混淆矩阵、NLL/ECE、重复 run | 选择与校准职责分离，类别顺序一致 |
| 画质 | blur、曝光、frame age、ROI coverage 边界 fixture | 不合格帧不进入分类/确认 |
| 推理 | 三尺度概率、temperature、EMA、margin、旧帧 | 相关证据不当独立票，旧帧不登记 |
| 并发 | capture/preview/confirm/UI 队列、timeout、drop | confirmation 不阻塞 capture/遥控/UI，无无限积压 |
| 视频 | 断流、重连、低 FPS、旋转画面 | UI 明确告警并恢复 |
| 域校准 | 25 张 target + 独立负场景 | 只冻结 quality/temperature/threshold，不形成 final 成绩 |
| 域终测 | 50 张未见 target + 50 负场景 | target `>= 46/50`、每类 `>= 9/10`、拒识 `>= 45/50` |
| UI/console | target、not_target、八条记录、撤销 | target 确认有 console 行；not_target 不打印 species |
| 全流程 | 遥控、寻找八图、返回起点 | 连续三次在 15 分钟内完成 |
| 离线 | 关闭网络后重启程序 | 不下载任何权重或依赖即可运行 |

每个失败都记录：时间、视频/图片 ID、真实类别、预测、置信度、是否稳定、网络状态和
处理结论。不要用“偶发”代替可复现证据。

---

## 12. 风险、降级和停止规则

| 风险 | 早期信号 | 当天动作 | 现场降级 |
| --- | --- | --- | --- |
| 网络图高、打印图低 | integration test 明显下降 | 加轻度打印/压缩增强，补独立打印样本 | 操作员更正对、更近地对准 ROI |
| Singapura/Pallas 混淆 | confusion matrix 集中 | 双人重审标签，补这两类多样样本 | 等待稳定窗口再确认 |
| 视频延迟 | 队列增长、画面滞后 | latest-frame 策略，降低显示分辨率 | 降推理频率但保持遥控流畅 |
| 断流 | frame age 超阈值 | 重连和清空概率/EMA 状态 | 显示 NOT READY，先恢复再登记 |
| GPU/环境故障 | CUDA 初始化失败 | 锁依赖并准备同机 CPU smoke test | 重启冻结环境，不现场安装包 |
| UI 被遮挡 | 遥控窗口抢占 | 固定窗口布局和键位 | console 保持独立可见 |
| 数据仍不足 | 周三上午 `< 1,200` | 全员停止 Advanced，集中收集清洗 | 保证均衡和质量，不伪造数量 |
| 多尺度结果冲突 | 不同 ROI 的 top-1 不一致 | 检查 framing 与训练 crop，冻结 margin/共识阈值 | 提示靠近或重新对准，不强行登记 |
| 背景被高置信度识别成猫 | 负场景 false-target rate 高 | 扩充 grouped `not_target`、校准 temperature/threshold | 只在确认模式输出，提示重新对准 |
| 置信度未校准 | 高 confidence 与实际准确率不符 | 比较 NLL/ECE，temperature scaling 后冻结阈值 | 不显示未经校准的“概率”含义 |
| 确认阻塞画面 | 按 Space 后视频/遥控卡顿 | confirmation priority job 与 capture/UI 解耦 | 关闭多模型共识，保留单模型概率融合 |

停止规则：

- 周三 17:00 后禁止无指标依据地更换主架构；
- 周四 12:00 后禁止新增功能；
- Gate B4 通过后禁止重新切分数据或重新训练，除非发现阻断性错误；
- 任何 Advanced 工作在 Baseline release 冻结前一律排队，不并行占用集成人员。

---

## 13. 报告材料清单

Answer Book 最终需要：

1. 全体成员姓名；
2. 五类各自的最终图像数量；
3. 一页架构说明：为何选择 YOLO26s classify 而不是 detection、如何使用 ImageNet
   预训练权重学习五个目标 breed 与内部 `not_target`、augmentation、loss 和优化器；
4. Training Accuracy 与 Validation Accuracy，注明 best epoch；
5. loss/accuracy 曲线和 confusion matrix 作为结论证据；
6. 是否 overfitting 及证据；
7. 是否 underfitting 及证据；
8. PDF 导出后检查名字、图表清晰度和页码；
9. 两人确认 Canvas 上传文件能够重新下载并打开。

五种猫的图像数按作业表格分别填写；`not_target` 数量与拒识指标在架构说明中另列，不能
冒充第六种猫。报告数字必须来自最终冻结 checkpoint 对应的 run，不得混用不同 split、
不同模型或反复查看 `robot_final` 后的调参结果。

---

## 14. 对 Advanced 的复用契约

Baseline 结束后允许直接复用：

- `FrameSource`、`FramePacket`、latest-frame queue 和重连逻辑；
- Ultralytics/PyTorch/CUDA 环境，以及 train/val/predict/export/benchmark 工具链；
- 通用 `ModelRunner[OutputT]` 生命周期、device selection、模型 manifest、health 和
  result-adapter fixture 模式；
- OpenCV overlay、console reporter、run logger 和 CSV 导出；
- 视频录制/回放、延迟统计和离线 smoke-test harness；
- Robotics 视频配置、窗口布局和现场恢复 runbook；
- release/checksum/offline packaging 流程。

Advanced 必须替换或扩展：

- 将 `B-M01` 的 `yolo26s-cls.pt` 和 `Results.probs` 替换为 M01 detection
  (`yolo26n.pt`, `Results.boxes`) 及其他专家；
- 保留 `ModelRunner`，将 `ClassificationObservation` 输出类型替换为
  `ExpertObservation`，再构建 `WorldState`；
- 新增 ROI router、Track ID、TTL、语义事件、FSM、安全门和 robot adapter；
- 使用 Advanced 专属桌面物体数据，不把猫数据混入目标检测训练。

明确不复用：猫分类 head、猫权重、五类 target label、`not_target`、85/15 猫数据
split、temperature、分类阈值和 `Results.probs` schema。复用发生在生命周期、框架、
部署和集成层，不宣称 classification model 可以直接变成 detection model。

抽取共享模块时必须先用 Baseline 冻结视频回放做回归：类别结果、FPS、P95 延迟和
console 记录不得无解释退化。这保证 Advanced 的复用是可验证的，不只是目录复用。

---

## 15. Baseline Definition of Done

只有全部满足才算正式 Baseline 完成：

- [ ] 五类 clean unique data 达到 2,000 张目标；若工期阻断，绝不低于 1,200 张 release
  floor，并记录未达目标的原因；85/15 split 和 manifest 已冻结；
- [ ] `not_target` 达到 300–600 张并按来源/session 分组，未混入五类猫报告数量；
- [ ] 数据无已知跨 split 近重复泄漏；
- [ ] `B-M01` `yolo26s-cls.pt` 的来源、版本、类顺序、配置和 SHA-256 已记录；
- [ ] 三个 `B-M01` 随机种子已按同一 split 比较，release checkpoint 有可追溯依据；
- [ ] val_select、val_cal、robot_calibration 与 robot_final 职责隔离；temperature、ECE、
  quality 和阈值均可追溯；
- [ ] 一次性 robot_final target/rejection 指标达到 release gate，或偏差有书面风险接受；
- [ ] 机器人真实直播能连续运行模型并显示 top-3、FPS 和 stream 状态；
- [ ] target 每次确认都在 UI 和 console 清楚显示 species；`not_target` 不打印 species；
- [ ] confirmation 不阻塞 capture、遥控或 UI，所有队列有界并报告 drop/timeout；
- [ ] 断流、旧帧和低置信度不会登记错误结果；
- [ ] 八条 census 记录和撤销操作可用；
- [ ] 全组连续三次在 15 分钟内识别 8/8 并返回起点；
- [ ] release 在断网状态可从头启动；
- [ ] 全员知道 reporting time、到场地点、现场职责和恢复流程；
- [ ] Answer Book 的数量、架构、准确率与拟合分析已由两人复核；
- [ ] 只有以上项目完成后，团队才进入 [`ADVANCED_PLAN.md`](ADVANCED_PLAN.md)。
