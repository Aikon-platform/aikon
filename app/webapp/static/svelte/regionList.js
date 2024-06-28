var regionList=function(){"use strict";function t(){}const e=t=>t;function n(t){return t()}function o(){return Object.create(null)}function l(t){t.forEach(n)}function c(t){return"function"==typeof t}function i(t,e){return t!=t?e==e:t!==e||t&&"object"==typeof t||"function"==typeof t}let s;function r(t,e){return s||(s=document.createElement("a")),s.href=e,t===s.href}function a(e,n,o){e.$$.on_destroy.push(function(e,...n){if(null==e)return t;const o=e.subscribe(...n);return o.unsubscribe?()=>o.unsubscribe():o}(n,o))}function u(t,e,n,o){return t[1]&&o?function(t,e){for(const n in e)t[n]=e[n];return t}(n.ctx.slice(),t[1](o(e))):n.ctx}const d="undefined"!=typeof window;let f=d?()=>window.performance.now():()=>Date.now(),p=d?t=>requestAnimationFrame(t):t;const g=new Set;function m(t){g.forEach((e=>{e.c(t)||(g.delete(e),e.f())})),0!==g.size&&p(m)}function h(t,e){t.appendChild(e)}function b(t){if(!t)return document;const e=t.getRootNode?t.getRootNode():t.ownerDocument;return e&&e.host?e:t.ownerDocument}function $(t){const e=x("style");return function(t,e){h(t.head||t,e),e.sheet}(b(t),e),e.sheet}function v(t,e,n){t.insertBefore(e,n||null)}function y(t){t.parentNode&&t.parentNode.removeChild(t)}function k(t,e){for(let n=0;n<t.length;n+=1)t[n]&&t[n].d(e)}function x(t){return document.createElement(t)}function w(t){return document.createElementNS("http://www.w3.org/2000/svg",t)}function L(t){return document.createTextNode(t)}function S(){return L(" ")}function E(){return L("")}function N(t,e,n,o){return t.addEventListener(e,n,o),()=>t.removeEventListener(e,n,o)}function P(t){return function(e){return e.preventDefault(),t.call(this,e)}}function C(t,e,n){null==n?t.removeAttribute(e):t.getAttribute(e)!==n&&t.setAttribute(e,n)}function O(t,e){e=""+e,t.data!==e&&(t.data=e)}function _(t,e,n){t.classList[n?"add":"remove"](e)}function z(t,e,{bubbles:n=!1,cancelable:o=!1}={}){const l=document.createEvent("CustomEvent");return l.initCustomEvent(t,n,o,e),l}const V=new Map;let I,A=0;function j(t,e,n,o,l,c,i,s=0){const r=16.666/o;let a="{\n";for(let t=0;t<=1;t+=r){const o=e+(n-e)*c(t);a+=100*t+`%{${i(o,1-o)}}\n`}const u=a+`100% {${i(n,1-n)}}\n}`,d=`__svelte_${function(t){let e=5381,n=t.length;for(;n--;)e=(e<<5)-e^t.charCodeAt(n);return e>>>0}(u)}_${s}`,f=b(t),{stylesheet:p,rules:g}=V.get(f)||function(t,e){const n={stylesheet:$(e),rules:{}};return V.set(t,n),n}(f,t);g[d]||(g[d]=!0,p.insertRule(`@keyframes ${d} ${u}`,p.cssRules.length));const m=t.style.animation||"";return t.style.animation=`${m?`${m}, `:""}${d} ${o}ms linear ${l}ms 1 both`,A+=1,d}function M(t,e){const n=(t.style.animation||"").split(", "),o=n.filter(e?t=>t.indexOf(e)<0:t=>-1===t.indexOf("__svelte")),l=n.length-o.length;l&&(t.style.animation=o.join(", "),A-=l,A||p((()=>{A||(V.forEach((t=>{const{ownerNode:e}=t.stylesheet;e&&y(e)})),V.clear())})))}function R(t){I=t}function T(){if(!I)throw new Error("Function called outside component initialization");return I}function H(){const t=T();return(e,n,{cancelable:o=!1}={})=>{const l=t.$$.callbacks[e];if(l){const c=z(e,n,{cancelable:o});return l.slice().forEach((e=>{e.call(t,c)})),!c.defaultPrevented}return!0}}const B=[],D=[];let U=[];const q=[],F=Promise.resolve();let G=!1;function J(t){U.push(t)}const X=new Set;let Y,K=0;function Q(){if(0!==K)return;const t=I;do{try{for(;K<B.length;){const t=B[K];K++,R(t),W(t.$$)}}catch(t){throw B.length=0,K=0,t}for(R(null),B.length=0,K=0;D.length;)D.pop()();for(let t=0;t<U.length;t+=1){const e=U[t];X.has(e)||(X.add(e),e())}U.length=0}while(B.length);for(;q.length;)q.pop()();G=!1,X.clear(),R(t)}function W(t){if(null!==t.fragment){t.update(),l(t.before_update);const e=t.dirty;t.dirty=[-1],t.fragment&&t.fragment.p(t.ctx,e),t.after_update.forEach(J)}}function Z(t,e,n){t.dispatchEvent(z(`${e?"intro":"outro"}${n}`))}const tt=new Set;let et;function nt(){et={r:0,c:[],p:et}}function ot(){et.r||l(et.c),et=et.p}function lt(t,e){t&&t.i&&(tt.delete(t),t.i(e))}function ct(t,e,n,o){if(t&&t.o){if(tt.has(t))return;tt.add(t),et.c.push((()=>{tt.delete(t),o&&(n&&t.d(1),o())})),t.o(e)}else o&&o()}const it={duration:0};function st(n,o,i,s){const r={direction:"both"};let a=o(n,i,r),u=s?0:1,d=null,h=null,b=null;function $(){b&&M(n,b)}function v(t,e){const n=t.b-u;return e*=Math.abs(n),{a:u,b:t.b,d:n,duration:e,start:t.start,end:t.start+e,group:t.group}}function y(o){const{delay:c=0,duration:i=300,easing:s=e,tick:r=t,css:y}=a||it,k={start:f()+c,b:o};o||(k.group=et,et.r+=1),d||h?h=k:(y&&($(),b=j(n,u,o,i,c,s,y)),o&&r(0,1),d=v(k,i),J((()=>Z(n,o,"start"))),function(t){let e;0===g.size&&p(m),new Promise((n=>{g.add(e={c:t,f:n})}))}((t=>{if(h&&t>h.start&&(d=v(h,i),h=null,Z(n,d.b,"start"),y&&($(),b=j(n,u,d.b,d.duration,0,s,a.css))),d)if(t>=d.end)r(u=d.b,1-u),Z(n,d.b,"end"),h||(d.b?$():--d.group.r||l(d.group.c)),d=null;else if(t>=d.start){const e=t-d.start;u=d.a+d.d*s(e/d.duration),r(u,1-u)}return!(!d&&!h)})))}return{run(t){c(a)?(Y||(Y=Promise.resolve(),Y.then((()=>{Y=null}))),Y).then((()=>{a=a(r),y(t)})):y(t)},end(){$(),d=h=null}}}function rt(t,e){const n=e.token={};function o(t,o,l,c){if(e.token!==n)return;e.resolved=c;let i=e.ctx;void 0!==l&&(i=i.slice(),i[l]=c);const s=t&&(e.current=t)(i);let r=!1;e.block&&(e.blocks?e.blocks.forEach(((t,n)=>{n!==o&&t&&(nt(),ct(t,1,1,(()=>{e.blocks[n]===t&&(e.blocks[n]=null)})),ot())})):e.block.d(1),s.c(),lt(s,1),s.m(e.mount(),e.anchor),r=!0),e.block=s,e.blocks&&(e.blocks[o]=s),r&&Q()}if(!(l=t)||"object"!=typeof l&&"function"!=typeof l||"function"!=typeof l.then){if(e.current!==e.then)return o(e.then,1,e.value,t),!0;e.resolved=t}else{const n=T();if(t.then((t=>{R(n),o(e.then,1,e.value,t),R(null)}),(t=>{if(R(n),o(e.catch,2,e.error,t),R(null),!e.hasCatch)throw t})),e.current!==e.pending)return o(e.pending,0),!0}var l}function at(t,e){ct(t,1,1,(()=>{e.delete(t.key)}))}function ut(t,e,n,o,c,i,s,r,a,u,d,f){let p=t.length,g=i.length,m=p;const h={};for(;m--;)h[t[m].key]=m;const b=[],$=new Map,v=new Map,y=[];for(m=g;m--;){const t=f(c,i,m),l=n(t);let r=s.get(l);r?o&&y.push((()=>r.p(t,e))):(r=u(l,t),r.c()),$.set(l,b[m]=r),l in h&&v.set(l,Math.abs(m-h[l]))}const k=new Set,x=new Set;function w(t){lt(t,1),t.m(r,d),s.set(t.key,t),d=t.first,g--}for(;p&&g;){const e=b[g-1],n=t[p-1],o=e.key,l=n.key;e===n?(d=e.first,p--,g--):$.has(l)?!s.has(o)||k.has(o)?w(e):x.has(l)?p--:v.get(o)>v.get(l)?(x.add(o),w(e)):(k.add(l),p--):(a(n,s),p--)}for(;p--;){const e=t[p];$.has(e.key)||a(e,s)}for(;g;)w(b[g-1]);return l(y),b}function dt(t){t&&t.c()}function ft(t,e,o,i){const{fragment:s,after_update:r}=t.$$;s&&s.m(e,o),i||J((()=>{const e=t.$$.on_mount.map(n).filter(c);t.$$.on_destroy?t.$$.on_destroy.push(...e):l(e),t.$$.on_mount=[]})),r.forEach(J)}function pt(t,e){const n=t.$$;null!==n.fragment&&(!function(t){const e=[],n=[];U.forEach((o=>-1===t.indexOf(o)?e.push(o):n.push(o))),n.forEach((t=>t())),U=e}(n.after_update),l(n.on_destroy),n.fragment&&n.fragment.d(e),n.on_destroy=n.fragment=null,n.ctx=[])}function gt(t,e){-1===t.$$.dirty[0]&&(B.push(t),G||(G=!0,F.then(Q)),t.$$.dirty.fill(0)),t.$$.dirty[e/31|0]|=1<<e%31}function mt(e,n,c,i,s,r,a,u=[-1]){const d=I;R(e);const f=e.$$={fragment:null,ctx:[],props:r,update:t,not_equal:s,bound:o(),on_mount:[],on_destroy:[],on_disconnect:[],before_update:[],after_update:[],context:new Map(n.context||(d?d.$$.context:[])),callbacks:o(),dirty:u,skip_bound:!1,root:n.target||d.$$.root};a&&a(f.root);let p=!1;if(f.ctx=c?c(e,n.props||{},((t,n,...o)=>{const l=o.length?o[0]:n;return f.ctx&&s(f.ctx[t],f.ctx[t]=l)&&(!f.skip_bound&&f.bound[t]&&f.bound[t](l),p&&gt(e,t)),n})):[],f.update(),p=!0,l(f.before_update),f.fragment=!!i&&i(f.ctx),n.target){if(n.hydrate){const t=function(t){return Array.from(t.childNodes)}(n.target);f.fragment&&f.fragment.l(t),t.forEach(y)}else f.fragment&&f.fragment.c();n.intro&&lt(e.$$.fragment),ft(e,n.target,n.anchor,n.customElement),Q()}R(d)}class ht{$destroy(){pt(this,1),this.$destroy=t}$on(e,n){if(!c(n))return t;const o=this.$$.callbacks[e]||(this.$$.callbacks[e]=[]);return o.push(n),()=>{const t=o.indexOf(n);-1!==t&&o.splice(t,1)}}$set(t){var e;this.$$set&&(e=t,0!==Object.keys(e).length)&&(this.$$.skip_bound=!0,this.$$set(t),this.$$.skip_bound=!1)}}function bt(t){localStorage.setItem("documentSet",JSON.stringify(t))}function $t(t,e,n){console.log("coucou");const{[e]:o,...l}=t[n];return t[n]=l,bt(t),t}function vt(t=null,e="full",n="full"){if(!t)return"https://via.placeholder.com/96x96?text=No+Image";if((t=t.split("_")).length<3)return"https://via.placeholder.com/96x96?text=No+Image";const o=t[t.length-1].includes(",")?t.pop().replace(".jpg",""):e,l=t.join("_").replace(".jpg","");return`${CANTALOUPE_APP_URL??"http://localhost:8182"}/iiif/2/${l}.jpg/${o}/${n}/0/default.jpg`}function yt(t=null,e=1){return`${SAS_APP_URL??"http://localhost:3000"}/index.html?iiif-content=${t}&canvas=${e}`}function kt(t,e=null,n=!1){return new Promise((o=>{if(document.getElementById("msg-modal")){n&&(document.getElementById("modal-footer").hidden=!1),e&&(document.getElementById("modal-title").textContent=e),document.getElementById("modal-body").textContent=t,document.getElementById("hidden-msg-btn").click();const l=document.getElementById("cancel-btn"),c=document.getElementById("ok-btn"),i=document.getElementById("modal-bkg"),s=()=>{l.removeEventListener("click",r),i.removeEventListener("click",r),c.removeEventListener("click",a),document.getElementById("modal-footer").hidden=!0},r=()=>{s(),o(!1)},a=()=>{s(),o(!0)};l.addEventListener("click",r),c.addEventListener("click",a)}else n?o(window.confirm(t)):(window.alert(t),o(void 0))}))}const xt=[];function wt(t,{delay:n=0,duration:o=400,easing:l=e}={}){const c=+getComputedStyle(t).opacity;return{delay:n,duration:o,easing:l,css:t=>"opacity: "+t*c}}function Lt(t){let e;return{c(){e=w("path"),C(e,"d","M384 336H192c-8.8 0-16-7.2-16-16V64c0-8.8 7.2-16 16-16l140.1 0L400 115.9V320c0 8.8-7.2 16-16 16zM192 384H384c35.3 0 64-28.7 64-64V115.9c0-12.7-5.1-24.9-14.1-33.9L366.1 14.1c-9-9-21.2-14.1-33.9-14.1H192c-35.3 0-64 28.7-64 64V320c0 35.3 28.7 64 64 64zM64 128c-35.3 0-64 28.7-64 64V448c0 35.3 28.7 64 64 64H256c35.3 0 64-28.7 64-64V416H272v32c0 8.8-7.2 16-16 16H64c-8.8 0-16-7.2-16-16V192c0-8.8 7.2-16 16-16H96V128H64z"),C(e,"class","svelte-l0tzvr")},m(t,n){v(t,e,n)},d(t){t&&y(e)}}}function St(t){let e;return{c(){e=w("path"),C(e,"d","M208 0H332.1c12.7 0 24.9 5.1 33.9 14.1l67.9 67.9c9 9 14.1 21.2 14.1 33.9V336c0 26.5-21.5 48-48 48H208c-26.5 0-48-21.5-48-48V48c0-26.5 21.5-48 48-48zM48 128h80v64H64V448H256V416h64v48c0 26.5-21.5 48-48 48H48c-26.5 0-48-21.5-48-48V176c0-26.5 21.5-48 48-48z"),C(e,"class","svelte-l0tzvr")},m(t,n){v(t,e,n)},d(t){t&&y(e)}}}function Et(t){let e,n="en"===t[3]?"Copy ID":"Copier l'ID";return{c(){e=L(n)},m(t,n){v(t,e,n)},p(t,o){8&o&&n!==(n="en"===t[3]?"Copy ID":"Copier l'ID")&&O(e,n)},d(t){t&&y(e)}}}function Nt(t){let e,n="en"===t[3]?"Copied!":"Copié !";return{c(){e=L(n)},m(t,n){v(t,e,n)},p(t,o){8&o&&n!==(n="en"===t[3]?"Copied!":"Copié !")&&O(e,n)},d(t){t&&y(e)}}}function Pt(t){let e,n,o,c,i,s,a,u,d,f,p,g,m,b,$,k,E,P,_=t[0].title+"";function z(t,e){return t[2]?St:Lt}let V=z(t),I=V(t);function A(t,e){return t[2]?Nt:Et}let j=A(t),M=j(t);return{c(){e=x("div"),n=x("figure"),o=x("img"),i=S(),s=x("div"),a=x("span"),u=L(_),d=S(),f=x("button"),p=w("svg"),I.c(),g=S(),m=x("span"),M.c(),r(o.src,c=vt(t[0].img,t[0].xyhw,"96,"))||C(o,"src",c),C(o,"alt","Extracted region"),C(a,"class","overlay-desc"),C(s,"class","overlay is-center svelte-l0tzvr"),C(n,"class","image is-96x96 card svelte-l0tzvr"),C(n,"tabindex","-1"),C(p,"xmlns","http://www.w3.org/2000/svg"),C(p,"viewBox","0 0 384 512"),C(p,"class","svelte-l0tzvr"),C(m,"class","tooltip svelte-l0tzvr"),C(f,"class","button region-btn tag svelte-l0tzvr"),C(e,"class",b="region image is-96x96 is-center "+(t[1]?"checked":"")+" svelte-l0tzvr")},m(l,c){v(l,e,c),h(e,n),h(n,o),h(n,i),h(n,s),h(s,a),h(a,u),h(e,d),h(e,f),h(f,p),I.m(p,null),h(f,g),h(f,m),M.m(m,null),k=!0,E||(P=[N(n,"click",t[6]),N(n,"keyup",Ct),N(f,"click",t[7])],E=!0)},p(t,[n]){(!k||1&n&&!r(o.src,c=vt(t[0].img,t[0].xyhw,"96,")))&&C(o,"src",c),(!k||1&n)&&_!==(_=t[0].title+"")&&O(u,_),V!==(V=z(t))&&(I.d(1),I=V(t),I&&(I.c(),I.m(p,null))),j===(j=A(t))&&M?M.p(t,n):(M.d(1),M=j(t),M&&(M.c(),M.m(m,null))),(!k||2&n&&b!==(b="region image is-96x96 is-center "+(t[1]?"checked":"")+" svelte-l0tzvr"))&&C(e,"class",b)},i(t){k||(J((()=>{k&&($||($=st(e,wt,{duration:500},!0)),$.run(1))})),k=!0)},o(t){$||($=st(e,wt,{duration:500},!1)),$.run(0),k=!1},d(t){t&&y(e),I.d(),M.d(),t&&$&&$.end(),E=!1,l(P)}}}const Ct=()=>null;function Ot(t,e,n){const o=H();let{block:l}=e,{isSelected:c=!1}=e,{isCopied:i=!1}=e,{appLang:s="en"}=e;function r(){o("toggleSelection",{block:l})}function a(){o("copyRef",{block:l})}return t.$$set=t=>{"block"in t&&n(0,l=t.block),"isSelected"in t&&n(1,c=t.isSelected),"isCopied"in t&&n(2,i=t.isCopied),"appLang"in t&&n(3,s=t.appLang)},[l,c,i,s,r,a,()=>r(),()=>a()]}class _t extends ht{constructor(t){super(),mt(this,t,Ot,Pt,i,{block:0,isSelected:1,isCopied:2,appLang:3})}}function zt(e){let n,o,l,c,i,s,r,a,u,d="en"===e[1]?"Selection":"Sélection";return{c(){n=x("div"),o=x("button"),l=x("span"),c=x("i"),i=S(),s=L(d),r=L("\n            ("),a=L(e[0]),u=L(")"),C(c,"class","fa-solid fa-book-bookmark"),C(l,"id","btn-content"),C(o,"id","set-btn"),C(o,"class","button px-5 py-4 is-link js-modal-trigger svelte-hs48f9"),C(o,"data-target","selection-modal"),C(n,"class","set-container svelte-hs48f9")},m(t,e){v(t,n,e),h(n,o),h(o,l),h(l,c),h(l,i),h(l,s),h(l,r),h(l,a),h(l,u)},p(t,[e]){2&e&&d!==(d="en"===t[1]?"Selection":"Sélection")&&O(s,d),1&e&&O(a,t[0])},i:t,o:t,d(t){t&&y(n)}}}function Vt(t,e,n){let{selectionLength:o=0}=e,{appLang:l="en"}=e,c=o;return t.$$set=t=>{"selectionLength"in t&&n(0,o=t.selectionLength),"appLang"in t&&n(1,l=t.appLang)},t.$$.update=()=>{if(5&t.$$.dirty&&o!==c){const t=o>c;n(2,c=o);const e=document.getElementById("btn-content");e&&e.animate([{transform:t?"translateY(-7px)":"translateX(-5px)"},{transform:t?"translateY(7px)":"translateX(5px)"},{transform:"translate(0)"}],{duration:300,easing:"cubic-bezier(0.65, 0, 0.35, 1)"})}},[o,l,c]}class It extends ht{constructor(t){super(),mt(this,t,Vt,zt,i,{selectionLength:0,appLang:1})}}function At(e){let n,o,c,i,s,r,a,u,d,f,p,g="en"===e[0]?"Clear selection":"Vider la sélection",m="en"===e[0]?"Save selection":"Sauvegarder la sélection";return{c(){n=x("footer"),o=x("div"),c=x("button"),i=L(g),s=S(),r=x("button"),a=x("i"),u=S(),d=L(m),C(c,"class","button is-link is-light"),C(a,"class","fa-solid fa-floppy-disk"),C(r,"class","button is-link"),C(o,"class","buttons"),C(n,"class","modal-card-foot is-center")},m(t,l){v(t,n,l),h(n,o),h(o,c),h(c,i),h(o,s),h(o,r),h(r,a),h(r,u),h(r,d),f||(p=[N(c,"click",e[2]),N(r,"click",e[3])],f=!0)},p(t,[e]){1&e&&g!==(g="en"===t[0]?"Clear selection":"Vider la sélection")&&O(i,g),1&e&&m!==(m="en"===t[0]?"Save selection":"Sauvegarder la sélection")&&O(d,m)},i:t,o:t,d(t){t&&y(n),f=!1,l(p)}}}function jt(t,e,n){const o=H();function l(t="save"){o("commitSelection",{updateType:t})}let{appLang:c="en"}=e;return t.$$set=t=>{"appLang"in t&&n(0,c=t.appLang)},[c,l,()=>l("clear"),()=>l("save")]}class Mt extends ht{constructor(t){super(),mt(this,t,jt,At,i,{appLang:0})}}function Rt(t){let e,n,o,l,c,i,s,a,d,f,p,g,m,b,$,k,w,E;const N=t[4].default,P=function(t,e,n,o){if(t){const l=u(t,e,n,o);return t[0](l)}}(N,t,t[3],null);return{c(){var u,h,v,y;e=x("tr"),n=x("th"),o=x("div"),l=x("img"),s=S(),a=x("div"),d=x("a"),f=x("i"),p=L("\n                    Page "),g=L(t[0]),b=S(),$=x("td"),k=x("div"),w=x("div"),P&&P.c(),r(l.src,c=vt(t[1],"full","250,"))||C(l,"src",c),C(l,"alt",i="Canvas "+t[0]),C(l,"class","mb-3 card"),C(f,"class","fa-solid fa-pen-to-square"),C(d,"class","tag px-2 py-1 is-rounded"),C(d,"href",m=yt(t[2],t[0])),C(d,"target","_blank"),C(a,"class","is-center mb-1"),C(o,"class","content-wrapper py-5"),C(n,"class","is-3 center-flex is-narrow"),u=n,h="width",null==(v="260px")?u.style.removeProperty(h):u.style.setProperty(h,v,y?"important":""),C(w,"class","grid is-gap-2"),C(k,"class","fixed-grid has-6-cols"),C($,"class","p-5 is-fullwidth")},m(t,c){v(t,e,c),h(e,n),h(n,o),h(o,l),h(o,s),h(o,a),h(a,d),h(d,f),h(d,p),h(d,g),h(e,b),h(e,$),h($,k),h(k,w),P&&P.m(w,null),E=!0},p(t,[e]){(!E||2&e&&!r(l.src,c=vt(t[1],"full","250,")))&&C(l,"src",c),(!E||1&e&&i!==(i="Canvas "+t[0]))&&C(l,"alt",i),(!E||1&e)&&O(g,t[0]),(!E||5&e&&m!==(m=yt(t[2],t[0])))&&C(d,"href",m),P&&P.p&&(!E||8&e)&&function(t,e,n,o,l,c){if(l){const i=u(e,n,o,c);t.p(i,l)}}(P,N,t,t[3],E?function(t,e,n,o){if(t[2]&&o){const l=t[2](o(n));if(void 0===e.dirty)return l;if("object"==typeof l){const t=[],n=Math.max(e.dirty.length,l.length);for(let o=0;o<n;o+=1)t[o]=e.dirty[o]|l[o];return t}return e.dirty|l}return e.dirty}(N,t[3],e,null):function(t){if(t.ctx.length>32){const e=[],n=t.ctx.length/32;for(let t=0;t<n;t++)e[t]=-1;return e}return-1}(t[3]),null)},i(t){E||(lt(P,t),E=!0)},o(t){ct(P,t),E=!1},d(t){t&&y(e),P&&P.d(t)}}}function Tt(t,e,n){let{$$slots:o={},$$scope:l}=e,{canvasNb:c}=e,{canvasImg:i}=e,{manifest:s}=e;return t.$$set=t=>{"canvasNb"in t&&n(0,c=t.canvasNb),"canvasImg"in t&&n(1,i=t.canvasImg),"manifest"in t&&n(2,s=t.manifest),"$$scope"in t&&n(3,l=t.$$scope)},[c,i,s,l,o]}class Ht extends ht{constructor(t){super(),mt(this,t,Tt,Rt,i,{canvasNb:0,canvasImg:1,manifest:2})}}function Bt(t){let e,n,o,l,c,i,s,r,a,u=t[0]>1&&Dt(t),d=t[0]<t[1]&&qt(t);return{c(){e=x("nav"),n=x("ul"),u&&u.c(),o=S(),l=x("li"),c=x("a"),i=L(t[0]),s=S(),d&&d.c(),C(c,"class","pagination-link is-current"),C(c,"href",null),C(n,"class","pagination-list"),C(e,"class","pagination is-centered"),C(e,"aria-label","pagination")},m(f,p){v(f,e,p),h(e,n),u&&u.m(n,null),h(n,o),h(n,l),h(l,c),h(c,i),h(n,s),d&&d.m(n,null),r||(a=N(c,"click",P(t[5])),r=!0)},p(t,e){t[0]>1?u?u.p(t,e):(u=Dt(t),u.c(),u.m(n,o)):u&&(u.d(1),u=null),1&e&&O(i,t[0]),t[0]<t[1]?d?d.p(t,e):(d=qt(t),d.c(),d.m(n,null)):d&&(d.d(1),d=null)},d(t){t&&y(e),u&&u.d(),d&&d.d(),r=!1,a()}}}function Dt(t){let e,n,o,l,c,i,s=t[0]-1>1&&Ut(t);return{c(){e=x("li"),n=x("a"),n.textContent="1",o=S(),s&&s.c(),l=E(),C(n,"class","pagination-link"),C(n,"href",null)},m(r,a){v(r,e,a),h(e,n),v(r,o,a),s&&s.m(r,a),v(r,l,a),c||(i=N(n,"click",P(t[3])),c=!0)},p(t,e){t[0]-1>1?s?s.p(t,e):(s=Ut(t),s.c(),s.m(l.parentNode,l)):s&&(s.d(1),s=null)},d(t){t&&y(e),t&&y(o),s&&s.d(t),t&&y(l),c=!1,i()}}}function Ut(t){let e,n,o,l,c,i,s,r=t[0]-1+"";return{c(){e=x("li"),e.innerHTML='<span class="pagination-ellipsis">…</span>',n=S(),o=x("li"),l=x("a"),c=L(r),C(l,"class","pagination-link"),C(l,"href",null)},m(r,a){v(r,e,a),v(r,n,a),v(r,o,a),h(o,l),h(l,c),i||(s=N(l,"click",P(t[4])),i=!0)},p(t,e){1&e&&r!==(r=t[0]-1+"")&&O(c,r)},d(t){t&&y(e),t&&y(n),t&&y(o),i=!1,s()}}}function qt(t){let e,n,o,l,c,i,s=t[0]+1<t[1]&&Ft(t);return{c(){s&&s.c(),e=S(),n=x("li"),o=x("a"),l=L(t[1]),C(o,"class","pagination-link"),C(o,"href",null)},m(r,a){s&&s.m(r,a),v(r,e,a),v(r,n,a),h(n,o),h(o,l),c||(i=N(o,"click",P(t[7])),c=!0)},p(t,n){t[0]+1<t[1]?s?s.p(t,n):(s=Ft(t),s.c(),s.m(e.parentNode,e)):s&&(s.d(1),s=null),2&n&&O(l,t[1])},d(t){s&&s.d(t),t&&y(e),t&&y(n),c=!1,i()}}}function Ft(t){let e,n,o,l,c,i,s,r=t[0]+1+"";return{c(){e=x("li"),n=x("a"),o=L(r),l=S(),c=x("li"),c.innerHTML='<span class="pagination-ellipsis">…</span>',C(n,"class","pagination-link"),C(n,"href",null)},m(r,a){v(r,e,a),h(e,n),h(n,o),v(r,l,a),v(r,c,a),i||(s=N(n,"click",P(t[6])),i=!0)},p(t,e){1&e&&r!==(r=t[0]+1+"")&&O(o,r)},d(t){t&&y(e),t&&y(l),t&&y(c),i=!1,s()}}}function Gt(e){let n,o=e[1]>1&&Bt(e);return{c(){o&&o.c(),n=E()},m(t,e){o&&o.m(t,e),v(t,n,e)},p(t,[e]){t[1]>1?o?o.p(t,e):(o=Bt(t),o.c(),o.m(n.parentNode,n)):o&&(o.d(1),o=null)},i:t,o:t,d(t){o&&o.d(t),t&&y(n)}}}function Jt(t,e,n){const o=H();let{pageNb:l}=e,{maxPage:c}=e;function i(t){o("pageUpdate",{pageNb:t})}return t.$$set=t=>{"pageNb"in t&&n(0,l=t.pageNb),"maxPage"in t&&n(1,c=t.maxPage)},[l,c,i,()=>i(1),()=>i(l-1),()=>i(l),()=>i(l+1),()=>i(c)]}class Xt extends ht{constructor(t){super(),mt(this,t,Jt,Gt,i,{pageNb:0,maxPage:1})}}function Yt(e){let n,o,l,c,i,s,r,a,u,d,f,p,g,m,b,$,k="en"===e[0]?"Cancel":"Annuler";return{c(){n=x("button"),o=S(),l=x("div"),c=x("div"),i=S(),s=x("div"),r=x("div"),r.innerHTML='<div class="title is-4 mb-0 media-content"><span id="modal-title" class="mb-0"></span></div> \n            <button class="delete media-left" aria-label="close"></button>',a=S(),u=x("section"),d=S(),f=x("footer"),p=x("div"),g=x("button"),m=L(k),b=S(),$=x("button"),$.textContent="OK",C(n,"id","hidden-msg-btn"),C(n,"class","js-modal-trigger"),C(n,"data-target","msg-modal"),n.hidden=!0,C(c,"id","modal-bkg"),C(c,"class","modal-background"),C(r,"class","modal-card-head media mb-0"),C(u,"id","modal-body"),C(u,"class","modal-card-body"),C(g,"id","cancel-btn"),C(g,"class","button is-link is-light"),C($,"id","ok-btn"),C($,"class","button is-link"),C(p,"class","buttons"),C(f,"id","modal-footer"),C(f,"class","modal-card-foot is-center pt-1"),f.hidden=!0,C(s,"class","modal-content"),C(l,"id","msg-modal"),C(l,"class","modal fade"),C(l,"tabindex","-1"),C(l,"aria-labelledby","selection-modal-label"),C(l,"aria-hidden","true")},m(t,e){v(t,n,e),v(t,o,e),v(t,l,e),h(l,c),h(l,i),h(l,s),h(s,r),h(s,a),h(s,u),h(s,d),h(s,f),h(f,p),h(p,g),h(g,m),h(p,b),h(p,$)},p(t,[e]){1&e&&k!==(k="en"===t[0]?"Cancel":"Annuler")&&O(m,k)},i:t,o:t,d(t){t&&y(n),t&&y(o),t&&y(l)}}}function Kt(t,e,n){let{appLang:o="en"}=e;return t.$$set=t=>{"appLang"in t&&n(0,o=t.appLang)},[o]}class Qt extends ht{constructor(t){super(),mt(this,t,Kt,Yt,i,{appLang:0})}}function Wt(t,e,n){const o=t.slice();return o[35]=e[n][0],o[36]=e[n][1],o}function Zt(t,e,n){const o=t.slice();return o[43]=e[n][0],o[44]=e[n][1],o}function te(t,e,n){const o=t.slice();return o[39]=e[n],o}function ee(t,e,n){const o=t.slice();return o[39]=e[n],o}function ne(t,e,n){const o=t.slice();return o[50]=e[n][0],o[36]=e[n][1],o}function oe(t){let e;return{c(){e=w("path"),C(e,"d","M471.6 21.7c-21.9-21.9-57.3-21.9-79.2 0L362.3 51.7l97.9 97.9 30.1-30.1c21.9-21.9 21.9-57.3 0-79.2L471.6 21.7zm-299.2 220c-6.1 6.1-10.8 13.6-13.5 21.9l-29.6 88.8c-2.9 8.6-.6 18.1 5.8 24.6s15.9 8.7 24.6 5.8l88.8-29.6c8.2-2.7 15.7-7.4 21.9-13.5L437.7 172.3 339.7 74.3 172.4 241.7zM96 64C43 64 0 107 0 160V416c0 53 43 96 96 96H352c53 0 96-43 96-96V320c0-17.7-14.3-32-32-32s-32 14.3-32 32v96c0 17.7-14.3 32-32 32H96c-17.7 0-32-14.3-32-32V160c0-17.7 14.3-32 32-32h96c17.7 0 32-14.3 32-32s-14.3-32-32-32H96z"),C(e,"class","svelte-16efmtz")},m(t,n){v(t,e,n)},d(t){t&&y(e)}}}function le(t){let e;return{c(){e=w("path"),C(e,"d","M438.6 105.4c12.5 12.5 12.5 32.8 0 45.3l-256 256c-12.5 12.5-32.8 12.5-45.3 0l-128-128c-12.5-12.5-12.5-32.8 0-45.3s32.8-12.5 45.3 0L160 338.7 393.4 105.4c12.5-12.5 32.8-12.5 45.3 0z"),C(e,"class","svelte-16efmtz")},m(t,n){v(t,e,n)},d(t){t&&y(e)}}}function ce(t){let e,n="en"===t[2]?"Edit":"Modifier";return{c(){e=L(n)},m(t,n){v(t,e,n)},p(t,o){4&o[0]&&n!==(n="en"===t[2]?"Edit":"Modifier")&&O(e,n)},d(t){t&&y(e)}}}function ie(t){let e,n="en"===t[2]?"Validate":"Valider";return{c(){e=L(n)},m(t,n){v(t,e,n)},p(t,o){4&o[0]&&n!==(n="en"===t[2]?"Validate":"Valider")&&O(e,n)},d(t){t&&y(e)}}}function se(t){let e,n,o,c,i,s,r,a,u,d,f,p,g,m,b,$,k,w="en"===t[2]?"Reload":"Recharger",E="en"===t[2]?"Go to editor":"Aller à l'éditeur",P="en"===t[2]?"Delete selected regions":"Supprimer les régions sélectionnées";return{c(){e=x("button"),n=x("i"),o=S(),c=L(w),i=S(),s=x("a"),r=x("i"),a=S(),u=L(E),f=S(),p=x("button"),g=x("i"),m=S(),b=L(P),C(n,"class","fa-solid fa-rotate-right"),C(e,"class","tag is-link is-light is-rounded mr-3"),C(r,"class","fa-solid fa-edit"),C(s,"class","tag is-link is-rounded mr-3"),C(s,"href",d=yt(t[3])),C(s,"target","_blank"),C(g,"class","fa-solid fa-trash"),C(p,"class","tag is-danger is-rounded")},m(l,d){v(l,e,d),h(e,n),h(e,o),h(e,c),v(l,i,d),v(l,s,d),h(s,r),h(s,a),h(s,u),v(l,f,d),v(l,p,d),h(p,g),h(p,m),h(p,b),$||(k=[N(e,"click",t[30]),N(p,"click",t[20])],$=!0)},p(t,e){4&e[0]&&w!==(w="en"===t[2]?"Reload":"Recharger")&&O(c,w),4&e[0]&&E!==(E="en"===t[2]?"Go to editor":"Aller à l'éditeur")&&O(u,E),8&e[0]&&d!==(d=yt(t[3]))&&C(s,"href",d),4&e[0]&&P!==(P="en"===t[2]?"Delete selected regions":"Supprimer les régions sélectionnées")&&O(b,P)},d(t){t&&y(e),t&&y(i),t&&y(s),t&&y(f),t&&y(p),$=!1,l(k)}}}function re(t){let e,n,o,c,i,s,r=t[36].text+"";function a(){return t[31](t[50])}return{c(){e=x("li"),n=x("a"),o=L(r),c=S(),C(n,"href",null),_(e,"is-active",t[50]===t[10])},m(t,l){v(t,e,l),h(e,n),h(n,o),h(e,c),i||(s=[N(e,"click",a),N(e,"keyup",Oe)],i=!0)},p(n,o){t=n,33792&o[0]&&_(e,"is-active",t[50]===t[10])},d(t){t&&y(e),i=!1,l(s)}}}function ae(e){let n;return{c(){n=x("div"),n.textContent="tout doux"},m(t,e){v(t,n,e)},p:t,i:t,o:t,d(t){t&&y(n)}}}function ue(e){let n;return{c(){n=x("div"),n.textContent="tout doux"},m(t,e){v(t,n,e)},p:t,i:t,o:t,d(t){t&&y(n)}}}function de(t){let e,n,o,l,c,i;e=new Xt({props:{pageNb:t[5],maxPage:10}}),e.$on("pageUpdate",t[17]);let s={ctx:t,current:null,token:null,hasCatch:!0,pending:ye,then:ge,catch:pe,value:42,error:49,blocks:[,,,]};return rt(c=t[9],s),{c(){dt(e.$$.fragment),n=S(),o=x("table"),l=x("tbody"),s.block.c(),C(o,"class","table is-fullwidth")},m(t,c){ft(e,t,c),v(t,n,c),v(t,o,c),h(o,l),s.block.m(l,s.anchor=null),s.mount=()=>l,s.anchor=null,i=!0},p(n,o){t=n;const l={};32&o[0]&&(l.pageNb=t[5]),e.$set(l),s.ctx=t,512&o[0]&&c!==(c=t[9])&&rt(c,s)||function(t,e,n){const o=e.slice(),{resolved:l}=t;t.current===t.then&&(o[t.value]=l),t.current===t.catch&&(o[t.error]=l),t.block.p(o,n)}(s,t,o)},i(t){i||(lt(e.$$.fragment,t),lt(s.block),i=!0)},o(t){ct(e.$$.fragment,t);for(let t=0;t<3;t+=1){ct(s.blocks[t])}i=!1},d(t){pt(e,t),t&&y(n),t&&y(o),s.block.d(),s.token=null,s=null}}}function fe(t){let e,n,o=[],l=new Map,c=Object.values(t[0]);const i=t=>t[39].id;for(let e=0;e<c.length;e+=1){let n=ee(t,c,e),s=i(n);l.set(s,o[e]=xe(s,n))}let s=null;return c.length||(s=ke()),{c(){e=x("div");for(let t=0;t<o.length;t+=1)o[t].c();s&&s.c(),C(e,"class","grid is-gap-2")},m(t,l){v(t,e,l);for(let t=0;t<o.length;t+=1)o[t]&&o[t].m(e,null);s&&s.m(e,null),n=!0},p(t,n){12583109&n[0]&&(c=Object.values(t[0]),nt(),o=ut(o,n,i,1,t,c,l,e,at,xe,null,ee),ot(),c.length?s&&(s.d(1),s=null):s||(s=ke(),s.c(),s.m(e,null)))},i(t){if(!n){for(let t=0;t<c.length;t+=1)lt(o[t]);n=!0}},o(t){for(let t=0;t<o.length;t+=1)ct(o[t]);n=!1},d(t){t&&y(e);for(let t=0;t<o.length;t+=1)o[t].d();s&&s.d()}}}function pe(e){let n,o,l,c=e[49]+"";return{c(){n=x("tr"),o=L("Error when retrieving paginated regions: "),l=L(c)},m(t,e){v(t,n,e),h(n,o),h(n,l)},p(t,e){512&e[0]&&c!==(c=t[49]+"")&&O(l,c)},i:t,o:t,d(t){t&&y(n)}}}function ge(t){let e,n,o,l,c;const i=[he,me],s=[];function r(t,n){return 8192&n[0]&&(e=null),null==e&&(e=!!(Object.values(t[13]).length>0)),e?0:1}return n=r(t,[-1,-1]),o=s[n]=i[n](t),{c(){o.c(),l=E()},m(t,e){s[n].m(t,e),v(t,l,e),c=!0},p(t,e){let c=n;n=r(t,e),n===c?s[n].p(t,e):(nt(),ct(s[c],1,1,(()=>{s[c]=null})),ot(),o=s[n],o?o.p(t,e):(o=s[n]=i[n](t),o.c()),lt(o,1),o.m(l.parentNode,l))},i(t){c||(lt(o),c=!0)},o(t){ct(o),c=!1},d(t){s[n].d(t),t&&y(l)}}}function me(e){let n;return{c(){n=x("tr"),n.textContent="NO ANNOTATION"},m(t,e){v(t,n,e)},p:t,i:t,o:t,d(t){t&&y(n)}}}function he(t){let e,n,o=Object.entries(t[13]),l=[];for(let e=0;e<o.length;e+=1)l[e]=ve(Zt(t,o,e));const c=t=>ct(l[t],1,1,(()=>{l[t]=null}));return{c(){for(let t=0;t<l.length;t+=1)l[t].c();e=E()},m(t,o){for(let e=0;e<l.length;e+=1)l[e]&&l[e].m(t,o);v(t,e,o),n=!0},p(t,n){if(12607692&n[0]){let i;for(o=Object.entries(t[13]),i=0;i<o.length;i+=1){const c=Zt(t,o,i);l[i]?(l[i].p(c,n),lt(l[i],1)):(l[i]=ve(c),l[i].c(),lt(l[i],1),l[i].m(e.parentNode,e))}for(nt(),i=o.length;i<l.length;i+=1)c(i);ot()}},i(t){if(!n){for(let t=0;t<o.length;t+=1)lt(l[t]);n=!0}},o(t){l=l.filter(Boolean);for(let t=0;t<l.length;t+=1)ct(l[t]);n=!1},d(t){k(l,t),t&&y(e)}}}function be(t,e){let n,o,l;return o=new _t({props:{block:e[39],appLang:e[2],isSelected:e[7](e[39]),isCopied:e[6](e[39])}}),o.$on("toggleSelection",e[22]),o.$on("copyRef",e[23]),{key:t,first:null,c(){n=E(),dt(o.$$.fragment),this.first=n},m(t,e){v(t,n,e),ft(o,t,e),l=!0},p(t,n){e=t;const l={};8192&n[0]&&(l.block=e[39]),4&n[0]&&(l.appLang=e[2]),8320&n[0]&&(l.isSelected=e[7](e[39])),8256&n[0]&&(l.isCopied=e[6](e[39])),o.$set(l)},i(t){l||(lt(o.$$.fragment,t),l=!0)},o(t){ct(o.$$.fragment,t),l=!1},d(t){t&&y(n),pt(o,t)}}}function $e(t){let e,n,o=[],l=new Map,c=Object.values(t[44]);const i=t=>t[39].id;for(let e=0;e<c.length;e+=1){let n=te(t,c,e),s=i(n);l.set(s,o[e]=be(s,n))}return{c(){for(let t=0;t<o.length;t+=1)o[t].c();e=S()},m(t,l){for(let e=0;e<o.length;e+=1)o[e]&&o[e].m(t,l);v(t,e,l),n=!0},p(t,n){12591300&n[0]&&(c=Object.values(t[44]),nt(),o=ut(o,n,i,1,t,c,l,e.parentNode,at,be,e,te),ot())},i(t){if(!n){for(let t=0;t<c.length;t+=1)lt(o[t]);n=!0}},o(t){for(let t=0;t<o.length;t+=1)ct(o[t]);n=!1},d(t){for(let e=0;e<o.length;e+=1)o[e].d(t);t&&y(e)}}}function ve(t){let e,n;return e=new Ht({props:{canvasImg:t[14](t[43]),canvasNb:t[43],manifest:t[3],$$slots:{default:[$e]},$$scope:{ctx:t}}}),{c(){dt(e.$$.fragment)},m(t,o){ft(e,t,o),n=!0},p(t,n){const o={};8192&n[0]&&(o.canvasImg=t[14](t[43])),8192&n[0]&&(o.canvasNb=t[43]),8&n[0]&&(o.manifest=t[3]),8388&n[0]|4194304&n[1]&&(o.$$scope={dirty:n,ctx:t}),e.$set(o)},i(t){n||(lt(e.$$.fragment,t),n=!0)},o(t){ct(e.$$.fragment,t),n=!1},d(t){pt(e,t)}}}function ye(e){let n;return{c(){n=x("tr"),n.textContent="Retrieving paginated regions...",C(n,"class","faded is-center")},m(t,e){v(t,n,e)},p:t,i:t,o:t,d(t){t&&y(n)}}}function ke(t){let e;return{c(){e=L("NO ANNOTATION")},m(t,n){v(t,e,n)},d(t){t&&y(e)}}}function xe(t,e){let n,o,l;return o=new _t({props:{block:e[39],appLang:e[2],isSelected:e[7](e[39]),isCopied:e[6](e[39])}}),o.$on("toggleSelection",e[22]),o.$on("copyRef",e[23]),{key:t,first:null,c(){n=E(),dt(o.$$.fragment),this.first=n},m(t,e){v(t,n,e),ft(o,t,e),l=!0},p(t,n){e=t;const l={};1&n[0]&&(l.block=e[39]),4&n[0]&&(l.appLang=e[2]),129&n[0]&&(l.isSelected=e[7](e[39])),65&n[0]&&(l.isCopied=e[6](e[39])),o.$set(l)},i(t){l||(lt(o.$$.fragment,t),l=!0)},o(t){ct(o.$$.fragment,t),l=!1},d(t){t&&y(n),pt(o,t)}}}function we(t){let e,n,o="en"===t[2]?"No regions in selection":"Aucune région sélectionnée";return{c(){e=x("div"),n=L(o)},m(t,o){v(t,e,o),h(e,n)},p(t,e){4&e[0]&&o!==(o="en"===t[2]?"No regions in selection":"Aucune région sélectionnée")&&O(n,o)},d(t){t&&y(e)}}}function Le(t){let e,n,o=Object.entries(t[4][t[1]]),l=[];for(let e=0;e<o.length;e+=1)l[e]=Se(Wt(t,o,e));return{c(){e=x("div"),n=x("div");for(let t=0;t<l.length;t+=1)l[t].c();C(n,"class","grid is-gap-2"),C(e,"class","fixed-grid has-6-cols")},m(t,o){v(t,e,o),h(e,n);for(let t=0;t<l.length;t+=1)l[t]&&l[t].m(n,null)},p(t,e){if(2097170&e[0]){let c;for(o=Object.entries(t[4][t[1]]),c=0;c<o.length;c+=1){const i=Wt(t,o,c);l[c]?l[c].p(i,e):(l[c]=Se(i),l[c].c(),l[c].m(n,null))}for(;c<l.length;c+=1)l[c].d(1);l.length=o.length}},d(t){t&&y(e),k(l,t)}}}function Se(t){let e,n,o,l,c,i,s,a,u,d,f,p,g,m=t[36].title+"";function b(){return t[32](t[35])}return{c(){e=x("div"),n=x("figure"),o=x("img"),c=S(),i=x("div"),s=x("span"),a=L(m),u=S(),d=x("button"),f=S(),r(o.src,l=vt(t[36].img,t[36].xyhw,"96,"))||C(o,"src",l),C(o,"alt","Extracted region"),C(s,"class","overlay-desc"),C(i,"class","overlay is-center svelte-16efmtz"),C(n,"class","image is-64x64 card"),C(d,"class","delete region-btn"),C(d,"aria-label","remove from selection"),C(e,"class","selection cell svelte-16efmtz")},m(t,l){v(t,e,l),h(e,n),h(n,o),h(n,c),h(n,i),h(i,s),h(s,a),h(e,u),h(e,d),h(e,f),p||(g=N(d,"click",b),p=!0)},p(e,n){t=e,16&n[0]&&!r(o.src,l=vt(t[36].img,t[36].xyhw,"96,"))&&C(o,"src",l),16&n[0]&&m!==(m=t[36].title+"")&&O(a,m)},d(t){t&&y(e),p=!1,g()}}}function Ee(t){let e,n,o,c,i,s,r,a,u,d,f,p,g,m,b,$,E,P,_,z,V,I,A,j,M,R,T,H,B,D,U,q,F,G,J,X,Y,K,Q,W,Z,tt,et,it,st,rt,at,ut,gt,mt,ht,bt="en"===t[2]?"Select all":"Tout sélectionner",$t="en"===t[2]?"Download":"Télecharger",vt="en"===t[2]?"Selected regions":"Regions sélectionnées";function yt(t,e){return t[8]?le:oe}e=new Qt({props:{appLang:t[2]}}),o=new It({props:{selectionLength:t[12],appLang:t[2]}});let kt=yt(t),xt=kt(t);function wt(t,e){return t[8]?ie:ce}let Lt=wt(t),St=Lt(t),Et=t[8]&&se(t),Nt=Object.entries(t[15]),Pt=[];for(let e=0;e<Nt.length;e+=1)Pt[e]=re(ne(t,Nt,e));const Ct=[fe,de,ue,ae],Ot=[];function _t(t,e){return"all"===t[10]?0:"page"===t[10]?1:"similarity"===t[10]?2:"vectorization"===t[10]?3:-1}function zt(t,e){return t[11]?Le:we}~(H=_t(t))&&(B=Ot[H]=Ct[H](t));let Vt=zt(t),At=Vt(t);return ut=new Mt({props:{appLang:t[2]}}),ut.$on("commitSelection",t[19]),{c(){dt(e.$$.fragment),n=S(),dt(o.$$.fragment),c=S(),i=x("div"),s=x("div"),r=x("div"),a=x("button"),u=w("svg"),xt.c(),d=S(),St.c(),p=S(),g=x("button"),m=x("i"),b=S(),$=L(bt),E=S(),P=x("button"),_=x("i"),z=S(),V=L($t),I=S(),A=x("div"),Et&&Et.c(),j=S(),M=x("div"),R=x("ul");for(let t=0;t<Pt.length;t+=1)Pt[t].c();T=S(),B&&B.c(),D=S(),U=x("div"),q=x("div"),F=S(),G=x("div"),J=x("div"),X=x("div"),Y=x("i"),K=S(),Q=L(vt),W=L("\n                ("),Z=L(t[12]),tt=L(")"),et=S(),it=x("button"),st=S(),rt=x("section"),At.c(),at=S(),dt(ut.$$.fragment),C(u,"xmlns","http://www.w3.org/2000/svg"),C(u,"viewBox","0 0 384 512"),C(u,"class","pr-3"),C(a,"class",f="button "+(t[8]?"is-success":"is-link")+" mr-3"),C(m,"class","fa-solid fa-square-check"),C(g,"class","button is-link is-light mr-3"),C(_,"class","fa-solid fa-download"),C(P,"class","button is-link is-light"),C(r,"class","is-left svelte-16efmtz"),C(A,"class","edit-action svelte-16efmtz"),C(s,"class","center-flex actions svelte-16efmtz"),C(R,"class","panel-tabs"),C(M,"class","tabs is-centered"),C(i,"id","nav-actions"),C(i,"class","mb-5 svelte-16efmtz"),C(q,"class","modal-background"),C(Y,"class","fa-solid fa-book-bookmark"),C(X,"class","title is-4 mb-0 media-content"),C(it,"class","delete media-left"),C(it,"aria-label","close"),C(J,"class","modal-card-head media mb-0"),C(rt,"class","modal-card-body"),C(G,"class","modal-content"),C(U,"id","selection-modal"),C(U,"class","modal fade"),C(U,"tabindex","-1"),C(U,"aria-labelledby","selection-modal-label"),C(U,"aria-hidden","true")},m(l,f){ft(e,l,f),v(l,n,f),ft(o,l,f),v(l,c,f),v(l,i,f),h(i,s),h(s,r),h(r,a),h(a,u),xt.m(u,null),h(a,d),St.m(a,null),h(r,p),h(r,g),h(g,m),h(g,b),h(g,$),h(r,E),h(r,P),h(P,_),h(P,z),h(P,V),h(s,I),h(s,A),Et&&Et.m(A,null),h(i,j),h(i,M),h(M,R);for(let t=0;t<Pt.length;t+=1)Pt[t]&&Pt[t].m(R,null);v(l,T,f),~H&&Ot[H].m(l,f),v(l,D,f),v(l,U,f),h(U,q),h(U,F),h(U,G),h(G,J),h(J,X),h(X,Y),h(X,K),h(X,Q),h(X,W),h(X,Z),h(X,tt),h(J,et),h(J,it),h(G,st),h(G,rt),At.m(rt,null),h(G,at),ft(ut,G,null),gt=!0,mt||(ht=[N(a,"click",t[29]),N(g,"click",Pe),N(P,"click",Ce)],mt=!0)},p(t,n){const l={};4&n[0]&&(l.appLang=t[2]),e.$set(l);const c={};if(4096&n[0]&&(c.selectionLength=t[12]),4&n[0]&&(c.appLang=t[2]),o.$set(c),kt!==(kt=yt(t))&&(xt.d(1),xt=kt(t),xt&&(xt.c(),xt.m(u,null))),Lt===(Lt=wt(t))&&St?St.p(t,n):(St.d(1),St=Lt(t),St&&(St.c(),St.m(a,null))),(!gt||256&n[0]&&f!==(f="button "+(t[8]?"is-success":"is-link")+" mr-3"))&&C(a,"class",f),(!gt||4&n[0])&&bt!==(bt="en"===t[2]?"Select all":"Tout sélectionner")&&O($,bt),(!gt||4&n[0])&&$t!==($t="en"===t[2]?"Download":"Télecharger")&&O(V,$t),t[8]?Et?Et.p(t,n):(Et=se(t),Et.c(),Et.m(A,null)):Et&&(Et.d(1),Et=null),33792&n[0]){let e;for(Nt=Object.entries(t[15]),e=0;e<Nt.length;e+=1){const o=ne(t,Nt,e);Pt[e]?Pt[e].p(o,n):(Pt[e]=re(o),Pt[e].c(),Pt[e].m(R,null))}for(;e<Pt.length;e+=1)Pt[e].d(1);Pt.length=Nt.length}let i=H;H=_t(t),H===i?~H&&Ot[H].p(t,n):(B&&(nt(),ct(Ot[i],1,1,(()=>{Ot[i]=null})),ot()),~H?(B=Ot[H],B?B.p(t,n):(B=Ot[H]=Ct[H](t),B.c()),lt(B,1),B.m(D.parentNode,D)):B=null),(!gt||4&n[0])&&vt!==(vt="en"===t[2]?"Selected regions":"Regions sélectionnées")&&O(Q,vt),(!gt||4096&n[0])&&O(Z,t[12]),Vt===(Vt=zt(t))&&At?At.p(t,n):(At.d(1),At=Vt(t),At&&(At.c(),At.m(rt,null)));const s={};4&n[0]&&(s.appLang=t[2]),ut.$set(s)},i(t){gt||(lt(e.$$.fragment,t),lt(o.$$.fragment,t),lt(B),lt(ut.$$.fragment,t),gt=!0)},o(t){ct(e.$$.fragment,t),ct(o.$$.fragment,t),ct(B),ct(ut.$$.fragment,t),gt=!1},d(t){pt(e,t),t&&y(n),pt(o,t),t&&y(c),t&&y(i),xt.d(),St.d(),Et&&Et.d(),k(Pt,t),t&&y(T),~H&&Ot[H].d(t),t&&y(D),t&&y(U),At.d(),pt(ut),mt=!1,l(ht)}}}async function Ne(t){const e=SAS_APP_URL.replace("https","http"),n=`${SAS_APP_URL}/annotation/destroy?uri=${e}/annotation/${t}`,o=await fetch(n,{method:"DELETE"});if(204!==o.status)throw new Error(`Failed to delete ${n} due to ${o.status}: '${o.statusText}'`)}const Pe=()=>null,Ce=()=>null,Oe=()=>null;function _e(e,n,o){let l,c,s,r,u,d,f,p,g,m,h;const b="Regions";let{regions:$={}}=n,{appLang:v="en"}=n,{manifest:y=""}=n,{isValidated:k=!1}=n,{imgPrefix:x=""}=n,{nbOfPages:w=1}=n;let L=JSON.parse(localStorage.getItem("documentSet"))??{};const S={all:{text:"en"===v?"All regions":"Toutes les régions"},page:{text:"en"===v?"Per page":"Par page"},similarity:{text:"en"===v?"Similarity":"Similarité"},vectorization:{text:"en"===v?"Vectorization":"Vectorisation"}},E=function(e,n=t){let o;const l=new Set;function c(t){if(i(e,t)&&(e=t,o)){const t=!xt.length;for(const t of l)t[1](),xt.push(t,e);if(t){for(let t=0;t<xt.length;t+=2)xt[t][0](xt[t+1]);xt.length=0}}}return{set:c,update:function(t){c(t(e))},subscribe:function(i,s=t){const r=[i,s];return l.add(r),1===l.size&&(o=n(c)||t),i(e),()=>{l.delete(r),0===l.size&&o&&(o(),o=null)}}}}({});function N(){o(8,r=!r)}function P(t){o(4,L=$t(L,t,b))}function C(t){o(4,L=function(t,e){return t.hasOwnProperty(e.type)||(t[e.type]=[]),t[e.type]={...t[e.type],[e.id]:e},bt(t),t}(L,t))}a(e,E,(t=>o(13,h=t)));return e.$$set=t=>{"regions"in t&&o(0,$=t.regions),"appLang"in t&&o(2,v=t.appLang),"manifest"in t&&o(3,y=t.manifest),"isValidated"in t&&o(24,k=t.isValidated),"imgPrefix"in t&&o(25,x=t.imgPrefix),"nbOfPages"in t&&o(26,w=t.nbOfPages)},e.$$.update=()=>{16&e.$$.dirty[0]&&o(12,l=L.hasOwnProperty(b)?Object.keys(L[b]).length:0),16&e.$$.dirty[0]&&o(7,c=t=>L[b]?.hasOwnProperty(t.id)),16&e.$$.dirty[0]&&o(11,s=Object.keys(L[b]??{}).length>0),16777216&e.$$.dirty[0]&&o(8,r=!k),268435488&e.$$.dirty[0]&&o(9,p=(async()=>{const t=await fetch(`${d}canvas?p=${f}`),e=await t.json();return E.set(e),e})()),134217728&e.$$.dirty[0]&&o(6,m=t=>g===t.ref)},o(10,u="all"),o(28,d=`${window.location.origin}${window.location.pathname}`),o(5,f=parseInt(new URLSearchParams(window.location.search).get("p")??1)),o(27,g=""),[$,b,v,y,L,f,m,c,r,p,u,s,l,h,function(t){return`${x}_${e=t,n=String(w).length+1,e.toString().padStart(n,"0")}`;var e,n},S,E,function(t){const{pageNb:e}=t.detail;o(5,f=e);const n=new URL(d);n.searchParams.set("p",f),window.history.pushState({},"",n)},N,function(t){const{updateType:e}=t.detail;"clear"===e?o(4,L=function(t,e){return e.map((e=>!t.hasOwnProperty(e)||delete t[e])),bt(t),t}(L,[b])):"save"===e&&o(4,L=function(t){return console.log(t),t}(L))},async function(){if(await kt("en"===v?"Are you sure you want to delete regions?":"Voulez-vous vraiment supprimer les régions?","en"===v?"Confirm deletion":"Confirmer la suppression",!0))for(const t of Object.keys(L[b]))try{if(!$.hasOwnProperty(t))continue;await Ne(t),delete $[t],o(0,$={...$}),E.update((e=>{for(const n in e)if(e[n][t]){const{[t]:o,...l}=e[n];return e[n]=l,e}return e})),o(4,L=$t(L,t,b))}catch(e){success=!1,await kt(`Failed to delete region ${t}: ${e.message}`,"Error")}},P,function(t){const{block:e}=t.detail;c(e)?P(e.id):C(e)},function(t){const{block:e}=t.detail,n=m(e)?"":e.ref;navigator.clipboard.writeText(n),o(27,g=n)},k,x,w,g,d,()=>N(),()=>location.reload(),t=>o(10,u=t),t=>P(t)]}const ze=(Ve="regions-data",document.getElementById(Ve)?JSON.parse(document.getElementById(Ve).textContent):[]);var Ve;return new class extends ht{constructor(t){super(),mt(this,t,_e,Ee,i,{regionsType:1,regions:0,appLang:2,manifest:3,isValidated:24,imgPrefix:25,nbOfPages:26},null,[-1,-1])}get regionsType(){return this.$$.ctx[1]}}({target:document.getElementById("region-list"),props:{regions:ze,regionsType:"Regions",appLang:APP_LANG,manifest:manifest,isValidated:isValidated,imgPrefix:imgPrefix,nbOfPages:nbOfPages}})}();
//# sourceMappingURL=regionList.js.map
