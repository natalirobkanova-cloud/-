#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CNC Программатор v2.0 — тёмная тема + группы параметров"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
import json, os, re, sys
from meters_module import MetersFrame

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_FILE = os.path.join(BASE_DIR, 'cnc_templates.json')
APP_TITLE = "CNC Программатор v2.0"

# ── Цвета ────────────────────────────────────────────────────────────────────
BG      = '#12121e'
SURF    = '#1c1c2e'
ELEV    = '#26263e'
BORDER  = '#38385e'
TEXT    = '#dcdcf0'
SUBT    = '#6868a0'
ACCENT  = '#5b72cc'
SUCCESS = '#4db870'
DANGER  = '#d95050'
INP     = '#202038'
CODEBG  = '#0a0a18'
CODEFG  = '#c8c8e8'

GROUP_PALETTE = [
    '#1a3560', '#3a1a60', '#184030', '#402800',
    '#401818', '#184040', '#383800', '#301840',
]

MONO = ('Courier New', 9)
UI   = ('Segoe UI', 9)
BOLD = ('Segoe UI', 9, 'bold')

# ── Тема ─────────────────────────────────────────────────────────────────────

def setup_theme(root):
    s = ttk.Style(root)
    s.theme_use('clam')
    root.configure(bg=BG)

    BTN   = '#2e2e4a'   # кнопки в норме — чуть светлее ELEV
    BTN_H = '#3c3c5c'   # кнопки при наведении
    ENT_F = '#2c2c52'   # поле ввода при фокусе

    # Базовые: убиваем все 3D-рамки clam через lightcolor/darkcolor
    s.configure('.', background=BG, foreground=TEXT, font=UI,
                bordercolor=BG, lightcolor=BG, darkcolor=BG,
                troughcolor=SURF, selectbackground=ACCENT, selectforeground='#ffffff',
                relief='flat', borderwidth=0)

    s.configure('TFrame', background=BG)
    s.configure('TLabelframe', background=BG, bordercolor=BORDER, relief='flat',
                borderwidth=1, lightcolor=BORDER, darkcolor=BORDER)
    s.configure('TLabelframe.Label', background=BG, foreground=SUBT, font=BOLD)
    s.configure('TLabel', background=BG, foreground=TEXT)

    # Кнопки — без рамки, выделение цветом
    s.configure('TButton', background=BTN, foreground=TEXT, relief='flat',
                padding=(10, 5), borderwidth=0, lightcolor=BTN, darkcolor=BTN)
    s.map('TButton',
          background=[('active', BTN_H), ('pressed', ACCENT), ('disabled', SURF)],
          lightcolor=[('active', BTN_H), ('pressed', ACCENT)],
          darkcolor=[('active', BTN_H), ('pressed', ACCENT)],
          foreground=[('disabled', SUBT)])

    s.configure('Accent.TButton', background=ACCENT, foreground='#ffffff', relief='flat',
                padding=(10, 5), borderwidth=0, lightcolor=ACCENT, darkcolor=ACCENT)
    s.map('Accent.TButton',
          background=[('active', '#6b82dc'), ('pressed', '#4a62bb')],
          lightcolor=[('active', '#6b82dc')], darkcolor=[('active', '#6b82dc')])

    s.configure('Danger.TButton', background='#3a1010', foreground='#e06060', relief='flat',
                padding=(10, 5), borderwidth=0, lightcolor='#3a1010', darkcolor='#3a1010')
    s.map('Danger.TButton',
          background=[('active', '#501818')],
          lightcolor=[('active', '#501818')], darkcolor=[('active', '#501818')],
          foreground=[('active', '#ff8080')])

    # Поля ввода — без рамки, цвет при фокусе
    s.configure('TEntry', fieldbackground=INP, foreground=TEXT,
                bordercolor=INP, insertcolor=TEXT, relief='flat',
                padding=(6, 4), borderwidth=0, lightcolor=INP, darkcolor=INP)
    s.map('TEntry',
          fieldbackground=[('focus', ENT_F)],
          lightcolor=[('focus', ENT_F)], darkcolor=[('focus', ENT_F)])

    # Combobox
    s.configure('TCombobox', fieldbackground=INP, background=BTN,
                foreground=TEXT, arrowcolor=TEXT, bordercolor=INP, relief='flat',
                padding=(6, 4), borderwidth=0, lightcolor=INP, darkcolor=INP)
    s.map('TCombobox',
          fieldbackground=[('readonly', INP)], background=[('readonly', BTN)],
          lightcolor=[('focus', ENT_F)], darkcolor=[('focus', ENT_F)])

    # Notebook — без рамки вокруг содержимого
    s.configure('TNotebook', background=BG, bordercolor=BG, relief='flat',
                borderwidth=0, lightcolor=BG, darkcolor=BG, tabmargins=0)
    s.configure('TNotebook.Tab', background=SURF, foreground=SUBT,
                padding=(18, 7), font=UI, borderwidth=0,
                lightcolor=SURF, darkcolor=SURF)
    s.map('TNotebook.Tab',
          background=[('selected', ELEV), ('active', '#252545')],
          foreground=[('selected', TEXT), ('active', '#a0a0c8')],
          lightcolor=[('selected', ELEV), ('active', '#252545')],
          darkcolor=[('selected', ELEV), ('active', '#252545')])

    # Treeview
    s.configure('Treeview', background=SURF, foreground=TEXT, fieldbackground=SURF,
                bordercolor=SURF, rowheight=26, font=UI, relief='flat', borderwidth=0,
                lightcolor=SURF, darkcolor=SURF)
    s.configure('Treeview.Heading', background=ELEV, foreground=SUBT, relief='flat',
                font=BOLD, borderwidth=0, lightcolor=ELEV, darkcolor=ELEV)
    s.map('Treeview',
          background=[('selected', ACCENT)], foreground=[('selected', '#ffffff')])

    # Scrollbar
    s.configure('TScrollbar', background=ELEV, troughcolor=SURF,
                bordercolor=SURF, arrowcolor=SUBT, relief='flat', width=10, borderwidth=0,
                lightcolor=ELEV, darkcolor=ELEV)
    s.map('TScrollbar',
          background=[('active', '#4a4a70')],
          lightcolor=[('active', '#4a4a70')], darkcolor=[('active', '#4a4a70')])

    s.configure('TSeparator', background=BORDER)
    s.configure('TPanedwindow', background=BORDER)

# ── Хранилище ────────────────────────────────────────────────────────────────

class TemplateStore:
    def __init__(self):
        self.templates = []
        self._load()

    def _load(self):
        if os.path.exists(TEMPLATES_FILE):
            try:
                with open(TEMPLATES_FILE, 'r', encoding='utf-8') as f:
                    self.templates = json.load(f)
                for t in self.templates:
                    if 'groups' not in t:
                        t['groups'] = []
            except Exception:
                self.templates = []

    def save(self):
        with open(TEMPLATES_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.templates, f, ensure_ascii=False, indent=2)

    def _next_id(self):
        return max((t['id'] for t in self.templates), default=0) + 1

    def add(self):
        t = {'id': self._next_id(), 'name': 'Новый шаблон', 'o_number': 'O0001',
             'code': '%\nO0001 (НАЗВАНИЕ)\n\nG90 G54\nM30\n%',
             'variables': [], 'groups': []}
        self.templates.append(t)
        self.save()
        return t

    def delete(self, tid):
        self.templates = [t for t in self.templates if t['id'] != tid]
        self.save()

    def get(self, tid):
        return next((t for t in self.templates if t['id'] == tid), None)

    def update(self, tmpl):
        for i, t in enumerate(self.templates):
            if t['id'] == tmpl['id']:
                self.templates[i] = tmpl
                break
        self.save()

    def generate(self, tmpl, values):
        code = tmpl['code']
        for var in tmpl['variables']:
            n = var['num']
            val = values.get(str(n), var['default'])
            code = code.replace(f'{{{{{n}}}}}', str(val))
        return code

    def get_var(self, tmpl, num):
        return next((v for v in tmpl['variables'] if v['num'] == num), None)

    def get_ungrouped(self, tmpl):
        grouped = {n for g in tmpl.get('groups', []) for n in g['var_nums']}
        return [v for v in tmpl['variables'] if v['num'] not in grouped]

    def next_group_id(self, tmpl):
        return max((g['id'] for g in tmpl.get('groups', [])), default=0) + 1

# ── Диалог переменной ────────────────────────────────────────────────────────

class VarDialog(tk.Toplevel):
    def __init__(self, parent, callback, existing=None):
        super().__init__(parent)
        self.configure(bg=BG)
        self.callback = callback
        self.title('Переменная')
        self.resizable(False, False)
        self.grab_set()
        self.focus_set()
        d = existing or {'num': 101, 'label': 'Параметр', 'unit': 'мм', 'default': '0.0'}
        self._v = {}
        rows = [('Номер (#NNN):', 'num', str(d['num'])),
                ('Метка (рус.):', 'label', d['label']),
                ('Единицы:',      'unit',  d.get('unit', 'мм')),
                ('По умолчанию:', 'default', str(d['default']))]
        for i, (lbl, key, val) in enumerate(rows):
            ttk.Label(self, text=lbl).grid(row=i, column=0, sticky='w', padx=14, pady=6)
            sv = tk.StringVar(value=val)
            ttk.Entry(self, textvariable=sv, width=28).grid(row=i, column=1, padx=14, pady=6)
            self._v[key] = sv
        ttk.Button(self, text='  OK  ', style='Accent.TButton',
                   command=self._ok).grid(row=len(rows), column=0, columnspan=2, pady=12)
        self.bind('<Return>', lambda _: self._ok())

    def _ok(self):
        try:
            num = int(self._v['num'].get())
        except ValueError:
            messagebox.showerror('Ошибка', 'Номер должен быть целым числом.', parent=self)
            return
        self.callback({'num': num, 'label': self._v['label'].get(),
                       'unit': self._v['unit'].get(), 'default': self._v['default'].get()})
        self.destroy()

# ── Диалог группы ────────────────────────────────────────────────────────────

class GroupDialog(tk.Toplevel):
    def __init__(self, parent, callback, existing=None):
        super().__init__(parent)
        self.configure(bg=BG)
        self.callback = callback
        self.title('Группа параметров')
        self.resizable(False, False)
        self.grab_set()
        self.focus_set()
        d = existing or {'name': 'Новая группа', 'color': GROUP_PALETTE[0]}
        self._color = d.get('color', GROUP_PALETTE[0])
        self._name = tk.StringVar(value=d['name'])

        ttk.Label(self, text='Название:').grid(row=0, column=0, sticky='w', padx=14, pady=8)
        ttk.Entry(self, textvariable=self._name, width=28).grid(row=0, column=1, padx=14, pady=8)

        ttk.Label(self, text='Цвет:').grid(row=1, column=0, sticky='w', padx=14, pady=8)
        cf = tk.Frame(self, bg=BG)
        cf.grid(row=1, column=1, sticky='w', padx=14, pady=8)

        self._swatch = tk.Label(cf, bg=self._color, width=6, height=1,
                                 relief='flat', cursor='hand2', text=' ')
        self._swatch.pack(side='left', padx=(0, 6))
        self._swatch.bind('<Button-1>', self._pick)

        for c in GROUP_PALETTE:
            sw = tk.Label(cf, bg=c, width=3, height=1, relief='flat', cursor='hand2')
            sw.pack(side='left', padx=1)
            sw.bind('<Button-1>', lambda e, col=c: self._set(col))

        ttk.Button(self, text='  OK  ', style='Accent.TButton',
                   command=self._ok).grid(row=2, column=0, columnspan=2, pady=12)
        self.bind('<Return>', lambda _: self._ok())

    def _pick(self, _):
        r = colorchooser.askcolor(color=self._color, parent=self, title='Цвет группы')
        if r and r[1]:
            self._set(r[1])

    def _set(self, c):
        self._color = c
        self._swatch.configure(bg=c)

    def _ok(self):
        name = self._name.get().strip()
        if not name:
            messagebox.showerror('Ошибка', 'Введите название.', parent=self)
            return
        self.callback({'name': name, 'color': self._color})
        self.destroy()

# ── Вспомогательный скроллируемый фрейм ─────────────────────────────────────

class ScrollFrame(tk.Frame):
    def __init__(self, parent, bg=BG, **kw):
        super().__init__(parent, bg=bg, **kw)
        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0)
        vsb = ttk.Scrollbar(self, orient='vertical', command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side='right', fill='y')
        self.canvas.pack(side='left', fill='both', expand=True)
        self.inner = tk.Frame(self.canvas, bg=bg)
        self._win = self.canvas.create_window((0, 0), window=self.inner, anchor='nw')
        self.inner.bind('<Configure>', lambda _: self.canvas.configure(
            scrollregion=self.canvas.bbox('all')))
        self.canvas.bind('<Configure>', lambda e: self.canvas.itemconfig(self._win, width=e.width))
        self.canvas.bind('<Enter>', lambda _: self.canvas.bind_all('<MouseWheel>', self._mw))
        self.canvas.bind('<Leave>', lambda _: self.canvas.unbind_all('<MouseWheel>'))
        self.inner.bind('<Enter>', lambda _: self.canvas.bind_all('<MouseWheel>', self._mw))
        self.inner.bind('<Leave>', lambda _: self.canvas.unbind_all('<MouseWheel>'))

    def _mw(self, e):
        self.canvas.yview_scroll(-1 * (e.delta // 120), 'units')

# ── Панель оператора ──────────────────────────────────────────────────────────

class OperatorPanel(ttk.Frame):
    def __init__(self, parent, store):
        super().__init__(parent)
        self.store = store
        self._tmpl = None
        self._entries = {}
        self._ids = []
        self._build()

    def _build(self):
        # ── Топ-бар ──
        top = tk.Frame(self, bg=SURF, pady=10)
        top.pack(fill='x')
        tk.Label(top, text='  Операция:', bg=SURF, fg=TEXT, font=BOLD).pack(side='left')
        self._cv = tk.StringVar()
        self._combo = ttk.Combobox(top, textvariable=self._cv, state='readonly', width=52)
        self._combo.pack(side='left', padx=8)
        self._combo.bind('<<ComboboxSelected>>', self._on_select)
        tk.Label(top, text='Станок:', bg=SURF, fg=TEXT).pack(side='left', padx=(16, 4))
        self._station = tk.StringVar(value='Haas / Fanuc')
        ttk.Combobox(top, textvariable=self._station,
                     values=['Haas / Fanuc', 'Litz'],
                     state='readonly', width=13).pack(side='left')
        ttk.Button(top, text='Сохранить файл…', style='Accent.TButton',
                   command=self._save).pack(side='right', padx=10)
        ttk.Button(top, text='Предпросмотр', command=self._do_preview).pack(side='right', padx=4)
        self._status = tk.Label(top, text='', bg=SURF, fg=SUCCESS)
        self._status.pack(side='right', padx=10)

        # ── Центр: параметры | превью ──
        pw = ttk.PanedWindow(self, orient='horizontal')
        pw.pack(fill='both', expand=True)

        lw = tk.Frame(pw, bg=BG)
        pw.add(lw, weight=1)
        self._sf = ScrollFrame(lw, bg=BG)
        self._sf.pack(fill='both', expand=True)

        rw = tk.Frame(pw, bg=BG)
        pw.add(rw, weight=1)
        tk.Label(rw, text='  Предпросмотр G-кода', bg=BG, fg=SUBT, font=BOLD).pack(anchor='w', pady=(6, 2))
        self._prev = tk.Text(rw, font=MONO, state='disabled',
                             bg=CODEBG, fg=CODEFG, wrap='none', relief='flat',
                             padx=8, pady=6, selectbackground=ACCENT)
        sc_y = ttk.Scrollbar(rw, command=self._prev.yview)
        sc_x = ttk.Scrollbar(rw, orient='horizontal', command=self._prev.xview)
        self._prev.configure(yscrollcommand=sc_y.set, xscrollcommand=sc_x.set)
        sc_x.pack(side='bottom', fill='x')
        sc_y.pack(side='right', fill='y')
        self._prev.pack(fill='both', expand=True, padx=8, pady=(0, 8))

    def refresh(self):
        self._ids = [t['id'] for t in self.store.templates]
        names = [f"{t['o_number']}  —  {t['name']}" for t in self.store.templates]
        self._combo['values'] = names
        if names and not self._cv.get():
            self._combo.current(0)
            self._load(self._ids[0])

    def _on_select(self, _):
        idx = self._combo.current()
        if 0 <= idx < len(self._ids):
            self._load(self._ids[idx])

    def _load(self, tid):
        self._tmpl = self.store.get(tid)
        self._entries.clear()
        for w in self._sf.inner.winfo_children():
            w.destroy()
        if not self._tmpl:
            return
        t = self._tmpl
        for group in t.get('groups', []):
            vars_in = [self.store.get_var(t, n) for n in group['var_nums']
                       if self.store.get_var(t, n)]
            if vars_in:
                self._render_group(group['name'], group.get('color', GROUP_PALETTE[0]), vars_in)
        ung = self.store.get_ungrouped(t)
        if ung:
            self._render_group('Без группы', ELEV, ung, dim=True)
        self._do_preview()

    def _render_group(self, name, color, variables, dim=False):
        inner = self._sf.inner
        wrap = tk.Frame(inner, bg=BG)
        wrap.pack(fill='x', padx=12, pady=(10, 0))

        # Затемнённая версия цвета для акцентной полосы
        dark = self._shade(color, 0.6)
        hdr = tk.Frame(wrap, bg=color)
        hdr.pack(fill='x')
        tk.Frame(hdr, bg=dark, width=5).pack(side='left', fill='y')
        tk.Label(hdr, text=f'  {name}', bg=color,
                 fg='#e0e8ff' if not dim else SUBT,
                 font=BOLD, pady=7, anchor='w').pack(side='left', fill='x', expand=True)

        for var in variables:
            row = tk.Frame(wrap, bg=SURF)
            row.pack(fill='x')
            tk.Frame(row, bg=dark if not dim else BORDER, width=5).pack(side='left', fill='y')
            tk.Label(row, text=f'  {var["label"]}', bg=SURF, fg=TEXT,
                     font=UI, width=30, anchor='w').pack(side='left', padx=(4, 0), pady=5)
            if var.get('unit'):
                tk.Label(row, text=var['unit'], bg=SURF, fg=SUBT, font=UI, width=5).pack(side='left')
            ent = ttk.Entry(row, width=14)
            ent.insert(0, str(var['default']))
            ent.pack(side='left', padx=8, pady=5)
            ent.bind('<KeyRelease>', lambda _: self._do_preview())
            self._entries[str(var['num'])] = ent

        tk.Frame(wrap, bg=BORDER, height=1).pack(fill='x')

    @staticmethod
    def _shade(h, f):
        try:
            r, g, b = int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16)
            return f'#{int(r*f):02x}{int(g*f):02x}{int(b*f):02x}'
        except Exception:
            return h

    def _do_preview(self):
        if not self._tmpl:
            return
        code = self.store.generate(self._tmpl, {k: e.get() for k, e in self._entries.items()})
        self._prev.configure(state='normal')
        self._prev.delete('1.0', 'end')
        self._prev.insert('1.0', code)
        self._prev.configure(state='disabled')

    def _save(self):
        if not self._tmpl:
            messagebox.showwarning('Нет шаблона', 'Выберите операцию.')
            return
        code = self.store.generate(self._tmpl, {k: e.get() for k, e in self._entries.items()})
        o = self._tmpl['o_number'].strip()
        if 'Litz' in self._station.get():
            path = filedialog.asksaveasfilename(initialfile=o, defaultextension='',
                filetypes=[('Программа Litz', ''), ('Все файлы', '*.*')])
        else:
            path = filedialog.asksaveasfilename(initialfile=f'{o}.nc', defaultextension='.nc',
                filetypes=[('NC файл', '*.nc'), ('Все файлы', '*.*')])
        if path:
            with open(path, 'w', encoding='ascii', errors='replace') as f:
                f.write(code)
            self._status.configure(text=f'✓  {os.path.basename(path)}')
            self.after(4000, lambda: self._status.configure(text=''))

# ── Панель конструктора ───────────────────────────────────────────────────────

class ConstructorPanel(ttk.Frame):
    def __init__(self, parent, store, on_change):
        super().__init__(parent)
        self.store     = store
        self.on_change = on_change
        self._cur_id   = None
        self._list_ids = []
        self._drag     = None
        self._build()
        self._refresh_list()

    def _build(self):
        pw = ttk.PanedWindow(self, orient='horizontal')
        pw.pack(fill='both', expand=True)

        # ── Левая: список ──
        left = tk.Frame(pw, bg=SURF, width=240)
        pw.add(left, weight=0)
        tk.Frame(left, bg=ELEV, height=36).pack(fill='x')
        tk.Label(left, text='  Шаблоны', bg=ELEV, fg=TEXT, font=BOLD).place(x=0, y=8)
        self._lb = tk.Listbox(left, bg=SURF, fg=TEXT, font=UI,
                              selectbackground=ACCENT, selectforeground='#fff',
                              borderwidth=0, highlightthickness=0,
                              activestyle='none', relief='flat')
        sc = ttk.Scrollbar(left, command=self._lb.yview)
        self._lb.configure(yscrollcommand=sc.set)
        sc.pack(side='right', fill='y')
        self._lb.pack(fill='both', expand=True, pady=(36, 0))
        self._lb.bind('<<ListboxSelect>>', self._on_list_sel)
        bb = tk.Frame(left, bg=SURF, pady=6)
        bb.pack(fill='x')
        ttk.Button(bb, text='＋', command=self._add_tmpl, width=4).pack(side='left', padx=6)
        ttk.Button(bb, text='✕', style='Danger.TButton',
                   command=self._del_tmpl, width=4).pack(side='left')

        # ── Правая: редактор ──
        right = tk.Frame(pw, bg=BG)
        pw.add(right, weight=1)

        hdr = tk.Frame(right, bg=SURF, pady=9)
        hdr.pack(fill='x')
        tk.Label(hdr, text='  Название:', bg=SURF, fg=TEXT).pack(side='left')
        self._name = tk.StringVar()
        ttk.Entry(hdr, textvariable=self._name, width=32).pack(side='left', padx=6)
        tk.Label(hdr, text='O-номер:', bg=SURF, fg=TEXT).pack(side='left', padx=(10, 0))
        self._onum = tk.StringVar()
        ttk.Entry(hdr, textvariable=self._onum, width=10).pack(side='left', padx=6)
        ttk.Button(hdr, text='💾  Сохранить шаблон', style='Accent.TButton',
                   command=self._save_tmpl).pack(side='right', padx=10)

        nb = ttk.Notebook(right)
        nb.pack(fill='both', expand=True, pady=4)

        # Вкладка G-код
        ct = tk.Frame(nb, bg=BG)
        nb.add(ct, text='  G-код  ')
        tb = tk.Frame(ct, bg=BG, pady=5)
        tb.pack(fill='x', padx=8)
        ttk.Button(tb, text='Извлечь переменные →', command=self._extract).pack(side='left')
        tk.Label(tb, text='  Найти #NNN = VALUE и добавить в список',
                 bg=BG, fg=SUBT).pack(side='left')
        self._code = tk.Text(ct, font=MONO, wrap='none', bg=CODEBG, fg=CODEFG,
                              insertbackground='white', relief='flat', padx=8, pady=6, undo=True,
                              selectbackground=ACCENT)
        scy = ttk.Scrollbar(ct, command=self._code.yview)
        scx = ttk.Scrollbar(ct, orient='horizontal', command=self._code.xview)
        self._code.configure(yscrollcommand=scy.set, xscrollcommand=scx.set)
        scx.pack(side='bottom', fill='x')
        scy.pack(side='right', fill='y')
        self._code.pack(fill='both', expand=True, padx=8, pady=(0, 8))

        # Вкладка Группы
        gt = tk.Frame(nb, bg=BG)
        nb.add(gt, text='  Группы  ')
        self._build_groups(gt)

        # Вкладка Переменные
        vt = tk.Frame(nb, bg=BG)
        nb.add(vt, text='  Переменные  ')
        self._build_vars(vt)

    def _build_groups(self, parent):
        tb = tk.Frame(parent, bg=BG, pady=6)
        tb.pack(fill='x', padx=8)
        ttk.Button(tb, text='＋ Группа', command=self._add_grp).pack(side='left')
        ttk.Button(tb, text='✎ Изменить', command=self._edit_grp).pack(side='left', padx=6)
        ttk.Button(tb, text='✕ Удалить', style='Danger.TButton',
                   command=self._del_grp).pack(side='left')
        tk.Label(tb, text='   ⠿ Перетащи переменную в нужную группу',
                 bg=BG, fg=SUBT).pack(side='left', padx=10)

        cols = ('label', 'unit', 'default')
        self._gt = ttk.Treeview(parent, columns=cols, show='tree headings', height=20)
        self._gt.heading('#0',      text='Переменная', anchor='w')
        self._gt.heading('label',   text='Метка', anchor='w')
        self._gt.heading('unit',    text='Ед.', anchor='center')
        self._gt.heading('default', text='По умолч.', anchor='center')
        self._gt.column('#0',      width=180, stretch=False)
        self._gt.column('label',   width=230)
        self._gt.column('unit',    width=60,  anchor='center')
        self._gt.column('default', width=90,  anchor='center')
        sc = ttk.Scrollbar(parent, command=self._gt.yview)
        self._gt.configure(yscrollcommand=sc.set)
        sc.pack(side='right', fill='y', padx=(0, 8))
        self._gt.pack(fill='both', expand=True, padx=8, pady=4)
        self._gt.bind('<ButtonPress-1>',  self._ds)
        self._gt.bind('<B1-Motion>',      self._dm)
        self._gt.bind('<ButtonRelease-1>', self._dd)

    def _build_vars(self, parent):
        tb = tk.Frame(parent, bg=BG, pady=6)
        tb.pack(fill='x', padx=8)
        ttk.Button(tb, text='＋ Добавить', command=self._add_var).pack(side='left')
        ttk.Button(tb, text='✕ Удалить',  command=self._del_var).pack(side='left', padx=6)
        ttk.Button(tb, text='↑', command=lambda: self._mv_var(-1), width=3).pack(side='left')
        ttk.Button(tb, text='↓', command=lambda: self._mv_var(1),  width=3).pack(side='left', padx=2)

        cols = ('num', 'label', 'unit', 'default')
        self._vt = ttk.Treeview(parent, columns=cols, show='headings', height=20)
        self._vt.heading('num',     text='#Переменная')
        self._vt.heading('label',   text='Метка (рус.)')
        self._vt.heading('unit',    text='Ед.')
        self._vt.heading('default', text='По умолч.')
        self._vt.column('num',     width=95,  anchor='center')
        self._vt.column('label',   width=250)
        self._vt.column('unit',    width=70,  anchor='center')
        self._vt.column('default', width=100, anchor='center')
        self._vt.bind('<Double-1>', self._edit_var)
        sc = ttk.Scrollbar(parent, command=self._vt.yview)
        self._vt.configure(yscrollcommand=sc.set)
        sc.pack(side='right', fill='y', padx=(0, 8))
        self._vt.pack(fill='both', expand=True, padx=8, pady=4)
        tk.Label(parent, text='В G-коде используйте  {{101}}  для переменной #101',
                 bg=BG, fg=SUBT).pack(pady=4)

    # ── Список шаблонов ──

    def _refresh_list(self):
        self._lb.delete(0, 'end')
        self._list_ids = []
        for t in self.store.templates:
            self._lb.insert('end', f"  {t['o_number']}  {t['name']}")
            self._list_ids.append(t['id'])

    def _on_list_sel(self, _):
        sel = self._lb.curselection()
        if not sel:
            return
        self._cur_id = self._list_ids[sel[0]]
        t = self.store.get(self._cur_id)
        self._name.set(t['name'])
        self._onum.set(t['o_number'])
        self._code.delete('1.0', 'end')
        self._code.insert('1.0', t.get('code', ''))
        self._reload_vt(t['variables'])
        self._reload_gt(t)

    def _add_tmpl(self):
        t = self.store.add()
        self._refresh_list()
        self.on_change()
        idx = len(self._list_ids) - 1
        self._lb.selection_clear(0, 'end')
        self._lb.selection_set(idx)
        self._on_list_sel(None)

    def _del_tmpl(self):
        if self._cur_id and messagebox.askyesno('Удалить', 'Удалить шаблон?'):
            self.store.delete(self._cur_id)
            self._cur_id = None
            self._refresh_list()
            self.on_change()

    def _save_tmpl(self):
        if self._cur_id is None:
            messagebox.showwarning('', 'Выберите шаблон из списка.')
            return
        t = self.store.get(self._cur_id)
        t['name']     = self._name.get()
        t['o_number'] = self._onum.get().strip()
        t['code']     = self._code.get('1.0', 'end-1c')
        self.store.update(t)
        self._refresh_list()
        self.on_change()
        messagebox.showinfo('Сохранено', 'Шаблон сохранён.')

    # ── Извлечение переменных ──

    def _extract(self):
        if self._cur_id is None:
            return
        code = self._code.get('1.0', 'end')
        pat = re.compile(r'(#(\d+)\s*=\s*)([-+]?\d+(?:\.\d+)?)\s*(?:\(([^)]*)\))?')
        matches = pat.findall(code)
        if not matches:
            messagebox.showinfo('Не найдено', 'Строки вида  #NNN = 123.0  не найдены.')
            return
        t = self.store.get(self._cur_id)
        existing = {v['num'] for v in t['variables']}
        added, new_code = 0, code
        for prefix, ns, val, comment in matches:
            num = int(ns)
            new_code = new_code.replace(f'{prefix}{val}', f'#{ns} = {{{{{num}}}}}', 1)
            if num in existing:
                continue
            t['variables'].append({'num': num,
                                   'label': comment.strip() if comment else f'Переменная #{num}',
                                   'unit': 'мм', 'default': val})
            existing.add(num)
            added += 1
        self.store.update(t)
        self._reload_vt(t['variables'])
        self._reload_gt(t)
        self._code.delete('1.0', 'end')
        self._code.insert('1.0', new_code)
        messagebox.showinfo('Готово',
            f'Добавлено: {added} переменных.\nЗначения заменены на {{{{NNN}}}}.\n\n'
            f'Перейди во вкладку "Группы" и разбей по категориям.')

    # ── Переменные (плоский список) ──

    def _reload_vt(self, variables):
        self._vt.delete(*self._vt.get_children())
        for v in variables:
            self._vt.insert('', 'end',
                values=(f"#{v['num']}", v['label'], v.get('unit', ''), v['default']))

    def _add_var(self):
        if self._cur_id is None:
            return
        VarDialog(self, lambda v: self._commit_var_add(v))

    def _commit_var_add(self, var):
        t = self.store.get(self._cur_id)
        t['variables'].append(var)
        self.store.update(t)
        self._reload_vt(t['variables'])
        self._reload_gt(t)

    def _del_var(self):
        sel = self._vt.selection()
        if not sel or self._cur_id is None:
            return
        idx = self._vt.index(sel[0])
        t = self.store.get(self._cur_id)
        num = t['variables'][idx]['num']
        t['variables'].pop(idx)
        for g in t.get('groups', []):
            g['var_nums'] = [n for n in g['var_nums'] if n != num]
        self.store.update(t)
        self._reload_vt(t['variables'])
        self._reload_gt(t)

    def _mv_var(self, d):
        sel = self._vt.selection()
        if not sel or self._cur_id is None:
            return
        idx = self._vt.index(sel[0])
        t = self.store.get(self._cur_id)
        ni = idx + d
        if 0 <= ni < len(t['variables']):
            t['variables'][idx], t['variables'][ni] = t['variables'][ni], t['variables'][idx]
            self.store.update(t)
            self._reload_vt(t['variables'])
            self._vt.selection_set(self._vt.get_children()[ni])

    def _edit_var(self, _):
        sel = self._vt.selection()
        if not sel or self._cur_id is None:
            return
        idx = self._vt.index(sel[0])
        t = self.store.get(self._cur_id)
        VarDialog(self, lambda v, i=idx: self._commit_var_edit(v, i), t['variables'][idx])

    def _commit_var_edit(self, var, idx):
        t = self.store.get(self._cur_id)
        t['variables'][idx] = var
        self.store.update(t)
        self._reload_vt(t['variables'])
        self._reload_gt(t)

    # ── Группы (treeview) ──

    def _reload_gt(self, t):
        tr = self._gt
        tr.delete(*tr.get_children())
        for i, grp in enumerate(t.get('groups', [])):
            color = grp.get('color', GROUP_PALETTE[i % len(GROUP_PALETTE)])
            fg = self._text_for(color)
            gid = f'grp_{grp["id"]}'
            tag = f'tag_{grp["id"]}'
            tr.insert('', 'end', iid=gid, text=f'  ● {grp["name"]}',
                      tags=(tag,), open=True)
            tr.tag_configure(tag, background=color, foreground=fg, font=BOLD)
            for vn in grp['var_nums']:
                v = self.store.get_var(t, vn)
                if v:
                    tr.insert(gid, 'end', iid=f'var_{vn}',
                              text=f'  ⠿  #{vn}',
                              values=(v['label'], v.get('unit', ''), v['default']),
                              tags=('var',))
        tr.insert('', 'end', iid='ungrouped', text='  Без группы',
                  tags=('ung',), open=True)
        tr.tag_configure('ung', background=ELEV, foreground=SUBT, font=BOLD)
        tr.tag_configure('var', background=SURF, foreground=TEXT)
        for v in self.store.get_ungrouped(t):
            tr.insert('ungrouped', 'end', iid=f'var_{v["num"]}',
                      text=f'  ⠿  #{v["num"]}',
                      values=(v['label'], v.get('unit', ''), v['default']),
                      tags=('var',))

    @staticmethod
    def _text_for(h):
        try:
            lum = 0.299*int(h[1:3],16) + 0.587*int(h[3:5],16) + 0.114*int(h[5:7],16)
            return '#e0e8ff' if lum < 140 else '#101020'
        except Exception:
            return '#e0e8ff'

    # ── Группы CRUD ──

    def _add_grp(self):
        if self._cur_id is None:
            return
        GroupDialog(self, self._commit_grp_add)

    def _commit_grp_add(self, data):
        t = self.store.get(self._cur_id)
        t.setdefault('groups', []).append({
            'id': self.store.next_group_id(t),
            'name': data['name'], 'color': data['color'], 'var_nums': []})
        self.store.update(t)
        self._reload_gt(t)

    def _edit_grp(self):
        sel = self._gt.selection()
        if not sel:
            return
        iid = sel[0]
        if not iid.startswith('grp_'):
            messagebox.showinfo('', 'Выбери строку с группой (● Название).')
            return
        gid = int(iid[4:])
        t = self.store.get(self._cur_id)
        g = next((x for x in t['groups'] if x['id'] == gid), None)
        if g:
            GroupDialog(self, lambda d, gid=gid: self._commit_grp_edit(d, gid),
                        {'name': g['name'], 'color': g.get('color', GROUP_PALETTE[0])})

    def _commit_grp_edit(self, data, gid):
        t = self.store.get(self._cur_id)
        for g in t['groups']:
            if g['id'] == gid:
                g['name'] = data['name']
                g['color'] = data['color']
                break
        self.store.update(t)
        self._reload_gt(t)

    def _del_grp(self):
        sel = self._gt.selection()
        if not sel:
            return
        iid = sel[0]
        if not iid.startswith('grp_'):
            messagebox.showinfo('', 'Выбери строку с группой.')
            return
        gid = int(iid[4:])
        t = self.store.get(self._cur_id)
        t['groups'] = [g for g in t['groups'] if g['id'] != gid]
        self.store.update(t)
        self._reload_gt(t)

    # ── Drag & Drop ──

    def _ds(self, event):
        item = self._gt.identify_row(event.y)
        if item and item.startswith('var_') and self._gt.parent(item):
            self._drag = item
            self._gt.configure(cursor='fleur')
        else:
            self._drag = None

    def _dm(self, event):
        if self._drag:
            t = self._gt.identify_row(event.y)
            if t:
                self._gt.see(t)

    def _dd(self, event):
        self._gt.configure(cursor='')
        if not self._drag or self._cur_id is None:
            self._drag = None
            return
        target = self._gt.identify_row(event.y)
        if not target or target == self._drag:
            self._drag = None
            return

        # Определить целевую группу
        if target in ('ungrouped',) or target.startswith('grp_'):
            new_grp = target
        else:
            new_grp = self._gt.parent(target)

        old_grp = self._gt.parent(self._drag)
        if new_grp == old_grp:
            self._drag = None
            return

        var_num = int(self._drag[4:])
        t = self.store.get(self._cur_id)

        if old_grp.startswith('grp_'):
            gid = int(old_grp[4:])
            for g in t['groups']:
                if g['id'] == gid:
                    g['var_nums'] = [n for n in g['var_nums'] if n != var_num]

        if new_grp.startswith('grp_'):
            gid = int(new_grp[4:])
            for g in t['groups']:
                if g['id'] == gid and var_num not in g['var_nums']:
                    g['var_nums'].append(var_num)

        self.store.update(t)
        self._reload_gt(t)
        self._drag = None

# ── Диалог пароля ────────────────────────────────────────────────────────────

class PasswordDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.configure(bg=BG)
        self.result = False
        self.title('Конструктор — доступ')
        self.resizable(False, False)
        self.grab_set()
        self.focus_set()

        tk.Label(self, text='🔒  Введите пароль', bg=BG, fg=TEXT, font=BOLD,
                 pady=18).pack()
        self._pv = tk.StringVar()
        ent = ttk.Entry(self, textvariable=self._pv, show='●', width=22, font=UI)
        ent.pack(padx=24, pady=4)
        ent.focus_set()

        self._err = tk.Label(self, text='', bg=BG, fg=DANGER, font=UI)
        self._err.pack(pady=2)

        bf = tk.Frame(self, bg=BG, pady=14)
        bf.pack()
        ttk.Button(bf, text='  Войти  ', style='Accent.TButton',
                   command=self._ok).pack(side='left', padx=6)
        ttk.Button(bf, text='Отмена', command=self.destroy).pack(side='left', padx=6)

        self.bind('<Return>', lambda _: self._ok())
        self.bind('<Escape>', lambda _: self.destroy())

    def _ok(self):
        if self._pv.get() == '752':
            self.result = True
            self.destroy()
        else:
            self._pv.set('')
            self._err.configure(text='Неверный пароль')

# ── Главное окно ──────────────────────────────────────────────────────────────

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        setup_theme(self)
        self.store = TemplateStore()
        self.title(APP_TITLE)
        self.geometry('1320x800')
        self.minsize(980, 640)
        self._unlocked = False
        self._nb = ttk.Notebook(self)
        self._nb.pack(fill='both', expand=True)
        self._op      = OperatorPanel(self._nb, self.store)
        self._con     = ConstructorPanel(self._nb, self.store, self._sync)
        self._meters  = MetersFrame(self._nb, data_file=os.path.join(BASE_DIR, 'meters_data.json'))
        self._nb.add(self._op,     text='   Генерация   ')
        self._nb.add(self._con,    text='   Конструктор  🔒')
        self._nb.add(self._meters, text='   Счётчики ЖКХ   ')
        self._nb.bind('<<NotebookTabChanged>>', self._on_tab)
        self.protocol('WM_DELETE_WINDOW', self._quit)
        self._op.refresh()

    def _quit(self):
        os._exit(0)

    def _on_tab(self, event):
        try:
            idx = self._nb.index('current')
        except Exception:
            return
        if idx == 1 and not self._unlocked:
            self._nb.select(0)
            dlg = PasswordDialog(self)
            self.wait_window(dlg)
            if dlg.result:
                self._unlocked = True
                self._nb.tab(1, text='   Конструктор  ✓')
                self._nb.select(1)
        elif idx == 0:
            self._op.refresh()

    def _sync(self):
        self._op.refresh()

if __name__ == '__main__':
    App().mainloop()
