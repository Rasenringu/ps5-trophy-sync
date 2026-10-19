import {test,expect,Page} from '@playwright/test';

// Synthetic routed responses only. No hardware support claim or console contact.
const base={profile_uuid:'MOCK',profile_label:'MOCK profile',source:'ps5_native',mock:false,artwork_url:null,icon_url:null};
function session(title:string,seconds:number|null,extra:Record<string,unknown>={}){
 return {...base,kind:'activity',data:{title_id:title,title,complete:seconds!==null,duration_seconds:seconds,
  duration_basis:'native_foreground_seconds',consistency:'sqlite_read_transaction',
  profile_binding:'activity_header_single_local_user',clock:'uncertain',...extra}};
}
async function mockLibrary(page:Page,rows:unknown[]){
 await page.route('**/api/account/me',r=>r.fulfill({json:{email:'mock-sorting@example.test'}}));
 await page.route('**/api/account/devices',r=>r.fulfill({json:[]}));
 await page.route('**/api/account/library**',r=>r.fulfill({json:rows}));
}

test('hours and sessions sort by eligible exact totals with deterministic title ties',async({page})=>{
 const rows=[session('MOCK Alpha',7200),session('MOCK Beta',3700),session('MOCK Beta',3700),
  session('MOCK Gamma',100),session('MOCK Gamma',100),session('MOCK Gamma',100),
  session('MOCK Unknown',null),session('MOCK Unknown',999999,{duration_basis:'unverified'}),
  session('MOCK Zero',0),session('MOCK No activity',null)];
 await mockLibrary(page,rows);await page.goto('/');
 const sort=page.getByRole('combobox',{name:'Sort games'});
 await expect(sort).toHaveValue('recent');
 await sort.selectOption('hours');
 await expect(page.locator('.game-card h2')).toHaveText(['MOCK Beta','MOCK Alpha','MOCK Gamma','MOCK No activity','MOCK Unknown','MOCK Zero']);
 await expect(page.locator('.total-playtime')).toHaveText('4h 8m');
 await sort.selectOption('sessions');
 await expect(page.locator('.game-card h2')).toHaveText(['MOCK Gamma','MOCK Beta','MOCK Alpha','MOCK Zero','MOCK No activity','MOCK Unknown']);
 await expect(page.locator('.game-card').filter({hasText:'MOCK Zero'}).locator('.playtime')).toHaveText('0h 0m recorded across 1 sessions');
 await page.getByRole('searchbox',{name:'Search games'}).fill('Beta');
 await expect(page.locator('.game-card h2')).toHaveText(['MOCK Beta']);
 await page.getByRole('searchbox',{name:'Search games'}).fill('');
 await page.getByRole('button',{name:'Cards',exact:true}).click();
 await page.setViewportSize({width:390,height:844});
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
});

test('shared library sorting uses aggregated session_count rather than row count',async({page})=>{
 const rows=[session('MOCK One session',7200,{duration_basis:'shared_total',session_count:1}),
  session('MOCK Twelve sessions',3600,{duration_basis:'shared_total',session_count:12}),
  session('MOCK Unknown',null,{duration_basis:'shared_total',session_count:0})];
 await page.route('**/api/players/mock_sort',r=>r.fulfill({json:{handle:'mock_sort',display_name:'MOCK shared player',
  relationship:'none',viewer_authenticated:false,library_visible:true}}));
 await page.route('**/api/players/mock_sort/library**',r=>r.fulfill({json:rows}));
 await page.goto('/players/mock_sort');
 const sort=page.getByRole('combobox',{name:'Sort games'});
 await sort.selectOption('sessions');
 await expect(page.locator('.game-card h2')).toHaveText(['MOCK Twelve sessions','MOCK One session','MOCK Unknown']);
 await expect(page.locator('.game-card').first().locator('.playtime')).toHaveText('1h 0m recorded across 12 sessions');
 await sort.selectOption('hours');
 await expect(page.locator('.game-card h2')).toHaveText(['MOCK One session','MOCK Twelve sessions','MOCK Unknown']);
});

test('collection card includes distinct component trophies and a single playtime total',async({page})=>{
 const collection={collection_title_id:'CUSA02344',collection_title:'MOCK Nathan Drake Collection'};
 let hidden=false;
 const rows=[{...session('MOCK launcher',65),source:'ps4_bc',data:{...session('MOCK launcher',65).data,title_id:'CUSA02344',...collection}},
  {...session('MOCK component 0',300),source:'ps4_bc',data:{...session('MOCK component 0',300).data,title_id:'NPWR09798_00',collection_component_title_id:'NPWR09798_00',...collection}},
  ...['NPWR09798_00','NPWR09799_00'].flatMap((title,index)=>[0,1].map(id=>({...base,source:'ps4_bc',kind:'trophy',
   data:{title_id:title,title:'MOCK component '+index,trophy_id:String(id),name:'MOCK trophy '+index+':'+id,
    grade:'bronze',unlocked:false,...collection}})))];
 await page.route('**/api/account/me',r=>r.fulfill({json:{email:'mock-collection@example.test'}}));
 await page.route('**/api/account/devices',r=>r.fulfill({json:[]}));
 await page.route('**/api/account/library**',r=>r.fulfill({json:rows.map(row=>({...row,game_hidden:hidden}))}));
 await page.route('**/api/account/games/visibility',r=>{
  expect(r.request().postDataJSON()).toEqual({source:'ps4_bc',title_id:'CUSA02344',hidden:!hidden});
  hidden=!hidden;return r.fulfill({json:{hidden}});
 });
 const errors:string[]=[];page.on('console',message=>{if(message.type()==='error')errors.push(message.text());});
 await page.goto('/');
 await expect(page.locator('.game-card')).toHaveCount(1);
 await expect(page.locator('.game-card h2')).toHaveText('MOCK Nathan Drake Collection');
 await expect(page.getByText('0/4 recorded trophies unlocked',{exact:true})).toBeVisible();
 await expect(page.getByText('0h 6m recorded across 2 sessions',{exact:true})).toBeVisible();
 await expect(page.locator('.total-playtime')).toHaveText('0h 6m');
 await page.getByRole('button',{name:'View trophies for MOCK Nathan Drake Collection',exact:true}).click();
 const dialog=page.getByRole('dialog');
 await expect(dialog.locator('.collection-game-open')).toHaveCount(2);
 await expect(dialog.locator('.collection-shared-time')).toContainText('0h 1m recorded across 1 sessions');
 await dialog.getByRole('button',{name:'View MOCK component 0 in this collection',exact:true}).click();
 await expect(dialog.getByRole('heading',{name:'MOCK component 0',exact:true})).toBeVisible();
 await expect(page.locator('.trophy-list li')).toHaveCount(2);
 await expect(dialog.getByText('0h 5m',{exact:true})).toBeVisible();
 for(const id of [0,1])await expect(dialog.getByRole('heading',{name:`MOCK trophy 0:${id}`,exact:true})).toBeVisible();
 await dialog.getByRole('button',{name:'Back to collection',exact:true}).click();
 await dialog.getByRole('button',{name:'View MOCK component 1 in this collection',exact:true}).click();
 await expect(dialog.getByText('Playtime not available separately',{exact:true})).toBeVisible();
 await expect(dialog.getByRole('heading',{name:'MOCK trophy 1:0',exact:true})).toBeVisible();
 await expect(dialog.getByRole('heading',{name:'MOCK trophy 0:0',exact:true})).toHaveCount(0);
 await page.getByRole('button',{name:'Close trophies',exact:true}).click();
 await page.setViewportSize({width:390,height:844});
 await page.locator('.game-card .collection-groups>summary').click();
 await expect(page.getByRole('button',{name:'View MOCK component 0 in this collection',exact:true})).toBeVisible();
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 await page.getByRole('searchbox',{name:'Search games'}).fill('component 1');
 await expect(page.locator('.game-card')).toHaveCount(1);
 await page.getByRole('button',{name:'Hide MOCK Nathan Drake Collection',exact:true}).click();
 await expect(page.locator('.game-card')).toHaveCount(0);
 await page.getByRole('button',{name:/^Hidden Games/}).click();
 await expect(page.locator('.game-card')).toHaveCount(1);
 await page.getByRole('button',{name:'Unhide MOCK Nathan Drake Collection',exact:true}).click();
 await page.getByRole('button',{name:'Game collection',exact:true}).click();
 await expect(page.locator('.game-card')).toHaveCount(1);
 expect(errors.filter(message=>/same key|unique.*key/i.test(message))).toEqual([]);
 if(process.env.COLLECTION_SCREENSHOT_DIR){
  await page.getByRole('button',{name:'Cards',exact:true}).click();
  await page.locator('.game-card .collection-groups').evaluate(element=>(element as HTMLDetailsElement).open=true);
  await page.evaluate(()=>{const label=document.createElement('p');label.textContent='SYNTHETIC UI PREVIEW — NO CONSOLE EVIDENCE';document.querySelector('main')?.prepend(label);});
  for(const width of [390,1440]){await page.setViewportSize({width,height:1000});await page.screenshot({path:process.env.COLLECTION_SCREENSHOT_DIR+`/collection-${width}.png`,fullPage:true});}
 }
});

test('public collection subgroups retain separate aggregated component time',async({page})=>{
 const collection={collection_title_id:'CUSA02344',collection_title:'MOCK public collection'};
 const rows=[{...base,source:'ps4_bc',kind:'trophy',data:{title_id:'NPWR09798_00',title:'MOCK public component',
  trophy_id:'0',name:'MOCK public trophy',grade:'bronze',unlocked:false,collection_component_title_id:'NPWR09798_00',...collection}},
  {...session('MOCK public component',120),source:'ps4_bc',data:{...session('MOCK public component',120).data,
   title_id:'NPWR09798_00',duration_basis:'shared_total',session_count:1,...collection}},
  {...session('MOCK public component',300),source:'ps4_bc',data:{...session('MOCK public component',300).data,
   title_id:'NPWR09798_00',duration_basis:'shared_total',session_count:3,collection_component_title_id:'NPWR09798_00',...collection}}];
 await page.route('**/api/players/mock_collection',r=>r.fulfill({json:{handle:'mock_collection',display_name:'MOCK player',
  relationship:'none',viewer_authenticated:false,library_visible:true}}));
 await page.route('**/api/players/mock_collection/library**',r=>r.fulfill({json:rows}));
 await page.goto('/players/mock_collection');
 await expect(page.locator('.game-card')).toHaveCount(1);
 await expect(page.locator('.game-card>.game-body>.playtime')).toHaveText('0h 7m recorded across 4 sessions');
 await page.getByRole('button',{name:'View trophies for MOCK public collection',exact:true}).click();
 await expect(page.getByRole('dialog').locator('.collection-shared-time')).toContainText('0h 2m recorded across 1 sessions');
 await page.getByRole('dialog').getByRole('button',{name:'View MOCK public component in this collection',exact:true}).click();
 await expect(page.getByRole('dialog').getByText('0h 5m',{exact:true})).toBeVisible();
 await expect(page.getByRole('heading',{name:'MOCK public trophy',exact:true})).toBeVisible();
 await expect(page.getByRole('button',{name:'Hide game',exact:true})).toHaveCount(0);
});
