var recordList=function(){"use strict";function t(){}function e(t){return t()}function n(){return Object.create(null)}function o(t){t.forEach(e)}function l(t){return"function"==typeof t}function r(t,e){return t!=t?e==e:t!==e||t&&"object"==typeof t||"function"==typeof t}let c,s;function i(t,e){return c||(c=document.createElement("a")),c.href=e,t===c.href}function u(e,...n){if(null==e)return t;const o=e.subscribe(...n);return o.unsubscribe?()=>o.unsubscribe():o}function a(t,e,n){t.$$.on_destroy.push(u(e,n))}function d(t,e,n,o){return t[1]&&o?function(t,e){for(const n in e)t[n]=e[n];return t}(n.ctx.slice(),t[1](o(e))):n.ctx}function f(t,e){t.appendChild(e)}function p(t,e,n){t.insertBefore(e,n||null)}function g(t){t.parentNode&&t.parentNode.removeChild(t)}function m(t,e){for(let n=0;n<t.length;n+=1)t[n]&&t[n].d(e)}function h(t){return document.createElement(t)}function $(t){return document.createElementNS("http://www.w3.org/2000/svg",t)}function b(t){return document.createTextNode(t)}function y(){return b(" ")}function x(){return b("")}function v(t,e,n,o){return t.addEventListener(e,n,o),()=>t.removeEventListener(e,n,o)}function k(t,e,n){null==n?t.removeAttribute(e):t.getAttribute(e)!==n&&t.setAttribute(e,n)}function _(t,e){e=""+e,t.data!==e&&(t.data=e)}function w(t,e,n){t.classList[n?"add":"remove"](e)}function A(t){s=t}const S=[],L=[];let E=[];const O=[],N=Promise.resolve();let R=!1;function j(t){E.push(t)}const C=new Set;let P=0;function M(){if(0!==P)return;const t=s;do{try{for(;P<S.length;){const t=S[P];P++,A(t),I(t.$$)}}catch(t){throw S.length=0,P=0,t}for(A(null),S.length=0,P=0;L.length;)L.pop()();for(let t=0;t<E.length;t+=1){const e=E[t];C.has(e)||(C.add(e),e())}E.length=0}while(S.length);for(;O.length;)O.pop()();R=!1,C.clear(),A(t)}function I(t){if(null!==t.fragment){t.update(),o(t.before_update);const e=t.dirty;t.dirty=[-1],t.fragment&&t.fragment.p(t.ctx,e),t.after_update.forEach(j)}}const V=new Set;let T;function H(){T={r:0,c:[],p:T}}function z(){T.r||o(T.c),T=T.p}function B(t,e){t&&t.i&&(V.delete(t),t.i(e))}function D(t,e,n,o){if(t&&t.o){if(V.has(t))return;V.add(t),T.c.push((()=>{V.delete(t),o&&(n&&t.d(1),o())})),t.o(e)}else o&&o()}function U(t,e){D(t,1,1,(()=>{e.delete(t.key)}))}function q(t){t&&t.c()}function J(t,n,r,c){const{fragment:s,after_update:i}=t.$$;s&&s.m(n,r),c||j((()=>{const n=t.$$.on_mount.map(e).filter(l);t.$$.on_destroy?t.$$.on_destroy.push(...n):o(n),t.$$.on_mount=[]})),i.forEach(j)}function X(t,e){const n=t.$$;null!==n.fragment&&(!function(t){const e=[],n=[];E.forEach((o=>-1===t.indexOf(o)?e.push(o):n.push(o))),n.forEach((t=>t())),E=e}(n.after_update),o(n.on_destroy),n.fragment&&n.fragment.d(e),n.on_destroy=n.fragment=null,n.ctx=[])}function Y(t,e){-1===t.$$.dirty[0]&&(S.push(t),R||(R=!0,N.then(M)),t.$$.dirty.fill(0)),t.$$.dirty[e/31|0]|=1<<e%31}function F(e,l,r,c,i,u,a,d=[-1]){const f=s;A(e);const p=e.$$={fragment:null,ctx:[],props:u,update:t,not_equal:i,bound:n(),on_mount:[],on_destroy:[],on_disconnect:[],before_update:[],after_update:[],context:new Map(l.context||(f?f.$$.context:[])),callbacks:n(),dirty:d,skip_bound:!1,root:l.target||f.$$.root};a&&a(p.root);let m=!1;if(p.ctx=r?r(e,l.props||{},((t,n,...o)=>{const l=o.length?o[0]:n;return p.ctx&&i(p.ctx[t],p.ctx[t]=l)&&(!p.skip_bound&&p.bound[t]&&p.bound[t](l),m&&Y(e,t)),n})):[],p.update(),m=!0,o(p.before_update),p.fragment=!!c&&c(p.ctx),l.target){if(l.hydrate){const t=function(t){return Array.from(t.childNodes)}(l.target);p.fragment&&p.fragment.l(t),t.forEach(g)}else p.fragment&&p.fragment.c();l.intro&&B(e.$$.fragment),J(e,l.target,l.anchor,l.customElement),M()}A(f)}class G{$destroy(){X(this,1),this.$destroy=t}$on(e,n){if(!l(n))return t;const o=this.$$.callbacks[e]||(this.$$.callbacks[e]=[]);return o.push(n),()=>{const t=o.indexOf(n);-1!==t&&o.splice(t,1)}}$set(t){var e;this.$$set&&(e=t,0!==Object.keys(e).length)&&(this.$$.skip_bound=!0,this.$$set(t),this.$$.skip_bound=!1)}}const K=[];function Q(e,n=t){let o;const l=new Set;function c(t){if(r(e,t)&&(e=t,o)){const t=!K.length;for(const t of l)t[1](),K.push(t,e);if(t){for(let t=0;t<K.length;t+=2)K[t][0](K[t+1]);K.length=0}}}return{set:c,update:function(t){c(t(e))},subscribe:function(r,s=t){const i=[r,s];return l.add(i),1===l.size&&(o=n(c)||t),r(e),()=>{l.delete(i),0===l.size&&o&&(o(),o=null)}}}}function W(e,n,r){const c=!Array.isArray(e),s=c?[e]:e,i=n.length<2;return a=e=>{let r=!1;const a=[];let d=0,f=t;const p=()=>{if(d)return;f();const o=n(c?a[0]:a,e);i?e(o):f=l(o)?o:t},g=s.map(((t,e)=>u(t,(t=>{a[e]=t,d&=~(1<<e),r&&p()}),(()=>{d|=1<<e}))));return r=!0,p(),function(){o(g),f(),r=!1}},{subscribe:Q(r,a).subscribe};var a}const Z=APP_LANG;USER_ID,CSRF_TOKEN,ADDITIONAL_MODULES;const tt="Regions";SAS_APP_URL;const et=CANTALOUPE_APP_URL;function nt(t=null,e="full",n="full"){if(!t)return"https://via.placeholder.com/96x96?text=No+Image";if((t=t.split("_")).length<3)return"https://via.placeholder.com/96x96?text=No+Image";const o=t[t.length-1].includes(",")?t.pop().replace(".jpg",""):e,l=t.join("_").replace(".jpg","");return`${et??"http://localhost:8182"}/iiif/2/${l}.jpg/${o}/${n}/0/default.jpg`}MEDIA_PATH;const ot=function(){const t=Q(JSON.parse(localStorage.getItem("documentSet"))||{}),{subscribe:e,get:n,update:o}=t;function l(t){localStorage.setItem("documentSet",JSON.stringify(t))}function r(t,e=!0){return e?t[tt]??{}:Object.entries(t).filter((([t,e])=>t!==tt))}function c(t,e,n){if(t[n]){const{[e]:o,...l}=t[n];t={...t,[n]:l}}return l(t),t}function s(t,e){return t.hasOwnProperty(e.type)||(t[e.type]={}),t[e.type]={...t[e.type],[e.id]:e},l(t),t}return{subscribe:e,save:()=>o((t=>(console.log(t),t))),empty:t=>o((e=>(t?delete e[tt]:Object.keys(e).forEach((t=>{t!==tt&&delete e[t]})),l(e),e))),addAll:t=>o((e=>function(t,e){return e.forEach((e=>{t[e.type]||(t[e.type]={}),t[e.type][e.id]=e})),l(t),t}(e,t))),removeAll:(t,e)=>o((n=>function(t,e,n){return t[n]?(e.forEach((e=>{delete t[n][e]})),l(t),t):t}(n,t,e))),remove:(t,e)=>o((n=>c(n,t,e))),add:t=>o((e=>s(e,t))),toggle:t=>o((e=>e[t.type]?.[t.id]?c(e,t.id,t.type):s(e,t))),toggleAll:(t,e,n)=>o((t=>{})),isSelected:W(t,(t=>e=>t[e.type]?.hasOwnProperty(e.id)||!1)),selected:W(t,(t=>e=>r(t,e))),nbSelected:W(t,(t=>e=>{const n=r(t,e);return e?Object.keys(n).length:n.reduce(((t,[e,n])=>t+Object.keys(n).length),0)}))}}();function lt(t,e,n){const o=t.slice();return o[5]=e[n][0],o[6]=e[n][1],o}function rt(t,e,n){const o=t.slice();return o[9]=e[n],o}function ct(t){let e;return{c(){e=h("span"),e.innerHTML='<span class="icon has-text-success"><i class="fas fa-check-circle"></i></span> \n                                <span style="margin-left: -0.5rem">Public</span>',k(e,"class","pl-3 icon-text is-size-7 is-center has-text-weight-normal")},m(t,n){p(t,e,n)},d(t){t&&g(e)}}}function st(t){let e,n,o=t[0].hasOwnProperty("iiif"),l=t[0].buttons.includes("regions"),r=o&&it(t),c=l&&at(t);return{c(){e=h("p"),r&&r.c(),n=y(),c&&c.c(),k(e,"class","subtitle is-6 mb-0 ml-2 pt-2")},m(t,o){p(t,e,o),r&&r.m(e,null),f(e,n),c&&c.m(e,null)},p(t,s){1&s&&(o=t[0].hasOwnProperty("iiif")),o?r?r.p(t,s):(r=it(t),r.c(),r.m(e,n)):r&&(r.d(1),r=null),1&s&&(l=t[0].buttons.includes("regions")),l?c?c.p(t,s):(c=at(t),c.c(),c.m(e,null)):c&&(c.d(1),c=null)},d(t){t&&g(e),r&&r.d(),c&&c.d()}}}function it(t){let e,n=t[0].iiif,o=[];for(let e=0;e<n.length;e+=1)o[e]=ut(rt(t,n,e));return{c(){for(let t=0;t<o.length;t+=1)o[t].c();e=x()},m(t,n){for(let e=0;e<o.length;e+=1)o[e]&&o[e].m(t,n);p(t,e,n)},p(t,l){if(1&l){let r;for(n=t[0].iiif,r=0;r<n.length;r+=1){const c=rt(t,n,r);o[r]?o[r].p(c,l):(o[r]=ut(c),o[r].c(),o[r].m(e.parentNode,e))}for(;r<o.length;r+=1)o[r].d(1);o.length=n.length}},d(t){m(o,t),t&&g(e)}}}function ut(t){let e,n=t[9]+"";return{c(){e=h("span"),k(e,"class","tag logo mt-1")},m(t,o){p(t,e,o),e.innerHTML=n},p(t,o){1&o&&n!==(n=t[9]+"")&&(e.innerHTML=n)},d(t){t&&g(e)}}}function at(t){let e,n,o,l,r;return{c(){e=h("a"),n=h("span"),o=y(),l=h("span"),l.textContent=""+("en"===Z?"Show regions":"Afficher les régions"),k(n,"class","iconify"),k(n,"data-icon","entypo:documents"),k(l,"class","ml-2"),k(e,"href",r=t[0].url+"regions/"),k(e,"class","button is-small is-rounded is-link px-2 py-1"),k(e,"title","en"===Z?"View image regions":"Afficher les régions d'images")},m(t,r){p(t,e,r),f(e,n),f(e,o),f(e,l)},p(t,n){1&n&&r!==(r=t[0].url+"regions/")&&k(e,"href",r)},d(t){t&&g(e)}}}function dt(t){let e,n,o=t[1]?"Retirer de la":"Ajouter à la";return{c(){e=b(o),n=b(" sélection")},m(t,o){p(t,e,o),p(t,n,o)},p(t,n){2&n&&o!==(o=t[1]?"Retirer de la":"Ajouter à la")&&_(e,o)},d(t){t&&g(e),t&&g(n)}}}function ft(t){let e,n,o=t[1]?"Remove from":"Add to";return{c(){e=b(o),n=b(" selection")},m(t,o){p(t,e,o),p(t,n,o)},p(t,n){2&n&&o!==(o=t[1]?"Remove from":"Add to")&&_(e,o)},d(t){t&&g(e),t&&g(n)}}}function pt(t){let e;return{c(){e=$("path"),k(e,"fill","currentColor"),k(e,"d","M0 48C0 21.5 21.5 0 48 0l0 48V441.4l130.1-92.9c8.3-6 19.6-6 27.9 0L336 441.4V48H48V0H336c26.5 0 48 21.5 48 48V488c0 9-5 17.2-13 21.3s-17.6 3.4-24.9-1.8L192 397.5 37.9 507.5c-7.3 5.2-16.9 5.9-24.9 1.8S0 497 0 488V48z")},m(t,n){p(t,e,n)},d(t){t&&g(e)}}}function gt(t){let e;return{c(){e=$("path"),k(e,"fill","currentColor"),k(e,"d","M0 48V487.7C0 501.1 10.9 512 24.3 512c5 0 9.9-1.5 14-4.4L192 400 345.7 507.6c4.1 2.9 9 4.4 14 4.4c13.4 0 24.3-10.9 24.3-24.3V48c0-26.5-21.5-48-48-48H48C21.5 0 0 21.5 0 48z")},m(t,n){p(t,e,n)},d(t){t&&g(e)}}}function mt(t){let e,n,o,l,r,c,s,i=t[5]+"",u=t[6]+"";return{c(){e=h("tr"),n=h("th"),o=b(i),l=y(),r=h("td"),c=b(u),s=y(),k(n,"class","is-narrow is-3")},m(t,i){p(t,e,i),f(e,n),f(n,o),f(e,l),f(e,r),f(r,c),f(e,s)},p(t,e){1&e&&i!==(i=t[5]+"")&&_(o,i),1&e&&u!==(u=t[6]+"")&&_(c,u)},d(t){t&&g(e)}}}function ht(e){let n,o,l,r,c,s,u,a,d,x,A,S,L,E,O,N,R,j,C,P,M,I,V,T,H,z,B,D,U,q,J,X,Y,F,G,K,Q,W=e[0].type+"",tt=e[0].id+"",et=e[0].title+"",ot=e[0].user+"",rt=e[0].updated_at+"",it=e[0].is_public&&ct(),ut=0!==e[0].buttons.length&&st(e);let at=("en"===Z?ft:dt)(e);function ht(t,e){return t[1]?gt:pt}let $t=ht(e),bt=$t(e),yt=Object.entries(e[0].metadata),xt=[];for(let t=0;t<yt.length;t+=1)xt[t]=mt(lt(e,yt,t));return{c(){n=h("div"),o=h("div"),l=h("div"),r=h("div"),c=h("div"),s=h("figure"),u=h("img"),d=y(),x=h("div"),A=h("a"),S=h("span"),L=b(W),E=b(" #"),O=b(tt),N=y(),R=b(et),j=y(),it&&it.c(),P=y(),M=h("p"),I=b(ot),V=y(),T=h("span"),H=b(rt),z=y(),ut&&ut.c(),B=y(),D=h("div"),U=h("button"),at.c(),q=y(),J=$("svg"),bt.c(),X=y(),Y=h("div"),F=h("table"),G=h("tbody");for(let t=0;t<xt.length;t+=1)xt[t].c();i(u.src,a=nt(e[0].img,"full","250,"))||k(u,"src",a),k(u,"alt","Record illustration"),k(s,"class","card image is-96x96 svelte-xqp9nk"),k(c,"class","media-left"),k(S,"class","tag px-2 py-1 mb-1 is-dark is-rounded"),k(A,"href",C=e[0].url),k(A,"class","title is-4 hoverable pt-2 svelte-xqp9nk"),k(T,"class","tag p-1 mb-1"),k(M,"class","subtitle is-6 mb-0 ml-2 pt-2"),k(x,"class","media-content"),k(J,"xmlns","http://www.w3.org/2000/svg"),k(J,"viewBox","0 0 384 512"),k(J,"class","svelte-xqp9nk"),k(U,"class","button"),w(U,"is-inverted",e[1]),k(D,"class","media-right"),k(r,"class","media"),k(F,"class","table pl-2 is-fullwidth"),k(Y,"class","content"),k(l,"class","card-content"),k(o,"class","card mb-3"),k(n,"class","item")},m(t,i){p(t,n,i),f(n,o),f(o,l),f(l,r),f(r,c),f(c,s),f(s,u),f(r,d),f(r,x),f(x,A),f(A,S),f(S,L),f(S,E),f(S,O),f(A,N),f(A,R),f(A,j),it&&it.m(A,null),f(x,P),f(x,M),f(M,I),f(M,V),f(M,T),f(T,H),f(x,z),ut&&ut.m(x,null),f(r,B),f(r,D),f(D,U),at.m(U,null),f(U,q),f(U,J),bt.m(J,null),f(l,X),f(l,Y),f(Y,F),f(F,G);for(let t=0;t<xt.length;t+=1)xt[t]&&xt[t].m(G,null);K||(Q=v(U,"click",e[4]),K=!0)},p(t,[e]){if(1&e&&!i(u.src,a=nt(t[0].img,"full","250,"))&&k(u,"src",a),1&e&&W!==(W=t[0].type+"")&&_(L,W),1&e&&tt!==(tt=t[0].id+"")&&_(O,tt),1&e&&et!==(et=t[0].title+"")&&_(R,et),t[0].is_public?it||(it=ct(),it.c(),it.m(A,null)):it&&(it.d(1),it=null),1&e&&C!==(C=t[0].url)&&k(A,"href",C),1&e&&ot!==(ot=t[0].user+"")&&_(I,ot),1&e&&rt!==(rt=t[0].updated_at+"")&&_(H,rt),0!==t[0].buttons.length?ut?ut.p(t,e):(ut=st(t),ut.c(),ut.m(x,null)):ut&&(ut.d(1),ut=null),at.p(t,e),$t!==($t=ht(t))&&(bt.d(1),bt=$t(t),bt&&(bt.c(),bt.m(J,null))),2&e&&w(U,"is-inverted",t[1]),1&e){let n;for(yt=Object.entries(t[0].metadata),n=0;n<yt.length;n+=1){const o=lt(t,yt,n);xt[n]?xt[n].p(o,e):(xt[n]=mt(o),xt[n].c(),xt[n].m(G,null))}for(;n<xt.length;n+=1)xt[n].d(1);xt.length=yt.length}},i:t,o:t,d(t){t&&g(n),it&&it.d(),ut&&ut.d(),at.d(),bt.d(),m(xt,t),K=!1,Q()}}}function $t(t,e,n){let o,l;const{isSelected:r}=ot;a(t,r,(t=>n(3,l=t)));let{item:c}=e;return t.$$set=t=>{"item"in t&&n(0,c=t.item)},t.$$.update=()=>{9&t.$$.dirty&&n(1,o=l(c))},[c,o,r,l,()=>ot.toggle(c)]}class bt extends G{constructor(t){super(),F(this,t,$t,ht,r,{item:0})}}function yt(e){let n,o,l,r,c,s,i,u,a,d="en"===Z?"Selection":"Sélection";return{c(){n=h("div"),o=h("button"),l=h("span"),r=h("i"),c=y(),s=b(d),i=b("\n            ("),u=b(e[0]),a=b(")"),k(r,"class","fa-solid fa-book-bookmark"),k(l,"id","btn-content"),k(o,"id","set-btn"),k(o,"class","button px-5 py-4 is-link js-modal-trigger svelte-hs48f9"),k(o,"data-target","selection-modal"),k(n,"class","set-container svelte-hs48f9")},m(t,e){p(t,n,e),f(n,o),f(o,l),f(l,r),f(l,c),f(l,s),f(l,i),f(l,u),f(l,a)},p(t,[e]){1&e&&_(u,t[0])},i:t,o:t,d(t){t&&g(n)}}}function xt(t,e,n){let{selectionLength:o=0}=e,l=o;return t.$$set=t=>{"selectionLength"in t&&n(0,o=t.selectionLength)},t.$$.update=()=>{if(3&t.$$.dirty&&o!==l){const t=o>l;n(1,l=o);const e=document.getElementById("btn-content");e&&e.animate([{transform:t?"translateY(-7px)":"translateX(-5px)"},{transform:t?"translateY(7px)":"translateX(5px)"},{transform:"translate(0)"}],{duration:300,easing:"cubic-bezier(0.65, 0, 0.35, 1)"})}},[o,l]}class vt extends G{constructor(t){super(),F(this,t,xt,yt,r,{selectionLength:0})}}function kt(e){let n,l,r,c,s,i,u,a,d,m,$="en"===Z?"Save selection":"Sauvegarder la sélection";return{c(){n=h("footer"),l=h("div"),r=h("button"),r.textContent=""+("en"===Z?"Clear selection":"Vider la sélection"),c=y(),s=h("button"),i=h("i"),u=y(),a=b($),k(r,"class","button is-link is-light"),k(i,"class","fa-solid fa-floppy-disk"),k(s,"class","button is-link"),k(l,"class","buttons"),k(n,"class","modal-card-foot is-center")},m(t,o){p(t,n,o),f(n,l),f(l,r),f(l,c),f(l,s),f(s,i),f(s,u),f(s,a),d||(m=[v(r,"click",e[1]),v(s,"click",e[2])],d=!0)},p:t,i:t,o:t,d(t){t&&g(n),d=!1,o(m)}}}function _t(t,e,n){let{isRegion:o=!0}=e;return t.$$set=t=>{"isRegion"in t&&n(0,o=t.isRegion)},[o,()=>ot.empty(o),()=>ot.save()]}class wt extends G{constructor(t){super(),F(this,t,_t,kt,r,{isRegion:0})}}function At(t){let e,n,o,l,r,c,s,i,u,a,m,$,x,v,w,A,S,L,E,O="en"===Z?"Selected regions":"Regions sélectionnées";const N=t[3].default,R=function(t,e,n,o){if(t){const l=d(t,e,n,o);return t[0](l)}}(N,t,t[2],null);return L=new wt({props:{isRegion:t[0]}}),{c(){e=h("div"),n=h("div"),o=y(),l=h("div"),r=h("div"),c=h("div"),s=h("i"),i=y(),u=b(O),a=b("\n                ("),m=b(t[1]),$=b(")"),x=y(),v=h("button"),w=y(),A=h("section"),R&&R.c(),S=y(),q(L.$$.fragment),k(n,"class","modal-background"),k(s,"class","fa-solid fa-book-bookmark"),k(c,"class","title is-4 mb-0 media-content"),k(v,"class","delete media-left"),k(v,"aria-label","close"),k(r,"class","modal-card-head media mb-0"),k(A,"class","modal-card-body"),k(l,"class","modal-content"),k(e,"id","selection-modal"),k(e,"class","modal fade"),k(e,"tabindex","-1"),k(e,"aria-labelledby","selection-modal-label"),k(e,"aria-hidden","true")},m(t,d){p(t,e,d),f(e,n),f(e,o),f(e,l),f(l,r),f(r,c),f(c,s),f(c,i),f(c,u),f(c,a),f(c,m),f(c,$),f(r,x),f(r,v),f(l,w),f(l,A),R&&R.m(A,null),f(l,S),J(L,l,null),E=!0},p(t,[e]){(!E||2&e)&&_(m,t[1]),R&&R.p&&(!E||4&e)&&function(t,e,n,o,l,r){if(l){const c=d(e,n,o,r);t.p(c,l)}}(R,N,t,t[2],E?function(t,e,n,o){if(t[2]&&o){const l=t[2](o(n));if(void 0===e.dirty)return l;if("object"==typeof l){const t=[],n=Math.max(e.dirty.length,l.length);for(let o=0;o<n;o+=1)t[o]=e.dirty[o]|l[o];return t}return e.dirty|l}return e.dirty}(N,t[2],e,null):function(t){if(t.ctx.length>32){const e=[],n=t.ctx.length/32;for(let t=0;t<n;t++)e[t]=-1;return e}return-1}(t[2]),null);const n={};1&e&&(n.isRegion=t[0]),L.$set(n)},i(t){E||(B(R,t),B(L.$$.fragment,t),E=!0)},o(t){D(R,t),D(L.$$.fragment,t),E=!1},d(t){t&&g(e),R&&R.d(t),X(L)}}}function St(t,e,n){let{$$slots:o={},$$scope:l}=e,{isRegion:r=!1}=e,{selectionLength:c=!1}=e;return t.$$set=t=>{"isRegion"in t&&n(0,r=t.isRegion),"selectionLength"in t&&n(1,c=t.selectionLength),"$$scope"in t&&n(2,l=t.$$scope)},[r,c,l,o]}class Lt extends G{constructor(t){super(),F(this,t,St,At,r,{isRegion:0,selectionLength:1})}}function Et(t,e,n){const o=t.slice();return o[8]=e[n][0],o[9]=e[n][1],o}function Ot(t,e,n){const o=t.slice();return o[12]=e[n][0],o[13]=e[n][1],o}function Nt(t,e,n){const o=t.slice();return o[16]=e[n],o}function Rt(t){let e,n,l=[],r=new Map,c=t[0];const s=t=>t[16].id;for(let e=0;e<c.length;e+=1){let n=Nt(t,c,e),o=s(n);r.set(o,l[e]=Ct(o,n))}let i=null;return c.length||(i=jt()),{c(){e=h("div");for(let t=0;t<l.length;t+=1)l[t].c();i&&i.c()},m(t,o){p(t,e,o);for(let t=0;t<l.length;t+=1)l[t]&&l[t].m(e,null);i&&i.m(e,null),n=!0},p(t,n){1&n&&(c=t[0],H(),l=function(t,e,n,l,r,c,s,i,u,a,d,f){let p=t.length,g=c.length,m=p;const h={};for(;m--;)h[t[m].key]=m;const $=[],b=new Map,y=new Map,x=[];for(m=g;m--;){const t=f(r,c,m),o=n(t);let i=s.get(o);i?l&&x.push((()=>i.p(t,e))):(i=a(o,t),i.c()),b.set(o,$[m]=i),o in h&&y.set(o,Math.abs(m-h[o]))}const v=new Set,k=new Set;function _(t){B(t,1),t.m(i,d),s.set(t.key,t),d=t.first,g--}for(;p&&g;){const e=$[g-1],n=t[p-1],o=e.key,l=n.key;e===n?(d=e.first,p--,g--):b.has(l)?!s.has(o)||v.has(o)?_(e):k.has(l)?p--:y.get(o)>y.get(l)?(k.add(o),_(e)):(v.add(l),p--):(u(n,s),p--)}for(;p--;){const e=t[p];b.has(e.key)||u(e,s)}for(;g;)_($[g-1]);return o(x),$}(l,n,s,1,t,c,r,e,U,Ct,null,Nt),z(),!c.length&&i?i.p(t,n):c.length?i&&(i.d(1),i=null):(i=jt(),i.c(),i.m(e,null)))},i(t){if(!n){for(let t=0;t<c.length;t+=1)B(l[t]);n=!0}},o(t){for(let t=0;t<l.length;t+=1)D(l[t]);n=!1},d(t){t&&g(e);for(let t=0;t<l.length;t+=1)l[t].d();i&&i.d()}}}function jt(e){let n;return{c(){n=h("p"),n.textContent=""+("en"===Z?"No records found":"Aucun document trouvé")},m(t,e){p(t,n,e)},p:t,d(t){t&&g(n)}}}function Ct(t,e){let n,o,l;return o=new bt({props:{item:e[16]}}),{key:t,first:null,c(){n=x(),q(o.$$.fragment),this.first=n},m(t,e){p(t,n,e),J(o,t,e),l=!0},p(t,n){e=t;const l={};1&n&&(l.item=e[16]),o.$set(l)},i(t){l||(B(o.$$.fragment,t),l=!0)},o(t){D(o.$$.fragment,t),l=!1},d(t){t&&g(n),X(o,t)}}}function Pt(e){let n,o,l;return{c(){n=h("tr"),o=h("td"),o.textContent=""+("en"===Z?"No documents in selection":"Aucun document sélectionné"),l=y()},m(t,e){p(t,n,e),f(n,o),f(n,l)},p:t,d(t){t&&g(n)}}}function Mt(e){let n,o,l;return{c(){n=h("tr"),o=h("td"),o.textContent=""+("en"===Z?"No documents in selection":"Aucun document sélectionné"),l=y()},m(t,e){p(t,n,e),f(n,o),f(n,l)},p:t,d(t){t&&g(n)}}}function It(t){let e,n,o,l,r,c,s,i,u,a,d,m,$,x,w,A,S=t[12]+"",L=t[13].title+"";function E(){return t[7](t[12],t[8])}return{c(){e=h("tr"),n=h("th"),o=h("span"),l=b("#"),r=b(S),c=y(),s=h("td"),i=h("a"),u=b(L),d=y(),m=h("td"),$=h("button"),x=y(),k(o,"class","tag px-2 py-1 mb-1 is-dark is-rounded"),k(n,"class","is-narrow is-3"),k(i,"href",a=t[13].url),k(i,"target","_blank"),k($,"class","delete"),k($,"aria-label","close"),k(m,"class","is-narrow")},m(t,a){p(t,e,a),f(e,n),f(n,o),f(o,l),f(o,r),f(e,c),f(e,s),f(s,i),f(i,u),f(e,d),f(e,m),f(m,$),f(e,x),w||(A=v($,"click",E),w=!0)},p(e,n){t=e,4&n&&S!==(S=t[12]+"")&&_(r,S),4&n&&L!==(L=t[13].title+"")&&_(u,L),4&n&&a!==(a=t[13].url)&&k(i,"href",a)},d(t){t&&g(e),w=!1,A()}}}function Vt(t){let e,n,o,l,r,c,s=t[8]+"",i=Object.entries(t[9]),u=[];for(let e=0;e<i.length;e+=1)u[e]=It(Ot(t,i,e));let a=null;return i.length||(a=Mt()),{c(){e=h("h3"),n=b(s),o=y(),l=h("table"),r=h("tbody");for(let t=0;t<u.length;t+=1)u[t].c();a&&a.c(),c=y(),k(l,"class","table pl-2 is-fullwidth")},m(t,s){p(t,e,s),f(e,n),p(t,o,s),p(t,l,s),f(l,r);for(let t=0;t<u.length;t+=1)u[t]&&u[t].m(r,null);a&&a.m(r,null),f(l,c)},p(t,e){if(4&e&&s!==(s=t[8]+"")&&_(n,s),4&e){let n;for(i=Object.entries(t[9]),n=0;n<i.length;n+=1){const o=Ot(t,i,n);u[n]?u[n].p(o,e):(u[n]=It(o),u[n].c(),u[n].m(r,null))}for(;n<u.length;n+=1)u[n].d(1);u.length=i.length,!i.length&&a?a.p(t,e):i.length?a&&(a.d(1),a=null):(a=Mt(),a.c(),a.m(r,null))}},d(t){t&&g(e),t&&g(o),t&&g(l),m(u,t),a&&a.d()}}}function Tt(t){let e,n=t[2],o=[];for(let e=0;e<n.length;e+=1)o[e]=Vt(Et(t,n,e));let l=null;return n.length||(l=Pt()),{c(){for(let t=0;t<o.length;t+=1)o[t].c();e=x(),l&&l.c()},m(t,n){for(let e=0;e<o.length;e+=1)o[e]&&o[e].m(t,n);p(t,e,n),l&&l.m(t,n)},p(t,r){if(4&r){let c;for(n=t[2],c=0;c<n.length;c+=1){const l=Et(t,n,c);o[c]?o[c].p(l,r):(o[c]=Vt(l),o[c].c(),o[c].m(e.parentNode,e))}for(;c<o.length;c+=1)o[c].d(1);o.length=n.length,!n.length&&l?l.p(t,r):n.length?l&&(l.d(1),l=null):(l=Pt(),l.c(),l.m(e.parentNode,e))}},d(t){m(o,t),t&&g(e),l&&l.d(t)}}}function Ht(t){let e,n,o,l,r;e=new vt({props:{selectionLength:t[1]}});let c=0!==t[0].length&&Rt(t);return l=new Lt({props:{selectionLength:t[1],$$slots:{default:[Tt]},$$scope:{ctx:t}}}),{c(){q(e.$$.fragment),n=y(),c&&c.c(),o=y(),q(l.$$.fragment)},m(t,s){J(e,t,s),p(t,n,s),c&&c.m(t,s),p(t,o,s),J(l,t,s),r=!0},p(t,[n]){const r={};2&n&&(r.selectionLength=t[1]),e.$set(r),0!==t[0].length?c?(c.p(t,n),1&n&&B(c,1)):(c=Rt(t),c.c(),B(c,1),c.m(o.parentNode,o)):c&&(H(),D(c,1,1,(()=>{c=null})),z());const s={};2&n&&(s.selectionLength=t[1]),524292&n&&(s.$$scope={dirty:n,ctx:t}),l.$set(s)},i(t){r||(B(e.$$.fragment,t),B(c),B(l.$$.fragment,t),r=!0)},o(t){D(e.$$.fragment,t),D(c),D(l.$$.fragment,t),r=!1},d(t){X(e,t),t&&g(n),c&&c.d(t),t&&g(o),X(l,t)}}}function zt(t,e,n){let o,l,r,c;const{selected:s,nbSelected:i}=ot;a(t,s,(t=>n(6,c=t))),a(t,i,(t=>n(5,r=t)));let{records:u=[]}=e;return t.$$set=t=>{"records"in t&&n(0,u=t.records)},t.$$.update=()=>{64&t.$$.dirty&&n(2,o=c(!1)),32&t.$$.dirty&&n(1,l=r(!1))},[u,l,o,s,i,r,c,(t,e)=>ot.remove(t,e)]}const Bt=(Dt="record-data",document.getElementById(Dt)?JSON.parse(document.getElementById(Dt).textContent):[]);var Dt;return new class extends G{constructor(t){super(),F(this,t,zt,Ht,r,{records:0})}}({target:document.getElementById("record-list"),props:{records:Bt}})}();
//# sourceMappingURL=recordList.js.map
