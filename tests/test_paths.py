import os

import pytest

from sportorg import paths


@pytest.fixture
def app_root(tmp_path, monkeypatch):
    """Point app_dir() at a temporary directory."""
    root = tmp_path / "app"
    root.mkdir()
    monkeypatch.setattr(
        paths, "app_dir", lambda *parts: os.path.join(str(root), *parts)
    )
    return root


@pytest.fixture
def package_root(tmp_path, monkeypatch):
    """Point package_dir() at a temporary stand-in for sportorg/data."""
    root = tmp_path / "package"
    for name in paths.SEEDED:
        directory = root / name
        directory.mkdir(parents=True)
        (directory / "{}.txt".format(name)).write_text("package", encoding="utf-8")

    monkeypatch.setattr(
        paths, "package_dir", lambda *parts: os.path.join(str(root), *parts)
    )
    return root


def test_app_dir_is_beside_the_executable_when_frozen(monkeypatch):
    monkeypatch.setattr(paths.sys, "frozen", True, raising=False)
    monkeypatch.setattr(
        paths.sys, "executable", os.path.join("C:", os.sep, "Prog", "SportOrg.exe")
    )

    assert paths.app_dir() == os.path.join("C:", os.sep, "Prog")
    assert paths.data_dir() == os.path.join("C:", os.sep, "Prog", "data")
    assert paths.log_dir() == os.path.join("C:", os.sep, "Prog", "logs")


def test_app_dir_is_the_repository_root_when_running_from_source(monkeypatch):
    monkeypatch.delattr(paths.sys, "frozen", raising=False)

    expected = os.path.abspath(os.path.join(os.path.dirname(paths.__file__), os.pardir))
    assert paths.app_dir() == expected


def test_working_directory_does_not_affect_resolution(tmp_path, monkeypatch):
    monkeypatch.delattr(paths.sys, "frozen", raising=False)
    before = paths.data_dir()

    monkeypatch.chdir(tmp_path)

    assert paths.data_dir() == before


def test_a_frozen_build_seeds_but_a_source_checkout_does_not(monkeypatch):
    monkeypatch.setattr(paths.sys, "frozen", True, raising=False)
    assert paths.should_seed()

    monkeypatch.delattr(paths.sys, "frozen", raising=False)
    assert not paths.should_seed()


def test_override_wins(app_root, package_root, tmp_path):
    override = tmp_path / "custom"

    assert paths.resolve_seeded("templates", override=str(override)) == str(override)


def test_data_directory_wins_over_the_package(app_root, package_root):
    (app_root / "data" / "templates").mkdir(parents=True)

    assert paths.resolve_seeded("templates") == str(app_root / "data" / "templates")


def test_falls_back_to_the_package(app_root, package_root):
    assert paths.resolve_seeded("templates") == str(package_root / "templates")
    assert paths.resolve_seeded("templates", "reports") == str(
        package_root / "templates" / "reports"
    )


def test_ensure_dirs_creates_data_and_logs(app_root):
    paths.ensure_dirs()

    assert (app_root / "data").is_dir()
    assert (app_root / "logs").is_dir()


def test_ensure_dirs_reports_an_unwritable_root(app_root, monkeypatch):
    def refuse(path, exist_ok=False):
        raise OSError(13, "Permission denied")

    monkeypatch.setattr(paths.os, "makedirs", refuse)

    with pytest.raises(paths.PathsError) as error:
        paths.ensure_dirs()

    assert error.value.path == str(app_root / "data")
    assert "Permission denied" in error.value.reason


def test_seeds_every_directory_on_a_first_run(app_root, package_root):
    paths.ensure_dirs()
    paths.seed_if_first_run()

    for name in paths.SEEDED:
        assert (app_root / "data" / name / "{}.txt".format(name)).read_text(
            encoding="utf-8"
        ) == "package"


def test_existing_settings_suppress_seeding(app_root, package_root):
    paths.ensure_dirs()
    (app_root / "data" / "settings.json").write_text("{}", encoding="utf-8")

    paths.seed_if_first_run()

    for name in paths.SEEDED:
        assert not (app_root / "data" / name).exists()


def test_existing_directory_is_left_alone(app_root, package_root):
    paths.ensure_dirs()
    configs = app_root / "data" / "configs"
    configs.mkdir()
    edited = configs / "configs.txt"
    edited.write_text("edited by the operator", encoding="utf-8")

    paths.seed_if_first_run()

    assert edited.read_text(encoding="utf-8") == "edited by the operator"
    # the other two are judged independently and still get seeded
    assert (app_root / "data" / "templates" / "templates.txt").exists()


def test_settings_and_directory_both_present_seeds_nothing(app_root, package_root):
    paths.ensure_dirs()
    (app_root / "data" / "settings.json").write_text("{}", encoding="utf-8")
    (app_root / "data" / "configs").mkdir()

    paths.seed_if_first_run()

    assert list((app_root / "data" / "configs").iterdir()) == []


def test_copy_failure_is_not_fatal(app_root, package_root, monkeypatch, caplog):
    def refuse(source, target):
        raise OSError(28, "No space left on device")

    monkeypatch.setattr(paths.shutil, "copytree", refuse)
    paths.ensure_dirs()

    paths.seed_if_first_run()

    assert "No space left on device" in caplog.text


def test_missing_package_directory_is_not_fatal(app_root, package_root, caplog):
    paths.ensure_dirs()
    for name in paths.SEEDED:
        for entry in (package_root / name).iterdir():
            entry.unlink()
        (package_root / name).rmdir()

    paths.seed_if_first_run()

    assert "is missing" in caplog.text
