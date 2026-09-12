"""Genera el HTML del dashboard a partir de los datos del modelo."""
import json

HTML = r"""<!DOCTYPE html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Pronostico de partidos</title><style>
*{box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;margin:0;padding:22px 14px;background:#f4f4f1;color:#1a1a19;line-height:1.55}
.wrap{max-width:920px;margin:0 auto}
h1{font-size:21px;font-weight:500;margin:0 0 3px}
.sub{color:#6b6a65;font-size:13px;margin:0 0 20px}
.card{background:#fff;border:1px solid #e1e0d9;border-radius:12px;padding:16px;margin-bottom:16px}
h2{font-size:16px;font-weight:500;margin:0 0 12px}
label{display:block;font-size:13px;color:#6b6a65;margin-bottom:4px}
select{width:100%;padding:9px;border:1px solid #d0cfc8;border-radius:8px;background:#fff;font-size:14px;font-family:inherit;margin-bottom:10px}
.tabs{display:flex;gap:6px;margin-bottom:14px}
.tabs button{flex:1;padding:8px;border:1px solid #d0cfc8;background:#fff;border-radius:8px;font-size:13px;font-family:inherit;cursor:pointer;color:#6b6a65}
.tabs button.on{background:#1a1a19;color:#fff;border-color:#1a1a19}
.day{font-size:12px;color:#8a8983;text-transform:uppercase;letter-spacing:.04em;margin:14px 0 6px}
.fx{display:flex;align-items:center;gap:10px;padding:10px;border:1px solid #ececE6;border-radius:9px;margin-bottom:6px;cursor:pointer;background:#fff}
.fx:hover{border-color:#c9c8c0;background:#fafaf8}
.fx.sel{border-color:#1a1a19;background:#fafaf8}
.fx .hr{font-size:12px;color:#8a8983;width:46px;flex-shrink:0;font-variant-numeric:tabular-nums}
.fx .tt{flex:1;font-size:14px}
.fx .mini{display:flex;gap:2px;width:78px;flex-shrink:0;height:7px;border-radius:3px;overflow:hidden}
.bar{display:flex;align-items:center;gap:9px;margin-bottom:7px;font-size:14px}
.bar .nm{width:150px;flex-shrink:0}
.bar .tr{flex:1;height:22px;background:#eeede8;border-radius:4px;overflow:hidden}
.bar .fl{height:100%}
.bar .pc{width:52px;text-align:right;font-variant-numeric:tabular-nums;font-weight:500}
.stats{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:14px}
.st{background:#f7f6f3;border-radius:8px;padding:11px}
.st .l{font-size:12px;color:#6b6a65}.st .v{font-size:21px;font-weight:500;font-variant-numeric:tabular-nums}
.sc{display:flex;flex-wrap:wrap;gap:6px;margin-top:12px;align-items:center}
.sc span{background:#f0efec;border-radius:6px;padding:4px 8px;font-size:13px;font-variant-numeric:tabular-nums}
table{width:100%;border-collapse:collapse;font-size:13px}
th{text-align:left;font-weight:500;color:#6b6a65;border-bottom:1px solid #e1e0d9;padding:6px 3px}
td{padding:6px 3px;border-bottom:1px solid #f0efec;font-variant-numeric:tabular-nums}
td.n,th.n{text-align:right}
.up{color:#177a4e;font-weight:500}.dn{color:#b03a2e;font-weight:500}.f0{color:#8a8983}
.note{font-size:12px;color:#8a8983;margin-top:12px}
.kpis{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:14px}
.kpi{background:#f7f6f3;border-radius:8px;padding:12px;text-align:center}
.kpi .v{font-size:23px;font-weight:500;font-variant-numeric:tabular-nums;line-height:1.2}
.kpi .l{font-size:11px;color:#6b6a65;margin-top:2px}
.ok{color:#177a4e;font-weight:500}.no{color:#b03a2e;font-weight:500}
.hrow{display:flex;align-items:center;gap:8px;padding:9px 0;border-bottom:1px solid #f0efec;font-size:13px}
.hrow .fe{width:42px;flex-shrink:0;color:#8a8983;font-size:11px}
.hrow .pt{flex:1;line-height:1.35}
.hrow .mk{width:64px;text-align:right;flex-shrink:0;font-variant-numeric:tabular-nums}
.hrow .ic{width:18px;text-align:center;flex-shrink:0;font-weight:600}
.vacio{padding:18px;text-align:center;color:#8a8983;font-size:13px}
.mm{display:flex;gap:14px;flex-wrap:wrap;margin-top:10px;font-size:13px;color:#6b6a65}
.hd{font-size:15px;font-weight:500;margin:2px 0 10px}
@media(max-width:640px){.bar .nm{width:98px;font-size:13px}.fx .mini{display:none}}
</style></head><body><div class="wrap">
<h1>Pronostico de partidos</h1>
<p class="sub">Elo + ataque/defensa + momento, calibrado por competencia &middot; __NPART__ partidos &middot; horarios de Bolivia &middot; actualizado __FECHA__</p>
<div class="card">
<label for="comp">Competencia</label><select id="comp"></select>
<div class="tabs"><button id="t1" class="on">Proximos partidos</button><button id="t2">Cruce libre</button></div>
<div id="pane1"><div id="list"></div></div>
<div id="pane2" style="display:none">
<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px">
<div><label for="loc">Local</label><select id="loc"></select></div>
<div><label for="vis">Visitante</label><select id="vis"></select></div></div></div>
</div>
<div class="card" id="res">
<div class="hd" id="hd">Elige un partido</div>
<div id="bars"></div>
<div class="stats"><div class="st"><div class="l">Goles esperados local</div><div class="v" id="gl">&mdash;</div></div>
<div class="st"><div class="l">Goles esperados visitante</div><div class="v" id="gv">&mdash;</div></div></div>
<div class="sc" id="sc"></div><div class="mm" id="mm"></div>
<div id="cf" style="margin-top:12px;padding:11px;background:#f7f6f3;border-radius:8px;font-size:13px"></div>
<p class="note">Mezcla validada: 45% Elo, 35% ataque/defensa, 20% momento reciente. Acierto en Champions 59,0%. No incluye lesiones ni alineaciones.</p>
</div>
<div class="card"><h2>Pronostico contra resultado</h2>
<div id="hist"></div></div>
<div class="card"><h2>Ranking de equipos</h2>
<label for="lgf">Competencia</label><select id="lgf"></select>
<table><thead><tr><th>#</th><th>Equipo</th><th class="n">Elo</th><th class="n">Ataque</th><th class="n">Defensa</th><th class="n">Momento</th></tr></thead><tbody id="tb"></tbody></table>
<p class="note">Momento: goles por partido por encima o por debajo de lo esperado en los ultimos 10 partidos.</p></div>
</div><script>
const D=__DATA__,T=D.teams,R=D.rosters,FX=D.fx,NOM=D.nom,W=D.w,CAL=D.cal,LAM=D.lam,CONF=D.conf,REL=D.rel;
const $=i=>document.getElementById(i),cap=s=>s.replace(/\b\w/g,c=>c.toUpperCase());
const DIAS=['domingo','lunes','martes','miercoles','jueves','viernes','sabado'];
const MES=['ene','feb','mar','abr','may','jun','jul','ago','sep','oct','nov','dic'];
const pois=(k,l)=>{let p=Math.exp(-l);for(let i=1;i<=k;i++)p*=l/i;return p;};
function grid(lh,la){const g=[];let t=0;
 for(let i=0;i<10;i++)for(let j=0;j<10;j++){let p=pois(i,lh)*pois(j,la),r=-0.03;
  if(i===0&&j===0)p*=1-lh*la*r;else if(i===0&&j===1)p*=1+lh*r;
  else if(i===1&&j===0)p*=1+la*r;else if(i===1&&j===1)p*=1-r;g.push([i,j,p]);t+=p;}
 return g.map(x=>[x[0],x[1],x[2]/t]);}
function agg(g){let H=0,E=0,A=0;g.forEach(([i,j,p])=>{i>j?H+=p:i===j?E+=p:A+=p});return[H,E,A];}
function pred(c,h,a){const th=T[h],ta=T[a];if(!th||!ta)return null;
 const d=(th.elo-ta.elo)/100;
 const p1=agg(grid(Math.exp(D.cL[c]+D.hL[c]+0.17*d),Math.exp(D.cL[c]-0.17*d)));
 const e2h=Math.exp(D.cL[c]+D.hL[c]+th.aL-ta.dL),e2a=Math.exp(D.cL[c]+ta.aL-th.dL);
 const e3h=Math.exp(D.cS[c]+D.hS[c]+th.aS-ta.dS),e3a=Math.exp(D.cS[c]+ta.aS-th.dS);
 const p2=agg(grid(e2h,e2a)),p3=agg(grid(e3h,e3a));
 let P=[0,1,2].map(i=>W[0]*p1[i]+W[1]*p2[i]+W[2]*p3[i]);let s=P.reduce((x,y)=>x+y);P=P.map(x=>x/s);
 let k=1,t=1;if(CAL[c]){k=1+LAM*(CAL[c][0]-1);t=1+LAM*(CAL[c][1]-1);}
 P=P.map(p=>Math.pow(p,1/t));P[1]*=k;s=P.reduce((x,y)=>x+y);P=P.map(x=>x/s);
 const e1h=Math.exp(D.cL[c]+D.hL[c]+0.17*d),e1a=Math.exp(D.cL[c]-0.17*d);
 return{P,lh:W[0]*e1h+W[1]*e2h+W[2]*e3h,la:W[0]*e1a+W[1]*e2a+W[2]*e3a};}
function tag(v){return `<span class="${v>0.15?'up':v<-0.15?'dn':'f0'}">${v>0?'+':''}${v.toFixed(2)}</span>`;}
const COL=['#2a78d6','#898781','#eb6834'];
function show(c,h,a,label){const r=pred(c,h,a);
 if(!r){$('bars').innerHTML='<p class="note">Faltan datos de uno de los equipos.</p>';return;}
 $('hd').textContent=label||(cap(h)+' vs '+cap(a));
 const L=[cap(h),'Empate',cap(a)];
 $('bars').innerHTML=r.P.map((p,i)=>`<div class="bar"><div class="nm">${L[i]}</div><div class="tr"><div class="fl" style="width:${(p*100).toFixed(1)}%;background:${COL[i]}"></div></div><div class="pc">${(p*100).toFixed(1)}%</div></div>`).join('');
 $('gl').textContent=r.lh.toFixed(2);$('gv').textContent=r.la.toFixed(2);
 $('sc').innerHTML='<span style="background:none;padding-left:0;color:#6b6a65">Marcadores probables:</span>'+
  grid(r.lh,r.la).sort((x,y)=>y[2]-x[2]).slice(0,6).map(([i,j,p])=>`<span>${i}-${j} &middot; ${(p*100).toFixed(0)}%</span>`).join('');
 $('mm').innerHTML=`<div>Momento ${cap(h)}: ataque ${tag(T[h].fA)} defensa ${tag(T[h].fD)}</div><div>Momento ${cap(a)}: ataque ${tag(T[a].fA)} defensa ${tag(T[a].fD)}</div>`;
 const mx=Math.max(...r.P),row=CONF.find(x=>mx>=x[0]&&mx<x[1])||CONF[0];
 const lvl=mx<0.45?['Baja','#b03a2e']:mx<0.55?['Media','#c07a1e']:mx<0.70?['Buena','#177a4e']:['Alta','#177a4e'];
 const rl=REL[c];
 $('cf').innerHTML=`<b style="color:${lvl[1]}">Confianza: ${lvl[0]}</b> &mdash; historicamente, cuando el modelo da entre ${Math.round(row[0]*100)}% y ${Math.round(Math.min(row[1],1)*100)}% al favorito, acierta el <b>${row[2].toFixed(1)}%</b> de las veces.`
  +(rl?`<div style="margin-top:6px;color:#6b6a65">En ${NOM[c]} el modelo acierta ${rl[0].toFixed(1)}% en promedio.</div>`:'');}
function lista(){const c=$('comp').value,f=FX[c]||[];
 if(!f.length){$('list').innerHTML='<p class="note">No hay partidos programados cargados para esta competencia. Usa "Cruce libre".</p>';return;}
 let out='',last='';
 f.forEach((m,i)=>{const dt=new Date(m.d+'T12:00:00');
  const dd=DIAS[dt.getDay()]+' '+dt.getDate()+' '+MES[dt.getMonth()];
  if(dd!==last){out+=`<div class="day">${dd}</div>`;last=dd;}
  const r=pred(c,m.h,m.a);
  const mini=r?`<div class="mini">${r.P.map((p,k)=>`<div style="width:${p*100}%;background:${COL[k]}"></div>`).join('')}</div>`:'';
  out+=`<div class="fx" data-i="${i}"><div class="hr">${m.t}</div><div class="tt">${m.hn} <span style="color:#8a8983">vs</span> ${m.an}</div>${mini}</div>`;});
 $('list').innerHTML=out;
 document.querySelectorAll('.fx').forEach(el=>el.onclick=()=>{
  document.querySelectorAll('.fx').forEach(x=>x.classList.remove('sel'));el.classList.add('sel');
  const m=f[+el.dataset.i];const dt=new Date(m.d+'T12:00:00');
  show(c,m.h,m.a,`${m.hn} vs ${m.an} — ${DIAS[dt.getDay()]} ${dt.getDate()} ${MES[dt.getMonth()]}, ${m.t}`);
  $('res').scrollIntoView({behavior:'smooth',block:'nearest'});});
 if(f.length){document.querySelector('.fx').click();}}
function libre(){const c=$('comp').value,l=(R[c]||[]).filter(t=>T[t]);
 [['loc',0],['vis',1]].forEach(([id,k])=>{const s=$(id),v=s.value;s.innerHTML='';
  l.forEach(t=>s.add(new Option(cap(t),t)));if(l.includes(v))s.value=v;else s.selectedIndex=k;});
 show(c,$('loc').value,$('vis').value);}
function tabla(){const lg=$('lgf').value,rows=(R[lg]||[]).filter(t=>T[t]).sort((a,b)=>T[b].elo-T[a].elo);
 $('tb').innerHTML=rows.map((t,i)=>`<tr><td>${i+1}</td><td>${cap(t)}</td><td class="n">${T[t].elo.toFixed(0)}</td><td class="n">${T[t].aL.toFixed(2)}</td><td class="n">${T[t].dL.toFixed(2)}</td><td class="n">${tag(T[t].fA+T[t].fD)}</td></tr>`).join('');}
Object.keys(NOM).forEach(k=>{if(R[k]){$('comp').add(new Option(NOM[k],k));$('lgf').add(new Option(NOM[k],k));}});
$('comp').value='UCL';$('lgf').value='UCL';
let tab=1;
$('t1').onclick=()=>{tab=1;$('t1').className='on';$('t2').className='';$('pane1').style.display='';$('pane2').style.display='none';lista();};
$('t2').onclick=()=>{tab=2;$('t2').className='on';$('t1').className='';$('pane2').style.display='';$('pane1').style.display='none';libre();};
$('comp').onchange=()=>{tab===1?lista():libre();};
['loc','vis'].forEach(i=>$(i).onchange=()=>show($('comp').value,$('loc').value,$('vis').value));
$('lgf').onchange=tabla;lista();tabla();
(function(){
 const H=D.hist||{n:0};
 if(!H.n){$('hist').innerHTML='<div class="vacio">Todavia no hay partidos cerrados.<br>El registro empieza a llenarse cuando se juegue el primer partido pronosticado.</div>';return;}
 const pc=100*H.hit/H.n;
 let out=`<div class="kpis">
  <div class="kpi"><div class="v">${H.n}</div><div class="l">partidos</div></div>
  <div class="kpi"><div class="v ${pc>=50?'ok':''}">${pc.toFixed(1)}%</div><div class="l">aciertos</div></div>
  <div class="kpi"><div class="v">33,3%</div><div class="l">azar</div></div></div>`;
 if(H.goles)out+=`<div class="note" style="margin:0 0 12px">Goles por partido: el modelo esperaba <b>${H.goles[0].toFixed(2)}</b> y se jugaron <b>${H.goles[1].toFixed(2)}</b>.</div>`;
 if(H.porcomp&&H.porcomp.length){
  out+='<table style="margin-bottom:16px"><thead><tr><th>Competencia</th><th class="n">Partidos</th><th class="n">Aciertos</th></tr></thead><tbody>';
  H.porcomp.forEach(([c,n,h])=>{out+=`<tr><td>${NOM[c]||c}</td><td class="n">${n}</td><td class="n">${(100*h/n).toFixed(0)}%</td></tr>`});
  out+='</tbody></table>';}
 if(H.calib&&H.calib.length){
  out+='<div class="note" style="margin:0 0 6px"><b>Calibracion:</b> cuando el modelo dice un porcentaje, ¿cuantas veces ocurre?</div>';
  out+='<table style="margin-bottom:16px"><thead><tr><th>Dijo</th><th class="n">Casos</th><th class="n">Predicho</th><th class="n">Ocurrio</th></tr></thead><tbody>';
  H.calib.forEach(([lo,hi,n,p,o])=>{out+=`<tr><td>${lo}-${hi}%</td><td class="n">${n}</td><td class="n">${p.toFixed(1)}%</td><td class="n">${o.toFixed(1)}%</td></tr>`});
  out+='</tbody></table>';}
 out+='<div class="note" style="margin:0 0 4px"><b>Ultimos partidos</b></div>';
 const MESC=['ene','feb','mar','abr','may','jun','jul','ago','sep','oct','nov','dic'];
 H.filas.forEach(f=>{const dt=new Date(f.d+'T12:00:00');
  const mx=Math.max(...f.p),qi=f.p.indexOf(mx);
  const eti=[f.hn,'Empate',f.an][qi];
  out+=`<div class="hrow"><div class="fe">${dt.getDate()} ${MESC[dt.getMonth()]}</div>
   <div class="pt">${f.hn} vs ${f.an}<br><span style="color:#8a8983;font-size:11.5px">dijo ${eti} ${(mx*100).toFixed(0)}%</span></div>
   <div class="mk">${f.r[0]}-${f.r[1]}</div>
   <div class="ic ${f.ok?'ok':'no'}">${f.ok?'\u2713':'\u2715'}</div></div>`;});
 $('hist').innerHTML=out;
})();
</script></body></html>"""

def construir(datos):
    return (HTML.replace("__DATA__", json.dumps(datos, separators=(",", ":"), ensure_ascii=False))
                .replace("__NPART__", f"{datos['nPartidos']:,}".replace(",", "."))
                .replace("__FECHA__", datos["generado"]))
