/**
 * AETHERIS x GhostCat 3d-earth: lightweight Three.js adaptation.
 * Inspired by / adapted from https://github.com/GhostCatcg/3d-earth (MIT, GhostCat 2022).
 * Globe texture and visual motifs are presentation assets, NOT NASA climate observations.
 * Original MIT notice: /static/vendor/ghostcat-earth/LICENSE
 */
(() => {
  'use strict';
  const BASE = '/static/vendor/ghostcat-earth/';
  const THREE_VERSION = '0.143.0';
  const reduced = () => window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const srcFallback = 'https://cdn.jsdelivr.net/npm/three@'+THREE_VERSION+'/build/three.min.js';
  const srcAlt = 'https://unpkg.com/three@'+THREE_VERSION+'/build/three.min.js';
  let started = false;
  let active = true;
  let globeGroup, renderer, scene, camera, earth, frame, observer;
  let stopped = false, isVisible = true, drag = false, previousX = 0, previousY = 0;
  let zoom = 312, orbitRings = [], satelliteGroups = [], pulses = [];
  let last = 0;
  const deg = Math.PI / 180;
  function loadScript(url) {
    return new Promise((resolve, reject) => {
      const script = document.createElement('script');
      script.src = url; script.defer = true;
      script.onload = () => window.THREE ? resolve(window.THREE) : reject(Error('Three.js unavailable'));
      script.onerror = () => { script.remove(); reject(Error('Three.js script unavailable')); };
      document.head.appendChild(script);
    });
  }
  async function ensureThree() {
    if (window.THREE) return window.THREE;
    for (const src of [BASE+'three.min.js', srcFallback, srcAlt]) {
      try { return await loadScript(src); } catch(_) { /* try next source */ }
    }
    throw Error('Unable to load Three.js');
  }
  function geolocate(lat, lon, r) {
    // Three.js equirectangular sphere UV convention: lon=0 faces z-negative.
    return new THREE.Vector3(
      r*Math.cos(lat*deg)*Math.sin(lon*deg),
      r*Math.sin(lat*deg),
      -r*Math.cos(lat*deg)*Math.cos(lon*deg)
    );
  }
  function atmosphereTexture() {
    const c=document.createElement('canvas'); c.width=c.height=256;
    const x=c.getContext('2d'); const g=x.createRadialGradient(128,128,54,128,128,126);
    g.addColorStop(0,'rgba(255,234,134,0.08)');
    g.addColorStop(.6,'rgba(255,207,62,0.24)');
    g.addColorStop(1,'rgba(255,204,44,0)');
    x.fillStyle=g;x.fillRect(0,0,256,256);
    return new THREE.CanvasTexture(c);
  }
  function addStars() {
    const pts=[];
    // Restrained stars rather than a dark full-screen effect, keeping white/yellow design.
    for(let i=0;i<170;i++) {
      const a=i*2.39996323, z=1-2*(i+.5)/170, t=Math.sqrt(1-z*z);
      const r=180+(i%7)*11;
      pts.push(r*t*Math.cos(a), r*z, r*t*Math.sin(a));
    }
    const geo=new THREE.BufferGeometry();geo.setAttribute('position',new THREE.Float32BufferAttribute(pts,3));
    const points=new THREE.Points(geo,new THREE.PointsMaterial({size:1.15,color:0xd2a52b,transparent:true,opacity:.43,depthWrite:false}));
    scene.add(points);
  }
  function addGlow() {
    const s=new THREE.Sprite(new THREE.SpriteMaterial({map:atmosphereTexture(),color:0xf6c54c,transparent:true,depthWrite:false,opacity:.58}));
    s.scale.set(220,220,1);s.position.z=-5;scene.add(s);
    // Original 3d-earth has a shader-driven atmospheric edge.
    const geo=new THREE.SphereGeometry(77.4,48,32);
    const mat=new THREE.ShaderMaterial({
      uniforms:{glowColor:{value:new THREE.Color(0xeebd35)}, strength:{value:.28}},
      vertexShader:'varying vec3 vNormal;varying vec3 vView;void main(){vec4 mv=modelViewMatrix*vec4(position,1.);vNormal=normalize(normalMatrix*normal);vView=normalize(-mv.xyz);gl_Position=projectionMatrix*mv;}',
      fragmentShader:'uniform vec3 glowColor;uniform float strength;varying vec3 vNormal;varying vec3 vView;void main(){float a=pow(1.-abs(dot(normalize(vNormal),normalize(vView))),3.);gl_FragColor=vec4(glowColor,a*strength);}',
      side:THREE.FrontSide,transparent:true,depthWrite:false,blending:THREE.AdditiveBlending
    });
    globeGroup.add(new THREE.Mesh(geo,mat));
  }
  function addSatellites() {
    // Three concentric orbital paths + moving satellites from GhostCat's createAnimateCircle idea.
    const configs=[{radius:84,axis:0.30,color:0xe4bd46,speed:.0015},
                   {radius:92,axis:-.50,color:0xc5a44a,speed:-.0011},
                   {radius:100,axis:.83,color:0xaab9b3,speed:.0008}];
    configs.forEach((cfg,k)=>{
      const group=new THREE.Group();group.rotation.x=cfg.axis;
      const path=new THREE.EllipseCurve(0,0,cfg.radius,cfg.radius,0,Math.PI*2,false,0);
      const points=path.getPoints(160).map(p=>new THREE.Vector3(p.x,0,p.y));
      const lineGeo=new THREE.BufferGeometry().setFromPoints(points);
      const line=new THREE.LineLoop(lineGeo,new THREE.LineBasicMaterial({color:cfg.color,transparent:true,opacity:.30,depthWrite:false}));
      group.add(line);
      for(let n=0;n<(k===0?2:1);n++) {
        const sat=new THREE.Mesh(new THREE.SphereGeometry(1.75,12,8),new THREE.MeshBasicMaterial({color:k===2?0x8b9ca1:0xe8bf53}));
        sat.userData={phase:n*Math.PI, speed:cfg.speed, radius:cfg.radius};
        group.add(sat);satelliteGroups.push(sat);
      }
      scene.add(group);orbitRings.push(group);
    });
  }
  function addLocation(lat,lon,color=0xffd55e) {
    const p=geolocate(lat,lon,77.2);
    const node=new THREE.Mesh(new THREE.SphereGeometry(1.7,12,9),new THREE.MeshBasicMaterial({color}));
    node.position.copy(p);globeGroup.add(node);
    const ring=new THREE.Mesh(new THREE.RingGeometry(3.2,3.7,30),new THREE.MeshBasicMaterial({color:0xf7d462,transparent:true,opacity:.65,side:THREE.DoubleSide,depthWrite:false}));
    ring.position.copy(p.clone().multiplyScalar(1.006));ring.quaternion.setFromUnitVectors(new THREE.Vector3(0,0,1),p.clone().normalize());
    globeGroup.add(ring);pulses.push(ring);
  }
  function addRoutes() {
    const start=geolocate(32.337,-6.349,78);
    // Deliberately symbolic data routes, not actual satellite measurements.
    [[33.573,-7.589],[31.63,-8.008],[34.064,-6.77]].forEach(([lat,lon],i)=>{
      const end=geolocate(lat,lon,78),mid=start.clone().add(end).multiplyScalar(.5).normalize().multiplyScalar(87+i*2);
      const curve=new THREE.QuadraticBezierCurve3(start,mid,end);
      const line=new THREE.Line(new THREE.BufferGeometry().setFromPoints(curve.getPoints(32)),new THREE.LineBasicMaterial({color:0xf7c858,opacity:.6,transparent:true,depthWrite:false}));
      globeGroup.add(line);
    });
  }
  function initRenderer(THREE) {
    const container=document.getElementById('hero-globe');
    if(!container) return false;
    let test;
    try {
      test=document.createElement('canvas');
      if(!test.getContext('webgl')&&!test.getContext('experimental-webgl')) throw Error('WebGL not supported');
      renderer=new THREE.WebGLRenderer({alpha:true,antialias:true,powerPreference:'low-power'});
    } catch(err) { throw Error('WebGL unavailable: '+err.message); }
    renderer.setPixelRatio(Math.min(window.devicePixelRatio||1,1.5));
    renderer.setClearColor(0x000000,0);
    renderer.outputEncoding=THREE.sRGBEncoding;
    renderer.domElement.className='ghostcat-canvas';
    renderer.domElement.setAttribute('aria-hidden','true');
    container.appendChild(renderer.domElement);
    scene=new THREE.Scene();camera=new THREE.PerspectiveCamera(35,1,.1,1000);
    camera.position.set(0,12,zoom);
    scene.add(new THREE.AmbientLight(0xffffff,.78));
    const key=new THREE.DirectionalLight(0xffffff,1.08);key.position.set(-70,70,125);scene.add(key);
    const fill=new THREE.DirectionalLight(0xffc865,.35);fill.position.set(80,-20,-70);scene.add(fill);
    globeGroup=new THREE.Group();
    globeGroup.rotation.y=Math.PI-.4;globeGroup.rotation.x=-.23;
    scene.add(globeGroup);
    const globeGeo=new THREE.SphereGeometry(76,72,56);
    const mat=new THREE.MeshPhongMaterial({color:0xffffff,shininess:11,specular:0x8a9d91});
    earth=new THREE.Mesh(globeGeo,mat);globeGroup.add(earth);
    // Texture is taken directly from GhostCat/3d-earth if installed; fallback is a bundled
    // cartographic drawing generated from Natural Earth geometry, never scientific NASA data.
    const loader=new THREE.TextureLoader();
    function textureOK(texture){
      texture.encoding=THREE.sRGBEncoding;
      texture.anisotropy=Math.min(4,renderer.capabilities.getMaxAnisotropy());
      mat.map=texture;mat.needsUpdate=true;
    }
    loader.load(BASE+'earth.jpg',textureOK,undefined,()=>{
      loader.load(BASE+'earth-fallback.jpg',textureOK,undefined,()=>{});
    });
    addGlow();addStars();addSatellites();addLocation(32.337,-6.349);
    addRoutes();
    const resize=()=>{
      if(!container.isConnected)return;
      const width=Math.max(1,container.clientWidth),height=Math.max(1,container.clientHeight);
      renderer.setSize(width,height,false);
      camera.aspect=width/height;camera.updateProjectionMatrix();
      renderer.render(scene,camera);
    };
    if(typeof ResizeObserver!=='undefined') {const ro=new ResizeObserver(resize);ro.observe(container);}
    else window.addEventListener('resize',resize,{passive:true});
    resize();
    // Show the WebGL globe only after a valid first frame; the old offline 2D globe remains
    // an independent fallback for machines where Three.js or WebGL cannot initialize.
    const fallback=document.getElementById('hero-globe-fallback');if(fallback) fallback.hidden=true;
    if(window.AetherisLegacyGlobe?.disable)window.AetherisLegacyGlobe.disable();
    container.classList.add('webgl-ready');
    const orbitControl=(dx,dy)=>{globeGroup.rotation.y+=dx*.006;globeGroup.rotation.x=Math.max(-1.15,Math.min(1.15,globeGroup.rotation.x+dy*.005));};
    renderer.domElement.addEventListener('pointerdown',e=>{drag=true;previousX=e.clientX;previousY=e.clientY;renderer.domElement.setPointerCapture(e.pointerId);});
    renderer.domElement.addEventListener('pointermove',e=>{if(!drag)return;orbitControl(e.clientX-previousX,e.clientY-previousY);previousX=e.clientX;previousY=e.clientY;});
    const finish=()=>{drag=false;};renderer.domElement.addEventListener('pointerup',finish);renderer.domElement.addEventListener('pointercancel',finish);
    renderer.domElement.addEventListener('wheel',e=>{e.preventDefault();zoom=Math.max(280,Math.min(420,zoom+e.deltaY*.16));},{passive:false});
    container.addEventListener('keydown',e=>{
      if(['ArrowLeft','ArrowRight','ArrowUp','ArrowDown'].includes(e.key)) {
        e.preventDefault();orbitControl(e.key==='ArrowLeft'?25:e.key==='ArrowRight'?-25:0,e.key==='ArrowUp'?20:e.key==='ArrowDown'?-20:0);
      }
    });
    if('IntersectionObserver'in window){observer=new IntersectionObserver(entries=>{isVisible=entries.some(e=>e.isIntersecting);});observer.observe(container);}
    document.addEventListener('visibilitychange',()=>{if(!document.hidden){last=0;}});
    let phase=0;
    function draw(t){
      if(stopped)return;
      frame=requestAnimationFrame(draw);
      if(document.hidden||!isVisible)return;
      if(last&&t-last<30)return;
      const dt=last?Math.min(60,t-last):16;last=t;
      if(active&&!reduced()){
        if(!drag)globeGroup.rotation.y+=.00020*dt;
        phase+=dt*.001;
        satelliteGroups.forEach((sat,i)=>{
          const angle=phase*(i%2?-.8:1.1)+sat.userData.phase;
          sat.position.set(Math.cos(angle)*sat.userData.radius,0,Math.sin(angle)*sat.userData.radius);
        });
        pulses.forEach((ring,i)=>{let s=1+.19*Math.sin(phase*1.6+i);ring.scale.setScalar(s);});
      }
      camera.position.z+=(zoom-camera.position.z)*.12;
      renderer.render(scene,camera);
    }
    frame=requestAnimationFrame(draw);
    window.addEventListener('pagehide',()=>{stopped=true;cancelAnimationFrame(frame);observer?.disconnect();renderer.dispose();},{once:true});
    const toggle=document.getElementById('globe-motion-toggle');
    if(toggle){toggle.hidden=false; toggle.textContent=active?'Pause rotation':'Resume rotation';toggle.addEventListener('click',()=>{active=!active;toggle.textContent=active?'Pause rotation':'Resume rotation';});}
    const reset=document.getElementById('globe-reset');
    if(reset){reset.hidden=false;reset.addEventListener('click',()=>{globeGroup.rotation.set(-.23,Math.PI-.4,0);zoom=312;});}
    return true;
  }
  async function initialize(){
    if(started)return;started=true;
    const container=document.getElementById('hero-globe');if(!container)return;
    if(window.AetherisLegacyGlobe)window.AetherisLegacyGlobe.initialize();
    try {
      await ensureThree();
      initRenderer(window.THREE);
      document.documentElement.dataset.globeEngine='ghostcat-webgl';
    } catch(error) {
      // Fully functional existing offline cartographic globe remains available.
      document.documentElement.dataset.globeEngine='offline-fallback';
      console.info('AETHERIS: using offline globe fallback:',error.message);
      // The 2D fallback was already initialized before WebGL loading.
    }
  }
  window.AetherisGlobe={initialize};
})();
