# Baseline Model Assets

Downloaded and trained weights in this directory are ignored by Git. The
tracked [`manifest.yaml`](manifest.yaml) is the authority for asset identity,
task, source, checksum, license, class order, and validation state.

`yolo26s-cls.pt` is the official ImageNet-pretrained **classification** base
weight for `B-M01`. It is not a Cat Census checkpoint until it has been trained
on the frozen reviewed split and the resulting checkpoint is registered as a
separate manifest entry.

The project currently uses Ultralytics under its AGPL-3.0 academic/open-source
terms. The team must review the license before distributing a closed-source or
commercial derivative; a university demonstration does not change the license
record kept here.
