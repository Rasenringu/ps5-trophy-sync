"""Import static PNGs from authorized captures, never credentials/unlock records.

Run in the API container with a read-only capture mount. No network requests,
console writes or account/profile changes. Only already imported real native
title/trophy identities can receive artwork. Repeated imports are idempotent.
"""
import argparse
import hashlib
from pathlib import Path
from sqlalchemy import select
from app.db import Session
from app.models import Artwork, Record, TrophyInfo, TrophyText
from app.console_artwork import read_artwork, read_trophy_info, read_localized_text

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    args = parser.parse_args()
    packages = sorted(args.directory.glob('definitions-*.ucp'))
    if not packages:
        raise SystemExit('No authorized UCP captures found')
    # Validate every selected package before any database mutation.
    decoded = []
    for p in packages:
        if p.stat().st_size>64*1024*1024:
            raise ValueError('Oversized capture')
        data=p.read_bytes();title,images=read_artwork(data);metadata_title,metadata=read_trophy_info(data)
        if title!=metadata_title:
            raise ValueError('Artwork metadata identity mismatch')
        localized_title,localized,default=read_localized_text(data)
        if localized_title!=title:
            raise ValueError('Localized title identity mismatch')
        decoded.append((title,images,metadata,localized,default))
    counts = {'games': 0, 'trophies': 0, 'changed': 0, 'metadata':0, 'localized_rows':0}
    with Session() as db:
        known = {}
        for record in db.scalars(select(Record).where(Record.mock == False, Record.source == 'ps5_native', Record.kind == 'trophy')):
            known.setdefault(record.data['title_id'],set()).add(record.data['trophy_id'])
        for title, images, metadata, localized, default in decoded:
            if title not in known:
                continue
            for trophy, content in images.items():
                if trophy and trophy not in known[title]:
                    continue
                digest = hashlib.sha256(content).hexdigest()
                row = db.scalar(select(Artwork).where(Artwork.source=='ps5_native',Artwork.title_id==title,Artwork.trophy_id==trophy))
                if row is None:
                    identity = hashlib.sha256(('ps5_native:'+title+':'+trophy).encode()).hexdigest()
                    row = Artwork(id=identity, source='ps5_native',title_id=title,trophy_id=trophy,digest=digest,content=content)
                    db.add(row)
                    counts['changed'] += 1
                elif row.digest != digest:
                    row.digest, row.content = digest, content
                    counts['changed'] += 1
                counts['trophies' if trophy else 'games'] += 1
            for trophy,(hidden,description) in metadata.items():
                if trophy not in known[title]:
                    continue
                row=db.get(TrophyInfo,('ps5_native',title,trophy))
                if row is None:
                    db.add(TrophyInfo(source='ps5_native',title_id=title,trophy_id=trophy,hidden=hidden,description=description))
                else:
                    row.hidden,row.description=hidden,description
                counts['metadata']+=1
            for language,texts in localized.items():
                for trophy,(name,description) in texts.items():
                    if trophy and trophy not in known[title]:
                        continue
                    row=db.get(TrophyText,('ps5_native',title,trophy,language))
                    if row is None:
                        db.add(TrophyText(source='ps5_native',title_id=title,trophy_id=trophy,language=language,name=name,description=description,is_default=language==default))
                    else:
                        row.name,row.description,row.is_default=name,description,language==default
                    counts['localized_rows']+=1
        db.commit()
    print('Console artwork imported:', counts)

if __name__ == '__main__':
    main()
