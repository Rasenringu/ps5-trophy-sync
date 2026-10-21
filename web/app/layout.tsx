import './style.css';
import './modern.css';
import './insights.css';
import {SiteShell} from './site-shell';
import type {Metadata,Viewport} from 'next';
export const metadata:Metadata={title:'TrophySync · Your collection',description:'Your games, trophies and playtime',applicationName:'TrophySync',appleWebApp:{capable:true,title:'TrophySync',statusBarStyle:'black-translucent'},other:{'apple-mobile-web-app-capable':'yes'},formatDetection:{telephone:false}};
export const viewport:Viewport={width:'device-width',initialScale:1,viewportFit:'cover',themeColor:'#080e1b'};
export default function Layout({children}:{children:React.ReactNode}){return <html lang="en"><body><SiteShell developmentTools={process.env.ENABLE_LOCAL_TESTS==='true'}>{children}</SiteShell></body></html>;}
