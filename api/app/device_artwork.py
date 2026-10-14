"""Authenticated, profile-scoped package cache; never changes unlock records."""
import hashlib
from sqlalchemy import select, delete
from .models import Record, DevicePackage, DeviceArtwork
from .console_artwork import png, read_artwork, read_trophy_info, read_localized_text

def application_imported(db, profile, title):
    return db.scalar(select(Record.id).where(Record.profile==profile,
        Record.source=='ps5_native',Record.mock==False,Record.kind=='activity',
        Record.data['title_id'].as_string()==title,
        Record.data['duration_basis'].as_string()=='native_foreground_seconds',
        Record.data['consistency'].as_string()=='sqlite_read_transaction',
        Record.data['profile_binding'].as_string()=='activity_header_single_local_user').limit(1)) is not None

def store_application_image(db, profile, title, raw):
    if not application_imported(db,profile,title):
        raise PermissionError('Import this profile application activity before its artwork')
    content=png(raw)
    sha=hashlib.sha256(content).hexdigest()
    identity=hashlib.sha256((profile+':'+title+':').encode()).hexdigest()
    image=db.get(DeviceArtwork,identity)
    if image:image.digest,image.content=sha,content
    else:db.add(DeviceArtwork(id=identity,profile=profile,title_id=title,trophy_id='',digest=sha,content=content))
    return title,sha

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

def store_ps4_package(db,profile,title,raw):
    from .ps4_artwork import read_package
    metadata,images=read_package(raw,title)
    rows=list(db.scalars(select(Record).where(Record.profile==profile,Record.source=='ps4_bc',Record.mock==False,
        Record.kind=='trophy',Record.data['title_id'].as_string()==title)))
    if not rows or any(r.data['trophy_id'] not in metadata['info'] or
        r.data.get('ps4_observation',{}).get('trp_sha1')!=metadata['trp_sha1'] or
        r.data['grade']!=metadata['grades'][r.data['trophy_id']] for r in rows):
        raise PermissionError('Import matching PS4 state before its package')
    sha=hashlib.sha256(raw).hexdigest();old=db.get(DevicePackage,(profile,title))
    if old and old.digest==sha and old.metadata_json.get('format')=='ps4_trp_v3':return title,sha
    if old:old.digest,old.metadata_json=sha,metadata
    else:db.add(DevicePackage(profile=profile,title_id=title,digest=sha,metadata_json=metadata))
    db.execute(delete(DeviceArtwork).where(DeviceArtwork.profile==profile,DeviceArtwork.title_id==title))
    for trophy,content in images.items():
        identity=hashlib.sha256((profile+':'+title+':'+trophy).encode()).hexdigest()
        db.add(DeviceArtwork(id=identity,profile=profile,title_id=title,trophy_id=trophy,digest=hashlib.sha256(content).hexdigest(),content=content))
    return title,sha
