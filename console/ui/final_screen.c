/* SPDX-License-Identifier: GPL-3.0-or-later */
/* Native software renderer; no network, file writes, credentials or new SDK API. */
#include "final_screen.h"
#include "../vendor/qrcodegen.h"
#include <stdio.h>
#include <string.h>

typedef struct {unsigned code,offset;int width,height,left,top,advance;} FontGlyph;
typedef struct {int size;unsigned first,count;} FontSize;
#include "font.inc"
enum {BG=0xff101116,PANEL=0xff191a21,BORDER=0xff30313e,WHITE=0xfff3f2f7,
      MUTED=0xffaaaab9,ACCENT=0xffb6a0ff,GREEN=0xff9cddba,GOLD=0xffdfc593,RED=0xfff0aaaa};
#ifndef TS_UI_FRENCH
#define TS_UI_FRENCH 1
#endif
#define L(fr,en) (TS_UI_FRENCH?(fr):(en))

static void box(uint32_t *p,int x,int y,int w,int h,uint32_t c){
    for(int j=y<0?0:y;j<y+h&&j<SCREEN_HEIGHT;j++)
        for(int i=x<0?0:x;i<x+w&&i<SCREEN_WIDTH;i++)p[j*SCREEN_WIDTH+i]=c;
}
static void rounded(uint32_t *p,int x,int y,int w,int h,int r,uint32_t c){
    for(int j=0;j<h;j++)for(int i=0;i<w;i++){
        int dx=i<r?r-i:i>=w-r?i-(w-r-1):0;
        int dy=j<r?r-j:j>=h-r?j-(h-r-1):0;
        if(dx*dx+dy*dy<=r*r&&x+i>=0&&x+i<SCREEN_WIDTH&&y+j>=0&&y+j<SCREEN_HEIGHT)p[(y+j)*SCREEN_WIDTH+x+i]=c;
    }
}
static void panel(uint32_t *p,int x,int y,int w,int h){rounded(p,x,y,w,h,20,BORDER);rounded(p,x+1,y+1,w-2,h-2,19,PANEL);}
static uint32_t blend(uint32_t base,uint32_t ink,unsigned alpha){
    unsigned r=(((base>>16)&255)*(255-alpha)+((ink>>16)&255)*alpha+127)/255;
    unsigned g=(((base>>8)&255)*(255-alpha)+((ink>>8)&255)*alpha+127)/255;
    unsigned b=((base&255)*(255-alpha)+(ink&255)*alpha+127)/255;
    return 0xff000000|(r<<16)|(g<<8)|b;
}
/* Bounded UTF-8 decoder: invalid/control bytes are replaced, never interpreted. */
static unsigned codepoint(const char **cursor){
    const unsigned char *s=(const unsigned char*)*cursor;unsigned c=*s++;
    if(c<128){*cursor=(const char*)s;return c<32?'?':c;}
    unsigned count=c>=0xc2&&c<=0xdf?1:c>=0xe0&&c<=0xef?2:c>=0xf0&&c<=0xf4?3:0;
    if(!count){*cursor=(const char*)s;return '?';}
    unsigned result=c&((1u<<(6-count))-1);
    for(unsigned i=0;i<count;i++){if(!s[i]||(s[i]&0xc0)!=0x80){*cursor=(const char*)s;return '?';}result=(result<<6)|(s[i]&63);}
    s+=count;*cursor=(const char*)s;
    if((count==1&&result<128)||(count==2&&result<2048)||(count==3&&result<65536)||result>0x10ffff||(result>=0xd800&&result<=0xdfff))return '?';
    return result;
}
static const FontGlyph *glyph(int size,unsigned point){
    const FontSize *font=&font_sizes[0];
    for(unsigned i=0;i<sizeof(font_sizes)/sizeof(*font_sizes);i++)if(font_sizes[i].size==size)font=&font_sizes[i];
    const FontGlyph *fallback=NULL;
    for(unsigned i=font->first;i<font->first+font->count;i++){if(font_glyphs[i].code==point)return &font_glyphs[i];if(font_glyphs[i].code=='?')fallback=&font_glyphs[i];}
    return fallback;
}
static void ink(uint32_t *p,int x,int baseline,const FontGlyph *g,uint32_t color){
    if(!g)return;
    for(int j=0;j<g->height;j++)for(int i=0;i<g->width;i++){
        int xx=x+g->left+i,yy=baseline+g->top+j;
        if(xx>=0&&xx<SCREEN_WIDTH&&yy>=0&&yy<SCREEN_HEIGHT){unsigned a=font_coverage[g->offset+j*g->width+i];if(a)p[yy*SCREEN_WIDTH+xx]=blend(p[yy*SCREEN_WIDTH+xx],color,a);}
    }
}
static int width(const char *s,int size){int n=0;while(*s){const FontGlyph *g=glyph(size,codepoint(&s));if(g)n+=g->advance;}return n;}
static void label(uint32_t *p,int x,int top,const char *s,int size,uint32_t color,int max_width){
    int used=0;while(*s){const FontGlyph *g=glyph(size,codepoint(&s));if(!g)continue;
        int reserve=*s?width("…",size):0;
        if(used+g->advance+reserve>max_width){ink(p,x+used,top+size,glyph(size,0x2026),color);return;}
        ink(p,x+used,top+size,g,color);used+=g->advance;
    }
}
static void paragraph(uint32_t *p,int x,int top,const char *s,int size,uint32_t color,int max_width,int lines){
    char line[512]={0};unsigned used=0;int row=0;
    while(*s&&row<lines){
        const char *begin=s;while(*s&&*s!=' ')s++;unsigned length=(unsigned)(s-begin);if(length>190)length=190;
        char word[192];memcpy(word,begin,length);word[length]=0;
        if(used&&width(line,size)+width(word,size)+width(" ",size)>max_width){label(p,x,top+row*(size+12),line,size,color,max_width);row++;used=0;line[0]=0;}
        if(row>=lines)break;
        if(used&&used<sizeof(line)-1)line[used++]=' ';
        if(length>sizeof(line)-used-1)length=(unsigned)(sizeof(line)-used-1);
        memcpy(line+used,word,length);used+=length;line[used]=0;while(*s==' ')s++;
    }
    if(row<lines&&used)label(p,x,top+row*(size+12),line,size,color,max_width);
}
static void line(uint32_t *p,int x0,int y0,int x1,int y1,int weight,uint32_t color){
    int dx=x1-x0,dy=y1-y0,steps=(dx<0?-dx:dx)>(dy<0?-dy:dy)?(dx<0?-dx:dx):(dy<0?-dy:dy);
    if(!steps)return;
    for(int i=0;i<=steps;i++)box(p,x0+dx*i/steps-weight/2,y0+dy*i/steps-weight/2,weight,weight,color);
}
static void trophy(uint32_t *p,int x,int y,int scale,uint32_t color){
    line(p,x+10*scale,y+4*scale,x+30*scale,y+4*scale,2*scale,color);
    line(p,x+10*scale,y+4*scale,x+10*scale,y+18*scale,2*scale,color);
    line(p,x+30*scale,y+4*scale,x+30*scale,y+18*scale,2*scale,color);
    line(p,x+10*scale,y+18*scale,x+20*scale,y+26*scale,2*scale,color);
    line(p,x+30*scale,y+18*scale,x+20*scale,y+26*scale,2*scale,color);
    line(p,x+20*scale,y+26*scale,x+20*scale,y+36*scale,2*scale,color);
    line(p,x+10*scale,y+36*scale,x+30*scale,y+36*scale,2*scale,color);
    line(p,x+4*scale,y+10*scale,x+10*scale,y+10*scale,2*scale,color);
    line(p,x+4*scale,y+10*scale,x+4*scale,y+20*scale,2*scale,color);
    line(p,x+4*scale,y+20*scale,x+13*scale,y+23*scale,2*scale,color);
    line(p,x+30*scale,y+10*scale,x+36*scale,y+10*scale,2*scale,color);
    line(p,x+36*scale,y+10*scale,x+36*scale,y+20*scale,2*scale,color);
    line(p,x+36*scale,y+20*scale,x+27*scale,y+23*scale,2*scale,color);
}
static void badge(uint32_t *p,int x,int y,const char *value,uint32_t color){
    int w=width(value,22)+50;rounded(p,x,y,w,48,24,0xff242430);rounded(p,x+17,y+20,8,8,4,color);label(p,x+35,y+8,value,22,color,w-45);
}
static int complete(const UiModel *m){return m->phase==UI_CONNECTED&&!strncmp(m->sync_status,"Sync complete:",14);}
static int partial(const UiModel *m){unsigned batches,missing,rejected;return complete(m)&&sscanf(m->sync_status,"Sync complete: %u batches. %u missing / %u rejected sets",&batches,&missing,&rejected)==3&&(missing||rejected);}
static const char *activity(const UiModel *m){
    if(strstr(m->error,"Uploading game artwork"))return L("Envoi des images et traductions","Uploading artwork and translations");
    if(strstr(m->error,"foreground sessions"))return L("Lecture des sessions de jeu","Reading game sessions");
    if(strstr(m->sync_status,"sending saved batch"))return L("Envoi sécurisé de vos données","Securely uploading your data");
    if(strstr(m->sync_status,"safely queued"))return L("Préparation des données","Preparing your data");
    return L("Lecture des trophées et du temps de jeu","Reading trophies and playtime");
}
static void qr_panel(uint32_t *p,const char *link){
    uint8_t temp[qrcodegen_BUFFER_LEN_FOR_VERSION(10)],qr[qrcodegen_BUFFER_LEN_FOR_VERSION(10)];
    if(!qrcodegen_encodeText(link,temp,qr,qrcodegen_Ecc_MEDIUM,1,10,qrcodegen_Mask_AUTO,true)){
        paragraph(p,1260,500,L("QR indisponible. Utilisez le code à gauche.","QR unavailable. Use the code on the left."),32,WHITE,470,3);return;
    }
    int n=qrcodegen_getSize(qr),scale=500/(n+8),w=scale*(n+8),x=1266+(500-w)/2,y=320+(500-w)/2;
    box(p,x,y,w,w,0xffffffff);
    for(int j=0;j<n;j++)for(int i=0;i<n;i++)if(qrcodegen_getModule(qr,i,j))box(p,x+(i+4)*scale,y+(j+4)*scale,scale,scale,0xff000000);
}
void ui_render_final(uint32_t *p,const UiModel *input,uint64_t now){
    /* IPC validation is independent; bounded copies also protect direct callers. */
    UiModel model=*input;model.profile[sizeof(model.profile)-1]=0;model.public_origin[sizeof(model.public_origin)-1]=0;model.manual_code[sizeof(model.manual_code)-1]=0;
    model.error[sizeof(model.error)-1]=0;model.reader_status[sizeof(model.reader_status)-1]=0;model.sync_status[sizeof(model.sync_status)-1]=0;const UiModel *m=&model;
    box(p,0,0,SCREEN_WIDTH,SCREEN_HEIGHT,BG);
    rounded(p,96,64,72,72,18,0xff2b2634);trophy(p,109,74,1,GOLD);
    label(p,190,72,"TrophySync",40,WHITE,500);
    label(p,190,122,L("VOS TROPHÉES. VOTRE PROGRESSION.","YOUR TROPHIES. YOUR PROGRESS."),22,MUTED,900);
    badge(p,1410,87,m->phase==UI_CONNECTED?L("Connecté","Connected"):m->phase==UI_PAIRING?L("Association","Pairing"):m->phase==UI_ERROR?L("À vérifier","Needs attention"):L("Connexion…","Connecting…"),m->phase==UI_CONNECTED?GREEN:m->phase==UI_ERROR?RED:ACCENT);
    box(p,96,184,1728,1,BORDER);
    const char *profile=!strncmp(m->profile,"Local profile ",14)?L("Profil PS5 actif","Active PS5 profile"):m->profile[0]?m->profile:L("Sélection en cours","Selecting profile");
    char link[256]={0},buffer[256];int pairing=ui_pairing_link(input,now,link,sizeof(link)),expired=m->phase==UI_PAIRING&&!pairing;
    panel(p,96,226,1080,636);panel(p,1204,226,620,636);
    label(p,140,260,L("PROFIL SÉLECTIONNÉ","SELECTED PROFILE"),22,MUTED,950);
    label(p,140,298,profile,32,WHITE,950);
    if(pairing){
        label(p,140,382,L("Associez votre compte","Link your account"),56,WHITE,975);
        paragraph(p,140,468,L("Scannez le QR, connectez-vous et confirmez ce profil sur TrophySync.","Scan the QR, sign in and confirm this profile on TrophySync."),26,MUTED,890,2);
        label(p,140,575,L("OU SAISISSEZ CE CODE","OR ENTER THIS CODE"),22,MUTED,850);
        label(p,140,611,m->manual_code,88,WHITE,900);
        snprintf(buffer,sizeof(buffer),"%.191s/pair",m->public_origin);label(p,140,731,buffer,26,ACCENT,950);
        unsigned long long ttl=(unsigned long long)((m->expires_at_ms-now+999)/1000);
        snprintf(buffer,sizeof(buffer),L("Expire dans %llu:%02llu","Expires in %llu:%02llu"),ttl/60,ttl%60);badge(p,140,787,buffer,GOLD);
        label(p,1248,263,L("SCANNEZ POUR CONTINUER","SCAN TO CONTINUE"),22,MUTED,535);qr_panel(p,link);
    }else{
        const char *heading=expired?L("Code expiré","Code expired"):m->phase==UI_ERROR?L("Synchronisation interrompue","Sync interrupted"):partial(m)?L("Synchronisation partielle","Partially synced"):complete(m)?L("Votre bibliothèque est à jour","Your library is up to date"):m->phase==UI_CONNECTED?L("Synchronisation en cours","Syncing your collection"):m->phase==UI_DIAGNOSTIC?L("Diagnostic du lecteur","Reader diagnostic"):L("Connexion à votre console","Connecting to your console");
        paragraph(p,140,399,heading,56,WHITE,965,2);
        const char *description=expired?L("Fermez puis rouvrez l’application pour obtenir un nouveau code.","Close and reopen the app to get a new code."):m->phase==UI_ERROR?L("Vérifiez la connexion ou le service indiqué ci-dessous, puis rouvrez l’application pour réessayer.","Check the connection or the service shown below, then reopen the app to retry."):partial(m)?L("Les données disponibles ont été envoyées. Certains jeux sont absents ou n’ont pas pu être lus.","Available data was uploaded. Some games are missing or could not be read."):complete(m)?L("Trophées, images et temps de jeu ont été envoyés. Retrouvez votre collection sur le site.","Trophies, artwork and playtime have been uploaded. Your collection is ready on the website."):m->phase==UI_CONNECTED?activity(m):L("L’application vérifie le profil actif et rejoint le service de synchronisation.","The app checks your active profile and connects to the sync service.");
        paragraph(p,140,565,description,26,MUTED,950,3);
        if(m->phase==UI_ERROR){paragraph(p,140,697,m->error,22,RED,950,3);}
        else if(m->public_origin[0])label(p,140,768,m->public_origin,26,ACCENT,950);
        rounded(p,1392,338,244,244,122,partial(m)?0xff342f22:complete(m)?0xff21352c:m->phase==UI_ERROR||expired?0xff36262a:0xff2c263c);
        if(complete(m)&&!partial(m)){line(p,1452,458,1498,504,10,GREEN);line(p,1498,504,1581,409,10,GREEN);}
        else if(m->phase==UI_ERROR||expired||partial(m)){uint32_t color=partial(m)?GOLD:RED;line(p,1514,397,1514,476,10,color);rounded(p,1507,503,14,14,7,color);}
        else {trophy(p,1434,381,4,ACCENT);}
        const char *state=partial(m)?L("À vérifier","Needs attention"):complete(m)?L("À jour","Up to date"):m->phase==UI_ERROR?L("Action nécessaire","Action required"):expired?L("Nouveau code requis","New code required"):L("Veuillez patienter","Please wait");
        label(p,1260,630,state,32,WHITE,525);
        paragraph(p,1260,702,L("Mode actuel : synchronisation à l’ouverture de l’application.","Current mode: sync when the app opens."),26,MUTED,510,3);
    }
    if(m->mock||m->phase==UI_DIAGNOSTIC)label(p,100,190,m->mock?"APERÇU / PREVIEW — DONNÉES FICTIVES":"DIAGNOSTIC — NO TROPHY IMPORT",22,GOLD,1710);
    panel(p,96,886,1728,96);
    label(p,128,906,L("SYNCHRONISATION","SYNC STATUS"),22,MUTED,305);
    if(m->phase==UI_ERROR)label(p,470,906,m->sync_status[0]?m->sync_status:L("Indisponible","Unavailable"),22,RED,1295);
    else label(p,470,906,partial(m)?L("Certains jeux n’ont pas pu être lus","Some games could not be read"):complete(m)?L("Envoi terminé","Upload complete"):pairing?L("En attente de votre confirmation","Waiting for your confirmation"):expired?L("Aucun code actif","No active code"):m->phase==UI_CONNECTED?activity(m):L("Connexion en cours","Connecting"),22,partial(m)?GOLD:complete(m)?GREEN:MUTED,1295);
    unsigned sets,sessions,incomplete,earned,locked,unknown;
    if(sscanf(m->reader_status,"Native: %u sets; playtime %u complete / %u incomplete",&sets,&sessions,&incomplete)==3)
        snprintf(buffer,sizeof(buffer),L("%u jeux • %u sessions complètes • %u incomplètes","%u games • %u complete sessions • %u incomplete"),sets,sessions,incomplete);
    else if(sscanf(m->reader_status,"Native: %u sets, %u earned, %u locked, %u unknown",&sets,&earned,&locked,&unknown)==4)
        snprintf(buffer,sizeof(buffer),L("%u jeux • %u trophées obtenus • %u verrouillés • %u inconnus","%u games • %u trophies earned • %u locked • %u unknown"),sets,earned,locked,unknown);
    else snprintf(buffer,sizeof(buffer),"%.159s",m->reader_status[0]?m->reader_status:L("Trophées • images • temps de jeu","Trophies • artwork • playtime"));
    label(p,470,943,buffer,22,MUTED,1295);
    label(p,96,1009,L("PS  >  Fermer l’application","PS  >  Close App"),22,MUTED,900);
    label(p,1390,1009,"TrophySync / PS5",22,MUTED,435);
}
