import {readFile} from 'node:fs/promises';
import {join} from 'node:path';

export const runtime='nodejs';
export const dynamic='force-dynamic';
const files=['manifest.json','background.js','provider.js','popup.html','popup.js','popup.css','README.md'];
function crc32(bytes:Buffer){let crc=0xffffffff;for(const byte of bytes){crc^=byte;for(let bit=0;bit<8;bit++)crc=crc>>>1^((crc&1)?0xedb88320:0);}return (crc^0xffffffff)>>>0;}

export async function GET(){
 const parts:Buffer[]=[],directory:Buffer[]=[];let offset=0;
 for(const file of files){
  const name=Buffer.from('trophysync-hltb-browser/'+file),data=await readFile(join(process.cwd(),'connector','hltb-browser',file));
  const local=Buffer.alloc(30);local.writeUInt32LE(0x04034b50);local.writeUInt16LE(20,4);local.writeUInt16LE(0x0800,6);
  local.writeUInt16LE(33,12);local.writeUInt32LE(crc32(data),14);local.writeUInt32LE(data.length,18);local.writeUInt32LE(data.length,22);local.writeUInt16LE(name.length,26);
  const central=Buffer.alloc(46);central.writeUInt32LE(0x02014b50);central.writeUInt16LE(20,4);central.writeUInt16LE(20,6);central.writeUInt16LE(0x0800,8);
  central.writeUInt16LE(33,14);central.writeUInt32LE(crc32(data),16);central.writeUInt32LE(data.length,20);central.writeUInt32LE(data.length,24);central.writeUInt16LE(name.length,28);central.writeUInt32LE(offset,42);
  parts.push(local,name,data);directory.push(central,name);offset+=local.length+name.length+data.length;
 }
 const index=Buffer.concat(directory),end=Buffer.alloc(22);end.writeUInt32LE(0x06054b50);end.writeUInt16LE(files.length,8);end.writeUInt16LE(files.length,10);end.writeUInt32LE(index.length,12);end.writeUInt32LE(offset,16);
 return new Response(new Uint8Array(Buffer.concat([...parts,index,end])),{headers:{'Content-Type':'application/zip','Content-Disposition':'attachment; filename="trophysync-hltb-browser.zip"','Cache-Control':'no-store','X-Content-Type-Options':'nosniff'}});
}
