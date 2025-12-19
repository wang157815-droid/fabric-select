from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any, Dict, List

import typer


def _write_jsonl(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def _clamp_int(x: float, lo: int, hi: int) -> int:
    return max(lo, min(hi, int(round(x))))


def gen_outdoor_catalog(rng: random.Random, n: int) -> List[Dict[str, Any]]:
    base_types = [
        "20D nylon taffeta",
        "30D nylon micro-ripstop",
        "40D nylon ripstop",
        "polyester stretch woven",
        "recycled nylon plain weave",
        "nylon/poly blend ripstop",
    ]
    regions = ["CN", "VN", "TW", "KR", "JP"]
    finishes = ["C0 DWR", "C6 DWR", "wax", "none"]

    rows: List[Dict[str, Any]] = []
    for i in range(1, n + 1):
        fabric_type = rng.choice(base_types)
        region = rng.choice(regions)
        finish = rng.choice(finishes)

        # 60..180 gsm，偏轻量
        weight_gsm = _clamp_int(rng.gauss(110, 22), 60, 180)

        # 1..5 等级：偏中高，但要留出 must-fail（<4）空间
        water_repellency = rng.choices([1, 2, 3, 4, 5], weights=[3, 8, 22, 40, 27])[0]
        breathability = rng.choices([1, 2, 3, 4, 5], weights=[5, 12, 28, 32, 23])[0]
        abrasion = rng.choices([1, 2, 3, 4, 5], weights=[4, 10, 24, 35, 27])[0]
        handfeel_noise = rng.choices([1, 2, 3, 4, 5], weights=[10, 20, 28, 24, 18])[0]

        # 成本/交期：1=好(低/短), 5=差(高/长)
        cost_level = rng.choices([1, 2, 3, 4, 5], weights=[18, 30, 28, 16, 8])[0]
        lead_time_level = rng.choices([1, 2, 3, 4, 5], weights=[22, 30, 25, 15, 8])[0]

        # PFAS-free：多数满足，但确保有一定比例不满足
        pfas_free = rng.random() < 0.85

        rows.append(
            {
                "id": f"outdoor_{i:04d}",
                "scenario": "outdoor_dwr_windbreaker",
                "fabric_type": fabric_type,
                "supplier_region": region,
                "finish": finish,
                "weight_gsm": float(weight_gsm),
                "water_repellency": int(water_repellency),
                "breathability": int(breathability),
                "abrasion": int(abrasion),
                "handfeel_noise": int(handfeel_noise),
                "cost_level": int(cost_level),
                "lead_time_level": int(lead_time_level),
                "compliance": {"pfas_free": bool(pfas_free)},
            }
        )

    return rows


def gen_winter_catalog(rng: random.Random, n: int) -> List[Dict[str, Any]]:
    types = [
        "grid fleece",
        "microfleece",
        "high-loft fleece",
        "synthetic batt insulation",
        "octa knit",
        "active insulation knit",
    ]
    regions = ["CN", "VN", "ID", "KR", "JP"]

    rows: List[Dict[str, Any]] = []
    for i in range(1, n + 1):
        t = rng.choice(types)
        region = rng.choice(regions)

        # loft_or_clo：0.8..2.6，偏中高但留出 must-fail（<1.2）
        loft_or_clo = max(0.7, min(2.7, rng.gauss(1.65, 0.35)))

        wind_blocking = rng.choices([1, 2, 3, 4, 5], weights=[12, 24, 30, 22, 12])[0]
        moisture_management = rng.choices([1, 2, 3, 4, 5], weights=[6, 14, 30, 30, 20])[0]

        # bulk_weight：1=轻薄, 5=臃肿/重；与 loft 有弱相关
        bulk_base = 2.2 + (loft_or_clo - 1.4) * 1.0 + rng.gauss(0, 0.6)
        bulk_weight = _clamp_int(bulk_base, 1, 5)

        cost_level = rng.choices([1, 2, 3, 4, 5], weights=[14, 26, 30, 20, 10])[0]
        lead_time_level = rng.choices([1, 2, 3, 4, 5], weights=[18, 28, 26, 18, 10])[0]

        machine_wash = rng.random() < 0.9
        pfas_free = rng.random() < 0.9

        rows.append(
            {
                "id": f"winter_{i:04d}",
                "scenario": "winter_warm_midlayer",
                "material_type": t,
                "supplier_region": region,
                "loft_or_clo": float(round(loft_or_clo, 2)),
                "wind_blocking": int(wind_blocking),
                "moisture_management": int(moisture_management),
                "bulk_weight": int(bulk_weight),
                "cost_level": int(cost_level),
                "lead_time_level": int(lead_time_level),
                "care": {"machine_wash": bool(machine_wash)},
                "compliance": {"pfas_free": bool(pfas_free)},
            }
        )

    return rows


app = typer.Typer(add_completion=False, help="生成半合成的面料 catalog（outdoor/winter）。")


@app.command()
def main(
    seed: int = typer.Option(42, help="随机种子（保证可复现）"),
    n_outdoor: int = typer.Option(120, "--n-outdoor", help="outdoor catalog 条目数"),
    n_winter: int = typer.Option(120, "--n-winter", help="winter catalog 条目数"),
    out_dir: Path = typer.Option(Path("data"), help="输出目录"),
) -> None:
    rng = random.Random(seed)

    outdoor = gen_outdoor_catalog(rng, n_outdoor)
    winter = gen_winter_catalog(rng, n_winter)

    # 为了严格可复现：不写 wall-clock 时间戳；只写 deterministic 的 meta
    for r in outdoor:
        r["gen_version"] = 1
        r["gen_seed"] = seed
    for r in winter:
        r["gen_version"] = 1
        r["gen_seed"] = seed

    _write_jsonl(out_dir / "catalog_outdoor.jsonl", outdoor)
    _write_jsonl(out_dir / "catalog_winter.jsonl", winter)

    typer.echo(f"Wrote {len(outdoor)} -> {out_dir/'catalog_outdoor.jsonl'}")
    typer.echo(f"Wrote {len(winter)} -> {out_dir/'catalog_winter.jsonl'}")


if __name__ == "__main__":
    app()


