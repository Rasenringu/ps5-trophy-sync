import json
import sys
from pathlib import Path
from app.main import app
from app.contracts import Snapshot, NativeSnapshot, NativeActivitySnapshot

target = Path(sys.argv[1])
target.mkdir(parents=True, exist_ok=True)
(target / 'openapi.json').write_text(json.dumps(app.openapi(), indent=2)+'\n')
(target / 'snapshot-v1.schema.json').write_text(json.dumps(Snapshot.model_json_schema(), indent=2)+'\n')
(target / 'snapshot-v2.schema.json').write_text(json.dumps(NativeSnapshot.model_json_schema(), indent=2)+'\n')
(target / 'snapshot-v3.schema.json').write_text(json.dumps(NativeActivitySnapshot.model_json_schema(), indent=2)+'\n')
