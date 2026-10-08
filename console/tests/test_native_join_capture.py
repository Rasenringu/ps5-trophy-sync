"""Private reference only; no console access and no raw names/IDs printed."""
from pathlib import Path
import json,subprocess,sys
cli=Path(sys.argv[1]);base=Path(sys.argv[2])
index_file=base/'definition-capture-index.json'
if index_file.exists():
    index=json.loads(index_file.read_text(encoding='utf-8'))
    matches=[item for item in index if item.get('naruto_reference_match') is True]
    assert len(matches)==1
    number=matches[0]['capture_index'];assert isinstance(number,int) and 0<=number<32
    result=subprocess.run([str(cli),str(base/f'definitions-{number}.ucp'),str(base/'naruto-state-investigation.dat')],capture_output=True,text=True)
    assert result.returncode==0,result.stderr
    actual=json.loads(result.stdout)
    assert actual=={'rc':0,'earned':6,'locked':39,'unknown':0,'bronze':6,'silver':0,'gold':0,'platinum':0},actual
    print('PASS private native join: real state IDs match definitions; reference six earned all bronze, 39 locked. No import or live snapshot guarantee.')
else:print('SKIP private native join reference: capture absent.')
