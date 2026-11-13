import * as THREE from '../node_modules/three/build/three.module.js';

(() => {
'use strict';
const $ = id => document.getElementById(id);
const SIZE = 56, HALF = (SIZE - 1) / 2, SAVE_KEY = 'cityforge-3d-save-v1';
const TOOLS = {
 road:{name:'Road',cost:12,group:'Infrastructure',color:0x424c58,upkeep:.2},
 res:{name:'Residential zone',cost:35,group:'Zones',color:0x54b978},
 com:{name:'Commercial zone',cost:40,group:'Zones',color:0x5798dc},
 ind:{name:'Industrial zone',cost:38,group:'Zones',color:0xd6a34b},
 power:{name:'Power station',cost:950,upkeep:16,range:15,group:'Utilities',color:0xd65b48},
 solar:{name:'Solar array',cost:650,upkeep:4,range:10,group:'Utilities',color:0x3e6eaa},
 water:{name:'Water tower',cost:520,upkeep:6,range:12,group:'Utilities',color:0x4baacb},
 park:{name:'Park',cost:100,upkeep:1,range:6,group:'Services',color:0x3b9d61},
 school:{name:'School',cost:480,upkeep:8,range:9,group:'Services',color:0xc49b50},
 clinic:{name:'Clinic',cost:520,upkeep:9,range:10,group:'Services',color:0xd9e2e8},
 police:{name:'Police station',cost:450,upkeep:8,range:10,group:'Services',color:0x5575c8},
 fire:{name:'Fire station',cost:470,upkeep:8,range:10,group:'Services',color:0xd75b43},
 hospital:{name:'Hospital',cost:1500,upkeep:22,range:16,group:'Services',color:0xe5e9ef},
 bulldoze:{name:'Bulldoze',cost:5,group:'Tools',color:0xb75c4e}
};
const scene = new THREE.Scene(); scene.background = new THREE.Color(0x9bb9c7); scene.fog = new THREE.Fog(0x9bb9c7,65,145);
const camera = new THREE.PerspectiveCamera(48, innerWidth/innerHeight,.1,350);
const renderer = new THREE.WebGLRenderer({antialias:true,powerPreference:'high-performance'});
renderer.setPixelRatio(Math.min(devicePixelRatio,2)); renderer.setSize(innerWidth,innerHeight); renderer.shadowMap.enabled=true; renderer.shadowMap.type=THREE.PCFSoftShadowMap;
renderer.outputColorSpace=THREE.SRGBColorSpace; renderer.toneMapping=THREE.ACESFilmicToneMapping; renderer.toneMappingExposure=1.15;
$('viewport').appendChild(renderer.domElement);
scene.add(new THREE.HemisphereLight(0xe7f5ff,0x65734d,2.0));
const sun=new THREE.DirectionalLight(0xffe3b5,2.6); sun.position.set(-42,75,35); sun.castShadow=true; sun.shadow.mapSize.set(2048,2048); sun.shadow.camera.left=-55;sun.shadow.camera.right=55;sun.shadow.camera.top=55;sun.shadow.camera.bottom=-55;scene.add(sun);
const ground=new THREE.Group();scene.add(ground); const city=new THREE.Group();scene.add(city); const decorations=new THREE.Group();scene.add(decorations); const overlays=new THREE.Group();scene.add(overlays);
const mat=(c,r=.85)=>new THREE.MeshStandardMaterial({color:c,roughness:r});
const materials={grass:mat(0x71965e),grass2:mat(0x789d65),water:mat(0x4d91b0,.55),road:mat(0x3d4651),line:mat(0xe6d18a),concrete:mat(0x999f9c),tree:mat(0x326c45),trunk:mat(0x684a31),glass:mat(0x8db9c7,.3)};
const raycaster=new THREE.Raycaster(), pointer=new THREE.Vector2();
let state, selected='road', hover=null, paused=false, speed=1, elapsed=0, last=performance.now(), orbit={yaw:.72,pitch:.78,distance:78,target:new THREE.Vector3(0,0,0)}, drag=null, layer='none', autoSave=0;
const tiles=[], tileMeshes=[], props=new Map(), cars=[];
const idx=(x,z)=>z*SIZE+x, tileAt=(x,z)=>x>=0&&z>=0&&x<SIZE&&z<SIZE?tiles[idx(x,z)]:null;
const heightAt=(x,z)=>{const n=Math.sin(x*.21)*.8+Math.cos(z*.17)*.75+Math.sin((x+z)*.11)*.65;return Math.max(-.35,n*.48);};
function fresh(seed=Math.floor(Math.random()*1e9)){let s=seed>>>0;const rand=()=>((s=(s*1664525+1013904223)>>>0)/4294967296);tiles.length=0;
 for(let z=0;z<SIZE;z++)for(let x=0;x<SIZE;x++){const h=heightAt(x-HALF,z-HALF), edge=Math.hypot(x-HALF,z-HALF);tiles.push({x,z,h,water:edge>23&&h<-.13,k:null,level:0,fire:0,tree:rand()<.105&&edge>8&&edge<25});}
 state={seed,money:24000,day:0,tax:9,pop:0,jobs:0,happy:55,income:0,expenses:0,rank:'Hamlet',demand:{res:65,com:35,ind:25},name:'New Horizon',disasters:true}; rebuildWorld(); orbit.target.set(0,0,0);updateCamera();refreshUI();toast('A new region is ready. Start with roads, then zone nearby land.');
}
function clearGroup(g){while(g.children.length){const o=g.children.pop();if(o.geometry)o.geometry.dispose();}}
function rebuildWorld(){clearGroup(ground);clearGroup(city);clearGroup(decorations);clearGroup(overlays);props.clear();tileMeshes.length=0;
 const geo=new THREE.BoxGeometry(.98,.18,.98);
 for(const t of tiles){const m=new THREE.Mesh(geo,t.water?materials.water:(t.x+t.z)%3===0?materials.grass2:materials.grass);m.position.set(t.x-HALF,t.h-.09,t.z-HALF);m.receiveShadow=true;m.userData.tile=t;ground.add(m);tileMeshes.push(m);
 if(t.tree&&!t.water){const g=new THREE.Group();const trunk=new THREE.Mesh(new THREE.CylinderGeometry(.09,.13,.8,6),materials.trunk);trunk.position.y=.35;trunk.castShadow=true;g.add(trunk);const crown=new THREE.Mesh(new THREE.ConeGeometry(.62,1.45,7),materials.tree);crown.position.y=1.28;crown.castShadow=true;g.add(crown);g.position.set(t.x-HALF,t.h,t.z-HALF);decorations.add(g);}
 }
 const sea=new THREE.Mesh(new THREE.PlaneGeometry(180,180),new THREE.MeshStandardMaterial({color:0x568da5,roughness:.4,metalness:.08}));sea.rotation.x=-Math.PI/2;sea.position.y=-.55;scene.add(sea);scene.userData.sea=sea;
 for(const t of tiles)if(t.k)buildObject(t);
 refreshCoverage();updateCamera();
}
function box(w,h,d,c,x,y,z,group=city){const m=new THREE.Mesh(new THREE.BoxGeometry(w,h,d),mat(c));m.position.set(x,y+h/2,z);m.castShadow=true;m.receiveShadow=true;group.add(m);return m;}
function buildObject(t){const x=t.x-HALF,z=t.z-HALF,y=t.h;const g=new THREE.Group();g.position.set(x,y,z);g.userData.tile=t;city.add(g);props.set(idx(t.x,t.z),g);
 const slab=new THREE.Mesh(new THREE.BoxGeometry(.96,.08,.96),mat(t.k==='road'?0x424b55:0x858d87));slab.position.y=.04;slab.receiveShadow=true;g.add(slab);
 if(t.k==='road'){const stripe=new THREE.Mesh(new THREE.BoxGeometry(.075,.012,.42),materials.line);stripe.position.y=.09;g.add(stripe);return;}
 if(['res','com','ind'].includes(t.k)){
  const level=Math.max(0,t.level), col= t.k==='res'?[0xd9bd99,0xc89e81,0xa9bbc7][Math.min(level,2)]:t.k==='com'?[0x6d9dc1,0x527fa7,0x426d98][Math.min(level,2)]:[0xb69a68,0xa98951,0x8f754d][Math.min(level,2)];
  const w=t.k==='res'?.58:.72, depth=t.k==='res'?.62:.72, h=level===0?.12:level===1?1.15:level===2?2.1:3.5;
  const body=new THREE.Mesh(new THREE.BoxGeometry(w,h,depth),mat(col));body.position.y=.12+h/2;body.castShadow=true;body.receiveShadow=true;g.add(body);
  if(level>0){const roof=new THREE.Mesh(new THREE.BoxGeometry(w+.05,.1,depth+.05),mat(t.k==='ind'?0x665e50:0x465969));roof.position.y=.12+h+.05;g.add(roof);
   const rows=Math.min(5,Math.floor(h/.45));for(let j=0;j<rows;j++)for(let side of [-1,1]){const win=new THREE.Mesh(new THREE.BoxGeometry(.045,.17,.018),materials.glass);win.position.set(side*(w/2+.011),.3+j*.42,depth/2+.012);g.add(win);}
  }
  if(t.k==='ind'&&level>0){const stack=new THREE.Mesh(new THREE.CylinderGeometry(.09,.12,.85,8),mat(0x777c7d));stack.position.set(.22,h+.55,0);stack.castShadow=true;g.add(stack);}
 }else{
  const serviceColors={power:0xd45e47,solar:0x3e6694,water:0x4baacb,park:0x3b9d61,school:0xc49b50,clinic:0xe0e5e9,police:0x5575c8,fire:0xd75b43,hospital:0xe5e9ef};
  if(t.k==='park'){for(const [a,b] of [[-.23,-.18],[.22,.16],[0,.3]]){const tr=new THREE.Mesh(new THREE.CylinderGeometry(.035,.06,.4,6),materials.trunk);tr.position.set(a,.28,b);g.add(tr);const cr=new THREE.Mesh(new THREE.SphereGeometry(.28,7,6),materials.tree);cr.position.set(a,.58,b);g.add(cr);}}
  else if(t.k==='solar'){for(let a=-1;a<=1;a++){const p=new THREE.Mesh(new THREE.BoxGeometry(.25,.05,.6),mat(0x397eb1));p.position.set(a*.28,.35,0);p.rotation.x=-.16;g.add(p);}}
  else if(t.k==='water'){const legs= new THREE.Mesh(new THREE.CylinderGeometry(.27,.27,.9,10),mat(0x6b8b9c));legs.position.y=.65;g.add(legs);const tank=new THREE.Mesh(new THREE.CylinderGeometry(.42,.42,.45,12),mat(serviceColors[t.k]));tank.position.y=1.3;g.add(tank);}
  else{const h=t.k==='hospital'?2.1:1.25;const b=new THREE.Mesh(new THREE.BoxGeometry(.72,h,.66),mat(serviceColors[t.k]));b.position.y=.12+h/2;b.castShadow=true;g.add(b);
   if(['clinic','hospital'].includes(t.k)){const cross=new THREE.Mesh(new THREE.BoxGeometry(.12,.65,.035),mat(0xc94e49));cross.position.set(0,h*.68,.35);g.add(cross);const c2=new THREE.Mesh(new THREE.BoxGeometry(.42,.13,.035),mat(0xc94e49));c2.position.set(0,h*.68,.35);g.add(c2);}
   if(t.k==='power'){const chimney=new THREE.Mesh(new THREE.CylinderGeometry(.1,.14,1.5,8),mat(0x68727b));chimney.position.set(.22,h+.65,0);g.add(chimney);}
  }
 }
}
function refreshCoverage(){const coverage={power:new Set(),water:new Set(),school:new Set(),clinic:new Set(),police:new Set(),fire:new Set(),park:new Set()};
 for(const t of tiles){if(!t.k)continue;const d=TOOLS[t.k];if(!d.range)continue;const type=t.k==='solar'?'power':t.k==='hospital'?'clinic':t.k;
  for(let z=Math.max(0,t.z-d.range);z<=Math.min(SIZE-1,t.z+d.range);z++)for(let x=Math.max(0,t.x-d.range);x<=Math.min(SIZE-1,t.x+d.range);x++)if(Math.hypot(x-t.x,z-t.z)<=d.range)coverage[type]?.add(idx(x,z));
 }state.coverage=coverage;updateLayer();}
function nearRoad(t){for(let z=Math.max(0,t.z-2);z<=Math.min(SIZE-1,t.z+2);z++)for(let x=Math.max(0,t.x-2);x<=Math.min(SIZE-1,t.x+2);x++){const a=tileAt(x,z);if(a?.k==='road')return true;}return false;}
function refreshWorldTile(t){const old=props.get(idx(t.x,t.z));if(old){city.remove(old);old.traverse(o=>{if(o.geometry)o.geometry.dispose();});props.delete(idx(t.x,t.z));}if(t.k)buildObject(t);refreshCoverage();}
function place(t){if(!t)return;const d=TOOLS[selected];if(!d)return;
 if(selected==='bulldoze'){if(!t.k&&!t.tree)return;if(state.money<d.cost)return toast('Insufficient funds.');state.money-=d.cost;t.k=null;t.level=0;t.fire=0;t.tree=false;refreshWorldTile(t);refreshUI();return;}
 if(t.water)return toast('This tile is water.');if(t.k)return toast('That tile is occupied.');if(state.money<d.cost)return toast('Insufficient funds.');
 t.k=selected;t.level=0;t.tree=false;state.money-=d.cost;refreshWorldTile(t);refreshUI();}
function simulate(){state.day++;refreshCoverage();let pop=0,jobs=0,weighted=0,homes=0,upkeep=0,roadCount=0;
 for(const t of tiles){if(!t.k)continue;const d=TOOLS[t.k];upkeep+=d.upkeep||0;if(t.k==='road'){upkeep+=.2;roadCount++;continue;}
 if(['res','com','ind'].includes(t.k)){const road=nearRoad(t),power=state.coverage.power.has(idx(t.x,t.z)),water=state.coverage.water.has(idx(t.x,t.z));
  if(t.level>0&&road&&power){if(t.k==='res'){const happiness=42+(state.coverage.school.has(idx(t.x,t.z))?8:0)+(state.coverage.clinic.has(idx(t.x,t.z))?10:0)+(state.coverage.park.has(idx(t.x,t.z))?10:0)+(state.coverage.police.has(idx(t.x,t.z))?7:0)+(state.coverage.fire.has(idx(t.x,t.z))?5:0)+(water?8:0)-state.tax*1.4;pop+=t.level*12;weighted+=Math.max(0,happiness)*t.level;homes+=t.level;}
   else jobs+=t.level*(t.k==='com'?8:10);}
  }
 }
 const happiness=homes?weighted/homes:55;const resDemand=Math.max(-100,Math.min(100,(jobs*.85+30-pop)/(jobs*.85+pop+30)*100+(happiness-50)*.6));const comDemand=Math.max(-100,Math.min(100,(pop*.9+20-jobs)/(pop*.9+jobs+20)*100));const indDemand=Math.max(-100,Math.min(100,(pop*.6+30-jobs)/(pop*.6+jobs+30)*100));
 state.pop=pop;state.jobs=jobs;state.happy=happiness;state.demand={res:resDemand,com:comDemand,ind:indDemand};
 for(const t of tiles){if(!['res','com','ind'].includes(t.k))continue;const powered=state.coverage.power.has(idx(t.x,t.z))&&nearRoad(t);if(powered&&t.level<3&&Math.random()<(.035+Math.max(0,state.demand[t.k])/1200)) {t.level++;refreshWorldTile(t);}else if(!powered&&t.level>0&&Math.random()<.025){t.level--;refreshWorldTile(t);}}
 state.income=pop*state.tax*.045+jobs*state.tax*.028;state.expenses=upkeep;state.money+=state.income-state.expenses;
 state.rank=pop>=10000?'Metropolis':pop>=3500?'Large city':pop>=1200?'City':pop>=400?'Town':pop>=100?'Village':'Hamlet';
 if(state.disasters&&state.day%19===0&&pop>80&&Math.random()<.35)disaster(false);
 if(state.money<0&&state.day%30===0)toast('Your treasury is in deficit. Review taxes and service upkeep.');
 if(state.day%30===0)save(true);refreshUI();}
function disaster(manual=true){const buildings=tiles.filter(t=>t.k&&!['road','park'].includes(t.k));if(!buildings.length)return toast('Build some structures first.');const t=buildings[Math.floor(Math.random()*buildings.length)];if(t.k==='res'||t.k==='com'||t.k==='ind'){if(state.coverage.fire.has(idx(t.x,t.z))){t.level=Math.max(0,t.level-1);toast('Fire crews contained an outbreak. One building level was damaged.');}else{t.fire=3;setTimeout(()=>{if(t.fire){t.k=null;t.level=0;t.fire=0;refreshWorldTile(t);toast('An unattended fire destroyed a building.');}},7000);toast('Fire! No station covers this location.');}}else{t.k=null;t.level=0;refreshWorldTile(t);toast('Severe storm damaged a city facility.');}if(manual)refreshUI();}
function save(silent=false){const data={...state,tiles:tiles.map(t=>({...t}))};localStorage.setItem(SAVE_KEY,JSON.stringify(data));if(!silent)toast('City saved locally.');}
function load(){try{const d=JSON.parse(localStorage.getItem(SAVE_KEY));if(!d?.tiles||d.tiles.length!==SIZE*SIZE)return false;state={...d};tiles.splice(0,tiles.length,...d.tiles);rebuildWorld();refreshUI();return true;}catch(e){return false;}}
function refreshUI(){$('cityName').value=state.name;$('rank').textContent=state.rank;$('money').textContent='$'+Math.round(state.money).toLocaleString();$('population').textContent=Math.round(state.pop).toLocaleString();$('jobs').textContent=Math.round(state.jobs).toLocaleString();$('happiness').textContent=Math.round(state.happy)+'%';$('date').textContent='Year '+(1+Math.floor(state.day/360))+' · '+['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][Math.floor(state.day%360/30)];$('income').textContent='$'+Math.round(state.income).toLocaleString();$('expenses').textContent='$'+Math.round(state.expenses).toLocaleString();$('net').textContent=(state.income>=state.expenses?'+':'−')+'$'+Math.round(Math.abs(state.income-state.expenses)).toLocaleString();$('tax').value=state.tax;$('taxValue').textContent=state.tax+'%';for(const k of ['res','com','ind']){$('d-'+k).style.width=((state.demand[k]+100)/2)+'%';$('v-'+k).textContent=Math.round(state.demand[k]);}}
function makeTools(){const root=$('tools');const groups=[...new Set(Object.values(TOOLS).map(t=>t.group))];for(const group of groups){const h=document.createElement('h4');h.textContent=group;root.append(h);for(const [id,d] of Object.entries(TOOLS).filter(([k,v])=>v.group===group)){const b=document.createElement('button');b.className='tool';b.dataset.tool=id;b.innerHTML='<i style="background:#'+d.color.toString(16).padStart(6,'0')+'"></i><span>'+d.name+'</span><b>'+(d.cost?'$'+d.cost:'')+'</b>';b.title=d.name+' — '+(d.cost?'$'+d.cost:'');b.onclick=()=>chooseTool(id);root.append(b);}}}
function chooseTool(id){selected=id;document.querySelectorAll('.tool').forEach(b=>b.classList.toggle('active',b.dataset.tool===id));$('selectedTool').textContent=TOOLS[id].name;}
function updateCamera(){const p=orbit.pitch,y=orbit.yaw,d=orbit.distance;camera.position.set(orbit.target.x+d*Math.sin(y)*Math.cos(p),orbit.target.y+d*Math.sin(p),orbit.target.z+d*Math.cos(y)*Math.cos(p));camera.lookAt(orbit.target);}
function toast(msg){const e=$('toast');e.textContent=msg;e.classList.add('show');clearTimeout(toast.timer);toast.timer=setTimeout(()=>e.classList.remove('show'),2800);}
function rayTile(ev){const r=renderer.domElement.getBoundingClientRect();pointer.set((ev.clientX-r.left)/r.width*2-1,-((ev.clientY-r.top)/r.height*2-1));raycaster.setFromCamera(pointer,camera);const hits=raycaster.intersectObjects(ground.children,false);return hits.length?hits[0].object.userData.tile:null;}
function updateHover(){if(!hoverMarker)return;hoverMarker.visible=!!hover;if(hover){hoverMarker.position.set(hover.x-HALF,hover.h+.07,hover.z-HALF);const ok=selected==='bulldoze'?!!hover.k||hover.tree:!hover.water&&!hover.k&&state.money>=TOOLS[selected].cost;hoverMarker.material.color.setHex(ok?0x40e0b0:0xf05d57);}}
const hoverMarker=new THREE.Mesh(new THREE.BoxGeometry(.97,.06,.97),new THREE.MeshBasicMaterial({color:0x40e0b0,transparent:true,opacity:.45,depthWrite:false}));hoverMarker.visible=false;scene.add(hoverMarker);
function updateLayer(){clearGroup(overlays);if(layer==='none'||!state?.coverage)return;const active=new Set();if(layer==='services'){for(const k of ['school','clinic','police','fire','park'])for(const i of state.coverage[k])active.add(i);}else if(state.coverage[layer]){for(const i of state.coverage[layer])active.add(i);}const color=layer==='power'?0x48d6a7:layer==='water'?0x4baadf:0xe5bb62;for(const i of active){const t=tiles[i];if(!t||t.water)continue;const m=new THREE.Mesh(new THREE.PlaneGeometry(.88,.88),new THREE.MeshBasicMaterial({color,transparent:true,opacity:.34,depthWrite:false,side:THREE.DoubleSide}));m.rotation.x=-Math.PI/2;m.position.set(t.x-HALF,t.h+.025,t.z-HALF);overlays.add(m);}}
function bind(){renderer.domElement.addEventListener('contextmenu',e=>e.preventDefault());renderer.domElement.addEventListener('pointerdown',e=>{renderer.domElement.setPointerCapture(e.pointerId);drag={x:e.clientX,y:e.clientY,button:e.button,moved:false};});
 renderer.domElement.addEventListener('pointermove',e=>{if(drag){const dx=e.clientX-drag.x,dy=e.clientY-drag.y;if(Math.abs(dx)+Math.abs(dy)>2)drag.moved=true;if(drag.button===2){orbit.yaw-=dx*.006;orbit.pitch=Math.max(.18,Math.min(1.35,orbit.pitch+dy*.004));updateCamera();}else if(drag.button===1){const right=new THREE.Vector3().setFromMatrixColumn(camera.matrix,0);const up=new THREE.Vector3().setFromMatrixColumn(camera.matrix,1);orbit.target.addScaledVector(right,-dx*.035);orbit.target.addScaledVector(up,dy*.035);updateCamera();}drag.x=e.clientX;drag.y=e.clientY;}
 hover=rayTile(e);updateHover();if(drag&&drag.button===0&&!drag.moved&&hover){} });
 renderer.domElement.addEventListener('pointerup',e=>{if(drag&&drag.button===0&&!drag.moved){const t=rayTile(e);if(t)place(t);}drag=null;});
 renderer.domElement.addEventListener('wheel',e=>{orbit.distance=Math.max(15,Math.min(125,orbit.distance*(e.deltaY>0?1.1:.9)));updateCamera();},{passive:true});
 addEventListener('keydown',e=>{if(['INPUT'].includes(e.target.tagName))return;const k=e.key.toLowerCase();const v=.9;if(k==='w'||k==='arrowup')orbit.target.z-=v;if(k==='s'||k==='arrowdown')orbit.target.z+=v;if(k==='a'||k==='arrowleft')orbit.target.x-=v;if(k==='d'||k==='arrowright')orbit.target.x+=v;if(k==='q')orbit.yaw-=.08;if(k==='e')orbit.yaw+=.08;if(k===' ')togglePause();if(k==='escape')chooseTool('road');updateCamera();});
 $('cityName').addEventListener('input',e=>state.name=e.target.value.slice(0,28));$('tax').addEventListener('input',e=>{state.tax=+e.target.value;$('taxValue').textContent=state.tax+'%';});
 $('save').onclick=()=>save();$('load').onclick=()=>toast(load()?'Saved city loaded.':'No saved city found.');$('new').onclick=()=>{if(confirm('Start a new city? Save first if you want to keep this one.'))fresh();};
 $('pause').onclick=togglePause;document.querySelectorAll('[data-speed]').forEach(b=>b.onclick=()=>{speed=+b.dataset.speed;paused=false;syncSpeed();});
 $('disasters').onchange=e=>state.disasters=e.target.checked;$('trigger').onclick=()=>disaster();
 $('layer').onchange=e=>{layer=e.target.value;updateLayer();toast(layer==='none'?'Map overlays hidden.':layer+' coverage overlay selected.');};
 $('help').onclick=()=> $('helpPanel').classList.toggle('visible');$('closeHelp').onclick=()=> $('helpPanel').classList.remove('visible');
}
function syncSpeed(){document.querySelectorAll('[data-speed]').forEach(b=>b.classList.toggle('active',+b.dataset.speed===speed));$('pause').textContent=paused?'Resume':'Pause';}
function togglePause(){paused=!paused;syncSpeed();}
function frame(now){const dt=Math.min(.05,(now-last)/1000);last=now;if(!paused){elapsed+=dt*speed;while(elapsed>=1.6){elapsed-=1.6;simulate();}}renderer.render(scene,camera);requestAnimationFrame(frame);}
function resize(){camera.aspect=innerWidth/innerHeight;camera.updateProjectionMatrix();renderer.setSize(innerWidth,innerHeight);}
makeTools();bind();addEventListener('resize',resize);camera.position.set(48,55,60);updateCamera();if(!load())fresh();else{rebuildWorld();refreshUI();}chooseTool('road');syncSpeed();requestAnimationFrame(frame);
})();