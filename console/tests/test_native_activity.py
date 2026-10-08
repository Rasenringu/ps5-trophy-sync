"""Synthetic session semantics, privacy and locked-source tests; no PS5 access."""
import json,os,sqlite3,subprocess,sys,tempfile
from pathlib import Path
with tempfile.TemporaryDirectory() as folder:
 root=Path(folder);path=root/'activity.db';meta=root/'appmeta/PPSA12345';meta.mkdir(parents=True)
 (meta/'param.json').write_text(json.dumps({'titleId':'PPSA12345','localizedParameters':{'en-US':{'titleName':'MOCK GAME'}}}))
 db=sqlite3.connect(path);db.execute('CREATE TABLE tbl_log(created_date TEXT,event_id TEXT,log TEXT,log_header TEXT)')
 def row(event,session,seconds=None,user='12345678',extra=None):
  body={'appTitleId':'PPSA12345','appSessionId':session,'psnSecret':'PRIVATE_DO_NOT_EXPORT'}
  if seconds is not None:body['fgTime']=seconds
  if extra:body.update(extra)
  db.execute('INSERT INTO tbl_log VALUES(?,?,?,?)',('2026-10-08T10:00:00Z',event,json.dumps(body),json.dumps({'localUserIds':user if isinstance(user,list) else [user],'psnAccountIds':['PRIVATE_ACCOUNT']})))
 row('ApplicationSessionStart','MOCK_ONE')
 row('ApplicationSessionEnd','MOCK_ONE',120)
 row('ApplicationSessionEndBi','MOCK_ONE',120)  # Duplicate analytics variant ignored.
 row('ApplicationSessionEnd','MOCK_ONE',180)  # Cumulative replay: max, never sum.
 row('ApplicationSessionEnd','MOCK_ONE',60)   # Older observation cannot reduce.
 row('ApplicationSessionEnd','MOCK_DECIMAL_ALIAS',999,user='305419896')
 row('ApplicationSessionEnd','MOCK_PREFIXED_ALIAS',999,user='0x12345678')
 row('ApplicationSessionEnd','MOCK_NUMERIC_ALIAS',999,user=305419896)
 row('ApplicationSessionStart','MOCK_MISSING')
 row('ApplicationSessionCrash','MOCK_CRASH')
 row('ApplicationSessionEnd','MOCK_OTHER_USER',99,user='87654321')
 row('ApplicationSessionEnd','MOCK_MULTI_USER',99,user=['12345678','87654321'])
 row('ApplicationSessionEnd','MOCK_BAD_COUNTER',-1)
 row('ApplicationSessionEnd','MOCK_BAD_TYPE','120')
 row('ApplicationSessionEnd','MOCK_TOO_LARGE',604801)
 db.commit();db.close();before=path.read_bytes()
 env={**os.environ,'MOCK_METADATA_ROOT':str(root/'appmeta')}
 result=subprocess.run([sys.argv[1],str(path)],env=env,capture_output=True,text=True,check=True)
 bodies=[json.loads(line) for line in result.stdout.splitlines()];activities=[a for b in bodies for a in b['activities']]
 assert all(b['schema_version']==3 and b['profile_binding']=='activity_header_single_local_user' for b in bodies)
 assert len(activities)==6
 complete=[a for a in activities if a['complete']];assert len(complete)==1 and complete[0]['duration_seconds']==180
 assert all(a['clock']=='uncertain' and a['duration_basis']=='native_foreground_seconds' for a in activities)
 assert all(a['duration_seconds'] is None for a in activities if not a['complete'])
 assert 'PRIVATE_' not in result.stdout and 'MOCK_ONE' not in result.stdout
 assert path.read_bytes()==before and not Path(str(path)+'-journal').exists()
 # Metadata identity mismatch is rejected, not silently relabeled.
 (meta/'param.json').write_text(json.dumps({'titleId':'PPSA54321','localizedParameters':{'en-US':{'titleName':'MOCK GAME'}}}))
 result=subprocess.run([sys.argv[1],str(path)],env=env,capture_output=True,text=True,check=True)
 assert not result.stdout and 'sessions=0' in result.stderr
print('PASS LOCAL native activity: End/Bi deduplication, monotonic session counters, incomplete/crashed/invalid records, exact single-profile gate, metadata identity, privacy, source unchanged.')
