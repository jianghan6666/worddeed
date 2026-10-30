"""生成 MANIFEST.json：包内全部交付文件的相对路径、大小与 SHA-256（不含 rerun/、__pycache__/ 与 MANIFEST 自身）。

用法（包根目录）：python code/tools/make_manifest.py
"""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKIP_DIRS = {"rerun", "__pycache__"}

files = []
for p in sorted(ROOT.rglob("*")):
    rel = p.relative_to(ROOT)
    if not p.is_file() or rel.name == "MANIFEST.json" or SKIP_DIRS & set(rel.parts):
        continue
    files.append({"path": rel.as_posix(), "bytes": p.stat().st_size,
                  "sha256": hashlib.sha256(p.read_bytes()).hexdigest()})
(ROOT / "MANIFEST.json").write_text(json.dumps({"n_files": len(files), "files": files}, indent=1), encoding="utf-8")
print(f"MANIFEST.json：{len(files)} 个文件，共 {sum(f['bytes'] for f in files) / 1e6:.1f} MB")
