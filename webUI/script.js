const BONBONEKA_VER = "3.0 BETA 'Gloopy Oopy Cat Factory'";
const B0MK_CORE_VER = "3.5";
document.getElementById('version-display').innerText = `V${BONBONEKA_VER} | CORE ${B0MK_CORE_VER}`;

const term = document.getElementById('terminal-body');
function log(msg, type='info') {
    const d = document.createElement('div');
    d.className = `line ${type}`;
    d.innerHTML = `<span style="color:#444">[${new Date().toLocaleTimeString()}]</span> ${msg}`;
    term.appendChild(d);
    term.scrollTop = term.scrollHeight;
}

/* ── Tabs ── */
function switchTab(name, btn) {
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.getElementById(`tab-${name}`).classList.add('active');
    btn.classList.add('active');
}

/* ── Build mode toggle ── */
let buildMode = 'statix';
function setBuildMode(m) {
    buildMode = m;
    document.getElementById('mode-statix').classList.toggle('active', m==='statix');
    document.getElementById('mode-fluid').classList.toggle('active',  m==='fluid');
    document.getElementById('fluid-config-row').style.display = m==='fluid' ? '' : 'none';
    document.getElementById('create-mode-label').textContent = m==='statix' ? 'StatiX Build' : 'Fluid Build';
}

/* ── PWA toggle ── */
function onPwaToggle() {
    const on = document.getElementById('f-pwa').checked;
    document.getElementById('build-header').style.display  = on ? 'none' : '';
    document.getElementById('pwa-header').style.display    = on ? ''     : 'none';
    document.getElementById('normal-build-inputs').style.display = on ? 'none' : '';
    document.getElementById('pwa-build-inputs').style.display    = on ? ''     : 'none';
    document.getElementById('create-mode-label').textContent = on ? 'PWA Build' : (buildMode==='fluid' ? 'Fluid Build' : 'StatiX Build');
}

/* ── Commands ── */
function runCmd(type) {
    let cmd = "bomk " + type;

    if (type === 'create') {
        const isPwa = document.getElementById('f-pwa').checked;
        if (isPwa) {
            const url = document.getElementById('path-pwa').value;
            if (!url) return log("Error: PWA URL required.", "error");
            cmd += ` --pwa ${url}`;
        } else if (buildMode === 'fluid') {
            const path = document.getElementById('path-create').value;
            const cfg  = document.getElementById('path-fluid-config').value;
            if (!path) return log("Error: Project path required.", "error");
            if (!cfg)  return log("Error: Config path required for Fluid build.", "error");
            cmd += ` ${path} ${cfg}`;
        } else {
            const path = document.getElementById('path-create').value;
            if (!path) return log("Error: Project path required.", "error");
            if (document.getElementById('f-s').checked)       cmd += " -s";
            if (document.getElementById('f-v').checked)       cmd += " --verbose";
            if (document.getElementById('f-nobuild').checked) cmd += " --nobuild";
            const name = document.getElementById('opt-name').value;
            if (name) cmd += ` --name "${name}"`;
            cmd += ` ${path}`;
        }
    } else {
        const path = document.getElementById('path-doctor').value;
        if (!path) return log("Error: Path required.", "error");
        cmd += ` ${path}`;
    }
    executeInBackground(cmd);
}

function runGit(flag) {
    const tmpl = document.getElementById('git-tmpl').value || "template";
    const url  = document.getElementById('git-url').value;
    let cmd = `bomk gitlink ${tmpl} ${flag}`;
    if (flag==='--set' && url) cmd += ` ${url}`;
    executeInBackground(cmd);
}

function executeInBackground(cmd) {
    log(`Spawning: <code>${cmd}</code>`);
    log(`Status: <span style="color:#7c6af7">RUNNING</span>`);
    setTimeout(() => log("Task accepted by B0MK Core. Thread spawned."), 800);
}

/* ── Hold-to-reveal ── */
const HOLD_MS = 800;
let holdTimer=null, activeHold=null;
function startHold(el) {
    activeHold = el; el.classList.add('holding');
    holdTimer = setTimeout(() => showOverlay(el), HOLD_MS);
}
function cancelHold() {
    clearTimeout(holdTimer); holdTimer=null;
    if (activeHold) { activeHold.classList.remove('holding'); activeHold=null; }
}
document.querySelectorAll('.holdable').forEach(el => {
    el.addEventListener('mousedown',  ()=>startHold(el));
    el.addEventListener('mouseleave', cancelHold);
    el.addEventListener('mouseup',    cancelHold);
    el.addEventListener('touchstart', e=>{e.preventDefault();startHold(el);},{passive:false});
    el.addEventListener('touchend',   cancelHold);
});
function showOverlay(el) {
    const diff = el.dataset.diff||'easy';
    const label = {easy:'Easy',med:'Medium',hard:'Hard'}[diff]||diff;
    document.getElementById('ov-name').textContent  = el.dataset.name||'??';
    document.getElementById('ov-desc').textContent  = el.dataset.desc||'No description.';
    document.getElementById('ov-ver').textContent   = el.dataset.ver||'??';
    document.getElementById('ov-diff2').textContent = label;
    const b = document.getElementById('ov-diff');
    b.textContent = label; b.className = `info-badge ${diff}`;
    document.getElementById('overlay').classList.add('visible');
}
function closeOverlay() { document.getElementById('overlay').classList.remove('visible'); }
document.addEventListener('keydown', e=>{ if(e.key==='Escape'){ closeOverlay(); closeFigModal(); }});

/* ── Slider ── */
const handle=document.getElementById('git-slider'), sliderBg=document.querySelector('.slider-bg');
let dragging=false;
handle.addEventListener('mousedown',()=>dragging=true);
window.addEventListener('mouseup',()=>{ if(dragging){dragging=false;handle.style.left='0px';}});
window.addEventListener('mousemove',e=>{
    if(!dragging) return;
    const r=sliderBg.getBoundingClientRect();
    let x=Math.max(0,Math.min(e.clientX-r.left-24, r.width-48));
    handle.style.left=x+'px';
    if(x>=r.width-48){dragging=false;runGit('--disengage');}
});

/* ══════════════════════════════════════════
   .bombundlefig Generator
══════════════════════════════════════════ */
function openFigModal()  { document.getElementById('fig-modal').classList.add('visible'); resizeCanvas(); }
function closeFigModal() { document.getElementById('fig-modal').classList.remove('visible'); }

/* ── Canvas setup ── */
const canvas = document.getElementById('fig-canvas');
const ctx    = canvas.getContext('2d');
let W=0, H=0;

function resizeCanvas() {
    const wrap = canvas.parentElement;
    W = canvas.width  = wrap.clientWidth;
    H = canvas.height = wrap.clientHeight;
    draw();
}
window.addEventListener('resize', ()=>{ if(document.getElementById('fig-modal').classList.contains('visible')) resizeCanvas(); });

/* ── State ── */
let bubbles  = [];   // {id,x,y,r,name,color}
let dots     = [];   // {id,x,y,name,bubbleId|null}
let links    = [];   // {a:dotId, b:dotId}
let selected = null; // {type:'bubble'|'dot', id}
let tool     = 'bubble';

let linkStart = null; // dotId for in-progress link
let pending   = null; // {type,x,y} waiting for name input

const BUBBLE_COLORS = ['rgba(124,106,247,','rgba(76,175,125,','rgba(224,180,92,','rgba(224,92,92,','rgba(92,178,224,'];
let colorIdx = 0;
let nextId   = 1;

function uid() { return nextId++; }

function setTool(t) {
    tool = t;
    document.querySelectorAll('.tool-btn').forEach(b=>b.classList.remove('active'));
    document.getElementById(`tool-${t}`).classList.add('active');
    canvas.style.cursor = t==='select' ? 'default' : 'crosshair';
    draw();
}

function setFileType(btn) {
    document.querySelectorAll('.ftype-btn').forEach(b=>b.classList.remove('active'));
    btn.classList.add('active');
    selectedFileExt = btn.dataset.ext;
}

/* ── Hit testing ── */
function hitDot(x,y) {
    for(let i=dots.length-1;i>=0;i--){
        const d=dots[i];
        if(Math.hypot(x-d.x,y-d.y)<=12) return d;
    }
    return null;
}
function hitBubble(x,y) {
    for(let i=bubbles.length-1;i>=0;i--){
        const b=bubbles[i];
        if(Math.hypot(x-b.x,y-b.y)<=b.r) return b;
    }
    return null;
}
function dotInsideBubble(dot,bubble) {
    return Math.hypot(dot.x-bubble.x, dot.y-bubble.y) <= bubble.r - 10;
}

/* ── Drag ── */
let draggingNode=null, dragOff={x:0,y:0};

canvas.addEventListener('mousedown', e=>{
    const {x,y} = pos(e);

    if(tool==='bubble') {
        pending = {type:'bubble',x,y};
        showNamePopup(e.clientX, e.clientY, 'Group name…');
        return;
    }
    if(tool==='dot') {
        pending = {type:'dot',x,y};
        showNamePopup(e.clientX, e.clientY, 'filename');
        return;
    }
    if(tool==='select') {
        const d=hitDot(x,y);
        if(d){ selected={type:'dot',id:d.id}; draggingNode={type:'dot',id:d.id}; dragOff={x:x-d.x,y:y-d.y}; draw(); return; }
        const b=hitBubble(x,y);
        if(b){ selected={type:'bubble',id:b.id}; draggingNode={type:'bubble',id:b.id}; dragOff={x:x-b.x,y:y-b.y}; draw(); return; }
        selected=null; draw();
    }
});

canvas.addEventListener('mousemove', e=>{
    if(!draggingNode) return;
    const {x,y}=pos(e);
    if(draggingNode.type==='dot'){
        const d=dots.find(d=>d.id===draggingNode.id);
        if(d){ d.x=x-dragOff.x; d.y=y-dragOff.y; assignDotToBubble(d); draw(); }
    } else {
        const b=bubbles.find(b=>b.id===draggingNode.id);
        if(b){ b.x=x-dragOff.x; b.y=y-dragOff.y; dots.filter(d=>d.bubbleId===b.id).forEach(d=>{ d.x+=x-dragOff.x-b.x; d.y+=y-dragOff.y-b.y; }); b.x=x-dragOff.x; b.y=y-dragOff.y; draw(); }
    }
});

canvas.addEventListener('mouseup', ()=>{ draggingNode=null; updatePreview(); });

/* Assign dot to bubble based on position */
function assignDotToBubble(dot) {
    dot.bubbleId = null;
    for(const b of bubbles){
        if(dotInsideBubble(dot,b)){ dot.bubbleId=b.id; break; }
    }
}

function pos(e) {
    const r=canvas.getBoundingClientRect();
    return {x:e.clientX-r.left, y:e.clientY-r.top};
}

/* ── Name popup ── */
const popup   = document.getElementById('name-popup');
const nameInp = document.getElementById('name-input');

function showNamePopup(cx,cy,ph) {
    popup.style.left = (cx+8)+'px';
    popup.style.top  = (cy+8)+'px';
    nameInp.placeholder = ph;
    nameInp.value = '';
    popup.classList.add('show');
    setTimeout(()=>nameInp.focus(),50);
}

function confirmName() {
    const base = nameInp.value.trim();
    popup.classList.remove('show');
    if(!pending) return;
    if(pending.type==='bubble'){
        const name = base || 'Group';
        const col = BUBBLE_COLORS[colorIdx++ % BUBBLE_COLORS.length];
        bubbles.push({id:uid(), x:pending.x, y:pending.y, r:80, name, color:col});
    } else {
        const name = base ? base + selectedFileExt : 'file' + selectedFileExt;
        const d = {id:uid(), x:pending.x, y:pending.y, name, bubbleId:null};
        assignDotToBubble(d);
        dots.push(d);
    }
    pending=null; draw(); updatePreview();
}

nameInp.addEventListener('keydown', e=>{ if(e.key==='Enter') confirmName(); if(e.key==='Escape'){popup.classList.remove('show');pending=null;} });

/* ── Delete ── */
function deleteSelected() {
    if(!selected) return;
    if(selected.type==='bubble'){
        bubbles = bubbles.filter(b=>b.id!==selected.id);
        dots.filter(d=>d.bubbleId===selected.id).forEach(d=>d.bubbleId=null);
    } else {
        dots  = dots.filter(d=>d.id!==selected.id);
        links = links.filter(l=>l.a!==selected.id&&l.b!==selected.id);
    }
    selected=null; draw(); updatePreview();
}

function clearCanvas() { bubbles=[]; dots=[]; links=[]; selected=null; linkStart=null; draw(); updatePreview(); }

/* ── Draw ── */
function draw() {
    ctx.clearRect(0,0,W,H);

    // Bubbles
    for(const b of bubbles){
        const isSelected = selected?.type==='bubble'&&selected.id===b.id;
        ctx.save();
        ctx.beginPath();
        ctx.arc(b.x,b.y,b.r,0,Math.PI*2);
        ctx.fillStyle   = b.color+'0.12)';
        ctx.strokeStyle = isSelected ? '#fff' : b.color+'0.7)';
        ctx.lineWidth   = isSelected ? 2.5 : 1.5;
        ctx.setLineDash(isSelected?[]:[6,4]);
        ctx.fill(); ctx.stroke();
        ctx.restore();
        // label
        ctx.font = '600 12px Inter, sans-serif';
        ctx.fillStyle = b.color+'0.9)';
        ctx.textAlign = 'center';
        ctx.fillText(b.name, b.x, b.y - b.r + 16);
    }

    // Dots
    for(const d of dots){
        const isSel = selected?.type==='dot'&&selected.id===d.id;
        ctx.beginPath(); ctx.arc(d.x,d.y,10,0,Math.PI*2);
        const dotColor = d.name.endsWith('.html') ? '#e0905c'
                       : d.name.endsWith('.js')   ? '#e0d45c'
                       : d.name.endsWith('.css')  ? '#5cb8e0'
                       : '#7c6af7';
        ctx.fillStyle   = isSel ? '#fff' : dotColor;
        ctx.strokeStyle = isSel ? '#fff' : dotColor+'99';
        ctx.lineWidth   = isSel ? 2.5 : 1.5;
        ctx.fill(); ctx.stroke();
        ctx.font='500 10px JetBrains Mono, monospace';
        ctx.fillStyle='#c8c8e0';
        ctx.textAlign='center';
        const label = d.name.length>14 ? d.name.slice(0,12)+'..' : d.name;
        ctx.fillText(label, d.x, d.y+22);
    }
}

let mousePos=null;
canvas.addEventListener('mousemove', e=>{ mousePos=pos(e); });

/* ── JSON preview ── */
function updatePreview() {
    const out = {};
    // Groups from bubbles
    for(const b of bubbles){
        const files = dots.filter(d=>d.bubbleId===b.id).map(d=>d.name);
        if(files.length) out[b.name] = files;
    }
    // Groups from links (dots not in any bubble)
    const linked = new Set();
    for(const l of links){
        const a=dots.find(d=>d.id===l.a), b=dots.find(d=>d.id===l.b);
        if(!a||!b||a.bubbleId||b.bubbleId) continue;
        // find or create group
        const key = [a.name,b.name].sort().join('+');
        if(!out[key]) out[key]=[];
        if(!out[key].includes(a.name)) out[key].push(a.name);
        if(!out[key].includes(b.name)) out[key].push(b.name);
    }
    document.getElementById('fig-json-preview').textContent = JSON.stringify(out, null, 2);
}

/* ── Export ── */
function exportFig() {
    updatePreview();
    const json = document.getElementById('fig-json-preview').textContent;
    const blob = new Blob([json], {type:'application/json'});
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = '.bombundlefig';
    a.click();
    log('Exported <code>.bombundlefig</code> — place it in your project root.');
}