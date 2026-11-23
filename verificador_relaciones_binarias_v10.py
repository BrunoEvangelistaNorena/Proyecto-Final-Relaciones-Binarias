"""
Verificador de propiedades de relaciones binarias - v10

Estructura:
  1. Lógica (funciones puras, sin interfaz): lectura de datos, propiedades
     con contraejemplos, clausuras, clases de equivalencia y diagrama de Hasse.
  2. Interfaz gráfica (tkinter).
"""

import math
import re
import tkinter as tk
from dataclasses import dataclass, field
from tkinter import ttk, messagebox, filedialog

MAX_ELEMENTOS = 20
MAX_EJEMPLOS = 6  # contraejemplos mostrados por propiedad

_ELEM = r"[^\s,;(){}]+"
_PAR_RE = re.compile(r"\(\s*(" + _ELEM + r")\s*,\s*(" + _ELEM + r")\s*\)")


# =====================================================================
# 1. LÓGICA
# =====================================================================

@dataclass
class Propiedad:
    nombre: str
    grupo: str                 # "basica" o "tipo"
    cumple: bool
    definicion: str
    detalle: str
    resaltar: set = field(default_factory=set)    # pares de R implicados
    faltantes: set = field(default_factory=set)   # pares que faltan en R
    componentes: list = field(default_factory=list)


def parsear_conjunto(texto):
    """'4' -> ['1','2','3','4'];  'a, b, c' o '{a,b,c}' -> ['a','b','c']."""
    t = texto.strip()
    if not t:
        raise ValueError("Ingresa el conjunto A: una cantidad (ej. 4) "
                         "o sus elementos (ej. a, b, c).")
    if re.fullmatch(r"\d+", t):
        n = int(t)
        if not 1 <= n <= MAX_ELEMENTOS:
            raise ValueError(f"La cantidad de elementos debe estar entre 1 y {MAX_ELEMENTOS}.")
        return [str(i) for i in range(1, n + 1)]

    if t.startswith("{") and t.endswith("}"):
        t = t[1:-1]
    elementos = [e for e in re.split(r"[,;\s]+", t) if e]
    if not elementos:
        raise ValueError("El conjunto A no puede ser vacío.")
    for e in elementos:
        if not re.fullmatch(_ELEM, e):
            raise ValueError(f"Elemento no válido en A: «{e}».")
    repetidos = sorted({e for e in elementos if elementos.count(e) > 1})
    if repetidos:
        raise ValueError("Elementos repetidos en A: " + ", ".join(repetidos) + ".")
    if len(elementos) > MAX_ELEMENTOS:
        raise ValueError(f"A puede tener como máximo {MAX_ELEMENTOS} elementos.")
    return elementos


def parsear_pares(texto, A):
    """Devuelve (pares_sin_repetir, repetidos). Texto vacío = relación vacía."""
    t = texto.strip()
    t = re.sub(r"^R\s*=\s*", "", t)
    encontrados = _PAR_RE.findall(t)
    resto = _PAR_RE.sub("", t)
    if not re.fullmatch(r"[\s,;{}]*", resto):
        raise ValueError("Formato incorrecto. Escribe pares como (1,2); (2,3) "
                         "o uno por línea.")
    conjunto_A = set(A)
    fuera = [f"({a},{b})" for a, b in encontrados
             if a not in conjunto_A or b not in conjunto_A]
    if fuera:
        raise ValueError("Estos pares usan elementos que no están en A: "
                         + ", ".join(fuera[:8]) + (" …" if len(fuera) > 8 else ""))
    vistos, pares, repetidos = set(), [], []
    for p in encontrados:
        if p in vistos:
            repetidos.append(p)
        else:
            vistos.add(p)
            pares.append(p)
    return pares, repetidos


def ordenar(pares, A):
    idx = {a: i for i, a in enumerate(A)}
    return sorted(pares, key=lambda p: (idx[p[0]], idx[p[1]]))


def fmt_par(p):
    return f"({p[0]},{p[1]})"


def fmt_conjunto(elems):
    return "{" + ", ".join(elems) + "}"


def fmt_relacion(pares, A):
    return "{" + ", ".join(fmt_par(p) for p in ordenar(pares, A)) + "}" if pares else "∅"


def _lista(items, fmt):
    textos = [fmt(x) for x in items[:MAX_EJEMPLOS]]
    extra = len(items) - MAX_EJEMPLOS
    return "; ".join(textos) + (f"; … y {extra} más" if extra > 0 else "")


def _y(nombres):
    nombres = [n.lower() for n in nombres]
    return nombres[0] if len(nombres) == 1 else ", ".join(nombres[:-1]) + " y " + nombres[-1]


TIPOS = [
    ("Preorden", ["Reflexiva", "Transitiva"]),
    ("Relación de equivalencia", ["Reflexiva", "Simétrica", "Transitiva"]),
    ("Orden parcial", ["Reflexiva", "Antisimétrica", "Transitiva"]),
    ("Orden total", ["Reflexiva", "Antisimétrica", "Transitiva", "Total (conexa)"]),
    ("Orden estricto", ["Irreflexiva", "Transitiva"]),
]


def verificar_propiedades(A, R):
    """Devuelve una lista de Propiedad (básicas y tipos) con contraejemplos."""
    R = set(R)
    idx = {a: i for i, a in enumerate(A)}
    Rord = ordenar(R, A)
    sucesores = {a: [] for a in A}
    for a, b in Rord:
        sucesores[a].append(b)
    props = {}

    faltan = [(a, a) for a in A if (a, a) not in R]
    props["Reflexiva"] = Propiedad(
        "Reflexiva", "basica", not faltan,
        "Para todo a ∈ A: (a,a) ∈ R.",
        "Todos los elementos se relacionan consigo mismos." if not faltan
        else "Faltan los lazos " + _lista(faltan, fmt_par) + ".",
        faltantes=set(faltan))

    lazos = [(a, a) for a in A if (a, a) in R]
    props["Irreflexiva"] = Propiedad(
        "Irreflexiva", "basica", not lazos,
        "Para todo a ∈ A: (a,a) ∉ R.",
        "Ningún elemento se relaciona consigo mismo." if not lazos
        else "Sobran los lazos " + _lista(lazos, fmt_par) + ".",
        resaltar=set(lazos))

    viol = [(a, b) for a, b in Rord if (b, a) not in R]
    props["Simétrica"] = Propiedad(
        "Simétrica", "basica", not viol,
        "Si (a,b) ∈ R, entonces (b,a) ∈ R.",
        "Cada par tiene su recíproco." if not viol
        else _lista(viol, lambda p: f"{fmt_par(p)} ∈ R pero ({p[1]},{p[0]}) ∉ R") + ".",
        resaltar=set(viol), faltantes={(b, a) for a, b in viol})

    viol = [(a, b) for a, b in Rord if a != b and (b, a) in R and idx[a] < idx[b]]
    props["Antisimétrica"] = Propiedad(
        "Antisimétrica", "basica", not viol,
        "Si (a,b) ∈ R y (b,a) ∈ R, entonces a = b.",
        "No hay pares recíprocos entre elementos distintos." if not viol
        else _lista(viol, lambda p: f"{fmt_par(p)} y ({p[1]},{p[0]}) ∈ R, pero {p[0]} ≠ {p[1]}") + ".",
        resaltar={q for a, b in viol for q in ((a, b), (b, a))})

    viol = [(a, b) for a, b in Rord if (b, a) in R and idx[a] <= idx[b]]
    props["Asimétrica"] = Propiedad(
        "Asimétrica", "basica", not viol,
        "Si (a,b) ∈ R, entonces (b,a) ∉ R (en particular, no hay lazos).",
        "Ningún par tiene recíproco ni hay lazos." if not viol
        else _lista(viol, lambda p: f"{fmt_par(p)} ∈ R (es un lazo)" if p[0] == p[1]
                    else f"{fmt_par(p)} y ({p[1]},{p[0]}) ∈ R") + ".",
        resaltar={q for a, b in viol for q in ((a, b), (b, a))})

    triples, faltan_t = [], []
    for a, b in Rord:
        for c in sucesores[b]:
            if (a, c) not in R:
                triples.append((a, b, c))
                if (a, c) not in faltan_t:
                    faltan_t.append((a, c))
    detalle = "Toda cadena (a,b), (b,c) tiene su atajo (a,c)."
    if triples:
        detalle = (_lista(triples, lambda t: f"({t[0]},{t[1]}) y ({t[1]},{t[2]}) ∈ R "
                                             f"pero ({t[0]},{t[2]}) ∉ R")
                   + f".  Faltan {len(faltan_t)} par(es): " + _lista(faltan_t, fmt_par) + ".")
    props["Transitiva"] = Propiedad(
        "Transitiva", "basica", not triples,
        "Si (a,b) ∈ R y (b,c) ∈ R, entonces (a,c) ∈ R.", detalle,
        resaltar={q for a, b, c in triples for q in ((a, b), (b, c))},
        faltantes=set(faltan_t))

    viol = [(a, b) for i, a in enumerate(A) for b in A[i:]
            if (a, b) not in R and (b, a) not in R]
    props["Total (conexa)"] = Propiedad(
        "Total (conexa)", "basica", not viol,
        "Para todo a, b ∈ A: (a,b) ∈ R o (b,a) ∈ R.",
        "Todo par de elementos es comparable." if not viol
        else _lista(viol, lambda p: f"falta el lazo ({p[0]},{p[0]})" if p[0] == p[1]
                    else f"{p[0]} y {p[1]} no son comparables") + ".",
        faltantes=set(viol))

    for nombre, requisitos in TIPOS:
        fallan = [r for r in requisitos if not props[r].cumple]
        definicion = "Debe ser " + _y(requisitos) + "."
        if nombre == "Orden estricto":
            definicion += " (Eso implica que también es asimétrica.)"
        props[nombre] = Propiedad(
            nombre, "tipo", not fallan, definicion,
            "Cumple todas las condiciones." if not fallan
            else "No es " + _y(fallan) + ".",
            resaltar=set().union(*(props[r].resaltar for r in fallan)) if fallan else set(),
            faltantes=set().union(*(props[r].faltantes for r in fallan)) if fallan else set(),
            componentes=requisitos)

    orden = ["Reflexiva", "Irreflexiva", "Simétrica", "Antisimétrica", "Asimétrica",
             "Transitiva", "Total (conexa)"] + [t[0] for t in TIPOS]
    return [props[n] for n in orden]


def clausura_reflexiva(A, R):
    return set(R) | {(a, a) for a in A}


def clausura_simetrica(A, R):
    return set(R) | {(b, a) for a, b in R}


def clausura_transitiva(A, R):
    """Algoritmo de Warshall."""
    M = set(R)
    for k in A:
        for i in A:
            if (i, k) in M:
                for j in A:
                    if (k, j) in M:
                        M.add((i, j))
    return M


def clases_equivalencia(A, R):
    clases, asignados = [], set()
    for a in A:
        if a not in asignados:
            clase = [b for b in A if (a, b) in R]
            asignados.update(clase)
            clases.append((a, clase))
    return clases


def cubrimientos_hasse(A, R):
    R = set(R)
    return [(a, b) for a, b in ordenar(R, A) if a != b and not any(
        c != a and c != b and (a, c) in R and (c, b) in R for c in A)]


def niveles_hasse(A, cubrimientos):
    debajo = {a: [x for x, y in cubrimientos if y == a] for a in A}
    memo = {}

    def nivel(a):
        if a not in memo:
            memo[a] = 0 if not debajo[a] else 1 + max(nivel(x) for x in debajo[a])
        return memo[a]

    return {a: nivel(a) for a in A}


def analizar(A, R, props):
    R = set(R)
    p = {x.nombre: x for x in props}
    resultado = {
        "dominio": [a for a in A if any((a, b) in R for b in A)],
        "imagen": [b for b in A if any((a, b) in R for a in A)],
        "clases": clases_equivalencia(A, R) if p["Relación de equivalencia"].cumple else None,
        "orden": None,
        "clausuras": [],
    }
    if p["Orden parcial"].cumple:
        cub = cubrimientos_hasse(A, R)
        resultado["orden"] = {
            "minimales": [a for a in A if not any(b != a and (b, a) in R for b in A)],
            "maximales": [a for a in A if not any(b != a and (a, b) in R for b in A)],
            "minimo": [a for a in A if all((a, b) in R for b in A)],
            "maximo": [a for a in A if all((b, a) in R for b in A)],
            "cubrimientos": cub,
            "niveles": niveles_hasse(A, cub),
        }
    for nombre, f in (("reflexiva", clausura_reflexiva), ("simétrica", clausura_simetrica),
                      ("transitiva", clausura_transitiva)):
        C = f(A, R)
        resultado["clausuras"].append((nombre, ordenar(C - R, A), C))
    return resultado


def matriz_texto(A, R):
    w = max(len(a) for a in A)
    lineas = [" " * (w + 3) + " ".join(a.rjust(w) for a in A)]
    for a in A:
        lineas.append(a.rjust(w) + " | " + " ".join(
            ("1" if (a, b) in R else "0").rjust(w) for b in A))
    return lineas


def texto_analisis(A, R, an):
    """Lista de (texto, etiqueta) para mostrar o exportar."""
    out = []

    def tit(t):
        out.append(("\n" + t + "\n", "titulo"))

    def lin(t="", tag=None):
        out.append((t + "\n", tag))

    tit("DATOS")
    lin(f"A = {fmt_conjunto(A)}    |A| = {len(A)}")
    lin(f"R = {fmt_relacion(R, A)}    |R| = {len(R)}")
    lin(f"Dominio de R = {fmt_conjunto(an['dominio']) if an['dominio'] else '∅'}")
    lin(f"Imagen de R  = {fmt_conjunto(an['imagen']) if an['imagen'] else '∅'}")
    lin()
    lin("Matriz de R (fila = primer elemento, columna = segundo):")
    for l in matriz_texto(A, R):
        lin("  " + l, "mono")

    tit("CLASES DE EQUIVALENCIA")
    if an["clases"] is None:
        lin("No aplica: R no es una relación de equivalencia.", "gris")
    else:
        for rep, clase in an["clases"]:
            lin(f"[{rep}] = {fmt_conjunto(clase)}")
        lin(f"Conjunto cociente A/R = {{{', '.join(fmt_conjunto(c) for _, c in an['clases'])}}}")
        lin(f"Número de clases: {len(an['clases'])}")

    tit("ELEMENTOS NOTABLES DEL ORDEN")
    o = an["orden"]
    if o is None:
        lin("No aplica: R no es un orden parcial.", "gris")
    else:
        lin("Minimales: " + ", ".join(o["minimales"]))
        lin("Maximales: " + ", ".join(o["maximales"]))
        lin("Mínimo:    " + (o["minimo"][0] if o["minimo"] else "no existe"))
        lin("Máximo:    " + (o["maximo"][0] if o["maximo"] else "no existe"))
        lin("Aristas del diagrama de Hasse: "
            + (", ".join(fmt_par(p) for p in o["cubrimientos"]) or "ninguna"))
        lin("(Pestaña «Grafo» → «Diagrama de Hasse» para verlo dibujado.)", "gris")

    tit("CLAUSURAS")
    for nombre, anadidos, C in an["clausuras"]:
        lin(f"Clausura {nombre}:", "negrita")
        if anadidos:
            lin(f"  Se añaden {len(anadidos)} par(es): " + ", ".join(fmt_par(p) for p in anadidos))
        else:
            lin(f"  No hace falta añadir nada: R ya es {nombre}.")
        lin(f"  Resultado: {fmt_relacion(C, A)}")
    return out


def generar_reporte(A, R, props, an):
    lineas = ["VERIFICADOR DE PROPIEDADES DE RELACIONES BINARIAS", "=" * 60]
    for grupo, titulo in (("basica", "PROPIEDADES"), ("tipo", "TIPO DE RELACIÓN")):
        lineas += ["", titulo, "-" * 60]
        for p in props:
            if p.grupo == grupo:
                lineas.append(f"[{'✔' if p.cumple else '✘'}] {p.nombre}: "
                              f"{'CUMPLE' if p.cumple else 'NO CUMPLE'}")
                lineas.append(f"     Definición: {p.definicion}")
                lineas.append(f"     Detalle: {p.detalle}")
    lineas.append("")
    return "\n".join(lineas) + "".join(t for t, _ in texto_analisis(A, R, an))


EJEMPLOS = {
    "Equivalencia (misma paridad)":
        ("1, 2, 3, 4, 5, 6", lambda a, b: int(a) % 2 == int(b) % 2),
    "Orden parcial (divisibilidad)":
        ("1, 2, 3, 4, 6, 12", lambda a, b: int(b) % int(a) == 0),
    "Orden total (≤)": ("4", lambda a, b: int(a) <= int(b)),
    "Orden estricto (<)": ("4", lambda a, b: int(a) < int(b)),
    "Sin propiedades especiales": ("3", [("1", "2"), ("2", "3"), ("3", "3")]),
    "Relación vacía": ("3", []),
}


def pares_de_ejemplo(nombre):
    texto_A, regla = EJEMPLOS[nombre]
    A = parsear_conjunto(texto_A)
    if callable(regla):
        return texto_A, [(a, b) for a in A for b in A if regla(a, b)]
    return texto_A, list(regla)


# =====================================================================
# 2. INTERFAZ
# =====================================================================

FONDO = "#f3f4f6"
PANEL = "#ffffff"
TEXTO = "#1f2328"
SUAVE = "#5f6368"
AZUL = "#1a56db"
VERDE = "#16743a"
ROJO = "#b3261e"
NARANJA = "#d97706"


class VerificadorRelaciones:
    def __init__(self, root):
        self.root = root
        root.title("Verificador de Propiedades de Relaciones Binarias")
        root.geometry("1200x780")
        root.minsize(1000, 660)
        root.configure(bg=FONDO)

        self.A = ["1", "2", "3"]
        self.modo = tk.StringVar(value="pares")
        self._modo_actual = "pares"
        self.marcados = set()     # pares marcados en la matriz
        self.celdas = {}
        self.ultimo = None        # (A, R, props, analisis)
        self.prop_sel = None
        self.vista = tk.StringVar(value="relacion")
        self.ejemplo = tk.StringVar(value=next(iter(EJEMPLOS)))

        self._estilos()
        self._crear_interfaz()
        self.aplicar_conjunto()

    # ---------------- construcción ----------------
    def _estilos(self):
        s = ttk.Style()
        try:
            s.theme_use("clam")
        except tk.TclError:
            pass
        s.configure(".", background=FONDO, foreground=TEXTO, font=("Segoe UI", 10))
        s.configure("TLabelframe", background=FONDO)
        s.configure("TLabelframe.Label", background=FONDO, font=("Segoe UI", 10, "bold"))
        s.configure("TButton", padding=6)
        s.configure("Accent.TButton", background=AZUL, foreground="white",
                    font=("Segoe UI", 10, "bold"), padding=8)
        s.map("Accent.TButton", background=[("active", "#1e40af")])
        s.configure("Title.TLabel", font=("Segoe UI", 16, "bold"))
        s.configure("Ayuda.TLabel", foreground=SUAVE, font=("Segoe UI", 9))
        s.configure("Treeview", rowheight=26, font=("Segoe UI", 10))
        s.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))
        s.configure("TNotebook.Tab", padding=(14, 6))

    def _crear_interfaz(self):
        main = ttk.Frame(self.root, padding=12)
        main.pack(fill="both", expand=True)
        ttk.Label(main, text="Verificador de relaciones binarias",
                  style="Title.TLabel").pack(anchor="w", pady=(0, 8))

        paned = ttk.PanedWindow(main, orient="horizontal")
        paned.pack(fill="both", expand=True)
        izq = ttk.Frame(paned, padding=(0, 0, 10, 0))
        der = ttk.Frame(paned)
        paned.add(izq, weight=2)
        paned.add(der, weight=3)

        self._panel_conjunto(izq)
        self._panel_relacion(izq)
        self._panel_acciones(izq)
        self._panel_resultados(der)

        self.estado = ttk.Label(main, text="Listo.", style="Ayuda.TLabel")
        self.estado.pack(anchor="w", pady=(6, 0))

    def _panel_conjunto(self, padre):
        f = ttk.LabelFrame(padre, text=" 1. Conjunto A ", padding=10)
        f.pack(fill="x", pady=(0, 6))
        fila = ttk.Frame(f)
        fila.pack(fill="x")
        self.a_entry = ttk.Entry(fila, font=("Consolas", 11))
        self.a_entry.pack(side="left", fill="x", expand=True)
        self.a_entry.insert(0, "3")
        ttk.Button(fila, text="Aplicar", command=self.aplicar_conjunto).pack(side="left", padx=(6, 0))
        self.a_entry.bind("<Return>", lambda e: self.aplicar_conjunto())
        self.a_entry.bind("<FocusOut>", lambda e: self.aplicar_conjunto())
        self.a_label = ttk.Label(f, text="", wraplength=420)
        self.a_label.pack(anchor="w", pady=(6, 0))
        ttk.Label(f, text="Escribe una cantidad (4 → {1, 2, 3, 4}) o los elementos "
                          "separados por comas (a, b, c).", style="Ayuda.TLabel",
                  wraplength=420).pack(anchor="w")

    def _panel_relacion(self, padre):
        f = ttk.LabelFrame(padre, text=" 2. Relación R ⊆ A × A ", padding=10)
        f.pack(fill="both", expand=True, pady=6)

        modos = ttk.Frame(f)
        modos.pack(fill="x")
        ttk.Radiobutton(modos, text="Pares ordenados", variable=self.modo, value="pares",
                        command=self._cambiar_modo).pack(side="left")
        ttk.Radiobutton(modos, text="Matriz", variable=self.modo, value="matriz",
                        command=self._cambiar_modo).pack(side="left", padx=14)
        self.info_r = ttk.Label(modos, text="", foreground=AZUL)
        self.info_r.pack(side="right")

        self.cont_rel = ttk.Frame(f)
        self.cont_rel.pack(fill="both", expand=True, pady=(6, 0))

        # Modo pares
        self.frame_pares = ttk.Frame(self.cont_rel)
        ttk.Label(self.frame_pares, text="Pares separados por «;» o uno por línea. "
                  "Ejemplo: (1,1); (1,2); (2,3).  Dejarlo vacío = relación vacía.",
                  style="Ayuda.TLabel", wraplength=420).pack(anchor="w", pady=(0, 4))
        self.entrada = tk.Text(self.frame_pares, height=8, font=("Consolas", 11), wrap="word",
                               relief="solid", borderwidth=1, undo=True)
        self.entrada.pack(fill="both", expand=True)
        self.entrada.insert("1.0", "(1,1); (1,2); (2,3)")
        self.entrada.bind("<KeyRelease>", lambda e: self._actualizar_info_r())

        # Modo matriz
        self.frame_matriz = ttk.Frame(self.cont_rel)
        ttk.Label(self.frame_matriz, text="Haz clic en una casilla para marcar o desmarcar "
                  "(fila, columna) ∈ R.", style="Ayuda.TLabel",
                  wraplength=420).pack(anchor="w", pady=(0, 4))
        botones = ttk.Frame(self.frame_matriz)
        botones.pack(side="bottom", fill="x", pady=(6, 0))
        for texto, accion in (("Vaciar", "vaciar"), ("Identidad", "identidad"),
                              ("Todo 1", "todo"), ("Invertir", "invertir")):
            ttk.Button(botones, text=texto,
                       command=lambda a=accion: self._accion_matriz(a)).pack(side="left", padx=(0, 4))
        marco = tk.Frame(self.frame_matriz, bg=PANEL, highlightthickness=1,
                         highlightbackground="#c4c7cc")
        marco.pack(fill="both", expand=True)
        self.mcanvas = tk.Canvas(marco, bg=PANEL, highlightthickness=0)
        vs = ttk.Scrollbar(marco, orient="vertical", command=self.mcanvas.yview)
        hs = ttk.Scrollbar(marco, orient="horizontal", command=self.mcanvas.xview)
        self.mcanvas.configure(yscrollcommand=vs.set, xscrollcommand=hs.set)
        vs.pack(side="right", fill="y")
        hs.pack(side="bottom", fill="x")
        self.mcanvas.pack(fill="both", expand=True)
        self.mgrid = tk.Frame(self.mcanvas, bg=PANEL)
        self.mcanvas.create_window((8, 8), window=self.mgrid, anchor="nw")
        self.mgrid.bind("<Configure>", lambda e: self.mcanvas.configure(
            scrollregion=self.mcanvas.bbox("all")))

        self.frame_pares.pack(fill="both", expand=True)

    def _panel_acciones(self, padre):
        f = ttk.LabelFrame(padre, text=" 3. Acciones ", padding=10)
        f.pack(fill="x", pady=(6, 0))
        fila = ttk.Frame(f)
        fila.pack(fill="x")
        ttk.Button(fila, text="Verificar propiedades", style="Accent.TButton",
                   command=self.verificar).pack(side="left")
        ttk.Button(fila, text="Limpiar", command=self.limpiar).pack(side="left", padx=6)
        ttk.Button(fila, text="Exportar .txt", command=self.exportar).pack(side="left")
        fila2 = ttk.Frame(f)
        fila2.pack(fill="x", pady=(8, 0))
        ttk.Label(fila2, text="Ejemplo:").pack(side="left")
        ttk.Combobox(fila2, textvariable=self.ejemplo, values=list(EJEMPLOS),
                     state="readonly", width=30).pack(side="left", padx=6)
        ttk.Button(fila2, text="Cargar", command=self.cargar_ejemplo).pack(side="left")

    def _panel_resultados(self, padre):
        self.nb = ttk.Notebook(padre)
        self.nb.pack(fill="both", expand=True)

        # --- Propiedades
        tab = ttk.Frame(self.nb, padding=8)
        self.nb.add(tab, text="Propiedades")
        self.tree = ttk.Treeview(tab, columns=("res", "det"), height=14, selectmode="browse")
        self.tree.heading("#0", text="Propiedad")
        self.tree.heading("res", text="Resultado")
        self.tree.heading("det", text="Detalle")
        self.tree.column("#0", width=210, stretch=False)
        self.tree.column("res", width=110, stretch=False, anchor="center")
        self.tree.column("det", width=360)
        self.tree.tag_configure("si", foreground=VERDE)
        self.tree.tag_configure("no", foreground=ROJO)
        self.tree.tag_configure("grupo", font=("Segoe UI", 10, "bold"))
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self._al_seleccionar)
        ttk.Label(tab, text="Selecciona una propiedad para ver su explicación y el "
                            "contraejemplo resaltado en el grafo.",
                  style="Ayuda.TLabel").pack(anchor="w", pady=(6, 2))
        self.explicacion = self._texto_lectura(tab, height=8)

        # --- Grafo
        tab = ttk.Frame(self.nb, padding=8)
        self.nb.add(tab, text="Grafo")
        barra = ttk.Frame(tab)
        barra.pack(fill="x")
        ttk.Radiobutton(barra, text="Grafo dirigido de R", variable=self.vista, value="relacion",
                        command=self._dibujar).pack(side="left")
        ttk.Radiobutton(barra, text="Diagrama de Hasse", variable=self.vista, value="hasse",
                        command=self._dibujar).pack(side="left", padx=14)
        self.lbl_resaltado = ttk.Label(barra, text="", foreground=ROJO)
        self.lbl_resaltado.pack(side="right")
        self.canvas = tk.Canvas(tab, bg=PANEL, highlightthickness=1,
                                highlightbackground="#c4c7cc")
        self.canvas.pack(fill="both", expand=True, pady=(6, 0))
        self.canvas.bind("<Configure>", lambda e: self._dibujar())

        # --- Análisis
        tab = ttk.Frame(self.nb, padding=8)
        self.nb.add(tab, text="Análisis y clausuras")
        self.analisis = self._texto_lectura(tab, height=20)
        self.analisis.tag_configure("titulo", font=("Segoe UI", 11, "bold"), foreground=AZUL)
        self.analisis.tag_configure("negrita", font=("Consolas", 10, "bold"))
        self.analisis.tag_configure("gris", foreground=SUAVE)

    def _texto_lectura(self, padre, height):
        marco = ttk.Frame(padre)
        marco.pack(fill="both", expand=True)
        t = tk.Text(marco, height=height, font=("Consolas", 10), wrap="word", state="disabled",
                    background=PANEL, relief="solid", borderwidth=1, padx=8, pady=6)
        sb = ttk.Scrollbar(marco, orient="vertical", command=t.yview)
        t.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        t.pack(fill="both", expand=True)
        t.tag_configure("si", foreground=VERDE, font=("Consolas", 10, "bold"))
        t.tag_configure("no", foreground=ROJO, font=("Consolas", 10, "bold"))
        t.tag_configure("negrita", font=("Consolas", 10, "bold"))
        t.tag_configure("gris", foreground=SUAVE)
        return t

    @staticmethod
    def _escribir(widget, fragmentos):
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        for texto, tag in fragmentos:
            widget.insert("end", texto, tag or ())
        widget.configure(state="disabled")

    # ---------------- conjunto A ----------------
    def aplicar_conjunto(self):
        try:
            nuevo = parsear_conjunto(self.a_entry.get())
        except ValueError as e:
            self.a_label.configure(text=str(e), foreground=ROJO)
            return False
        cambio = nuevo != self.A
        if cambio:
            self.A = nuevo
            conj = set(nuevo)
            self.marcados = {(a, b) for a, b in self.marcados if a in conj and b in conj}
            self._estado("Conjunto A actualizado. Pulsa «Verificar propiedades» para recalcular.")
        if self._modo_actual == "matriz" and (cambio or not self.celdas):
            self._construir_matriz()
        self.a_label.configure(text=f"A = {fmt_conjunto(self.A)}     |A| = {len(self.A)}",
                               foreground=TEXTO)
        self._actualizar_info_r()
        return True

    # ---------------- relación ----------------
    def _cambiar_modo(self):
        nuevo = self.modo.get()
        if nuevo == self._modo_actual:
            return
        if nuevo == "matriz":
            if not self.aplicar_conjunto():
                messagebox.showerror("Conjunto A no válido", self.a_label.cget("text"))
                self.modo.set("pares")
                return
            try:
                pares, _ = parsear_pares(self.entrada.get("1.0", "end"), self.A)
            except ValueError as e:
                messagebox.showerror("No se puede pasar a matriz", str(e))
                self.modo.set("pares")
                return
            self.marcados = set(pares)
            self._modo_actual = "matriz"
            self._construir_matriz()
            self.frame_pares.pack_forget()
            self.frame_matriz.pack(fill="both", expand=True)
        else:
            self.entrada.delete("1.0", "end")
            self.entrada.insert("1.0", "; ".join(fmt_par(p) for p in ordenar(self.marcados, self.A)))
            self._modo_actual = "pares"
            self.frame_matriz.pack_forget()
            self.frame_pares.pack(fill="both", expand=True)
        self._actualizar_info_r()

    def _construir_matriz(self):
        for w in self.mgrid.winfo_children():
            w.destroy()
        self.celdas = {}
        ancho = max(3, max(len(a) for a in self.A) + 1)
        cab = dict(bg=PANEL, fg=AZUL, font=("Consolas", 10, "bold"))
        tk.Label(self.mgrid, text="R", width=ancho, **cab).grid(row=0, column=0)
        for j, b in enumerate(self.A, start=1):
            tk.Label(self.mgrid, text=b, width=ancho, **cab).grid(row=0, column=j, pady=(0, 2))
        for i, a in enumerate(self.A, start=1):
            tk.Label(self.mgrid, text=a, width=ancho, anchor="e", **cab).grid(row=i, column=0, padx=(0, 4))
            for j, b in enumerate(self.A, start=1):
                c = tk.Label(self.mgrid, width=ancho, font=("Consolas", 11), relief="solid",
                             bd=1, cursor="hand2")
                c.grid(row=i, column=j, padx=1, pady=1, ipady=2)
                c.bind("<Button-1>", lambda e, p=(a, b): self._alternar(p))
                self.celdas[(a, b)] = c
                self._pintar_celda((a, b))

    def _pintar_celda(self, p):
        c = self.celdas.get(p)
        if c is None:
            return
        if p in self.marcados:
            c.configure(text="1", bg=AZUL, fg="white")
        else:
            c.configure(text="0", bg="#eef0f3" if p[0] == p[1] else PANEL, fg="#9aa0a6")

    def _alternar(self, p):
        self.marcados ^= {p}
        self._pintar_celda(p)
        self._actualizar_info_r()

    def _accion_matriz(self, accion):
        todos = {(a, b) for a in self.A for b in self.A}
        if accion == "vaciar":
            self.marcados = set()
        elif accion == "identidad":
            self.marcados = {(a, a) for a in self.A}
        elif accion == "todo":
            self.marcados = todos
        elif accion == "invertir":
            self.marcados = todos - self.marcados
        for p in self.celdas:
            self._pintar_celda(p)
        self._actualizar_info_r()

    def _leer_relacion(self):
        if self._modo_actual == "matriz":
            return ordenar(self.marcados, self.A), []
        return parsear_pares(self.entrada.get("1.0", "end"), self.A)

    def _actualizar_info_r(self):
        try:
            pares, rep = self._leer_relacion()
            txt = f"|R| = {len(pares)} par{'es' if len(pares) != 1 else ''}"
            if rep:
                txt += f"  ({len(rep)} repetido{'s' if len(rep) != 1 else ''} se ignorará{'n' if len(rep) != 1 else ''})"
            self.info_r.configure(text=txt, foreground=AZUL)
        except ValueError:
            self.info_r.configure(text="Formato incompleto…", foreground=NARANJA)

    def _poner_relacion(self, pares):
        if self._modo_actual == "matriz":
            self.marcados = set(pares)
            for p in self.celdas:
                self._pintar_celda(p)
        else:
            self.entrada.delete("1.0", "end")
            self.entrada.insert("1.0", "; ".join(fmt_par(p) for p in pares))
        self._actualizar_info_r()

    # ---------------- acciones ----------------
    def verificar(self):
        if not self.aplicar_conjunto():
            messagebox.showerror("Conjunto A no válido", self.a_label.cget("text"))
            return
        try:
            R, repetidos = self._leer_relacion()
        except ValueError as e:
            messagebox.showerror("Relación no válida", str(e))
            return

        props = verificar_propiedades(self.A, R)
        an = analizar(self.A, R, props)
        self.ultimo = (list(self.A), set(R), props, an)
        self.prop_sel = None

        self.tree.delete(*self.tree.get_children())
        for grupo, titulo in (("basica", "Propiedades"), ("tipo", "Tipo de relación")):
            gid = self.tree.insert("", "end", iid="g_" + grupo, text=titulo,
                                   open=True, tags=("grupo",))
            for p in props:
                if p.grupo == grupo:
                    self.tree.insert(gid, "end", iid=p.nombre, text=p.nombre,
                                     values=("✔ Cumple" if p.cumple else "✘ No cumple", p.detalle),
                                     tags=("si" if p.cumple else "no",))

        tipos = [p.nombre for p in props if p.grupo == "tipo" and p.cumple]
        resumen = ("R es: " + ", ".join(tipos) + "." if tipos
                   else "R no es preorden, equivalencia ni orden.")
        self._escribir(self.explicacion, [(resumen + "\n\n", "negrita"),
                                          ("Selecciona una fila para ver el detalle.", None)])
        self._escribir(self.analisis, texto_analisis(self.A, set(R), an))
        self.vista.set("hasse" if an["orden"] and self.vista.get() == "hasse" else "relacion")
        self._dibujar()

        msg = f"Verificación completa: |A| = {len(self.A)}, |R| = {len(R)}."
        if repetidos:
            msg += (f"  Aviso: se ignoraron {len(repetidos)} par(es) repetido(s): "
                    + ", ".join(fmt_par(p) for p in repetidos[:5]) + ".")
        self._estado(msg)
        self.nb.select(0)

    def _al_seleccionar(self, _e=None):
        sel = self.tree.selection()
        if not sel or not self.ultimo or sel[0].startswith("g_"):
            return
        props = {p.nombre: p for p in self.ultimo[2]}
        p = props[sel[0]]
        self.prop_sel = p
        frag = [(f"{p.nombre}: ", "negrita"),
                ("✔ CUMPLE\n" if p.cumple else "✘ NO CUMPLE\n", "si" if p.cumple else "no"),
                (f"\nDefinición: {p.definicion}\n", None)]
        if p.componentes:
            frag.append(("\nCondiciones:\n", None))
            for c in p.componentes:
                pc = props[c]
                frag.append(("  ✔ " if pc.cumple else "  ✘ ", "si" if pc.cumple else "no"))
                frag.append((f"{c}" + ("" if pc.cumple else f" — {pc.detalle}") + "\n", None))
        else:
            frag.append((f"\nDetalle: {p.detalle}\n", None))
        if not p.cumple and (p.resaltar or p.faltantes):
            frag.append(("\nEn el grafo: en rojo los pares de R que causan el fallo; "
                         "en naranja punteado los pares que faltan.", "gris"))
        self._escribir(self.explicacion, frag)
        if self.vista.get() != "relacion":
            self.vista.set("relacion")
        self._dibujar()

    def limpiar(self):
        self._poner_relacion([])
        self.ultimo = None
        self.prop_sel = None
        self.tree.delete(*self.tree.get_children())
        self._escribir(self.explicacion, [])
        self._escribir(self.analisis, [])
        self._dibujar()
        self._estado("Relación y resultados borrados.")

    def cargar_ejemplo(self):
        texto_A, pares = pares_de_ejemplo(self.ejemplo.get())
        self.a_entry.delete(0, "end")
        self.a_entry.insert(0, texto_A)
        self.aplicar_conjunto()
        self._poner_relacion(pares)
        self.verificar()

    def exportar(self):
        if not self.ultimo:
            messagebox.showinfo("Exportar", "Primero pulsa «Verificar propiedades».")
            return
        ruta = filedialog.asksaveasfilename(
            title="Guardar reporte", defaultextension=".txt", initialfile="reporte_relacion.txt",
            filetypes=[("Archivo de texto", "*.txt"), ("Todos", "*.*")])
        if not ruta:
            return
        try:
            with open(ruta, "w", encoding="utf-8") as f:
                f.write(generar_reporte(*self.ultimo))
        except OSError as e:
            messagebox.showerror("Exportar", f"No se pudo guardar el archivo:\n{e}")
            return
        self._estado(f"Reporte guardado en {ruta}")

    def _estado(self, texto):
        self.estado.configure(text=texto)

    # ---------------- dibujo ----------------
    def _dibujar(self):
        c = self.canvas
        c.delete("all")
        w, h = c.winfo_width(), c.winfo_height()
        if w < 50 or h < 50:
            return
        if not self.ultimo:
            self.lbl_resaltado.configure(text="")
            c.create_text(w / 2, h / 2, text="Pulsa «Verificar propiedades» para ver el grafo.",
                          fill=SUAVE, font=("Segoe UI", 11))
            return
        A, R, props, an = self.ultimo
        if self.vista.get() == "hasse":
            self.lbl_resaltado.configure(text="")
            self._dibujar_hasse(A, an, w, h)
        else:
            p = self.prop_sel
            mostrar = p is not None and not p.cumple
            self.lbl_resaltado.configure(text=f"Contraejemplo: {p.nombre}" if mostrar else "")
            self._dibujar_relacion(A, R, p.resaltar if mostrar else set(),
                                   p.faltantes if mostrar else set(), w, h)

    def _radio_nodo(self, n):
        return 18 if n <= 10 else 14

    def _nodo(self, x, y, nombre, r):
        self.canvas.create_oval(x - r, y - r, x + r, y + r, fill="#e8f0fe", outline=AZUL, width=2)
        self.canvas.create_text(x, y, text=nombre, fill=TEXTO,
                                font=("Segoe UI", 10 if r >= 18 else 9, "bold"))

    @staticmethod
    def _hacia(x, y, tx, ty, d):
        dx, dy = tx - x, ty - y
        L = math.hypot(dx, dy) or 1
        return x + dx / L * d, y + dy / L * d

    def _dibujar_relacion(self, A, R, resaltar, faltantes, w, h):
        c = self.canvas
        n = len(A)
        nr = self._radio_nodo(n)
        cx, cy = w / 2, (h - 30) / 2
        radio = max(40, min(w, h - 30) / 2 - 55)
        pos = {}
        for i, a in enumerate(A):
            if n == 1:
                pos[a] = (cx, cy)
            else:
                ang = -math.pi / 2 + 2 * math.pi * i / n
                pos[a] = (cx + radio * math.cos(ang), cy + radio * math.sin(ang))
        todos = set(R) | set(faltantes)

        def arco(p, estilo):
            a, b = p
            (x1, y1), (x2, y2) = pos[a], pos[b]
            if a == b:
                vx, vy = (x1 - cx, y1 - cy) if n > 1 else (0, -1)
                L = math.hypot(vx, vy) or 1
                vx, vy = vx / L, vy / L
                lx, ly, lr = x1 + vx * (nr + 9), y1 + vy * (nr + 9), 11
                c.create_oval(lx - lr, ly - lr, lx + lr, ly + lr, outline=estilo["fill"],
                              width=estilo["width"], dash=estilo.get("dash"))
                return
            if (b, a) in todos:
                dx, dy = x2 - x1, y2 - y1
                L = math.hypot(dx, dy) or 1
                mx, my = (x1 + x2) / 2 - dy / L * 24, (y1 + y2) / 2 + dx / L * 24
                sx, sy = self._hacia(x1, y1, mx, my, nr)
                ex, ey = self._hacia(x2, y2, mx, my, nr + 2)
                c.create_line(sx, sy, mx, my, ex, ey, smooth=True, arrow="last",
                              arrowshape=(10, 12, 4), **estilo)
            else:
                sx, sy = self._hacia(x1, y1, x2, y2, nr)
                ex, ey = self._hacia(x2, y2, x1, y1, nr + 2)
                c.create_line(sx, sy, ex, ey, arrow="last", arrowshape=(10, 12, 4), **estilo)

        normal = {"fill": "#6b7280", "width": 1.5}
        rojo = {"fill": ROJO, "width": 3}
        falta = {"fill": NARANJA, "width": 2, "dash": (6, 4)}
        for p in ordenar(R, A):
            if p not in resaltar:
                arco(p, normal)
        for p in ordenar(faltantes, A):
            arco(p, falta)
        for p in ordenar(resaltar & set(R), A):
            arco(p, rojo)
        for a in A:
            self._nodo(*pos[a], a, nr)

        y = h - 14
        c.create_line(12, y, 40, y, fill="#6b7280", width=1.5, arrow="last")
        c.create_text(46, y, text="par de R", anchor="w", fill=SUAVE, font=("Segoe UI", 9))
        if resaltar or faltantes:
            c.create_line(120, y, 148, y, fill=ROJO, width=3, arrow="last")
            c.create_text(154, y, text="causa el fallo", anchor="w", fill=SUAVE, font=("Segoe UI", 9))
            c.create_line(250, y, 278, y, fill=NARANJA, width=2, dash=(6, 4), arrow="last")
            c.create_text(284, y, text="falta en R", anchor="w", fill=SUAVE, font=("Segoe UI", 9))
        if not R:
            c.create_text(w / 2, 18, text="R = ∅ (relación vacía)", fill=SUAVE,
                          font=("Segoe UI", 10, "italic"))

    def _dibujar_hasse(self, A, an, w, h):
        c = self.canvas
        o = an["orden"]
        if o is None:
            c.create_text(w / 2, h / 2, width=w - 60, justify="center", fill=SUAVE,
                          font=("Segoe UI", 11),
                          text="R no es un orden parcial (reflexiva, antisimétrica y "
                               "transitiva), así que no tiene diagrama de Hasse.")
            return
        niveles = o["niveles"]
        nmax = max(niveles.values())
        por_nivel = {}
        for a in A:
            por_nivel.setdefault(niveles[a], []).append(a)
        nr = self._radio_nodo(len(A))
        margen = 50
        pos = {}
        for lv, elems in por_nivel.items():
            y = h / 2 if nmax == 0 else h - margen - lv * (h - 2 * margen) / nmax
            for k, a in enumerate(elems):
                pos[a] = (w * (k + 1) / (len(elems) + 1), y)
        for a, b in o["cubrimientos"]:
            (x1, y1), (x2, y2) = pos[a], pos[b]
            c.create_line(x1, y1, x2, y2, fill="#4b5563", width=2)
        for a in A:
            self._nodo(*pos[a], a, nr)
        c.create_text(12, h - 12, anchor="w", fill=SUAVE, font=("Segoe UI", 9),
                      text="Abajo los menores. Una línea de a hacia arriba hasta b "
                           "significa que b cubre a a.")


if __name__ == "__main__":
    ventana = tk.Tk()
    VerificadorRelaciones(ventana)
    ventana.mainloop()
