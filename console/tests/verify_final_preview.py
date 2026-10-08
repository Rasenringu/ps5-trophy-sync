"""Independent QR/expiry check on host-rendered synthetic screens."""
from pathlib import Path
from PIL import Image
import zxingcpp

root=Path('/workspace/artifacts/console/final-ui/previews')
for state in ('pairing','expired','connected','syncing','connecting','error','long','partial'):
    preview=Image.open(root/f'{state}.ppm')
    assert preview.size==(1920,1080)
    qr=zxingcpp.read_barcodes(preview)
    if state=='pairing':
        assert len(qr)==1 and qr[0].text=='https://example.invalid/pair?code=DEMO-2345'
    else:
        assert not qr,f'{state}: stale authorization QR'
    preview.save(root/f'{state}.png')
print('PASS eight synthetic native renders: exact independent QR decode, expiry/completed/error removal, full-size PNG previews.')
