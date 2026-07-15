"""The package reorganization must preserve old imports while exposing new ones."""


def test_domain_contract_legacy_import_is_compatible() -> None:
    from deskmate_baseline.contracts import FramePacket as LegacyFramePacket
    from deskmate_baseline.domain.contracts import FramePacket

    assert LegacyFramePacket is FramePacket


def test_perception_legacy_import_is_compatible() -> None:
    from deskmate_baseline.localization import route_classification_roi as legacy_route
    from deskmate_baseline.perception.localization import route_classification_roi

    assert legacy_route is route_classification_roi


def test_experiment_legacy_import_is_compatible() -> None:
    from deskmate_baseline.training import build_training_plan as legacy_build_plan
    from deskmate_baseline.experiments.training import build_training_plan

    assert legacy_build_plan is build_training_plan


def test_app_legacy_import_is_compatible() -> None:
    from deskmate_baseline.video import OpenCVFrameSource as LegacyFrameSource
    from deskmate_baseline.app.video import OpenCVFrameSource

    assert LegacyFrameSource is OpenCVFrameSource
