// Independent implementation of the pinned Playnite protocol. Runs only inside
// the provider tab; returns identity/receipts, never cookies, passwords or rosters.
export async function providerOperation(input) {
  let posted=false;
  const fail=code=>{throw new Error(code);};
  const validInt=(n,min=0)=>Number.isSafeInteger(n)&&n>=min;
  const request=async(path,body,html=false)=>{
    if(!/^\/(?:api\/user(?:\/[1-9]\d*\/games\/list)?|api\/submit|submit\/edit\/[1-9]\d*)$/.test(path))fail('invalid_response');
    const response=await fetch(path,{method:body===undefined?'GET':'POST',credentials:'same-origin',redirect:'error',cache:'no-store',
      headers:body===undefined?{}:{'Content-Type':'application/json'},body:body===undefined?undefined:JSON.stringify(body),signal:AbortSignal.timeout(15000)});
    if(response.status===429)fail('rate_limited');
    if(response.status===401||response.status===403)fail('sign_in_required');
    if(!response.ok)fail('provider_unavailable');
    if(!(response.headers.get('content-type')||'').includes(html?'text/html':'application/json'))fail('invalid_response');
    const reader=response.body.getReader();const chunks=[];let size=0;
    try{while(true){const {value,done}=await reader.read();if(done)break;size+=value.length;if(size>2*1024*1024)fail('invalid_response');chunks.push(value);}}
    finally{await reader.cancel();}
    const bytes=new Uint8Array(size);let at=0;for(const chunk of chunks){bytes.set(chunk,at);at+=chunk.length;}
    const text=new TextDecoder('utf-8',{fatal:true}).decode(bytes);
    return html?text:JSON.parse(text);
  };
  const user=async()=>{
    const response=await request('/api/user');const row=response?.data?.[0];
    if(!validInt(row?.user_id,1)||!/^\w{3,20}$/.test(row?.user_name||'')||row?.redirect)fail('sign_in_required');
    return {user_id:row.user_id,username:row.user_name};
  };
  try{
    const identity=await user();
    if(input.operation==='identity')return identity;
    const job=input.job;
    if(identity.user_id!==input.user_id)fail('account_changed');
    if(!job||!validInt(job.hltb_id,1)||!validInt(job.seconds,1)||job.seconds>36000000||
       !['PlayStation 4','PlayStation 5'].includes(job.platform)||typeof job.title!=='string'||job.title.length>400)fail('invalid_response');
    const lists=async()=>{
      const response=await request('/api/user/'+identity.user_id+'/games/list',{
        user_id:identity.user_id,lists:['playing','backlog','replays','custom','custom2','custom3','completed','retired'],
        set_playstyle:'comp_all',name:'',platform:'',storefront:'',sortBy:'',sortFlip:0,view:'',random:0,limit:5000,currentUserHome:true});
      const data=response?.data,rows=data?.gamesList;
      if(!Array.isArray(rows)||rows.length>5000||!validInt(data.total)||data.total!==rows.length)fail('invalid_response');
      if(rows.some(r=>!validInt(r.id,1)||!validInt(r.game_id,1)||typeof r.platform!=='string'))fail('invalid_response');
      const matches=rows.filter(r=>r.game_id===job.hltb_id&&r.platform===job.platform);
      if(matches.length>1)fail('ambiguous_entries');
      return matches[0]||null;
    };
    const timeSeconds=t=>{
      if(!t||typeof t!=='object')fail('invalid_response');
      const values=['hours','minutes','seconds'].map(k=>t[k]===null?0:t[k]);
      if(values.some(n=>!validInt(n))||values[1]>59||values[2]>59)fail('invalid_response');
      return values[0]*3600+values[1]*60+values[2];
    };
    const edit=async row=>{
      const html=await request('/submit/edit/'+row.id,undefined,true);
      const match=/<script\b(?=[^>]*\bid=["']__NEXT_DATA__["'])[^>]*>(.*?)<\/script\s*>/is.exec(html);
      if(!match)fail('invalid_response');
      const value=JSON.parse(match[1])?.props?.pageProps?.editData;
      if(!value||value.userId!==identity.user_id||value.gameId!==job.hltb_id||value.submissionId!==row.id||value.platform!==job.platform)fail('invalid_response');
      timeSeconds(value.general?.progress);
      if(!value.lists||!value.singlePlayer||!value.review||!value.additionals)fail('invalid_response');
      return value;
    };
    const receipt=async()=>{
      const row=await lists();
      if(!row)return null;
      const data=await edit(row);
      return timeSeconds(data.general.progress)===job.seconds?{state:'synced',submission_id:row.id,seconds:job.seconds,error:null}:null;
    };
    const existing=await lists();let payload;
    if(existing){
      payload=await edit(existing);
      const previous=timeSeconds(payload.general.progress);
      if(previous===job.seconds)return {state:'synced',submission_id:existing.id,seconds:job.seconds,error:null};
      if(previous>job.seconds)fail('existing_time_greater');
    }
    if(input.reconcile_only)return {state:'uncertain',error:'write_unverified'};
    if(!payload){
      const time=()=>({hours:null,minutes:null,seconds:null}),entry=()=>({time:time(),notes:''}),date=()=>({year:'0000',month:'00',day:'00'});
      payload={submissionId:0,userIp:'',userId:identity.user_id,userName:identity.username,gameId:job.hltb_id,title:job.title,
        platform:job.platform,storefront:'',lists:{playing:true,backlog:false,replay:false,custom:false,custom2:false,custom3:false,completed:false,retired:false},
        general:{progress:time(),retirementNotes:'',completionDate:date(),startDate:date(),progressBefore:time()},
        singlePlayer:{playCount:false,includesDLC:false,compMain:entry(),compPlus:entry(),comp100:entry()},
        speedRuns:{percAny:entry(),perc100:entry()},multiPlayer:{coOp:{time:time()},vs:{time:time()}},
        review:{score:0,notes:''},additionals:{notes:'',video:''},manualTimer:{time:time()},adminId:null,
        customLabels:{custom:'',custom2:'',custom3:''}};
    }
    payload.general.progress={hours:Math.floor(job.seconds/3600),minutes:Math.floor(job.seconds%3600/60),seconds:job.seconds%60};
    if((await user()).user_id!==identity.user_id)fail('account_changed');
    posted=true;
    // At most one POST. Even a timeout/rejected response is reconciled by reads.
    try{await request('/api/submit',payload);}catch{/* read back below */}
    const verified=await receipt();
    return verified||{state:'uncertain',error:'write_unverified'};
  }catch(error){
    const codes=['sign_in_required','account_changed','ambiguous_entries','existing_time_greater','invalid_response','provider_unavailable','rate_limited'];
    return {state:posted||input.reconcile_only?'uncertain':'failed',error:posted?'write_unverified':codes.includes(error.message)?error.message:'provider_unavailable'};
  }
}
