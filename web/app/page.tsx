import {Library} from './library';
export const dynamic='force-dynamic';
export default function Page(){return <Library developmentTools={process.env.ENABLE_LOCAL_TESTS==='true'}/>;}
