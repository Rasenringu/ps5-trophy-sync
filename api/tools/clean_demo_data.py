"""Remove provable local demo fixtures after an explicit database backup.

Never selects accounts with non-mock records or deletes revoked real profiles.
Default is read-only. No console is contacted.
"""
import argparse
import json
import re
from pathlib import Path
from sqlalchemy import select,delete,func,or_
from app.db import Session
from app.models import Account,Login,SocialProfile,Friendship,Profile,Pairing,Record,Import,DevicePackage,DeviceArtwork,Installation

parser=argparse.ArgumentParser()
parser.add_argument('--apply',action='store_true')
parser.add_argument('--backup',type=Path)
args=parser.parse_args()
if args.apply:
    if not args.backup or not args.backup.is_file() or args.backup.stat().st_size<100:
        parser.error('Apply requires a verified local PostgreSQL custom-format backup')
    with args.backup.open('rb') as capture:
        if capture.read(5)!=b'PGDMP':parser.error('Backup is not PostgreSQL custom format')

pattern=re.compile(r'(?:browser-test-[0-9a-f-]{36}|local-guide-test-[0-9a-f-]{36}|friend_[ab]_[0-9a-f]{12})@example\.test')
with Session() as db:
    real_before=db.scalar(select(func.count()).select_from(Record).where(Record.mock==False))
    real_owners=set(db.scalars(select(Profile.owner).join(Record,Record.profile==Profile.id).where(Record.mock==False)))
    accounts={a.id for a in db.scalars(select(Account)) if pattern.fullmatch(a.email) and a.id not in real_owners}
    protected=set(db.scalars(select(Record.profile).where(Record.mock==False)))
    profiles=[p for p in db.scalars(select(Profile)) if p.id not in protected and
        (p.owner in accounts or (p.local_id.startswith('MOCK') and p.label.startswith('MOCK')))]
    ids={p.id for p in profiles};installations={p.installation for p in profiles}
    result={'mode':'apply' if args.apply else 'dry-run','generated_accounts':len(accounts),
        'demo_profiles':len(ids),'mock_records':db.scalar(select(func.count()).select_from(Record).where(Record.mock==True)),
        'mock_imports':db.scalar(select(func.count()).select_from(Import).where(Import.mock==True)),
        'native_records_preserved':real_before}
    if args.apply:
        db.execute(delete(Record).where(Record.mock==True))
        db.execute(delete(Import).where(Import.mock==True))
        for model in (DeviceArtwork,DevicePackage,Pairing,Import):
            db.execute(delete(model).where(model.profile.in_(ids)))
        db.execute(delete(Pairing).where(Pairing.account.in_(accounts)))
        db.execute(delete(Profile).where(Profile.id.in_(ids)))
        db.execute(delete(Friendship).where(or_(Friendship.first.in_(accounts),Friendship.second.in_(accounts))))
        db.execute(delete(Login).where(Login.account.in_(accounts)))
        db.execute(delete(SocialProfile).where(SocialProfile.account.in_(accounts)))
        db.execute(delete(Account).where(Account.id.in_(accounts)))
        for installation in installations:
            if db.scalar(select(Profile.id).where(Profile.installation==installation).limit(1)) is None:
                db.execute(delete(Installation).where(Installation.id==installation))
        assert db.scalar(select(func.count()).select_from(Record).where(Record.mock==False))==real_before
        db.commit()
    print(json.dumps(result))
