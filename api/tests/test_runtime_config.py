"""Production startup must reject development/insecure configuration."""
import os
import subprocess
import sys
import pytest

@pytest.mark.parametrize('change',[
    {'WEB_ORIGIN':'http://trophysync.example'},
    {'COOKIE_SECURE':'false'},
    {'ENABLE_DEVELOPMENT_TOOLS':'true'},
    {'WEB_ORIGIN':'https://trophysync.example/path'},
])
def test_production_rejects_insecure_runtime(change):
    settings={**os.environ,'ENVIRONMENT':'production','WEB_ORIGIN':'https://trophysync.example',
              'COOKIE_SECURE':'true','ENABLE_DEVELOPMENT_TOOLS':'false',**change}
    result=subprocess.run([sys.executable,'-c','import app.main'],env=settings,capture_output=True,text=True)
    assert result.returncode!=0
    assert 'Production requires an HTTPS origin' in result.stderr

def test_production_accepts_secure_runtime():
    settings={**os.environ,'ENVIRONMENT':'production','WEB_ORIGIN':'https://trophysync.example',
              'COOKIE_SECURE':'true','ENABLE_DEVELOPMENT_TOOLS':'false'}
    result=subprocess.run([sys.executable,'-c','import app.main'],env=settings,capture_output=True,text=True)
    assert result.returncode==0,result.stderr
