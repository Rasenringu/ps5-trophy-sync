import {test,expect,request} from '@playwright/test';
import {randomUUID} from 'node:crypto';

test('registration, explicit pairing, mock isolation, device revocation and login',async({page})=>{
  // Node API requests do not use Chromium's Docker localhost DNS mapping.
  const device = await request.newContext({baseURL:'http://host.docker.internal:3000'});
  const email='browser-test-'+randomUUID()+'@example.test';
  const password='browser-test-password-123';
  await page.goto('/login');
  await page.getByRole('button',{name:'Create an account',exact:true}).click();
  await page.getByLabel('Email',{exact:true}).fill(email);
  await page.getByLabel('Password',{exact:true}).fill(password);
  await page.getByRole('button',{name:'Register',exact:true}).click();
  await expect(page.getByRole('heading',{name:'Your library',exact:true})).toBeVisible();
  const i=await (await device.post('/api/device/installations')).json();
  const p=await (await device.post('/api/device/pairings',{
    headers:{authorization:'Bearer '+i.installation_secret},
    data:{installation_id:i.installation_id,profile_id:'MOCK_BROWSER_PROFILE',profile_label:'MOCK browser console'}})).json();
  expect(p.user_code).toBeTruthy();
  await page.goto('/pair?code='+p.user_code);
  await page.getByRole('button',{name:'Check code',exact:true}).click();
  await expect(page.getByRole('link',{name:'Console profiles',exact:true})).toHaveAttribute('href','/connections');
  await expect(page.getByRole('button',{name:'Approve profile',exact:true})).toBeDisabled();
  await page.getByRole('checkbox').check();
  await page.getByRole('button',{name:'Approve profile',exact:true}).click();
  await expect(page.getByRole('heading',{name:'Profile approved',exact:true})).toBeVisible();
  const credential=await (await device.post('/api/device/pairings/poll',{data:{device_code:p.device_code}})).json();
  expect(credential.device_token).toBeTruthy();
  await page.goto('/');
  const developmentTools=await page.getByRole('checkbox',{name:'Include clearly labeled mock test imports',exact:true}).count()>0;
  if(developmentTools){
  const sync=await device.post('/api/device/sync',{
    headers:{authorization:'Bearer '+credential.device_token},data:{schema_version:1,batch_id:randomUUID(),source:'ps5_native',mock:true,
      trophies:[{title_id:'MOCK001',title:'MOCK browser game',trophy_id:'0',name:'MOCK trophy',grade:'platinum',unlocked:true,unlocked_at:null}],
      activities:[{event_id:'MOCK_EVENT',title_id:'MOCK001',title:'MOCK browser game',complete:false,clock:'unknown',duration_seconds:null}]}});
  expect(sync.status()).toBe(200);
  await page.goto('/');
  await expect(page.getByRole('link',{name:'Console profiles',exact:true})).toHaveAttribute('href','/connections');
  await expect(page.getByRole('heading',{name:'MOCK browser game',exact:true})).toHaveCount(0);
  await page.getByRole('checkbox').check();
  await expect(page.getByRole('heading',{name:'MOCK browser game',exact:true})).toBeVisible();
  await expect(page.getByText('MOCK TEST DATA — NO HARDWARE EVIDENCE',{exact:true})).toBeVisible();
  // Synthetic v2 observations verify unknown states and absent playtime without
  // touching the console or treating the fixtures as hardware evidence.
  const nativeSync=await device.post('/api/device/sync',{
    headers:{authorization:'Bearer '+credential.device_token},data:{schema_version:2,batch_id:randomUUID(),source:'ps5_native',mock:true,
      consistency:'stable_read_not_atomic',profile_binding:'foreground_user_path_scoped',activities:[],
      trophies:[
        {title_id:'MOCK_NATIVE',title:'MOCK native observations',trophy_id:'0',name:'MOCK unknown state',grade:'bronze',unlocked:null,unlocked_at:null,clock:'unknown',native_observation:{raw_flags:16,first_raw:'0',second_raw:'63926921220000000'}},
        {title_id:'MOCK_NATIVE',title:'MOCK native observations',trophy_id:'1',name:'MOCK uncertain time',grade:'bronze',unlocked:true,unlocked_at:'2026-10-06T22:07:00Z',clock:'uncertain',native_observation:{raw_flags:17,first_raw:'63926921220000000',second_raw:'63926921220000000'}}]}});
  expect(nativeSync.status()).toBe(200);
  await page.reload();
  await page.getByRole('checkbox').check();
  const nativeCard=page.locator('section').filter({has:page.getByRole('heading',{name:'MOCK native observations',exact:true})});
  await expect(nativeCard.getByText('1 trophy states are unknown.',{exact:true})).toBeVisible();
  await expect(nativeCard.getByText('Playtime unavailable: no complete sessions with trusted clocks.',{exact:true})).toBeVisible();
  await expect(nativeCard.getByText(/0h 0m/)).toHaveCount(0);
  await nativeCard.getByRole('button',{name:'View trophies for MOCK native observations',exact:true}).click();
  const gameDialog=page.getByRole('dialog');
  await expect(gameDialog.locator('li').filter({has:page.getByRole('heading',{name:'MOCK unknown state',exact:true})}).getByText('State unknown',{exact:true})).toBeVisible();
  await expect(gameDialog.getByText(/console time uncertain/)).toHaveCount(0);
  await expect(gameDialog.getByText('✓ Earned',{exact:true})).toBeVisible();
  await gameDialog.getByLabel('Show trophies',{exact:true}).selectOption('unknown');
  await expect(gameDialog.getByRole('heading',{name:'MOCK uncertain time',exact:true})).toHaveCount(0);
  await gameDialog.getByLabel('Show trophies',{exact:true}).selectOption('all');
  await page.keyboard.press('Escape');
  await expect(page.getByRole('dialog')).toHaveCount(0);
  await expect(nativeCard.getByRole('button',{name:'View trophies for MOCK native observations',exact:true})).toBeFocused();
  await page.getByLabel('Search games',{exact:true}).fill('native observations');
  await expect(page.getByRole('heading',{name:'MOCK browser game',exact:true})).toHaveCount(0);
  await page.getByLabel('Search games',{exact:true}).fill('no matches here');
  await expect(page.getByRole('heading',{name:'No matching games',exact:true})).toBeVisible();
  await page.getByRole('button',{name:'Clear search',exact:true}).click();

  }else{
    const denied=await device.post('/api/device/sync',{headers:{authorization:'Bearer '+credential.device_token},data:{schema_version:1,batch_id:randomUUID(),source:'ps5_native',mock:true,trophies:[],activities:[]}});
    expect(denied.status()).toBe(422);
    await expect(page.getByRole('heading',{name:'MOCK browser game',exact:true})).toHaveCount(0);
  }
  await page.setViewportSize({width:390,height:844});
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBe(true);
  await page.goto('/connections');
  await page.getByRole('button',{name:'Disconnect console',exact:true}).click();
  await expect(page.getByRole('button',{name:'Disconnect console',exact:true})).toHaveCount(0);
  await page.goto('/');
  await page.getByRole('button',{name:'Sign out',exact:true}).click();
  await expect(page.getByRole('heading',{name:'Welcome back',exact:true})).toBeVisible();
  await page.getByLabel('Email',{exact:true}).fill(email);
  await page.getByLabel('Password',{exact:true}).fill(password);
  await page.getByRole('button',{name:'Sign in',exact:true}).click();
  await expect(page.getByRole('heading',{name:'Your library',exact:true})).toBeVisible();
  await device.dispose();
});
