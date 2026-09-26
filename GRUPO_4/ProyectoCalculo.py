import tkinter as tk
from tkinter import messagebox

import ttkbootstrap as ttk
import numpy as np
import pandas as pd

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


# ============================================================
# MODELO MATEMÁTICO
# ============================================================

class ModeloUsuarios:
    def __init__(self, usuarios_iniciales, saturacion, tasa, capacidad):
        if usuarios_iniciales <= 0:
            raise ValueError("Los usuarios iniciales deben ser mayores que 0.")
        if saturacion <= usuarios_iniciales:
            raise ValueError(
                "La saturación teórica debe ser mayor que los usuarios iniciales."
            )
        if tasa <= 0:
            raise ValueError("La tasa de crecimiento debe ser mayor que 0.")
        if capacidad <= 0:
            raise ValueError("La capacidad debe ser mayor que 0.")

        self.n0 = usuarios_iniciales
        self.k = saturacion
        self.r = tasa
        self.capacidad = capacidad
        self.a = (self.k - self.n0) / self.n0

    def usuarios(self, t):
        return self.k / (1 + self.a * np.exp(-self.r * t))

    def tasa_crecimiento(self, t):
        n = self.usuarios(t)
        return self.r * n * (1 - n / self.k)

    def aceleracion(self, t):
        n = self.usuarios(t)
        crecimiento = self.tasa_crecimiento(t)
        return self.r * crecimiento * (1 - 2 * n / self.k)

    def punto_inflexion(self):
        t = np.log(self.a) / self.r
        return t, self.usuarios(t)

    def limite_usuarios(self):
        return self.k

    def tiempo_para_usuarios(self, objetivo):
        if objetivo <= 0:
            raise ValueError("El objetivo debe ser mayor que 0.")
        if objetivo >= self.k:
            return np.inf

        return -np.log((self.k / objetivo - 1) / self.a) / self.r

    def proyectar_capacidad(self, porcentaje_alerta=0.80):
        if porcentaje_alerta <= 0 or porcentaje_alerta >= 1:
            raise ValueError("El porcentaje de alerta debe estar entre 0 y 1.")

        limite_alerta = self.capacidad * porcentaje_alerta
        mes_alerta = self.tiempo_para_usuarios(limite_alerta)
        mes_capacidad = self.tiempo_para_usuarios(self.capacidad)

        return limite_alerta, mes_alerta, mes_capacidad


# ============================================================
# INTERFAZ GRÁFICA
# ============================================================

class Aplicacion:
    PAGINAS = [
        "Configuración",
        "Resumen",
        "Tabla de proyección",
        "Usuarios N(t)",
        "Crecimiento N'(t)",
        "Aceleración N''(t)",
        "Comparación",
        "Conclusiones",
    ]

    SUBTITULOS = [
        "Defina los parámetros del escenario que desea analizar.",
        "Indicadores principales y validación matemática del modelo.",
        "Proyección mensual de usuarios, crecimiento y aceleración.",
        "Evolución de la cantidad total de usuarios.",
        "Comportamiento de la primera derivada.",
        "Comportamiento de la segunda derivada y la concavidad.",
        "Escenario base frente a un crecimiento alternativo.",
        "Interpretación matemática y recomendación empresarial.",
    ]

    def __init__(self, root):
        self.root = root
        self.root.title("Crecimiento de Usuarios y Planificación de Capacidad")
        self.root.geometry("1280x820")
        self.root.minsize(1120, 720)

        self.pagina_actual = 0
        self.modelo = None
        self.modelo_alternativo = None

        self.meses = None
        self.tabla = None
        self.usuarios_proyectados = None
        self.crecimiento = None
        self.aceleracion = None

        self.limite_alerta = None
        self.mes_alerta = None
        self.mes_capacidad = None
        self.mes_inflexion = None
        self.usuarios_inflexion = None
        self.crecimiento_maximo = None

        # Verificación analítica y numérica
        self.crecimiento_analitico = None
        self.verificacion_analitica = None

        self.alerta_alternativa = None
        self.capacidad_alternativa = None

        self.botones_menu = []

        self.crear_variables()
        self.crear_estructura()
        self.mostrar_pagina(0)

    # --------------------------------------------------------
    # VARIABLES DE ENTRADA
    # --------------------------------------------------------

    def crear_variables(self):
        self.var_n0 = tk.StringVar(value="2000")
        self.var_k = tk.StringVar(value="30000")
        self.var_r = tk.StringVar(value="0.22")
        self.var_capacidad = tk.StringVar(value="20000")
        self.var_periodos = tk.StringVar(value="24")
        self.var_alerta = tk.StringVar(value="80")
        self.var_r_alternativa = tk.StringVar(value="0.30")

    # --------------------------------------------------------
    # ESTRUCTURA GENERAL
    # --------------------------------------------------------

    def crear_estructura(self):
        marco_principal = ttk.Frame(self.root)
        marco_principal.pack(fill="both", expand=True)

        # Menú lateral
        self.sidebar = ttk.Frame(marco_principal, padding=(16, 18))
        self.sidebar.pack(side="left", fill="y")

        ttk.Label(
            self.sidebar,
            text="ANALÍTICA DIGITAL",
            font=("Segoe UI", 15, "bold"),
            bootstyle="primary",
        ).pack(anchor="w")

        ttk.Label(
            self.sidebar,
            text="Proyecto 4 · MA-0321",
            font=("Segoe UI", 9),
            bootstyle="secondary",
        ).pack(anchor="w", pady=(2, 18))

        ttk.Separator(self.sidebar, orient="horizontal").pack(
            fill="x", pady=(0, 14)
        )

        for indice, nombre in enumerate(self.PAGINAS):
            boton = ttk.Button(
                self.sidebar,
                text=f"{indice + 1:02d}  {nombre}",
                command=lambda i=indice: self.mostrar_pagina(i),
                bootstyle="secondary-outline",
                width=25,
            )
            boton.pack(fill="x", pady=4)
            self.botones_menu.append(boton)

        ttk.Separator(self.sidebar, orient="horizontal").pack(
            fill="x", pady=(18, 12)
        )

        self.lbl_sidebar_estado = ttk.Label(
            self.sidebar,
            text="Modelo logístico\nDatos simulados reproducibles",
            justify="left",
            font=("Segoe UI", 9),
            bootstyle="secondary",
        )
        self.lbl_sidebar_estado.pack(anchor="w")

        ttk.Separator(marco_principal, orient="vertical").pack(
            side="left", fill="y"
        )

        # Área principal
        self.area_derecha = ttk.Frame(marco_principal)
        self.area_derecha.pack(side="left", fill="both", expand=True)

        encabezado = ttk.Frame(self.area_derecha, padding=(22, 16))
        encabezado.pack(fill="x")

        bloque_titulo = ttk.Frame(encabezado)
        bloque_titulo.pack(side="left", fill="x", expand=True)

        self.lbl_titulo = ttk.Label(
            bloque_titulo,
            text="",
            font=("Segoe UI", 19, "bold"),
        )
        self.lbl_titulo.pack(anchor="w")

        self.lbl_subtitulo = ttk.Label(
            bloque_titulo,
            text="",
            font=("Segoe UI", 10),
            bootstyle="secondary",
        )
        self.lbl_subtitulo.pack(anchor="w", pady=(3, 0))

        self.lbl_pagina = ttk.Label(
            encabezado,
            text="",
            font=("Segoe UI", 10, "bold"),
            bootstyle="primary",
        )
        self.lbl_pagina.pack(side="right")

        ttk.Separator(self.area_derecha, orient="horizontal").pack(fill="x")

        self.contenido = ttk.Frame(self.area_derecha, padding=20)
        self.contenido.pack(fill="both", expand=True)

        ttk.Separator(self.area_derecha, orient="horizontal").pack(fill="x")

        navegacion = ttk.Frame(self.area_derecha, padding=(20, 12))
        navegacion.pack(fill="x")

        self.btn_config = ttk.Button(
            navegacion,
            text="Editar parámetros",
            command=lambda: self.mostrar_pagina(0),
            bootstyle="secondary-outline",
        )
        self.btn_config.pack(side="left")

        self.btn_anterior = ttk.Button(
            navegacion,
            text="← Anterior",
            command=self.anterior,
            bootstyle="secondary",
        )
        self.btn_anterior.pack(side="right")

        self.btn_siguiente = ttk.Button(
            navegacion,
            text="Siguiente →",
            command=self.siguiente,
            bootstyle="primary",
        )
        self.btn_siguiente.pack(side="right", padx=(0, 10))

    # --------------------------------------------------------
    # NAVEGACIÓN
    # --------------------------------------------------------

    def limpiar_contenido(self):
        for widget in self.contenido.winfo_children():
            widget.destroy()

    def actualizar_navegacion(self):
        self.lbl_titulo.config(text=self.PAGINAS[self.pagina_actual])
        self.lbl_subtitulo.config(text=self.SUBTITULOS[self.pagina_actual])
        self.lbl_pagina.config(
            text=f"{self.pagina_actual + 1} / {len(self.PAGINAS)}"
        )

        for indice, boton in enumerate(self.botones_menu):
            if indice == self.pagina_actual:
                boton.configure(bootstyle="primary")
            else:
                boton.configure(bootstyle="secondary-outline")

        self.btn_anterior.config(
            state="disabled" if self.pagina_actual == 0 else "normal"
        )
        self.btn_siguiente.config(
            state=(
                "disabled"
                if self.pagina_actual == len(self.PAGINAS) - 1
                else "normal"
            )
        )

    def actualizar_sidebar_modelo(self):
        if self.modelo is None:
            self.lbl_sidebar_estado.config(
                text="Modelo logístico\nDatos simulados reproducibles"
            )
            return

        self.lbl_sidebar_estado.config(
            text=(
                "Escenario base\n"
                f"N₀ = {self.modelo.n0:,.0f}\n"
                f"K = {self.modelo.k:,.0f}\n"
                f"r = {self.modelo.r:.2f}\n"
                f"Capacidad = {self.modelo.capacidad:,.0f}"
            )
        )

    def anterior(self):
        if self.pagina_actual > 0:
            self.mostrar_pagina(self.pagina_actual - 1)

    def siguiente(self):
        if self.pagina_actual == 0 and self.modelo is None:
            if not self.calcular_proyeccion(ir_a_resumen=False):
                return

        if self.pagina_actual < len(self.PAGINAS) - 1:
            self.mostrar_pagina(self.pagina_actual + 1)

    def mostrar_pagina(self, indice):
        if indice > 0 and self.modelo is None:
            if not self.calcular_proyeccion(ir_a_resumen=False):
                return

        self.pagina_actual = indice
        self.limpiar_contenido()
        self.actualizar_navegacion()

        paginas = {
            0: self.pagina_configuracion,
            1: self.pagina_resumen,
            2: self.pagina_tabla,
            3: self.pagina_grafica_usuarios,
            4: self.pagina_grafica_crecimiento,
            5: self.pagina_grafica_aceleracion,
            6: self.pagina_comparacion,
            7: self.pagina_conclusiones,
        }

        paginas[indice]()

    # --------------------------------------------------------
    # CÁLCULO DE LA PROYECCIÓN
    # --------------------------------------------------------

    def calcular_proyeccion(self, ir_a_resumen=True):
        try:
            n0 = float(self.var_n0.get())
            k = float(self.var_k.get())
            r = float(self.var_r.get())
            capacidad = float(self.var_capacidad.get())
            periodos = int(self.var_periodos.get())
            porcentaje_alerta = float(self.var_alerta.get()) / 100
            r_alternativa = float(self.var_r_alternativa.get())

            if periodos < 20:
                raise ValueError(
                    "El proyecto requiere al menos 20 períodos.\n\nUtilice 20 o más."
                )

            if r_alternativa <= 0:
                raise ValueError(
                    "La tasa del escenario alternativo debe ser mayor que 0."
                )

            self.modelo = ModeloUsuarios(n0, k, r, capacidad)
            self.modelo_alternativo = ModeloUsuarios(
                n0, k, r_alternativa, capacidad
            )

            self.meses = np.arange(0, periodos)
            self.usuarios_proyectados = self.modelo.usuarios(self.meses)
            self.crecimiento = self.modelo.tasa_crecimiento(self.meses)
            self.aceleracion = self.modelo.aceleracion(self.meses)

            self.tabla = pd.DataFrame(
                {
                    "Mes": self.meses,
                    "Usuarios": self.usuarios_proyectados,
                    "Tasa de crecimiento": self.crecimiento,
                    "Aceleración": self.aceleracion,
                }
            )

            self.tabla["Usuarios"] = (
                self.tabla["Usuarios"].round(0).astype(int)
            )
            self.tabla["Tasa de crecimiento"] = self.tabla[
                "Tasa de crecimiento"
            ].round(2)
            self.tabla["Aceleración"] = self.tabla["Aceleración"].round(2)

            (
                self.limite_alerta,
                self.mes_alerta,
                self.mes_capacidad,
            ) = self.modelo.proyectar_capacidad(porcentaje_alerta)

            (
                self.mes_inflexion,
                self.usuarios_inflexion,
            ) = self.modelo.punto_inflexion()

            # Valor calculado por la función programada
            self.crecimiento_maximo = self.modelo.tasa_crecimiento(
                self.mes_inflexion
            )

            # VERIFICACIÓN ANALÍTICA:
            # Para el modelo logístico N'máx = rK / 4
            self.crecimiento_analitico = self.modelo.r * self.modelo.k / 4

            # Comparación numérica entre el resultado analítico
            # y el obtenido mediante la función tasa_crecimiento().
            self.verificacion_analitica = np.isclose(
                self.crecimiento_analitico,
                self.crecimiento_maximo,
            )

            (
                _,
                self.alerta_alternativa,
                self.capacidad_alternativa,
            ) = self.modelo_alternativo.proyectar_capacidad(
                porcentaje_alerta
            )

            self.actualizar_sidebar_modelo()

            if ir_a_resumen:
                self.mostrar_pagina(1)

            return True

        except ValueError as error:
            messagebox.showerror("Datos inválidos", str(error))
            return False

    # --------------------------------------------------------
    # UTILIDADES
    # --------------------------------------------------------

    @staticmethod
    def formatear_mes(valor):
        if np.isinf(valor):
            return "No se alcanza"
        if valor < 0:
            return f"{valor:.2f} (ya se había alcanzado al inicio)"
        return f"{valor:.2f}"

    def mensaje_alerta_automatica(self):
        if np.isinf(self.mes_alerta):
            return (
                "El umbral preventivo configurado no se alcanza antes de la "
                "saturación teórica."
            )

        if self.mes_alerta < 0:
            return (
                "El nivel preventivo ya había sido superado al inicio del análisis."
            )

        if np.isinf(self.mes_capacidad):
            return (
                f"Alerta preventiva estimada para el mes {self.mes_alerta:.2f}. "
                "La capacidad operativa indicada no se alcanza dentro del límite "
                "teórico del modelo."
            )

        return (
            f"ALERTA PREVENTIVA: iniciar la planificación aproximadamente en el "
            f"mes {self.mes_alerta:.2f}, cuando se alcanzan "
            f"{self.limite_alerta:,.0f} usuarios. La capacidad operativa se "
            f"alcanzaría aproximadamente en el mes {self.mes_capacidad:.2f}."
        )

    def diferencia_escenarios(self):
        if np.isinf(self.mes_capacidad) or np.isinf(
            self.capacidad_alternativa
        ):
            return "No comparable"

        diferencia = self.mes_capacidad - self.capacidad_alternativa
        return f"{abs(diferencia):.2f} meses"

    # --------------------------------------------------------
    # FÓRMULAS MATEMÁTICAS CON MATPLOTLIB MATHTEXT
    # --------------------------------------------------------

    def mostrar_formula(self, contenedor, formula, alto=0.80, tamano=17):
        figura = Figure(figsize=(7.0, alto), dpi=100)
        figura.patch.set_facecolor("white")

        eje = figura.add_subplot(111)
        eje.set_facecolor("white")
        eje.axis("off")
        eje.text(
            0.5,
            0.5,
            formula,
            fontsize=tamano,
            ha="center",
            va="center",
        )

        figura.tight_layout(pad=0.2)

        canvas = FigureCanvasTkAgg(figura, master=contenedor)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="x", pady=(4, 8))

    # --------------------------------------------------------
    # TARJETAS
    # --------------------------------------------------------

    def crear_tarjeta(
        self,
        contenedor,
        titulo,
        valor,
        subtitulo="",
        estilo="primary",
    ):
        tarjeta = ttk.LabelFrame(
            contenedor,
            text=titulo,
            padding=12,
            bootstyle=estilo,
        )

        ttk.Label(
            tarjeta,
            text=valor,
            font=("Segoe UI", 15, "bold"),
        ).pack(anchor="w")

        if subtitulo:
            ttk.Label(
                tarjeta,
                text=subtitulo,
                font=("Segoe UI", 9),
                bootstyle="secondary",
                wraplength=235,
                justify="left",
            ).pack(anchor="w", pady=(4, 0))

        return tarjeta

    def crear_metricas_grafica(self, elementos):
        marco = ttk.Frame(self.contenido)
        marco.pack(fill="x", pady=(0, 8))

        for columna in range(len(elementos)):
            marco.columnconfigure(columna, weight=1)

        for columna, (titulo, valor, estilo) in enumerate(elementos):
            tarjeta = self.crear_tarjeta(
                marco,
                titulo,
                valor,
                "",
                estilo,
            )
            tarjeta.grid(
                row=0,
                column=columna,
                sticky="nsew",
                padx=5,
            )

    # ========================================================
    # PÁGINA 1: CONFIGURACIÓN
    # ========================================================

    def pagina_configuracion(self):
        self.contenido.columnconfigure(0, weight=1)
        self.contenido.columnconfigure(1, weight=1)

        panel_base = ttk.LabelFrame(
            self.contenido,
            text="Escenario base",
            padding=16,
            bootstyle="primary",
        )
        panel_base.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(0, 10),
            pady=(0, 12),
        )

        campos_base = [
            ("Usuarios iniciales N₀", self.var_n0, "Cantidad de usuarios al iniciar."),
            ("Saturación teórica K", self.var_k, "Límite teórico del modelo."),
            ("Tasa mensual r", self.var_r, "Velocidad de crecimiento."),
            (
                "Capacidad operativa",
                self.var_capacidad,
                "Máximo tecnológico soportado.",
            ),
        ]

        for fila, (etiqueta, variable, ayuda) in enumerate(campos_base):
            ttk.Label(
                panel_base,
                text=etiqueta,
                font=("Segoe UI", 10, "bold"),
            ).grid(row=fila * 2, column=0, sticky="w", pady=(4, 0))

            ttk.Entry(
                panel_base,
                textvariable=variable,
                width=22,
                bootstyle="primary",
            ).grid(
                row=fila * 2,
                column=1,
                sticky="ew",
                padx=(12, 0),
                pady=(4, 0),
            )

            ttk.Label(
                panel_base,
                text=ayuda,
                font=("Segoe UI", 8),
                bootstyle="secondary",
            ).grid(
                row=fila * 2 + 1,
                column=0,
                columnspan=2,
                sticky="w",
                pady=(0, 7),
            )

        panel_base.columnconfigure(1, weight=1)

        panel_analisis = ttk.LabelFrame(
            self.contenido,
            text="Configuración del análisis",
            padding=16,
            bootstyle="info",
        )
        panel_analisis.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=(10, 0),
            pady=(0, 12),
        )

        campos_analisis = [
            (
                "Cantidad de períodos",
                self.var_periodos,
                "El proyecto requiere 20 o más.",
            ),
            (
                "Alerta preventiva (%)",
                self.var_alerta,
                "Porcentaje de la capacidad operativa.",
            ),
            (
                "Tasa escenario alternativo",
                self.var_r_alternativa,
                "Se utiliza para comparar escenarios.",
            ),
        ]

        for fila, (etiqueta, variable, ayuda) in enumerate(campos_analisis):
            ttk.Label(
                panel_analisis,
                text=etiqueta,
                font=("Segoe UI", 10, "bold"),
            ).grid(row=fila * 2, column=0, sticky="w", pady=(4, 0))

            ttk.Entry(
                panel_analisis,
                textvariable=variable,
                width=22,
                bootstyle="info",
            ).grid(
                row=fila * 2,
                column=1,
                sticky="ew",
                padx=(12, 0),
                pady=(4, 0),
            )

            ttk.Label(
                panel_analisis,
                text=ayuda,
                font=("Segoe UI", 8),
                bootstyle="secondary",
            ).grid(
                row=fila * 2 + 1,
                column=0,
                columnspan=2,
                sticky="w",
                pady=(0, 7),
            )

        panel_analisis.columnconfigure(1, weight=1)

        ttk.Button(
            panel_analisis,
            text="Calcular proyección",
            command=self.calcular_proyeccion,
            bootstyle="success",
        ).grid(row=7, column=0, sticky="ew", pady=(18, 0))

        ttk.Button(
            panel_analisis,
            text="Restablecer valores",
            command=self.restablecer_valores,
            bootstyle="secondary-outline",
        ).grid(
            row=7,
            column=1,
            sticky="ew",
            padx=(10, 0),
            pady=(18, 0),
        )

        formula = ttk.LabelFrame(
            self.contenido,
            text="Modelo matemático utilizado",
            padding=12,
            bootstyle="secondary",
        )
        formula.grid(row=1, column=0, columnspan=2, sticky="ew")

        self.mostrar_formula(
            formula,
            r"$N(t)=\frac{K}{1+A e^{-rt}}$",
            alto=0.75,
            tamano=19,
        )

        ttk.Label(
            formula,
            text=(
                "A = (K - N₀) / N₀. Los datos son simulados y deterministas: "
                "con los mismos parámetros se obtienen exactamente los mismos resultados."
            ),
            wraplength=820,
            justify="center",
            bootstyle="secondary",
        ).pack(pady=(0, 4))

    def restablecer_valores(self):
        self.var_n0.set("2000")
        self.var_k.set("30000")
        self.var_r.set("0.22")
        self.var_capacidad.set("20000")
        self.var_periodos.set("24")
        self.var_alerta.set("80")
        self.var_r_alternativa.set("0.30")

        self.modelo = None
        self.modelo_alternativo = None
        self.actualizar_sidebar_modelo()

        messagebox.showinfo(
            "Valores restablecidos",
            "Se restauró el escenario base reproducible del proyecto.",
        )

    # ========================================================
    # PÁGINA 2: RESUMEN
    # ========================================================

    def pagina_resumen(self):
        panel = ttk.Frame(self.contenido)
        panel.pack(fill="both", expand=True)

        for columna in range(3):
            panel.columnconfigure(columna, weight=1)

        datos = [
            (
                "Usuarios iniciales",
                f"{self.modelo.n0:,.0f}",
                "Valor N₀ del modelo.",
                "primary",
            ),
            (
                "Saturación teórica",
                f"{self.modelo.k:,.0f}",
                "Límite K cuando t → ∞.",
                "info",
            ),
            (
                "Capacidad operativa",
                f"{self.modelo.capacidad:,.0f}",
                "Límite tecnológico usado para decidir.",
                "warning",
            ),
            (
                "Punto de inflexión",
                f"Mes {self.mes_inflexion:.2f}",
                f"{self.usuarios_inflexion:,.0f} usuarios.",
                "primary",
            ),
            (
                "Crecimiento máximo",
                f"{self.crecimiento_maximo:,.2f}",
                "usuarios por mes.",
                "success",
            ),
            (
                "Alerta preventiva",
                f"Mes {self.formatear_mes(self.mes_alerta)}",
                f"{self.limite_alerta:,.0f} usuarios.",
                "warning",
            ),
            (
                "Capacidad alcanzada",
                f"Mes {self.formatear_mes(self.mes_capacidad)}",
                "Momento estimado de capacidad operativa.",
                "danger",
            ),
            (
                "Crecimiento analítico",
                f"{self.crecimiento_analitico:,.2f}",
                "Resultado de rK/4.",
                "success",
            ),
            (
                "Verificación",
                "CORRECTA" if self.verificacion_analitica else "REVISAR",
                (
                    "El resultado analítico coincide con Python."
                    if self.verificacion_analitica
                    else "Los resultados no coinciden."
                ),
                "success" if self.verificacion_analitica else "danger",
            ),
        ]

        for indice, (titulo, valor, subtitulo, estilo) in enumerate(datos):
            fila = indice // 3
            columna = indice % 3

            tarjeta = self.crear_tarjeta(
                panel,
                titulo,
                valor,
                subtitulo,
                estilo,
            )
            tarjeta.grid(
                row=fila,
                column=columna,
                sticky="nsew",
                padx=7,
                pady=7,
            )

        formula = ttk.LabelFrame(
            self.contenido,
            text="Modelo del escenario actual",
            padding=8,
            bootstyle="secondary",
        )
        formula.pack(fill="x", pady=(12, 8))

        formula_modelo = (
            rf"$N(t)=\frac{{{self.modelo.k:.0f}}}"
            rf"{{1+{self.modelo.a:.4g}e^{{-{self.modelo.r:.4g}t}}}}$"
        )

        self.mostrar_formula(
            formula,
            formula_modelo,
            alto=0.72,
            tamano=18,
        )

        alerta = ttk.LabelFrame(
            self.contenido,
            text="Alerta automática de infraestructura",
            padding=12,
            bootstyle="warning",
        )
        alerta.pack(fill="x", pady=(4, 0))

        ttk.Label(
            alerta,
            text=self.mensaje_alerta_automatica(),
            wraplength=900,
            justify="left",
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor="w")

    # ========================================================
    # PÁGINA 3: TABLA
    # ========================================================

    def pagina_tabla(self):
        superior = ttk.Frame(self.contenido)
        superior.pack(fill="x", pady=(0, 10))

        ttk.Label(
            superior,
            text=f"{len(self.tabla)} períodos mensuales simulados y reproducibles",
            font=("Segoe UI", 10, "bold"),
            bootstyle="primary",
        ).pack(side="left")

        ttk.Label(
            superior,
            text="N(t): usuarios · N'(t): usuarios/mes · N''(t): usuarios/mes²",
            bootstyle="secondary",
        ).pack(side="right")

        marco_tabla = ttk.Frame(self.contenido)
        marco_tabla.pack(fill="both", expand=True)

        columnas = (
            "Mes",
            "Usuarios",
            "Tasa de crecimiento",
            "Aceleración",
        )

        tree = ttk.Treeview(
            marco_tabla,
            columns=columnas,
            show="headings",
            bootstyle="primary",
        )

        encabezados = {
            "Mes": "Mes",
            "Usuarios": "Usuarios N(t)",
            "Tasa de crecimiento": "N'(t) · usuarios/mes",
            "Aceleración": "N''(t) · usuarios/mes²",
        }

        for columna in columnas:
            tree.heading(columna, text=encabezados[columna])
            tree.column(columna, anchor="center", width=190)

        scrollbar_y = ttk.Scrollbar(
            marco_tabla,
            orient="vertical",
            command=tree.yview,
            bootstyle="primary-round",
        )
        tree.configure(yscrollcommand=scrollbar_y.set)

        tree.pack(side="left", fill="both", expand=True)
        scrollbar_y.pack(side="right", fill="y")

        for _, fila in self.tabla.iterrows():
            tree.insert(
                "",
                "end",
                values=(
                    int(fila["Mes"]),
                    int(fila["Usuarios"]),
                    f'{fila["Tasa de crecimiento"]:.2f}',
                    f'{fila["Aceleración"]:.2f}',
                ),
            )

    # --------------------------------------------------------
    # GRÁFICAS
    # --------------------------------------------------------

    def insertar_figura(self, figura):
        canvas = FigureCanvasTkAgg(figura, master=self.contenido)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    # ========================================================
    # PÁGINA 4: N(t)
    # ========================================================

    def pagina_grafica_usuarios(self):
        self.crear_metricas_grafica(
            [
                ("Alerta preventiva", f"{self.limite_alerta:,.0f}", "warning"),
                (
                    "Capacidad operativa",
                    f"{self.modelo.capacidad:,.0f}",
                    "danger",
                ),
                (
                    "Saturación teórica K",
                    f"{self.modelo.k:,.0f}",
                    "info",
                ),
            ]
        )

        formula = ttk.LabelFrame(
            self.contenido,
            text="Función de usuarios",
            padding=4,
            bootstyle="secondary",
        )
        formula.pack(fill="x", pady=(0, 8))

        formula_modelo = (
            rf"$N(t)=\frac{{{self.modelo.k:.0f}}}"
            rf"{{1+{self.modelo.a:.4g}e^{{-{self.modelo.r:.4g}t}}}}$"
        )
        self.mostrar_formula(formula, formula_modelo, alto=0.62, tamano=16)

        figura = Figure(figsize=(10, 5.0), dpi=100)
        eje = figura.add_subplot(111)

        t_suave = np.linspace(0, self.meses[-1], 400)
        usuarios_suaves = self.modelo.usuarios(t_suave)

        eje.plot(
            t_suave,
            usuarios_suaves,
            label="Usuarios proyectados N(t)",
            linewidth=2,
        )
        eje.scatter(
            self.meses,
            self.usuarios_proyectados,
            label="Períodos mensuales",
            s=18,
        )

        eje.axhline(
            y=self.limite_alerta,
            linestyle=":",
            label="Alerta preventiva",
        )
        eje.axhline(
            y=self.modelo.capacidad,
            linestyle="--",
            label="Capacidad operativa",
        )
        eje.axhline(
            y=self.modelo.k,
            linestyle="-.",
            label="Saturación teórica K",
        )

        if (
            not np.isinf(self.mes_alerta)
            and 0 <= self.mes_alerta <= self.meses[-1]
        ):
            eje.axvline(
                x=self.mes_alerta,
                linestyle=":",
                label="Mes de alerta",
            )

        if (
            not np.isinf(self.mes_capacidad)
            and 0 <= self.mes_capacidad <= self.meses[-1]
        ):
            eje.axvline(
                x=self.mes_capacidad,
                linestyle="--",
                label="Mes de capacidad operativa",
            )

        eje.set_xlabel("Mes")
        eje.set_ylabel("Cantidad de usuarios")
        eje.set_title("Proyección del crecimiento de usuarios")
        eje.legend(fontsize=8)
        eje.grid(True, alpha=0.3)

        figura.tight_layout()
        self.insertar_figura(figura)

    # ========================================================
    # PÁGINA 5: N'(t)
    # ========================================================

    def pagina_grafica_crecimiento(self):
        self.crear_metricas_grafica(
            [
                (
                    "Punto de inflexión",
                    f"Mes {self.mes_inflexion:.2f}",
                    "primary",
                ),
                (
                    "Crecimiento máximo",
                    f"{self.crecimiento_maximo:,.2f}",
                    "success",
                ),
                (
                    "Verificación",
                    "Correcta" if self.verificacion_analitica else "Revisar",
                    "success" if self.verificacion_analitica else "danger",
                ),
            ]
        )

        formula = ttk.LabelFrame(
            self.contenido,
            text="Primera derivada",
            padding=4,
            bootstyle="secondary",
        )
        formula.pack(fill="x", pady=(0, 8))

        formula_derivada = (
            rf"$N'(t)={self.modelo.r:.4g}N(t)"
            rf"\left(1-\frac{{N(t)}}{{{self.modelo.k:.0f}}}\right)$"
        )
        self.mostrar_formula(formula, formula_derivada, alto=0.62, tamano=16)

        figura = Figure(figsize=(10, 5.0), dpi=100)
        eje = figura.add_subplot(111)

        t_suave = np.linspace(0, self.meses[-1], 400)
        crecimiento_suave = self.modelo.tasa_crecimiento(t_suave)

        eje.plot(
            t_suave,
            crecimiento_suave,
            label="Tasa de crecimiento N'(t)",
            linewidth=2,
        )
        eje.axvline(
            x=self.mes_inflexion,
            linestyle="--",
            label="Punto de inflexión",
        )
        eje.scatter(
            self.mes_inflexion,
            self.crecimiento_maximo,
            label="Crecimiento máximo",
            s=55,
        )

        eje.set_xlabel("Mes")
        eje.set_ylabel("Usuarios por mes")
        eje.set_title("Tasa de crecimiento de usuarios")
        eje.legend()
        eje.grid(True, alpha=0.3)

        figura.tight_layout()
        self.insertar_figura(figura)

    # ========================================================
    # PÁGINA 6: N''(t)
    # ========================================================

    def pagina_grafica_aceleracion(self):
        self.crear_metricas_grafica(
            [
                ("Antes de la inflexión", "N''(t) > 0", "success"),
                ("En la inflexión", "N''(t) = 0", "primary"),
                ("Después de la inflexión", "N''(t) < 0", "warning"),
            ]
        )

        formula = ttk.LabelFrame(
            self.contenido,
            text="Segunda derivada",
            padding=4,
            bootstyle="secondary",
        )
        formula.pack(fill="x", pady=(0, 8))

        formula_aceleracion = (
            rf"$N''(t)={self.modelo.r:.4g}N'(t)"
            rf"\left(1-\frac{{2N(t)}}{{{self.modelo.k:.0f}}}\right)$"
        )
        self.mostrar_formula(formula, formula_aceleracion, alto=0.62, tamano=16)

        figura = Figure(figsize=(10, 5.0), dpi=100)
        eje = figura.add_subplot(111)

        t_suave = np.linspace(0, self.meses[-1], 400)
        aceleracion_suave = self.modelo.aceleracion(t_suave)

        eje.plot(
            t_suave,
            aceleracion_suave,
            label="Aceleración N''(t)",
            linewidth=2,
        )
        eje.axhline(y=0, linestyle="--", label="Aceleración = 0")
        eje.axvline(
            x=self.mes_inflexion,
            linestyle="--",
            label="Punto de inflexión",
        )
        eje.scatter(
            self.mes_inflexion,
            0,
            label="Cambio de concavidad",
            s=55,
        )

        eje.set_xlabel("Mes")
        eje.set_ylabel("Usuarios por mes²")
        eje.set_title("Aceleración del crecimiento de usuarios")
        eje.legend()
        eje.grid(True, alpha=0.3)

        figura.tight_layout()
        self.insertar_figura(figura)

    # ========================================================
    # PÁGINA 7: COMPARACIÓN
    # ========================================================

    def pagina_comparacion(self):
        self.crear_metricas_grafica(
            [
                (
                    f"Base r={self.modelo.r:.2f}",
                    f"Capacidad: {self.formatear_mes(self.mes_capacidad)}",
                    "primary",
                ),
                (
                    f"Alternativo r={self.modelo_alternativo.r:.2f}",
                    f"Capacidad: {self.formatear_mes(self.capacidad_alternativa)}",
                    "info",
                ),
                (
                    "Diferencia temporal",
                    self.diferencia_escenarios(),
                    "warning",
                ),
            ]
        )

        resumen = ttk.LabelFrame(
            self.contenido,
            text="Resumen de escenarios",
            padding=10,
            bootstyle="secondary",
        )
        resumen.pack(fill="x", pady=(0, 8))

        ttk.Label(
            resumen,
            text=(
                f"Escenario base: r = {self.modelo.r:.2f}  |  "
                f"Alerta: mes {self.formatear_mes(self.mes_alerta)}  |  "
                f"Capacidad operativa: mes {self.formatear_mes(self.mes_capacidad)}"
            ),
            font=("Segoe UI", 9, "bold"),
        ).pack(anchor="w")

        ttk.Label(
            resumen,
            text=(
                f"Escenario alternativo: r = {self.modelo_alternativo.r:.2f}  |  "
                f"Alerta: mes {self.formatear_mes(self.alerta_alternativa)}  |  "
                f"Capacidad operativa: mes "
                f"{self.formatear_mes(self.capacidad_alternativa)}"
            ),
            font=("Segoe UI", 9, "bold"),
        ).pack(anchor="w", pady=(4, 0))

        figura = Figure(figsize=(10, 5.1), dpi=100)
        eje = figura.add_subplot(111)

        t_suave = np.linspace(0, self.meses[-1], 400)
        usuarios_base = self.modelo.usuarios(t_suave)
        usuarios_alternativos = self.modelo_alternativo.usuarios(t_suave)

        eje.plot(
            t_suave,
            usuarios_base,
            label=f"Escenario base r = {self.modelo.r:.2f}",
            linewidth=2,
        )
        eje.plot(
            t_suave,
            usuarios_alternativos,
            label=f"Escenario alternativo r = {self.modelo_alternativo.r:.2f}",
            linewidth=2,
        )
        eje.axhline(
            y=self.limite_alerta,
            linestyle=":",
            label="Alerta preventiva",
        )
        eje.axhline(
            y=self.modelo.capacidad,
            linestyle="--",
            label="Capacidad operativa",
        )

        eje.set_xlabel("Mes")
        eje.set_ylabel("Cantidad de usuarios")
        eje.set_title("Comparación de escenarios de crecimiento")
        eje.legend(fontsize=8)
        eje.grid(True, alpha=0.3)

        figura.tight_layout()
        self.insertar_figura(figura)

    # ========================================================
    # PÁGINA 8: CONCLUSIONES
    # ========================================================

    def pagina_conclusiones(self):
        marco_superior = ttk.Frame(self.contenido)
        marco_superior.pack(fill="x", pady=(0, 10))

        tarjeta_alerta = self.crear_tarjeta(
            marco_superior,
            "Decisión empresarial",
            f"Planificar desde el mes {self.formatear_mes(self.mes_alerta)}",
            (
                "Procurar capacidad adicional antes del mes "
                f"{self.formatear_mes(self.mes_capacidad)}."
            ),
            "warning",
        )
        tarjeta_alerta.pack(fill="x")

        marco = ttk.Frame(self.contenido)
        marco.pack(fill="both", expand=True)

        texto = tk.Text(
            marco,
            wrap="word",
            font=("Segoe UI", 10),
            padx=18,
            pady=16,
            relief="flat",
        )

        scrollbar = ttk.Scrollbar(
            marco,
            orient="vertical",
            command=texto.yview,
            bootstyle="primary-round",
        )
        texto.configure(yscrollcommand=scrollbar.set)

        texto.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        texto.insert("1.0", self.generar_conclusion())
        texto.config(state="disabled")

    # --------------------------------------------------------
    # CONCLUSIONES DINÁMICAS
    # --------------------------------------------------------

    def generar_conclusion(self):
        alerta = self.formatear_mes(self.mes_alerta)
        capacidad = self.formatear_mes(self.mes_capacidad)

        if np.isinf(self.mes_capacidad):
            conclusion_capacidad = (
                "Con los parámetros actuales, la capacidad tecnológica indicada no "
                "se alcanza porque es igual o superior a la saturación teórica del modelo."
            )
        elif self.mes_capacidad < 0:
            conclusion_capacidad = (
                "La capacidad indicada ya habría sido superada al inicio del período analizado."
            )
        else:
            conclusion_capacidad = (
                f"La capacidad operativa de {self.modelo.capacidad:,.0f} usuarios "
                f"se alcanzaría aproximadamente en el mes {capacidad}."
            )

        if np.isinf(self.mes_alerta):
            conclusion_alerta = (
                "El umbral preventivo configurado no se alcanza dentro del comportamiento "
                "límite del modelo."
            )
        elif self.mes_alerta < 0:
            conclusion_alerta = (
                "El nivel preventivo ya estaría superado desde el inicio."
            )
        else:
            conclusion_alerta = (
                f"La alerta preventiva se activa aproximadamente en el mes {alerta}, "
                f"cuando se alcanzan {self.limite_alerta:,.0f} usuarios. Este momento "
                "puede utilizarse para iniciar la planificación de ampliación."
            )

        return (
            "1. MODELO UTILIZADO\n\n"
            "Se utiliza un modelo logístico de crecimiento:\n\n"
            "N(t) = K / (1 + A·e^(-r·t))\n\n"
            f"El escenario base inicia con {self.modelo.n0:,.0f} usuarios, "
            f"una saturación teórica K = {self.modelo.k:,.0f}, una tasa "
            f"r = {self.modelo.r:.4f} por mes y una capacidad operativa de "
            f"{self.modelo.capacidad:,.0f} usuarios.\n\n"

            "2. LÍMITE\n\n"
            f"Cuando t tiende a infinito, N(t) se aproxima a "
            f"{self.modelo.limite_usuarios():,.0f} usuarios.\n\n"
            "Por lo tanto, el modelo no proyecta un crecimiento indefinido.\n\n"

            "3. CRECIMIENTO Y PUNTO DE INFLEXIÓN\n\n"
            f"El punto de inflexión ocurre aproximadamente en el mes "
            f"{self.mes_inflexion:.2f}, con {self.usuarios_inflexion:,.0f} usuarios.\n\n"
            f"En ese momento la tasa de crecimiento alcanza aproximadamente "
            f"{self.crecimiento_maximo:,.2f} usuarios por mes.\n\n"
            f"Antes del mes {self.mes_inflexion:.2f}, N''(t) es positiva y el "
            "crecimiento se acelera.\n\n"
            "Después de ese momento, N''(t) es negativa y la cantidad de usuarios "
            "sigue aumentando, pero a una velocidad cada vez menor.\n\n"

            "4. VERIFICACIÓN ANALÍTICA Y NUMÉRICA\n\n"
            f"Mediante el cálculo analítico N'máx = rK/4, la tasa máxima de crecimiento "
            f"es {self.crecimiento_analitico:,.2f} usuarios por mes.\n\n"
            f"Mediante la función tasa_crecimiento(t) de Python se obtiene "
            f"{self.crecimiento_maximo:,.2f} usuarios por mes.\n\n"
            f"Verificación: "
            f"{'los resultados coinciden correctamente.' if self.verificacion_analitica else 'los resultados deben revisarse.'}\n\n"

            "5. CAPACIDAD TECNOLÓGICA\n\n"
            f"{conclusion_alerta}\n\n"
            f"{conclusion_capacidad}\n\n"

            "6. COMPARACIÓN DE ESCENARIOS\n\n"
            f"Con la tasa base r = {self.modelo.r:.2f}, la capacidad operativa se "
            f"alcanza en el mes {self.formatear_mes(self.mes_capacidad)}.\n\n"
            f"Con la tasa alternativa r = {self.modelo_alternativo.r:.2f}, la capacidad "
            f"operativa se alcanza en el mes "
            f"{self.formatear_mes(self.capacidad_alternativa)}.\n\n"
            "Esto muestra que una variación en la tasa de crecimiento puede cambiar "
            "significativamente el momento en que se necesita ampliar la infraestructura.\n\n"

            "7. DATOS SIMULADOS Y REPRODUCIBILIDAD\n\n"
            f"Esta ejecución utiliza {len(self.meses)} períodos de datos simulados.\n\n"
            "Los datos son reproducibles porque se generan a partir de la fórmula y de "
            "los parámetros mostrados en la pantalla de configuración.\n\n"
            "No se utiliza una semilla aleatoria, ya que los valores se generan de manera "
            "determinística mediante la función logística. Con los mismos parámetros se "
            "obtienen exactamente los mismos resultados.\n\n"
            "Los datos no se presentan como datos reales.\n\n"
            "Si se utilizaran datos reales, sería necesario indicar su fuente y definir "
            "cómo se ajusta el modelo matemático a esos datos.\n\n"

            "8. CONCLUSIÓN EMPRESARIAL\n\n"
            f"{self.mensaje_alerta_automatica()}\n\n"
            "El modelo permite anticipar cuándo la infraestructura actual puede resultar "
            "insuficiente y comparar diferentes escenarios antes de tomar decisiones.\n\n"
            "El umbral preventivo permite actuar antes de llegar al límite tecnológico, "
            "mientras que el modelo logístico evita suponer que el crecimiento puede "
            "continuar de manera indefinida."
        )


# ============================================================
# FUNCIÓN PRINCIPAL
# ============================================================

def main():
    # Puede cambiar "flatly" por "cosmo", "minty", "litera",
    # "darkly" o "superhero" para probar otros estilos.
    root = ttk.Window(themename="flatly")
    Aplicacion(root)
    root.mainloop()


if __name__ == "__main__":
    main()
