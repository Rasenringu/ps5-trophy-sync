'use client';
import Link from 'next/link';
import {useEffect,useState} from 'react';
import {api} from './client';
import {useLocale} from './i18n';
type Device={id:string;installation_id:string;profile_label:string;revoked:boolean;status:string;last_sync:number|null};
export function Connections(){const {t,browserLocale,ready:localeReady}=useLocale();
 const [devices,setDevices]=useState<Device[]>([]),[error,setError]=useState(''),[ready,setReady]=useState(false);
 async function load(){try{setDevices((await api('/account/devices')).filter((p:Device)=>!p.revoked));setError('');}catch(e){setError((e as Error).message);}finally{setReady(true);}}
 useEffect(()=>{if(localeReady)load();},[localeReady]);
 async function revoke(id:string){try{await api('/account/devices/'+id+'/revoke',{});await load();}catch(e){setError((e as Error).message);}}
 if(!ready)return <p role='status'>{t('Loading profile…')}</p>;
 return <><div className='page-heading'><h1>{t('Console profiles')}</h1><Link className='button' href='/pair'>{t('Pair a profile')}</Link></div>{error&&<p role='alert'>{error}</p>}
<section id="profiles" className="profile-section"><div className="collection-heading"><h2>{t("Console profiles")}</h2><p>{t("Manage the connections to your library")}</p></div><div className="profile-grid">{devices.map(d=><div className="profile-card" key={d.id}><div className="profile-avatar">{d.profile_label.slice(0,1).toUpperCase()}</div><div><h2>{d.profile_label}</h2><p><span className={'status-dot '+(d.revoked?'revoked':'')}/>{d.status==='revoked'?t("Revoked"):d.status==='paired'?t("Paired"):t("Finish pairing on your console")} · {t('Last import: {date}',{date:d.last_sync?new Date(d.last_sync*1000).toLocaleString(browserLocale):t('Never')})}</p><button className="quiet danger" disabled={d.revoked} onClick={()=>revoke(d.id)}>{t("Disconnect console")}</button></div></div>)}</div>{!devices.length&&<p>{t("No paired profiles yet. Open the console app and enter its pairing code.")}</p>}</section>
</>;
}
