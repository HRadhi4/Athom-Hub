"""A backup file is not trusted: crafted ids and fields never reach the page. Run with:  python -m pytest tests"""
import importlib.util
import pathlib

spec = importlib.util.spec_from_file_location("backup", pathlib.Path(__file__).parents[1] / "custom_components" / "athom_hub" / "backup.py")
backup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(backup)

T = [9000, -4500, 560, -560, 560, -40000]


def test_crafted_ids_are_replaced():
    bad = '"><img src=x onerror=alert(1)>'
    r = backup.clean_remote({"id": bad, "name": "TV", "emitter_ir": bad, "temp_sensor": "sensor.ok_one",
                             "buttons": [{"id": bad, "name": "Power", "timings": T, "sends": "9; drop"}, {"id": "0123456789", "timings": T},
                                         {"id": "0123456789", "timings": T}, "junk", {"timings": [1, 2]}]})
    assert backup.is_id(r["id"]) and r["id"] != bad
    assert r["emitter_ir"] is None and r["temp_sensor"] == "sensor.ok_one"
    ids = [b["id"] for b in r["buttons"]]
    assert len(ids) == 3 and all(backup.is_id(i) for i in ids) and len(set(ids)) == 3
    assert ids[1] == "0123456789", "an id in our own format is kept"
    assert r["buttons"][0]["sends"] == 1


def test_good_backup_keeps_its_ids():
    r = backup.clean_remote({"id": "abcdef0123", "name": "AC", "kind": "ac", "buttons": [{"id": "1234567890", "name": "Cool", "kind": "rf", "timings": T, "sends": 3}]})
    assert r["id"] == "abcdef0123" and r["buttons"][0]["id"] == "1234567890" and r["buttons"][0]["kind"] == "rf" and r["buttons"][0]["sends"] == 3


def test_not_a_remote():
    assert backup.clean_remote("x") is None and backup.clean_remote({"name": "no buttons"}) is None
