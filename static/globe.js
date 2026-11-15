/* AETHERIS ORBITAL ATLAS — offline orthographic globe, not a climate data layer.
   Land points are sampled from bundled Natural Earth geometry. No API keys. */
(() => {
  'use strict';
  let dots=[];
  const deg=Math.PI/180;
  const state={lon:-23,lat:20,dragging:false,lastX:0,ready:false,lastFrame:0,visible:true,enabled:true};
  function initialize(){
    const canvas=document.getElementById('hero-globe-fallback');if(!canvas)return;
    const ctx=canvas.getContext('2d',{alpha:true});if(!ctx)return;
    const reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;
    fetch('/static/assets/land-dots.json').then(r=>{if(!r.ok)throw Error('geography unavailable');return r.json();}).then(d=>{dots=d;state.ready=true;draw();}).catch(()=>{state.ready=true;draw();});
    if(window.IntersectionObserver){const observer=new IntersectionObserver(items=>{state.visible=items.some(x=>x.isIntersecting);});observer.observe(canvas);}
    const proj=(lat,lon,cx,cy,r)=>{
      const phi=lat*deg,d=(lon-state.lon)*deg,phi0=state.lat*deg;
      const z=Math.sin(phi)*Math.sin(phi0)+Math.cos(phi)*Math.cos(phi0)*Math.cos(d);
      return {x:cx+r*Math.cos(phi)*Math.sin(d), y:cy-r*(Math.sin(phi)*Math.cos(phi0)-Math.cos(phi)*Math.sin(phi0)*Math.cos(d)),z};
    };
    function graticule(cx,cy,r,axis,value){
      ctx.beginPath();let segment=false;
      for(let i=0;i<=180;i++){
        const latitude=axis==='lon'?-89+i*178/180:value;
        const longitude=axis==='lon'?value:-180+i*360/180;
        const p=proj(latitude,longitude,cx,cy,r);
        if(p.z<0){segment=false;continue;}
        if(!segment){ctx.moveTo(p.x,p.y);segment=true;}else ctx.lineTo(p.x,p.y);
      }
      ctx.stroke();
    }
    function draw(){
      if(!state.ready)return;
      const dpr=Math.min(devicePixelRatio||1,1.5),size=460;
      if(canvas.width!==Math.round(size*dpr)||canvas.height!==Math.round(size*dpr)){
        canvas.width=Math.round(size*dpr);canvas.height=Math.round(size*dpr);
      }
      ctx.setTransform(dpr,0,0,dpr,0,0);ctx.clearRect(0,0,size,size);
      const cx=230,cy=228,r=160;
      // Atmospheric halo behind sphere.
      let atmosphere=ctx.createRadialGradient(cx,cy,r*.88,cx,cy,r*1.44);
      atmosphere.addColorStop(0,'rgba(245,199,58,.24)');atmosphere.addColorStop(.48,'rgba(226,170,26,.09)');atmosphere.addColorStop(1,'rgba(198,149,15,0)');
      ctx.fillStyle=atmosphere;ctx.beginPath();ctx.arc(cx,cy,r*1.44,0,Math.PI*2);ctx.fill();
      // Globe illumination and night terminator (illustrative map styling).
      const ocean=ctx.createRadialGradient(cx-r*.48,cy-r*.55,r*.1,cx+r*.3,cy+r*.1,r*1.7);
      ocean.addColorStop(0,'#526674');ocean.addColorStop(.31,'#344650');ocean.addColorStop(.62,'#20343f');ocean.addColorStop(1,'#101f28');
      ctx.beginPath();ctx.arc(cx,cy,r,0,Math.PI*2);ctx.fillStyle=ocean;ctx.fill();
      ctx.save();ctx.beginPath();ctx.arc(cx,cy,r,0,Math.PI*2);ctx.clip();
      ctx.lineWidth=.65;ctx.strokeStyle='rgba(255,220,110,.23)';
      for(let lat=-60;lat<=60;lat+=30)graticule(cx,cy,r,'lat',lat);
      for(let lon=-180;lon<180;lon+=30)graticule(cx,cy,r,'lon',lon);
      // Offline sampled geography: drawn as luminous survey points, not pixels of NASA data.
      ctx.fillStyle='rgba(255,212,67,.82)';
      for(let i=0;i<dots.length;i++){
        const q=dots[i],p=proj(q[1],q[0],cx,cy,r);if(p.z<=.03)continue;
        const opacity=.25+.7*p.z;
        ctx.globalAlpha=opacity;const w=1.05+p.z*.65;
        ctx.fillRect(p.x-w/2,p.y-w/2,w,w);
      }
      ctx.globalAlpha=1;
      // The geographic reference point shown in Explorer: Beni Mellal.
      const loc=proj(32.337,-6.349,cx,cy,r);
      if(loc.z>.05){
        const rad=ctx.createRadialGradient(loc.x,loc.y,0,loc.x,loc.y,17);
        rad.addColorStop(0,'rgba(255,238,150,.85)');rad.addColorStop(1,'rgba(255,208,52,0)');
        ctx.fillStyle=rad;ctx.beginPath();ctx.arc(loc.x,loc.y,17,0,Math.PI*2);ctx.fill();
        ctx.fillStyle='#fff8ca';ctx.beginPath();ctx.arc(loc.x,loc.y,2.9,0,Math.PI*2);ctx.fill();
        ctx.strokeStyle='rgba(255,236,136,.84)';ctx.lineWidth=.7;ctx.beginPath();ctx.arc(loc.x,loc.y,8,0,Math.PI*2);ctx.stroke();
      }
      let shadow=ctx.createLinearGradient(cx-r,cy-r,cx+r,cy+r);
      shadow.addColorStop(0,'rgba(255,241,189,.08)');shadow.addColorStop(.55,'rgba(0,0,0,0)');shadow.addColorStop(1,'rgba(0,0,0,.45)');
      ctx.fillStyle=shadow;ctx.fillRect(cx-r,cy-r,r*2,r*2);
      ctx.restore();
      ctx.beginPath();ctx.arc(cx,cy,r,0,Math.PI*2);
      ctx.strokeStyle='rgba(231,190,67,.55)';ctx.lineWidth=1.3;ctx.stroke();
    }
    function frame(now){
      if(!state.enabled)return;
      if(!state.dragging&&!reduced&&state.visible&&!document.hidden&&now-state.lastFrame>54){
        state.lon=(state.lon+.15+180)%360-180;state.lastFrame=now;draw();
      }
      requestAnimationFrame(frame);
    }
    canvas.addEventListener('pointerdown',e=>{state.dragging=true;state.lastX=e.clientX;canvas.setPointerCapture(e.pointerId);});
    canvas.addEventListener('pointermove',e=>{if(!state.dragging)return;state.lon-= (e.clientX-state.lastX)*.38;state.lastX=e.clientX;draw();});
    canvas.addEventListener('pointerup',()=>{state.dragging=false;});
    canvas.addEventListener('pointercancel',()=>{state.dragging=false;});
    requestAnimationFrame(frame);
  }
  window.AetherisLegacyGlobe={initialize,disable:()=>{state.enabled=false;}};
})();
