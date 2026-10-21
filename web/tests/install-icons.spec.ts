import {test,expect} from '@playwright/test';

test('all pages offer a real opaque Apple PNG and a standalone manifest without authentication',async({page})=>{
 await page.goto('/login');
 const get=async(url:string)=>page.evaluate(async path=>{const response=await fetch(path);return {status:response.status,type:response.headers.get('content-type')||'',body:Array.from(new Uint8Array(await response.arrayBuffer()))};},url);
 await expect(page.locator('meta[charset]')).toHaveAttribute('charset','utf-8');
 await expect(page.locator('meta[name="apple-mobile-web-app-capable"]')).toHaveAttribute('content','yes');
 await expect(page.locator('meta[name="viewport"]')).toHaveAttribute('content',/viewport-fit=cover/);
 const icon=await page.locator('link[rel="apple-touch-icon"]').getAttribute('href');expect(icon).toBeTruthy();
 const png=await get(icon!);expect(png.status).toBe(200);expect(png.type).toContain('image/png');
 const body=Buffer.from(png.body);expect(body.subarray(0,8).equals(Buffer.from([137,80,78,71,13,10,26,10]))).toBe(true);
 expect(body.readUInt32BE(16)).toBe(180);expect(body.readUInt32BE(20)).toBe(180);
 const fallback=await get('/apple-touch-icon.png');expect(fallback.status).toBe(200);expect(fallback.type).toContain('image/png');
 const corner=await page.evaluate(async url=>{const image=new Image();image.src=url;await image.decode();const canvas=document.createElement('canvas');canvas.width=canvas.height=180;const ctx=canvas.getContext('2d')!;ctx.drawImage(image,0,0);return ctx.getImageData(0,0,1,1).data[3];},icon!);
 expect(corner).toBe(255);
 const link=await page.locator('link[rel="manifest"]').getAttribute('href');const response=await get(link!);expect(response.status).toBe(200);
 const manifest=JSON.parse(Buffer.from(response.body).toString('utf8'));expect(manifest.display).toBe('standalone');expect(manifest.start_url).toBe('/');
 for(const size of [192,512]){const entry=manifest.icons.find((x:any)=>x.sizes===size+'x'+size);expect(entry.type).toBe('image/png');const response=await get(entry.src);expect(response.status).toBe(200);const data=Buffer.from(response.body);expect(data.readUInt32BE(16)).toBe(size);expect(data.readUInt32BE(20)).toBe(size);}
 expect((await get('/app-icons/1')).status).toBe(404);
});
