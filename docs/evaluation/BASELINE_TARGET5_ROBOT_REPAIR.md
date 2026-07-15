# Baseline target-five robot-domain repair

## Outcome

The selected deployment candidate is a single 30% robot-domain / 70% general-domain
weight interpolation. It preserves the original target validation score while fixing
most robot-camera domain errors.

| Candidate | Robot diagnostic | General target val | General target calibration |
| --- | ---: | ---: | ---: |
| Six-class clean baseline | 14/24 (58.33%) | 96.31% previously reported | 98.41% previously reported |
| Five-class general | 14/24 (58.33%) | 242/254 (95.28%) | not selected |
| Five-class fully robot-adapted | 24/24 (100%) | 142/254 (55.91%) | rejected for forgetting |
| **Five-class robot alpha 0.3** | **23/24 (95.83%)** | **242/254 (95.28%)** | **121/126 (96.03%)** |

On the separate nine labeled legacy stills, the selected candidate scores 8/9,
compared with 6/9 for the preceding clean six-class pipeline.

The remaining robot error is `Pallas_04.jpg`, routed through centre fallback after a
detector miss and classified as Persian. Do not add a one-image exception rule.

## Contract

- The breed head exposes exactly five target breeds and cannot emit `not_target`.
- Existing consumers receive a six-slot probability tuple with a zero-valued
  `not_target` slot through `UltralyticsTargetClassificationBackend`.
- Exact diagnostic source frames were excluded from domain-adaptation training.
- An independent SHA-256 overlap check found 0 exact source images shared by the 350
  adaptation rows and 24 diagnostic rows.
- Adaptation and diagnostic frames still share source bursts, so 23/24 is a demo
  development result, not an independent generalization claim.
- Final evaluation requires newly captured sessions held out by session and displayed
  source image.
