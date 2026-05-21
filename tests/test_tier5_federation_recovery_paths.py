from transmission_layers.intelligence.tier5.federation_recovery_paths import federation_recovery_paths


def test_recovery_paths_deterministic_and_bounded():
    paths=[{"path_id":"2","source":"B","target":"C","contained":False},{"path_id":"1","source":"A","target":"B","contained":True}]
    snaps=[{"snapshot_id":"2","state":"degraded"},{"snapshot_id":"1","state":"ok"}]
    a=federation_recovery_paths(paths,snaps)
    b=federation_recovery_paths(list(reversed(paths)),list(reversed(snaps)))
    assert a==b
    assert 0<=a["federation_recovery_path_score"]<=1
