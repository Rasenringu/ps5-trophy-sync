'use client';
import {useEffect,useState} from 'react';
import {api} from '../client';
import {useLocale} from '../i18n';

type Publication={id:string;title:string;state:string;error:string|null;seconds:number};
type Connection={connected:boolean;username:string|null;expires:number|null;publications:Publication[]};
const errors:Record<string,string>={sign_in_required:'Sign in on HowLongToBeat again.',account_changed:'The HowLongToBeat login changed. Reconnect your account.',ambiguous_entries:'Several entries match this game. Review them on HowLongToBeat.',existing_time_greater:'Your HowLongToBeat entry already has more time. Review it there.',invalid_response:'The provider returned data we could not verify.',provider_unavailable:'The provider is unavailable. Try again later.',rate_limited:'The provider limit has been reached. Try again later.',write_unverified:'Update not verified. Run the connector again to check the existing entry.',game_unavailable:'This game is no longer available in your library.'};

export default function Integrations(){
 const{t,browserLocale}=useLocale();const[connection,setConnection]=useState<Connection|null>(null),[error,setError]=useState(''),[busy,setBusy]=useState(false);
 const[pair,setPair]=useState<{code:string;expires:number}|null>(null);
 async function refresh(){try{setConnection(await api('/account/integrations/howlongtobeat/connection'));}catch(e){setError((e as Error).message);}}
 useEffect(()=>{refresh();},[]);
 async function connect(){setBusy(true);setError('');try{setPair(await api('/account/integrations/howlongtobeat/connect',{}));}catch(e){setError((e as Error).message);}finally{setBusy(false);}}
 async function disconnect(){setBusy(true);setError('');try{await api('/account/integrations/howlongtobeat/disconnect',{});setPair(null);await refresh();}catch(e){setError((e as Error).message);}finally{setBusy(false);}}
 return <><div className="page-heading"><div><p className="eyebrow">{t('YOUR COLLECTION')}</p><h1>{t('Integrations')}</h1></div></div>{error&&<p role="alert" className="error">{error}</p>}
 <div className="integration-grid"><section className="social-panel"><span className="integration-status">{connection?.connected?t('Connected as {name}',{name:connection.username||''}):t('Automatic completion estimates')}</span><h2>HowLongToBeat</h2>
 <p>{t('Completion estimates load when you open a game.')}</p>
 <div className="insight-actions"><button disabled={busy} onClick={connect}>{t(connection?.connected?'Reconnect account':'Connect account')}</button>{connection?.connected&&<button className="secondary" disabled={busy} onClick={disconnect}>{t('Disconnect')}</button>}<button className="quiet" onClick={refresh}>{t('Refresh status')}</button></div>
 {pair&&<div className="connector-setup"><ol><li><a className="text-link" href="/downloads/trophysync-hltb-browser.zip" download>{t('Download browser connector')}</a><p>{t('Unzip, open chrome://extensions or edge://extensions, enable Developer mode, then Load unpacked and select the connector folder.')}</p></li><li><a className="text-link" href="https://howlongtobeat.com/login" target="_blank" rel="noopener noreferrer">{t('Sign in on HowLongToBeat')}</a></li><li>{t('Open the connector, enter this website URL and connection code.')}<p><code>{typeof location==='undefined'?'':location.origin}</code></p><p><code className="connector-code">{pair.code}</code></p><p>{t('Expires {time}',{time:new Date(pair.expires*1000).toLocaleTimeString(browserLocale)})}</p></li><li>{t('Review a game’s playtime, queue its update, then choose Sync queued updates in the connector.')}</li></ol></div>}
 {connection?.publications.length?<ul className="publication-list">{connection.publications.map(job=><li key={job.id}><strong>{job.title}</strong><span>{t(({pending:'Queued',processing:'Checking update',synced:'Synced',failed:'Failed',uncertain:'Needs verification',cancelled:'Cancelled'} as Record<string,string>)[job.state]||job.state)}</span>{job.error&&<p role="status">{t(errors[job.error]||'The provider is unavailable. Try again later.')}</p>}</li>)}</ul>:null}
 <a className="text-link" href="/api/account/integrations/playtime.csv">{t('Export my playtime (CSV)')}</a></section>
 <section className="social-panel"><span className="integration-status">{t('No API key needed')}</span><h2>{t('Trophy earn rates')}</h2><p>Exophase</p><p>{t('Open a game, choose Find trophy earn rates, and paste its Exophase trophy listing URL.')}</p><a className="text-link" href="https://www.exophase.com" target="_blank" rel="noopener noreferrer">Exophase ↗</a></section></div></>;
}
