// Node VM functional tests. Deliberately not a browser/layout certification.
const vm=require('node:vm');const fs=require('node:fs');const assert=require('node:assert/strict');const path=require('node:path');
const nodes=new Map();
function node(selector){if(!nodes.has(selector))nodes.set(selector,{innerHTML:'',textContent:'',hidden:false,value:'',open:false,dataset:{},style:{},listeners:{},classList:{toggle(){return true},remove(){}},addEventListener(type,fn){this.listeners[type]=fn},setAttribute(){},replaceChildren(){this.innerHTML=''},close(){this.open=false},showModal(){this.open=true},focus(){},reset(){},querySelector(){return node(selector+'/button')}});return nodes.get(selector)}
const document={querySelector:node,querySelectorAll:()=>[],createElement:()=>({click(){}})};
let cookies='',exportURL;
const context=vm.createContext({document,location:{hash:''},navigator:{},window:{addEventListener(){}},console,setTimeout,clearTimeout,Date,URL:{createObjectURL(blob){exportURL=blob;return 'blob:example'},revokeObjectURL(){}},Blob,confirm:()=>true,FormData:class{constructor(target){this.data=target.formData}*[Symbol.iterator](){yield*Object.entries(this.data)}},fetch:async(url,options)=>{const response=await fetch('http://127.0.0.1:8765'+url,{...options,headers:{...options.headers,Cookie:cookies}});const cookie=response.headers.get('set-cookie');if(cookie)cookies=cookie.split(';')[0];return response;}});
const evalJS=code=>vm.runInContext(code,context);
const fixture={kind:'task',title:'Frontend Test <script>x</script>',body:'Suchwort Abc321',module:'projects',status:'open',due:'2026-10-04',project_id:'',source:'Frontend-Testfixture',evidence:'review',observed:'2026-10-04',tags:'Test',url:''};
(async()=>{
 vm.runInContext(fs.readFileSync(path.join(__dirname,'../web/app.js'),'utf8'),context);
 await new Promise(r=>setTimeout(r,100));
 await evalJS("(async()=>{const r=await api('/api/login',{method:'POST',body:JSON.stringify({password:'Demo-only-password-42!'})});csrf=r.csrf;await enter()})()");
 assert.equal(node('#shell').hidden,false);
 assert.equal((node('#navigation').innerHTML.match(/href="#/g)||[]).length,9);
 const result=await evalJS(`api('/api/records',{method:'POST',body:${JSON.stringify(JSON.stringify(fixture))}})`);
 await evalJS('refresh()');
 node('#search').value='Abc321';evalJS('render()');
 assert.match(node('#content').innerHTML,/Frontend Test &lt;script&gt;x&lt;\/script&gt;/);
 assert.doesNotMatch(node('#content').innerHTML,/<script>x/);
 assert.match(node('#content').innerHTML,/Frontend-Testfixture/);
 const editor=node('#record-form');editor.formData={id:result.id,...fixture,title:'Frontend · bearbeitet'};editor.querySelector=()=>node('save-button');
 await editor.listeners.submit({preventDefault(){},target:editor});
 await evalJS('refresh()');
 assert.equal(evalJS(`records.find(r=>r.id==='${result.id}').title`),'Frontend · bearbeitet');
 evalJS("ask('Welche Fristen stehen an?')");assert.match(node('#answer').innerHTML,/Quelle: Frontend-Testfixture/);
 assert.match(evalJS("projectProgress(records.find(r=>r.kind==='project'))"),/1 \/ 2 Aufgaben erledigt · 50 %/);
 for(const view of ['lounge','library','economics','health','laboratory','crew','projects','systems']){context.location.hash='#'+view;node('#search').value='';evalJS('render()');assert.match(node('#content').innerHTML,/<h1>/);}
 assert.match(node('#content').innerHTML,/Nicht eingerichtet/);assert.match(node('#content').innerHTML,/Inaktiv/);
 await node('#content').listeners.click({target:{closest(){return {id:'export',dataset:{}}}}});
 assert.equal(JSON.parse(await exportURL.text()).schema_version,1);
 const oldFetch=context.fetch;context.fetch=async()=>{throw new Error('Disconnected')};
 await assert.rejects(evalJS("api('/api/records')"),/nicht erreichbar/);context.fetch=oldFetch;
 await evalJS(`api('/api/records/${result.id}',{method:'DELETE'})`);
 await node('#logout').listeners.click();
 assert.equal(node('#shell').hidden,true);assert.equal(node('#content').innerHTML,'');
 await assert.rejects(evalJS("api('/api/export')"),/Bitte anmelden/);
 console.log('Frontend PASS: navigation (9), login/API, create, form edit, refresh, search, XSS escaping, sources, real progress, export, connection failure, logout. No browser/layout/iOS claim.');
})().catch(e=>{console.error(e);process.exit(1)});
