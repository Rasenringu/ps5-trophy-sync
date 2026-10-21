'use client';
import {useEffect,useState,useRef} from 'react';
import {api} from './client';
import {useLocale} from './i18n';

type HltbGame={hltb_id:number;title:string;platforms:string[];url:string};
type Completion={title?:string;entry_mode?:string;status?:string;stale?:boolean;candidates?:HltbGame[];hltb_id:number|null;main_seconds:number|null;extra_seconds:number|null;completionist_seconds:number|null;url:string;updated:number|null};
type Listing={id:number|string;title:string;platform:string;url:string};
type Rarity={provider?:string;status:string;rates:Record<string,number|null>;listing:Listing|null;stale:boolean;fetched:number|null};
type Insights={howlongtobeat:Completion;rarity:Rarity};
const fields=['main_seconds','extra_seconds','completionist_seconds'] as const;
const labels=['Main Story','Main + Extras','Completionist (100%)'];
function hoursMinutes(seconds:number){return String(Math.floor(seconds/3600)).padStart(2,'0')+'h'+String(Math.floor(seconds%3600/60)).padStart(2,'0')+'min';}
export function GameInsights({source,titleId,playerHandle,seconds,onRates}:{source:string;titleId:string;playerHandle?:string;seconds:number|null;onRates:(rates:Record<string,number|null>)=>void}){
 const {t,browserLocale}=useLocale();
 const [value,setValue]=useState<Insights|null>(null),[error,setError]=useState(''),[editing,setEditing]=useState(false),[busy,setBusy]=useState(false);
 const [candidates,setCandidates]=useState<Listing[]|null>(null),[notice,setNotice]=useState(''),[searchStatus,setSearchStatus]=useState('');
 const [copied,setCopied]=useState(false),[hltbChoices,setHltbChoices]=useState<HltbGame[]|null>(null);
 const [hltbSearchStatus,setHltbSearchStatus]=useState('');
 const [freeListing,setFreeListing]=useState(false);
 const [publishing,setPublishing]=useState(false);
 const mounted=useRef(true);
 useEffect(()=>{mounted.current=true;return()=>{mounted.current=false;};},[]);
 const query=new URLSearchParams({source,title_id:titleId}).toString();
 const root=playerHandle?'/players/'+encodeURIComponent(playerHandle):'/account';
 function accept(data:Insights){if(!mounted.current)return;setValue(data);onRates(data.rarity.rates);}
 useEffect(()=>{let active=true;onRates({});api(root+'/games/insights?'+query).then(data=>{if(active)accept(data);}).catch(e=>{if(active)setError(e.message);});return()=>{active=false;};},[root,query]);
 async function save(event:React.FormEvent<HTMLFormElement>){event.preventDefault();setError('');setBusy(true);const data=new FormData(event.currentTarget);
  try{
   const link=String(data.get('hltb')||'').trim();let hltb_id:number|null=null;
   if(link){const match=/^https:\/\/(?:www\.)?howlongtobeat\.com\/game\/(\d+)\/?$/.exec(link);if(!match)throw new Error(t('Enter a HowLongToBeat game URL.'));hltb_id=Number(match[1]);}
   const times=Object.fromEntries(fields.map(field=>{const hours=String(data.get(field)||'').trim();return [field,hours===''?null:Math.round(Number(hours)*3600)];}));
   accept(await api('/account/games/howlongtobeat',{source,title_id:titleId,hltb_id,...times}));setEditing(false);setNotice(t('Completion times saved.'));
  }catch(e){setError((e as Error).message);}finally{setBusy(false);}
 }
 async function search(){setBusy(true);setError('');setNotice('');try{const data=await api('/account/integrations/platprices/search?'+query);setCandidates(data.games);setSearchStatus(data.status);}catch(e){setError((e as Error).message);}finally{setBusy(false);}}
 async function select(id:number|null){setBusy(true);setError('');setNotice('');try{accept(await api('/account/games/platprices',{source,title_id:titleId,platprices_id:id}));setCandidates(null);setSearchStatus('');}catch(e){setError((e as Error).message);}finally{setBusy(false);}}
 async function automatic(id:number|null){setBusy(true);setError('');setNotice('');try{accept(await api('/account/games/howlongtobeat/automatic',{source,title_id:titleId,hltb_id:id}));setHltbChoices(null);setEditing(false);}catch(e){setError((e as Error).message);}finally{setBusy(false);}}
 async function findCompletion(){setBusy(true);setError('');try{const result=await api('/account/integrations/howlongtobeat/search?'+query);setHltbChoices(result.candidates);setHltbSearchStatus(result.status);}catch(e){setError((e as Error).message);}finally{setBusy(false);}}
 async function saveFreeListing(event:React.FormEvent<HTMLFormElement>){event.preventDefault();setBusy(true);setError('');try{accept(await api('/account/games/trophy-rates',{source,title_id:titleId,listing_url:String(new FormData(event.currentTarget).get('listing')||'').trim()}));setFreeListing(false);}catch(e){setError((e as Error).message);}finally{setBusy(false);}}
 async function removeFreeListing(){setBusy(true);setError('');try{accept(await api('/account/games/trophy-rates',{source,title_id:titleId,listing_url:null}));}catch(e){setError((e as Error).message);}finally{setBusy(false);}}
 async function publish(event:React.FormEvent<HTMLFormElement>){event.preventDefault();setBusy(true);setError('');try{const result=await api('/account/games/howlongtobeat/publish',{source,title_id:titleId,hltb_id:value?.howlongtobeat.hltb_id,seconds,confirm:true});setNotice(t(result.state==='synced'?'Playtime already synced.':'Queued. Open the browser connector and sync queued updates.'));setPublishing(false);}catch(e){setError((e as Error).message);}finally{setBusy(false);}}
 const unavailable:Record<string,string>={not_configured:'Trophy earn rates need a free PlatPrices key on the server.',not_selected:'Choose the matching game to see trophy earn rates.',not_cached:'Trophy earn rates have not been loaded by the library owner yet.',mismatch:'This listing does not match the imported trophy list.',rate_limited:'The provider limit has been reached. Try again later.',configuration_error:'The provider key or store region needs attention on the server.',unavailable:'The provider is unavailable. Try again later.',invalid_response:'The provider returned data we could not verify.',not_found:'No trophy data was found for this listing.'};
 if(!value)return <section className="game-insights" aria-label={t('Game information')}>{error?<p role="alert" className="error">{error}</p>:<p role="status">{t('Loading game information…')}</p>}</section>;
 const completion=value.howlongtobeat,rarity=value.rarity;
 const automaticMode=completion.entry_mode==='provider';
 const choices=hltbChoices||completion.candidates||[];
 const freeProvider=rarity.provider==='exophase';
 return <section className="game-insights" aria-label={t('Game information')}>
  <div className="insight-heading"><h3>HowLongToBeat</h3><a href={completion.url} target="_blank" rel="noopener noreferrer">{t(completion.hltb_id?'View on HowLongToBeat':'Find on HowLongToBeat')} <span aria-hidden="true">↗</span></a></div>
  {automaticMode&&completion.title&&<p className="insight-note hltb-source-title">{completion.title}</p>}
  <dl className="completion-times">{fields.map((field,i)=><div key={field}><dt>{t(labels[i])}</dt><dd>{completion[field]==null?t('Unknown'):<time dateTime={'PT'+completion[field]+'S'}>{hoursMinutes(completion[field]!)}</time>}</dd></div>)}</dl>
  {(completion.updated||completion.stale)&&<p className="insight-note">{completion.updated?t('Updated {date}',{date:new Date(completion.updated*1000).toLocaleDateString(browserLocale)}):null}{completion.stale?' · '+t('Cached data; refresh unavailable'):null}</p>}
  {!playerHandle&&<div className="insight-actions"><button className="secondary" disabled={busy} onClick={automaticMode?findCompletion:()=>automatic(completion.hltb_id)}>{t(automaticMode?'Match a HowLongToBeat game':'Use automatic estimates')}</button><button className="secondary" onClick={()=>{setEditing(!editing);setNotice('');}} aria-expanded={editing}>{t(editing?'Cancel':'Edit completion times')}</button>{seconds!=null&&<button className="quiet" onClick={async()=>{try{await navigator.clipboard.writeText(t('{hours}h {minutes}m',{hours:Math.floor(seconds/3600),minutes:Math.floor(seconds%3600/60)}));setCopied(true);}catch{setError(t('Copy failed. Your recorded playtime is shown below.'));}}}>{t(copied?'Playtime copied':'Copy my recorded playtime')}</button>}</div>}
  {!playerHandle&&choices.length>0&&<div className="provider-candidates"><p className="insight-note">{t('Choose the matching HowLongToBeat edition.')}</p>{choices.map(game=><button className="secondary" disabled={busy} key={game.hltb_id} onClick={()=>automatic(game.hltb_id)}><span>{game.title}</span><span>#{game.hltb_id}</span></button>)}</div>}
  {!playerHandle&&seconds!=null&&seconds>0&&completion.hltb_id&&<div className="insight-actions"><button className="secondary" disabled={busy} onClick={()=>setPublishing(!publishing)}>{t('Publish playtime')}</button><a className="text-link" href="/integrations">{t('Account connection')}</a></div>}
  {publishing&&!playerHandle&&seconds!=null&&<form className="completion-form" onSubmit={publish}><p>{t('Recorded progress: {hours}h {minutes}m {seconds}s',{hours:Math.floor(seconds/3600),minutes:Math.floor(seconds%3600/60),seconds:seconds%60})}</p><label className="completion-link"><span><input type="checkbox" required style={{width:'auto'}}/> {t('Publish this time as progress on HowLongToBeat')}</span></label><button disabled={busy}>{t('Queue update')}</button></form>}
  {!playerHandle&&hltbChoices?.length===0&&<p role="status" className="insight-note">{t(hltbSearchStatus==='ok'||hltbSearchStatus==='not_found'?'No matching listings were found.':'HowLongToBeat lookup is unavailable. You can still enter estimates manually.')}</p>}
  {editing&&!playerHandle&&<form className="completion-form" onSubmit={save}><label className="completion-link">{t('HowLongToBeat game URL')}<input name="hltb" type="url" placeholder="https://howlongtobeat.com/game/…" defaultValue={completion.hltb_id?'https://howlongtobeat.com/game/'+completion.hltb_id:''}/></label>{fields.map((field,i)=><label key={field}>{t(labels[i])}<span className="input-unit"><input aria-label={t(labels[i])+" ("+t("hours")+")"} name={field} type="number" min="0.0003" max="10000" step="any" inputMode="decimal" defaultValue={completion[field]==null?'':completion[field]!/3600}/><span>{t('hours')}</span></span></label>)}<p className="insight-note">{t('Leave a time blank when unknown. These estimates do not change your recorded playtime.')}</p><button disabled={busy}>{t(busy?'Saving…':'Save completion times')}</button></form>}
  <div className="rarity-panel"><div className="insight-heading"><h3>{t('Trophy earn rates')}</h3><a href={rarity.listing?.url||(freeProvider?'https://www.exophase.com':'https://platprices.com')} target="_blank" rel="noopener noreferrer">{freeProvider?'Exophase':t('Powered by PlatPrices')}</a></div>
   {Object.keys(rarity.rates).length>0?<p className="insight-note">{rarity.listing?.title} · {rarity.fetched?t('Updated {date}',{date:new Date(rarity.fetched*1000).toLocaleDateString(browserLocale)}):null}{rarity.stale?' · '+t('Cached data; refresh unavailable'):null}</p>:rarity.status!=='not_selected'&&<p className="insight-note">{t(unavailable[rarity.status]||'The provider is unavailable. Try again later.')}</p>}
   {!playerHandle&&<div className="insight-actions"><button className="secondary" disabled={busy} onClick={freeProvider?()=>setFreeListing(!freeListing):search}>{t(busy?'Loading…':rarity.listing?'Change listing':'Find trophy earn rates')}</button>{rarity.listing&&<button className="quiet" disabled={busy} onClick={freeProvider?removeFreeListing:()=>select(null)}>{t('Remove listing')}</button>}</div>}
   {freeListing&&!playerHandle&&<form className="completion-form" onSubmit={saveFreeListing}><label className="completion-link">{t('Exophase trophy listing URL')}<input name="listing" type="url" required placeholder="https://www.exophase.com/game/…/trophies/" defaultValue={rarity.listing?.url||''}/></label><button disabled={busy}>{t('Use this listing')}</button></form>}
   {candidates&&<div className="provider-candidates"><p className="insight-note">{t('Select the correct edition. We check its platform and trophy names and grades before showing rates.')}</p>{candidates.map(game=><button type="button" className="secondary" key={game.id} disabled={busy} onClick={()=>select(Number(game.id))}><span>{game.title}</span><span>{game.platform}</span></button>)}{!candidates.length&&<p role="status">{t(unavailable[searchStatus]||'No matching listings were found.')}</p>}</div>}
  </div>
  {notice&&<p role="status">{notice}</p>}{error&&<p role="alert" className="error">{error}</p>}
 </section>;
}

export function TrophyRarity({rate}:{rate:number|null}){const{t,browserLocale}=useLocale();const number=(n:number)=>new Intl.NumberFormat(browserLocale,{maximumFractionDigits:1}).format(n);return <div className="trophy-rarity">{rate==null?<span>{t('Earn rate unknown')}</span>:<><strong>{t('{percent}% earned',{percent:number(rate)})}</strong><span>{t('{percent}% not earned',{percent:number(100-rate)})}</span></>}</div>;}
