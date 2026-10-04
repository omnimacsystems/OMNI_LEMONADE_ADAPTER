import argparse
import json
from pathlib import Path
from .core import SCENARIOS, Hold, run, digest
from .runtime import Client, preflight

ROOT=Path(__file__).resolve().parent.parent


def main():
    p=argparse.ArgumentParser(description="Standalone Lemonade synthetic qualification; one explicit run, no retries")
    sub=p.add_subparsers(dest="command",required=True)
    r=sub.add_parser("run")
    r.add_argument("scenario",choices=SCENARIOS)
    r.add_argument("--endpoint",required=True)
    r.add_argument("--lemonade-dir",required=True)
    r.add_argument("--backend-dir",required=True)
    r.add_argument("--model",required=True)
    r.add_argument("--output",required=True)
    v=sub.add_parser("verify-seal");v.add_argument("directory")
    a=p.parse_args()
    if a.command=="verify-seal":
        folder=Path(a.directory);seal=json.loads((folder/"SEAL.json").read_text())
        valid=all(Path(k).name==k and (folder/k).is_file() and digest((folder/k).read_bytes())==h for k,h in seal.items())
        valid=valid and set(seal)=={f.name for f in folder.iterdir() if f.is_file() and f.name!="SEAL.json"}
        print("PASS" if valid else "FAIL");return 0 if valid else 1
    try:
        lock=json.loads((ROOT/"config/runtime-lock.json").read_text())
        config=json.loads((ROOT/"config/agent.json").read_text())
        client=Client(a.endpoint,lock["api_model_id"],lock["fingerprint"])
        template,identity=preflight(client,lock,a.lemonade_dir,a.backend_dir,a.model)
        report,out=run(a.scenario,client,template,config,
                       json.loads((ROOT/"corpus/documents.json").read_text()),
                       json.loads((ROOT/"corpus/answer_key.json").read_text()),a.output,identity)
        print(json.dumps({"report":str(out/"report.json"),"final_verdict":report["final_verdict"],
                          "scenario_verdict":report["scenario_verdict"],"hold_reason":report["hold_reason"]}))
        return 0 if report["scenario_verdict"]=="PASS" else 1
    except (Hold,OSError,ValueError) as exc:
        print("PREFLIGHT_HOLD",str(exc));return 2


if __name__=="__main__":
    raise SystemExit(main())
