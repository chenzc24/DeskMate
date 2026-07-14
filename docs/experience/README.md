# Experience Notes

`docs/experience/` stores reusable project lessons extracted from plans, logs,
commits, reviews, validation reports, and failed attempts. It is not a second
maintenance log.

## What Belongs Here

A note explains a transferable judgment:

- what assumption was tested;
- what happened;
- what evidence supports the conclusion;
- what rule, template, validation command, or habit should change;
- where the lesson does and does not apply.

Raw changed-file lists, commit messages, daily status updates, and validation
transcripts without interpretation belong in `plan/log.md`, Git history, or a
status report.

## Human And Agent Responsibilities

A human decides whether work produced a reusable lesson and when to request
extraction. An Agent may surface a possible signal and, when asked, draft a
candidate note with evidence. The human accepts, edits, or rejects it.

## Workflow

1. Target plans and `plan/log.md` record facts first.
2. A human reviews evidence and decides whether to request a lesson.
3. The Agent drafts a candidate from `lesson.template.md` and cites evidence.
4. The human accepts, edits, or rejects the note.
5. Mature lessons may update `AGENTS.md`, templates, validation, or review
   practices.

Use short dated names for event-specific lessons:

```text
YYYY-MM-DD-short-lesson-title.md
```
