"""Execute one adapter in the configured numerical environment."""

import json
import shutil
import sys
from pathlib import Path

from .workflow import sha, write_json


def execute(request):
    stage, config, out = request["stage"], request["config"], Path(request["out"])
    previous = request["artifacts"]
    if stage == "step1":
        from .step1 import run
        return run(config, out)
    if stage == "step2":
        if config["profile"] == "reproduce":
            source = Path(config["selection"])
            selection = json.loads(source.read_text())
            catalogue = Path(previous["step1"]["catalogue"])
            if (selection.get("topic_model_id") != previous["step1"]["topic_model_id"]
                    or selection.get("catalogue_sha256") != sha(catalogue)):
                raise ValueError("Saved selection belongs to a different topic model or catalogue")
            final = selection["final"]
            ids = [i for key in ("relevant", "irrelevant", "unresolved") for i in final[key]]
            if len(ids) != 354 or set(ids) != {str(i) for i in range(354)}:
                raise ValueError("Saved selection must partition all 354 topics exactly once")
            selected = out / "selected_topics.json"
            if selected.exists() and selected.read_bytes() != source.read_bytes():
                raise ValueError("Existing selection differs from the configured selection")
            shutil.copyfile(source, selected)
            return {"selection": str(selected), "mode": "saved_primary_selection"}
        from .screening import run
        result = run(config, out)
        # A fresh selection must be tied to the same Stage 1 catalogue.
        selected = json.loads(Path(result["selection"]).read_text())
        if (selected.get("topic_model_id") != previous["step1"]["topic_model_id"]
                or selected.get("catalogue_sha256") != sha(previous["step1"]["catalogue"])):
            raise ValueError("Fresh screening and Stage 1 catalogue identities differ")
        return result
    if stage == "step3":
        from .step3 import run
        config["step3"].update({k: previous["step1"][k] for k in ("topics", "components")})
        return run(config, out, Path(previous["step2"]["selection"]))
    if stage == "step4_prepare":
        from .step4 import prepare
        return prepare(config, out, Path(previous["step3"]["scores"]), Path(previous["step3"]["panel"]))
    if stage == "step4":
        from .step4 import estimate
        return estimate(config, out.parent / "step4_prepare")
    raise ValueError(stage)


if __name__ == "__main__":
    write_json(Path(sys.argv[2]), execute(json.loads(Path(sys.argv[1]).read_text())))
