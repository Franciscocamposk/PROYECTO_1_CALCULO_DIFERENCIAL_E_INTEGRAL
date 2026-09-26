"""
================================================================================
 UNIVERSIDAD DE COSTA RICA - ESCUELA DE MATEMÁTICA
 MA-0321 Cálculo Diferencial e Integral
 PROYECTO DE MATE: Capacidad de Servidores y Costo Marginal
 
 Prototipo Interactivo con Tooltips, Explicaciones Pedagógicas y Presets Dinámicos
================================================================================
"""

import sys
import sympy as sp
import numpy as np
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import tkinter as tk
from tkinter import ttk, messagebox

# ==============================================================================
# TOOLTIP / GLOBO DE AYUDA AL PASAR EL CURSOR (HOVER)
# ==============================================================================

class ToolTip:
    """Crea una ventana emergente explicativa cuando el usuario pasa el mouse."""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        self.widget.bind("<Enter>", self.show_tip)
        self.widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, event=None):
        if self.tip_window or not self.text:
            return
        try:
            x = self.widget.winfo_rootx() + 20
            y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
            self.tip_window = tw = tk.Toplevel(self.widget)
            tw.wm_overrideredirect(True)
            tw.wm_geometry(f"+{x}+{y}")
            tw.attributes("-topmost", True)
            
            lbl = tk.Label(
                tw, text=self.text, justify=tk.LEFT,
                background="#0f172a", foreground="#38bdf8",
                relief=tk.SOLID, borderwidth=1, highlightthickness=0,
                font=("Segoe UI", 9, "bold"), padx=10, pady=7
            )
            lbl.pack()
        except Exception:
            pass

    def hide_tip(self, event=None):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None


# ==============================================================================
# 1. FUNCIONES BASE DEL MODELO ECONÓMICO (REQUERIDAS POR RÚBRICA)
# ==============================================================================

def costo(x, fijos=3000.0, costo_usuario=8.0, factor_cuadratico=0.02):
    """
    Función de Costo C(x) = F + c*x + k*x^2
    - F: Costos fijos (servidores base, licencias, mantenimiento).
    - c: Costo variable lineal por usuario.
    - k: Factor cuadrático que modela la saturación y sobrecarga técnica.
    """
    return fijos + costo_usuario * x + factor_cuadratico * (x ** 2)


def ingreso(x, tarifa=50.0):
    """
    Función de Ingreso R(x) = p*x
    - p: Tarifa cobrada por cada usuario simultáneo.
    """
    return tarifa * x


def utilidad(x, fijos=3000.0, costo_usuario=8.0, factor_cuadratico=0.02, tarifa=50.0):
    """
    Función de Utilidad U(x) = R(x) - C(x)
    """
    return ingreso(x, tarifa) - costo(x, fijos, costo_usuario, factor_cuadratico)


# ==============================================================================
# 2. ANÁLISIS MATEMÁTICO RIGUROSO CON CÁLCULO SIMBÓLICO (SYMPY)
# ==============================================================================

def calculos_matematicos(tarifa, fijos, costo_usuario, factor_cuadratico):
    """
    Calcula de manera simbólica y exacta todos los requerimientos de cálculo:
    C'(x), R'(x), U'(x), Punto Crítico, 2da Derivada, Concavidad y Límite al infinito.
    """
    x = sp.Symbol('x', real=True, positive=True)
    
    C_sym = fijos + costo_usuario * x + factor_cuadratico * (x ** 2)
    R_sym = tarifa * x
    U_sym = R_sym - C_sym
    
    C_prime = sp.diff(C_sym, x)
    R_prime = sp.diff(R_sym, x)
    U_prime = sp.diff(U_sym, x)
    
    puntos_criticos = sp.solve(U_prime, x)
    x_optimo = float(puntos_criticos[0]) if puntos_criticos else 0.0
    
    U_double_prime = sp.diff(U_prime, x)
    C_double_prime = sp.diff(C_prime, x)
    limite_inf = sp.limit(U_sym, x, sp.oo)
    
    return {
        'C_sym': str(C_sym),
        'R_sym': str(R_sym),
        'U_sym': str(U_sym),
        'C_prime': str(C_prime),
        'R_prime': str(R_prime),
        'U_prime': str(U_prime),
        'x_optimo': x_optimo,
        'U_double_prime': float(U_double_prime),
        'C_double_prime': float(C_double_prime),
        'limite_inf': str(limite_inf)
    }


# ==============================================================================
# 3. RECOMENDACIÓN DE CAPACIDAD Y COMPARACIÓN DE INFRAESTRUCTURAS
# ==============================================================================

INFRAESTRUCTURAS_DEFAULT = {
    'Básica': {
        'fijos': 1000.0,
        'costo_usuario': 10.0,
        'factor_cuadratico': 0.1,
        'capacidad_maxima': 500
    },
    'Intermedia': {
        'fijos': 3000.0,
        'costo_usuario': 8.0,
        'factor_cuadratico': 0.02,
        'capacidad_maxima': 1500
    },
    'Ampliada': {
        'fijos': 15000.0,
        'costo_usuario': 5.0,
        'factor_cuadratico': 0.002,
        'capacidad_maxima': 15000
    }
}

def recomendar_capacidad(demanda_proyectada, infraestructuras, tarifa):
    """
    Evalúa y compara las infraestructuras, retornando un reporte con alertas.
    """
    reporte = []
    mejor_opcion = None
    mejor_utilidad = -float('inf')
    
    for nombre, datos in infraestructuras.items():
        cap_max = datos['capacidad_maxima']
        fijos = datos['fijos']
        c_u = datos['costo_usuario']
        k = datos['factor_cuadratico']
        
        x_opt = (tarifa - c_u) / (2.0 * k) if k > 0 else 0
        usuarios_atendidos = min(demanda_proyectada, cap_max)
        util_estimada = utilidad(usuarios_atendidos, fijos, c_u, k, tarifa)
        saturada = demanda_proyectada > cap_max
        
        info = {
            'nombre': nombre,
            'cap_max': cap_max,
            'x_opt': x_opt,
            'usuarios_atendidos': usuarios_atendidos,
            'utilidad': util_estimada,
            'saturada': saturada,
            'sobrecupo': demanda_proyectada - cap_max if saturada else 0
        }
        reporte.append(info)
        
        if util_estimada > mejor_utilidad:
            mejor_utilidad = util_estimada
            mejor_opcion = info
            
    return reporte, mejor_opcion


# ==============================================================================
# 4. INTERFAZ GRÁFICA MODERNA (PROYECTO DE MATE)
# ==============================================================================

class CapacidadApp(tk.Tk):
    def __init__(self):
        super().__init__()
        # Título de ventana solicitado
        self.title("Proyecto de Mate — Cálculo Diferencial e Integral (MA-0321)")
        self.geometry("1300x880")
        self.minsize(1100, 750)
        self.configure(bg="#0f111a")
        
        # Variables del modelo
        self.var_tarifa = tk.DoubleVar(value=50.0)
        self.var_fijos = tk.DoubleVar(value=3000.0)
        self.var_costo_u = tk.DoubleVar(value=8.0)
        self.var_factor_k = tk.DoubleVar(value=0.02)
        self.var_cap_max = tk.IntVar(value=1500)
        self.var_demanda = tk.IntVar(value=900)
        
        # Variable interactiva del punto seleccionado
        self.var_punto_x = tk.DoubleVar(value=900.0)
        self.arrastrando_punto = False
        self.preset_actual = 'problema'
        
        self.infras = INFRAESTRUCTURAS_DEFAULT.copy()
        
        self._configurar_estilos()
        self._construir_interfaz()
        self.actualizar_modelo()

    def _configurar_estilos(self):
        style = ttk.Style(self)
        style.theme_use('clam')
        
        self.c_bg = "#0f111a"
        self.c_card = "#181a27"
        self.c_card_inner = "#12131d"
        self.c_accent = "#38bdf8"
        self.c_green = "#4ade80"
        self.c_red = "#f87171"
        self.c_yellow = "#fbbf24"
        
        style.configure("TLabel", background=self.c_card, foreground="#f1f5f9", font=("Segoe UI", 10))
        style.configure("Header.TLabel", background=self.c_card, foreground=self.c_accent, font=("Segoe UI", 12, "bold"))
        style.configure("TScale", background=self.c_card)

    def _construir_interfaz(self):
        # Contenedor principal sin cabecera sobrante
        main_container = tk.Frame(self, bg=self.c_bg)
        main_container.pack(fill=tk.BOTH, expand=True, padx=14, pady=12)
        
        # ----------------- PANEL IZQUIERDO -----------------
        left_panel = tk.Frame(main_container, bg=self.c_card, width=440, padx=16, pady=14, relief=tk.RAISED, bd=1)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 12))
        left_panel.pack_propagate(False)
        
        # --- PRESETS DE ESCENARIOS / INFRAESTRUCTURA ---
        lbl_presets = ttk.Label(left_panel, text="Presets de Escenarios:", style="Header.TLabel")
        lbl_presets.pack(anchor=tk.W, pady=(0, 6))
        ToolTip(lbl_presets, "Selecciona rápidamente entre el problema base original, el escenario en pérdidas o el caso de sobrecupo.")
        
        preset_frame = tk.Frame(left_panel, bg=self.c_card)
        preset_frame.pack(fill=tk.X, pady=(0, 12))
        
        self.btn_problema = tk.Button(preset_frame, text="Problema Base", bg="#2563eb", fg="white", activebackground="#1d4ed8",
                                      font=("Segoe UI", 9, "bold"), command=lambda: self.cargar_escenario('problema'), relief=tk.FLAT, pady=5)
        self.btn_problema.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        ToolTip(self.btn_problema, "Caso Original del Enunciado: Tarifa=$50, Fijos=$3,000, Demanda=900 u, Capacidad=1,500 u (Operación Rentable).")
        
        self.btn_perdidas = tk.Button(preset_frame, text="Zona Pérdidas", bg="#334155", fg="white", activebackground="#475569",
                                      font=("Segoe UI", 9, "bold"), command=lambda: self.cargar_escenario('perdidas'), relief=tk.FLAT, pady=5)
        self.btn_perdidas.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        ToolTip(self.btn_perdidas, "Escenario de Pérdidas: Simula x=2,000 usuarios donde el costo cuadrático supera los ingresos (U < $0).")
        
        self.btn_sobrecupo = tk.Button(preset_frame, text="Sobrecupo", bg="#334155", fg="white", activebackground="#475569",
                                       font=("Segoe UI", 9, "bold"), command=lambda: self.cargar_escenario('sobrecupo'), relief=tk.FLAT, pady=5)
        self.btn_sobrecupo.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        ToolTip(self.btn_sobrecupo, "Escenario de Sobrecupo: Demanda proyectada (3,500 u) excede la capacidad física (1,500 u), disparando alerta.")
        
        # --- PARÁMETROS MODIFICABLES ---
        lbl_params_title = ttk.Label(left_panel, text="Parámetros Modificables:", style="Header.TLabel")
        lbl_params_title.pack(anchor=tk.W, pady=(2, 6))
        ToolTip(lbl_params_title, "Puedes escribir nuevos valores o ajustarlos y hacer clic en Recalcular.")
        
        form_frame = tk.Frame(left_panel, bg=self.c_card)
        form_frame.pack(fill=tk.X, pady=(0, 10))
        
        parametros_info = [
            ("Tarifa por Usuario ($ p):", self.var_tarifa, "Tarifa (p): Precio unitario cobrado por usuario. Genera el ingreso R(x) = p*x."),
            ("Costos Fijos ($ F):", self.var_fijos, "Costos Fijos (F): Servidores base, licencias y mantenimiento independiente del tráfico."),
            ("Costo Lineal por Usuario ($ c):", self.var_costo_u, "Costo Lineal (c): Costo operativo básico recurrente por cada usuario activo."),
            ("Factor Sobrecarga Cuadrático (k):", self.var_factor_k, "Factor Cuadrático (k): Modela cuellos de botella y costo acelerado por saturación."),
            ("Capacidad Máxima (usuarios):", self.var_cap_max, "Capacidad Máxima: Límite físico contractual del servidor antes de degradarse."),
            ("Demanda Proyectada (usuarios):", self.var_demanda, "Demanda Proyectada: Cantidad de usuarios simultáneos que desean conectarse.")
        ]
        
        for idx, (label_text, var, tooltip_txt) in enumerate(parametros_info):
            lbl = tk.Label(form_frame, text=label_text, bg=self.c_card, fg="#e2e8f0", font=("Segoe UI", 10, "bold"))
            lbl.grid(row=idx, column=0, sticky=tk.W, pady=4)
            ToolTip(lbl, tooltip_txt)
            
            ent = tk.Entry(form_frame, textvariable=var, width=12, bg="#0f111a", fg="#38bdf8",
                           insertbackground="white", font=("Segoe UI", 10, "bold"), justify='right', relief=tk.SOLID, bd=1)
            ent.grid(row=idx, column=1, sticky=tk.E, pady=4, padx=(10, 0))
            ToolTip(ent, f"Modifica este valor y presiona 'Recalcular'.\n{tooltip_txt}")
            
        btn_actualizar = tk.Button(left_panel, text="RECALCULAR MODELO", bg="#0284c7", fg="white", activebackground="#0369a1",
                                   font=("Segoe UI", 11, "bold"), relief=tk.FLAT, pady=6, command=self.actualizar_modelo)
        btn_actualizar.pack(fill=tk.X, pady=(2, 10))
        ToolTip(btn_actualizar, "Aplica todos los cambios de parámetros, recalcula derivadas simbólicas y actualiza la gráfica.")
        
        # --- SLIDER DE CONTROL DE USUARIOS ---
        lbl_slider_title = ttk.Label(left_panel, text="Mover Usuarios Simultáneos (x):", style="Header.TLabel")
        lbl_slider_title.pack(anchor=tk.W, pady=(2, 2))
        ToolTip(lbl_slider_title, "Mueve esta barra para cambiar la cantidad de usuarios simultáneos y ver las métricas en tiempo real.")
        
        self.slider_x = tk.Scale(left_panel, from_=0, to=2000, orient=tk.HORIZONTAL, variable=self.var_punto_x,
                                 command=self._on_slider_change, bg=self.c_card, fg="#38bdf8",
                                 troughcolor="#0f111a", highlightthickness=0, font=("Segoe UI", 9, "bold"))
        self.slider_x.pack(fill=tk.X, pady=(0, 10))
        
        # --- ANÁLISIS DE CÁLCULO EXPLICADO ---
        lbl_analisis_title = ttk.Label(left_panel, text="Análisis de Cálculo Simbólico (SymPy Explicado):", style="Header.TLabel")
        lbl_analisis_title.pack(anchor=tk.W, pady=(4, 4))
        ToolTip(lbl_analisis_title, "Muestra el desarrollo matemático paso a paso con las fórmulas de cálculo diferencial y su explicación.")
        
        self.txt_calculo = tk.Text(left_panel, bg="#0f111a", fg="#38bdf8", font=("Consolas", 9),
                                   relief=tk.FLAT, bd=0, padx=10, pady=10, height=14)
        self.txt_calculo.pack(fill=tk.BOTH, expand=True)

        # ----------------- PANEL DERECHO -----------------
        right_panel = tk.Frame(main_container, bg=self.c_bg)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Tarjeta de métricas en tiempo real
        metrics_card = tk.Frame(right_panel, bg=self.c_card, relief=tk.RAISED, bd=1, padx=14, pady=10)
        metrics_card.pack(fill=tk.X, pady=(0, 10))
        
        self.lbl_metric_x = tk.Label(metrics_card, text="Usuarios: 900", bg=self.c_card, fg="#ffffff", font=("Segoe UI", 12, "bold"))
        self.lbl_metric_x.pack(side=tk.LEFT, padx=(0, 15))
        ToolTip(self.lbl_metric_x, "Cantidad de usuarios simultáneos seleccionada actualmente.")
        
        self.lbl_metric_c = tk.Label(metrics_card, text="Costo: $23,400", bg=self.c_card, fg="#f87171", font=("Segoe UI", 12, "bold"))
        self.lbl_metric_c.pack(side=tk.LEFT, padx=(0, 15))
        ToolTip(self.lbl_metric_c, "Costo total de infraestructura C(x) para la cantidad de usuarios seleccionada.")
        
        self.lbl_metric_r = tk.Label(metrics_card, text="Ingreso: $45,000", bg=self.c_card, fg="#4ade80", font=("Segoe UI", 12, "bold"))
        self.lbl_metric_r.pack(side=tk.LEFT, padx=(0, 15))
        ToolTip(self.lbl_metric_r, "Ingreso bruto generado R(x) = p * x.")
        
        self.lbl_metric_u = tk.Label(metrics_card, text="Utilidad: $21,600", bg=self.c_card, fg="#38bdf8", font=("Segoe UI", 13, "bold"))
        self.lbl_metric_u.pack(side=tk.LEFT, padx=(0, 15))
        ToolTip(self.lbl_metric_u, "Utilidad neta U(x) = Ingreso - Costo. Representa la ganancia real.")

        self.lbl_metric_status = tk.Label(metrics_card, text="[Capacidad Óptima]", bg=self.c_card, fg="#fbbf24", font=("Segoe UI", 11, "bold"))
        self.lbl_metric_status.pack(side=tk.RIGHT)
        
        # Gráfica Matplotlib Canvas
        graph_card = tk.Frame(right_panel, bg=self.c_card, relief=tk.RAISED, bd=1, padx=8, pady=8)
        graph_card.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.fig, self.ax = plt.subplots(figsize=(7.5, 4.5), dpi=100)
        self.fig.patch.set_facecolor('#181a27')
        self.ax.set_facecolor('#0f111a')
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=graph_card)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Conectar eventos de ratón
        self.canvas.mpl_connect('button_press_event', self._on_canvas_click)
        self.canvas.mpl_connect('motion_notify_event', self._on_canvas_drag)
        self.canvas.mpl_connect('button_release_event', self._on_canvas_release)
        
        # Sección de Decisión y Comparativa
        decision_card = tk.Frame(right_panel, bg=self.c_card, relief=tk.RAISED, bd=1, padx=14, pady=10)
        decision_card.pack(fill=tk.X)
        
        lbl_dec = ttk.Label(decision_card, text="Decisión Empresarial y Comparación de Infraestructuras:", style="Header.TLabel")
        lbl_dec.pack(anchor=tk.W)
        ToolTip(lbl_dec, "Compara las 3 infraestructuras contra la demanda proyectada y emite alertas de saturación si se excede el límite físico.")
        
        self.txt_decision = tk.Text(decision_card, bg="#0f111a", fg="#f8fafc", font=("Segoe UI", 10),
                                    relief=tk.FLAT, height=6, padx=10, pady=8)
        self.txt_decision.pack(fill=tk.X, pady=(6, 0))

    def _actualizar_estilo_botones_presets(self):
        """Resalta visualmente el botón del preset seleccionado."""
        self.btn_problema.config(bg="#2563eb" if self.preset_actual == 'problema' else "#334155")
        self.btn_perdidas.config(bg="#ef4444" if self.preset_actual == 'perdidas' else "#334155")
        self.btn_sobrecupo.config(bg="#f59e0b" if self.preset_actual == 'sobrecupo' else "#334155")

    def cargar_escenario(self, tipo):
        """Carga el escenario solicitado: 'problema', 'perdidas' o 'sobrecupo'."""
        self.preset_actual = tipo
        self._actualizar_estilo_botones_presets()
        
        if tipo == 'problema':
            # Caso Base del enunciado (Intermedia, demanda 900)
            self.var_tarifa.set(50.0)
            self.var_fijos.set(3000.0)
            self.var_costo_u.set(8.0)
            self.var_factor_k.set(0.02)
            self.var_cap_max.set(1500)
            self.var_demanda.set(900)
            self.var_punto_x.set(900.0)
        elif tipo == 'perdidas':
            # Escenario de Pérdidas por saturación (x=2000 u -> U = -$9,000 < 0)
            self.var_tarifa.set(50.0)
            self.var_fijos.set(3000.0)
            self.var_costo_u.set(8.0)
            self.var_factor_k.set(0.02)
            self.var_cap_max.set(2500)
            self.var_demanda.set(2000)
            self.var_punto_x.set(2000.0)
        elif tipo == 'sobrecupo':
            # Escenario de Sobrecupo (Demanda 3500 u > Capacidad 1500 u)
            self.var_tarifa.set(50.0)
            self.var_fijos.set(3000.0)
            self.var_costo_u.set(8.0)
            self.var_factor_k.set(0.02)
            self.var_cap_max.set(1500)
            self.var_demanda.set(3500)
            self.var_punto_x.set(1500.0)
            
        self.actualizar_modelo()

    def _on_slider_change(self, val):
        self._actualizar_punto_grafica_y_metricas()

    def _on_canvas_click(self, event):
        if event.inaxes == self.ax and event.xdata is not None:
            self.arrastrando_punto = True
            x_val = max(0, min(event.xdata, self.rango_max_actual))
            self.var_punto_x.set(round(x_val, 1))
            self._actualizar_punto_grafica_y_metricas()

    def _on_canvas_drag(self, event):
        if self.arrastrando_punto and event.inaxes == self.ax and event.xdata is not None:
            x_val = max(0, min(event.xdata, self.rango_max_actual))
            self.var_punto_x.set(round(x_val, 1))
            self._actualizar_punto_grafica_y_metricas()

    def _on_canvas_release(self, event):
        self.arrastrando_punto = False

    def actualizar_modelo(self):
        try:
            tarifa = float(self.var_tarifa.get())
            fijos = float(self.var_fijos.get())
            costo_u = float(self.var_costo_u.get())
            k = float(self.var_factor_k.get())
            cap_max = int(self.var_cap_max.get())
            demanda = int(self.var_demanda.get())
        except Exception:
            messagebox.showerror("Error de Entrada", "Por favor verifique que todos los parámetros sean números válidos.")
            return
            
        if k <= 0:
            messagebox.showerror("Parámetro Inválido", "El factor de saturación (k) debe ser positivo (> 0).")
            return

        # 1. Cálculos de SymPy
        self.res_math = calculos_matematicos(tarifa, fijos, costo_u, k)
        x_opt = self.res_math['x_optimo']
        u_max = utilidad(x_opt, fijos, costo_u, k, tarifa)
        
        # Ajustar rango máximo del slider y gráfica
        self.rango_max_actual = max(cap_max, int(x_opt * 1.5), demanda, 1000)
        self.slider_x.config(to=self.rango_max_actual)
        
        # Texto de cálculo simbólico con explicaciones detalladas y pedagógicas
        txt = (
            f"1. Costo Marginal C'(x):\n"
            f"   C'(x) = {self.res_math['C_prime']}\n"
            f"   -> Costo adicional por cada nuevo usuario conectado.\n\n"
            f"2. Ingreso Marginal R'(x):\n"
            f"   R'(x) = {self.res_math['R_prime']}\n"
            f"   -> Ingreso directo generado por cada nuevo usuario.\n\n"
            f"3. Utilidad Marginal U'(x):\n"
            f"   U'(x) = {self.res_math['U_prime']}\n"
            f"   -> Ganancia neta añadida por usuario (R' - C').\n\n"
            f"4. Punto Crítico (U'(x) = 0):\n"
            f"   x* = {x_opt:,.1f} usuarios  |  Utilidad Máx = ${u_max:,.2f}\n"
            f"   -> Punto exacto donde R'(x) = C'(x) (máxima ganancia).\n\n"
            f"5. Criterio de la 2da Derivada:\n"
            f"   U''(x) = {self.res_math['U_double_prime']:.4f} < 0\n"
            f"   -> Como U'' es negativa, confirma un MÁXIMO ABSOLUTO.\n\n"
            f"6. Análisis de Concavidad:\n"
            f"   • C''(x) = {self.res_math['C_double_prime']:.4f} > 0 => C(x) cóncava hacia arriba.\n"
            f"   • U''(x) < 0 => U(x) cóncava hacia abajo (saturación).\n\n"
            f"7. Límite al Infinito:\n"
            f"   lim(x->∞) U(x) = {self.res_math['limite_inf']}\n"
            f"   -> Demuestra que la capacidad no puede crecer indefinidamente\n"
            f"      sin ampliar la infraestructura (costo cuadrático domina)."
        )
        self.txt_calculo.delete("1.0", tk.END)
        self.txt_calculo.insert(tk.END, txt)
        
        # 2. Actualizar Gráfica
        self._redibujar_grafica_completa()
        
        # 3. Comparativa y Decisión
        self.infras['Intermedia'] = {
            'fijos': fijos,
            'costo_usuario': costo_u,
            'factor_cuadratico': k,
            'capacidad_maxima': cap_max
        }
        reporte, mejor = recomendar_capacidad(demanda, self.infras, tarifa)
        
        dec_txt = f"Demanda Proyectada: {demanda} usuarios simultáneos | Tarifa: ${tarifa:,.2f}/usuario\n"
        dec_txt += "─"*72 + "\n"
        for item in reporte:
            status = f"[SATURADA: Sobrecupo de {item['sobrecupo']} u]" if item['saturada'] else "[Capacidad OK]"
            dec_txt += f"• {item['nombre'].upper():<11}: Capacidad {item['cap_max']:>5} u | Utilidad: ${item['utilidad']:>11,.2f} | {status}\n"
            
        dec_txt += "─"*72 + "\n"
        if mejor:
            alerta_amp = " (SE RECOMIENDA AMPLIAR INFRAESTRUCTURA)" if mejor['saturada'] else " (Capacidad suficiente, sin necesidad de ampliación)"
            dec_txt += f"DECISIÓN: Operar con Infraestructura '{mejor['nombre'].upper()}' (Utilidad: ${mejor['utilidad']:,.2f}).{alerta_amp}"
            
        self.txt_decision.delete("1.0", tk.END)
        self.txt_decision.insert(tk.END, dec_txt)

    def _redibujar_grafica_completa(self):
        tarifa = float(self.var_tarifa.get())
        fijos = float(self.var_fijos.get())
        costo_u = float(self.var_costo_u.get())
        k = float(self.var_factor_k.get())
        cap_max = int(self.var_cap_max.get())
        demanda = int(self.var_demanda.get())
        x_opt = self.res_math['x_optimo']
        u_max = utilidad(x_opt, fijos, costo_u, k, tarifa)
        
        self.ax.clear()
        x_vals = np.linspace(0, self.rango_max_actual, 450)
        c_vals = costo(x_vals, fijos, costo_u, k)
        r_vals = ingreso(x_vals, tarifa)
        u_vals = utilidad(x_vals, fijos, costo_u, k, tarifa)
        
        # Curvas principales
        self.ax.plot(x_vals, c_vals, label='Costo Total C(x)', color='#f87171', linestyle='--', linewidth=2.2)
        self.ax.plot(x_vals, r_vals, label='Ingreso Total R(x)', color='#4ade80', linestyle='--', linewidth=2.2)
        self.ax.plot(x_vals, u_vals, label='Utilidad Neta U(x)', color='#38bdf8', linewidth=2.8)
        self.ax.axhline(0, color='#64748b', linewidth=1)
        
        # Línea de capacidad física contractual
        self.ax.axvline(cap_max, color='#fbbf24', linestyle='-.', linewidth=1.8, label=f'Capacidad Máx ({cap_max} u)')
        
        # Línea de demanda proyectada
        self.ax.axvline(demanda, color='#c084fc', linestyle=':', linewidth=1.8, label=f'Demanda ({demanda} u)')
        
        # Punto Óptimo Teórico
        if x_opt > 0:
            self.ax.scatter([x_opt], [u_max], color='#e11d48', s=90, zorder=6, label=f'Óptimo (x={x_opt:.0f})')
            self.ax.annotate(
                f'Óptimo Teórico\nx = {x_opt:.0f} u\nU = ${u_max:,.0f}',
                xy=(x_opt, u_max),
                xytext=(x_opt * 1.05, u_max * 0.9),
                bbox=dict(boxstyle="round,pad=0.4", fc="#181926", ec="#38bdf8", lw=1.5),
                arrowprops=dict(arrowstyle="->", color="#38bdf8", lw=1.5),
                color='#ffffff', fontsize=9, fontweight='bold'
            )
            
        # Marcador interactivo dinámico
        self.dynamic_point, = self.ax.plot([], [], 'o', color='#facc15', markersize=12, zorder=8, markeredgecolor='#ffffff', markeredgewidth=1.5)
        self.dynamic_vline = self.ax.axvline(0, color='#facc15', linestyle='--', linewidth=1.2, alpha=0.7)
        
        self.ax.set_title("Curvas de Costo, Ingreso y Utilidad (Haz clic o arrastra el punto amarillo)", color='#f8fafc', fontsize=12, fontweight='bold', pad=10)
        self.ax.set_xlabel("Cantidad de Usuarios Simultáneos (x)", color='#cbd5e1', fontsize=10, fontweight='bold')
        self.ax.set_ylabel("Monto en Dólares ($)", color='#cbd5e1', fontsize=10, fontweight='bold')
        self.ax.tick_params(colors='#94a3b8', labelsize=9)
        self.ax.grid(True, linestyle=':', alpha=0.35, color='#64748b')
        self.ax.legend(facecolor='#181926', edgecolor='#475569', labelcolor='#e2e8f0', fontsize=9, loc='upper left')
        
        self._actualizar_punto_grafica_y_metricas()

    def _actualizar_punto_grafica_y_metricas(self):
        try:
            tarifa = float(self.var_tarifa.get())
            fijos = float(self.var_fijos.get())
            costo_u = float(self.var_costo_u.get())
            k = float(self.var_factor_k.get())
            cap_max = int(self.var_cap_max.get())
            x_val = float(self.var_punto_x.get())
        except Exception:
            return
            
        c_val = costo(x_val, fijos, costo_u, k)
        r_val = ingreso(x_val, tarifa)
        u_val = utilidad(x_val, fijos, costo_u, k, tarifa)
        
        # Actualizar métricas visuales superiores
        self.lbl_metric_x.config(text=f"Usuarios (x): {x_val:,.0f}")
        self.lbl_metric_c.config(text=f"Costo C(x): ${c_val:,.2f}")
        self.lbl_metric_r.config(text=f"Ingreso R(x): ${r_val:,.2f}")
        self.lbl_metric_u.config(text=f"Utilidad U(x): ${u_val:,.2f}")
        
        if x_val > cap_max:
            self.lbl_metric_status.config(text=f"SOBRECAPACIDAD (+{x_val-cap_max:.0f} u)", fg="#f87171")
        elif u_val < 0:
            self.lbl_metric_status.config(text="ZONA DE PÉRDIDAS", fg="#f87171")
        else:
            self.lbl_metric_status.config(text="OPERACIÓN RENTABLE", fg="#4ade80")
            
        # Mover marcador dinámico en la gráfica
        if hasattr(self, 'dynamic_point'):
            self.dynamic_point.set_data([x_val], [u_val])
            self.dynamic_vline.set_xdata([x_val, x_val])
            self.canvas.draw_idle()
            
        # Guardar automáticamente la imagen actualizada
        try:
            self.fig.savefig('grafico_utilidad.png', dpi=120)
        except Exception:
            pass


# ==============================================================================
# 5. PUNTO DE ENTRADA
# ==============================================================================

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--auto':
        res = calculos_matematicos(50.0, 3000.0, 8.0, 0.02)
        rep, mejor = recomendar_capacidad(900, INFRAESTRUCTURAS_DEFAULT, 50.0)
        print("Cálculo Simbólico:", res)
        print("Mejor Opción:", mejor)
    else:
        app = CapacidadApp()
        app.mainloop()
