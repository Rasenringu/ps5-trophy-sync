import type {MetadataRoute} from 'next';
export default function manifest():MetadataRoute.Manifest{return {
 id:'/',name:'TrophySync',short_name:'TrophySync',description:'Your games, trophies and playtime',
 start_url:'/',scope:'/',display:'standalone',background_color:'#080e1b',theme_color:'#080e1b',
 icons:[192,512].flatMap(size=>(['any','maskable'] as const).map(purpose=>({src:'/app-icons/'+size,sizes:size+'x'+size,type:'image/png',purpose})))
};}
