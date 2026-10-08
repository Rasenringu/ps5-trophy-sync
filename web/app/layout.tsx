import './style.css';
import {SiteShell} from './site-shell';
export const metadata={title:'TrophySync · Your collection',description:'Your games, trophies and playtime'};
export default function Layout({children}:{children:React.ReactNode}){return <html lang="en"><body><SiteShell developmentTools={process.env.ENABLE_LOCAL_TESTS==='true'}>{children}</SiteShell></body></html>;}
