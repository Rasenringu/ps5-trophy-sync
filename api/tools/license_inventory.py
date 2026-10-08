import json
import importlib.metadata as metadata
from pathlib import Path
import sys

packages=[]
for package in sorted(metadata.distributions(), key=lambda p:p.metadata['Name'].lower()):
    m=package.metadata
    license = m.get('License-Expression') or m.get('License') or '; '.join(m.get_all('Classifier') or [])
    packages.append({'name':m['Name'],'version':package.version,'license_metadata':license,
                     'license_files':[str(f) for f in package.files or [] if 'license' in str(f).lower() or 'copying' in str(f).lower()]})
web_lock=json.loads(Path('/workspace/web/package-lock.json').read_text())
web=[{'package':name,'version':data.get('version'),'license':data.get('license','See installed package notices')}
     for name,data in web_lock['packages'].items() if name]
Path(sys.argv[1]).write_text(json.dumps({'python':packages,'npm':web},indent=2)+'\n')
