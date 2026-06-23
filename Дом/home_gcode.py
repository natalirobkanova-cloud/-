#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""G-код Генератор — Mach3 (.tap) / Fanuc (.nc)"""
import re, os, math
import tkinter as tk
from tkinter import ttk, filedialog

# ── Цвета ────────────────────────────────────────────────────────────────────
BG='#12121e'; SURF='#1c1c2e'; ELEV='#26263e'; BORDER='#38385e'
TEXT='#dcdcf0'; SUBT='#6868a0'; ACCENT='#5b72cc'; SUCCESS='#4db870'
INP='#202038'; CODEBG='#0a0a18'; CODEFG='#c8c8e8'
MONO=('Courier New',9); UI=('Segoe UI',9); BOLD=('Segoe UI',9,'bold')

# ── Тема ─────────────────────────────────────────────────────────────────────
def setup_theme(root):
    s=ttk.Style(root); s.theme_use('clam')
    BTN='#2e2e4a'; BTN_H='#3c3c5c'
    s.configure('.',background=BG,foreground=TEXT,font=UI,lightcolor=BG,
        darkcolor=BG,relief='flat',borderwidth=0,troughcolor=SURF,
        fieldbackground=INP,insertcolor=TEXT)
    s.configure('TFrame',background=BG)
    s.configure('TLabel',background=BG,foreground=TEXT)
    s.configure('TButton',background=BTN,foreground=TEXT,padding=(10,5),
        lightcolor=BTN,darkcolor=BTN)
    s.map('TButton',background=[('active',BTN_H)],
        lightcolor=[('active',BTN_H)],darkcolor=[('active',BTN_H)])
    s.configure('Tog.TButton',background='#1a1a35',foreground=SUBT,
        padding=(14,5),font=UI,lightcolor='#1a1a35',darkcolor='#1a1a35')
    s.map('Tog.TButton',background=[('active','#22224a')],
        lightcolor=[('active','#22224a')],darkcolor=[('active','#22224a')])
    s.configure('TogOn.TButton',background='#252550',foreground=TEXT,
        padding=(14,5),font=BOLD,lightcolor=ACCENT,darkcolor=ACCENT)
    s.map('TogOn.TButton',background=[('active','#2e2e60')],
        lightcolor=[('active',ACCENT)],darkcolor=[('active',ACCENT)])
    s.configure('Save.TButton',background='#1e5c38',foreground='#fff',
        font=BOLD,padding=(14,6),lightcolor='#1e5c38',darkcolor='#1e5c38')
    s.map('Save.TButton',background=[('active','#2e7a50')],
        lightcolor=[('active','#2e7a50')],darkcolor=[('active','#2e7a50')])
    s.configure('TEntry',fieldbackground=INP,foreground=TEXT,
        insertcolor=TEXT,lightcolor=INP,darkcolor=INP,padding=(6,4))
    s.map('TEntry',lightcolor=[('focus',ACCENT)],darkcolor=[('focus',ACCENT)])
    s.configure('TScrollbar',background=ELEV,troughcolor=BG,
        arrowcolor=SUBT,lightcolor=ELEV,darkcolor=ELEV)
    s.map('TScrollbar',background=[('active',BORDER)])
    s.configure('TNotebook',background=BG,tabmargins=0,
        lightcolor=BG,darkcolor=BG,relief='flat',borderwidth=0)
    s.configure('TNotebook.Tab',background=ELEV,foreground=SUBT,font=UI,
        padding=(16,8),lightcolor=ELEV,darkcolor=ELEV)
    s.map('TNotebook.Tab',
        background=[('selected',SURF)],foreground=[('selected',TEXT)],
        lightcolor=[('selected',SURF)],darkcolor=[('selected',SURF)])
    for w in ('TRadiobutton','TCheckbutton'):
        s.configure(w,background=SURF,foreground=TEXT,indicatorcolor=INP)
        s.map(w,indicatorcolor=[('selected',ACCENT)],background=[('active',SURF)])

# ── ScrollFrame ───────────────────────────────────────────────────────────────
class ScrollFrame(tk.Frame):
    def __init__(self,parent,**kw):
        super().__init__(parent,bg=BG,**kw)
        self.canvas=tk.Canvas(self,bg=BG,highlightthickness=0,bd=0)
        sb=ttk.Scrollbar(self,orient='vertical',command=self.canvas.yview)
        self.inner=tk.Frame(self.canvas,bg=BG)
        win=self.canvas.create_window((0,0),window=self.inner,anchor='nw')
        self.canvas.configure(yscrollcommand=sb.set)
        self.canvas.pack(side='left',fill='both',expand=True)
        sb.pack(side='right',fill='y')
        self.inner.bind('<Configure>',
            lambda _:self.canvas.configure(scrollregion=self.canvas.bbox('all')))
        self.canvas.bind('<Configure>',
            lambda e:self.canvas.itemconfigure(win,width=e.width))

# ── UI-хелперы ────────────────────────────────────────────────────────────────
def section(parent,title,color=ACCENT):
    outer=tk.Frame(parent,bg=BG); outer.pack(fill='x',padx=10,pady=(10,0))
    hdr=tk.Frame(outer,bg=ELEV,height=28); hdr.pack(fill='x'); hdr.pack_propagate(False)
    tk.Frame(hdr,bg=color,width=3).pack(side='left',fill='y')
    tk.Label(hdr,text=f'  {title}',bg=ELEV,fg=TEXT,font=BOLD).pack(side='left',pady=4)
    body=tk.Frame(outer,bg=SURF,padx=10,pady=8); body.pack(fill='x')
    return body

def le(parent,label,var,row,w=9,unit=''):
    tk.Label(parent,text=label,bg=SURF,fg=SUBT,font=UI).grid(
        row=row,column=0,sticky='w',pady=2)
    ttk.Entry(parent,textvariable=var,width=w).grid(
        row=row,column=1,sticky='w',padx=(8,0),pady=2)
    if unit:
        tk.Label(parent,text=unit,bg=SURF,fg='#404070',font=UI).grid(
            row=row,column=2,sticky='w',padx=(4,0))

# ── G-код: форматирование ─────────────────────────────────────────────────────
def f3(v): return f'{v:.3f}'
def f4(v): return f'{v:.4f}'
def ctrl_style(ctrl):
    if ctrl=='mach3': return {'ff':f4,'G0':'G0','G1':'G1','G2':'G2','G3':'G3'}
    return                   {'ff':f3,'G0':'G00','G1':'G01','G2':'G02','G3':'G03'}

def Fm(val,st):
    if st.get('f')!=val: st['f']=val; return f' F{int(val)}'
    return ''

def z_levels(p):
    zsurf=p['zsurf']; zd=p['zd']
    zstep=max(0.001,abs(p['zstep']))
    total=abs(zd-zsurf); n=math.ceil(total/zstep) if total>0.001 else 1
    return [zsurf-min(i*zstep,total) for i in range(1,n+1)]

# ── G-код: шапка / подвал ────────────────────────────────────────────────────
def make_header(p):
    ff=p['ff']; G0=p['G0']; zs=ff(p['zs']); t=int(p['tool']); rpm=int(p['rpm'])
    if p['ctrl']=='mach3':
        return [f'({p["name"]})','G21 G49 G80 G90',f'{G0} Z{zs}',f'M3 S{rpm}','']
    return [f'({p["name"]})','%',f'O{t:04d}','G17 G21 G40 G49 G80 G90',
            f'T{t:02d} M06','G54',f'S{rpm} M03',f'G43 H{t:02d}',f'{G0} Z{zs}','']

def make_footer(p):
    ff=p['ff']; G0=p['G0']
    if p['ctrl']=='mach3':
        return ['',f'{G0} Z{ff(50.)}',f'{G0} X{ff(0.)} Y{ff(0.)}','M5','M30']
    return ['',f'{G0} Z{ff(50.)}','M05','M30','%']

# ── G-код: контур — окружность (спираль) ─────────────────────────────────────
def contour_circle(cx,cy,p,n,st):
    ff=p['ff']; G0=p['G0']; G1=p['G1']; G2=p['G2']
    t=p['td']/2
    r=max(0.001,p['diam']/2-t) if p['mtype']=='contour_in' else p['diam']/2+t
    fz=p['fz']; fxy=p['fxy']
    out=['',f'(Окр.{n:02d}  X{ff(cx)} Y{ff(cy)}  D{ff(p["diam"])})',
         f'{G0} X{ff(cx+r)} Y{ff(cy)}',f'{G0} Z{ff(p["zs"])}',
         f'{G1} Z{ff(p["zsurf"])}{Fm(fz,st)}']
    for z in z_levels(p):
        out.append(f'{G2} X{ff(cx+r)} Y{ff(cy)} I{ff(-r)} J{ff(0.)} Z{ff(z)}{Fm(fxy,st)}')
    out+=[f'{G2} X{ff(cx+r)} Y{ff(cy)} I{ff(-r)} J{ff(0.)}',f'{G0} Z{ff(p["zs"])}']
    return out

# ── G-код: контур — квадрат (рампа) ──────────────────────────────────────────
def contour_square(cx,cy,p,n,st):
    ff=p['ff']; G0=p['G0']; G1=p['G1']
    t=p['td']/2
    h=max(0.001,p['side']/2-t) if p['mtype']=='contour_in' else p['side']/2+t
    x1,y1=cx-h,cy-h; x2,y2=cx+h,cy-h; x3,y3=cx+h,cy+h; x4,y4=cx-h,cy+h
    out=['',f'(Кв.{n:02d}  X{ff(cx)} Y{ff(cy)}  A{ff(p["side"])})',
         f'{G0} X{ff(x1)} Y{ff(y1)}',f'{G0} Z{ff(p["zs"])}',
         f'{G1} Z{ff(p["zsurf"])}{Fm(p["fz"],st)}']
    z_prev=p['zsurf']
    for z_next in z_levels(p):
        dz=(z_next-z_prev)/4; fxy=p['fxy']
        out+=[f'{G1} X{ff(x2)} Y{ff(y2)} Z{ff(z_prev+dz)}{Fm(fxy,st)}',
              f'{G1} X{ff(x3)} Y{ff(y3)} Z{ff(z_prev+2*dz)}',
              f'{G1} X{ff(x4)} Y{ff(y4)} Z{ff(z_prev+3*dz)}',
              f'{G1} X{ff(x1)} Y{ff(y1)} Z{ff(z_next)}',
              f'{G1} X{ff(x2)} Y{ff(y2)}',f'{G1} X{ff(x3)} Y{ff(y3)}',
              f'{G1} X{ff(x4)} Y{ff(y4)}',f'{G1} X{ff(x1)} Y{ff(y1)}']
        z_prev=z_next
    out.append(f'{G0} Z{ff(p["zs"])}'); return out

# ── G-код: торцевое — окружность ─────────────────────────────────────────────
def face_circle(cx,cy,p,n,st):
    ff=p['ff']; G0=p['G0']; G1=p['G1']; G2=p['G2']
    t=p['td']/2; r_max=max(t,p['diam']/2-t)
    step=max(0.1,p['td']*(p['overlap']/100))
    radii=[]; r=t
    while r<r_max-0.001: radii.append(r); r+=step
    radii.append(r_max)
    out=['',f'(Торц.{n:02d}  X{ff(cx)} Y{ff(cy)}  D{ff(p["diam"])})']
    for z in z_levels(p):
        out+=[f'{G0} X{ff(cx+radii[0])} Y{ff(cy)}',f'{G0} Z{ff(p["zs"])}',
              f'{G1} Z{ff(z)}{Fm(p["fz"],st)}']
        for j,r in enumerate(radii):
            if j: out.append(f'{G1} X{ff(cx+r)} Y{ff(cy)}{Fm(p["fxy"],st)}')
            out.append(f'{G2} X{ff(cx+r)} Y{ff(cy)} I{ff(-r)} J{ff(0.)}{Fm(p["fxy"],st)}')
        out.append(f'{G0} Z{ff(p["zs"])}')
    return out

# ── G-код: торцевое — квадрат ────────────────────────────────────────────────
def face_square(cx,cy,p,n,st):
    ff=p['ff']; G0=p['G0']; G1=p['G1']
    t=p['td']/2; h_max=max(t,p['side']/2-t)
    step=max(0.1,p['td']*(p['overlap']/100))
    halves=[]; h=t
    while h<h_max-0.001: halves.append(h); h+=step
    halves.append(h_max)
    out=['',f'(Торц.кв.{n:02d}  X{ff(cx)} Y{ff(cy)}  A{ff(p["side"])})']
    for z in z_levels(p):
        h0=halves[0]
        out+=[f'{G0} X{ff(cx-h0)} Y{ff(cy-h0)}',f'{G0} Z{ff(p["zs"])}',
              f'{G1} Z{ff(z)}{Fm(p["fz"],st)}']
        for j,h in enumerate(halves):
            if j: out.append(f'{G1} X{ff(cx-h)} Y{ff(cy-h)}{Fm(p["fxy"],st)}')
            out+=[f'{G1} X{ff(cx+h)} Y{ff(cy-h)}{Fm(p["fxy"],st)}',
                  f'{G1} X{ff(cx+h)} Y{ff(cy+h)}',
                  f'{G1} X{ff(cx-h)} Y{ff(cy+h)}',
                  f'{G1} X{ff(cx-h)} Y{ff(cy-h)}']
        out.append(f'{G0} Z{ff(p["zs"])}')
    return out

# ── G-код: генерация ──────────────────────────────────────────────────────────
def generate(p):
    try:
        p=dict(p); p.update(ctrl_style(p['ctrl']))
        lines=make_header(p); st={'f':None}; n=0
        for row in range(max(1,p['ny'])):
            for col in range(max(1,p['nx'])):
                n+=1; cx=p['cx1']+col*p['sx']; cy=p['cy1']+row*p['sy']
                if p['shape']=='circle':
                    fn=face_circle if p['mtype']=='face' else contour_circle
                else:
                    fn=face_square if p['mtype']=='face' else contour_square
                lines+=fn(cx,cy,p,n,st)
        lines+=make_footer(p); return '\n'.join(lines)
    except Exception as e: return f'( ОШИБКА: {e} )'

# ── Подсветка синтаксиса ──────────────────────────────────────────────────────
def highlight(w):
    for tag,col in [('cmt','#484878'),('g','#7aacff'),
                    ('m','#ff9060'),('co','#90d090'),('pct','#5a5090')]:
        w.tag_configure(tag,foreground=col)
    for i,line in enumerate(w.get('1.0','end-1c').split('\n'),1):
        def mk(a,b,r=i): return f'{r}.{a}',f'{r}.{b}'
        s=line.strip()
        if not s: continue
        if s.startswith('%'): w.tag_add('pct',*mk(0,len(line))); continue
        if s.startswith('('): w.tag_add('cmt',*mk(0,len(line))); continue
        for m in re.finditer(r'\bG\d+\.?\d*',line): w.tag_add('g',*mk(m.start(),m.end()))
        for m in re.finditer(r'\bM\d+',line):        w.tag_add('m',*mk(m.start(),m.end()))
        for m in re.finditer(r'[XYZIJFHST](?=-?[\d.])',line):
            w.tag_add('co',*mk(m.start(),m.end()))

# ── 2D: утилиты ───────────────────────────────────────────────────────────────
def _nice_step(v):
    for s in (1,2,5,10,20,25,50,100,200,250,500,1000):
        if float(s)>=v: return float(s)
    return 1000.

def _arrow(cvs,x,y,deg,sz=7,col=SUCCESS):
    a=math.radians(deg)
    t=(x+sz*math.cos(a),y-sz*math.sin(a))
    l=(x+sz*.5*math.cos(a+math.pi*.75),y-sz*.5*math.sin(a+math.pi*.75))
    r=(x+sz*.5*math.cos(a-math.pi*.75),y-sz*.5*math.sin(a-math.pi*.75))
    cvs.create_polygon(t[0],t[1],l[0],l[1],r[0],r[1],fill=col,outline='')

# ── 3D: проекция ─────────────────────────────────────────────────────────────
def proj3d(x,y,z,az,el,sc,tx,ty):
    c,s=math.cos(az),math.sin(az); ce,se=math.cos(el),math.sin(el)
    sx=x*c+y*s; sz=x*s*se-y*c*se+z*ce
    return tx+sx*sc, ty-sz*sc

# ── 3D: генерация пакетов пути (кешируется) ───────────────────────────────────
# Каждый пакет: (тип, z_сред, [(x,y,z),...])
# тип: 'r'=подвод, 'h'=рез (спираль), 'f'=чистовой

def _r3(p):
    t=p['td']/2
    if p['mtype']=='contour_in': return max(0.001,p['diam']/2-t)
    if p['mtype']=='contour_out': return p['diam']/2+t
    return p['diam']/2-t

def _h3(p):
    t=p['td']/2
    if p['mtype']=='contour_in': return max(0.001,p['side']/2-t)
    if p['mtype']=='contour_out': return p['side']/2+t
    return p['side']/2-t

def gen3d_batched(p):
    SG=40  # сегментов на окружность (с smooth=True выглядит как 80+)
    batches=[]; lvl=z_levels(p)
    for row in range(max(1,p['ny'])):
      for col in range(max(1,p['nx'])):
        cx=p['cx1']+col*p['sx']; cy=p['cy1']+row*p['sy']
        zs=p['zs']; zsurf=p['zsurf']
        if p['shape']=='circle':
            if p['mtype']=='face':
                t=p['td']/2; r_max=max(t,p['diam']/2-t)
                step=max(0.1,p['td']*(p['overlap']/100))
                radii=[]; r=t
                while r<r_max-0.001: radii.append(r); r+=step
                radii.append(r_max)
                for z in lvl:
                    for j,r in enumerate(radii):
                        batches.append(('r',z,[(cx+r,cy,zs),(cx+r,cy,z)]))
                        pts=[(cx+r*math.cos(2*math.pi*i/SG),
                              cy+r*math.sin(2*math.pi*i/SG),z)
                             for i in range(SG+1)]
                        batches.append(('f' if j==len(radii)-1 else 'h',z,pts))
                    batches.append(('r',zs,[(cx+radii[-1],cy,z),(cx+radii[-1],cy,zs)]))
            else:
                r=_r3(p)
                batches.append(('r',zsurf,[(cx+r,cy,zs),(cx+r,cy,zsurf)]))
                z_prev=zsurf
                for z_next in lvl:
                    pts=[(cx+r*math.cos(2*math.pi*i/SG),
                          cy+r*math.sin(2*math.pi*i/SG),
                          z_prev+(z_next-z_prev)*i/SG) for i in range(SG+1)]
                    batches.append(('h',(z_prev+z_next)/2,pts)); z_prev=z_next
                pts=[(cx+r*math.cos(2*math.pi*i/SG),
                      cy+r*math.sin(2*math.pi*i/SG),z_prev) for i in range(SG+1)]
                batches.append(('f',z_prev,pts))
                batches.append(('r',zs,[(cx+r,cy,z_prev),(cx+r,cy,zs)]))
        else:
            if p['mtype']=='face':
                t=p['td']/2; h_max=max(t,p['side']/2-t)
                step=max(0.1,p['td']*(p['overlap']/100))
                halves=[]; h=t
                while h<h_max-0.001: halves.append(h); h+=step
                halves.append(h_max)
                for z in lvl:
                    for j,h in enumerate(halves):
                        batches.append(('r',z,[(cx-h,cy-h,zs),(cx-h,cy-h,z)]))
                        pts=[(cx-h,cy-h,z),(cx+h,cy-h,z),(cx+h,cy+h,z),
                             (cx-h,cy+h,z),(cx-h,cy-h,z)]
                        batches.append(('f' if j==len(halves)-1 else 'h',z,pts))
                    batches.append(('r',zs,[(cx-halves[-1],cy-halves[-1],z),
                                            (cx-halves[-1],cy-halves[-1],zs)]))
            else:
                h=_h3(p)
                cs=[(cx-h,cy-h),(cx+h,cy-h),(cx+h,cy+h),(cx-h,cy+h),(cx-h,cy-h)]
                batches.append(('r',zsurf,[(cs[0][0],cs[0][1],zs),
                                           (cs[0][0],cs[0][1],zsurf)]))
                z_prev=zsurf
                for z_next in lvl:
                    dz=(z_next-z_prev)/4
                    ramp=[(cs[0][0],cs[0][1],z_prev)]+\
                         [(cs[k+1][0],cs[k+1][1],z_prev+(k+1)*dz) for k in range(4)]
                    batches.append(('h',(z_prev+z_next)/2,ramp))
                    flat=[(cx2,cy2,z_next) for cx2,cy2 in cs]
                    batches.append(('f',z_next,flat)); z_prev=z_next
                batches.append(('r',zs,[(cs[0][0],cs[0][1],z_prev),
                                        (cs[0][0],cs[0][1],zs)]))
    return batches

# ── Приложение ────────────────────────────────────────────────────────────────
class App(tk.Tk):
    _aid=None; _in_draw=False
    # 2D состояние
    _ts=None; _tx=0.; _ty=0.; _ds=None; _dtx=0.; _dty=0.
    # 3D состояние
    _viz3d=False; _path_cache=None
    _3az=math.radians(35); _3el=math.radians(40); _3sc=None
    _3tx=0.; _3ty=0.; _3dr=None; _3daz=0.; _3del=0.
    _3pr=None; _3dtx=0.; _3dty=0.

    def __init__(self):
        super().__init__()
        self.title('G-код Генератор'); self.geometry('1200x740')
        self.configure(bg=BG); setup_theme(self)
        self.protocol('WM_DELETE_WINDOW',self._quit)
        self._vars(); self._build(); self._on_shape(); self._on_mtype()
        self.bind_all('<MouseWheel>',self._wheel)
        self._refresh()

    def _quit(self):
        try: self.destroy()
        except: pass
        os._exit(0)

    def _vars(self):
        S=tk.StringVar
        self.vName=S(value='ПРОГРАММА'); self.vTool=S(value='1')
        self.vRpm=S(value='18000');      self.vCtrl=S(value='mach3')
        self.vShape=S(value='circle');   self.vMtype=S(value='contour_in')
        self.vDiam=S(value='40.0');      self.vSide=S(value='40.0')
        self.vTd=S(value='6.0');         self.vOverlap=S(value='80')
        self.vCx1=S(value='30.0');       self.vCy1=S(value='30.0')
        self.vSx=S(value='60.0');        self.vSy=S(value='60.0')
        self.vNx=S(value='2');           self.vNy=S(value='2')
        self.vZs=S(value='5.0');         self.vZsurf=S(value='0.0')
        self.vZd=S(value='-10.0');       self.vZstep=S(value='2.0')
        self.vFz=S(value='500');         self.vFxy=S(value='1500')
        for v in (self.vName,self.vTool,self.vRpm,self.vCtrl,self.vShape,
                  self.vMtype,self.vDiam,self.vSide,self.vTd,self.vOverlap,
                  self.vCx1,self.vCy1,self.vSx,self.vSy,self.vNx,self.vNy,
                  self.vZs,self.vZsurf,self.vZd,self.vZstep,self.vFz,self.vFxy):
            v.trace_add('write',self._sched)

    # ── Колесо: зум или скролл панели ────────────────────────────────────────
    def _wheel(self,event):
        w=self.winfo_containing(event.x_root,event.y_root)
        on_cvs=False; n=w
        while n:
            if hasattr(self,'_cvs') and n is self._cvs: on_cvs=True; break
            try:
                pp=n.winfo_parent()
                if not pp: break
                n=self.nametowidget(pp)
            except: break
        f=1.18 if event.delta>0 else 1/1.18
        if on_cvs:
            ex=event.x_root-self._cvs.winfo_rootx()
            ey=event.y_root-self._cvs.winfo_rooty()
            if self._viz3d:
                if self._3sc is None: return
                self._3tx=ex+(self._3tx-ex)*f; self._3ty=ey+(self._3ty-ey)*f
                self._3sc*=f
            else:
                if self._ts is None: return
                self._tx=ex+(self._tx-ex)*f; self._ty=ey+(self._ty-ey)*f
                self._ts*=f
            self._draw()
        elif hasattr(self,'_sf'):
            self._sf.canvas.yview_scroll(-1*(event.delta//120),'units')

    # ── Построение UI ─────────────────────────────────────────────────────────
    def _build(self):
        root=tk.Frame(self,bg=BG); root.pack(fill='both',expand=True,padx=10,pady=10)
        left=tk.Frame(root,bg=BG,width=305)
        left.pack(side='left',fill='y'); left.pack_propagate(False)
        self._sf=ScrollFrame(left); self._sf.pack(fill='both',expand=True)
        self._build_left(self._sf.inner)
        tk.Frame(root,bg=BORDER,width=1).pack(side='left',fill='y',padx=8)
        right=tk.Frame(root,bg=BG); right.pack(side='left',fill='both',expand=True)
        self._build_right(right)

    def _build_left(self,p):
        c=section(p,'Контроллер',color='#c06820')
        ttk.Radiobutton(c,text='Mach3  (.tap)',variable=self.vCtrl,value='mach3').pack(anchor='w')
        ttk.Radiobutton(c,text='Fanuc / Haas  (.nc)',variable=self.vCtrl,value='fanuc').pack(anchor='w')

        c=section(p,'Программа')
        le(c,'Название:',self.vName,0,w=16)
        le(c,'Инструмент T:',self.vTool,1,w=5)
        le(c,'Обороты S:',self.vRpm,2,w=7)

        c=section(p,'Форма')
        ttk.Radiobutton(c,text='Окружность',variable=self.vShape,
            value='circle',command=self._on_shape).pack(anchor='w')
        ttk.Radiobutton(c,text='Квадрат',variable=self.vShape,
            value='square',command=self._on_shape).pack(anchor='w')
        self._shape_c=tk.Frame(c,bg=SURF); self._shape_c.pack(fill='x',pady=(6,0))

        c=section(p,'Тип обработки',color='#7060c0')
        ttk.Radiobutton(c,text='По контуру изнутри',variable=self.vMtype,
            value='contour_in',command=self._on_mtype).pack(anchor='w')
        ttk.Radiobutton(c,text='По контуру снаружи',variable=self.vMtype,
            value='contour_out',command=self._on_mtype).pack(anchor='w')
        ttk.Radiobutton(c,text='Торцевое (весь карман)',variable=self.vMtype,
            value='face',command=self._on_mtype).pack(anchor='w')
        self._mtype_c=tk.Frame(c,bg=SURF); self._mtype_c.pack(fill='x',pady=(6,0))

        c=section(p,'Сетка / Позиция')
        le(c,'X 1-го центра:',self.vCx1,0,unit='мм')
        le(c,'Y 1-го центра:',self.vCy1,1,unit='мм')
        le(c,'Шаг X:',self.vSx,2,unit='мм')
        le(c,'Шаг Y:',self.vSy,3,unit='мм')
        le(c,'Кол-во X:',self.vNx,4,w=5)
        le(c,'Кол-во Y:',self.vNy,5,w=5)
        self._lbl_count=tk.Label(c,text='',bg=SURF,fg=ACCENT,font=BOLD)
        self._lbl_count.grid(row=6,column=0,columnspan=3,sticky='w',pady=(6,2))

        c=section(p,'Глубина',color='#5070a0')
        le(c,'Z безопасная:',self.vZs,0,unit='мм')
        le(c,'Z поверхность:',self.vZsurf,1,unit='мм')
        le(c,'Z глубина общая:',self.vZd,2,unit='мм')
        le(c,'Z за проход:',self.vZstep,3,unit='мм')
        self._lbl_passes=tk.Label(c,text='',bg=SURF,fg='#8080c0',font=UI)
        self._lbl_passes.grid(row=4,column=0,columnspan=3,sticky='w',pady=(4,2))

        c=section(p,'Подачи')
        le(c,'Подача Z (погружение):',self.vFz,0,unit='мм/мин')
        le(c,'Подача XY (контур):',self.vFxy,1,unit='мм/мин')
        tk.Frame(p,bg=BG,height=20).pack()

    def _build_right(self,parent):
        bar=tk.Frame(parent,bg=ELEV,height=38)
        bar.pack(fill='x'); bar.pack_propagate(False)
        tk.Frame(bar,bg=SUCCESS,width=3).pack(side='left',fill='y')
        tk.Label(bar,text='  G-код Генератор',bg=ELEV,fg=TEXT,font=BOLD).pack(side='left',padx=4)
        ttk.Button(bar,text='  Сохранить  ',style='Save.TButton',
            command=self._save).pack(side='right',padx=8,pady=4)
        nb=ttk.Notebook(parent); nb.pack(fill='both',expand=True,pady=(4,0))

        # ── Таб G-код
        tc=tk.Frame(nb,bg=CODEBG); nb.add(tc,text='   G-код   ')
        sy=ttk.Scrollbar(tc,orient='vertical'); sx=ttk.Scrollbar(tc,orient='horizontal')
        self._txt=tk.Text(tc,bg=CODEBG,fg=CODEFG,font=MONO,relief='flat',bd=0,
            padx=10,pady=8,wrap='none',state='disabled',insertbackground=TEXT,
            selectbackground='#2a2a4a',yscrollcommand=sy.set,xscrollcommand=sx.set)
        sy.configure(command=self._txt.yview); sx.configure(command=self._txt.xview)
        sy.pack(side='right',fill='y'); sx.pack(side='bottom',fill='x')
        self._txt.pack(fill='both',expand=True)

        # ── Таб Траектория
        tv=tk.Frame(nb,bg=BG); nb.add(tv,text='   Траектория   ')
        # Тулбар с переключателем 2D/3D
        tbar=tk.Frame(tv,bg='#0e0e20',height=30); tbar.pack(fill='x'); tbar.pack_propagate(False)
        self._btn2d=ttk.Button(tbar,text='2D',style='TogOn.TButton',command=lambda:self._set_viz(False))
        self._btn3d=ttk.Button(tbar,text='3D',style='Tog.TButton', command=lambda:self._set_viz(True))
        self._btn2d.pack(side='left',padx=(8,0),pady=3)
        self._btn3d.pack(side='left',padx=(2,0),pady=3)
        self._hint=tk.Label(tbar,text='  колесо=зум  ср.кнопка=пан  2×клик=вписать',
            bg='#0e0e20',fg='#2a2a55',font=('Segoe UI',7))
        self._hint.pack(side='left',padx=12)
        # Единый канвас
        self._cvs=tk.Canvas(tv,bg=CODEBG,highlightthickness=0,bd=0)
        self._cvs.pack(fill='both',expand=True)
        self._cvs.bind('<Configure>',       lambda _:self._draw())
        self._cvs.bind('<ButtonPress-1>',   self._lmb_dn)
        self._cvs.bind('<B1-Motion>',       self._lmb_mv)
        self._cvs.bind('<ButtonRelease-1>', self._lmb_up)
        self._cvs.bind('<ButtonPress-2>',   self._mmb_dn)
        self._cvs.bind('<B2-Motion>',       self._mmb_mv)
        self._cvs.bind('<ButtonRelease-2>', lambda _:(setattr(self,'_ds',None),
                        setattr(self,'_3pr',None),self._cvs.configure(cursor='')))
        self._cvs.bind('<Double-Button-1>', lambda _:self._view_reset())
        nb.bind('<<NotebookTabChanged>>',    lambda _:self._draw())

    # ── Динамические секции ───────────────────────────────────────────────────
    def _on_shape(self,*_):
        for w in self._shape_c.winfo_children(): w.destroy()
        le(self._shape_c,'Диаметр:' if self.vShape.get()=='circle' else 'Сторона:',
           self.vDiam if self.vShape.get()=='circle' else self.vSide,0,unit='мм')

    def _on_mtype(self,*_):
        for w in self._mtype_c.winfo_children(): w.destroy()
        le(self._mtype_c,'Диаметр фрезы:',self.vTd,0,unit='мм')
        if self.vMtype.get()=='face':
            le(self._mtype_c,'Перекрытие:',self.vOverlap,1,w=5,unit='%')

    def _set_viz(self,mode3d):
        self._viz3d=mode3d
        self._btn2d.configure(style='TogOn.TButton' if not mode3d else 'Tog.TButton')
        self._btn3d.configure(style='TogOn.TButton' if mode3d else 'Tog.TButton')
        hint='  ЛКМ=вращение  колесо=зум  ср.кнопка=пан  2×клик=сброс' \
             if mode3d else '  ЛКМ=пан  колесо=зум  2×клик=вписать'
        self._hint.configure(text=hint)
        if mode3d: self._3sc=None
        else:      self._ts=None
        self._draw()

    # ── Мышь: ЛКМ ─────────────────────────────────────────────────────────────
    def _lmb_dn(self,e):
        if self._viz3d:
            self._3dr=(e.x,e.y); self._3daz=self._3az; self._3del=self._3el
        else:
            self._ds=(e.x,e.y); self._dtx=self._tx; self._dty=self._ty
            self._cvs.configure(cursor='fleur')
    def _lmb_mv(self,e):
        if self._viz3d:
            if not self._3dr: return
            dx=e.x-self._3dr[0]; dy=e.y-self._3dr[1]
            self._3az=self._3daz+math.radians(dx*0.5)
            self._3el=max(math.radians(-5),min(math.radians(85),
                          self._3del-math.radians(dy*0.4)))
            self._draw()
        else:
            if not self._ds: return
            self._tx=self._dtx+(e.x-self._ds[0])
            self._ty=self._dty+(e.y-self._ds[1]); self._draw()
    def _lmb_up(self,e):
        self._3dr=None; self._ds=None; self._cvs.configure(cursor='')

    # ── Мышь: ср.кнопка (пан всегда) ─────────────────────────────────────────
    def _mmb_dn(self,e):
        self._cvs.configure(cursor='fleur')
        if self._viz3d: self._3pr=(e.x,e.y); self._3dtx=self._3tx; self._3dty=self._3ty
        else:           self._ds=(e.x,e.y);  self._dtx=self._tx;   self._dty=self._ty
    def _mmb_mv(self,e):
        if self._viz3d:
            if not self._3pr: return
            self._3tx=self._3dtx+(e.x-self._3pr[0])
            self._3ty=self._3dty+(e.y-self._3pr[1]); self._draw()
        else:
            if not self._ds: return
            self._tx=self._dtx+(e.x-self._ds[0])
            self._ty=self._dty+(e.y-self._ds[1]); self._draw()

    def _view_reset(self):
        if self._viz3d: self._3az=math.radians(35); self._3el=math.radians(40); self._3sc=None
        else:           self._ts=None
        self._draw()

    # ── Параметры ─────────────────────────────────────────────────────────────
    def _sched(self,*_):
        if self._aid: self.after_cancel(self._aid)
        self._aid=self.after(120,self._refresh)

    def _params(self):
        def f(v):
            try: return float(v.get())
            except: return 0.
        def i(v):
            try: return max(1,int(v.get()))
            except: return 1
        return dict(
            name=self.vName.get() or 'ПРОГРАММА',
            tool=i(self.vTool),rpm=f(self.vRpm),ctrl=self.vCtrl.get(),
            shape=self.vShape.get(),mtype=self.vMtype.get(),
            diam=f(self.vDiam),side=f(self.vSide),
            td=f(self.vTd),overlap=f(self.vOverlap),
            cx1=f(self.vCx1),cy1=f(self.vCy1),
            sx=f(self.vSx),sy=f(self.vSy),nx=i(self.vNx),ny=i(self.vNy),
            zs=f(self.vZs),zsurf=f(self.vZsurf),zd=f(self.vZd),zstep=f(self.vZstep),
            fz=f(self.vFz),fxy=f(self.vFxy),
        )

    def _refresh(self):
        if not hasattr(self,'_txt'): return
        p=self._params()
        try:
            nx,ny=p['nx'],p['ny']
            self._lbl_count.configure(text=f'Итого: {nx}×{ny} = {nx*ny} фигур')
        except: pass
        try:
            lvls=z_levels(p)
            self._lbl_passes.configure(text=f'{len(lvls)} прох.: {lvls[0]:.2f} → {lvls[-1]:.2f}')
        except: pass
        code=generate(p)
        self._txt.configure(state='normal')
        self._txt.delete('1.0','end')
        self._txt.insert('1.0',code)
        highlight(self._txt)
        self._txt.configure(state='disabled')
        # Инвалидировать кеши
        self._ts=None; self._3sc=None
        try: self._path_cache=gen3d_batched(p)
        except: self._path_cache=[]
        self._draw()

    # ── Отрисовка (диспетчер) ─────────────────────────────────────────────────
    def _draw(self):
        if self._in_draw or not hasattr(self,'_cvs'): return
        self._in_draw=True
        try:
            if self._viz3d: self._draw3d()
            else:           self._draw2d()
        finally:
            self._in_draw=False

    # ── 2D ───────────────────────────────────────────────────────────────────
    def _draw2d(self):
        cvs=self._cvs; W=cvs.winfo_width(); H=cvs.winfo_height()
        if W<50 or H<50: return
        cvs.delete('all'); cvs.configure(bg=CODEBG)
        p=self._params()
        centers=[(p['cx1']+col*p['sx'],p['cy1']+row*p['sy'])
                 for row in range(max(1,p['ny'])) for col in range(max(1,p['nx']))]
        if not centers: return
        rp=(p['diam'] if p['shape']=='circle' else p['side'])/2
        t=p['td']/2
        if p['mtype']=='contour_in': rp=max(.5,rp-t)
        elif p['mtype']=='contour_out': rp+=t

        if self._ts is None:
            xs=[c[0] for c in centers]; ys=[c[1] for c in centers]
            mg=rp+max(10.,rp*.3)
            x0=min(min(xs)-mg,-10); x1=max(max(xs)+mg,10)
            y0=min(min(ys)-mg,-10); y1=max(max(ys)+mg,10)
            PAD=45; ww=x1-x0 or 1; wh=y1-y0 or 1
            ts=min((W-2*PAD)/ww,(H-2*PAD)/wh)
            self._ts=ts; self._tx=W/2-(x0+x1)/2*ts; self._ty=H/2+(y0+y1)/2*ts

        ts=self._ts; tx=self._tx; ty=self._ty
        wx=lambda x:tx+x*ts; wy=lambda y:ty-y*ts

        step=_nice_step(min(W,H)/ts/6)
        vx0=(0-tx)/ts; vx1=(W-tx)/ts; vy0=(ty-H)/ts; vy1=ty/ts
        gx=math.floor(vx0/step)*step
        while gx<=vx1:
            px=wx(gx); cvs.create_line(px,0,px,H,fill='#161628',width=1)
            cvs.create_text(px,H-10,text=f'{gx:.0f}',fill='#2e2e58',font=('Segoe UI',7))
            gx+=step
        gy=math.floor(vy0/step)*step
        while gy<=vy1:
            py=wy(gy); cvs.create_line(0,py,W,py,fill='#161628',width=1)
            cvs.create_text(12,py,text=f'{gy:.0f}',fill='#2e2e58',font=('Segoe UI',7),anchor='w')
            gy+=step
        if vx0<=0<=vx1:
            ax=wx(0); cvs.create_line(ax,0,ax,H,fill='#222245',width=1)
        if vy0<=0<=vy1:
            ay=wy(0); cvs.create_line(0,ay,W,ay,fill='#222245',width=1)

        CLR='#5b84ff'; ARW=SUCCESS
        prev=(0.,0.)
        mtype=p['mtype']
        for i,(fcx,fcy) in enumerate(centers):
            sp=(fcx+rp,fcy) if p['shape']=='circle' else (fcx-rp,fcy-rp)
            cvs.create_line(wx(prev[0]),wy(prev[1]),wx(sp[0]),wy(sp[1]),
                fill='#252545',width=1,dash=(5,4))
            prev=sp
            if p['shape']=='circle':
                if mtype=='face':
                    step_r=max(.5,p['td']*(p['overlap']/100)); r=t
                    while r<=rp+.001:
                        r2=min(r,rp)
                        cvs.create_oval(wx(fcx-r2),wy(fcy+r2),wx(fcx+r2),wy(fcy-r2),
                            outline=CLR,width=1 if r<rp else 2); r+=step_r
                else:
                    cvs.create_oval(wx(fcx-rp),wy(fcy+rp),wx(fcx+rp),wy(fcy-rp),
                        outline=CLR,width=2)
                    _arrow(cvs,wx(fcx),wy(fcy+rp),0,col=ARW)
            else:
                if mtype=='face':
                    step_h=max(.5,p['td']*(p['overlap']/100)); h=t
                    while h<=rp+.001:
                        h2=min(h,rp)
                        cvs.create_rectangle(wx(fcx-h2),wy(fcy+h2),wx(fcx+h2),wy(fcy-h2),
                            outline=CLR,width=1 if h<rp else 2); h+=step_h
                else:
                    cvs.create_rectangle(wx(fcx-rp),wy(fcy+rp),wx(fcx+rp),wy(fcy-rp),
                        outline=CLR,width=2)
            cxp,cyp=wx(fcx),wy(fcy)
            cvs.create_line(cxp-4,cyp,cxp+4,cyp,fill='#303060',width=1)
            cvs.create_line(cxp,cyp-4,cxp,cyp+4,fill='#303060',width=1)
            cvs.create_text(cxp,cyp,text=str(i+1),fill='#4a4a90',font=('Segoe UI',7,'bold'))

        opx,opy=wx(0),wy(0)
        cvs.create_oval(opx-3,opy-3,opx+3,opy+3,fill=SUCCESS,outline='')
        cvs.create_text(opx+10,opy-10,text='0,0',fill=SUCCESS,font=('Segoe UI',7),anchor='w')

        bar_px=step*ts; bx2=W-45; bx1=bx2-bar_px; by=H-26
        if bar_px>20:
            cvs.create_line(bx1,by,bx2,by,fill='#4a4a80',width=2)
            cvs.create_line(bx1,by-4,bx1,by+4,fill='#4a4a80',width=1)
            cvs.create_line(bx2,by-4,bx2,by+4,fill='#4a4a80',width=1)
            cvs.create_text((bx1+bx2)/2,by-10,text=f'{step:.0f} мм',
                fill='#4a4a80',font=('Segoe UI',7))

    # ── 3D ───────────────────────────────────────────────────────────────────
    def _draw3d(self):
        cvs=self._cvs; W=cvs.winfo_width(); H=cvs.winfo_height()
        if W<50 or H<50: return
        cvs.delete('all'); cvs.configure(bg='#070710')
        p=self._params()
        az=self._3az; el=self._3el
        batches=self._path_cache or []

        # Авто-вписывание
        if self._3sc is None and batches:
            all_pts=[(x,y,z) for _,_,pts in batches for x,y,z in pts]
            sxs=[proj3d(x,y,z,az,el,1,0,0)[0] for x,y,z in all_pts]
            szs=[proj3d(x,y,z,az,el,1,0,0)[1] for x,y,z in all_pts]
            sx0,sx1=min(sxs),max(sxs); sz0,sz1=min(szs),max(szs)
            PAD=70
            sc=min((W-2*PAD)/max(sx1-sx0,0.1),(H-2*PAD)/max(sz1-sz0,0.1))
            self._3sc=sc; self._3tx=W/2-(sx0+sx1)/2*sc; self._3ty=H/2+(sz0+sz1)/2*sc
        if self._3sc is None: self._3sc=8.; self._3tx=W/2; self._3ty=H/2

        sc=self._3sc; tx=self._3tx; ty=self._3ty
        def pr(x,y,z): return proj3d(x,y,z,az,el,sc,tx,ty)

        # Сетка на поверхности
        zsurf=p['zsurf']; zd=p['zd']
        rf=(p['diam'] if p['shape']=='circle' else p['side'])/2
        nx=max(1,p['nx']); ny=max(1,p['ny'])
        gx0=p['cx1']-rf-15; gx1=p['cx1']+(nx-1)*p['sx']+rf+15
        gy0=p['cy1']-rf-15; gy1=p['cy1']+(ny-1)*p['sy']+rf+15
        gs=max(5.,_nice_step(max(gx1-gx0,gy1-gy0)/8))
        gx=math.floor(gx0/gs)*gs
        while gx<=gx1:
            a=pr(gx,gy0,zsurf); b=pr(gx,gy1,zsurf)
            cvs.create_line(a[0],a[1],b[0],b[1],fill='#141428',width=1); gx+=gs
        gy=math.floor(gy0/gs)*gs
        while gy<=gy1:
            a=pr(gx0,gy,zsurf); b=pr(gx1,gy,zsurf)
            cvs.create_line(a[0],a[1],b[0],b[1],fill='#141428',width=1); gy+=gs

        # Рамка поверхности
        corners2d=[(gx0,gy0),(gx1,gy0),(gx1,gy1),(gx0,gy1),(gx0,gy0)]
        for i in range(4):
            a=pr(corners2d[i][0],corners2d[i][1],zsurf)
            b=pr(corners2d[i+1][0],corners2d[i+1][1],zsurf)
            cvs.create_line(a[0],a[1],b[0],b[1],fill='#22225a',width=1)
        # Глубина
        for i in range(4):
            a=pr(corners2d[i][0],corners2d[i][1],zd)
            b=pr(corners2d[i+1][0],corners2d[i+1][1],zd)
            cvs.create_line(a[0],a[1],b[0],b[1],fill='#1c1c40',width=1,dash=(3,5))
        for ax,ay in corners2d[:4]:
            a=pr(ax,ay,zsurf); b=pr(ax,ay,zd)
            cvs.create_line(a[0],a[1],b[0],b[1],fill='#1c1c40',width=1,dash=(3,5))

        # Контуры фигур (ghost)
        SG=40
        for row in range(ny):
          for col in range(nx):
            fcx=p['cx1']+col*p['sx']; fcy=p['cy1']+row*p['sy']
            r_=rf
            if p['shape']=='circle':
                pts=[pr(fcx+r_*math.cos(2*math.pi*i/SG),
                        fcy+r_*math.sin(2*math.pi*i/SG),zsurf) for i in range(SG+1)]
            else:
                pts=[pr(fcx+dx*r_,fcy+dy*r_,zsurf)
                     for dx,dy in [(-1,-1),(1,-1),(1,1),(-1,1),(-1,-1)]]
            flat=[v for pt in pts for v in pt]
            if len(flat)>=4: cvs.create_line(flat,fill='#22225a',width=1)

        # Путь инструмента (из кеша)
        zr=zsurf-zd if zsurf!=zd else 1
        def col3(z,k):
            if k=='r': return None
            t_=max(0.,min(1.,(zsurf-z)/zr))
            if k=='f': return f'#{220:02x}{max(0,int(180-80*t_)):02x}{int(40+60*t_):02x}'
            ri=int(30+90*t_); gi=int(220-180*t_)
            return f'#{ri:02x}{gi:02x}ff'

        for kind,z_mid,pts in batches:
            if not pts: continue
            projected=[pr(x,y,z) for x,y,z in pts]
            flat=[v for pt in projected for v in pt]
            if len(flat)<4: continue
            if kind=='r':
                cvs.create_line(flat,fill='#181838',width=1,dash=(4,6))
            elif kind=='h':
                c=col3(z_mid,'h')
                cvs.create_line(flat,fill=c,width=2,smooth=True)
            else:
                c=col3(z_mid,'f')
                cvs.create_line(flat,fill=c,width=3,smooth=True)

        # Оси координат
        ax0,ay0=58,H-52
        for (dx,dy,dz),col,lbl in [(1,0,0,'#ff5555','X'),(0,1,0,'#55cc55','Y'),(0,0,1,'#5599ff','Z')]:
            ex,ey=proj3d(dx*36,dy*36,dz*36,az,el,1,ax0,ay0)
            cvs.create_line(ax0,ay0,ex,ey,fill=col,width=2)
            cvs.create_text(ex+(ex-ax0)*.25,ey+(ey-ay0)*.25,
                text=lbl,fill=col,font=('Segoe UI',8,'bold'))

        cvs.create_text(W-6,H-6,
            text=f'az {math.degrees(az):.0f}°  el {math.degrees(el):.0f}°',
            fill='#252550',font=('Segoe UI',7),anchor='se')

    # ── Сохранение ────────────────────────────────────────────────────────────
    def _save(self):
        ctrl=self.vCtrl.get()
        if ctrl=='mach3':
            ft=[('Mach3 TAP','*.tap'),('TXT','*.txt'),('Все','*.*')]; ext='.tap'
        else:
            ft=[('G-код (.nc)','*.nc'),('Все','*.*')]; ext='.nc'
        path=filedialog.asksaveasfilename(
            title='Сохранить G-код',defaultextension=ext,filetypes=ft,
            initialfile=self.vName.get() or 'ПРОГРАММА',
            initialdir=r'C:\Users\ilya\ЧПУ программы\Дом')
        if not path: return
        with open(path,'w',encoding='utf-8') as fh:
            fh.write(generate(self._params()))


if __name__=='__main__':
    App().mainloop()
