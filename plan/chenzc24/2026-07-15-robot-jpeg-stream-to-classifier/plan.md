# Robot JPEG Stream To Baseline Classifier

## 目标

将机器人以约 4.5 FPS 写入目录的 640x480 JPG 连续帧，可靠地转换为：

```text
atomic JPG -> FramePacket -> quality gate -> B-D01 -> ROI router
           -> one B-M01 classifier -> temporal consensus -> confirmation event
```

该目标只建立可回放、可观测、不会积压旧帧的 Baseline 实时链路。模型训练、
数据补充和自动驾驶不与本目标绑定；分类器的切换只能在同一 replay 输入上完成
A/B 证据后进行。

## 已观测输入

| 输入目录 | JPG 数量 | 分辨率 | 中位帧间隔 | 按大于 2 秒间隔划分 |
| --- | ---: | ---: | ---: | ---: |
| `data/downloads/Camera/2026-07-15/` | 428 | 640x480 | 213.4 ms | 8 bursts |
| `data/downloads/Camera/frame_20260715_143931_994185/` | 1,146 | 640x480 | 224.4 ms | 15 bursts |

补充事实：

- 1,574 个文件均可解码，文件名均包含微秒级本地拍摄时间，且无完全相同文件；
- 相邻帧中约 46% 的 dHash 距离不超过 2，存在大量近重复画面；
- blur score 小于 20 的帧约占 32%，曝光没有发现系统性失效；
- 第二个目录跨越约 32 分钟，因此目录名不能被当作单一 frame 或 session 身份；
- 打印纸经常位于画面边缘，不能假定 centre fallback 总能包含目标。

## Dirty-State 决策

开始时 `main` 与 `origin/main` 对齐，但存在多组训练、数据源、评估和计划的未提交
修改。本目标的实现不得修改这些现有脏文件，包括 `.gitignore`、`AGENTS.md`、
现有模型 manifest、训练配置、训练脚本和已有评估报告。

规划阶段只拥有本文件。进入实现后，每个 Phase 应先重新检查以下 proposed paths
是否仍无并发占用；如有重叠，拆成新的目标而不是覆盖。

## Owner

- Target owner: `chenzc24`

## Proposed Owned Files

- `configs/baseline_robot_jpeg_stream.toml`
- `src/deskmate_baseline/jpeg_stream.py`
- `src/deskmate_baseline/stream_pipeline.py`
- `scripts/inspect_robot_jpeg_stream.py`
- `scripts/replay_robot_jpeg_stream.py`
- `scripts/run_baseline_robot_stream.py`
- `tests/test_jpeg_stream.py`
- `tests/test_stream_pipeline.py`
- `docs/evaluation/BASELINE_ROBOT_STREAM_REPLAY.md`
- `docs/evaluation/BASELINE_ROBOT_STREAM_REPLAY.json`
- ignored/generated `artifacts/robot_stream/`
- this plan and an append-only completion entry in `plan/log.md`

## Read-Only Dependencies

- both robot-camera directories listed above;
- `src/deskmate_baseline/contracts.py`;
- `src/deskmate_baseline/video.py`;
- `src/deskmate_baseline/runtime.py`;
- `src/deskmate_baseline/localization.py`;
- `src/deskmate_baseline/inference.py`;
- `configs/baseline_phase0.toml`;
- `configs/baseline_localizer.toml`;
- `configs/baseline_inference.toml`;
- current and hardened-candidate classifier checkpoints;
- all pre-existing dirty and untracked paths.

若实现证明必须改变 `FramePacket`、localizer 或 runtime 的共享接口，应停止当前目标，
单独建立 contract-change target，并在同一提交更新生产者、消费者和 contract tests。

## 核心契约

### 1. 文件接收契约

生产端首选：

```text
frame_<YYYYMMDD>_<HHMMSS>_<ffffff>.jpg.tmp
-> fsync/close
-> atomic rename to .jpg
```

消费者只接受最终 `.jpg`。如果机器人端暂时无法原子重命名，fallback 为文件大小和
修改时间连续两个 poll（间隔 100 ms）不变后再解码。解码失败不得重试为旧帧，
只记录 `partial_or_invalid_jpeg`。

### 2. 帧身份契约

新增 `JpegFrameRecord`，至少包含：

- `source_frame_key`: 完整文件 stem；
- `captured_at_ns`: 从文件名按 Asia/Singapore 解析；
- `received_at_ns`: 接收端首次发现时间；
- `session_id`: 连接身份，replay 中以相邻帧 gap 大于 2 秒切分；
- `path`, `width`, `height`, `jpeg_bytes` 或 SHA-256；
- 单调递增的本地 `frame_id`。

向现有模型边界转换时构造 `FramePacket`，并令
`source="robot_jpeg:<session_id>:<source_frame_key>"`。不依赖文件 mtime，不把目录名
当作 frame ID。

### 3. 时间语义

- live 模式使用真实 wall clock 进行 stale 检查；
- replay 模式使用文件中的 capture timeline 驱动 replay clock，不能把历史文件按
  当前 wall clock 判为 stale；
- 新 session、超过最大 gap、断连或连续无有效帧时清空 temporal state；
- 乱序且早于已处理 watermark 的 live 文件记录为 `late_frame`，不回灌状态机。

## 初始配置（进入 replay 校准前均为 provisional）

```toml
[source]
expected_width = 640
expected_height = 480
expected_fps = 5.0
poll_interval_ms = 50
stable_file_checks = 2
stable_file_check_interval_ms = 100
session_gap_ms = 2000
maximum_live_frame_age_ms = 750

[scheduler]
latest_frame_capacity = 5
maximum_pending_preview_jobs = 1
drop_old_preview_frames = true

[quality]
minimum_blur_score = 20.0
minimum_mean_brightness = 20.0
maximum_mean_brightness = 235.0
maximum_overexposed_ratio = 0.35
maximum_underexposed_ratio = 0.35

[localizer]
confidence_threshold = 0.25
minimum_box_area_ratio = 0.01
maximum_candidates = 5
candidate_deduplication_iou_threshold = 0.85
padding_ratio = 0.15
minimum_padded_short_side_pixels = 64
last_stable_box_ttl_ms = 750

[temporal]
window_size = 5
minimum_valid_observations = 3
maximum_observation_gap_ms = 1000
provisional_confidence = 0.65
provisional_margin = 0.20
```

关键语义：blur、stale、detector miss 和非法 ROI 产生 invalid/`unknown`，不能伪装为
有效 `not_target`；只有对有效 ROI 完成分类后，`not_target` 才是合法分类结果。

## Phase 0 — 固定 replay 输入与标注边界

### 工作

1. `inspect_robot_jpeg_stream.py` 只读扫描 JPG：解析时间、尺寸、解码状态、blur、
   brightness、相邻 gap、exact hash 和 dHash。
2. 以 gap `> 2 s` 生成稳定的 burst/session manifest，不移动、不改名原图。
3. 为 23 个 bursts 生成待人工填写的 session label 模板。标签只能由人工依据实验
   布置填写，推理代码不得读取打印纸文字或使用 OCR。
4. 明确哪些 sessions 属于 model selection/calibration，哪些从未用于调参并保留为
   final replay；同一 burst 不得跨集合。

### 产物

- generated `artifacts/robot_stream/input_inventory.csv`；
- generated `artifacts/robot_stream/session_manifest.csv`；
- generated contact sheets，每个 burst 等时间抽取 6–10 帧；
- 人工 label 模板，不自动声称 ground truth。

### Gate P0

- 1,574/1,574 文件可重复解析并保持严格时间顺序；
- 428/1,146、640x480 和 8/15 burst 计数被测试固定；
- 输入 manifest 双次生成具有相同 hash；
- 未读取纸面文字，未修改原始 JPG。

## Phase 1 — JPG watcher、latest-only 调度与质量门控

### 工作

1. `jpeg_stream.py` 实现 filename parser、stable-file gate、sessionizer、live watcher 和
   deterministic replay source。
2. watcher 将新帧推入现有 `LatestFrameBuffer(capacity=5)`；推理繁忙时旧 preview
   自动丢弃，confirmation job 不被 preview 挤占。
3. 解码保持原始 640x480 BGR；不在 detector 前拉伸为 480x480。
4. 计算 Laplacian blur、亮度与过曝/欠曝比例，并复用 `evaluate_quality`。
5. invalid、missing、disconnect、session change 必须清空 temporal state。

### Gate P1

- `.tmp`、半写入、损坏 JPEG、重复通知和乱序文件有单元测试；
- producer 以 5 FPS 写入、consumer 故意降速时，内存队列保持有界且处理最新帧；
- live stale 和 replay virtual clock 分别正确；
- 质量阈值 20 的保留/拒绝计数被报告，不把阈值 40 直接用于真实流。

## Phase 2 — Detector、候选 ROI 与时序路由

### 工作

1. 每个通过质量门的最新帧运行现有 B-D01，完整输入为 640x480。
2. 去除 IoU 高于 0.85 的重复候选，保留最多 5 个候选。
3. 每个候选使用 15% padding，拒绝最短边小于 64 px 的 crop。
4. 单框时分类该框；多框时分类前若干可靠候选，保留每个候选的概率而非静默选择
   detector top-1。
5. 当前帧 miss 时可以在同一 session 内短暂复用上一稳定框，TTL 最大 750 ms；
   必须检查坐标边界并扩大上下文。
6. stable-box TTL 过期后：operator 已将目标置中才允许 centre fallback；否则输出
   invalid `unknown/searching`，不强制给出品种。

### Gate P2

- replay 报告 detector hit/miss/multi-box、box TTL reuse、centre fallback、invalid
  和每种 route 的数量；
- 可视化所有 route 类型及至少 50 个均匀抽样 ROI；
- 覆盖错误 frame ID、stale box、小框、越界框、多框和无框测试；
- 不以两张 Pallas 静态图作为 release 指标。

## Phase 3 — 单分类器与 temporal consensus

### 工作

1. `stream_pipeline.py` 只通过现有 backend 调用一个激活的 B-M01；框架原生对象不
   泄漏到调度、日志或 UI。
2. 每个 ROI 保留 canonical 六类概率、top-3、confidence、margin、route 和 frame
   identity。
3. 最近 5 个有效 observation 按概率平均聚合；要求至少 3 个有效 observation。
4. 初始 confirmation gate 使用 confidence 0.65、margin 0.20，但必须在 replay 的
   calibration sessions 上调整后冻结。
5. `not_target` 不产生 species event；invalid 也不作为 `not_target` 投票。
6. 同一 target 只产生一次 confirmation，离场/新 session 后才允许重新确认；控制台
   只打印 confirmed species，preview 不刷屏。

### Gate P3

- 单帧预测、聚合预测和 confirmation event 均能追溯到 source frames；
- stale/missing/invalid 会清空窗口；
- 三帧一致、概率冲突、低 margin、label oscillation、`not_target` 和 session reset
  均有确定性测试；
- 不允许 detector、classifier 或 expert 触发机器人运动。

## Phase 4 — 同一 replay 上的模型与策略 A/B

### 固定比较

在完全相同的 FramePacket、质量结果和 ROI 上比较：

1. 当前 provisional B-M01；
2. disabled hardened candidate；
3. frame-level 与 5-frame temporal consensus；
4. detector crop、stable-box reuse 和 centre fallback 各 route。

不得为不同模型重新选择有利帧或 ROI。机器人 sessions 一旦用于模型选择，就不能
再作为 final replay。

### 指标

- input/decode/quality-valid/detector-valid/classifier-valid rate；
- stale、missing、dropped preview、late frame rate；
- per-route 与 per-session top-1、macro F1（仅人工标签完成后）；
- confirmation precision、target confirmation rate、false confirmation count；
- time-to-first-confirmation；
- detector、classifier、end-to-end mean/P95 latency 和实际 throughput；
- Pallas/Singapura/Persian confusion 与低 margin 分布；
- current 到 candidate 的逐 session regression list。

### Gate P4

- 所有结果包含输入 manifest hash、配置 hash、模型 hash、硬件和软件版本；
- temporal 策略相对 frame-level 降低抖动且不显著增加 false confirmation；
- candidate 只有在新、未参与设计的 sessions 上保持 Pallas 增益，并且 Singapura、
  Persian 和 rejection 无重大回归时才能启用；
- 未达到 gate 时保留当前模型，并明确记录数据缺口。

## Phase 5 — Live CLI 与 demo 验收

### CLI

```powershell
.\.venv\Scripts\python.exe scripts/run_baseline_robot_stream.py `
  --watch-dir <robot-output-directory> `
  --config configs/baseline_robot_jpeg_stream.toml
```

CLI 启动时必须离线加载并验证 detector/classifier hash，预热模型，然后输出简洁健康
状态。运行日志写入 ignored artifact 目录，包含 frame、session、route、quality、
prediction、drop 和 latency 字段。

### 录制验收场景

1. 清晰目标从远到近；
2. 目标在左/右/底部而非中心；
3. 快速运动造成连续模糊；
4. detector 间歇 miss；
5. 两个 cat-like 区域或多框；
6. 背景/无目标；
7. JPG 半写入、断连和恢复；
8. Pallas、Singapura、Persian 的混淆场景。

### Gate P5

- 运行 10 分钟内存与队列有界，无旧帧追赶；
- 断连后立即失效旧 prediction，恢复后建立新 session；
- confirmed species 在控制台可见且每个事件只打印一次；
- replay 与 live 对同一帧序列产生一致的决策；
- 无网络也能加载全部模型；
- 无任何机器人运动命令。

## Phase 6 — 可选数据提取，独立于实时发布

1,574 帧不能视为 1,574 个独立训练样本。只有在人工决定将某些 sessions 用于训练
后，才执行：

- 按 burst/session 分组，不随机拆相邻帧；
- 首先过滤 blur < 20；
- 使用时间间隔和 perceptual distance 选择 keyframes；
- 每个 burst 限制最大样本数，避免一个慢速片段支配训练；
- calibration/final sessions 永不进入训练；
- 记录 derived frame 到 source session 的完整 lineage。

该工作应建立单独 dataset target，不与 Phase 0–5 的实时链路提交合并。

## 实施顺序与预计工作量

| 顺序 | Phase | 预计 | 是否阻塞下一步 |
| --- | --- | ---: | --- |
| 1 | P0 replay inventory/session split | 0.5 天 | 是 |
| 2 | P1 watcher/latest-only/quality | 0.5–1 天 | 是 |
| 3 | P2 detector/temporal ROI routing | 0.5–1 天 | 是 |
| 4 | P3 classifier/consensus/events | 0.5–1 天 | 是 |
| 5 | P4 replay A/B and calibration | 1 天 | 是 |
| 6 | P5 live CLI/video acceptance | 0.5–1 天 | release gate |
| 7 | P6 training keyframe extraction | 独立安排 | 否 |

Baseline 最短可演示路径是 P0 -> P1 -> P2 -> P3 -> P4 的 current-model replay，随后
完成 P5 live 验收。P6 不是当前链路上线的前置条件。

## 全局验证

- targeted tests for filename/session/watcher/pipeline modules；
- `python -m pytest -q tests`；
- replay 两次输出相同 decision manifest hash；
- JSON/TOML/CSV 使用真实 parser；
- 模型 SHA-256 与 canonical class mapping；
- actual-camera replay 与 recorded live demo；
- `git diff --check`；
- `git status --short --branch`，只 stage 本目标 owned paths。

## 明确非目标

- 不进行 OCR 或利用打印出的 breed 名称；
- 不把每张连续帧当独立训练图片；
- 不在 watcher 中阻塞等待 inference；
- 不因 detector miss 强行输出一个 breed；
- 不同时启用两个 classifier 作为发布 runtime；
- 不控制机器人电机或自主移动；
- 不在本目标中重新训练模型。

## Commit Intent

本轮只制定详细计划，不自动 commit 或 push。后续实现应按 Phase 拆成小提交，且在每个
Phase 开始前重新确认 dirty worktree 与路径所有权。
