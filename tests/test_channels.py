import pytest

from automation import channels


def test_registry_is_structurally_valid():
    channels.validate()  # raises AssertionError on any malformed job


def test_all_channel_names_are_known():
    for job in channels.JOBS.values():
        assert job.primary in channels.CHANNELS
        for fb in job.fallbacks:
            assert fb in channels.CHANNELS


def test_select_unknown_lists_known():
    with pytest.raises(KeyError) as exc:
        channels.select("nope.nope")
    assert "known job" in str(exc.value).lower()


def test_gui_only_param_uses_als_then_uia_and_is_verified():
    job = channels.select("device.param_gui_only")
    assert job.primary == "als"
    assert "uia" in job.fallbacks
    assert job.verified is True


def test_by_channel_primary_only_vs_with_fallbacks():
    prim = channels.by_channel("als")
    assert any(j.id == "device.param_gui_only" for j in prim)

    with_fb = channels.by_channel("uia", include_fallbacks=True)
    ids = {j.id for j in with_fb}
    assert "device.param_gui_only" in ids          # uia is a fallback here
    assert "track.arm_monitor" in ids               # uia is primary here


def test_by_channel_rejects_unknown():
    with pytest.raises(ValueError):
        channels.by_channel("telepathy")


def test_matrix_is_sorted_by_area_then_id():
    rows = channels.matrix()
    keys = [(r["area"], r["id"]) for r in rows]
    assert keys == sorted(keys)
    assert all(r["primary"] in channels.CHANNELS for r in rows)


def test_export_is_a_handoff_not_uia():
    job = channels.select("file.export_render")
    assert job.primary == "handoff"
    assert "uia" in job.fallbacks


def test_no_job_uses_sdk_future_without_an_upgrade_requirement():
    for job in channels.by_channel("sdk_future"):
        assert "12.4.5" in job.requires
