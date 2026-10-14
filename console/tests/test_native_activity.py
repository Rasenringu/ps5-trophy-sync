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
 for title,name in [('PPSA74207','MOCK Simpsons recomp'),('PPSA99902','MOCK Sonic recomp')]:
  metadata=root/'appmeta'/title;metadata.mkdir()
  (metadata/'param.json').write_text(json.dumps({'titleId':title,'localizedParameters':{'en-US':{'titleName':name}}}))
  row('ApplicationSessionEnd','MOCK_'+title,240,extra={'appTitleId':title})
 row('ApplicationSessionEnd','MOCK_PS4',360,extra={'appTitleId':'CUSA03804'})
 db.commit();db.close();before=path.read_bytes()
 env={**os.environ,'MOCK_METADATA_ROOT':str(root/'appmeta')}
 result=subprocess.run([sys.argv[1],str(path)],env=env,capture_output=True,text=True,check=True)
 bodies=[json.loads(line) for line in result.stdout.splitlines()];activities=[a for b in bodies for a in b['activities']]
 assert all(b['schema_version']==3 and b['profile_binding']=='activity_header_single_local_user' for b in bodies)
 assert len(activities)==9
 complete=[a for a in activities if a['complete']];assert len(complete)==4
 assert next(a for a in complete if a['title_id']=='PPSA12345')['duration_seconds']==180
 assert next(a for a in complete if a['title_id']=='CUSA03804')['title']=='CUSA03804'
 assert {a['title'] for a in complete if a['title_id'] in ('PPSA74207','PPSA99902')}=={'MOCK Simpsons recomp','MOCK Sonic recomp'}
 assert all(a['clock']=='uncertain' and a['duration_basis']=='native_foreground_seconds' for a in activities)
 assert all(a['duration_seconds'] is None for a in activities if not a['complete'])
 assert 'PRIVATE_' not in result.stdout and 'MOCK_ONE' not in result.stdout
 assert path.read_bytes()==before and not Path(str(path)+'-journal').exists()
 # Actual console-observed shell schema, independent optional name source.
 shell=root/'shell.db';db=sqlite3.connect(shell)
 db.execute('CREATE TABLE tbl_contentinfo(titleId TEXT,titleName TEXT)')
 db.execute('INSERT INTO tbl_contentinfo VALUES(?,?)',('CUSA03804','MOCK Attack on Titan'))
 db.commit();db.close();shell_before=shell.read_bytes()
 named_env={**env,'MOCK_APP_DB':str(shell)}
 result=subprocess.run([sys.argv[1],str(path)],env=named_env,capture_output=True,text=True,check=True)
 named=[a for line in result.stdout.splitlines() for a in json.loads(line)['activities']]
 assert next(a for a in named if a['title_id']=='CUSA03804')['title']=='MOCK Attack on Titan'
 assert shell.read_bytes()==shell_before and not Path(str(shell)+'-journal').exists()
 # Conflicting labels cannot pick an arbitrary title; native session remains.
 db=sqlite3.connect(shell);db.execute('INSERT INTO tbl_contentinfo VALUES(?,?)',('CUSA03804','MOCK conflict'));db.commit();db.close()
 result=subprocess.run([sys.argv[1],str(path)],env=named_env,capture_output=True,text=True,check=True)
 named=[a for line in result.stdout.splitlines() for a in json.loads(line)['activities']]
 assert next(a for a in named if a['title_id']=='CUSA03804')['title']=='CUSA03804'
 # Metadata identity mismatch is rejected, not silently relabeled.
 (meta/'param.json').write_text(json.dumps({'titleId':'PPSA54321','localizedParameters':{'en-US':{'titleName':'MOCK GAME'}}}))
 result=subprocess.run([sys.argv[1],str(path)],env=env,capture_output=True,text=True,check=True)
 assert 'PPSA12345' not in result.stdout and 'sessions=3' in result.stderr
print('PASS LOCAL native activity: End/Bi deduplication, monotonic session counters, incomplete/crashed/invalid records, exact single-profile gate, metadata identity, privacy, source unchanged.')
