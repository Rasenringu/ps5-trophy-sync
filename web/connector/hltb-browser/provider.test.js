// Synthetic transport fixtures only. No provider accounts or network.
import {test,afterEach} from 'node:test';
import assert from 'node:assert/strict';
import {providerOperation} from './provider.js';

const original=globalThis.fetch;
afterEach(()=>{globalThis.fetch=original;});
const job={id:'a'.repeat(64),hltb_id:123,title:'SYNTHETIC Game',platform:'PlayStation 5',seconds:3500};
const input={operation:'publish',user_id:1234,job,reconcile_only:false};
const time=seconds=>({hours:Math.floor(seconds/3600),minutes:Math.floor(seconds%3600/60),seconds:seconds%60});
function edit(seconds=100){return {submissionId:77,userId:1234,userName:'SYNTHETIC',gameId:123,title:'SYNTHETIC custom title',platform:'PlayStation 5',
 lists:{completed:true,custom:true},general:{progress:time(seconds),completionDate:{year:'2025',month:'12',day:'21'},retirementNotes:'PRIVATE original notes'},
 singlePlayer:{compMain:{time:time(700),notes:'PRIVATE main notes'}},review:{score:8,notes:'PRIVATE review'},additionals:{notes:'PRIVATE notes',video:'PRIVATE video'},unknownFutureField:{keep:'PRIVATE preserved'}};}

function fixture({existing=null,ambiguous=false,timeout=false,commit=true,changed=false,incomplete=false,malformed=false}={}){
 let data=existing?structuredClone(existing):null;const writes=[],calls=[];
 globalThis.fetch=async(path,options)=>{
  calls.push({path,options});assert.equal(options.credentials,'same-origin');assert.equal(options.redirect,'error');
  const json=value=>new Response(JSON.stringify(value),{headers:{'content-type':'application/json'}});
  if(path==='/api/user')return json({data:[{user_id:changed?4321:1234,user_name:'SYNTHETIC'}]});
  if(path==='/api/user/1234/games/list'){
   const row=data?{id:77,game_id:123,platform:'PlayStation 5',invested_pro:100}:null;
   const rows=row?(ambiguous?[row,{...row,id:78}]:[row]):[];
   return json({data:{gamesList:rows,total:incomplete?rows.length+1:rows.length}});
  }
  if(path==='/submit/edit/77'){
   const value=malformed?{...data,userId:9999}:data;
   return new Response('<script id="__NEXT_DATA__" type="application/json">'+JSON.stringify({props:{pageProps:{editData:value}}})+'</script>',{headers:{'content-type':'text/html'}});
  }
  if(path==='/api/submit'){
   const payload=JSON.parse(options.body);writes.push(payload);
   if(commit)data={...payload,submissionId:77};
   if(timeout)throw new TypeError('SYNTHETIC lost response after write');
   return json({status:'success'});
  }
  throw new Error('Unexpected provider URL '+path);
 };
 return {writes,calls};
}

test('new entry publishes an absolute progress total with no completion assertion',async()=>{
 const f=fixture();const result=await providerOperation(input);
 assert.deepEqual(result,{state:'synced',submission_id:77,seconds:3500,error:null});
 assert.equal(f.writes.length,1);const payload=f.writes[0];
 assert.deepEqual(payload.general.progress,time(3500));assert.equal(payload.lists.playing,true);assert.equal(payload.lists.completed,false);
 assert.deepEqual(payload.singlePlayer.compMain.time,{hours:null,minutes:null,seconds:null});
 assert.ok(f.calls.every(c=>c.path.startsWith('/')));
});

test('update preserves existing completion categories notes dates reviews and future fields',async()=>{
 const before=edit();const f=fixture({existing:before});const result=await providerOperation(input);
 assert.equal(result.state,'synced');assert.equal(f.writes.length,1);
 assert.deepEqual(f.writes[0],{...before,general:{...before.general,progress:time(3500)}});
 assert.ok(!JSON.stringify(result).includes('PRIVATE'));
});

test('same total is already synced and a larger provider total is never overwritten',async()=>{
 let f=fixture({existing:edit(3500)});assert.equal((await providerOperation(input)).state,'synced');assert.equal(f.writes.length,0);
 f=fixture({existing:edit(3501)});assert.deepEqual(await providerOperation(input),{state:'failed',error:'existing_time_greater'});assert.equal(f.writes.length,0);
});

test('a lost write response is verified by read-back without a second post',async()=>{
 const f=fixture({timeout:true});assert.equal((await providerOperation(input)).state,'synced');assert.equal(f.writes.length,1);
 assert.equal((await providerOperation({...input,reconcile_only:true})).state,'synced');assert.equal(f.writes.length,1);
});

test('an unverifiable write is uncertain and retry performs only reads',async()=>{
 const f=fixture({commit:false});assert.deepEqual(await providerOperation(input),{state:'uncertain',error:'write_unverified'});
 assert.equal(f.writes.length,1);
 assert.deepEqual(await providerOperation({...input,reconcile_only:true}),{state:'uncertain',error:'write_unverified'});
 assert.equal(f.writes.length,1);
});

test('account change duplicate entries partial lists and mismatched edit ownership fail before writing',async()=>{
 for(const options of [{changed:true},{existing:edit(),ambiguous:true},{incomplete:true},{existing:edit(),malformed:true}]){
  const f=fixture(options);const result=await providerOperation(input);assert.equal(result.state,'failed');assert.equal(f.writes.length,0);
 }
});

test('identity operation returns only the signed-in identity',async()=>{
 fixture();assert.deepEqual(await providerOperation({operation:'identity'}),{user_id:1234,username:'SYNTHETIC'});
});

test('blocked login and non-JSON responses never produce a successful connection',async()=>{
 globalThis.fetch=async()=>new Response('<html>CAPTCHA</html>',{status:403});
 assert.deepEqual(await providerOperation({operation:'identity'}),{state:'failed',error:'sign_in_required'});
 globalThis.fetch=async()=>new Response('<html>login</html>',{headers:{'content-type':'text/html'}});
 assert.equal((await providerOperation({operation:'identity'})).error,'invalid_response');
});
