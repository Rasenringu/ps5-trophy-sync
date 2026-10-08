'use client';
import {Navigation} from './components';
import {LocaleProvider,useLocale} from './i18n';
function Chrome({children,developmentTools}:{children:React.ReactNode;developmentTools:boolean}){const{t}=useLocale();return <><a className="skip-link" href="#main">{t('Skip to content')}</a><Navigation developmentTools={developmentTools}/><div className="app-shell"><header className="topbar"><span>{t('YOUR PERSONAL TROPHY LIBRARY')}</span></header><main id="main">{children}</main><div className="site-footer"><span>TrophySync</span><span>{t('Your progress belongs to you.')}</span></div></div></>;}
export function SiteShell({children,developmentTools=false}:{children:React.ReactNode;developmentTools?:boolean}){return <LocaleProvider><Chrome developmentTools={developmentTools}>{children}</Chrome></LocaleProvider>;}
