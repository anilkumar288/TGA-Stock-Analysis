(() => {
  const canvas = document.getElementById('priceChart');
  const data = window.chartData;
  if (!canvas || !data) return;
  const tip = document.getElementById('chartTip');
  let points = [];

  function draw() {
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr; canvas.height = rect.height * dpr;
    const ctx = canvas.getContext('2d'); ctx.scale(dpr, dpr);
    const w = rect.width, h = rect.height, pad = {l:58,r:12,t:10,b:31};
    const all = [data.close,data.sma20,data.sma50,data.sma200].flat().filter(Number.isFinite);
    let min = Math.min(...all), max = Math.max(...all); const buffer = (max-min)*.06; min-=buffer; max+=buffer;
    const x = i => pad.l + i*(w-pad.l-pad.r)/(data.dates.length-1);
    const y = v => pad.t + (max-v)*(h-pad.t-pad.b)/(max-min);
    ctx.font='10px DM Mono'; ctx.fillStyle='#77807b'; ctx.strokeStyle='#dedcd2'; ctx.lineWidth=1;
    for(let i=0;i<5;i++){const yy=pad.t+i*(h-pad.t-pad.b)/4;ctx.beginPath();ctx.moveTo(pad.l,yy);ctx.lineTo(w-pad.r,yy);ctx.stroke();const val=max-i*(max-min)/4;ctx.fillText('$'+val.toFixed(0),4,yy+3)}
    const series=[[data.sma200,'#9c5d80',1],[data.sma50,'#c38928',1.2],[data.sma20,'#1b8b6a',1.2],[data.close,'#17221d',2.2]];
    series.forEach(([vals,color,width])=>{ctx.strokeStyle=color;ctx.lineWidth=width;ctx.beginPath();let active=false;vals.forEach((v,i)=>{if(v==null){active=false;return}active?ctx.lineTo(x(i),y(v)):ctx.moveTo(x(i),y(v));active=true});ctx.stroke()});
    points=data.close.map((v,i)=>({x:x(i),y:y(v),value:v,date:data.dates[i]}));
    const ticks=4;ctx.fillStyle='#77807b';for(let i=0;i<=ticks;i++){const idx=Math.round(i*(data.dates.length-1)/ticks);ctx.fillText(data.dates[idx].slice(0,7),Math.min(x(idx),w-48),h-7)}
  }
  canvas.addEventListener('mousemove', e=>{if(!points.length)return;const r=canvas.getBoundingClientRect();const mx=e.clientX-r.left;const p=points.reduce((a,b)=>Math.abs(b.x-mx)<Math.abs(a.x-mx)?b:a);tip.hidden=false;tip.textContent=`${p.date}  $${p.value.toFixed(2)}`;tip.style.left=Math.min(p.x+20,r.width-145)+'px';tip.style.top=Math.max(p.y,70)+'px'});
  canvas.addEventListener('mouseleave',()=>tip.hidden=true);
  new ResizeObserver(draw).observe(canvas); draw();
})();
