import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"apps/api"))
from app.main import app
out=Path(__file__).resolve().parents[1]/'packages/shared-contracts/openapi.json'
out.write_text(json.dumps(app.openapi(),indent=2))
print(out)
