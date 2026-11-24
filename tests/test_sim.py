from pathlib import Path
from resolverlens.cli import main
from resolverlens.sim import build_sim_bundle


def test_sim_bundle_loads_committed_datasets():
    bundle = build_sim_bundle(".")
    ds = bundle["datasets"]
    assert "main" in ds and "challenge" in ds and "fault" in ds
    assert len(ds["main"]["targets"]) == 20
    assert len(ds["challenge"]["targets"]) == 6
    c04 = next(t for t in ds["challenge"]["targets"] if t["id"] == "c04")
    assert c04["hops"] == ["t14", "t01"]


def test_sim_cli_writes_cloud_html_and_site_bundle(tmp_path: Path):
    out_file = tmp_path / "sim.html"
    site_dir = tmp_path / "_site"
    assert main(["sim", "--out", str(out_file), "--site-dir", str(site_dir)]) == 0
    assert out_file.exists() and (site_dir / "index.html").exists()
    content = out_file.read_text(encoding="utf-8")
    assert "ResolverLens Cloud Packet Tracer" in content
    assert "127.0.0.1" not in content
