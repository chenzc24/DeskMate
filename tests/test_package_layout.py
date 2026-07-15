"""The package layout exposes each responsibility from its canonical package."""


def test_domain_contract_is_available() -> None:
    from deskmate_baseline.domain.contracts import FramePacket

    assert FramePacket.__module__ == "deskmate_baseline.domain.contracts"


def test_perception_route_is_available() -> None:
    from deskmate_baseline.perception.localization import route_classification_roi

    assert callable(route_classification_roi)


def test_experiment_training_is_available() -> None:
    from deskmate_baseline.experiments.training import build_training_plan

    assert callable(build_training_plan)


def test_app_video_is_available() -> None:
    from deskmate_baseline.app.video import OpenCVFrameSource

    assert OpenCVFrameSource.__module__ == "deskmate_baseline.app.video"
