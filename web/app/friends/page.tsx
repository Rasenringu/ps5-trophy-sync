'use client';
import Link from 'next/link';
import {useEffect,useState} from 'react';
import {api} from '../client';
import {useLocale} from '../i18n';

type Person={handle:string;display_name:string;request_id?:string;visibility?:'public'|'friends'};
type Connections={friends:Person[];incoming:Person[];outgoing:Person[];denied:Person[]};
export default function Friends(){
 const {t,ready:localeReady}=useLocale();
 const [visibility,setVisibility]=useState('friends');
 const [me,setMe]=useState<Person|null>(null),[handle,setHandle]=useState(''),[name,setName]=useState('');
 const [connections,setConnections]=useState<Connections>({friends:[],incoming:[],outgoing:[],denied:[]});
 const [query,setQuery]=useState(''),[results,setResults]=useState<Person[]>([]),[searched,setSearched]=useState(false);
 const [error,setError]=useState(''),[notice,setNotice]=useState(''),[busy,setBusy]=useState(false),[ready,setReady]=useState(false);
 async function refresh(){setConnections(await api('/account/friends'));}
 useEffect(()=>{if(!localeReady)return;let active=true;
  Promise.all([api('/account/profile'),api('/account/friends')]).then(([p,c])=>{if(active){setMe(p);setHandle(p.handle);setName(p.display_name);setVisibility(p.visibility||'friends');setConnections(c);}}).catch(e=>{if(active)setError(e.message);}).finally(()=>{if(active)setReady(true);});
  const timer=setInterval(()=>{if(active)refresh().catch(()=>{});},30000);return()=>{active=false;clearInterval(timer);};
 },[localeReady]);
 async function save(event:React.FormEvent){event.preventDefault();setBusy(true);setError('');setNotice('');try{const p=await api('/account/profile',{handle:handle.trim().toLowerCase(),display_name:name,visibility});setMe(p);setHandle(p.handle);setName(p.display_name);setNotice(t('Profile saved'));window.dispatchEvent(new Event('profileupdated'));}catch(e){setError((e as Error).message);}finally{setBusy(false);}}
 async function search(event:React.FormEvent){event.preventDefault();setBusy(true);setError('');try{setResults(await api('/players?q='+encodeURIComponent(query.trim())));setSearched(true);}catch(e){setError((e as Error).message);}finally{setBusy(false);}}
 async function act(person:Person,action:string){setBusy(true);setError('');try{await api('/account/friends/'+person.request_id,{action});await refresh();}catch(e){setError((e as Error).message);}finally{setBusy(false);}}
 if(!ready)return <p role="status">{t('Loading friends…')}</p>;
 if(!me)return <section className="social-panel"><h1>{t('Friends')}</h1><p>{t('Sign in to connect with other players.')}</p><Link className="button" href="/login">{t('Sign in or register')}</Link>{error&&<p role="alert">{error}</p>}</section>;
 return <><div className="page-heading"><div><p className="eyebrow">TROPHYSYNC</p><h1>{t('Friends')}</h1><p className="lead">{t('Find your friends. Compare your progress.')}</p></div><button className="secondary" onClick={()=>refresh().catch(e=>setError(e.message))}>{t('Refresh')}</button></div>
 {error&&<p className="error" role="alert">{error}</p>}{notice&&<p className="social-notice" role="status">{notice}</p>}
 <section className="social-panel"><h2>{t('Your public profile')}</h2><p className="subtle">{t('Choose who can see your game collection.')}</p>
 <form className="profile-form" onSubmit={save}><label>{t('Display name')}<input required maxLength={60} value={name} onChange={e=>setName(e.target.value)}/></label><label>{t('Public handle')}<input aria-label={t('Public handle')} required minLength={3} maxLength={32} pattern="[a-z][a-z0-9_]{2,31}" autoCapitalize="none" value={handle} onChange={e=>setHandle(e.target.value.toLowerCase())}/><small>{t('Start with a letter. Use lowercase letters, numbers or underscores.')}</small></label><label>{t('Library visibility')}<select aria-label={t('Library visibility')} value={visibility} onChange={e=>setVisibility(e.target.value)}><option value='friends'>{t('Friends only')}</option><option value='public'>{t('Public')}</option></select></label><button disabled={busy}>{t('Save profile')}</button></form>
 <Link className="profile-link" href={'/players/'+me.handle}>{t('Open your profile')} <span>@{me.handle}</span></Link></section>
 <section className="social-panel"><h2>{t('Find a player')}</h2><form className="friend-search" onSubmit={search}><label className="sr-only" htmlFor="player-search">{t('Search by name or handle')}</label><input id="player-search" type="search" minLength={2} maxLength={50} required placeholder={t('Search by name or handle')} value={query} onChange={e=>setQuery(e.target.value)}/><button disabled={busy}>{t('Search')}</button></form>
 {searched&&!results.length&&<p>{t('No players found.')}</p>}<ul className="people-list">{results.map(p=><li key={p.handle}><Link className="person-link" href={'/players/'+p.handle}><span className="person-avatar" aria-hidden="true">{p.display_name.slice(0,1)}</span><span><strong>{p.display_name}</strong><small>@{p.handle}</small></span><span aria-hidden="true">↗</span></Link></li>)}</ul></section>
 <div className="social-columns">{(['incoming','outgoing','friends','denied'] as const).map(section=><section className="social-panel" key={section}><h2>{t(section==='incoming'?'Requests received':section==='outgoing'?'Requests sent':section==='denied'?'Declined requests':'Your friends')} <span className="section-count">{connections[section].length}</span></h2>
 {!connections[section].length&&<p className="subtle">{t(section==='friends'?'Your friends will appear here.':section==='denied'?'No declined requests.':'No pending requests.')}</p>}
 <ul className="people-list">{connections[section].map(p=><li key={p.handle}><Link className="person-link" href={'/players/'+p.handle}><span className="person-avatar" aria-hidden="true">{p.display_name.slice(0,1)}</span><span><strong>{p.display_name}</strong><small>@{p.handle}</small></span></Link><div className="person-actions">{section==='incoming'?<><button disabled={busy} onClick={()=>act(p,'accept')}>{t('Accept')}</button><button className="secondary" disabled={busy} onClick={()=>act(p,'deny')}>{t('Deny')}</button></>:section==='denied'?<span className="subtle">{t('Request declined')}</span>:section==='outgoing'?<button className="secondary" disabled={busy} onClick={()=>act(p,'cancel')}>{t('Cancel request')}</button>:<><Link className="button" href={'/players/'+p.handle}>{t('Compare trophies')}</Link><button className="secondary" disabled={busy} onClick={()=>act(p,'remove')}>{t('Remove friend')}</button></>}</div></li>)}</ul></section>)}</div></>;
}
