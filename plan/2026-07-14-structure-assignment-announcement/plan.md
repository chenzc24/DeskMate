# Structure Assignment Announcement

## Goal

Convert the copied Great Cat Census announcement into clear, structured Markdown while preserving every substantive detail, requirement, and stated logistical item.

## Dirty-State Note

Start state from `git status --short --branch`:

```text
## main...origin/main
 D References/<three existing WeChat image files>
?? References/The previous works/
?? References/The requirement/
```

The announcement directory is currently untracked and is owned by this target. The three deleted image files and `References/The previous works/` are unrelated and will remain untouched.

## Owner

- Target owner: Codex

## Owned Files

- `References/The requirement/Assignment announcement.md`
- `plan/2026-07-14-structure-assignment-announcement/plan.md`
- `plan/log.md`

## Read-Only Files

- Existing deleted WeChat image files under `References/`
- `References/The previous works/`

## Shared Dependencies

- No model, dataset, hardware, robot-protocol, or external-service dependency.

## Expected Work

1. Add headings and lists that reflect the announcement's sections and evaluation criteria.
2. Remove duplicated web-interface label text and correct the copied time-range encoding without dropping announcement content.
3. Restore details that were previously condensed, then validate Markdown structure and repository diff hygiene; no recorded-video validation applies to this documentation-only target.

## Validation

- `git diff --check`
- `git status --short --branch`
- Review headings, lists, and preserved requirements in the rendered Markdown source.

## Experience Signal (for human review)


## Real Robot Motion

No. This target changes documentation only and does not modify or exercise robot control.

## Commit Intent

```text
Commit: included in the user-requested consolidation of all pending project changes on `main`.
```
