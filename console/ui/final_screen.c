/* SPDX-License-Identifier: GPL-3.0-or-later */
/* Native software renderer; no network, file writes, credentials or new SDK API. */
#include "final_screen.h"
#include "../vendor/qrcodegen.h"
#include <stdio.h>
#include <string.h>

typedef struct {unsigned code,offset;int width,height,left,top,advance;} FontGlyph;
typedef struct {int size;unsigned first,count;} FontSize;
#include "font.inc"
enum {BG=0xff080e1b,PANEL=0xff101e33,BORDER=0xff304966,WHITE=0xfff4f8ff,
      MUTED=0xffb1c4df,ACCENT=0xff92c7ff,GREEN=0xff9cddba,GOLD=0xffdfc593,RED=0xfff0aaaa};
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
static void panel(uint32_t *p,int x,int y,int w,int h){rounded(p,x,y,w,h,28,BORDER);rounded(p,x+1,y+1,w-2,h-2,27,PANEL);}
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
    int truncate=width(s,size)>max_width;
    int used=0;while(*s){const FontGlyph *g=glyph(size,codepoint(&s));if(!g)continue;
        int reserve=truncate&&*s?width("…",size):0;
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
/* Original trophy plus two sync arcs; shared with the website/title icon. */
static void sync_mark(uint32_t *p,int x,int y,int scale,uint32_t color){
    static const int upper[][2]={{51,23},{48,16},{42,11},{34,9},{26,9},{19,12},{13,17}};
    static const int lower[][2]={{13,41},{16,48},{22,53},{30,55},{38,55},{45,52},{51,47}};
    for(int i=1;i<7;i++){
        line(p,x+upper[i-1][0]*scale,y+upper[i-1][1]*scale,x+upper[i][0]*scale,y+upper[i][1]*scale,2*scale,color);
        line(p,x+lower[i-1][0]*scale,y+lower[i-1][1]*scale,x+lower[i][0]*scale,y+lower[i][1]*scale,2*scale,color);
    }
    line(p,x+13*scale,y+9*scale,x+13*scale,y+17*scale,2*scale,color);
    line(p,x+13*scale,y+17*scale,x+21*scale,y+17*scale,2*scale,color);
    line(p,x+51*scale,y+47*scale,x+51*scale,y+55*scale,2*scale,color);
    line(p,x+43*scale,y+47*scale,x+51*scale,y+47*scale,2*scale,color);
    rounded(p,x+24*scale,y+19*scale,16*scale,21*scale,7*scale,color);
    box(p,x+24*scale,y+19*scale,16*scale,10*scale,color);
    line(p,x+24*scale,y+23*scale,x+19*scale,y+23*scale,2*scale,color);
    line(p,x+19*scale,y+23*scale,x+19*scale,y+31*scale,2*scale,color);
    line(p,x+19*scale,y+31*scale,x+26*scale,y+35*scale,2*scale,color);
    line(p,x+40*scale,y+23*scale,x+45*scale,y+23*scale,2*scale,color);
    line(p,x+45*scale,y+23*scale,x+45*scale,y+31*scale,2*scale,color);
    line(p,x+45*scale,y+31*scale,x+38*scale,y+35*scale,2*scale,color);
    line(p,x+32*scale,y+40*scale,x+32*scale,y+48*scale,2*scale,color);
    line(p,x+25*scale,y+48*scale,x+39*scale,y+48*scale,2*scale,color);
}
static void badge(uint32_t *p,int x,int y,const char *value,uint32_t color){
    int w=width(value,22)+50;rounded(p,x,y,w,48,24,0xff19304c);rounded(p,x+17,y+20,8,8,4,color);label(p,x+35,y+8,value,22,color,w-45);
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
        paragraph(p,1324,490,L("QR indisponible. Utilisez le code affiché.","QR unavailable. Use the displayed code."),26,WHITE,455,3);return;
    }
    int n=qrcodegen_getSize(qr),scale=440/(n+8),w=scale*(n+8),x=1336+(440-w)/2,y=368+(440-w)/2;
    box(p,x,y,w,w,0xffffffff);
    for(int j=0;j<n;j++)for(int i=0;i<n;i++)if(qrcodegen_getModule(qr,i,j))box(p,x+(i+4)*scale,y+(j+4)*scale,scale,scale,0xff000000);
}
static void step(uint32_t *p,int y,const char *number,const char *title,const char *detail,int active,int done){
    if(active)rounded(p,80,y-13,272,112,18,0xff193c68);
    rounded(p,99,y+1,37,37,18,done?0xff204e45:0xff253b56);
    label(p,108,y+3,number,22,done?GREEN:WHITE,25);
    label(p,151,y,title,26,active?WHITE:MUTED,192);
    label(p,151,y+43,detail,22,active?ACCENT:MUTED,190);
}
void ui_render_final(uint32_t *p,const UiModel *input,uint64_t now){
    UiModel model=*input;model.profile[sizeof(model.profile)-1]=0;model.public_origin[sizeof(model.public_origin)-1]=0;model.manual_code[sizeof(model.manual_code)-1]=0;
    model.error[sizeof(model.error)-1]=0;model.reader_status[sizeof(model.reader_status)-1]=0;model.sync_status[sizeof(model.sync_status)-1]=0;const UiModel *m=&model;
    char link[256]={0},buffer[256];int pairing=ui_pairing_link(m,now,link,sizeof(link)),expired=m->phase==UI_PAIRING&&!pairing;
    int finished=complete(m),attention=partial(m)||m->phase==UI_ERROR||expired;
    const char *profile=!strncmp(m->profile,"Local profile ",14)?L("Profil PS5 actif","Active PS5 profile"):m->profile[0]?m->profile:L("Sélection du profil…","Selecting profile…");
    for(int y=0;y<SCREEN_HEIGHT;y+=4)for(int x=0;x<SCREEN_WIDTH;x+=4){
        int dx=x-1620,dy=y-80;
        unsigned glow=dx*dx+dy*dy<1500000?(unsigned)(1500000-dx*dx-dy*dy)/18000:0;
        box(p,x,y,4,4,blend(BG,0xff245ea5,glow));
    }
    /* The website's rail, luminous blue brand and panel hierarchy, at TV scale. */
    panel(p,64,56,304,968);
    rounded(p,100,91,80,80,22,0xff2166ce);sync_mark(p,108,99,1,WHITE);
    label(p,100,193,"TrophySync",40,WHITE,248);
    paragraph(p,100,253,L("Vos trophées. Votre progression.","Your trophies. Your progress."),22,MUTED,232,2);
    box(p,100,336,232,1,BORDER);
    label(p,100,366,L("VOTRE CONSOLE","YOUR CONSOLE"),22,ACCENT,232);
    step(p,430,"1",L("Association","Pair account"),L("Votre compte","Your account"),pairing||expired,m->phase==UI_CONNECTED);
    step(p,567,"2",L("Synchroniser","Sync library"),L("Trophées et jeu","Trophies & time"),m->phase==UI_CONNECTED&&!finished,finished);
    step(p,704,"3",L("Collection","Collection"),L("Sur le site web","On the website"),finished&&!partial(m),finished&&!partial(m));
    box(p,100,878,232,1,BORDER);
    label(p,100,904,"PS5",32,WHITE,232);
    label(p,100,955,L("Sync à l’ouverture","Sync on launch"),22,MUTED,232);

    label(p,408,65,L("VOTRE BIBLIOTHÈQUE PERSONNELLE","YOUR PERSONAL TROPHY LIBRARY"),22,ACCENT,1080);
    label(p,408,113,L("Synchronisation PS5","PS5 synchronization"),56,WHITE,1050);
    badge(p,1560,117,m->phase==UI_CONNECTED?L("Connecté","Connected"):m->phase==UI_PAIRING?L("Association","Pairing"):m->phase==UI_ERROR?L("À vérifier","Needs attention"):L("Connexion…","Connecting…"),m->phase==UI_CONNECTED?GREEN:m->phase==UI_ERROR?RED:ACCENT);
    label(p,408,199,L("Votre progression vous appartient.","Your progress belongs to you."),26,MUTED,1300);
    label(p,408,250,L("PROFIL SÉLECTIONNÉ","SELECTED PROFILE"),22,MUTED,330);
    label(p,760,243,profile,32,WHITE,1050);
    box(p,408,295,1416,1,BORDER);
    panel(p,408,320,852,540);panel(p,1288,320,536,540);
    if(pairing){
        label(p,448,355,L("CONNECTER VOTRE COMPTE","CONNECT YOUR ACCOUNT"),22,ACCENT,770);
        paragraph(p,448,401,L("Retrouvez votre collection.","Bring your collection together."),56,WHITE,758,2);
        paragraph(p,448,550,L("Scannez le QR, connectez-vous et confirmez ce profil. Ou saisissez ce code sur le site :","Scan the QR, sign in and confirm this profile. Or enter this code on the website:"),26,MUTED,740,3);
        label(p,448,665,m->manual_code,88,WHITE,770);
        unsigned long long ttl=(unsigned long long)((m->expires_at_ms-now+999)/1000);
        snprintf(buffer,sizeof(buffer),L("Expire dans %llu:%02llu","Expires in %llu:%02llu"),ttl/60,ttl%60);badge(p,448,789,buffer,GOLD);
        label(p,1328,325,L("SCANNER POUR ASSOCIER","SCAN TO PAIR"),22,MUTED,456);qr_panel(p,link);
        label(p,1328,811,L("Code temporaire · usage unique","Temporary code · single use"),22,MUTED,455);
    }else{
        const char *eyebrow=attention?L("VOTRE ATTENTION EST REQUISE","YOUR ATTENTION IS NEEDED"):finished?L("SYNCHRONISATION TERMINÉE","SYNCHRONIZATION COMPLETE"):L("VOTRE COLLECTION","YOUR COLLECTION");
        label(p,448,355,eyebrow,22,attention?GOLD:ACCENT,770);
        const char *heading=expired?L("Le code a expiré.","The code has expired."):m->phase==UI_ERROR?L("Synchronisation interrompue.","Synchronization interrupted."):partial(m)?L("Une partie reste à vérifier.","Some data needs attention."):finished?L("Votre collection est à jour.","Your collection is up to date."):m->phase==UI_CONNECTED?L("Votre progression, en route.","Your progress is on its way."):m->phase==UI_DIAGNOSTIC?L("Diagnostic du lecteur","Reader diagnostic"):L("Connexion à votre console.","Connecting to your console.");
        paragraph(p,448,405,heading,56,WHITE,754,2);
        const char *description=expired?L("Fermez puis rouvrez l’application pour obtenir un nouveau code.","Close and reopen the app to get a new code."):m->phase==UI_ERROR?L("Vérifiez l’action indiquée ci-dessous, puis rouvrez l’application pour réessayer.","Check the action below, then reopen the app to retry."):partial(m)?L("Les données disponibles ont été envoyées. Certains jeux n’ont pas pu être lus.","Available data was uploaded. Some games could not be read."):finished?L("Trophées et temps de jeu enregistrés sont disponibles sur le site.","Your trophies and recorded playtime are ready on the website."):m->phase==UI_CONNECTED?activity(m):L("Vérification du profil actif et connexion au service de synchronisation.","Checking the active profile and connecting to the synchronization service.");
        paragraph(p,448,563,description,26,MUTED,750,3);
        if(m->phase==UI_ERROR)paragraph(p,448,694,m->error,22,RED,746,3);
        else label(p,448,777,finished?L("Ouvrez le site pour voir votre collection.","Open the website to explore your collection."):L("Gardez l’application ouverte pendant l’envoi.","Keep the app open while uploading."),22,MUTED,750);
        rounded(p,1436,404,240,240,120,attention?0xff392d2b:finished?0xff1c3e38:0xff193c64);
        if(finished&&!partial(m)){line(p,1490,526,1536,572,10,GREEN);line(p,1536,572,1624,475,10,GREEN);}
        else if(attention){line(p,1556,459,1556,545,10,GOLD);rounded(p,1549,574,14,14,7,GOLD);}
        else sync_mark(p,1428,396,4,ACCENT);
        const char *state=partial(m)?L("À vérifier","Needs attention"):finished?L("Tout est prêt","All set"):m->phase==UI_ERROR?L("Action nécessaire","Action required"):expired?L("Nouveau code requis","New code required"):L("Veuillez patienter","Please wait");
        label(p,1328,690,state,32,WHITE,450);
        paragraph(p,1328,751,L("Trophées · images · temps de jeu","Trophies · artwork · playtime"),22,MUTED,448,2);
    }
    /* Independent connection and sync status remain visible in every phase. */
    panel(p,408,884,1416,96);
    label(p,440,900,L("SYNCHRONISATION","SYNC STATUS"),22,MUTED,290);
    label(p,750,900,m->phase==UI_ERROR?(m->sync_status[0]?m->sync_status:L("Indisponible","Unavailable")):partial(m)?L("Certains jeux n’ont pas pu être lus","Some games could not be read"):finished?L("Envoi terminé","Upload complete"):pairing?L("En attente de votre confirmation","Waiting for your confirmation"):expired?L("Aucun code actif","No active code"):m->phase==UI_CONNECTED?activity(m):L("Connexion en cours","Connecting"),22,attention?GOLD:finished?GREEN:WHITE,1030);
    unsigned sets,sessions,incomplete,earned,locked,unknown;
    if(sscanf(m->reader_status,"Native: %u sets; playtime %u complete / %u incomplete",&sets,&sessions,&incomplete)==3)
        snprintf(buffer,sizeof(buffer),L("%u jeux · %u sessions complètes · %u incomplètes","%u games · %u complete sessions · %u incomplete"),sets,sessions,incomplete);
    else if(sscanf(m->reader_status,"Native: %u sets, %u earned, %u locked, %u unknown",&sets,&earned,&locked,&unknown)==4)
        snprintf(buffer,sizeof(buffer),L("%u jeux · %u obtenus · %u verrouillés · %u inconnus","%u games · %u earned · %u locked · %u unknown"),sets,earned,locked,unknown);
    else snprintf(buffer,sizeof(buffer),"%.159s",m->reader_status[0]?m->reader_status:L("Trophées · images · temps de jeu","Trophies · artwork · playtime"));
    label(p,750,938,buffer,22,MUTED,1030);
    snprintf(buffer,sizeof(buffer),"%.191s%s",m->public_origin,pairing?"/pair":"");
    label(p,408,998,buffer,22,ACCENT,965);
    label(p,1410,998,L("PS  >  Fermer l’application","PS  >  Close App"),22,MUTED,414);
    if(m->mock||m->phase==UI_DIAGNOSTIC)label(p,408,12,m->mock?"APERÇU / PREVIEW — DONNÉES FICTIVES":"DIAGNOSTIC — NO TROPHY IMPORT",22,GOLD,1416);
}
