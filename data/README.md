# Baseline Data Workspace

Raw and downloaded images are local artifacts and must not be committed. The
tracked `manifests/source_manifest.template.csv` defines the provenance and
split contract used by the Phase 0 auditor.

The official five target labels are:

```text
ragdoll / singapura / persian / sphynx / pallas
```

`not_target` is an internal rejection output. Keep its 300–600 grouped negative
images separate from the five target-cat report counts. Assignment example
images under `References/The requirement/` are smoke-test inputs only and must
never enter training or validation manifests.

Recommended local layout:

```text
data/
├── manifests/
├── raw/                 # ignored
├── downloads/           # ignored
└── cat_census/          # add to ignore before materializing
```

Run an audit with:

```powershell
python scripts/audit_source_manifest.py data/manifests/source_manifest.csv
```
