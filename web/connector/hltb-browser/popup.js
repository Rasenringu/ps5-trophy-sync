const result=document.querySelector('#result');
const {connection}=await chrome.storage.local.get('connection');
if(connection){document.querySelector('#origin').value=connection.base;document.querySelector('#identity').textContent=connection.username;}
async function action(message){
  document.querySelectorAll('button').forEach(button=>button.disabled=true);result.textContent='Working… Keep this popup open.';
  try{const response=await chrome.runtime.sendMessage(message);result.textContent=response?.error||response?.message||'No response. Reopen the connector.';}
  catch{result.textContent='Connector interrupted. Retry to check the existing entry.';}
  finally{document.querySelectorAll('button').forEach(button=>button.disabled=false);}
}
document.querySelector('#connect').addEventListener('submit',async event=>{
  event.preventDefault();
  try{
    const url=new URL(document.querySelector('#origin').value);
    if(!['https:','http:'].includes(url.protocol)||url.username||url.password||url.pathname!=='/'||url.search||url.hash||
       (url.protocol==='http:'&&!['localhost','127.0.0.1'].includes(url.hostname)))throw new Error('Use an HTTPS TrophySync origin.');
    if(!await chrome.permissions.request({origins:[url.origin+'/*']}))throw new Error('Site access was declined.');
    await action({action:'connect',origin:url.origin,code:document.querySelector('#code').value.trim()});
    document.querySelector('#code').value='';
  }catch(error){result.textContent=error.message;}
});
document.querySelector('#sync').addEventListener('click',()=>action({action:'sync'}));
document.querySelector('#forget').addEventListener('click',()=>action({action:'forget'}));
