"""Real SQLite generated LOCAL fixtures; no console data or connections."""
import hashlib
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

cli=sys.argv[1]
def inventory(root):
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in root.iterdir() if p.is_file()}
def run(path):
    return subprocess.check_output([cli,str(path)],text=True,timeout=5).strip().split()
with tempfile.TemporaryDirectory(prefix='MOCK-schema-') as temp:
    root=Path(temp); db=root/'activity.db'
    c=sqlite3.connect(db)
    c.execute('CREATE TABLE tbl_log(created_date TEXT,log TEXT)')
    c.execute('INSERT INTO tbl_log VALUES (?,?)',('MOCK_DATE','MOCK_PRIVATE_PROFILE_12345678'))
    c.commit();c.close()
    before=inventory(root)
    assert run(db)==['0','1','1','1','1','delete']
    assert inventory(root)==before, 'Read-only probe changed source bytes/sidecars'
    alias=root/'source-alias.db';alias.symlink_to(db)
    linked=root/'directory-alias';linked.symlink_to(root,target_is_directory=True)
    before=inventory(root)
    assert run(alias)[0]!='0', 'Final source symlink must fail closed'
    assert run(linked/'activity.db')[0]!='0', 'Intermediate directory symlink must fail closed'
    assert inventory(root)==before
    alias.unlink();linked.unlink();before=inventory(root)
    missing=root/'absent.db';assert run(missing)[0]!='0' and not missing.exists()
    # A real writer holding EXCLUSIVE must cause a bounded failure, no unlocked read.
    writer=sqlite3.connect(db);writer.execute('BEGIN EXCLUSIVE')
    assert run(db)[0]!='0';assert inventory(root)==before
    writer.rollback();writer.close()
    wal=sqlite3.connect(db);wal.execute('PRAGMA journal_mode=WAL')
    wal.execute('INSERT INTO tbl_log VALUES (?,?)',('MOCK','MOCK_UNCOMMITTED_SNAPSHOT'));wal.commit()
    before=inventory(root);assert run(db)[0]!='0';assert inventory(root)==before
    wal.close()
    # Recovery of a hot rollback journal must fail without changing any file.
    hot=root/'hot.db'
    with sqlite3.connect(hot) as init:
        init.execute('CREATE TABLE tbl_log(created_date,log)')
        init.executemany('INSERT INTO tbl_log VALUES (?,?)',[(str(i),'MOCK'*100) for i in range(1000)])
    subprocess.run([sys.executable,'-c',
        'import sqlite3,os,sys; c=sqlite3.connect(sys.argv[1]); c.execute("PRAGMA cache_size=5"); c.execute("BEGIN IMMEDIATE"); c.execute("UPDATE tbl_log SET log=log||log"); os._exit(0)',str(hot)],check=True)
    assert Path(str(hot)+'-journal').exists()
    before=inventory(root);assert run(hot)[0]!='0';assert inventory(root)==before
print('PASS LOCAL SQLite: transaction/schema, symlink refusal, missing file, exclusive writer, WAL refusal, hot-journal refusal; all bytes/sidecars unchanged.')
