// Meta Pixel (browser side) and the first-touch attribution cookie.
//
// Server-side helpers only: the snippets are strings that
// components/MetaPixel.astro renders inline into every <head>. Pages fire
// events through `window.iaTrack(name, params, eventId)`, which exists on every
// page — as the real pixel when it is on, as a no-op when it is off — so no page
// has to know whether measurement is enabled.
import { cookies } from './prefs';

// Same runtime fallback as site.ts: the value is read when the server answers,
// not baked into the image, so turning the pixel on is an env change, not a build.
const RAW = String(import.meta.env.PUBLIC_META_PIXEL_ID ?? process.env.PUBLIC_META_PIXEL_ID ?? '').trim();
// Set but wrong is a misconfiguration, not "no pixel": refuse to boot.
if (RAW && !/^\d{6,20}$/.test(RAW)) throw new Error('PUBLIC_META_PIXEL_ID must be the numeric Meta dataset id');

export const META_PIXEL_ID = RAW;
/** Visitor opted out on /privacidad. One year, first-party, honoured server-side. */
export const COOKIE_NO_ADS = 'no_ads';
/** First touch: which ad or campaign brought this browser. Ours, 90 days. */
export const COOKIE_ATTR = 'ia_attr';

export const pixelConfigured = (): boolean => META_PIXEL_ID !== '';

export function pixelEnabled(request: Request): boolean {
  return pixelConfigured() && cookies(request)[COOKIE_NO_ADS] !== '1';
}

/**
 * Records utm_* / fbclid from the landing URL once, first touch wins. Read by the
 * api when checkout starts, so a sale can be tied to the ad that brought the
 * buyer without depending on Meta's own attribution.
 */
export function attributionSnippet(): string {
  return `(function(){if(/(^|; )no_ads=1(;|$)/.test(document.cookie))return;try{var q=new URLSearchParams(location.search),a={},k=['utm_source','utm_medium','utm_campaign','utm_content','utm_term','fbclid'];`
    + `for(var i=0;i<k.length;i++){var v=q.get(k[i]);if(v)a[k[i].replace('utm_','')]=v.slice(0,200);}`
    + `if(!Object.keys(a).length||/(^|; )${COOKIE_ATTR}=/.test(document.cookie))return;`
    + `a.landing=location.pathname.slice(0,120);a.ts=Date.now();`
    + `document.cookie='${COOKIE_ATTR}='+encodeURIComponent(JSON.stringify(a))+'; Max-Age=7776000; Path=/; SameSite=Lax'+(location.protocol==='https:'?'; Secure':'');}catch(e){}})();`;
}

/** Meta's standard bootstrap plus the `iaTrack` wrapper. The id is validated above. */
export function pixelSnippet(id: string): string {
  return `if(/(^|; )no_ads=1(;|$)/.test(document.cookie)){window.iaTrack=function(){};}else{!function(f,b,e,v,n,t,s){if(f.fbq)return;n=f.fbq=function(){n.callMethod?n.callMethod.apply(n,arguments):n.queue.push(arguments)};`
    + `if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';n.queue=[];t=b.createElement(e);t.async=!0;t.src=v;`
    + `s=b.getElementsByTagName(e)[0];s.parentNode.insertBefore(t,s)}(window,document,'script','https://connect.facebook.net/en_US/fbevents.js');`
    + `fbq('init','${id}');fbq('track','PageView');`
    + `window.iaTrack=function(n,p,id){try{fbq('track',n,p||{},id?{eventID:id}:undefined)}catch(e){}};} `;
}

export const noopSnippet = (): string => 'window.iaTrack=function(){};';
