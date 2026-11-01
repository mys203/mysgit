import { sealVisualTrack } from "@hypit/composition";
import type { VisualElement } from "@hypit/composition";
import { htmlVisual } from "@hypit/html-program";
import type { FontStackRef } from "@hypit/media";
import type { Timeline } from "@hypit/timeline";
import type { SpatialFrame } from "@hypit/spatial";
import { assertTemporalWindowFor } from "@hypit/temporal";
import type { TemporalWindow } from "@hypit/temporal";
import { ACCENT_FRAMES } from "./beats.js";
import { AUTHORED_SECONDS, LINES, STATEMENTS } from "./content.js";

export type SceneOptions = { readonly id: string; readonly title: string; readonly tag: string };

const FPS = 30;

/** A one-off scene for 《痛苦和坚持》: every frame is computed from the requested frame alone. */
export function renderScene(timeline: Timeline, within: SpatialFrame, window: TemporalWindow,
  font: FontStackRef, options: SceneOptions) {
  assertTemporalWindowFor(window, { subjectId: options.id, timeline: timeline });
  const start = window.span.startFrame;
  const length = window.span.endFrameExclusive - start;
  if (length <= 0) throw new Error("Pain and persistence scene needs a non-empty window.");

  const programId = options.id + "-program";
  let order = 0;
  const elements: VisualElement[] = [];

  const base = (id: string, extra: { name: string; value: string | number }[]) => {
    elements.push({
      id: id, kind: "text", parent: programId, order: ++order, text: "",
      fonts: font.faces,
      style: [
        { name: "position", value: "absolute" },
        { name: "margin", value: "0px" },
        ...extra,
      ],
    } as VisualElement);
  };

  const label = (id: string, text: string, extra: { name: string; value: string | number }[]) => {
    base(id, extra);
    const last = elements[elements.length - 1] as { text: string };
    last.text = text;
  };

  for (const statement of STATEMENTS) {
    label(statement.id, statement.text, [
      { name: "left", value: "0px" }, { name: "top", value: "132px" },
      { name: "width", value: "1920px" }, { name: "text-align", value: "center" },
      { name: "font-size", value: "104px" },
      { name: "line-height", value: 1.1 }, { name: "letter-spacing", value: "0px" },
      { name: "color", value: "#EDEAE3" },
    ]);
  }
  for (const line of LINES) {
    label(line.id, line.text, [
      { name: "left", value: "140px" }, { name: "top", value: "906px" },
      { name: "width", value: "1640px" }, { name: "text-align", value: "center" },
      { name: "font-size", value: "42px" },
      { name: "line-height", value: 1.35 }, { name: "color", value: "#EDEAE3" },
    ]);
  }
  label("label", options.title, [
    { name: "left", value: "96px" }, { name: "top", value: "52px" }, { name: "width", value: "900px" },
    { name: "text-align", value: "left" }, { name: "font-size", value: "26px" },
    { name: "letter-spacing", value: "4px" },
    { name: "color", value: "#C9A96A" },
  ]);
  label("tag", options.tag, [
    { name: "left", value: "924px" }, { name: "top", value: "52px" }, { name: "width", value: "900px" },
    { name: "text-align", value: "right" }, { name: "font-size", value: "24px" },
    { name: "letter-spacing", value: "2px" },
    { name: "color", value: "#79809B" },
  ]);
  label("loopA", "预期", [
    { name: "left", value: "210px" }, { name: "top", value: "356px" }, { name: "width", value: "240px" },
    { name: "text-align", value: "left" }, { name: "font-size", value: "30px" },
    { name: "color", value: "#C9A96A" },
  ]);
  label("loopB", "真实", [
    { name: "left", value: "210px" }, { name: "top", value: "700px" }, { name: "width", value: "240px" },
    { name: "text-align", value: "left" }, { name: "font-size", value: "30px" },
    { name: "color", value: "#D9777F" },
  ]);

  const timeScale = (length / FPS) / AUTHORED_SECONDS;
  const local = (seconds: number) => Math.round(seconds * timeScale * FPS) - start;
  const schedule = (items: readonly { id: string; start: number; end: number }[]) =>
    items.map((item) => ({ s: local(item.start), e: local(item.end) }));

  const data = {
    start: start,
    length: length,
    scale: timeScale,
    seconds: length / FPS,
    accents: ACCENT_FRAMES.filter((f) => f >= start && f < start + length).map((f) => f - start),
    statements: schedule(STATEMENTS),
    lines: schedule(LINES),
    loops: { s: local(31), e: local(76) },
    labelFade: local(94),
  };

  const html = [
    '<div class="stage">',
    '<canvas class="paint" width="1920" height="1080"></canvas>',
    '<div class="layer">',
    STATEMENTS.map((s, i) => '<div data-big="' + i + '">{{' + s.id + '}}</div>').join(""),
    LINES.map((l, i) => '<div data-line="' + i + '">{{' + l.id + '}}</div>').join(""),
    '<div data-fixed="label">{{label}}</div>',
    '<div data-fixed="tag">{{tag}}</div>',
    '<div data-fixed="loopA">{{loopA}}</div>',
    '<div data-fixed="loopB">{{loopB}}</div>',
    "</div>",
    "</div>",
  ].join("");

  const css = [
    ":scope{background:#0A0A1E;overflow:hidden}",
    ".stage{position:absolute;inset:0}",
    ".paint{position:absolute;left:0;top:0;width:1920px;height:1080px;z-index:0}",
    ".layer{position:absolute;inset:0;z-index:5}",
    ".layer>div{text-shadow:0 0 26px rgba(10,10,30,.85);opacity:0}",
    ".layer>[data-big]{font-weight:700}",
    ".layer>[data-line]{font-weight:400}",
    ".layer>[data-fixed=label]{font-weight:600}",
    ".layer>[data-fixed=tag]{font-weight:400}",
    ".layer>[data-fixed=loopA]{font-weight:400}",
    ".layer>[data-fixed=loopB]{font-weight:600}",
  ].join("");

  const setup = `
const cv = root.querySelector('.paint');
const g = cv.getContext('2d');
const W = 1920, H = 1080;
const INK = '#EDEAE3', DIM = '#79809B', GOLD = '#C9A96A', TEAL = '#6FD3C7', VIO = '#6B5BD2', COOL = '#8E9AD0';

function mk(a){return function(){a|=0;a=a+0x6D2B79F5|0;var t=Math.imul(a^a>>>15,1|a);t=t+Math.imul(t^t>>>7,61|t)^t;return ((t^t>>>14)>>>0)/4294967296;};}
const rnd = mk(20261011);
const parts = [];
for (let i=0;i<96;i++){parts.push({x:rnd()*W,y:rnd()*H,r:0.6+rnd()*1.9,s:5+rnd()*20,a:0.05+rnd()*0.10});}
const stars = [];
for (let i=0;i<150;i++){stars.push({x:rnd()*W,y:rnd()*H*0.72,r:0.4+rnd()*1.25,tw:0.5+rnd()*1.6,ph:rnd()*6.283,a:0.10+rnd()*0.50});}
const fog = [];
for (let i=0;i<6;i++){fog.push({x:120+rnd()*(W-240),y:150+rnd()*(H-260),r:300+rnd()*420,a:0.024+rnd()*0.034,hue:i%3});}
const bokeh = [];
for (let i=0;i<28;i++){bokeh.push({x:rnd()*W,y:rnd()*H,r:22+rnd()*56,s:2+rnd()*7,a:0.022+rnd()*0.045,ph:rnd()*6.283});}

const bigEls = Array.prototype.slice.call(root.querySelectorAll('[data-big]'));
const lineEls = Array.prototype.slice.call(root.querySelectorAll('[data-line]'));
const fixedEls = {};
Array.prototype.slice.call(root.querySelectorAll('[data-fixed]')).forEach(function(el){fixedEls[el.getAttribute('data-fixed')] = el;});

function cl(v,a,b){return v<a?a:(v>b?b:v);}
function eo(p){p=cl(p,0,1);return 1-Math.pow(1-p,3);}
function eio(p){p=cl(p,0,1);return p<0.5?4*p*p*p:1-Math.pow(-2*p+2,3)/2;}
function sg(v,a,b){return cl((v-a)/(b-a),0,1);}
function lerp(a,b,p){return a+(b-a)*p;}

const LEN = data.length;
const PULSE = new Float64Array(LEN);
for (let i=0;i<data.accents.length;i++){
  const a = data.accents[i];
  for (let d=0; d<15; d++){ const f=a+d; if(f>=0&&f<LEN){ const v=1-d/15; if(v>PULSE[f])PULSE[f]=v; } }
}
function pulse(f){return f>=0&&f<LEN?PULSE[f]:0;}

function bar(f){ // slower pulse on every fourth accent
  let v=0;
  for (let i=0;i<data.accents.length;i+=4){ const d=f-data.accents[i]; if(d>=0&&d<26) v=Math.max(v,1-d/26); }
  return v;
}

// ---------- shared drawing ----------
function disc(x,y,r,color,alpha){
  if(alpha<=0.004||r<=0) return;
  g.save(); g.globalAlpha=alpha; g.fillStyle=color;
  g.beginPath(); g.arc(x,y,r,0,6.283); g.fill(); g.restore();
}
function line(x1,y1,x2,y2,color,alpha,width){
  if(alpha<=0.004) return;
  g.save(); g.globalAlpha=alpha; g.strokeStyle=color; g.lineWidth=width;
  g.beginPath(); g.moveTo(x1,y1); g.lineTo(x2,y2); g.stroke(); g.restore();
}
function rrect(x,y,w,h,r,color,alpha){
  if(alpha<=0.004||w<=0||h<=0) return;
  g.save(); g.globalAlpha=alpha; g.fillStyle=color;
  g.beginPath(); g.roundRect(x,y,w,h,r); g.fill(); g.restore();
}
function rrectStroke(x,y,w,h,r,color,alpha,width){
  if(alpha<=0.004) return;
  g.save(); g.globalAlpha=alpha; g.strokeStyle=color; g.lineWidth=width;
  g.beginPath(); g.roundRect(x,y,w,h,r); g.stroke(); g.restore();
}

function background(f,t){
  g.setTransform(1,0,0,1,0,0);
  const p = pulse(f);

  // base with a very slight vertical grade
  const base = g.createLinearGradient(0,0,0,H);
  base.addColorStop(0,'#070713');
  base.addColorStop(0.5,'#0A0A1E');
  base.addColorStop(1,'#080916');
  g.fillStyle=base; g.fillRect(0,0,W,H);

  // far: stars
  for (let i=0;i<stars.length;i++){
    const s = stars[i];
    const tw = 0.55 + 0.45*Math.sin(f*0.04*s.tw + s.ph);
    disc(s.x, s.y, s.r, '#E8ECFF', s.a*tw);
    if (s.a > 0.45) disc(s.x, s.y, s.r*2.6, '#B9C4FF', s.a*0.08*tw);
  }

  // mid: drifting fog
  for (let i=0;i<fog.length;i++){
    const q = fog[i];
    const x = ((q.x + Math.sin(f*0.05 + i*1.7)*18) % W + W) % W;
    const y = ((q.y + Math.cos(f*0.04 + i)*14) % H + H) % H;
    const col = q.hue===0 ? '107,91,210' : (q.hue===1 ? '111,211,199' : '142,154,208');
    const gr = g.createRadialGradient(x,y,0,x,y,q.r);
    gr.addColorStop(0,'rgba('+col+','+(q.a+p*0.018)+')');
    gr.addColorStop(1,'rgba('+col+',0)');
    g.fillStyle=gr; g.fillRect(0,0,W,H);
  }

  // near: large soft depth dots
  for (let i=0;i<bokeh.length;i++){
    const q = bokeh[i];
    const span = H + q.r*2;
    const y = (((q.y - f*q.s*0.16) % span) + span) % span - q.r;
    const a = q.a*(0.55+0.45*Math.sin(f*0.02+q.ph));
    const gr = g.createRadialGradient(q.x,y,0,q.x,y,q.r);
    gr.addColorStop(0,'rgba(159,176,224,'+a+')');
    gr.addColorStop(1,'rgba(159,176,224,0)');
    g.fillStyle=gr; g.fillRect(q.x-q.r,y-q.r,q.r*2,q.r*2);
  }

  g.save();
  g.globalAlpha = 0.030 + 0.020*p;
  g.strokeStyle = '#5A6690'; g.lineWidth = 1;
  const ox = (f*0.5)%128, oy = (f*0.22)%128;
  g.beginPath();
  for (let x=-ox; x<W+128; x+=128){ g.moveTo(x,0); g.lineTo(x,H); }
  for (let y=-oy; y<H+128; y+=128){ g.moveTo(0,y); g.lineTo(W,y); }
  g.stroke();
  g.restore();

  // near: small drifting particles
  for (let i=0;i<parts.length;i++){
    const q = parts[i];
    const y = ((q.y - f*q.s*0.25) % H + H) % H;
    disc(q.x, y, q.r*(1+0.8*p), COOL, q.a*(0.6+0.4*Math.sin(f*0.03+i))*(1+0.5*p));
  }

  // complementary glows: cool upper-left, warm lower-right
  const coolGlow = g.createRadialGradient(W*0.16,H*0.18,0,W*0.16,H*0.18,560);
  coolGlow.addColorStop(0,'rgba(111,211,199,0.035)');
  coolGlow.addColorStop(1,'rgba(111,211,199,0)');
  g.fillStyle=coolGlow; g.fillRect(0,0,W,H);

  const grad = g.createRadialGradient(W*0.5,H*0.60,60,W*0.5,H*0.60,940);
  grad.addColorStop(0,'rgba(107,91,210,'+(0.045+0.10*p)+')');
  grad.addColorStop(1,'rgba(0,0,0,0)');
  g.fillStyle=grad; g.fillRect(0,0,W,H);

  const warmGlow = g.createRadialGradient(W*0.88,H*0.72,0,W*0.88,H*0.72,620);
  warmGlow.addColorStop(0,'rgba(201,169,106,0.030)');
  warmGlow.addColorStop(1,'rgba(201,169,106,0)');
  g.fillStyle=warmGlow; g.fillRect(0,0,W,H);

  const vg = g.createRadialGradient(W/2,H/2,270,W/2,H/2,1200);
  vg.addColorStop(0,'rgba(0,0,0,0)'); vg.addColorStop(1,'rgba(0,0,0,0.74)');
  g.fillStyle=vg; g.fillRect(0,0,W,H);
}

// ---------- the two curves: expectation vs real ----------
const HURT = '#D9777F';
const CURVE_X0 = 540, CURVE_X1 = 1080, CURVE_Y = 760, REAL_AMP = 200;

function noiseAt(x){
  return Math.sin(x*2.4)*0.42 + Math.sin(x*6.8+1.7)*0.22 + Math.sin(x*13.1+3.9)*0.10;
}

function curvePoints(amp, steps){
  const N = 120, pts = [];
  for (let i=0;i<=N;i++){
    const prog = i/N;
    const x = CURVE_X0 + (CURVE_X1-CURVE_X0)*prog;
    let y;
    if (steps>0){
      const k = Math.min(steps-1, Math.floor(prog*steps));
      y = CURVE_Y - amp*(0.18 + 0.82*(k/(steps-1)));
    } else {
      y = CURVE_Y - amp*(0.18 + 0.82*prog) - noiseAt(prog*9)*amp*0.16;
    }
    pts.push([x,y]);
  }
  return pts;
}

function strokePoints(pts,color,alpha,width,dash){
  if(alpha<=0.01) return;
  g.save(); g.globalAlpha=alpha; g.strokeStyle=color; g.lineWidth=width; g.lineJoin='round';
  if(dash) g.setLineDash(dash);
  g.beginPath();
  for (let i=0;i<pts.length;i++){ if(i===0)g.moveTo(pts[i][0],pts[i][1]); else g.lineTo(pts[i][0],pts[i][1]); }
  g.stroke(); g.restore();
}

function fillGap(upper,lower,color,alpha){
  if(alpha<=0.01) return;
  g.save(); g.globalAlpha=alpha; g.fillStyle=color; g.beginPath();
  for (let i=0;i<upper.length;i++){ if(i===0)g.moveTo(upper[i][0],upper[i][1]); else g.lineTo(upper[i][0],upper[i][1]); }
  for (let i=lower.length-1;i>=0;i--){ g.lineTo(lower[i][0],lower[i][1]); }
  g.closePath(); g.fill(); g.restore();
}

function drawCurves(t,f){
  const a = eo(sg(t,0.8,2.0))*(1-sg(t,90.0,97.3));
  if(a<=0.01) return;

  const grow = eo(sg(t,0.8,8.5));
  const expIn = eo(sg(t,14.4,21.0));
  const expDrop = eo(sg(t,54.0,66.0));
  const gapIn = eo(sg(t,31.5,34.5))*(1-sg(t,50.0,53.0));
  const stepMix = eo(sg(t,53.0,60.0));
  const collapse = eo(sg(t,78.0,90.0));

  const real = curvePoints(REAL_AMP*(1-0.42*stepMix), 0);
  const realSteps = curvePoints(REAL_AMP, 8);
  const realBlend = real.map((p,i)=>[p[0], lerp(p[1], realSteps[i][1], stepMix)]);
  const expAmp = lerp(REAL_AMP*1.75, REAL_AMP*0.86, expDrop);
  const exp = curvePoints(expAmp, 0);
  const flat = curvePoints(REAL_AMP*0.30, 0).map((p)=>[p[0], CURVE_Y - REAL_AMP*0.30]);

  strokePoints(realBlend, HURT, a*grow*0.18, 24);
  strokePoints(exp, GOLD, a*expIn*0.95, 4, [14,10]);
  strokePoints(realBlend, HURT, a*grow*0.95, 5);
  strokePoints(realBlend, '#FF9BA3', a*grow*pulse(f)*0.55, 3);
  fillGap(exp, realBlend, HURT, a*gapIn*0.16);

  if (stepMix>0.02){
    const n = 8;
    for (let k=1;k<n;k++){
      const x = CURVE_X0 + (CURVE_X1-CURVE_X0)*k/n;
      const y = CURVE_Y - REAL_AMP*(0.18+0.82*((k-1)/(n-1)));
      const y2 = CURVE_Y - REAL_AMP*(0.18+0.82*(k/(n-1)));
      line(x,y-8,x,y2+8,GOLD,a*stepMix*0.7,2);
    }
  }

  if (collapse>0.02){
    strokePoints(flat, GOLD, a*collapse*0.85, 3);
  }
}

function beatRings(f){
  const p = pulse(f);
  if(p<=0.01) return;
  const cx=960, cy=600, r=30+(1-p)*340;
  g.save(); g.globalAlpha=p*0.16; g.strokeStyle=GOLD; g.lineWidth=2;
  g.beginPath(); g.arc(cx,cy,r,0,6.283); g.stroke(); g.restore();
}

function drawTimer(t,f){
  const a = eo(sg(t,64.2,66.0))*(1-sg(t,74.0,76.0));
  if(a<=0.01) return;
  const cx=1240, cy=520, r=132, cycle=20;
  const p = ((t-64.2)%cycle)/cycle;
  g.save(); g.globalAlpha=a*0.18; g.strokeStyle=DIM; g.lineWidth=3;
  g.beginPath(); g.arc(cx,cy,r,0,6.283); g.stroke(); g.restore();
  g.save(); g.globalAlpha=a*0.95; g.strokeStyle=GOLD; g.lineWidth=14; g.lineCap='round';
  g.beginPath(); g.arc(cx,cy,r,-1.5708,-1.5708+p*6.283); g.stroke(); g.restore();
  const bp = pulse(f);
  disc(cx,cy-r,5+9*bp,GOLD,a*(0.5+0.5*bp));
  disc(cx,cy,58+34*bp,GOLD,a*0.12);
  disc(cx,cy,18,GOLD,a*0.85);
}

// ---------- close ----------
function drawClose(t,f){
  const a = eo(sg(t,88.0,90.5));
  if(a<=0.01) return;
  const y = 548;
  const w = eo(sg(t,88.0,92.0))*720;
  rrect(960-w/2, y-3, w, 6, 3, GOLD, a*0.9);
  const p = pulse(f);
  for (let i=0;i<5;i++){
    const rr = 60+i*90+(1-p)*40;
    g.save(); g.globalAlpha=a*p*0.16*(1-i/5); g.strokeStyle=GOLD; g.lineWidth=2;
    g.beginPath(); g.arc(960,y,rr,0,6.283); g.stroke(); g.restore();
  }
}

return function(frame){
  const f = frame;
  const t = (f/30) / data.scale;
  g.setTransform(1,0,0,1,0,0);
  background(f,t);

  beatRings(f);
  drawCurves(t,f);
  drawTimer(t,f);
  drawClose(t,f);

  // labels
  for (let i=0;i<bigEls.length;i++){
    const sc = data.statements[i];
    if(!sc){continue;}
    const inA = eo(sg(f,sc.s,sc.s+9));
    const outA = 1-sg(f,sc.e-9,sc.e);
    const a = inA*outA;
    const rise = (1-eo(sg(f,sc.s,sc.s+12)))*22;
    bigEls[i].style.opacity = String(a);
    bigEls[i].style.transform = 'translateY('+rise.toFixed(2)+'px)';
  }
  for (let i=0;i<lineEls.length;i++){
    const sc = data.lines[i];
    if(!sc){continue;}
    const inA = eo(sg(f,sc.s,sc.s+8));
    const outA = 1-sg(f,sc.e-8,sc.e);
    lineEls[i].style.opacity = String(inA*outA*0.96);
  }
  const fade = 1-sg(f,data.labelFade,data.labelFade+24);
  fixedEls.label.style.opacity = String(0.92*fade);
  fixedEls.tag.style.opacity = String(0.85*fade);
  const la = eo(sg(f,data.loops.s+14,data.loops.s+34))*(1-sg(f,data.loops.e-40,data.loops.e));
  fixedEls.loopA.style.opacity = String(la*0.95);
  fixedEls.loopB.style.opacity = String(la*0.95);
};
`;

  const program = htmlVisual({ html: html, css: css, data: data, setup: setup });

  return sealVisualTrack({
    id: options.id,
    timelineId: timeline.id,
    visualIr: "hypit.visual-ir@1",
    presents: [{
      id: options.id,
      order: 0,
      z: 0,
      span: window.span,
      elements: [
        {
          id: programId, kind: "program", order: 0, program: program,
          style: [
            { name: "position", value: "absolute" },
            { name: "left", value: within.xPx + "px" },
            { name: "top", value: within.yPx + "px" },
            { name: "width", value: within.widthPx + "px" },
            { name: "height", value: within.heightPx + "px" },
          ],
        } as VisualElement,
        ...elements,
      ],
    }],
  });
}
