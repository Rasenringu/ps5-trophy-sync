"""Authenticated, profile-scoped package cache; never changes unlock records."""
import hashlib
from sqlalchemy import select, delete
from .models import Record, DevicePackage, DeviceArtwork
from .console_artwork import read_artwork, read_trophy_info, read_localized_text

def store_package(db, profile, raw):
    title,images=read_artwork(raw)
    info_title,info=read_trophy_info(raw)
    text_title,texts,default=read_localized_text(raw)
    if info_title!=title or text_title!=title:
        raise ValueError('Package identities differ')
    known={r.data['trophy_id'] for r in db.scalars(select(Record).where(
        Record.profile==profile, Record.source=='ps5_native', Record.mock==False,
        Record.kind=='trophy', Record.data['title_id'].as_string()==title))}
    if not known or not known.issubset(info):
        raise PermissionError('Import this profile trophy set before its artwork')
    sha=hashlib.sha256(raw).hexdigest()
    old=db.get(DevicePackage,(profile,title))
    if old and old.digest==sha:
        return title,sha
    metadata={'info':info,'texts':texts,'default':default}
    if old:old.digest,old.metadata_json=sha,metadata
    else:db.add(DevicePackage(profile=profile,title_id=title,digest=sha,metadata_json=metadata))
    db.execute(delete(DeviceArtwork).where(DeviceArtwork.profile==profile,DeviceArtwork.title_id==title))
    for trophy,content in images.items():
        identity=hashlib.sha256((profile+':'+title+':'+trophy).encode()).hexdigest()
        db.add(DeviceArtwork(id=identity,profile=profile,title_id=title,trophy_id=trophy,
            digest=hashlib.sha256(content).hexdigest(),content=content))
    return title,sha
