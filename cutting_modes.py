#!/usr/bin/env python3
# cutting_modes.py  v2.0  — Подбор режимов резания для фрез
import tkinter as tk
from tkinter import ttk, messagebox
import math, json, os, sys, copy

# ─── ЦВЕТА ────────────────────────────────────────────────────────────────────
BG      = '#0d1117'
PANEL   = '#161b22'
CARD    = '#21262d'
CARD_H  = '#2d333b'
CARD_S  = '#1c3a6b'
BORDER  = '#30363d'
ACCENT  = '#4493f8'
GREEN   = '#3fb950'
YELLOW  = '#d29922'
RED     = '#f85149'
TEXT    = '#e6edf3'
DIM     = '#8b949e'
BTN_BLU = '#1f6feb'
BTN_GRY = '#21262d'

F_H  = ('Segoe UI', 13, 'bold')
F_B  = ('Segoe UI', 10)
F_S  = ('Segoe UI', 9)
F_M  = ('Consolas', 11)
F_MS = ('Consolas', 10)

# ─── ДАННЫЕ ───────────────────────────────────────────────────────────────────
MATERIALS = [
    ('plastic',          'Пластик / ПКМ',              'N',  'Полимеры, стеклопластик, углепластик'),
    ('aluminum',         'Алюминий и сплавы',           'N',  'Д16, АМГ, АЛ, силумины, 7075'),
    ('structural_steel', 'Конструкционная сталь',       'P1', 'σ < 850 МПа  (Ст3, 20, 45, 40Х)'),
    ('alloy_steel',      'Легированная сталь',          'P2', '850–1100 МПа  (4340, 42CrMo4)'),
    ('hard_steel',       'Твёрдая / инструм. сталь',   'P3', '> 1100 МПа  (Х12МФ, Р6М5, ХВГ)'),
    ('cast_iron',        'Серый / ковкий чугун',        'K1', 'СЧ10–СЧ35, КЧ30, КЧ35'),
    ('ductile_iron',     'Высокопрочный чугун',         'K2', 'ВЧ50, ВЧ70, ADI'),
    ('stainless',        'Нержавейка (аустенит)',       'M1', 'AISI 304, 316L, 321, 12Х18Н10Т'),
    ('duplex',           'Дуплекс / супердуплекс',     'M2', '2205, 2507, SAF 2906'),
    ('titanium',         'Титановые сплавы',            'S1', 'ВТ6 (Ti-6Al-4V), ВТ20, ВТ22'),
    ('heat_resistant',   'Жаропрочные сплавы',          'S2', 'Inconel 718, Waspaloy, ЭП741'),
    ('hardened',         'Закалённая сталь',            'H',  'HRC 40–65  (D2, M2, H13, ШХ15)'),
]

CUTTER_TYPES = [
    # key, name, has_inserts, db_key
    ('end_solid',     'Концевая монолитная  (ТС)',          False, 'end_solid'),
    ('end_hss',       'Концевая монолитная  (HSS)',          False, 'end_hss'),
    ('end_idx',       'Концевая  —  сменные пластины',      True,  'end_indexable'),
    ('face_idx',      'Торцевая  —  сменные пластины',      True,  'face'),
    ('highfeed',      'Высокоподачная  (High-Feed)',         True,  'highfeed'),
    ('ball_solid',    'Шаровая монолитная  (ТС)',            False, 'ball_solid'),
    ('ball_idx',      'Шаровая  —  сменные пластины',       True,  'ball_indexable'),
    ('tslot',         'Т-образная / пазовая',               True,  'tslot'),
    ('disc',          'Дисковая / трёхсторонняя',           True,  'disc'),
    ('corner_radius', 'Радиусная тороидальная  (монолит)',  False, 'corner_radius'),
    ('chamfer',       'Фасочная / угловая  (монолит)',      False, 'chamfer'),
]

# Рекомендации по инструменту: (mat) -> (для монолита, для пластин + High-Feed)
INSERT_REC = {
    'plastic':          ('Монолит без покрытия (uncoated). Острые кромки. Высокий передний угол.',
                         'Группа N (ISO). Незакрытые / TiB₂. Полированный передний угол. Острая кромка.'),
    'aluminum':         ('Монолит uncoated или TiB₂. Полированные канавки. 2–3 зуба.',
                         'Группа N (ISO). Uncoated / TiB₂. Полированный передний угол. 2–3 зуба.'),
    'structural_steel': ('AlTiN или TiAlN. 4 зуба черновая, 5–6 чистовая.',
                         'Группа P (ISO). TiAlN / AlTiN. Умеренный стружкодробитель.'),
    'alloy_steel':      ('AlCrN или AlTiN. Мелкозернистый ТС.',
                         'Группа P (ISO). AlCrN. Умеренная геометрия.'),
    'hard_steel':       ('AlCrN. Субмикронный твёрдый сплав.',
                         'Группа P/H. AlCrN или CBN при HRC > 55.'),
    'cast_iron':        ('AlTiN или uncoated монолит. 4–6 зубьев.',
                         'Группа K (ISO). TiAlN / uncoated. Умеренный радиус при вершине.'),
    'ductile_iron':     ('AlTiN монолит.',
                         'Группа K / M (ISO). AlTiN или AlCrN.'),
    'stainless':        ('PVD TiAlN. Острые кромки. Не останавливать подачу!',
                         'Группа M (ISO). PVD TiAlN / AlCrN. Острая кромка, позитивная геометрия.'),
    'duplex':           ('PVD AlCrN. Острые кромки. Малые ae.',
                         'Группа M (ISO). AlCrN-X. Острая кромка. Малый радиус при вершине.'),
    'titanium':         ('TiAlN-X (высокое содержание Al). Острые кромки. СОЖ обязателен!',
                         'Группа S (ISO). TiAlN-X. Острая кромка. Позитивная геометрия.'),
    'heat_resistant':   ('Uncoated ТС (мелкое зерно) или TiAlN-X. Острые кромки.',
                         'Группа S (ISO). Uncoated / TiAlN-X. Острая кромка. Позитивная.'),
    'hardened':         ('CBN или алмаз. При HRC > 55 — CBN обязателен.',
                         'Группа H (ISO). CBN / PcBN пластины. Жёсткое закрепление.'),
}

# Рекомендация пластины High-Feed отдельно (XNMU/ONMU тип)
HF_INSERT_REC = {
    'plastic':          'XNMU / RDHX — uncoated или TiB₂. Группа N.',
    'aluminum':         'XNMU / RDHX — uncoated или TiB₂. Группа N. Полированный передний угол.',
    'structural_steel': 'XNMU / ONMU — TiAlN или AlTiN. Группа P. Угол наклона 15–18°.',
    'alloy_steel':      'XNMU / ONMU — AlCrN или TiAlN. Группа P. Угол наклона 15–18°.',
    'hard_steel':       'XNMU — AlCrN. Группа P. Усиленная геометрия.',
    'cast_iron':        'XNMU / RDMT — TiAlN или uncoated. Группа K.',
    'ductile_iron':     'XNMU — TiAlN. Группа K/M.',
    'stainless':        'XNMU — PVD TiAlN. Группа M. Острая кромка.',
    'duplex':           'XNMU — AlCrN. Группа M. Острая кромка, малый радиус при вершине.',
    'titanium':         'XNMU / RDHX — TiAlN-X. Группа S. СОЖ обязателен!',
    'heat_resistant':   'XNMU — uncoated мелкозернистый ТС. Группа S.',
    'hardened':         'Специализированные CBN пластины HF-типа. Группа H.',
}

# ─── БАЗА РЕЖИМОВ РЕЗАНИЯ ─────────────────────────────────────────────────────
# coolant: 'yes' / 'no' / 'opt'
# ap_abs:  True  → ap в мм абс.   False → ap = ratio × D
DEFAULT_DATA = {
    # ── ПЛАСТИК ──────────────────────────────────────────────────────────────
    ('plastic','end_solid'):     {'vc':(150,500),  'fz':(0.05,0.20),'ap':(0.5,2.0), 'ae':(0.40,0.75),'coolant':'no', 'ap_abs':False,'notes':'Воздушный обдув. Острые кромки.'},
    ('plastic','end_hss'):       {'vc':(80,200),   'fz':(0.05,0.15),'ap':(0.5,1.5), 'ae':(0.40,0.75),'coolant':'no', 'ap_abs':False,'notes':''},
    ('plastic','end_indexable'): {'vc':(150,500),  'fz':(0.06,0.22),'ap':(0.5,2.0), 'ae':(0.40,0.75),'coolant':'no', 'ap_abs':False,'notes':''},
    ('plastic','face'):          {'vc':(200,600),  'fz':(0.08,0.25),'ap':(1.0,5.0), 'ae':(0.60,0.80),'coolant':'no', 'ap_abs':False,'notes':''},
    ('plastic','highfeed'):      {'vc':(200,800),  'fz':(0.80,2.50),'ap':(0.3,1.5), 'ae':(0.50,1.00),'coolant':'no', 'ap_abs':True, 'notes':'ap абс. мм. Воздушный обдув.'},
    ('plastic','ball_solid'):    {'vc':(100,400),  'fz':(0.03,0.12),'ap':(0.1,0.5), 'ae':(0.05,0.30),'coolant':'no', 'ap_abs':False,'notes':'Vc по эффективному диаметру.'},
    ('plastic','ball_indexable'):{'vc':(120,450),  'fz':(0.04,0.14),'ap':(0.1,0.5), 'ae':(0.05,0.30),'coolant':'no', 'ap_abs':False,'notes':''},
    ('plastic','tslot'):         {'vc':(80,250),   'fz':(0.03,0.10),'ap':(0.3,0.8), 'ae':(0.20,0.50),'coolant':'no', 'ap_abs':False,'notes':'Длинный вылет — снизить скорость.'},
    ('plastic','disc'):          {'vc':(100,350),  'fz':(0.04,0.15),'ap':(0.3,1.0), 'ae':(0.20,0.50),'coolant':'no', 'ap_abs':False,'notes':''},
    ('plastic','corner_radius'): {'vc':(120,450),  'fz':(0.04,0.16),'ap':(0.1,0.5), 'ae':(0.05,0.30),'coolant':'no', 'ap_abs':False,'notes':''},
    ('plastic','chamfer'):       {'vc':(150,500),  'fz':(0.03,0.12),'ap':(0.2,1.0), 'ae':(0.30,0.60),'coolant':'no', 'ap_abs':False,'notes':''},

    # ── АЛЮМИНИЙ ──────────────────────────────────────────────────────────────
    ('aluminum','end_solid'):     {'vc':(300,1200),'fz':(0.05,0.25),'ap':(0.5,3.0), 'ae':(0.40,0.75),'coolant':'opt','ap_abs':False,'notes':'TiB₂ или uncoated. Полированные канавки.'},
    ('aluminum','end_hss'):       {'vc':(150,450), 'fz':(0.05,0.18),'ap':(0.5,2.0), 'ae':(0.40,0.75),'coolant':'opt','ap_abs':False,'notes':''},
    ('aluminum','end_indexable'): {'vc':(300,1500),'fz':(0.08,0.35),'ap':(0.3,1.5), 'ae':(0.40,0.70),'coolant':'opt','ap_abs':False,'notes':'Пластины N, uncoated или TiB₂.'},
    ('aluminum','face'):          {'vc':(500,2500),'fz':(0.10,0.60),'ap':(1.0,8.0), 'ae':(0.60,0.80),'coolant':'opt','ap_abs':False,'notes':'СОЖ при чистовой.'},
    ('aluminum','highfeed'):      {'vc':(400,2000),'fz':(1.50,5.00),'ap':(0.5,3.0), 'ae':(0.60,1.00),'coolant':'no', 'ap_abs':True, 'notes':'ap абс. мм. Сухая обработка или обдув.'},
    ('aluminum','ball_solid'):    {'vc':(200,900), 'fz':(0.04,0.20),'ap':(0.1,0.5), 'ae':(0.05,0.30),'coolant':'opt','ap_abs':False,'notes':''},
    ('aluminum','ball_indexable'):{'vc':(300,1200),'fz':(0.08,0.30),'ap':(0.1,0.5), 'ae':(0.10,0.30),'coolant':'opt','ap_abs':False,'notes':''},
    ('aluminum','tslot'):         {'vc':(150,600), 'fz':(0.04,0.15),'ap':(0.3,1.0), 'ae':(0.20,0.50),'coolant':'opt','ap_abs':False,'notes':''},
    ('aluminum','disc'):          {'vc':(200,900), 'fz':(0.06,0.25),'ap':(0.3,1.2), 'ae':(0.20,0.50),'coolant':'opt','ap_abs':False,'notes':''},
    ('aluminum','corner_radius'): {'vc':(200,900), 'fz':(0.05,0.22),'ap':(0.1,0.5), 'ae':(0.05,0.30),'coolant':'opt','ap_abs':False,'notes':''},
    ('aluminum','chamfer'):       {'vc':(300,1200),'fz':(0.04,0.18),'ap':(0.2,1.5), 'ae':(0.30,0.60),'coolant':'opt','ap_abs':False,'notes':''},

    # ── КОНСТРУКЦИОННАЯ СТАЛЬ P1 ──────────────────────────────────────────────
    ('structural_steel','end_solid'):     {'vc':(80,220),  'fz':(0.04,0.15),'ap':(0.3,1.0), 'ae':(0.40,0.70),'coolant':'yes','ap_abs':False,'notes':'AlTiN. Обильный СОЖ.'},
    ('structural_steel','end_hss'):       {'vc':(25,65),   'fz':(0.03,0.10),'ap':(0.3,0.8), 'ae':(0.40,0.65),'coolant':'yes','ap_abs':False,'notes':''},
    ('structural_steel','end_indexable'): {'vc':(100,280), 'fz':(0.05,0.20),'ap':(0.2,0.8), 'ae':(0.35,0.65),'coolant':'yes','ap_abs':False,'notes':'Пластины P.'},
    ('structural_steel','face'):          {'vc':(150,380), 'fz':(0.10,0.45),'ap':(1.0,5.0), 'ae':(0.60,0.80),'coolant':'yes','ap_abs':False,'notes':''},
    ('structural_steel','highfeed'):      {'vc':(120,300), 'fz':(0.80,2.50),'ap':(0.3,1.5), 'ae':(0.50,1.00),'coolant':'no', 'ap_abs':True, 'notes':'ap абс. мм. Строго без СОЖ — воздушный обдув. XNMU/ONMU, TiAlN, 15–18°.'},
    ('structural_steel','ball_solid'):    {'vc':(60,160),  'fz':(0.02,0.10),'ap':(0.1,0.4), 'ae':(0.05,0.25),'coolant':'yes','ap_abs':False,'notes':''},
    ('structural_steel','ball_indexable'):{'vc':(80,200),  'fz':(0.05,0.15),'ap':(0.1,0.4), 'ae':(0.05,0.25),'coolant':'yes','ap_abs':False,'notes':''},
    ('structural_steel','tslot'):         {'vc':(40,100),  'fz':(0.02,0.07),'ap':(0.2,0.5), 'ae':(0.15,0.40),'coolant':'yes','ap_abs':False,'notes':'Длинный вылет — снижать скорость.'},
    ('structural_steel','disc'):          {'vc':(60,160),  'fz':(0.03,0.12),'ap':(0.2,0.6), 'ae':(0.15,0.40),'coolant':'yes','ap_abs':False,'notes':''},
    ('structural_steel','corner_radius'): {'vc':(70,180),  'fz':(0.03,0.12),'ap':(0.1,0.4), 'ae':(0.05,0.25),'coolant':'yes','ap_abs':False,'notes':''},
    ('structural_steel','chamfer'):       {'vc':(80,200),  'fz':(0.02,0.10),'ap':(0.2,1.0), 'ae':(0.30,0.60),'coolant':'yes','ap_abs':False,'notes':''},

    # ── ЛЕГИРОВАННАЯ СТАЛЬ P2 ─────────────────────────────────────────────────
    ('alloy_steel','end_solid'):     {'vc':(50,160), 'fz':(0.03,0.12),'ap':(0.2,0.8), 'ae':(0.35,0.65),'coolant':'yes','ap_abs':False,'notes':'AlTiN или AlCrN.'},
    ('alloy_steel','end_hss'):       {'vc':(15,45),  'fz':(0.02,0.08),'ap':(0.2,0.6), 'ae':(0.35,0.60),'coolant':'yes','ap_abs':False,'notes':''},
    ('alloy_steel','end_indexable'): {'vc':(80,200), 'fz':(0.04,0.16),'ap':(0.15,0.6),'ae':(0.30,0.60),'coolant':'yes','ap_abs':False,'notes':''},
    ('alloy_steel','face'):          {'vc':(100,260),'fz':(0.08,0.35),'ap':(0.5,4.0), 'ae':(0.55,0.75),'coolant':'yes','ap_abs':False,'notes':''},
    ('alloy_steel','highfeed'):      {'vc':(100,250),'fz':(0.60,2.00),'ap':(0.3,1.2), 'ae':(0.50,1.00),'coolant':'no', 'ap_abs':True, 'notes':'ap абс. мм. Строго без СОЖ — воздушный обдув.'},
    ('alloy_steel','ball_solid'):    {'vc':(40,130), 'fz':(0.02,0.08),'ap':(0.1,0.3), 'ae':(0.05,0.20),'coolant':'yes','ap_abs':False,'notes':''},
    ('alloy_steel','ball_indexable'):{'vc':(50,150), 'fz':(0.03,0.10),'ap':(0.1,0.3), 'ae':(0.05,0.20),'coolant':'yes','ap_abs':False,'notes':''},
    ('alloy_steel','tslot'):         {'vc':(25,80),  'fz':(0.02,0.05),'ap':(0.15,0.4),'ae':(0.15,0.35),'coolant':'yes','ap_abs':False,'notes':''},
    ('alloy_steel','disc'):          {'vc':(40,120), 'fz':(0.02,0.10),'ap':(0.15,0.5),'ae':(0.15,0.35),'coolant':'yes','ap_abs':False,'notes':''},
    ('alloy_steel','corner_radius'): {'vc':(45,135), 'fz':(0.02,0.09),'ap':(0.1,0.3), 'ae':(0.05,0.20),'coolant':'yes','ap_abs':False,'notes':''},
    ('alloy_steel','chamfer'):       {'vc':(50,160), 'fz':(0.02,0.09),'ap':(0.2,0.8), 'ae':(0.30,0.60),'coolant':'yes','ap_abs':False,'notes':''},

    # ── ТВЁРДАЯ СТАЛЬ P3 ──────────────────────────────────────────────────────
    ('hard_steel','end_solid'):     {'vc':(30,100), 'fz':(0.02,0.08),'ap':(0.1,0.5), 'ae':(0.25,0.55),'coolant':'yes','ap_abs':False,'notes':'AlCrN. Жёсткое закрепление.'},
    ('hard_steel','end_hss'):       {'vc':(8,25),   'fz':(0.01,0.05),'ap':(0.1,0.3), 'ae':(0.25,0.45),'coolant':'yes','ap_abs':False,'notes':'Не рекомендуется.'},
    ('hard_steel','end_indexable'): {'vc':(50,140), 'fz':(0.03,0.12),'ap':(0.1,0.4), 'ae':(0.25,0.50),'coolant':'yes','ap_abs':False,'notes':''},
    ('hard_steel','face'):          {'vc':(80,220), 'fz':(0.06,0.25),'ap':(0.5,2.5), 'ae':(0.50,0.75),'coolant':'yes','ap_abs':False,'notes':''},
    ('hard_steel','highfeed'):      {'vc':(80,200), 'fz':(0.40,1.50),'ap':(0.2,0.8), 'ae':(0.40,0.90),'coolant':'no', 'ap_abs':True, 'notes':'ap абс. мм. Строго без СОЖ — воздушный обдув.'},
    ('hard_steel','ball_solid'):    {'vc':(25,80),  'fz':(0.01,0.06),'ap':(0.05,0.2),'ae':(0.03,0.15),'coolant':'yes','ap_abs':False,'notes':''},
    ('hard_steel','ball_indexable'):{'vc':(35,100), 'fz':(0.02,0.08),'ap':(0.05,0.2),'ae':(0.03,0.15),'coolant':'yes','ap_abs':False,'notes':''},
    ('hard_steel','tslot'):         {'vc':(15,50),  'fz':(0.01,0.04),'ap':(0.08,0.2),'ae':(0.10,0.25),'coolant':'yes','ap_abs':False,'notes':'Крайне осторожно.'},
    ('hard_steel','disc'):          {'vc':(25,80),  'fz':(0.02,0.06),'ap':(0.08,0.2),'ae':(0.10,0.25),'coolant':'yes','ap_abs':False,'notes':''},
    ('hard_steel','corner_radius'): {'vc':(28,88),  'fz':(0.01,0.05),'ap':(0.05,0.15),'ae':(0.03,0.12),'coolant':'yes','ap_abs':False,'notes':''},
    ('hard_steel','chamfer'):       {'vc':(40,120), 'fz':(0.01,0.06),'ap':(0.1,0.5), 'ae':(0.25,0.50),'coolant':'yes','ap_abs':False,'notes':''},

    # ── СЕРЫЙ ЧУГУН K1 ────────────────────────────────────────────────────────
    ('cast_iron','end_solid'):     {'vc':(80,280),  'fz':(0.04,0.15),'ap':(0.3,1.0), 'ae':(0.40,0.70),'coolant':'no', 'ap_abs':False,'notes':'Сухая обработка или туман. AlTiN.'},
    ('cast_iron','end_hss'):       {'vc':(20,55),   'fz':(0.03,0.08),'ap':(0.3,0.7), 'ae':(0.35,0.65),'coolant':'no', 'ap_abs':False,'notes':''},
    ('cast_iron','end_indexable'): {'vc':(100,320), 'fz':(0.05,0.20),'ap':(0.2,0.8), 'ae':(0.35,0.65),'coolant':'no', 'ap_abs':False,'notes':'Пластины K.'},
    ('cast_iron','face'):          {'vc':(150,450), 'fz':(0.10,0.45),'ap':(1.0,6.0), 'ae':(0.60,0.80),'coolant':'no', 'ap_abs':False,'notes':''},
    ('cast_iron','highfeed'):      {'vc':(200,500), 'fz':(1.00,3.00),'ap':(0.5,2.5), 'ae':(0.60,1.00),'coolant':'no', 'ap_abs':True, 'notes':'ap абс. мм. Строго без СОЖ.'},
    ('cast_iron','ball_solid'):    {'vc':(60,220),  'fz':(0.03,0.12),'ap':(0.1,0.4), 'ae':(0.05,0.25),'coolant':'no', 'ap_abs':False,'notes':''},
    ('cast_iron','ball_indexable'):{'vc':(80,250),  'fz':(0.04,0.16),'ap':(0.1,0.4), 'ae':(0.05,0.25),'coolant':'no', 'ap_abs':False,'notes':''},
    ('cast_iron','tslot'):         {'vc':(40,110),  'fz':(0.02,0.07),'ap':(0.2,0.5), 'ae':(0.15,0.35),'coolant':'no', 'ap_abs':False,'notes':''},
    ('cast_iron','disc'):          {'vc':(60,200),  'fz':(0.03,0.15),'ap':(0.2,0.6), 'ae':(0.15,0.40),'coolant':'no', 'ap_abs':False,'notes':''},
    ('cast_iron','corner_radius'): {'vc':(70,210),  'fz':(0.03,0.12),'ap':(0.1,0.4), 'ae':(0.05,0.25),'coolant':'no', 'ap_abs':False,'notes':''},
    ('cast_iron','chamfer'):       {'vc':(80,250),  'fz':(0.02,0.10),'ap':(0.2,1.0), 'ae':(0.30,0.60),'coolant':'no', 'ap_abs':False,'notes':''},

    # ── ВЫСОКОПРОЧНЫЙ ЧУГУН K2 ────────────────────────────────────────────────
    ('ductile_iron','end_solid'):     {'vc':(60,200), 'fz':(0.03,0.12),'ap':(0.3,0.8), 'ae':(0.35,0.65),'coolant':'no', 'ap_abs':False,'notes':''},
    ('ductile_iron','end_hss'):       {'vc':(15,40),  'fz':(0.02,0.07),'ap':(0.2,0.6), 'ae':(0.30,0.60),'coolant':'no', 'ap_abs':False,'notes':''},
    ('ductile_iron','end_indexable'): {'vc':(80,250), 'fz':(0.04,0.18),'ap':(0.2,0.7), 'ae':(0.30,0.60),'coolant':'no', 'ap_abs':False,'notes':''},
    ('ductile_iron','face'):          {'vc':(100,300),'fz':(0.08,0.38),'ap':(0.5,4.5), 'ae':(0.55,0.75),'coolant':'no', 'ap_abs':False,'notes':''},
    ('ductile_iron','highfeed'):      {'vc':(150,400),'fz':(0.80,2.50),'ap':(0.4,2.0), 'ae':(0.55,1.00),'coolant':'no', 'ap_abs':True, 'notes':'ap абс. мм. Строго без СОЖ.'},
    ('ductile_iron','ball_solid'):    {'vc':(50,160), 'fz':(0.02,0.10),'ap':(0.1,0.3), 'ae':(0.05,0.20),'coolant':'no', 'ap_abs':False,'notes':''},
    ('ductile_iron','ball_indexable'):{'vc':(60,180), 'fz':(0.03,0.12),'ap':(0.1,0.3), 'ae':(0.05,0.20),'coolant':'no', 'ap_abs':False,'notes':''},
    ('ductile_iron','tslot'):         {'vc':(30,90),  'fz':(0.02,0.05),'ap':(0.15,0.4),'ae':(0.12,0.30),'coolant':'no', 'ap_abs':False,'notes':''},
    ('ductile_iron','disc'):          {'vc':(50,160), 'fz':(0.03,0.12),'ap':(0.15,0.5),'ae':(0.12,0.35),'coolant':'no', 'ap_abs':False,'notes':''},
    ('ductile_iron','corner_radius'): {'vc':(55,170), 'fz':(0.02,0.10),'ap':(0.1,0.3), 'ae':(0.05,0.20),'coolant':'no', 'ap_abs':False,'notes':''},
    ('ductile_iron','chamfer'):       {'vc':(65,200), 'fz':(0.02,0.08),'ap':(0.2,0.8), 'ae':(0.30,0.60),'coolant':'no', 'ap_abs':False,'notes':''},

    # ── НЕРЖАВЕЙКА M1 ─────────────────────────────────────────────────────────
    ('stainless','end_solid'):     {'vc':(40,130), 'fz':(0.03,0.10),'ap':(0.2,0.7), 'ae':(0.30,0.60),'coolant':'yes','ap_abs':False,'notes':'Обильный СОЖ! Не останавливаться — наклёп.'},
    ('stainless','end_hss'):       {'vc':(12,32),  'fz':(0.02,0.06),'ap':(0.2,0.5), 'ae':(0.30,0.55),'coolant':'yes','ap_abs':False,'notes':''},
    ('stainless','end_indexable'): {'vc':(50,160), 'fz':(0.03,0.12),'ap':(0.15,0.5),'ae':(0.25,0.55),'coolant':'yes','ap_abs':False,'notes':'Пластины M.'},
    ('stainless','face'):          {'vc':(80,220), 'fz':(0.06,0.28),'ap':(0.5,3.5), 'ae':(0.55,0.75),'coolant':'yes','ap_abs':False,'notes':''},
    ('stainless','highfeed'):      {'vc':(80,180), 'fz':(0.50,1.50),'ap':(0.2,0.8), 'ae':(0.40,0.80),'coolant':'yes','ap_abs':True, 'notes':'ap абс. мм. СОЖ обязателен — предотвращение наклёпа.'},
    ('stainless','ball_solid'):    {'vc':(30,95),  'fz':(0.02,0.07),'ap':(0.08,0.3),'ae':(0.03,0.18),'coolant':'yes','ap_abs':False,'notes':''},
    ('stainless','ball_indexable'):{'vc':(40,120), 'fz':(0.03,0.10),'ap':(0.08,0.3),'ae':(0.03,0.18),'coolant':'yes','ap_abs':False,'notes':''},
    ('stainless','tslot'):         {'vc':(20,65),  'fz':(0.01,0.04),'ap':(0.15,0.4),'ae':(0.12,0.30),'coolant':'yes','ap_abs':False,'notes':''},
    ('stainless','disc'):          {'vc':(30,90),  'fz':(0.02,0.08),'ap':(0.15,0.4),'ae':(0.12,0.30),'coolant':'yes','ap_abs':False,'notes':''},
    ('stainless','corner_radius'): {'vc':(35,105), 'fz':(0.02,0.07),'ap':(0.08,0.3),'ae':(0.03,0.18),'coolant':'yes','ap_abs':False,'notes':''},
    ('stainless','chamfer'):       {'vc':(40,130), 'fz':(0.01,0.06),'ap':(0.15,0.8),'ae':(0.25,0.55),'coolant':'yes','ap_abs':False,'notes':''},

    # ── ДУПЛЕКС M2 ────────────────────────────────────────────────────────────
    ('duplex','end_solid'):     {'vc':(25,85),  'fz':(0.02,0.08),'ap':(0.15,0.5),'ae':(0.25,0.50),'coolant':'yes','ap_abs':False,'notes':'Высокое давление СОЖ. Острые кромки.'},
    ('duplex','end_hss'):       {'vc':(8,20),   'fz':(0.01,0.04),'ap':(0.1,0.3), 'ae':(0.20,0.40),'coolant':'yes','ap_abs':False,'notes':'Не рекомендуется.'},
    ('duplex','end_indexable'): {'vc':(30,95),  'fz':(0.03,0.10),'ap':(0.1,0.4), 'ae':(0.20,0.45),'coolant':'yes','ap_abs':False,'notes':''},
    ('duplex','face'):          {'vc':(50,140), 'fz':(0.05,0.22),'ap':(0.3,2.5), 'ae':(0.50,0.70),'coolant':'yes','ap_abs':False,'notes':''},
    ('duplex','highfeed'):      {'vc':(50,130), 'fz':(0.30,1.00),'ap':(0.15,0.6),'ae':(0.35,0.70),'coolant':'yes','ap_abs':True, 'notes':'ap абс. мм. СОЖ обязателен.'},
    ('duplex','ball_solid'):    {'vc':(20,65),  'fz':(0.01,0.05),'ap':(0.05,0.2),'ae':(0.03,0.12),'coolant':'yes','ap_abs':False,'notes':''},
    ('duplex','ball_indexable'):{'vc':(25,80),  'fz':(0.02,0.06),'ap':(0.05,0.2),'ae':(0.03,0.12),'coolant':'yes','ap_abs':False,'notes':''},
    ('duplex','tslot'):         {'vc':(15,45),  'fz':(0.01,0.03),'ap':(0.1,0.3), 'ae':(0.10,0.25),'coolant':'yes','ap_abs':False,'notes':''},
    ('duplex','disc'):          {'vc':(20,65),  'fz':(0.02,0.06),'ap':(0.1,0.3), 'ae':(0.10,0.25),'coolant':'yes','ap_abs':False,'notes':''},
    ('duplex','corner_radius'): {'vc':(22,70),  'fz':(0.01,0.05),'ap':(0.05,0.18),'ae':(0.03,0.10),'coolant':'yes','ap_abs':False,'notes':''},
    ('duplex','chamfer'):       {'vc':(28,90),  'fz':(0.01,0.05),'ap':(0.1,0.5), 'ae':(0.20,0.45),'coolant':'yes','ap_abs':False,'notes':''},

    # ── ТИТАН S1 ──────────────────────────────────────────────────────────────
    ('titanium','end_solid'):     {'vc':(30,90),  'fz':(0.02,0.08),'ap':(0.2,0.8), 'ae':(0.30,0.60),'coolant':'yes','ap_abs':False,'notes':'ОБЯЗАТЕЛЕН СОЖ! Опасность возгорания стружки.'},
    ('titanium','end_hss'):       {'vc':(8,20),   'fz':(0.01,0.04),'ap':(0.1,0.4), 'ae':(0.25,0.50),'coolant':'yes','ap_abs':False,'notes':''},
    ('titanium','end_indexable'): {'vc':(40,110), 'fz':(0.03,0.10),'ap':(0.15,0.5),'ae':(0.25,0.55),'coolant':'yes','ap_abs':False,'notes':''},
    ('titanium','face'):          {'vc':(50,130), 'fz':(0.05,0.20),'ap':(0.3,2.5), 'ae':(0.50,0.70),'coolant':'yes','ap_abs':False,'notes':''},
    ('titanium','highfeed'):      {'vc':(40,100), 'fz':(0.30,1.00),'ap':(0.2,0.8), 'ae':(0.30,0.65),'coolant':'yes','ap_abs':True, 'notes':'ap абс. мм. СОЖ ОБЯЗАТЕЛЕН — пожарная безопасность!'},
    ('titanium','ball_solid'):    {'vc':(20,65),  'fz':(0.01,0.05),'ap':(0.05,0.2),'ae':(0.03,0.12),'coolant':'yes','ap_abs':False,'notes':''},
    ('titanium','ball_indexable'):{'vc':(25,80),  'fz':(0.02,0.07),'ap':(0.05,0.2),'ae':(0.03,0.12),'coolant':'yes','ap_abs':False,'notes':''},
    ('titanium','tslot'):         {'vc':(15,45),  'fz':(0.01,0.03),'ap':(0.1,0.3), 'ae':(0.10,0.25),'coolant':'yes','ap_abs':False,'notes':''},
    ('titanium','disc'):          {'vc':(20,65),  'fz':(0.02,0.06),'ap':(0.1,0.3), 'ae':(0.10,0.25),'coolant':'yes','ap_abs':False,'notes':''},
    ('titanium','corner_radius'): {'vc':(22,70),  'fz':(0.01,0.05),'ap':(0.05,0.18),'ae':(0.03,0.10),'coolant':'yes','ap_abs':False,'notes':''},
    ('titanium','chamfer'):       {'vc':(28,90),  'fz':(0.01,0.05),'ap':(0.1,0.5), 'ae':(0.20,0.45),'coolant':'yes','ap_abs':False,'notes':''},

    # ── ЖАРОПРОЧНЫЕ S2 ────────────────────────────────────────────────────────
    ('heat_resistant','end_solid'):     {'vc':(15,55),  'fz':(0.01,0.06), 'ap':(0.1,0.4), 'ae':(0.20,0.50),'coolant':'yes','ap_abs':False,'notes':'Высокое давление СОЖ. Не останавливать подачу!'},
    ('heat_resistant','end_hss'):       {'vc':(5,15),   'fz':(0.005,0.03),'ap':(0.05,0.2),'ae':(0.15,0.35),'coolant':'yes','ap_abs':False,'notes':'Не рекомендуется.'},
    ('heat_resistant','end_indexable'): {'vc':(20,65),  'fz':(0.02,0.08), 'ap':(0.1,0.3), 'ae':(0.15,0.45),'coolant':'yes','ap_abs':False,'notes':''},
    ('heat_resistant','face'):          {'vc':(25,75),  'fz':(0.03,0.12), 'ap':(0.2,1.5), 'ae':(0.40,0.65),'coolant':'yes','ap_abs':False,'notes':''},
    ('heat_resistant','highfeed'):      {'vc':(20,60),  'fz':(0.20,0.60), 'ap':(0.1,0.5), 'ae':(0.25,0.55),'coolant':'yes','ap_abs':True, 'notes':'ap абс. мм. СОЖ высокое давление.'},
    ('heat_resistant','ball_solid'):    {'vc':(10,38),  'fz':(0.01,0.04), 'ap':(0.03,0.12),'ae':(0.02,0.08),'coolant':'yes','ap_abs':False,'notes':''},
    ('heat_resistant','ball_indexable'):{'vc':(15,45),  'fz':(0.01,0.05), 'ap':(0.03,0.12),'ae':(0.02,0.08),'coolant':'yes','ap_abs':False,'notes':''},
    ('heat_resistant','tslot'):         {'vc':(8,28),   'fz':(0.005,0.02),'ap':(0.05,0.18),'ae':(0.08,0.20),'coolant':'yes','ap_abs':False,'notes':''},
    ('heat_resistant','disc'):          {'vc':(10,35),  'fz':(0.01,0.04), 'ap':(0.05,0.18),'ae':(0.08,0.20),'coolant':'yes','ap_abs':False,'notes':''},
    ('heat_resistant','corner_radius'): {'vc':(12,40),  'fz':(0.01,0.03), 'ap':(0.03,0.10),'ae':(0.02,0.06),'coolant':'yes','ap_abs':False,'notes':''},
    ('heat_resistant','chamfer'):       {'vc':(15,50),  'fz':(0.005,0.03),'ap':(0.05,0.3), 'ae':(0.15,0.40),'coolant':'yes','ap_abs':False,'notes':''},

    # ── ЗАКАЛЁННАЯ СТАЛЬ H ────────────────────────────────────────────────────
    ('hardened','end_solid'):     {'vc':(30,105), 'fz':(0.02,0.06), 'ap':(0.05,0.3), 'ae':(0.15,0.45),'coolant':'yes','ap_abs':False,'notes':'CBN или субмикронный ТС. Жёсткость станка!'},
    ('hardened','end_hss'):       {'vc':(5,15),   'fz':(0.01,0.03), 'ap':(0.03,0.1), 'ae':(0.10,0.25),'coolant':'yes','ap_abs':False,'notes':'Крайне не рекомендуется.'},
    ('hardened','end_indexable'): {'vc':(40,125), 'fz':(0.02,0.08), 'ap':(0.05,0.2), 'ae':(0.15,0.40),'coolant':'yes','ap_abs':False,'notes':'Пластины H, CBN/PcBN.'},
    ('hardened','face'):          {'vc':(60,200), 'fz':(0.05,0.16), 'ap':(0.1,0.9),  'ae':(0.40,0.65),'coolant':'yes','ap_abs':False,'notes':''},
    ('hardened','highfeed'):      {'vc':(50,150), 'fz':(0.20,0.80), 'ap':(0.05,0.3), 'ae':(0.30,0.60),'coolant':'yes','ap_abs':True, 'notes':'ap абс. мм. CBN пластины HF-типа.'},
    ('hardened','ball_solid'):    {'vc':(25,85),  'fz':(0.01,0.04), 'ap':(0.02,0.1), 'ae':(0.02,0.08),'coolant':'yes','ap_abs':False,'notes':'CBN шаровые. Чистовая.'},
    ('hardened','ball_indexable'):{'vc':(30,100), 'fz':(0.01,0.05), 'ap':(0.02,0.1), 'ae':(0.02,0.08),'coolant':'yes','ap_abs':False,'notes':''},
    ('hardened','tslot'):         {'vc':(15,55),  'fz':(0.005,0.02),'ap':(0.03,0.1), 'ae':(0.08,0.20),'coolant':'yes','ap_abs':False,'notes':'Крайне осторожно.'},
    ('hardened','disc'):          {'vc':(20,65),  'fz':(0.01,0.04), 'ap':(0.03,0.1), 'ae':(0.08,0.20),'coolant':'yes','ap_abs':False,'notes':''},
    ('hardened','corner_radius'): {'vc':(28,90),  'fz':(0.01,0.03), 'ap':(0.02,0.08),'ae':(0.02,0.06),'coolant':'yes','ap_abs':False,'notes':''},
    ('hardened','chamfer'):       {'vc':(40,130), 'fz':(0.01,0.04), 'ap':(0.05,0.3), 'ae':(0.20,0.45),'coolant':'yes','ap_abs':False,'notes':''},
}

FALLBACK = {'end_hss':'end_solid','ball_indexable':'ball_solid',
            'corner_radius':'ball_solid','chamfer':'end_solid'}

# ─── ЗАГРУЗКА / СОХРАНЕНИЕ БАЗЫ ──────────────────────────────────────────────
def data_path():
    base = os.path.dirname(sys.executable if getattr(sys,'frozen',False)
                           else os.path.abspath(__file__))
    return os.path.join(base, 'cutting_data.json')

def load_data():
    p = data_path()
    if not os.path.exists(p):
        return copy.deepcopy(DEFAULT_DATA)
    try:
        with open(p, encoding='utf-8') as f:
            raw = json.load(f)
        out = {}
        for k, v in raw.items():
            mat, ct = k.split('|')
            d = dict(v)
            d['vc']  = tuple(d['vc'])
            d['fz']  = tuple(d['fz'])
            d['ap']  = tuple(d['ap'])
            d['ae']  = tuple(d['ae'])
            out[(mat, ct)] = d
        return out
    except Exception:
        return copy.deepcopy(DEFAULT_DATA)

def save_data(data):
    out = {}
    for (mat, ct), v in data.items():
        out[f'{mat}|{ct}'] = dict(v)
    with open(data_path(), 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

CUTTING_DATA = load_data()

def get_data(mat, db_key):
    key = (mat, db_key)
    if key in CUTTING_DATA:
        return CUTTING_DATA[key]
    fb = FALLBACK.get(db_key)
    return CUTTING_DATA.get((mat, fb)) if fb else None

# ─── ВСПОМОГАТЕЛЬНЫЕ ВИДЖЕТЫ ──────────────────────────────────────────────────
def styled_btn(parent, text, cmd, primary=True, width=None):
    bg = BTN_BLU if primary else BTN_GRY
    b = tk.Button(parent, text=text, command=cmd,
                  bg=bg, fg=TEXT, font=F_B, relief='flat', bd=0,
                  padx=18, pady=7, cursor='hand2',
                  activebackground='#388bfd' if primary else CARD_H,
                  activeforeground=TEXT)
    if width:
        b.config(width=width)
    def on_enter(_): b.config(bg='#388bfd' if primary else CARD_H)
    def on_leave(_): b.config(bg=BTN_BLU if primary else BTN_GRY)
    b.bind('<Enter>', on_enter)
    b.bind('<Leave>', on_leave)
    return b

def center(win, w, h):
    win.update_idletasks()
    sw = win.winfo_screenwidth()
    sh = win.winfo_screenheight()
    win.geometry(f'{w}x{h}+{(sw-w)//2}+{(sh-h)//2}')

# ─── ГЛАВНОЕ ОКНО ────────────────────────────────────────────────────────────
class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Режимы резания фрез')
        self.configure(bg=BG)
        self.resizable(False, False)
        center(self, 460, 340)
        self._build()

    def _build(self):
        tk.Frame(self, bg=ACCENT, height=4).pack(fill='x')

        body = tk.Frame(self, bg=BG)
        body.pack(fill='both', expand=True, padx=40, pady=30)

        tk.Label(body, text='⚙', bg=BG, fg=ACCENT, font=('Segoe UI', 36)).pack()
        tk.Label(body, text='РЕЖИМЫ РЕЗАНИЯ ФРЕЗ', bg=BG, fg=TEXT,
                 font=('Segoe UI', 16, 'bold')).pack(pady=(4, 2))
        tk.Label(body, text='Подбор параметров обработки по материалу и инструменту',
                 bg=BG, fg=DIM, font=F_S).pack(pady=(0, 30))

        styled_btn(body, '  Подобрать режимы  →', self._start, primary=True).pack(
            fill='x', pady=(0, 10))
        styled_btn(body, '  База данных и формулы', self._settings, primary=False).pack(
            fill='x')

        tk.Label(body, text='v2.0', bg=BG, fg=DIM, font=F_S).pack(side='bottom', pady=(20,0))

    def _start(self):
        self._open_s1()

    def _open_s1(self):
        Step1Dialog(self, on_next=self._s1_done)

    def _s1_done(self, mat):
        self._last_mat = mat
        self._open_s2(mat)

    def _open_s2(self, mat):
        Step2Dialog(self, mat, on_next=self._s2_done, on_back=self._open_s1)

    def _s2_done(self, mat, cutter_key, cutter_name, has_ins, db_key):
        self._last_cutter = (mat, cutter_key, cutter_name, has_ins, db_key)
        self._open_s3(mat, cutter_key, cutter_name, has_ins, db_key)

    def _open_s3(self, mat, cutter_key, cutter_name, has_ins, db_key):
        Step3Dialog(self, mat, cutter_key, cutter_name, has_ins, db_key,
                    on_next=self._show_result,
                    on_back=lambda: self._open_s2(self._last_mat))

    def _show_result(self, mat, cutter_key, cutter_name, has_ins, db_key, D, z, ae_pct):
        ResultWindow(self, mat, cutter_name, has_ins, db_key, D, z, ae_pct)

    def _settings(self):
        SettingsWindow(self)

# ─── БАЗОВЫЙ ДИАЛОГ ──────────────────────────────────────────────────────────
class BaseDialog(tk.Toplevel):
    def __init__(self, parent, title, step, total, w, h):
        super().__init__(parent)
        self.title(title)
        self.configure(bg=BG)
        self.resizable(True, True)
        self.minsize(500, 460)
        self.grab_set()
        center(self, w, h)
        self.transient(parent)
        # header strip
        hdr = tk.Frame(self, bg=PANEL, pady=12)
        hdr.pack(fill='x')
        tk.Label(hdr, text=title, bg=PANEL, fg=TEXT, font=F_H).pack(side='left', padx=20)
        tk.Label(hdr, text=f'Шаг {step} из 3', bg=PANEL, fg=DIM, font=F_S).pack(
            side='right', padx=20)
        # progress bar
        bar_bg = tk.Frame(self, bg=BORDER, height=3)
        bar_bg.pack(fill='x')
        tk.Frame(bar_bg, bg=ACCENT, height=3,
                 width=int(w * step / 3)).place(x=0, y=0)
        # ── footer FIRST — иначе body с expand=True съедает всё место ──
        tk.Frame(self, bg=BORDER, height=1).pack(fill='x', side='bottom')
        self.foot = tk.Frame(self, bg=PANEL, pady=12)
        self.foot.pack(fill='x', side='bottom')
        # content area — заполняет оставшееся пространство
        self.body = tk.Frame(self, bg=BG)
        self.body.pack(fill='both', expand=True, padx=20, pady=12)

# ─── ШАГ 1: МАТЕРИАЛ ─────────────────────────────────────────────────────────
class Step1Dialog(BaseDialog):
    def __init__(self, parent, on_next):
        super().__init__(parent, 'Выберите материал', 1, 3, 720, 600)
        self._on_next = on_next
        self._sel = tk.StringVar(value='')
        self._cards = {}
        self._build()

    def _build(self):
        tk.Label(self.body, text='Обрабатываемый материал',
                 bg=BG, fg=DIM, font=F_S).pack(anchor='w', pady=(0, 8))
        grid = tk.Frame(self.body, bg=BG)
        grid.pack(fill='both', expand=True)
        for i, (key, name, grp, desc) in enumerate(MATERIALS):
            r, c = divmod(i, 3)
            self._make_card(grid, key, grp, name, desc, r, c)
        styled_btn(self.foot, '  Отмена', self.destroy, primary=False).pack(
            side='left', padx=16)
        styled_btn(self.foot, 'Далее  →', self._next, primary=True).pack(
            side='right', padx=16)

    def _make_card(self, parent, key, grp, name, desc, row, col):
        f = tk.Frame(parent, bg=CARD, cursor='hand2', bd=2, relief='flat')
        f.grid(row=row, column=col, padx=5, pady=5, sticky='nsew')
        parent.grid_columnconfigure(col, weight=1)
        parent.grid_rowconfigure(row, weight=1)
        lbl_grp  = tk.Label(f, text=grp,  bg=CARD, fg=ACCENT, font=('Segoe UI', 10, 'bold'))
        lbl_name = tk.Label(f, text=name, bg=CARD, fg=TEXT,   font=('Segoe UI', 9,  'bold'), wraplength=150)
        lbl_desc = tk.Label(f, text=desc, bg=CARD, fg=DIM,    font=('Segoe UI', 8),           wraplength=150)
        lbl_grp.pack(anchor='w', padx=10, pady=(8,0))
        lbl_name.pack(anchor='w', padx=10)
        lbl_desc.pack(anchor='w', padx=10, pady=(0,8))
        self._cards[key] = (f, lbl_grp, lbl_name, lbl_desc)
        for w in (f, lbl_grp, lbl_name, lbl_desc):
            w.bind('<Button-1>', lambda e, k=key: self._select(k))

    def _select(self, key):
        # deselect all
        for k, (f, lg, ln, ld) in self._cards.items():
            bg = CARD_S if k == key else CARD
            fg_g = '#a0c8ff' if k == key else ACCENT
            for w in (f, lg, ln, ld):
                w.config(bg=bg)
            lg.config(fg=fg_g)
        self._sel.set(key)

    def _next(self):
        if not self._sel.get():
            messagebox.showwarning('Выбор', 'Выберите материал', parent=self)
            return
        self.destroy()
        self._on_next(self._sel.get())

# ─── ШАГ 2: ТИП ФРЕЗЫ ────────────────────────────────────────────────────────
class Step2Dialog(BaseDialog):
    def __init__(self, parent, mat, on_next, on_back=None):
        super().__init__(parent, 'Выберите тип фрезы', 2, 3, 700, 560)
        self._mat = mat
        self._on_next = on_next
        self._on_back = on_back
        self._sel_key = tk.StringVar(value='')
        self._cards = {}
        self._build()

    def _build(self):
        mat_name = next(n for k,n,*_ in MATERIALS if k==self._mat)
        tk.Label(self.body, text=f'Материал: {mat_name}',
                 bg=BG, fg=DIM, font=F_S).pack(anchor='w', pady=(0,8))
        grid = tk.Frame(self.body, bg=BG)
        grid.pack(fill='both', expand=True)
        for i, (key, name, has_ins, db_key) in enumerate(CUTTER_TYPES):
            r, c = divmod(i, 2)
            self._make_card(grid, key, name, has_ins, r, c)
        for c in range(2):
            grid.grid_columnconfigure(c, weight=1)

        styled_btn(self.foot, '← Назад', self._back, primary=False).pack(
            side='left', padx=16)
        styled_btn(self.foot, 'Далее  →', self._next, primary=True).pack(
            side='right', padx=16)

    def _back(self):
        self.destroy()
        if self._on_back:
            self._on_back()

    def _make_card(self, parent, key, name, has_ins, row, col):
        badge = 'ПЛАСТИНЫ' if has_ins else 'МОНОЛИТ'
        badge_c = YELLOW if has_ins else GREEN
        f = tk.Frame(parent, bg=CARD, cursor='hand2', bd=1, relief='flat')
        f.grid(row=row, column=col, padx=5, pady=4, sticky='ew')
        inner = tk.Frame(f, bg=CARD)
        inner.pack(fill='x', padx=10, pady=6)
        lbl_n = tk.Label(inner, text=name, bg=CARD, fg=TEXT, font=F_B, anchor='w')
        lbl_b = tk.Label(inner, text=badge, bg=CARD, fg=badge_c, font=('Segoe UI',7,'bold'))
        lbl_n.pack(side='left')
        lbl_b.pack(side='right')
        self._cards[key] = (f, inner, lbl_n, lbl_b)
        for w in (f, inner, lbl_n, lbl_b):
            w.bind('<Button-1>', lambda e, k=key: self._select(k))

    def _select(self, key):
        for k, (f, inn, ln, lb) in self._cards.items():
            bg = CARD_S if k == key else CARD
            for w in (f, inn, ln, lb):
                w.config(bg=bg)
        self._sel_key.set(key)

    def _next(self):
        k = self._sel_key.get()
        if not k:
            messagebox.showwarning('Выбор', 'Выберите тип фрезы', parent=self)
            return
        info = next(x for x in CUTTER_TYPES if x[0] == k)
        self.destroy()
        self._on_next(self._mat, k, info[1], info[2], info[3])

# ─── ШАГ 3: ПАРАМЕТРЫ ────────────────────────────────────────────────────────
class Step3Dialog(BaseDialog):
    def __init__(self, parent, mat, cutter_key, cutter_name, has_ins, db_key,
                 on_next, on_back=None):
        super().__init__(parent, 'Параметры инструмента', 3, 3, 500, 480)
        self._args = (mat, cutter_key, cutter_name, has_ins, db_key)
        self._on_next = on_next
        self._on_back = on_back
        self._build()

    def _build(self):
        mat, cutter_key, cutter_name, has_ins, db_key = self._args
        mat_name = next(n for k,n,*_ in MATERIALS if k==mat)

        tk.Label(self.body, text=f'{mat_name}   /   {cutter_name}',
                 bg=BG, fg=DIM, font=F_S).pack(anchor='w', pady=(0,16))

        def row(parent, label, var, default, hint=''):
            f = tk.Frame(parent, bg=BG)
            f.pack(fill='x', pady=6)
            tk.Label(f, text=label, bg=BG, fg=TEXT, font=F_B, width=22, anchor='w').pack(side='left')
            e = tk.Entry(f, textvariable=var, width=10, bg=CARD, fg=TEXT,
                         insertbackground=TEXT, font=F_M, relief='flat', bd=4)
            e.pack(side='left', padx=(0,8))
            if hint:
                tk.Label(f, text=hint, bg=BG, fg=DIM, font=F_S).pack(side='left')
            var.set(default)
            return e

        self._D = tk.StringVar()
        self._z = tk.StringVar()
        row(self.body, 'Диаметр фрезы  D (мм)', self._D, '12', 'мм')
        row(self.body, 'Число зубьев  z',        self._z, '4',  'шт')

        # ae slider
        tk.Label(self.body, text='Перекрытие  ae  (% от D)',
                 bg=BG, fg=TEXT, font=F_B).pack(anchor='w', pady=(14,4))

        self._ae = tk.IntVar(value=50)
        sl_f = tk.Frame(self.body, bg=CARD, padx=12, pady=8)
        sl_f.pack(fill='x')
        sl = tk.Scale(sl_f, from_=5, to=100, orient='horizontal',
                      variable=self._ae, bg=CARD, fg=TEXT,
                      troughcolor=BORDER, highlightthickness=0,
                      activebackground=ACCENT, font=F_S, showvalue=False,
                      command=lambda _: self._upd_ae())
        sl.pack(fill='x')
        self._ae_lbl = tk.Label(sl_f, text='ae = 50%', bg=CARD, fg=ACCENT, font=F_B)
        self._ae_lbl.pack()
        self._upd_ae()

        styled_btn(self.foot, '← Назад', self._back, primary=False).pack(
            side='left', padx=16)
        styled_btn(self.foot, 'Рассчитать  →', self._next, primary=True).pack(
            side='right', padx=16)

    def _back(self):
        self.destroy()
        if self._on_back:
            self._on_back()

    def _upd_ae(self):
        try:
            D = float(self._D.get())
            self._ae_lbl.config(text=f'ae = {self._ae.get()}%  =  {D*self._ae.get()/100:.2f} мм')
        except Exception:
            self._ae_lbl.config(text=f'ae = {self._ae.get()}%')

    def _next(self):
        try:
            D = float(self._D.get())
            assert D > 0
        except Exception:
            messagebox.showerror('Ошибка', 'Введите корректный диаметр D', parent=self)
            return
        try:
            z = int(self._z.get())
            assert z > 0
        except Exception:
            messagebox.showerror('Ошибка', 'Введите корректное число зубьев z', parent=self)
            return
        mat, cutter_key, cutter_name, has_ins, db_key = self._args
        self.destroy()
        self._on_next(mat, cutter_key, cutter_name, has_ins, db_key,
                      D, z, self._ae.get() / 100.0)

# ─── РЕЗУЛЬТАТ ────────────────────────────────────────────────────────────────
class ResultWindow(tk.Toplevel):
    def __init__(self, parent, mat, cutter_name, has_ins, db_key, D, z, ae_pct):
        super().__init__(parent)
        self.title('Результат — Режимы резания')
        self.configure(bg=BG)
        self.resizable(True, True)
        self.grab_set()
        center(self, 700, 640)
        self.transient(parent)
        self._build(mat, cutter_name, has_ins, db_key, D, z, ae_pct)

    def _build(self, mat, cutter_name, has_ins, db_key, D, z, ae_pct):
        tk.Frame(self, bg=ACCENT, height=4).pack(fill='x')
        hdr = tk.Frame(self, bg=PANEL, pady=10)
        hdr.pack(fill='x')
        tk.Label(hdr, text='РЕЗУЛЬТАТ — Режимы резания',
                 bg=PANEL, fg=TEXT, font=F_H).pack(side='left', padx=20)

        out = tk.Text(self, bg=BG, fg=TEXT, font=F_M, relief='flat', bd=12,
                      wrap='word', state='disabled', spacing1=3, spacing3=3)
        sb = tk.Scrollbar(self, command=out.yview, bg=PANEL)
        out.config(yscrollcommand=sb.set)
        sb.pack(side='right', fill='y')
        out.pack(fill='both', expand=True)

        out.tag_configure('h1',    foreground=ACCENT,  font=('Segoe UI',12,'bold'))
        out.tag_configure('val',   foreground=GREEN,   font=F_M)
        out.tag_configure('warn',  foreground=RED,     font=('Consolas',11,'bold'))
        out.tag_configure('ok',    foreground=GREEN,   font=('Consolas',11,'bold'))
        out.tag_configure('note',  foreground=YELLOW,  font=('Consolas',10,'italic'))
        out.tag_configure('lbl',   foreground=DIM,     font=F_M)
        out.tag_configure('sep',   foreground=BORDER,  font=F_MS)
        out.tag_configure('ins',   foreground='#c9a0dc', font=('Consolas',10))
        out.tag_configure('small', foreground=DIM,     font=F_MS)

        data = get_data(mat, db_key)
        mat_name = next(n for k,n,*_ in MATERIALS if k==mat)

        def w(text, tag='lbl'):
            out.configure(state='normal')
            out.insert('end', text, tag)
            out.configure(state='disabled')

        def sep():
            w('  ' + '─'*60 + '\n', 'sep')

        if not data:
            w('\n  Данные для выбранной комбинации отсутствуют.\n', 'warn')
            self._footer(out)
            return

        vc = data['vc']; fz = data['fz']; ap = data['ap']
        ae_r = data['ae']; ap_abs = data.get('ap_abs', False)
        coolant = data['coolant']; notes = data.get('notes', '')

        w('\n')
        w('  Материал   :  ', 'lbl');    w(f'{mat_name}\n', 'val')
        w('  Фреза      :  ', 'lbl');    w(f'{cutter_name}\n', 'val')
        w(f'  D = {D} мм   z = {z} зубьев\n', 'h1')
        w('\n')
        sep()

        # Vc → n
        w('\n  Скорость резания       Vc  :  ', 'h1')
        w(f'{vc[0]} – {vc[1]}  м/мин\n', 'val')

        rpm_lo = int(vc[0]*1000/(math.pi*D))
        rpm_hi = int(vc[1]*1000/(math.pi*D))
        w('  Обороты шпинделя       n   :  ', 'h1')
        w(f'{rpm_lo:,} – {rpm_hi:,}  об/мин\n', 'val')

        # fz → Vf
        w('\n  Подача на зуб         fz   :  ', 'h1')
        w(f'{fz[0]:.3f} – {fz[1]:.3f}  мм/зуб\n', 'val')

        vf_lo = int(fz[0]*z*rpm_lo)
        vf_hi = int(fz[1]*z*rpm_hi)
        w('  Подача стола           Vf   :  ', 'h1')
        w(f'{vf_lo:,} – {vf_hi:,}  мм/мин\n', 'val')

        # ap
        w('\n  Глубина резания        ap   :  ', 'h1')
        if ap_abs:
            w(f'{ap[0]:.2f} – {ap[1]:.2f}  мм  (абсолютное)\n', 'val')
        else:
            w(f'{ap[0]:.2f}·D – {ap[1]:.2f}·D  =  {ap[0]*D:.2f} – {ap[1]*D:.2f}  мм\n', 'val')

        # ae
        ae_mm = round(D * ae_pct, 2)
        in_range = ae_r[0] <= ae_pct <= ae_r[1]
        w('  Перекрытие             ae   :  ', 'h1')
        pct_str = f'{int(ae_pct*100)}%  =  {ae_mm} мм'
        if in_range:
            w(f'{pct_str}  ✓\n', 'ok')
        else:
            w(f'{pct_str}  ← ВНЕ ДИАПАЗОНА!\n', 'warn')
            w(f'  {"":42} Норма: {int(ae_r[0]*100)}–{int(ae_r[1]*100)}%\n', 'note')

        # СОЖ
        w('\n')
        sep()
        w('\n  СОЖ  :  ', 'h1')
        if coolant == 'yes':
            w('  ОБЯЗАТЕЛЬНО  (эмульсия / масло, обильно)\n', 'warn')
        elif coolant == 'opt':
            w('  Рекомендуется  (или сухая + обдув)\n', 'ok')
        else:
            w('  НЕ ПРИМЕНЯТЬ  —  сухая обработка / воздушный обдув\n', 'ok')

        # Примечания
        if notes:
            w(f'\n  ⚠  {notes}\n', 'note')

        # Рекомендация инструмента
        w('\n')
        sep()
        w('\n  РЕКОМЕНДУЕМЫЙ ИНСТРУМЕНТ\n', 'h1')

        solid_rec, idx_rec = INSERT_REC.get(mat, ('', ''))
        if db_key == 'highfeed':
            w(f'  Тип пластины  :  ', 'lbl')
            w(HF_INSERT_REC.get(mat, idx_rec) + '\n', 'ins')
            w('  Форма         :  ', 'lbl')
            w('XNMU / ONMU / RDHX  —  угол наклона 15–18°, позитивная геометрия\n', 'ins')
            w('  Принцип       :  ', 'lbl')
            w('Chip thinning: реальная толщина стружки << fz (программный)\n', 'ins')
            w('  Формула       :  ', 'lbl')
            w('hex = fz × sin(KAPR),  KAPR ≈ 15–18°\n', 'ins')
        elif has_ins:
            w(f'  Пластины      :  ', 'lbl')
            w(idx_rec + '\n', 'ins')
        else:
            w(f'  Покрытие ТС   :  ', 'lbl')
            w(solid_rec + '\n', 'ins')

        w('\n')
        sep()
        w('\n  Черновая:  нижний Vc, верхний fz, максимальный ap\n', 'small')
        w('  Чистовая:  верхний Vc, нижний fz, меньший ap\n', 'small')
        w('  * Данные усреднённые — уточняйте по каталогу производителя.\n', 'small')

        self._footer(out)

    def _footer(self, out):
        foot = tk.Frame(self, bg=PANEL, pady=10)
        foot.pack(fill='x', side='bottom')
        styled_btn(foot, '  Закрыть', self.destroy, primary=False).pack(
            side='right', padx=16)
        styled_btn(foot, '← Новый расчёт', lambda: [self.destroy()], primary=True).pack(
            side='left', padx=16)

# ─── ОКНО НАСТРОЕК ───────────────────────────────────────────────────────────
class SettingsWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title('База данных и формулы')
        self.configure(bg=BG)
        self.resizable(True, True)
        center(self, 1100, 720)
        self.transient(parent)
        self._build()

    def _build(self):
        tk.Frame(self, bg=ACCENT, height=4).pack(fill='x')

        hdr = tk.Frame(self, bg=PANEL, pady=10)
        hdr.pack(fill='x')
        tk.Label(hdr, text='База данных и формулы',
                 bg=PANEL, fg=TEXT, font=F_H).pack(side='left', padx=20)
        styled_btn(hdr, '  Закрыть', self.destroy, primary=False).pack(
            side='right', padx=16)

        tab_bar = tk.Frame(self, bg=CARD)
        tab_bar.pack(fill='x')
        tk.Frame(self, bg=BORDER, height=1).pack(fill='x')

        self._content = tk.Frame(self, bg=BG)
        self._content.pack(fill='both', expand=True)

        self._tab_frames = {}
        self._tab_btns   = {}
        for key, label in [('formulas', '  Формулы расчёта  '),
                            ('table',    '  База режимов резания  ')]:
            f = tk.Frame(self._content, bg=BG)
            self._tab_frames[key] = f
            btn = tk.Button(tab_bar, text=label, relief='flat', bd=0,
                           bg=CARD, fg=DIM, font=F_B, padx=8, pady=10,
                           cursor='hand2', activebackground=BG,
                           activeforeground=TEXT,
                           command=lambda k=key: self._show_tab(k))
            btn.pack(side='left')
            self._tab_btns[key] = btn

        self._build_formulas(self._tab_frames['formulas'])
        self._build_table(self._tab_frames['table'])
        self._show_tab('formulas')

    def _show_tab(self, key):
        for f in self._tab_frames.values():
            f.pack_forget()
        self._tab_frames[key].pack(fill='both', expand=True)
        for k, btn in self._tab_btns.items():
            btn.config(bg=BG if k == key else CARD,
                       fg=ACCENT if k == key else DIM)

    # ── Формулы ──────────────────────────────────────────────────────────────
    def _build_formulas(self, parent):
        t = tk.Text(parent, bg=BG, fg=TEXT, font=('Consolas', 11),
                    relief='flat', bd=0, wrap='word', state='disabled',
                    spacing1=4, spacing3=4, padx=28, pady=14)
        sb = tk.Scrollbar(parent, command=t.yview, bg=PANEL,
                         troughcolor=BG, activebackground=ACCENT,
                         relief='flat', bd=0, width=12)
        t.config(yscrollcommand=sb.set)
        sb.pack(side='right', fill='y')
        t.pack(fill='both', expand=True)

        t.tag_configure('title',  foreground=ACCENT,    font=('Consolas', 14, 'bold'))
        t.tag_configure('head',   foreground=YELLOW,    font=('Consolas', 12, 'bold'))
        t.tag_configure('code',   foreground=GREEN,     font=('Consolas', 12, 'bold'))
        t.tag_configure('dim',    foreground=DIM,       font=('Consolas', 10))
        t.tag_configure('normal', foreground=TEXT,      font=('Consolas', 11))
        t.tag_configure('sep',    foreground=BORDER,    font=('Consolas', 11))
        t.tag_configure('num',    foreground=ACCENT,    font=('Consolas', 13, 'bold'))
        t.tag_configure('hi',     foreground='#c9a0dc', font=('Consolas', 11))

        def w(text, tag='normal'):
            t.configure(state='normal')
            t.insert('end', text, tag)
            t.configure(state='disabled')

        def sep():
            w('\n  ' + '─' * 68 + '\n', 'sep')

        w('\n')
        w('  ФОРМУЛЫ РАСЧЁТА РЕЖИМОВ РЕЗАНИЯ\n', 'title')
        w('  Справочник параметров фрезерной обработки\n\n', 'dim')
        sep()

        w('\n  1  ', 'num'); w('ОБОРОТЫ ШПИНДЕЛЯ\n', 'head')
        w('\n         Vc × 1000\n', 'code')
        w('    n = ───────────    об/мин\n', 'code')
        w('           π × D\n\n', 'code')
        w('    Vc — скорость резания, м/мин      D — диаметр фрезы, мм      π = 3.14159\n', 'dim')

        sep()
        w('\n  2  ', 'num'); w('ПОДАЧА СТОЛА (минутная подача)\n', 'head')
        w('\n    Vf = fz × z × n    мм/мин\n\n', 'code')
        w('    fz — подача на зуб, мм/зуб      z — число зубьев      n — об/мин\n', 'dim')

        sep()
        w('\n  3  ', 'num'); w('РАДИАЛЬНОЕ ПЕРЕКРЫТИЕ\n', 'head')
        w('\n    ae = ae% × D    мм\n\n', 'code')
        w('    ae% — процент перекрытия от диаметра (5–100%)\n', 'dim')

        sep()
        w('\n  4  ', 'num'); w('ГЛУБИНА РЕЗАНИЯ (осевая)\n', 'head')
        w('\n    ap = ratio × D   мм  — обычные фрезы (ratio задаётся в базе)\n', 'code')
        w('    ap = абс. мм      мм  — High-Feed фрезы (абсолютное значение)\n\n', 'code')

        sep()
        w('\n  5  ', 'num'); w('HIGH-FEED — УТОНЬШЕНИЕ СТРУЖКИ  (Chip Thinning)\n', 'head')
        w('\n    hex = fz × sin(KAPR)    мм  — реальная толщина стружки\n\n', 'code')
        w('    KAPR — угол наклона пластины (lead angle), типично 15–18°\n', 'dim')
        w('    sin(15°) ≈ 0.259     sin(18°) ≈ 0.309\n', 'dim')
        w('    Пример: fz = 2.0 мм/зуб  →  hex = 2.0 × 0.259 = 0.52 мм\n\n', 'dim')
        w('    ► ', 'hi'); w('Тепло уходит со стружкой — СОЖ не нужен (сталь / чугун)\n', 'normal')
        w('    ► ', 'hi'); w('Малый ap при большом fz = высокая производительность\n', 'normal')

        sep()
        w('\n  6  ', 'num'); w('СТРАТЕГИЯ ОБРАБОТКИ\n', 'head')
        w('\n    Черновая:  ', 'normal'); w('нижний Vc,  верхний fz,  максимальный ap\n', 'dim')
        w('    Чистовая:  ', 'normal'); w('верхний Vc, нижний  fz,  меньший    ap\n\n', 'dim')

        sep()
        w('\n  7  ', 'num'); w('ГРУППЫ ISO ПЛАСТИН\n', 'head')
        iso_rows = [
            ('P', 'Сталь конструкционная / легированная', 'Синяя',      'TiAlN, AlTiN, AlCrN'),
            ('M', 'Нержавейка / нейтральные сплавы',      'Жёлтая',     'PVD TiAlN, AlCrN'),
            ('K', 'Чугун (серый, ковкий, ВЧ)',            'Красная',    'TiAlN, uncoated, PCBN'),
            ('N', 'Алюминий / цветные металлы',           'Зелёная',    'Uncoated, TiB₂'),
            ('S', 'Жаропрочные / титановые сплавы',       'Коричневая', 'TiAlN-X, uncoated fine grain'),
            ('H', 'Закалённые стали HRC 40+',             'Серая',      'CBN, PcBN'),
        ]
        w('\n')
        for grp, mat_n, color, coat in iso_rows:
            w('    '); w(f'{grp}', 'code')
            w(f'  —  {mat_n:<42} {color:<14} {coat}\n', 'dim')

        w('\n')

    # ── Таблица данных ────────────────────────────────────────────────────────
    def _build_table(self, parent):
        fbar = tk.Frame(parent, bg=PANEL, padx=16, pady=8)
        fbar.pack(fill='x')

        tk.Label(fbar, text='Материал:', bg=PANEL, fg=DIM,
                 font=('Segoe UI', 9, 'bold')).pack(side='left')

        mat_names = ['Все'] + [n for _, n, *__ in MATERIALS]
        self._flt_mat_var = tk.StringVar(value='Все')
        om_mat = tk.OptionMenu(fbar, self._flt_mat_var, *mat_names,
                               command=lambda _: self._populate())
        om_mat.config(bg=CARD, fg=TEXT, font=F_S, relief='flat', bd=0,
                     activebackground=CARD_H, activeforeground=TEXT,
                     highlightthickness=1, highlightbackground=BORDER,
                     padx=10, pady=4)
        om_mat['menu'].config(bg=CARD, fg=TEXT, font=F_S, relief='flat',
                              activebackground=CARD_S, activeforeground=TEXT, bd=0)
        om_mat.pack(side='left', padx=(4, 20))

        tk.Label(fbar, text='Фреза:', bg=PANEL, fg=DIM,
                 font=('Segoe UI', 9, 'bold')).pack(side='left')

        ct_names = ['Все'] + [n for _, n, *__ in CUTTER_TYPES]
        self._flt_ct_var = tk.StringVar(value='Все')
        om_ct = tk.OptionMenu(fbar, self._flt_ct_var, *ct_names,
                              command=lambda _: self._populate())
        om_ct.config(bg=CARD, fg=TEXT, font=F_S, relief='flat', bd=0,
                    activebackground=CARD_H, activeforeground=TEXT,
                    highlightthickness=1, highlightbackground=BORDER,
                    padx=10, pady=4)
        om_ct['menu'].config(bg=CARD, fg=TEXT, font=F_S, relief='flat',
                             activebackground=CARD_S, activeforeground=TEXT, bd=0)
        om_ct.pack(side='left', padx=(4, 0))

        styled_btn(fbar, 'Сбросить', lambda: [
            self._flt_mat_var.set('Все'),
            self._flt_ct_var.set('Все'),
            self._populate()
        ], primary=False).pack(side='left', padx=14)

        styled_btn(fbar, '  Сохранить изменения  ', self._save,
                   primary=True).pack(side='right')

        cols = ('mat','ct','vc_lo','vc_hi','fz_lo','fz_hi',
                'ap_lo','ap_hi','ae_lo','ae_hi','ap_abs','coolant','notes')
        hdrs = ('Материал','Фреза','Vc↓','Vc↑','fz↓','fz↑',
                'ap↓','ap↑','ae↓','ae↑','ap абс','СОЖ','Примечание')
        widths = (140, 160, 45, 45, 55, 55, 50, 50, 50, 50, 52, 55, 200)

        frm = tk.Frame(parent, bg=BG)
        frm.pack(fill='both', expand=True)

        s = ttk.Style()
        s.configure('Data.Treeview',
                    background=CARD, fieldbackground=CARD,
                    foreground=TEXT, rowheight=24, font=F_MS, borderwidth=0)
        s.configure('Data.Treeview.Heading',
                    background=PANEL, foreground=DIM,
                    font=('Segoe UI', 9, 'bold'), relief='flat')
        s.map('Data.Treeview',
              background=[('selected', CARD_S)],
              foreground=[('selected', TEXT)])
        s.map('Data.Treeview.Heading',
              background=[('active', CARD_H)],
              foreground=[('active', TEXT)])

        self._tv = ttk.Treeview(frm, columns=cols, show='headings',
                                style='Data.Treeview')
        vsb = tk.Scrollbar(frm, command=self._tv.yview, bg=PANEL,
                          troughcolor=BG, activebackground=ACCENT,
                          relief='flat', bd=0, width=12)
        hsb = tk.Scrollbar(frm, command=self._tv.xview, orient='horizontal',
                          bg=PANEL, troughcolor=BG, activebackground=ACCENT,
                          relief='flat', bd=0, width=12)
        self._tv.config(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.pack(side='right', fill='y')
        hsb.pack(side='bottom', fill='x')
        self._tv.pack(fill='both', expand=True)

        for col, hdr, w in zip(cols, hdrs, widths):
            self._tv.heading(col, text=hdr)
            self._tv.column(col, width=w, minwidth=30, anchor='center')
        self._tv.column('mat',   anchor='w')
        self._tv.column('ct',    anchor='w')
        self._tv.column('notes', anchor='w')

        self._tv.tag_configure('odd',  background=CARD)
        self._tv.tag_configure('even', background='#1a2030')

        self._tv.bind('<Double-1>', self._on_dbl)
        self._populate()

    def _populate(self):
        fmat = self._flt_mat_var.get()
        fct  = self._flt_ct_var.get()
        self._tv.delete(*self._tv.get_children())
        mat_map  = {n: k for k, n, *_ in MATERIALS}
        ct_map   = {n: k for k, n, *_ in CUTTER_TYPES}
        fmat_key = mat_map.get(fmat)
        fct_key  = ct_map.get(fct)

        row_idx = 0
        for (mat, ct), d in sorted(CUTTING_DATA.items()):
            if fmat != 'Все' and mat != fmat_key:
                continue
            if fct != 'Все':
                db_key = next((dk for k, _, __, dk in CUTTER_TYPES
                               if k == fct_key), None)
                if ct != db_key:
                    continue
            mat_name = next((n for k, n, *_ in MATERIALS if k == mat), mat)
            ct_name  = next((n for k, n, _, dk in CUTTER_TYPES if dk == ct), ct)
            ap_abs_s = 'мм' if d.get('ap_abs') else '×D'
            cool_s   = {'yes': 'ДА', 'no': 'НЕТ', 'opt': 'ОПЦ'}.get(
                d['coolant'], d['coolant'])
            tag = 'odd' if row_idx % 2 == 0 else 'even'
            self._tv.insert('', 'end', iid=f'{mat}|{ct}',
                values=(mat_name, ct_name,
                        d['vc'][0], d['vc'][1],
                        d['fz'][0], d['fz'][1],
                        d['ap'][0], d['ap'][1],
                        d['ae'][0], d['ae'][1],
                        ap_abs_s, cool_s, d.get('notes', '')),
                tags=(tag,))
            row_idx += 1

    def _on_dbl(self, event):
        iid = self._tv.focus()
        if not iid:
            return
        mat, ct = iid.split('|')
        data = CUTTING_DATA.get((mat, ct))
        if not data:
            return
        EditRowDialog(self, mat, ct, data, self._after_edit)

    def _after_edit(self, mat, ct, new_data):
        CUTTING_DATA[(mat, ct)] = new_data
        self._populate()

    def _save(self):
        try:
            save_data(CUTTING_DATA)
            messagebox.showinfo('Сохранено',
                f'База данных сохранена:\n{data_path()}', parent=self)
        except Exception as e:
            messagebox.showerror('Ошибка', str(e), parent=self)

# ─── РЕДАКТОР СТРОКИ ──────────────────────────────────────────────────────────
class EditRowDialog(tk.Toplevel):
    def __init__(self, parent, mat, ct, data, callback):
        super().__init__(parent)
        self.title('Редактировать строку')
        self.configure(bg=BG)
        self.resizable(False, False)
        self.grab_set()
        center(self, 420, 500)
        self.transient(parent)
        self._mat = mat; self._ct = ct; self._cb = callback
        self._build(data)

    def _build(self, d):
        mat_name = next((n for k,n,*_ in MATERIALS if k==self._mat), self._mat)
        ct_name  = next((n for k,n,_,dk in CUTTER_TYPES if dk==self._ct), self._ct)

        body = tk.Frame(self, bg=BG, padx=20, pady=16)
        body.pack(fill='both', expand=True)

        tk.Label(body, text=f'{mat_name}', bg=BG, fg=ACCENT, font=F_H).pack(anchor='w')
        tk.Label(body, text=ct_name, bg=BG, fg=DIM, font=F_B).pack(anchor='w', pady=(0,14))

        def pair(label, lo_val, hi_val, unit=''):
            f = tk.Frame(body, bg=BG)
            f.pack(fill='x', pady=4)
            tk.Label(f, text=label, bg=BG, fg=TEXT, font=F_S, width=18, anchor='w').pack(side='left')
            lo = tk.StringVar(value=str(lo_val))
            hi = tk.StringVar(value=str(hi_val))
            tk.Entry(f, textvariable=lo, width=8, bg=CARD, fg=TEXT,
                     insertbackground=TEXT, font=F_M, relief='flat', bd=3).pack(side='left', padx=2)
            tk.Label(f, text='–', bg=BG, fg=DIM, font=F_B).pack(side='left')
            tk.Entry(f, textvariable=hi, width=8, bg=CARD, fg=TEXT,
                     insertbackground=TEXT, font=F_M, relief='flat', bd=3).pack(side='left', padx=2)
            if unit:
                tk.Label(f, text=unit, bg=BG, fg=DIM, font=F_S).pack(side='left', padx=4)
            return lo, hi

        self._vc  = pair('Vc (м/мин)',   d['vc'][0], d['vc'][1], 'м/мин')
        self._fz  = pair('fz (мм/зуб)',  d['fz'][0], d['fz'][1], 'мм/зуб')
        self._ap  = pair('ap',           d['ap'][0], d['ap'][1])
        self._ae  = pair('ae (×D)',       d['ae'][0], d['ae'][1], '×D')

        # ap_abs
        f3 = tk.Frame(body, bg=BG)
        f3.pack(fill='x', pady=4)
        tk.Label(f3, text='ap — абсолютное (мм)', bg=BG, fg=TEXT, font=F_S, width=18, anchor='w').pack(side='left')
        self._ap_abs = tk.BooleanVar(value=d.get('ap_abs', False))
        tk.Checkbutton(f3, variable=self._ap_abs, bg=BG, fg=TEXT,
                       selectcolor=CARD, activebackground=BG, font=F_S,
                       text='да').pack(side='left')

        # coolant
        f4 = tk.Frame(body, bg=BG)
        f4.pack(fill='x', pady=4)
        tk.Label(f4, text='СОЖ', bg=BG, fg=TEXT, font=F_S, width=18, anchor='w').pack(side='left')
        self._cool = tk.StringVar(value=d['coolant'])
        for val, lbl in (('yes','Обязателен'),('opt','Опционально'),('no','Не применять')):
            tk.Radiobutton(f4, text=lbl, variable=self._cool, value=val,
                           bg=BG, fg=TEXT, selectcolor=CARD, activebackground=BG,
                           font=F_S).pack(side='left', padx=4)

        # notes
        tk.Label(body, text='Примечание', bg=BG, fg=TEXT, font=F_S).pack(anchor='w', pady=(8,2))
        self._notes = tk.Text(body, bg=CARD, fg=TEXT, font=F_S, relief='flat',
                              bd=4, height=3, insertbackground=TEXT)
        self._notes.insert('1.0', d.get('notes',''))
        self._notes.pack(fill='x')

        foot = tk.Frame(self, bg=PANEL, pady=8)
        foot.pack(fill='x', side='bottom')
        styled_btn(foot, 'Отмена', self.destroy, primary=False).pack(side='left', padx=12)
        styled_btn(foot, 'Сохранить', self._save, primary=True).pack(side='right', padx=12)

    def _save(self):
        try:
            def g(pair): return (float(pair[0].get()), float(pair[1].get()))
            new = {
                'vc':     g(self._vc),
                'fz':     g(self._fz),
                'ap':     g(self._ap),
                'ae':     g(self._ae),
                'ap_abs': self._ap_abs.get(),
                'coolant':self._cool.get(),
                'notes':  self._notes.get('1.0','end').strip(),
            }
            self.destroy()
            self._cb(self._mat, self._ct, new)
        except ValueError as e:
            messagebox.showerror('Ошибка', f'Некорректное число: {e}', parent=self)

# ─── ЗАПУСК ───────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    app = MainWindow()
    app.mainloop()
