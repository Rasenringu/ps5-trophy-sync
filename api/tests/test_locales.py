"""Synthetic locale/package fixtures: no console reads or authenticity claims."""
import json
import pytest
from app.locales import choose_language
from app.console_artwork import read_localized_text
from test_artwork import package

@pytest.mark.parametrize('requested,expected',[
 ('fr-CA,fr-FR,en-US','fr-CA'),('fr-BE,en-US','fr-FR'),
 ('de-AT,en-US','de-DE'),('pt-BR,pt-PT,en-US','pt-BR'),
 ('pt-PT,pt-BR','pt-PT'),('pt','pt-PT'),('es-MX','es-ES'),
 ('es-419,es-ES','es-419'),('it-CH','it-IT'),('zh-Hant-HK','zh-Hant'),
 ('xx,en-US','en-US'),('xx','en-US'),('../fr-FR','en-US')])
def test_locale_matching(requested,expected):
    languages=['en-US','fr-FR','fr-CA','de-DE','pt-PT','pt-BR','es-ES','es-419','it-IT','zh-Hans','zh-Hant']
    assert choose_language(languages,requested,'en-US')==expected

def test_official_translations_require_exact_identity_and_trophy_ids():
    conf={'trophyNpCommId':'NPWR12345_00','trophyDefinitionRevision':'1',
          'trophySetVersion':'1','defaultLanguage':'en-US','trophies':[{'id':'0021'}]}
    def meta(name):
        return {**{k:conf[k] for k in ('trophyNpCommId','trophyDefinitionRevision','trophySetVersion')},
          'schemaVersion':'0.90','metadata':{'titleMetadata':{'name':'MOCK '+name},
          'trophyMetadata':[{'id':'0021','name':name,'detail':'MOCK description '+name}]}}
    english=meta('English');french=meta('Français')
    def encoded():
        return package({'tropconf.json':json.dumps(conf).encode(),
                        'tropmeta_en-US.json':json.dumps(english).encode(),
                        'tropmeta_fr-FR.json':json.dumps(french).encode()})
    title,rows,default=read_localized_text(encoded())
    assert title=='NPWR12345_00' and default=='en-US'
    assert rows['fr-FR']['0021']==('Français','MOCK description Français')
    french['metadata']['trophyMetadata'][0]['id']='21'
    with pytest.raises(ValueError):read_localized_text(encoded())
    french=meta('Français');french['trophySetVersion']='2'
    with pytest.raises(ValueError):read_localized_text(encoded())
