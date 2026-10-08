'use client';
import Link from 'next/link';
import {useLocale,translateText} from '../i18n';
import {useEffect,useRef,useState} from 'react';
import {api} from '../client';

type Pairing={pairing_id:string;device_code:string;user_code:string;expires_at:number};
type Credential={device_token:string;profile_uuid:string};

async function deviceRequest(path:string,body:unknown,token?:string) {
  const response=await fetch('/api/device'+path,{method:'POST',credentials:'omit',
    headers:{'Content-Type':'application/json',...(token?{Authorization:'Bearer '+token}:{})},
    body:JSON.stringify(body),cache:'no-store'});
  const data=await response.json();
  if(!response.ok)throw new Error(translateText(typeof data.detail==='string'?data.detail:'Local test request failed. Try again.'));
  return data;
}

export default function LocalTest({enabled}:{enabled:boolean}) {const {t,locale,preferences,browserLocale,ready:localeReady}=useLocale();
  const [email,setEmail]=useState(''),[ready,setReady]=useState(false),[error,setError]=useState(''),[busy,setBusy]=useState(false);
  const [pair,setPair]=useState<Pairing|null>(null),[approved,setApproved]=useState(false),[imported,setImported]=useState(false),[retry,setRetry]=useState(false),[clock,setClock]=useState(Date.now());
  const credential=useRef<Credential|null>(null);
  const snapshot=useRef<object|null>(null);
  const profileLabel='MOCK local test profile';
  useEffect(()=>{
    api('/account/me').then(user=>setEmail(user.email)).catch(()=>{}).finally(()=>setReady(true));
    const timer=setInterval(()=>setClock(Date.now()),1000);
    return ()=>{clearInterval(timer);credential.current=null;snapshot.current=null;};
  },[]);
  async function run(action:()=>Promise<void>) {
    setBusy(true);setError('');
    try{await action();}catch(e){setError((e as Error).message);}finally{setBusy(false);}
  }
  async function createCode() {
    const installation=await deviceRequest('/installations',{});
    const pairing=await deviceRequest('/pairings',{installation_id:installation.installation_id,
      profile_id:'MOCK_LOCAL_TEST',profile_label:profileLabel},installation.installation_secret);
    setPair(pairing);
  }
  async function approve() {
    if(!pair)return;
    const inspected=await api('/account/pairings/inspect',{code:pair.user_code});
    if(inspected.pairing_id!==pair.pairing_id||inspected.profile_id!=='MOCK_LOCAL_TEST'||inspected.profile_label!==profileLabel)
      throw new Error(translateText('The test profile changed. Reload this page and create a new code.'));
    await api('/account/pairings/approve',{code:pair.user_code,pairing_id:pair.pairing_id,physical_possession:true});
    setApproved(true);
  }
  async function importSample() {
    if(!pair||!approved)return;
    if(!credential.current){
      const result=await deviceRequest('/pairings/poll',{device_code:pair.device_code});
      if(result.status!=='paired')throw new Error(translateText('Profile is still awaiting approval. No sample imported.'));
      credential.current=result;
    }
    if(!snapshot.current)snapshot.current={schema_version:1,batch_id:crypto.randomUUID(),source:'ps5_native',mock:true,
      trophies:[
        {title_id:'MOCK_LOCAL_GAME',title:'MOCK local test game',trophy_id:'first',name:'MOCK first achievement',grade:'bronze',unlocked:true,unlocked_at:null},
        {title_id:'MOCK_LOCAL_GAME',title:'MOCK local test game',trophy_id:'finish',name:'MOCK final achievement',grade:'gold',unlocked:false,unlocked_at:null},
      ],
      activities:[
        {event_id:'MOCK_COMPLETE_SESSION',title_id:'MOCK_LOCAL_GAME',title:'MOCK local test game',started_at:'2026-01-01T12:00:00Z',ended_at:'2026-01-01T12:30:00Z',duration_seconds:1800,complete:true,clock:'trusted'},
        {event_id:'MOCK_INCOMPLETE_SESSION',title_id:'MOCK_LOCAL_GAME',title:'MOCK local test game',duration_seconds:null,complete:false,clock:'unknown'},
      ]};
    const result=await deviceRequest('/sync',snapshot.current,credential.current!.device_token);
    if(result.status==='duplicate')setRetry(true);
    else if(result.status==='imported')setImported(true);
    else throw new Error(translateText('Unexpected import response.'));
  }
  const expired=pair!==null&&clock/1000>=pair.expires_at;
  return <>
    <h1>{t("Test locally")}</h1>
    <p>{t("Try account pairing, trophy views and playtime on this PC. This test uses the real local service with clearly labeled sample data.")}</p>
    <nav><Link href="/">{t("Your library")}</Link><Link href="/pair">{t("Enter a console code")}</Link></nav>
    <section className="card"><h2>{t("1. Sign in or create an account")}</h2>
      {!ready?<p>{t("Checking your session…")}</p>:email?<p>{t('Signed in as {email}.',{email})}</p>:<p><Link href="/login?next=/test">{t("Sign in or register to start the test")}</Link>. {t('No PSN account is needed.')}</p>}
    </section>
    <section className="card"><h2>{t("2. Pair a simulated profile")}</h2>
      <p className="tag">{t("MOCK TEST — NO PS5 CONNECTION")}</p>
      <p>{t('The test creates {profile} in your account. No console files are read. Sample imports stay hidden until you enable mock test imports.',{profile:profileLabel})}</p>
      {!enabled?<p>{t("Sample testing is disabled on this server. The local development stack enables it.")}</p>:!pair?<button disabled={!email||busy} onClick={()=>run(createCode)}>{t("Create test pairing code")}</button>:<>
        <p>{t("Test code:")} <strong>{pair.user_code}</strong><br/>{t("Selected profile:")} {profileLabel}<br/>{approved?t("Approved"):expired?t("Code expired"):t('Expires in {seconds} seconds',{seconds:Math.max(0,Math.ceil(pair.expires_at-clock/1000))})}</p>
        {!approved&&<button disabled={busy||expired} onClick={()=>run(approve)}>{t("Approve simulated profile")}</button>}
        {expired&&!approved&&<p>{t("Reload this page to create a new code.")}</p>}
      </>}
    </section>
    <section className="card"><h2>{t("3. Import the sample and open your library")}</h2>
      <p>{t("Expect one unlocked bronze trophy, one locked gold trophy, a 30-minute sample session and an incomplete session with unknown duration.")}</p>
      {enabled&&<button disabled={!approved||busy||imported} onClick={()=>run(importSample)}>{t("Import sample data")}</button>}
      {imported&&<><p role="status">{t("Sample imported. Open your library and check “Include clearly labeled mock test imports”.")}</p>
        <p><Link href="/">{t("Open your library")}</Link></p>
        <button disabled={busy||retry} onClick={()=>run(importSample)}>{t("Test repeat import")}</button>
        {retry&&<p role="status">{t("Repeat import recognized. No duplicate trophies or sessions were added.")}</p>}
        <p>{t('You can revoke {profile} from Console profiles. Reloading this page discards the temporary test credential.',{profile:profileLabel})}</p>
      </>}
    </section>
    {busy&&<p role="status">{t("Working…")}</p>}{error&&<p role="alert" className="error">{error}</p>}
    <section className="card"><h2>{t("Testing your actual PS5")}</h2>
      <p>{t('Open {url} on this PC. The PS5 connects to the configured HTTPS service.',{url:'http://localhost:3000'})}</p>
      <p>{t('Launch Native Trophies V2 on the PS5. If a code appears, enter it on the pairing page to connect your actual profile.')}</p>
      <p>{t("The Native Trophies V2 console app has imported real trophy observations, including Naruto’s six earned bronze trophies. Playtime interpretation remains unverified. This sample test only imports clearly labeled mock data.")}</p>
    </section>
  </>;
}
