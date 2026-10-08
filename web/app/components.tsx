'use client';
import Link from 'next/link';
import {useEffect,useState} from 'react';
import {api} from './client';
import {useLocale} from './i18n';
import {usePathname} from 'next/navigation';
export function TrophyMark(){return <svg viewBox="0 0 32 32" fill="none" aria-hidden="true"><path d="M10 5h12v8c0 5-3 8-6 8s-6-3-6-8V5Z" stroke="currentColor" strokeWidth="1.8"/><path d="M10 8H5v3c0 4 2 6 6 6m11-9h5v3c0 4-2 6-6 6M16 21v6m-6 0h12" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/><path d="m16 9 1.1 2.3 2.5.4-1.8 1.8.4 2.5-2.2-1.2-2.2 1.2.4-2.5-1.8-1.8 2.5-.4L16 9Z" fill="currentColor"/></svg>;}
export function Navigation({developmentTools=false}:{developmentTools?:boolean}){
 const {t}=useLocale();const path=usePathname();
 const [profile,setProfile]=useState<{handle:string;display_name:string}|null>(null),[loaded,setLoaded]=useState(false);
 useEffect(()=>{let active=true;const refresh=()=>api('/account/profile').then(value=>{if(active)setProfile(value);}).catch(()=>{if(active)setProfile(null);}).finally(()=>{if(active)setLoaded(true);});refresh();window.addEventListener('profileupdated',refresh);window.addEventListener('focus',refresh);return()=>{active=false;window.removeEventListener('profileupdated',refresh);window.removeEventListener('focus',refresh);};},[]);
 const profilePath=profile?'/players/'+encodeURIComponent(profile.handle):null;
 const active=path==='/'?'library':path==='/connections'?'connections':path==='/pair'?'pair':profilePath&&path===profilePath?'profile':path==='/friends'||loaded&&path.startsWith('/players/')?'friends':path==='/test'?'test':null;
 const items=[{key:'library',href:'/',label:'My library',icon:'▦'},...(profilePath?[{key:'profile',href:profilePath,label:'My profile',icon:'◎'}]:[]),{key:'friends',href:'/friends',label:'Friends',icon:'♧'},{key:'connections',href:'/connections',label:'Console profiles',icon:'◉'},{key:'pair',href:'/pair',label:'Pair console',icon:'⊕'}];
 return <aside className="sidebar"><Link className="brand" href="/"><span className="brand-symbol"><TrophyMark/></span><span>Trophy<span className="brand-light">Sync</span><small>{t('TROPHIES & PLAYTIME')}</small></span></Link><span className="nav-caption">{t('WORKSPACE')}</span><nav aria-label={t('Main navigation')}>{items.map(item=><Link key={item.key} href={item.href} className={active===item.key?'active':undefined} aria-current={active===item.key?'page':undefined}><span aria-hidden="true">{item.key==='friends'?<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="1.5"><circle cx="9" cy="7" r="3"/><path d="M3 21v-3a6 6 0 0 1 12 0v3M16 4a3 3 0 0 1 0 6M17 13a5 5 0 0 1 4 5v3"/></svg>:item.icon}</span>{t(item.label)}</Link>)}</nav>{developmentTools&&<div className="sidebar-bottom"><Link className="test-link" aria-current={active==='test'?'page':undefined} href="/test">{t('Local sample test')}</Link></div>}</aside>;
}
