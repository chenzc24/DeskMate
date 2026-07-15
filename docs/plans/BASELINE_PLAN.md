# SWS3009A 正式 Baseline：五种猫识别与机器人集成计划

> 版本：v1.4（Official Cat Census Baseline，Detector-derived classifier views）
> 计划日期：2026-07-14
> 状态更新：2026-07-15
> 评测日期：2026-07-17
> 报告截止：2026-07-17 23:59（Canvas）
> 计算资源：本地 NVIDIA RTX 4070；不租云算力
> 当前原则：Baseline 通过以前，Advanced DeskMate 功能全部暂停

---

## 1. 最终决策

正式 Baseline 是 **The Great Cat Census**，不是桌宠行为识别。Deep Learning
部分只完成一条最短、可重复、可在真实机器人视频上运行的链路：

```text
human-accepted base images
    -> grouped 85/10/5 split
    -> frozen B-D01 automatic cat crops (derived views, no new labels/counts)
    -> base-balanced original/crop training views
    -> B-M01 breed classifier
```

```text
robot live video
    -> frame capture and reconnect
    -> optional B-D01 COCO-pretrained cat localization
       -> stable padded detection crop
       -> or operator-aligned multi-scale centre-ROI fallback
    -> B-M01 YOLO26 five-breed classifier
    -> confidence margin + spatial/temporal consensus
    -> visible UI overlay + mandatory console print
    -> census record
```

机器人由团队 **远程控制**；Baseline 不需要自主导航，也不让 DL 代码发送电机命令。
操作员通过机器人摄像头寻找八张猫图：启用 `B-D01` 时只需让猫的视觉内容进入画面，
定位器给出候选框并裁剪；定位器未启用、漏检或结果过期时，操作员把目标大致置于中央
ROI。`B-M01` 始终是唯一品种判定器，确认后在控制台打印物种，最后由操作员把机器人
开回起点。

Baseline 的 detection 只允许一个可关闭、无需本项目框标注的 COCO `cat` 辅助定位器；
它不识别品种、不导航、也不是 release 依赖。Advanced 的多类别 detection、多专家、
语义融合、FSM 和自主动作仍不进入 Baseline 关键路径。这些工作保存在
[`ADVANCED_PLAN.md`](ADVANCED_PLAN.md)，只有本文件 Gate B4 通过后才启动。

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
| Derived-view 完整性 | crop `parent_image_id`/split 可追溯；detector miss 不删 base image；所有正式数量按 unique base image |
| 可选在线 `B-D01` 准入 | 同一冻结机器人视频上比 centre-ROI-only 降低 time-to-confirm，且 target/rejection gate 不下降；否则禁用 |

如模型指标和机器人联排冲突，优先修复端到端联排。高离线准确率不能替代真实摄像头
可用性。

---

## 3. 范围冻结

### 3.1 Baseline P0 优先级：周五评测前必须完成

本节的 `P0` 表示“必须交付”的优先级；第 9 节的 `Phase 0–4` 表示执行阶段，两者不要
混用。任何 Phase 内都先完成 Baseline P0 项，再处理低成本加分。

1. 五类猫数据集、来源清单、去重、85/15 固定切分；
2. `yolo26s-cls.pt` 六输出迁移学习：五种目标猫加内部 `not_target` 拒识类；B1 split
   冻结后用固定 `B-D01` 生成派生 crop，以 base image 为单位混合 original/crop 训练；
3. 机器人直播读取、断线提示和重连；
4. 多尺度中央 ROI、实时 top-3、置信度差值、时空共识和大字体物种显示；
5. 每次确认都向 console 打印物种、置信度和时间戳；
6. 八个目标的 census counter，避免漏记和重复记录；
7. 真实机器人/同款摄像头的打印图片测试；
8. 三次完整 15 分钟联排与离线启动检查；
9. Answer Book 所需图像数、架构说明、曲线和结果表。

### 3.2 P0 完成后才允许的低成本加分

- 无标注辅助定位：官方 COCO 预训练 `B-D01` 找 `cat`，稳定框外扩后交给 `B-M01`；
  无框时立即回退中央 ROI，开发与同视频比较不得阻塞 P0；
- 清晰的 mission-control UI：`FOUND 3/8`、类别、置信度、FPS；
- 确认识别时播放提示音或显示简短动画；
- 保存带时间戳的八条 census 记录供评委查看；
- 一键导出本次 run 的 CSV。

总投入上限为 2 小时；任何影响稳定性的效果立即移除。

人工数据复核进行期间，允许并行完成 `B-D01` 官方权重下载、typed adapter/centre-fallback
contract tests 和作业示例图离线 smoke；这些准备不得进入 active runtime、不得声称机器人
准入，也不改变 B0/B1。真实直播集成和 release go/no-go 仍必须等 `B-M01` centre-ROI 主链
可用后，在同一机器人视频上比较。

### 3.3 Baseline 明确不做

- detector 微调、bounding-box 标注或五品种直接 detection；`B-D01` 的官方预训练
  `cat` 输出是唯一例外；
- `B-D01 -> B-M01` 以外的多模型同帧 ensemble；
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

品种判定选择 YOLO26 **classification** 而不是让 detection 直接预测五个 breed：正式
输出是整张候选图的品种，现有数据只有 image-level 标签，不需要新增 bounding-box
标注。可选 `B-D01` 只负责提出猫的位置，不能替代 `B-M01`。两者共用
Ultralytics/PyTorch 环境、模型加载和离线打包流程，但 head、输出 schema、阈值与任务
权重不互相复用。

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

### 4.2 可选辅助定位器 `B-D01`

| 字段 | 决策 |
| --- | --- |
| 架构 | Ultralytics YOLO26s Detect；延迟不合格时回退 YOLO26n Detect |
| 初始化 | 官方 COCO 预训练 `yolo26s.pt`，不做本项目 detector 训练 |
| 任务 | 只保留模型 `names` 中的 `cat` 类，提出猫视觉内容候选框 |
| 输入 | 默认完整 RGB frame，初始 `imgsz=640`，最终值由机器人视频冻结 |
| 输出 | `Results.boxes` 适配后的 `LocalizerObservation`；不输出 breed |
| 标注 | 不制作训练 bounding box；人工筛选仍只服务 classification data |
| 部署 | 默认关闭，机器人同视频准入通过后才进入 release 配置 |
| 官方来源 | [Ultralytics COCO detection documentation](https://docs.ultralytics.com/datasets/detect/coco/) |

`B-D01` 学到的是 COCO 的真实猫视觉概念，不是专门的“打印卡片”类。它可能只框住打印
图片中的猫身体，也可能因距离、透视、反光或运动模糊漏检。因此它只能做高召回候选
生成：候选框外扩后交给 `B-M01`；`B-M01` 独立决定五个 target breed 或
`not_target`。没有候选框、框不稳定、框太小或框过期时立即使用 centre multi-scale
ROIs，不能等待 detector，也不能阻断确认。

冻结 `B-D01` 时必须记录权重来源、Ultralytics 版本、SHA-256、许可、`model.names` 中
实际解析出的 `cat` class ID、`imgsz`、候选上限和 threshold。不得只因第三方 Hugging
Face 模型名称含 `cat` 就引入来源、训练集或指标不清的 checkpoint。若 COCO 权重在真实
打印图视频上不通过准入，Baseline 的动作是禁用 `B-D01`，不是临时启动 detector 标注或
微调。

同一冻结 `B-D01` 还可以在 **离线训练预处理** 中使用：它只从已通过人工 breed 审核、
已完成 grouped split 的 base image 生成 padded crop view。该 crop 不构成新的标签、base
image 或 detector annotation，不能进入另一个 split，也不能因为 detector 命中而让该
parent 获得双倍采样权重。Detector miss 保留 original view 并计入每类 coverage 报告。

现有 GPU smoke 已证明官方权重和 `cat` mapping 能运行，并在五张 assignment smoke 图片
上产生 proposal；这只属于可执行性证据。课程 example 及其 crop 仍禁止进入训练，且该
结果不能替代机器人打印图/视频准入。

### 4.3 重复训练、后备与可选共识

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
├── view_manifest.csv
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
├── derived/
│   └── bd01_crops/
│       ├── train/<same six internal outputs>/
│       ├── val_select/<same six internal outputs>/
│       └── val_cal/<same six internal outputs>/
└── integration_test/
    ├── calibration/
    └── final/
```

`data/`、原图、打印扫描、视频、checkpoint 和训练输出均不提交 Git。Git 只保存脚本、
配置、去除私人路径的 manifest 模板和聚合指标。

**2026-07-15 当前状态：** 候选数据已经取得并交付人工筛选。最近一次可复查 handoff
包含 2,321 个 pending candidates（1,875 target、446 negative），当时 human-accepted
计数仍为 0，不能据此宣称达到 1,200 release floor 或冻结 split。人工决定写回、双人
复核、去重簇确认和 B1 audit 通过以前，不开始正式训练。当前操作入口见
[Phase 0 manual-action dashboard](../evaluation/BASELINE_PHASE0_MANUAL_ACTIONS.md)。
在 accepted base images 和 split 尚未冻结时，不得提前批量生成 classifier crop；否则
很容易把同一原图的不同派生视图分到不同 split，或对最终会被 reject 的图片浪费审核。

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
- 先在 unique base image/source/duplicate group 上冻结 split，再生成任何 detector crop；
- 每个 derived view 必须继承 parent split，且 `parent_image_id` 不得为空；原图与所有
  padding/crop/压缩派生永远不能跨 split；
- 作业报告、B1 数量和 class balance 只按 unique accepted base image 统计，不能把
  original 与 crop 相加。

### 5.6 Detector-derived classifier views

人工筛选负责判断 breed 标签、图像可用性、来源与重复关系；固定的 `B-D01` 只做自动
定位和裁剪，不能覆盖人工标签。处理顺序固定为：

```text
human acceptance + dedup/group audit
    -> freeze base-image split
    -> run pinned B-D01 per split
    -> choose one primary cat candidate
    -> pad + clamp + quality check
    -> write derived view and view_manifest
```

`view_manifest.csv` 每个 view 至少记录：

- `view_id`、`parent_image_id`、canonical `label`、inherited `split`；
- `view_kind=original|bd01_crop`、原图/crop 相对路径和 crop SHA-256；
- detector model ID、weight SHA-256、Ultralytics version、解析后的 `cat` class ID；
- normalized `xyxy`、detector confidence、padding ratio、clamp/quality 结果；
- `detector_status=hit|miss|multi_box|invalid`、生成脚本/config hash 和生成时间。

生成规则：

1. 每个 target base image 最多保留一个 deterministic primary crop。多框时按冻结的
   confidence/面积/中心性规则选主框；猫群、混杂品种或错误框由 contact sheet 人工复核，
   不自动制造多个“新样本”；
2. primary box 初始向外 padding `15%` 并 clamp 到原图边界；padding 候选只用
   `val_select` 比较后冻结。训练可在冻结值附近做小幅 padding jitter，`val_select`/
   `val_cal` 使用完全确定的 crop；
3. target detector miss 或 invalid crop **不得删除 parent**，只提供 original/letterboxed
   view，并在每类 hit/miss/invalid coverage 中报告；
4. 其他猫品种命中的 crop 保持 `not_target`；无猫背景即使无框也保留 original/centre-ROI
   `not_target` view；detector false-positive crop 只有人工复核后才可作为 hard negative；
5. assignment examples、`robot_calibration`、`robot_final` 及其任何 crop 不得进入训练或
   validation view manifest；
6. derived 文件、contact sheets 和缓存留在 ignored data/artifact 路径；Git 只提交生成
   代码、配置、manifest schema 和聚合 coverage。

训练 loader 以 `parent_image_id` 为采样单位，每次访问一个 parent 只选择一个 view：有
有效 crop 时按 `crop_view_probability` 在 original 与 crop 之间选择，无 crop 时使用
original。初值为 `0.5`，只能由 `val_select` 调整；禁止把两个文件直接平铺进普通
folder loader 后让 detector-hit parent 获得双倍权重。Validation 保持 base-image 数量，
分别报告 deterministic original view、frozen detector-crop view（仅 hit 子集）和完整
crop-plus-original-fallback policy；正式合并 15% 指标必须清楚说明采用的单一冻结 policy。

若 base-balanced multi-view loader 未在 Phase 2 cutoff 前通过 deterministic tests，立即
降级为 **one-view-per-parent materialization**：有效 crop 作为该 parent 的 training view，
miss/invalid 使用 original；每个 base image 在 folder tree 中恰好出现一次。不得为了实现
随机 multi-view 阻塞首个可训练 seed，也不得把 original+crop 同时平铺来绕过 loader。

### 5.7 打印图与机器人域测试

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

机器人视频到位后，在相同冻结 clips 上比较三条路径：

```text
A: centre ROIs -> B-M01
B: B-D01 detection crop -> B-M01
C: B-D01 detection crop + centre-ROI fallback -> B-M01
```

`B-D01` 不需要训练集框标注，但需要真实视频准入证据。按 base image/session 统计一秒
窗口内的 stable-box success、false proposals、stale/missing rate、time-to-first-stable-box、
端到端 time-to-confirm、FPS 和 P95；重复帧不增加样本数。只有 C 相比 A 降低
time-to-confirm，且 target/rejection gate 无下降时才启用。B 只做消融，不作为没有
fallback 的现场模式。

---

## 6. 训练方案

### 6.1 可复现配置初值

```yaml
task: classify
seed: 20260714
model: yolo26s-cls.pt
data: data/cat_census
view_manifest: data/cat_census/view_manifest.csv
sampling_unit: parent_image_id
crop_view_probability: 0.5
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

`view_manifest`、`sampling_unit` 和 `crop_view_probability` 是项目 wrapper 配置，不是
未经确认的 Ultralytics 原生参数。后续实现必须用 base-balanced dataset/loader 保证每个
parent 每次只贡献一个 view，并通过 deterministic fixture 验证采样；不能仅把字段写进
YAML 而继续使用会双倍采样的普通 folder loader。

Ultralytics 原生记录 top-1/top-5；本项目另用固定 validation prediction 计算 macro F1、
per-class recall 和 confusion matrix。Batch 如显存或 DataLoader 不稳定可降至 32；其他
超参数不因单次结果随意改变。

### 6.2 Augmentation

训练集使用适度的：

- original view 使用受限 random resized crop；detector crop 只做轻度 scale/padding jitter；
- horizontal flip；
- `±10°` rotation 和轻微 perspective；
- brightness/contrast/color jitter；
- 轻度 blur、JPEG compression 和噪声；
- 小概率遮挡。

避免过强裁剪、垂直翻转和严重颜色变化，以免抹掉品种特征。Ultralytics classify 默认
crop-based transform 可能裁掉极端宽高比图片中的关键信息，因此数据审查必须检查变换
后的训练预览；必要时使用保持宽高比的 resize/pad 自定义 transform。Validation 使用
冻结的确定性 transform，不做随机增强。Original/crop 的 resize、normalization 和颜色
处理必须一致；crop 不能再次被 aggressive centre/random crop 切掉耳朵或身体。

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
- 按 breed 的 detector hit/miss/invalid coverage、crop box/padding 分布，以及 original、
  crop-hit 子集、crop-plus-original-fallback 三种 validation view 指标；
- base-image 采样审计：每个 parent 的访问权重一致，派生 view 未改变官方样本数；
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

`B-M01` runner 将 `Results.probs` 转成 canonical `ClassificationObservation`。现有 bounded
smoke target 已同时实现 `B-D01` 的 `LocalizerBox`/`LocalizerObservation` adapter 和
same-frame crop router，并用 contract tests 隔离 breed semantics；它仍处于 disabled/not
release-admitted 状态。`LocalizerObservation` 承载 normalized box、detector confidence、
model/frame/timestamp、valid/reason，不包含 breed。UI、crop router、日志和调度器不得直接
读取 Torch tensor 或 Ultralytics result。任何 derived-view generator 必须消费这一 typed
contract 或等价的序列化 manifest，不得重新把 native results 泄漏到数据层。Advanced
runner 将自己的 `Results.boxes` 转成 `ExpertObservation`；各 runner 复用
`ModelRunner[OutputT]`、`FramePacket`、设备选择、健康状态、telemetry 和 fixture 模式，
但不混用业务输出类型。

### 7.2 Worker 与队列

```text
Capture worker -> latest-frame ring buffer -> display
                         |                  -> B-D01 latest-only localization job
                         |                         -> stable padded crop router
                         |                         -> centre-ROI fallback
                         +-----------------------> B-M01 preview/confirmation jobs
GPU runners -> typed observations -> Aggregator -> UI/console/logger
```

- Capture worker 永不等待模型，只写入有界 latest-frame ring buffer；
- UI 始终显示最新 capture frame，而不是等待推理完成的旧画面；
- Preview 只取最新帧，队列最多 1 个 pending job，旧 preview 自动丢弃；
- `B-D01` 也只有 1 个 latest-only pending job；localization 结果过期、无框或框质量不过门
  时 crop router 立即选择 centre ROI，不等待重试；
- Confirmation job 固定快照最近 5 个新鲜帧并获得 GPU 优先级，但不能阻塞 capture、遥控
  或 UI event loop；确认期间可以降低 preview 推理频率；
- Aggregator 和 logger 只接收标准 observation/event；所有队列有长度、超时和 dropped
  counter，禁止无限积压。

### 7.3 画质门、预览与确认

1. 视频连续预览并保留 `wide / medium / tight` 中央引导框；启用 `B-D01` 时额外显示其
   最新新鲜候选框，但框和 detector confidence 绝不构成 species 输出；
2. `B-D01` 候选按 confidence、面积、画面边界和时间稳定性过滤，候选数有上限；稳定框
   做边界安全的 padding 后成为分类 ROI，无有效框则选择中央 ROI；
3. 推理前计算 blur、平均亮度、过曝/欠曝比例、frame age 和 ROI coverage；画质不过门时
   UI 直接提示 `MOVE CLOSER / HOLD STILL / ADJUST LIGHT`，不让分类器猜；
4. 实时 preview 优先处理稳定 detection crop，否则处理 `medium` centre ROI；使用
   calibrated probability，UI 显示 top-3、margin、quality、FPS、延迟、stream 和
   localization/fallback 状态；preview 与 detector 都不写 species console 行；
5. 最近 7 个有效 preview 经时间 EMA 后为目标 breed 且超过 calibration 冻结的
   confidence/margin 才在 UI 大字显示 `STABLE: <species>`；若 top-1 为 `not_target`，显示
   `SEARCHING / NO TARGET`；
6. 操作员按 Space 后，若最近 5 个新鲜帧都有 IoU 连贯的 detection crop，则对每帧的
   padded crop 分类；否则对三个 centre ROI scale 分类。所有概率先应用 temperature，再
   做空间/时间聚合；相关 crop、scale 和帧不得称为独立投票；
7. 只有聚合 top-1 是目标 breed、时序一致性、quality、calibrated confidence 和 margin
   全过门时才确认；centre-ROI 模式额外要求至少 2/3 scale 在至少 4/5 帧同意。`not_target`
   或共识不足时显示 `UNCERTAIN — MOVE CLOSER/REALIGN`，不登记；
8. 确认成功后 UI 与 console 同时显示 species 并刷新 `FOUND n/8`；Backspace 可撤销最后
   一条误登记，但日志保留 correction 事件；
9. 视频过期、分类模型异常或 calibration 配置不匹配时显示 `UNKNOWN/NOT READY`，不登记；
   仅 detector 异常时显示 `LOCALIZER OFF / CENTRE ROI` 并继续分类 fallback。

console 最低输出格式：

```text
2026-07-17T09:42:18+08:00 CONFIRMED species=Ragdoll confidence=0.934 margin=0.281 found=3/8 model=B-M01
```

### 7.4 稳定性要求

- capture、GPU runner、aggregator 和 UI 解耦，所有队列均有界并记录 dropped jobs；
- 断流超过 500 ms 时清空 temporal window，禁止沿用旧预测；
- detector 的 box window 与 classifier 的 probability window 分开清空，禁止旧框裁剪新帧；
- 自动重连并在 UI 显示重连次数；
- GPU 推理失败时显示明确错误，不静默输出旧类别；
- 所有权重、字体和配置提前离线缓存；
- release 前验证 Windows 路径、中文路径和摄像头 URL 配置。

---

## 8. 与 Robotics 组的接口

**2026-07-15 当前状态：** Robotics 正在交接机器人视频。当前只记录了期望配置
`480 x 480 JPEG quality 85 @ 8 FPS`；delivery protocol、endpoint/configuration
method、真实分辨率/FPS、orientation/color、source-frame identity 和断线行为仍未验证。
交接中的视频在实际收到、检查并产生 replay evidence 前，不能写成 Gate B0 已通过。

DL 组仍需要 Robotics 组确认：

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
DL: stream consumer + optional cat localizer + breed classifier + visible prediction + census log
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
- 冻结 `B-D01` 只使用官方 COCO `cat`、不训练/不标框、失败回退 centre ROI 的原则；
  该增强的模型下载、实现与准入不新增 Gate B0 条件。

**Gate B0：** 五类映射、manifest schema、来源 pilot、真实机器人帧和端到端假模型 UI
均有可复查证据。B0 不要求已经爬满数据，也不允许因为爬虫未完成而阻塞软件骨架。

**当前状态：NOT PASSED。** 软件骨架与 source pilots 已完成；机器人真实帧和 delivery
contract 仍是仅有的两个 open checks，正在等待视频交接。Phase 1 人工筛选与 B0 是两条
并行的人工作业，不得互相冒充完成证据。

### Phase 1 — Acquisition、清洗与冻结（7 月 15 日 12:00 前）

- 先获取 Oxford、Wikimedia 与 iNaturalist 候选，生成去重后覆盖报告；
- 仅对 `< 400` 的类别启动定向 Selenium gap-fill；
- 双人复核易混淆类，完成 exact/near-duplicate 聚类和 source-group 标记；
- 先达到每类 `>= 220`、总计 `>= 1,200` 的 release floor，再补到每类约 400、总计
  2,000；
- `not_target` 达到至少 300 张，并按来源/录制 session 分组；
- 冻结 85% train / 10% val_select / 5% val_cal 和 manifest；不得为了等待 3,000 张而
  推迟训练。
- 本阶段只冻结 accepted base images 和 split；不得在 split 前生成并随机分配 detector
  crops，派生视图不参与 B1 数量门槛。

**Gate B1：** `>= 1,200` 张 clean unique target images、每类不低于 220、`>= 300`
张 grouped `not_target`、来源可追溯、85/10/5 split 冻结且训练可复现；正式目标仍为
2,000 张目标猫。

**当前状态：HUMAN REVIEW IN PROGRESS。** 候选数据获取和最小 review handoff 已完成；
最近审计的 2,321 个候选仍等待人工决定，尚不能按 accepted 计数，B1 未通过，正式 split
未冻结。优先完成筛选和必需双人复核，不再为增加 raw 数量重开无边界收集。

### Phase 2 — 训练与首次机器人集成（7 月 15 日 17:00 前）

- B1 通过后立即用 pinned `B-D01` 按 split 生成 deterministic primary crops、
  `view_manifest`、per-class coverage 和 contact sheets；miss/invalid 使用 original，不能
  为等 crop 或提高 hit rate 推迟首轮训练；
- 用通过测试的 base-balanced original/crop loader 跑一个 `yolo26s-cls` seed；若 loader
  未过门，使用 one-view-per-parent materialization，记录曲线、混淆矩阵、target-only/
  拒识指标和分 view 指标；
- 只针对有证据的主要混淆类补数据，不重开无边界收集；
- 最迟 17:00 把 best checkpoint 接到真实直播；先过直播 Gate，再补其他 seed、
  `yolo26m-cls` challenger 或 EfficientNet 后备；
- 晚上只使用 `robot_calibration` 做第一轮 target/negative 测试和 15 分钟机器人联排；
- `B-M01` centre-ROI 直播链路通过后，才在同一机器人视频上零训练测试
  `B-D01=yolo26s.pt` 的 COCO `cat` 输出；不标框、不微调，不让该实验阻塞 B2；
- 在 09:00–12:00 或 14:00–17:00 带实际问题参加 Makers@SoC consultation。

**Gate B2：** 单个 `yolo26s-cls` 已在真实直播中区分 target/not_target，UI 可见
species，只有 confirmation 向 console 打印；worker 队列无阻塞增长。`B-D01` 不属于
B2 在线必需项，禁用在线 detector 时必须完整通过。若训练使用 derived views，
`parent_image_id`、继承 split、base-balanced sampling 和 detector-miss fallback 必须有
审计证据。

### Phase 3 — 域适配、可靠性与冻结（7 月 16 日 18:00 前）

- 修复打印图/直播域差，不再扩展功能；
- 用 `val_cal + robot_calibration` 拟合 temperature 并冻结 quality、confidence、margin、
  ROI 权重、EMA、checkpoint、class mapping 和依赖；如果 `B-D01` 通过同视频准入，同时
  冻结其 weight hash、cat class mapping、imgsz、threshold、padding、候选上限和 fallback；
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
| 派生视图 | split-before-derive、parent inheritance、hit/miss/multi-box、crop hash | crop 不跨 split/不增加 base count；miss 不删除 parent |
| 训练采样 | original/crop view selection、无 crop fallback、固定 seed | 每次每 parent 一个 view，hit parent 不获双倍权重 |
| 模型 | val_select、val_cal、混淆矩阵、NLL/ECE、重复 run | 选择与校准职责分离，类别顺序一致 |
| 辅助定位 | detector present/missing/stale、多框、box padding/clamp、centre fallback | 无框或坏框不阻塞分类；detector 不产生 species |
| 画质 | blur、曝光、frame age、ROI coverage 边界 fixture | 不合格帧不进入分类/确认 |
| 推理 | 三尺度概率、temperature、EMA、margin、旧帧 | 相关证据不当独立票，旧帧不登记 |
| 并发 | capture/localize/preview/confirm/UI 队列、timeout、drop | detector/confirmation 不阻塞 capture/遥控/UI，无无限积压 |
| 视频 | 断流、重连、低 FPS、旋转画面 | UI 明确告警并恢复 |
| 定位消融 | 同一冻结视频的 A/B/C 三条路径 | 只有 C 降低 time-to-confirm 且正确率不退化才启用 `B-D01` |
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
| Detector crop 产生类别偏差 | 每类 hit/miss 差异大，某类只剩“容易图” | 保留所有 original、按类报告 coverage，人工审查 crop；不按 hit 过滤 base | 提高 original-view 比例或禁用 crop view |
| Crop 切掉品种特征 | 耳朵/身体频繁被截断，crop-view recall 下降 | 增加 padding、contact-sheet 审核；val_select 冻结 padding | 使用 original/centre ROI view |
| Multi-view loader 延误首训 | 自定义 loader fixture 未过且 B1 已完成 | 立即生成 one-view-per-parent tree | 不把 original+crop 平铺，先跑可追溯单视图 seed |
| 视频延迟 | 队列增长、画面滞后 | latest-frame 策略，降低显示分辨率 | 降推理频率但保持遥控流畅 |
| 断流 | frame age 超阈值 | 重连和清空概率/EMA 状态 | 显示 NOT READY，先恢复再登记 |
| GPU/环境故障 | CUDA 初始化失败 | 锁依赖并准备同机 CPU smoke test | 重启冻结环境，不现场安装包 |
| UI 被遮挡 | 遥控窗口抢占 | 固定窗口布局和键位 | console 保持独立可见 |
| 数据仍不足 | 周三上午 `< 1,200` | 全员停止 Advanced，集中收集清洗 | 保证均衡和质量，不伪造数量 |
| 多尺度结果冲突 | 不同 ROI 的 top-1 不一致 | 检查 framing 与训练 crop，冻结 margin/共识阈值 | 提示靠近或重新对准，不强行登记 |
| COCO detector 不识别打印猫 | 一秒窗口无稳定框 | 检查 `imgsz`/threshold 和真实距离；不启动标注微调 | 关闭 `B-D01`，centre ROI 继续工作 |
| Detector 误框海报/玩具 | false proposals 高 | 候选上限、面积/质量门和 `not_target` hard negatives | classifier 拒绝，不打印 species |
| 两模型争用 GPU | FPS/P95 退化或队列 drop 增加 | detector 降频、latest-only；必要时回退 `yolo26n.pt` | 关闭 detector，保留单 classifier |
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
3. 一页架构说明：为何由 YOLO26s classify 负责正式 breed 输出、如何使用 ImageNet
   预训练权重学习五个目标 breed 与内部 `not_target`、augmentation、loss 和优化器；
   说明固定 `B-D01` 如何从已 split 的 base images 生成不增加官方数量的 padded training
   views、如何保持 parent-balanced sampling；若实际启用在线 `B-D01`，再说明 centre-ROI
   fallback，不把 COCO detector 指标写成品种识别成绩；
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
- `B-D01` 的 latest-only detector scheduling、`Results.boxes` adapter、box quality/padding、
  crop routing 和 same-video ablation harness；
- split-after-review/derive-after-split workflow、derived-view manifest、base-balanced
  multi-view loader、coverage/contact-sheet audit 和 view-specific evaluation；
- OpenCV overlay、console reporter、run logger 和 CSV 导出；
- 视频录制/回放、延迟统计和离线 smoke-test harness；
- Robotics 视频配置、窗口布局和现场恢复 runbook；
- release/checksum/offline packaging 流程。

Advanced 必须替换或扩展：

- 将 Baseline 的 `B-D01` cat-only filter/threshold 和 `B-M01` breed classifier 替换为
  Advanced M01 多类别 detection (`yolo26n.pt` 或证据支持的 `yolo26s.pt`) 及其他专家；
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
- [ ] 若使用 detector-derived classifier views，所有 crop 有 parent/split/model/config/hash
  追踪，miss parent 未删除，派生图未增加官方数量或改变 base sampling weight；
- [ ] original、detector-crop hit 子集和 crop-plus-original-fallback 指标已在冻结 validation
  上分别报告，assignment/robot calibration/final 图未进入 derived training views；
- [ ] `B-M01` `yolo26s-cls.pt` 的来源、版本、类顺序、配置和 SHA-256 已记录；
- [ ] 三个 `B-M01` 随机种子已按同一 split 比较，release checkpoint 有可追溯依据；
- [ ] val_select、val_cal、robot_calibration 与 robot_final 职责隔离；temperature、ECE、
  quality 和阈值均可追溯；
- [ ] 一次性 robot_final target/rejection 指标达到 release gate，或偏差有书面风险接受；
- [ ] 机器人真实直播能连续运行模型并显示 top-3、FPS 和 stream 状态；
- [ ] detector 禁用时 centre-ROI-only release 路径完整可用；若启用 `B-D01`，官方权重
  来源/hash、cat mapping、同视频准入、typed observation、bounded queue 和 fallback
  均有证据，且没有 detector 训练/框标注依赖；
- [ ] target 每次确认都在 UI 和 console 清楚显示 species；`not_target` 不打印 species；
- [ ] confirmation 不阻塞 capture、遥控或 UI，所有队列有界并报告 drop/timeout；
- [ ] 断流、旧帧和低置信度不会登记错误结果；
- [ ] 八条 census 记录和撤销操作可用；
- [ ] 全组连续三次在 15 分钟内识别 8/8 并返回起点；
- [ ] release 在断网状态可从头启动；
- [ ] 全员知道 reporting time、到场地点、现场职责和恢复流程；
- [ ] Answer Book 的数量、架构、准确率与拟合分析已由两人复核；
- [ ] 只有以上项目完成后，团队才进入 [`ADVANCED_PLAN.md`](ADVANCED_PLAN.md)。
