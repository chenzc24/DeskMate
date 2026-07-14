# Transcribe Requirement Documents to Markdown

## Goal

Create complete Markdown transcriptions of the supplied baseline SOP, assignment brief, and assignment answer-book documents, preserving all source information without summarization.

## Dirty-State Note

Start state from `git status --short --branch`:

```text
## main...origin/main
 D References/<three existing WeChat image files>
?? References/The previous works/
?? References/The requirement/
?? plan/2026-07-14-structure-assignment-announcement/
```

The requirement source directory is untracked and in scope. The deleted WeChat images, previous-work references, and assignment-announcement target remain read-only.

## Owner

- Target owner: Codex

## Owned Files

- `References/The requirement/Baseline SOP.md`
- `References/The requirement/SWS3009A_Assg.md`
- `References/The requirement/SWS3009A_AssgAnsBk.md`
- `References/The requirement/SWS3009A_Assg_assets/`
- `plan/2026-07-14-transcribe-requirement-documents/plan.md`
- `plan/log.md`

## Read-Only Files

- `References/The requirement/Baseline SOP.pdf`
- `References/The requirement/SWS3009A_Assg.pdf`
- `References/The requirement/SWS3009A_AssgAnsBk.docx`
- Existing deleted WeChat image files under `References/`
- `References/The previous works/`
- `plan/2026-07-14-structure-assignment-announcement/`

## Shared Dependencies

- PDF text extraction and page rendering tools.
- DOCX extraction and rendering tools.
- No model, dataset, hardware, robot-protocol, or real-motion dependency.

## Expected Work

1. Extract text, tables, and embedded/visible content from each source document.
2. Reconstruct the source content in Markdown with source filenames and page boundaries where helpful for traceability.
3. Render/review source pages and compare extracted content against each source before recording validation results.

## Validation

- `git diff --check`
- `git status --short --branch`
- Extracted-text coverage check for each PDF and DOCX.
- Rendered source-page review for visual-only content, tables, and layout-dependent text.

## Validation Results

- Extracted all two pages of `Baseline SOP.pdf` and retained both source tables and page boundaries.
- Extracted all two pages of `SWS3009A_Assg.pdf`, including the assignment URL and its five embedded cat-example images.
- Extracted all 34 paragraphs of `SWS3009A_AssgAnsBk.docx`; the document contains no tables, inline images, headers, or footers.
- Source PDF pages were rendered and reviewed. The supplied DOCX renderer could not run because LibreOffice is unavailable in this environment; its text, paragraph styles, headers/footers, tables, and inline-image structure were inspected directly instead.
- `plan/log.md` became dirty after this target began and was left read-only to avoid overwriting unrelated work; these results are recorded here instead.
- A completeness review corrected the literal `\\n\\n` sequence in the scoring-table Speed cell to a Markdown-compatible paragraph break.
- The DOCX visual review confirmed one page, a centered automatic page-number footer, and numbered response prompts; the Markdown now preserves those elements.
- PDF font-run inspection added the source bold emphasis to the Baseline SOP transcription.

## Experience Signal (for human review)


## Real Robot Motion

No. This target only adds document transcriptions.

## Commit Intent

```text
Commit: `Transcribe requirement documents to Markdown`.
```
