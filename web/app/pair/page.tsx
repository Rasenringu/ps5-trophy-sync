'use client';
import Link from 'next/link';
import {useLocale} from '../i18n';
import {useEffect,useState} from 'react';
import {api} from '../client';
type Pair = {pairing_id:string;installation_id:string;profile_label:string;profile_id:string;expires_at:number};
export default function PairPage() {const {t,locale,preferences,browserLocale,ready:localeReady}=useLocale();
  const [code,setCode] = useState(''),[info,setInfo] = useState<Pair|null>(null),[error,setError] = useState(''),[done,setDone] = useState(false),[checked,setChecked] = useState(false),[busy,setBusy] = useState(false),[clock,setClock] = useState(Date.now());
  useEffect(()=>{setCode(new URLSearchParams(location.search).get('code')||'');
    api('/account/me').catch(()=>{location.href='/login?next='+encodeURIComponent(location.pathname+location.search);});
    const t=setInterval(()=>setClock(Date.now()),1000);return ()=>clearInterval(t);},[]);
  async function inspect(e:React.FormEvent) {e.preventDefault();setBusy(true);setError('');setInfo(null);setChecked(false);
    try {setInfo(await api('/account/pairings/inspect',{code}));} catch(e) {setError((e as Error).message);} finally {setBusy(false);}}
  async function approve() {if(!info)return;setBusy(true);setError('');
    try {await api('/account/pairings/approve',{code,pairing_id:info.pairing_id,physical_possession:true});setDone(true);} catch(e) {setError((e as Error).message);} finally {setBusy(false);}}
  const left=info?Math.max(0,info.expires_at-Math.floor(clock/1000)):0;
  return <section className="auth-wrap"><p className="eyebrow">{t("A CONNECTION THAT’S YOURS")}</p><h1>{t("Pair your console profile")}</h1><p className="lead">{t("Enter the short code shown on your console. Check the installation and selected profile before approving.")}</p>
    {error&&<p className="error" role="alert">{error}</p>}{done?<div className="card pair-success"><h2>{t("Profile approved")}</h2><p>{t("The console can now collect its credential once. Return to the console to complete pairing.")}</p><Link className="button" href="/">{t("Open your dashboard")}</Link></div>:<>
    <form className="pair-code" onSubmit={inspect}><label>{t("Manual code")}<input value={code} onChange={e=>{setCode(e.target.value.toUpperCase());setInfo(null);}} placeholder="ABCD-2345" pattern="[A-Z2-9]{4}-[A-Z2-9]{4}" maxLength={9} required/></label><button disabled={busy}>{t("Check code")}</button></form>
    {info&&<div className="card pair-confirm"><h2>{info.profile_label}</h2><p>{t("Local profile:")} <code>{info.profile_id}</code><br/>{t("Installation:")} <code>{info.installation_id}</code><br/>{t('Expires in {seconds} seconds',{seconds:left})}</p>
    <label><input type="checkbox" checked={checked} onChange={e=>setChecked(e.target.checked)}/>{t("I have physical access to this console and its displayed code, and I want this profile linked to my account.")}</label>
    <button disabled={!checked||busy||left===0} onClick={approve}>{t("Approve profile")}</button>{left===0&&<p className="error">{t("Code expired. Request a new code on the console.")}</p>}</div>}</>}</section>;
}
