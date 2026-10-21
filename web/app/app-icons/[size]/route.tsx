import {ImageResponse} from 'next/og';
import {AppIcon} from '../../app-icon';
export async function GET(_request:Request,{params}:{params:Promise<{size:string}>}){
 const {size}=await params;
 if(size!=='192'&&size!=='512')return new Response('Not found',{status:404});
 const pixels=Number(size);
 return new ImageResponse(<AppIcon/>,{width:pixels,height:pixels,headers:{'Cache-Control':'public, max-age=86400'}});
}
