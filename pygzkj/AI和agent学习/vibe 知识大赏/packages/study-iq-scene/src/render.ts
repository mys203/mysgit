import { sealVisualTrack } from "@hypit/composition";
import type { VisualElement } from "@hypit/composition";
import { htmlVisual } from "@hypit/html-program";
import type { FontStackRef } from "@hypit/media";
import type { Timeline } from "@hypit/timeline";
import type { SpatialFrame } from "@hypit/spatial";
import { assertTemporalWindowFor } from "@hypit/temporal";
import type { TemporalWindow } from "@hypit/temporal";
import { ACCENT_FRAMES, BEAT_SECONDS, DURATION_SECONDS } from "./beats.js";
import { CHUNK_GROUPS, LINES, PIECE_SQUARES, SCRAMBLED_SQUARES, STATEMENTS } from "./content.js";

export type SceneOptions = { readonly id: string; readonly title: string; readonly tag: string };

const FPS = 30;

/** A one-off scene for 《学习与智商》: every frame is computed from the requested frame alone. */
export function renderScene(timeline: Timeline, within: SpatialFrame, window: TemporalWindow,
  font: FontStackRef, options: SceneOptions) {
  assertTemporalWindowFor(window, { subjectId: options.id, timeline: timeline });
  const start = window.span.startFrame;
  const length = window.span.endFrameExclusive - start;
  if (length <= 0) throw new Error("Study and IQ scene needs a non-empty window.");

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
  label("loopA", "重复阅读", [
    { name: "left", value: "560px" }, { name: "top", value: "736px" }, { name: "width", value: "280px" },
    { name: "text-align", value: "center" }, { name: "font-size", value: "30px" },
    { name: "color", value: "#79809B" },
  ]);
  label("loopB", "提取练习", [
    { name: "left", value: "1080px" }, { name: "top", value: "736px" }, { name: "width", value: "280px" },
    { name: "text-align", value: "center" }, { name: "font-size", value: "30px" },
    { name: "color", value: "#C9A96A" },
  ]);

  // The piece is authored at the soundtrack's own length. Handing the component a
  // shorter window tightens the whole choreography without touching the music's
  // tempo, so every accent still lands on the beat it was written against.
  const timeScale = (length / FPS) / DURATION_SECONDS;
  const local = (seconds: number) => Math.round(seconds * timeScale * FPS) - start;
  const schedule = (items: readonly { id: string; start: number; end: number }[]) =>
    items.map((item) => ({ s: local(item.start), e: local(item.end) }));

  const data = {
    start: start,
    length: length,
    scale: timeScale,
    seconds: length / FPS,
    beat: BEAT_SECONDS,
    accents: ACCENT_FRAMES.filter((f) => f >= start && f < start + length).map((f) => f - start),
    statements: schedule(STATEMENTS),
    lines: schedule(LINES),
    loops: { s: local(104.6), e: local(134.4) },
    labelFade: local(142.6),
    total: Math.round(DURATION_SECONDS * FPS),
    real: PIECE_SQUARES.map((s) => [s[0], s[1]]),
    random: SCRAMBLED_SQUARES.map((s) => [s[0], s[1]]),
    groups: CHUNK_GROUPS.map((g) => g.slice()),
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
    disc(q.x, y, q.r, COOL, q.a*(0.6+0.4*Math.sin(f*0.03+i)));
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

// ---------- act 1: twelve things ----------
function actDots(t,f){
  const cx=960, cy=548, cols=4, rows=3, sx=152, sy=118;
  for (let i=0;i<12;i++){
    const px = cx + ((i%cols) - (cols-1)/2)*sx;
    const py = cy + (((i/cols)|0) - (rows-1)/2)*sy;
    const aAppear = 0.5 + i*0.155;
    const app = eo(sg(t, aAppear, aAppear+0.45));
    const dis = sg(t, 5.95 + i*0.105, 6.35 + i*0.105);
    const a = app*(1-dis);
    if (a<=0.01) continue;
    const r = 40*app;
    disc(px,py,r, i%3===0?GOLD:COOL, a*0.95);
    disc(px,py,r*0.42,'#0A0A1E', a*0.9);
    disc(px,py,r*1.9, COOL, a*0.05);
  }
}

// ---------- act 2: capacity ----------
function actCapacity(t,f){
  const x0=620, x1=1300, y=556, h=38, cap=7, total=12;
  const show = eo(sg(t,12.6,14.6));
  if (show<=0.01) return;
  rrect(x0,y,x1-x0,h,19,'rgba(237,234,227,0.10)',0.55*show);
  const fill = eo(sg(t,13.6,17.2));
  const w = (x1-x0)*fill;
  rrect(x0,y,Math.max(w,8),h,19,TEAL,0.9*show);
  for (let i=1;i<total;i++){
    const x = x0 + (x1-x0)*i/total;
    line(x,y-7,x,y+h+7,'#0A0A1E',0.75*show,3);
  }
  const mx = x0 + (x1-x0)*cap/total;
  const mA = eo(sg(t,16.6,17.8));
  line(mx,y-46,mx,y+h+46,GOLD,mA*show,3);
  disc(mx, y-62, 9, GOLD, mA*show);
  // overflow: what does not fit
  const spill = eo(sg(t,20.2,25.4));
  for (let i=0;i<5;i++){
    const bx = x0 + (x1-x0)*(cap+0.4+i*0.9)/total*1.0;
    const rise = spill*(150 + i*34);
    const a = spill*(1-sg(t,25.4,28.2));
    disc(bx, y + h/2 - rise, 22, VIO, a*0.85);
    disc(bx, y + h/2 - rise, 46, VIO, a*0.10);
  }
}

// ---------- acts 3-5: the board ----------
const CELL = 58, BX = 960, BY = 548;
const BOARD_HALF = CELL*4;

function sq(i){
  const col = i%8, row = (i/8)|0;
  return { x: BX - BOARD_HALF + (col+0.5)*CELL, y: BY - BOARD_HALF + (row+0.5)*CELL };
}

function squareOf(rc){ return { x: BX - BOARD_HALF + (rc[0]+0.5)*CELL, y: BY - BOARD_HALF + (rc[1]+0.5)*CELL }; }
const SQUARES_REAL = data.real.map(squareOf);
const SQUARES_RANDOM = data.random.map(squareOf);
const GROUPS = data.groups.map(function(idxs){
  let x=0, y=0;
  for (let i=0;i<idxs.length;i++){ const s = SQUARES_RANDOM[idxs[i]]; x+=s.x; y+=s.y; }
  return { x: x/idxs.length, y: y/idxs.length };
});

function drawBoardGuide(alpha, f){
  if(alpha<=0.01) return;
  const x0 = BX-BOARD_HALF, y0 = BY-BOARD_HALF;
  rrect(x0-26,y0-26,BOARD_HALF*2+52,BOARD_HALF*2+52,18,'rgba(237,234,227,0.05)',alpha);
  rrectStroke(x0-26,y0-26,BOARD_HALF*2+52,BOARD_HALF*2+52,18,'rgba(237,234,227,0.30)',alpha,2);
  g.save(); g.globalAlpha=alpha*0.22; g.strokeStyle=INK; g.lineWidth=1; g.beginPath();
  for (let i=0;i<=8;i++){
    const x = x0 + i*CELL, y = y0 + i*CELL;
    g.moveTo(x,y0); g.lineTo(x,y0+CELL*8);
    g.moveTo(x0,y); g.lineTo(x0+CELL*8,y);
  }
  g.stroke(); g.restore();
}

// A piece's state through the whole board passage.
function pieceState(t){
  const appearStart = 31.4;
  const scrambleAt = 58.8;
  const mergeAt = 88.6;
  const dissolveAt = 104.6;
  return { appearStart, scrambleAt, mergeAt, dissolveAt };
}

function drawPieces(t,f,alpha,trackAlpha){
  const P = pieceState(t);
  const SEC = data.seconds;
  for (let i=0;i<12;i++){
    const appear = eo(sg(t, P.appearStart + i*0.135, P.appearStart + i*0.135 + 0.4));
    if (appear<=0.01) continue;
    const from = SQUARES_REAL[i];
    const to = SQUARES_RANDOM[i];
    const sp = eio(sg(t, P.scrambleAt + (i%4)*0.10, P.scrambleAt + 1.5 + (i%4)*0.10));
    let x = lerp(from.x, to.x, sp);
    let y = lerp(from.y, to.y, sp);
    // jolt while scrambling
    const jolt = Math.sin(cl(sg(t,P.scrambleAt+0.2,P.scrambleAt+2.2),0,1)*3.14159);
    const group = (i/3)|0;
    const mp = eio(sg(t, P.mergeAt + group*0.22, P.mergeAt + 1.4 + group*0.22));
    const cx = (x + (GROUPS[group].x - x)*mp);
    const cy = (y + (GROUPS[group].y - y)*mp);
    const r = lerp(28, 42, mp);
    const spanA = appear*(1-sg(t, P.dissolveAt, P.dissolveAt+1.6));
    const a = spanA*alpha;
    const jx = (sp>0 && sp<1) ? Math.sin(f*0.9 + i)*2.4*jolt : 0;
    disc(cx+jx, cy, r*2.4, i%3===0?GOLD:COOL, a*0.09);
    disc(cx+jx, cy, r, i%3===0?GOLD:COOL, a);
    disc(cx+jx, cy, r*0.40, '#0A0A1E', a);
  }
}

function drawGroups(t,f,alpha){
  const P = pieceState(t);
  const a0 = eo(sg(t,79.0,82.5));
  const a1 = 1-sg(t, P.mergeAt+0.9, P.mergeAt+2.0);
  const a = a0*a1*alpha;
  if(a<=0.01) return;
  for (let gi=0; gi<4; gi++){
    const pts = [];
    for (let k=0;k<3;k++){ const s = SQUARES_RANDOM[gi*3+k]; pts.push(s); }
    let minx=1e9,miny=1e9,maxx=-1e9,maxy=-1e9;
    for (let k=0;k<3;k++){ minx=Math.min(minx,pts[k].x); maxx=Math.max(maxx,pts[k].x); miny=Math.min(miny,pts[k].y); maxy=Math.max(maxy,pts[k].y); }
    const pad = 34;
    rrectStroke(minx-pad,miny-pad,(maxx-minx)+pad*2,(maxy-miny)+pad*2,26,GOLD,a*0.75,2);
  }
}

// ---------- act 6: two ways to study ----------
function drawLoops(t,f){
  const A = eo(sg(t,105.2,107.4));
  const B = sg(t,134.0,136.2);
  const a = A*(1-B);
  if (a<=0.01) return;
  const cyc = 2.4;
  // left: repetition that fades
  const la = cl((t-105.2)/cyc, 0, 1e9);
  const fade = Math.max(0.12, 1 - la*0.16);
  const lx = 700, rx = 1220, r = 132;
  const cy = 548;
  g.save(); g.globalAlpha = a*0.18; g.strokeStyle = DIM; g.lineWidth = 2;
  g.beginPath(); g.arc(lx,cy,r,0,6.283); g.stroke();
  g.beginPath(); g.arc(rx,cy,r,0,6.283); g.stroke(); g.restore();
  const sweep = ((t-105.2)%cyc)/cyc;
  g.save(); g.globalAlpha = a*fade*0.85; g.strokeStyle = DIM; g.lineWidth = 5;
  g.beginPath(); g.arc(lx,cy,r,-1.5708, -1.5708 + sweep*6.283); g.stroke(); g.restore();
  disc(lx,cy,52*(1-0.35*fade),DIM,a*0.30*fade);
  // right: retrieval that deepens
  const rl = cl((t-105.2)/(cyc*1.6),0,1e9);
  const depth = cl(0.25 + rl*0.075, 0, 1);
  g.save(); g.globalAlpha = a*(0.45+0.55*depth); g.strokeStyle = GOLD; g.lineWidth = 5+9*depth;
  g.beginPath(); g.arc(rx,cy,r,-1.5708, -1.5708 + sweep*6.283); g.stroke(); g.restore();
  const gr = g.createRadialGradient(rx,cy,4,rx,cy,r);
  gr.addColorStop(0,'rgba(201,169,106,'+(a*(0.10+0.34*depth))+')');
  gr.addColorStop(1,'rgba(201,169,106,0)');
  g.fillStyle=gr; g.beginPath(); g.arc(rx,cy,r,0,6.283); g.fill();
  disc(rx,cy,26+34*depth,GOLD,a*0.85);
}

// ---------- act 7: close ----------
function drawClose(t,f){
  const a = eo(sg(t,137.0,139.6));
  if (a<=0.01) return;
  const y = 548;
  const w = eo(sg(t,137.0,140.5))*760;
  rrect(960-w/2, y-3, w, 6, 3, GOLD, a*0.9);
  const p = pulse(f);
  for (let i=0;i<5;i++){
    const rr = 60 + i*90 + (1-p)*40;
    g.save(); g.globalAlpha = a*p*0.16*(1-i/5); g.strokeStyle = GOLD; g.lineWidth = 2;
    g.beginPath(); g.arc(960,y,rr,0,6.283); g.stroke(); g.restore();
  }
}

return function(frame){
  const f = frame;
  const t = (f/30) / data.scale;
  g.setTransform(1,0,0,1,0,0);
  background(f,t);

  const boardAlpha =
    eo(sg(t,30.4,33.0)) *
    (1 - sg(t,64.2,65.4)*(1-sg(t,69.6,70.8))) *
    (1 - sg(t,104.4,106.2));
  drawBoardGuide(boardAlpha*0.9, f);
  drawGroups(t,f,boardAlpha);
  drawPieces(t,f,boardAlpha,1);

  if (t<13) actDots(t,f);
  if (t>=12 && t<30.4) actCapacity(t,f);
  drawLoops(t,f);
  drawClose(t,f);

  // comparison bars, act 4
  const ca = eo(sg(t,64.6,65.8))*(1-sg(t,69.4,70.4));
  if (ca>0.01){
    rrect(560,430,800,500,18,'rgba(10,10,30,0.72)',ca);
    const rows = [[560,'大师',0.92,0.20,GOLD],[700,'新手',0.18,0.16,COOL]];
    for (let i=0;i<2;i++){
      const row = rows[i];
      const grow = eo(sg(t,64.8+i*0.25,66.6+i*0.25));
      const from = i===0?0.92:0.18;
      const to = row[3];
      const v = lerp(from,to,grow);
      rrect(660,row[0],520,34,17,'rgba(237,234,227,0.10)',ca*0.7);
      rrect(660,row[0],Math.max(520*v,8),34,17,row[4],ca*0.92);
    }
  }

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
