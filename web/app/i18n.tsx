'use client';
import {createContext,useContext,useEffect,useState} from 'react';
import french from './messages/fr.json';
import german from './messages/de.json';
import portuguese from './messages/pt.json';
import brazilianPortuguese from './messages/pt-BR.json';
import spanish from './messages/es.json';
import italian from './messages/it.json';
type Params=Record<string,string|number>;
type Language='en'|'fr'|'de'|'pt'|'pt-BR'|'es'|'it';
const messages:Partial<Record<Language,Record<string,string>>>={fr:french,de:german,pt:portuguese,'pt-BR':brazilianPortuguese,es:spanish,it:italian};
export function interfaceLanguage(languages:readonly string[]):Language{
 for(const language of languages){const tag=language.toLowerCase();const primary=tag.split('-')[0];if(tag==='pt-br')return 'pt-BR';if(['en','fr','de','pt','es','it'].includes(primary))return primary as Language;}return 'en';
}
export function translateText(source:string,params:Params={},language?:Language){const selected=language||(typeof navigator==='undefined'?'en':interfaceLanguage(navigator.languages));return (messages[selected]?.[source]||source).replace(/\{(\w+)\}/g,(match,key)=>key in params?String(params[key]):match);}
const LocaleContext=createContext({locale:'en' as Language,preferences:'en-US',browserLocale:'en-US',ready:false,t:(source:string,params:Params={})=>translateText(source,params,'en')});
export function LocaleProvider({children}:{children:React.ReactNode}){
 const[settings,setSettings]=useState({locale:'en' as Language,preferences:'en-US',browserLocale:'en-US',ready:false});
 useEffect(()=>{function detect(){const languages=(navigator.languages?.length?navigator.languages:[navigator.language||'en-US']).slice(0,8);const locale=interfaceLanguage(languages);let browserLocale=languages[0];try{browserLocale=Intl.getCanonicalLocales(browserLocale)[0];}catch{browserLocale=locale;}setSettings({locale,preferences:languages.join(',').slice(0,160),browserLocale,ready:true});document.documentElement.lang=locale;document.title='TrophySync · '+translateText('Your library',{},locale);}detect();window.addEventListener('languagechange',detect);return()=>window.removeEventListener('languagechange',detect);},[]);
 return <LocaleContext.Provider value={{...settings,t:(source,params={})=>translateText(source,params,settings.locale)}}>{children}</LocaleContext.Provider>;
}
export function useLocale(){return useContext(LocaleContext);}
