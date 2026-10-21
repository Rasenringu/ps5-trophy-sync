import {providerOperation} from './provider.js';

function origin(value){
  const url=new URL(value);
  if(url.username||url.password||url.search||url.hash||url.pathname!=='/'||
     !(url.protocol==='https:'||(url.protocol==='http:'&&['localhost','127.0.0.1'].includes(url.hostname))))throw new Error('Use an HTTPS TrophySync origin.');
  return url.origin;
}
async function server(base,path,body,token){
  const response=await fetch(base+'/api/integrations/howlongtobeat/'+path,{method:'POST',credentials:'omit',redirect:'error',
    referrerPolicy:'no-referrer',headers:{'Content-Type':'application/json',...(token?{Authorization:'Bearer '+token}:{})},
    body:JSON.stringify(body),signal:AbortSignal.timeout(20000)});
  const data=await response.json();
  if(!response.ok)throw new Error(typeof data.detail==='string'?data.detail:'TrophySync request failed.');
  return data;
}
async function provider(input){
  const tabs=await chrome.tabs.query({url:'https://howlongtobeat.com/*'});
  const tab=tabs.find(t=>t.active)||tabs[0];
  if(!tab)throw new Error('Open HowLongToBeat and sign in first.');
  const results=await chrome.scripting.executeScript({target:{tabId:tab.id},world:'ISOLATED',func:providerOperation,args:[input]});
  return results[0]?.result;
}
let running=false;
chrome.runtime.onMessage.addListener((message,sender,reply)=>{
  if(sender.id!==chrome.runtime.id||sender.url!==chrome.runtime.getURL('popup.html'))return false;
  if(running){reply({error:'A connector action is already running.'});return false;}
  running=true;
  (async()=>{
    await chrome.storage.local.setAccessLevel({accessLevel:'TRUSTED_CONTEXTS'});
    if(message.action==='connect'){
      const base=origin(message.origin);
      if(!await chrome.permissions.contains({origins:[base+'/*']}))throw new Error('Grant access to your TrophySync site first.');
      const identity=await provider({operation:'identity'});
      if(!identity?.user_id)throw new Error('Sign in on HowLongToBeat, then connect again.');
      const data=await server(base,'claim',{code:message.code,...identity});
      await chrome.storage.local.set({connection:{base,token:data.token,expires:data.expires,username:data.username}});
      return {message:'Connected as '+data.username+'.'};
    }
    if(message.action==='forget'){await chrome.storage.local.remove('connection');return {message:'Local connection removed. Revoke it in TrophySync Integrations.'};}
    if(message.action!=='sync')throw new Error('Unknown connector action.');
    const {connection}=await chrome.storage.local.get('connection');
    if(!connection||connection.expires<=Date.now()/1000)throw new Error('Connect TrophySync again.');
    let synced=0;
    for(let i=0;i<10;i++){
      const result=await server(connection.base,'next',{},connection.token);
      if(!result.job)break;
      const receipt=await provider({operation:'publish',...result});
      if(!receipt?.state)throw new Error('The provider tab did not respond. Retry to check the existing entry.');
      await server(connection.base,'receipt',{job_id:result.job.id,...receipt},connection.token);
      if(receipt.state!=='synced'){
        const errors={sign_in_required:'Sign in on HowLongToBeat again.',account_changed:'The HowLongToBeat login changed. Reconnect your account.',
          ambiguous_entries:'Several entries match this game. Review them on HowLongToBeat.',existing_time_greater:'Your HowLongToBeat entry already has more time. Review it there.',
          invalid_response:'The provider returned data we could not verify.',provider_unavailable:'The provider is unavailable. Try again later.',
          rate_limited:'The provider limit has been reached. Try again later.',write_unverified:'Update not verified. Run the connector again to check the existing entry.'};
        throw new Error(errors[receipt.error]||'Check this update in TrophySync Integrations.');
      }
      synced++;
    }
    return {message:synced+' update(s) verified. Refresh TrophySync Integrations.'};
  })().then(reply).catch(error=>reply({error:error.message})).finally(()=>{running=false;});
  return true;
});
