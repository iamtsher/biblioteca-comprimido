import os
from datetime import datetime, timedelta

import tkinter as tk
from tkinter import ttk, messagebox

from models import Prestamo, Ejemplar, Libro, Usuario, Recibo
from auth_manager import AuthManager, quitar_boton_cerrar, generar_pdf_reporte

try:
    from PIL import Image, ImageTk
    PIL_OK = True
except ImportError:
    PIL_OK = False


class PrestamosView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="#f1f5f9")
        self.auth = AuthManager()
        self._prestamos_actuales = []
        self._build_ui()

    def on_show(self):
        self.cargar_activos()

    def _build_ui(self):
        header = tk.Frame(self, bg="#f1f5f9", height=55)
        header.pack(fill="x", padx=25, pady=(12, 0))
        header.pack_propagate(False)

        tk.Button(header, text="Nuevo Préstamo",
                  font=("Segoe UI", 11, "bold"),
                  bg="#38bdf8", fg="#0f172a",
                  activebackground="#0ea5e9", activeforeground="white",
                  bd=0, cursor="hand2", padx=20, pady=8,
                  command=self.nuevo).pack(side="right", pady=8)

        tk.Button(header, text="Imprimir",
                  font=("Segoe UI", 11, "bold"),
                  bg="#8b5cf6", fg="white",
                  activebackground="#7c3aed", activeforeground="white",
                  bd=0, cursor="hand2", padx=20, pady=8,
                  command=self.imprimir_prestamos
                  ).pack(side="right", padx=(0, 10), pady=8)

        cards = tk.Frame(self, bg="#f1f5f9")
        cards.pack(fill="x", padx=25, pady=(10, 15))
        for i in range(4):
            cards.grid_columnconfigure(i, weight=1)

        self.card_activos = self._crear_card_resumen(
            cards, "Activos", "0", "#ef4444", 0)
        self.card_historial = self._crear_card_resumen(
            cards, "Históricos", "0", "#06b6d4", 1)
        self.card_ejemplares = self._crear_card_resumen(
            cards, "Ejemplares", "0", "#64748b", 2)
        self.card_fecha = self._crear_card_resumen(
            cards, "Fecha", datetime.now().strftime("%d/%m"), "#10b981", 3)

        acciones = tk.Frame(self, bg="#f1f5f9")
        acciones.pack(fill="x", padx=25, pady=(0, 10))

        botones = [
            ("Nuevo Préstamo", "#38bdf8", "#0f172a", self.nuevo),
            ("Historial", "#64748b", "white", self.historial),
        ]
        for texto, bg, fg, cmd in botones:
            tk.Button(acciones, text=texto,
                      font=("Segoe UI", 10, "bold"),
                      bg=bg, fg=fg,
                      activebackground=bg,
                      bd=0, cursor="hand2",
                      padx=15, pady=8,
                      command=cmd).pack(side="left", padx=3)

        tk.Button(acciones, text="Actualizar",
                  font=("Segoe UI", 10),
                  bg="#e2e8f0", fg="#0f172a",
                  activebackground="#cbd5e1",
                  bd=0, cursor="hand2",
                  padx=15, pady=8,
                  command=self.cargar_activos).pack(side="right", padx=3)

        buscar_frame = tk.Frame(self, bg="white", highlightthickness=1,
                                highlightbackground="#e2e8f0")
        buscar_frame.pack(fill="x", padx=25, pady=(0, 15))

        tk.Label(buscar_frame, text="Buscar:",
                 font=("Segoe UI", 10, "bold"),
                 bg="white", fg="#334155").pack(side="left", padx=(20, 10))

        self.entry_buscar = ttk.Entry(buscar_frame, width=40, font=("Segoe UI", 10))
        self.entry_buscar.pack(side="left", padx=5, pady=15)
        self.entry_buscar.bind("<Return>", lambda e: self.buscar())

        tk.Button(buscar_frame, text="Buscar",
                  font=("Segoe UI", 10, "bold"),
                  bg="#1e293b", fg="white",
                  bd=0, cursor="hand2", padx=18, pady=8,
                  command=self.buscar).pack(side="left", padx=5)

        tk.Button(buscar_frame, text="Mostrar Activos",
                  font=("Segoe UI", 10),
                  bg="#e2e8f0", fg="#1e293b",
                  bd=0, cursor="hand2", padx=18, pady=8,
                  command=self.cargar_activos).pack(side="left", padx=5)

        container_outer = tk.Frame(self, bg="#f1f5f9")
        container_outer.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self.canvas = tk.Canvas(container_outer, bg="#f1f5f9", highlightthickness=0)
        scroll = tk.Scrollbar(container_outer, orient="vertical",
                              command=self.canvas.yview)
        self.frame_prestamos = tk.Frame(self.canvas, bg="#f1f5f9")

        self.canvas_window = self.canvas.create_window(
            (0, 0), window=self.frame_prestamos, anchor="nw")
        self.canvas.configure(yscrollcommand=scroll.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        self.frame_prestamos.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width))

        self.frame_prestamos.grid_columnconfigure(0, weight=1, uniform="col")
        self.frame_prestamos.grid_columnconfigure(1, weight=1, uniform="col")

        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_mousewheel(self, event):
        try:
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        except Exception:
            pass

    def _crear_card_resumen(self, parent, titulo, valor, color, col):
        card = tk.Frame(parent, bg="white", highlightthickness=1,
                        highlightbackground="#e2e8f0")
        card.grid(row=0, column=col, padx=6, pady=6, sticky="nsew")
        tk.Frame(card, bg=color, height=4).pack(fill="x")

        inner = tk.Frame(card, bg="white")
        inner.pack(fill="both", expand=True, padx=18, pady=12)

        tk.Label(inner, text=titulo, font=("Segoe UI", 9),
                 bg="white", fg="#64748b").pack(anchor="w")

        lbl_valor = tk.Label(inner, text=valor,
                             font=("Segoe UI", 20, "bold"),
                             bg="white", fg=color)
        lbl_valor.pack(anchor="w", pady=(2, 0))

        card.lbl_valor = lbl_valor
        return card

    def _limpiar_tarjetas(self):
        for w in self.frame_prestamos.winfo_children():
            w.destroy()

    def _crear_tarjeta(self, parent, prestamo, fila, columna):
        es_admin = self.auth.es_admin()
        u_actual = self.auth.get_usuario_actual()
        es_mi_prestamo = (u_actual and prestamo.nombre_usuario == u_actual.usuario_login)

        hoy = datetime.now().date()
        dias_restantes = None

        try:
            if prestamo.fecha_devolucion_esperada:
                fecha_dev = datetime.strptime(
                    str(prestamo.fecha_devolucion_esperada)[:10],
                    "%Y-%m-%d").date()
                dias_restantes = (fecha_dev - hoy).days
        except Exception:
            pass

        if prestamo.estado_prestamo == "activo":
            if dias_restantes is not None and dias_restantes < 0:
                color_estado, bg_estado, fg_estado = ("#ef4444", "#fee2e2", "#991b1b")
                texto_estado = f"Vencido hace {abs(dias_restantes)} días"
            elif dias_restantes is not None and dias_restantes <= 3:
                color_estado, bg_estado, fg_estado = ("#f59e0b", "#fed7aa", "#9a3412")
                texto_estado = f"Vence en {dias_restantes} días"
            else:
                color_estado, bg_estado, fg_estado = ("#3b82f6", "#dbeafe", "#1e40af")
                texto_estado = "Activo"
        elif prestamo.estado_prestamo == "vencido":
            color_estado, bg_estado, fg_estado = ("#dc2626", "#fee2e2", "#991b1b")
            texto_estado = "Vencido"
        else:
            color_estado, bg_estado, fg_estado = ("#64748b", "#e2e8f0", "#334155")
            texto_estado = "Devuelto"

        card = tk.Frame(parent, bg="white", highlightthickness=1,
                        highlightbackground="#e2e8f0")
        card.grid(row=fila, column=columna, padx=8, pady=8, sticky="nsew")
        tk.Frame(card, bg=color_estado, height=4).pack(fill="x")

        inner = tk.Frame(card, bg="white")
        inner.pack(fill="both", expand=True, padx=18, pady=15)

        top = tk.Frame(inner, bg="white")
        top.pack(fill="x")

        info_top = tk.Frame(top, bg="white")
        info_top.pack(side="left", fill="x", expand=True)

        if es_admin:
            tk.Label(info_top, text=f"Préstamo #{prestamo.id_prestamo}",
                     font=("Segoe UI", 13, "bold"),
                     bg="white", fg="#0f172a").pack(anchor="w")
        else:
            tk.Label(info_top, text="Mi préstamo",
                     font=("Segoe UI", 13, "bold"),
                     bg="white", fg="#0f172a").pack(anchor="w")

        tk.Label(info_top, text=f"{prestamo.nombre_usuario}",
                 font=("Segoe UI", 10),
                 bg="white", fg="#475569").pack(anchor="w", pady=(2, 0))

        tk.Frame(inner, bg="#e2e8f0", height=1).pack(fill="x", pady=12)

        fechas = tk.Frame(inner, bg="white")
        fechas.pack(fill="x")

        f1 = tk.Frame(fechas, bg="white")
        f1.pack(side="left", fill="x", expand=True)

        tk.Label(f1, text="Solicitado", font=("Segoe UI", 9),
                 bg="white", fg="#94a3b8").pack(anchor="w")
        fecha_sol = str(prestamo.fecha_solicitud)[:10] if prestamo.fecha_solicitud else "—"
        tk.Label(f1, text=fecha_sol,
                 font=("Segoe UI", 10, "bold"),
                 bg="white", fg="#0f172a").pack(anchor="w")

        f2 = tk.Frame(fechas, bg="white")
        f2.pack(side="left", fill="x", expand=True)

        tk.Label(f2, text="Devolución", font=("Segoe UI", 9),
                 bg="white", fg="#94a3b8").pack(anchor="w")
        fecha_dev = (str(prestamo.fecha_devolucion_esperada)[:10]
                     if prestamo.fecha_devolucion_esperada else "—")
        tk.Label(f2, text=fecha_dev,
                 font=("Segoe UI", 10, "bold"),
                 bg="white", fg="#0f172a").pack(anchor="w")

        badge_frame = tk.Frame(inner, bg="white")
        badge_frame.pack(fill="x", pady=(12, 0))

        tk.Label(badge_frame,
                 text=f"  {texto_estado}  ",
                 font=("Segoe UI", 10, "bold"),
                 bg=bg_estado, fg=fg_estado,
                 padx=10, pady=5).pack(side="left")

        botones = tk.Frame(inner, bg="white")
        botones.pack(fill="x", pady=(12, 0))

        tk.Button(botones, text="Comprobante",
                  font=("Segoe UI", 9, "bold"),
                  bg="#e2e8f0", fg="#0f172a",
                  activebackground="#cbd5e1",
                  bd=0, cursor="hand2", padx=12, pady=6,
                  command=lambda p=prestamo: self.comprobante_directo(p)
                  ).pack(side="left", padx=2)

        if prestamo.estado_prestamo == "activo":
            if not es_admin and es_mi_prestamo:
                tk.Button(botones, text="Devolver",
                          font=("Segoe UI", 9, "bold"),
                          bg="#dbeafe", fg="#1e40af",
                          activebackground="#bfdbfe",
                          bd=0, cursor="hand2", padx=12, pady=6,
                          command=lambda p=prestamo: self.devolver_directo(p)
                          ).pack(side="left", padx=2)
            elif es_admin:
                tk.Button(botones, text="Gestionar",
                          font=("Segoe UI", 9, "bold"),
                          bg="#fef3c7", fg="#92400e",
                          activebackground="#fde68a",
                          bd=0, cursor="hand2", padx=12, pady=6,
                          command=lambda p=prestamo: self.gestionar_admin(p)
                          ).pack(side="left", padx=2)

    def cargar_activos(self):
        self._limpiar_tarjetas()
        self.entry_buscar.delete(0, tk.END)

        try:
            es_admin = self.auth.es_admin()
            u_actual = self.auth.get_usuario_actual()
            prestamos = Prestamo.obtener_activos()

            if not es_admin and u_actual:
                prestamos = [p for p in prestamos
                             if p.nombre_usuario == u_actual.usuario_login]

            self._prestamos_actuales = prestamos

            for i, prestamo in enumerate(prestamos):
                self._crear_tarjeta(self.frame_prestamos, prestamo,
                                    i // 2, i % 2)

            total_ejemplares = sum(p.ejemplares_count or 0 for p in prestamos)

            self.card_activos.lbl_valor.config(text=str(len(prestamos)))
            self.card_ejemplares.lbl_valor.config(text=str(total_ejemplares))

            try:
                historial = Prestamo.obtener_historial()
                if not es_admin and u_actual:
                    historial = [h for h in historial
                                 if h.nombre_usuario == u_actual.usuario_login]
                self.card_historial.lbl_valor.config(text=str(len(historial)))
            except Exception:
                self.card_historial.lbl_valor.config(text="0")

            self.card_fecha.lbl_valor.config(text=datetime.now().strftime("%d/%m"))
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar:\n\n{e}")

    def buscar(self):
        texto = self.entry_buscar.get().strip().lower()
        if not texto:
            self.cargar_activos()
            return

        self._limpiar_tarjetas()
        try:
            es_admin = self.auth.es_admin()
            u_actual = self.auth.get_usuario_actual()
            prestamos = Prestamo.obtener_activos()

            if not es_admin and u_actual:
                prestamos = [p for p in prestamos
                             if p.nombre_usuario == u_actual.usuario_login]

            filtrados = [p for p in prestamos
                         if texto in str(p.nombre_usuario or "").lower()]
            self._prestamos_actuales = filtrados

            for i, prestamo in enumerate(filtrados):
                self._crear_tarjeta(self.frame_prestamos, prestamo,
                                    i // 2, i % 2)

            if not filtrados:
                tk.Label(self.frame_prestamos,
                         text="No se encontraron préstamos",
                         font=("Segoe UI", 12),
                         bg="#f1f5f9", fg="#94a3b8").pack(pady=40)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def imprimir_prestamos(self):
        if not self._prestamos_actuales:
            messagebox.showwarning("Sin datos",
                                   "No hay préstamos para imprimir.\n\n"
                                   "Carga algunos préstamos primero.")
            return

        try:
            columnas = ["ID", "Usuario", "Solicitud", "Devolución",
                        "Estado", "Ejemplares"]
            filas = []
            activos = devueltos = vencidos = 0
            hoy = datetime.now().date()

            for prestamo in self._prestamos_actuales:
                estado_texto = prestamo.estado_prestamo.capitalize()
                if (prestamo.estado_prestamo == "activo"
                        and prestamo.fecha_devolucion_esperada):
                    try:
                        fecha_dev = datetime.strptime(
                            str(prestamo.fecha_devolucion_esperada)[:10],
                            "%Y-%m-%d").date()
                        if fecha_dev < hoy:
                            estado_texto = "VENCIDO"
                            vencidos += 1
                    except Exception:
                        pass

                filas.append([
                    prestamo.id_prestamo,
                    prestamo.nombre_usuario or "—",
                    str(prestamo.fecha_solicitud)[:10] if prestamo.fecha_solicitud else "—",
                    str(prestamo.fecha_devolucion_esperada)[:10] if prestamo.fecha_devolucion_esperada else "—",
                    estado_texto,
                    prestamo.ejemplares_count or 0,
                ])

                if prestamo.estado_prestamo == "activo":
                    activos += 1
                else:
                    devueltos += 1

            resumen = [
                ("Total de préstamos", len(filas)),
                ("Activos", activos),
                ("Devueltos", devueltos),
            ]
            if vencidos > 0:
                resumen.append(("Vencidos", vencidos))

            fecha_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            ruta_pdf = generar_pdf_reporte(
                titulo_reporte="REPORTE DE PRÉSTAMOS",
                columnas=columnas,
                filas=filas,
                resumen=resumen,
                nombre_archivo=f"Reporte_Prestamos_{fecha_str}.pdf"
            )

            try:
                os.startfile(ruta_pdf)
                messagebox.showinfo("PDF generado",
                                    f"Reporte generado correctamente:\n\n{ruta_pdf}")
            except Exception:
                messagebox.showinfo("PDF generado",
                                    f"Reporte guardado en:\n\n{ruta_pdf}")
        except ImportError as e:
            messagebox.showerror("Error", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo generar el PDF:\n\n{e}")

    def nuevo(self):
        w = tk.Toplevel(self)
        w.title("Nuevo Préstamo")
        w.geometry("700x680")
        w.configure(bg="#f1f5f9")
        w.transient(self)
        w.grab_set()
        w.focus_force()
        w.resizable(False, False)
        quitar_boton_cerrar(w)

        header = tk.Frame(w, bg="#0f172a", height=100)
        header.pack(fill="x")
        header.pack_propagate(False)

        header_inner = tk.Frame(header, bg="#0f172a")
        header_inner.pack(side="left", padx=30, pady=20)

        titulos_frame = tk.Frame(header_inner, bg="#0f172a")
        titulos_frame.pack(side="left")

        tk.Label(titulos_frame, text="Registrar Nuevo Préstamo",
                 font=("Segoe UI", 20, "bold"),
                 bg="#0f172a", fg="#f8fafc").pack(anchor="w")

        tk.Label(titulos_frame, text="Completa los datos del préstamo",
                 font=("Segoe UI", 11),
                 bg="#0f172a", fg="#94a3b8").pack(anchor="w", pady=(2, 0))

        tk.Button(header, text="Cerrar",
                  font=("Segoe UI", 11, "bold"),
                  bg="#ef4444", fg="white",
                  activebackground="#dc2626", activeforeground="white",
                  bd=0, cursor="hand2", padx=25, pady=10,
                  command=w.destroy).pack(side="right", padx=30, pady=30)

        body = tk.Frame(w, bg="#f1f5f9")
        body.pack(fill="both", expand=True, padx=25, pady=15)

        card_sel = tk.Frame(body, bg="white", highlightthickness=1,
                            highlightbackground="#e2e8f0")
        card_sel.pack(fill="x", pady=(0, 12))
        tk.Frame(card_sel, bg="#38bdf8", height=5).pack(fill="x")

        inner_sel = tk.Frame(card_sel, bg="white", padx=30, pady=20)
        inner_sel.pack(fill="x")

        tk.Label(inner_sel, text="Información del Préstamo",
                 font=("Segoe UI", 14, "bold"),
                 bg="white", fg="#0f172a").pack(anchor="w", pady=(0, 5))

        tk.Label(inner_sel,
                 text="Selecciona el usuario, el libro y el ejemplar a prestar",
                 font=("Segoe UI", 10),
                 bg="white", fg="#64748b").pack(anchor="w", pady=(0, 15))

        es_admin = self.auth.es_admin()
        u_actual = self.auth.get_usuario_actual()

        def crear_campo(parent, label):
            frame = tk.Frame(parent, bg="white")
            frame.pack(fill="x", pady=(0, 12))

            tk.Label(frame, text=label,
                     font=("Segoe UI", 11, "bold"),
                     bg="white", fg="#334155",
                     width=14, anchor="w").pack(side="left")
            return frame

        f_usuario = crear_campo(inner_sel, "Usuario")
        combo_usuario = ttk.Combobox(f_usuario, width=42, state="readonly",
                                     font=("Segoe UI", 11))

        if es_admin:
            usuarios = Usuario.obtener_todos()
            combo_usuario["values"] = [
                f"{u.id_usuario} - {u.usuario_login}" for u in usuarios
            ]
            if usuarios:
                combo_usuario.current(0)
        else:
            combo_usuario["values"] = [
                f"{u_actual.id_usuario} - {u_actual.usuario_login}"
            ]
            combo_usuario.current(0)

        combo_usuario.pack(side="left", padx=(10, 0), ipady=5)

        f_libro = crear_campo(inner_sel, "Libro")
        combo_libro = ttk.Combobox(f_libro, width=42, state="readonly",
                                   font=("Segoe UI", 11))
        libros = Libro.obtener_todos(limit=1000)
        combo_libro["values"] = [f"{l.idLibro} - {l.Book_Title}" for l in libros]
        combo_libro.pack(side="left", padx=(10, 0), ipady=5)

        f_ejemplar = crear_campo(inner_sel, "Ejemplar")
        combo_ejemplar = ttk.Combobox(f_ejemplar, width=42, state="readonly",
                                      font=("Segoe UI", 11))
        combo_ejemplar.pack(side="left", padx=(10, 0), ipady=5)

        f_fecha = crear_campo(inner_sel, "Devolución")
        entry_fecha = ttk.Entry(f_fecha, width=20, font=("Segoe UI", 11))
        entry_fecha.insert(0, (datetime.now() + timedelta(days=14))
                           .strftime("%Y-%m-%d"))
        entry_fecha.pack(side="left", padx=(10, 0), ipady=5)

        tk.Label(f_fecha, text="(YYYY-MM-DD)",
                 font=("Segoe UI", 9, "italic"),
                 bg="white", fg="#94a3b8").pack(side="left", padx=(10, 0))

        def seleccionar_libro(event):
            seleccionado = combo_libro.get()
            if not seleccionado or " - " not in seleccionado:
                return
            try:
                id_libro = int(seleccionado.split(" - ")[0])
            except Exception:
                return

            ejemplares = Ejemplar.obtener_disponibles_por_libro(id_libro)
            combo_ejemplar["values"] = [
                f"{e.id_ejemplar} - {e.titulo_libro} [{e.estado}]"
                for e in ejemplares
            ]
            if ejemplares:
                combo_ejemplar.current(0)
            else:
                combo_ejemplar.set("")
                messagebox.showwarning("Sin ejemplares",
                                       "Este libro no tiene ejemplares disponibles.",
                                       parent=w)

        combo_libro.bind("<<ComboboxSelected>>", seleccionar_libro)

        card_info = tk.Frame(body, bg="#eff6ff", highlightthickness=1,
                             highlightbackground="#bfdbfe")
        card_info.pack(fill="x", pady=(0, 12))

        inner_info = tk.Frame(card_info, bg="#eff6ff", padx=25, pady=12)
        inner_info.pack(fill="x")

        tk.Label(inner_info, text="Información Importante",
                 font=("Segoe UI", 11, "bold"),
                 bg="#eff6ff", fg="#1e40af").pack(anchor="w", pady=(0, 6))

        tips = [
            "Selecciona el libro para cargar los ejemplares disponibles",
            "La fecha por defecto es 14 días desde hoy",
        ]
        for tip in tips:
            fila = tk.Frame(inner_info, bg="#eff6ff")
            fila.pack(fill="x", pady=1)

            tk.Label(fila, text="•",
                     font=("Segoe UI", 10),
                     bg="#eff6ff", fg="#2563eb").pack(side="left", anchor="n", pady=3)

            tk.Label(fila, text=tip,
                     font=("Segoe UI", 10),
                     bg="#eff6ff", fg="#1e40af",
                     anchor="w", justify="left",
                     wraplength=550).pack(side="left", padx=(10, 0))

        def guardar():
            usuario = combo_usuario.get()
            ejemplar = combo_ejemplar.get()

            if not usuario or " - " not in usuario:
                messagebox.showwarning("Campos requeridos",
                                       "Selecciona un usuario.", parent=w)
                combo_usuario.focus()
                return

            if not ejemplar or " - " not in ejemplar:
                messagebox.showwarning("Campos requeridos",
                                       "Selecciona un ejemplar.\n\n"
                                       "Recuerda: primero debes elegir un libro.",
                                       parent=w)
                combo_ejemplar.focus()
                return

            try:
                uid = int(usuario.split(" - ")[0])
                eid = int(ejemplar.split(" - ")[0])
                fecha = entry_fecha.get().strip()

                if Usuario.tiene_prestamos_vencidos(uid):
                    messagebox.showwarning(
                        "Usuario bloqueado",
                        "Este usuario tiene préstamos VENCIDOS.\n\n"
                        "Debe devolverlos antes de pedir nuevos libros.",
                        parent=w)
                    return

                p = Prestamo(id_usuario=uid,
                             fecha_devolucion_esperada=fecha)
                ok, msg = p.realizar_prestamo(eid)

                if ok:
                    w.destroy()
                    self.cargar_activos()
                    messagebox.showinfo("Éxito",
                                        "Préstamo registrado correctamente.")
                else:
                    messagebox.showerror("Error", msg, parent=w)
            except Exception as e:
                messagebox.showerror("Error", str(e), parent=w)

        botones_frame = tk.Frame(body, bg="#f1f5f9")
        botones_frame.pack(fill="x", pady=(5, 0))

        btn_registrar = tk.Button(
            botones_frame, text="Registrar Préstamo",
            font=("Segoe UI", 13, "bold"),
            bg="#10b981", fg="white",
            activebackground="#059669", activeforeground="white",
            bd=0, cursor="hand2",
            padx=45, pady=10,
            command=guardar)
        btn_registrar.pack()

        btn_registrar.bind("<Enter>",
                           lambda e: btn_registrar.config(bg="#059669"))
        btn_registrar.bind("<Leave>",
                           lambda e: btn_registrar.config(bg="#10b981"))

    def devolver(self):
        messagebox.showinfo("Info",
                            "Haz clic en el botón Devolver dentro de la tarjeta.")

    def devolver_directo(self, prestamo):
        if messagebox.askyesno("Confirmar devolución",
                               f"¿Registrar devolución del préstamo "
                               f"#{prestamo.id_prestamo}?\n\n"
                               f"Usuario: {prestamo.nombre_usuario}"):
            try:
                ok, msg = prestamo.devolver()
                if ok:
                    self.cargar_activos()
                    messagebox.showinfo("Éxito", f"{msg}")
                else:
                    messagebox.showerror("Error", msg)
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def gestionar_admin(self, prestamo):
        w = tk.Toplevel(self)
        w.title(f"Gestionar Préstamo #{prestamo.id_prestamo}")
        w.geometry("480x420")
        w.configure(bg="#f1f5f9")
        w.transient(self)
        w.grab_set()
        w.focus_force()
        quitar_boton_cerrar(w)

        header = tk.Frame(w, bg="#334155", height=80)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(header, text="Gestionar Préstamo",
                 font=("Segoe UI", 16, "bold"),
                 bg="#334155", fg="#93c5fd").pack(side="left", padx=25, pady=25)

        tk.Button(header, text="Cerrar",
                  font=("Segoe UI", 10, "bold"),
                  bg="#ef4444", fg="white",
                  activebackground="#dc2626", activeforeground="white",
                  bd=0, cursor="hand2", padx=15, pady=6,
                  command=w.destroy).pack(side="right", padx=20, pady=22)

        body = tk.Frame(w, bg="white", padx=30, pady=25)
        body.pack(fill="both", expand=True, padx=15, pady=15)

        tk.Label(body, text=f"Préstamo #{prestamo.id_prestamo}",
                 font=("Segoe UI", 13, "bold"),
                 bg="white", fg="#0f172a").pack(anchor="w")

        tk.Label(body, text=f"Usuario: {prestamo.nombre_usuario}",
                 font=("Segoe UI", 10),
                 bg="white", fg="#64748b").pack(anchor="w", pady=(4, 20))

        def marcar_vencido():
            if messagebox.askyesno(
                    "Confirmar",
                    "¿Marcar este préstamo como VENCIDO?\n\n"
                    "El usuario ya no podrá devolverlo normalmente.",
                    parent=w):
                ok, msg = prestamo.marcar_vencido()
                if ok:
                    messagebox.showinfo("Éxito", f"{msg}", parent=w)
                    w.destroy()
                    self.cargar_activos()
                else:
                    messagebox.showerror("Error", msg, parent=w)

        def eliminar_prestamo():
            if messagebox.askyesno(
                    "Confirmar",
                    "¿Eliminar este préstamo del sistema?\n\n"
                    "El ejemplar volverá a estar disponible.",
                    parent=w):
                prestamo.eliminar()
                messagebox.showinfo("Éxito",
                                    "Préstamo eliminado.", parent=w)
                w.destroy()
                self.cargar_activos()

        tk.Button(body, text="Marcar como Vencido",
                  font=("Segoe UI", 11, "bold"),
                  bg="#3b82f6", fg="white",
                  activebackground="#2563eb", activeforeground="white",
                  bd=0, cursor="hand2", padx=20, pady=12,
                  command=marcar_vencido).pack(fill="x", pady=5)

        tk.Button(body, text="Eliminar Préstamo",
                  font=("Segoe UI", 11, "bold"),
                  bg="#1e40af", fg="white",
                  activebackground="#1e3a8a", activeforeground="white",
                  bd=0, cursor="hand2", padx=20, pady=12,
                  command=eliminar_prestamo).pack(fill="x", pady=5)

    def comprobante(self):
        messagebox.showinfo("Info",
                            "Haz clic en el botón Comprobante dentro de la tarjeta.")

    def comprobante_directo(self, prestamo):
        recibo = Recibo.obtener_o_crear(prestamo.id_prestamo)

        if recibo is None:
            messagebox.showwarning(
                "Aviso",
                "No se pudo registrar el recibo en la base de datos.\n\n"
                "Se generará el PDF igualmente, pero no quedará constancia.")

        w = tk.Toplevel(self)
        w.title(f"Recibo #{prestamo.id_prestamo}")
        w.geometry("600x680")
        w.configure(bg="#f1f5f9")
        w.transient(self)
        w.grab_set()
        w.focus_force()
        w.resizable(False, False)
        quitar_boton_cerrar(w)

        id_recibo = recibo.id_recibo if recibo else None
        num_mostrar = (str(id_recibo).zfill(6) if id_recibo
                       else str(prestamo.id_prestamo).zfill(6))

        # ---------- Header azul claro ----------
        header = tk.Frame(w, bg="#1e40af", height=150)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Button(header, text="Cerrar",
                  font=("Segoe UI", 9, "bold"),
                  bg="#64748b", fg="white",
                  activebackground="#475569", activeforeground="white",
                  bd=0, cursor="hand2", padx=14, pady=6,
                  command=w.destroy).place(relx=1.0, rely=0.0,
                                           anchor="ne", x=-15, y=15)

        header_inner = tk.Frame(header, bg="#1e40af")
        header_inner.place(relx=0.5, rely=0.5, anchor="center")

        logo_frame = tk.Frame(header_inner, bg="#1e40af")
        logo_frame.pack(pady=(0, 8))

        ruta_logo = None
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            rutas = [
                os.path.join(base_dir, "logo_unai.png"),
                os.path.join(base_dir, "logo_unai.jpeg"),
                os.path.join(base_dir, "logo_unai.jpg"),
            ]
            ruta_logo = next((r for r in rutas if os.path.exists(r)), None)
        except Exception:
            pass

        if PIL_OK and ruta_logo:
            try:
                img = Image.open(ruta_logo).convert("RGBA")
                img.thumbnail((50, 50), Image.LANCZOS)
                logo_img = ImageTk.PhotoImage(img)

                lbl_logo = tk.Label(logo_frame, image=logo_img, bg="#1e40af")
                lbl_logo.image = logo_img
                lbl_logo.pack(side="left", padx=(0, 14))
            except Exception:
                tk.Label(logo_frame, text="Biblioteca",
                         font=("Segoe UI", 14, "bold"),
                         bg="#1e40af", fg="white"
                         ).pack(side="left", padx=(0, 12))
        else:
            tk.Label(logo_frame, text="Biblioteca",
                     font=("Segoe UI", 14, "bold"),
                     bg="#1e40af", fg="white"
                     ).pack(side="left", padx=(0, 12))

        tk.Label(logo_frame, text="BIBLIOTECA UNI",
                 font=("Segoe UI", 20, "bold"),
                 bg="#1e40af", fg="white").pack(side="left")

        tk.Label(header_inner, text="Sistema de Gestión Bibliotecaria",
                 font=("Segoe UI", 9),
                 bg="#1e40af", fg="#bfdbfe").pack(pady=(0, 12))

        tk.Label(header_inner,
                 text=f"RECIBO N° {num_mostrar}",
                 font=("Segoe UI", 14, "bold"),
                 bg="#1e40af", fg="white").pack(pady=(6, 0))

        # ---------- Cuerpo del recibo ----------
        body = tk.Frame(w, bg="#f1f5f9")
        body.pack(fill="both", expand=True, padx=20, pady=15)

        info_fecha = tk.Frame(body, bg="#f1f5f9")
        info_fecha.pack(fill="x", pady=(0, 10))

        ahora = datetime.now()
        tk.Label(info_fecha,
                 text=f"Emitido: {ahora.strftime('%d/%m/%Y %H:%M')}",
                 font=("Segoe UI", 9),
                 bg="#f1f5f9", fg="#64748b").pack(side="right")

        if recibo:
            tk.Label(info_fecha,
                     text=f"Recibo N° {num_mostrar} registrado",
                     font=("Segoe UI", 9, "italic"),
                     bg="#f1f5f9", fg="#10b981").pack(side="left")

        card_user = tk.Frame(body, bg="white", highlightthickness=1,
                             highlightbackground="#e2e8f0")
        card_user.pack(fill="x", pady=(0, 12))

        tk.Frame(card_user, bg="#1e40af", height=4).pack(fill="x")

        inner_user = tk.Frame(card_user, bg="white", padx=22, pady=16)
        inner_user.pack(fill="x")

        tk.Label(inner_user, text="DATOS DEL USUARIO",
                 font=("Segoe UI", 10, "bold"),
                 bg="white", fg="#1e40af").pack(anchor="w", pady=(0, 12))

        def fila_dato(parent, label, valor):
            f = tk.Frame(parent, bg="white")
            f.pack(fill="x", pady=4)

            tk.Label(f, text=label,
                     font=("Segoe UI", 10),
                     bg="white", fg="#64748b",
                     width=20, anchor="w").pack(side="left")

            tk.Label(f, text=str(valor) if valor else "—",
                     font=("Segoe UI", 10, "bold"),
                     bg="white", fg="#0f172a",
                     anchor="w").pack(side="left")

        fila_dato(inner_user, "Usuario:", prestamo.nombre_usuario)
        fila_dato(inner_user, "ID Préstamo:", f"#{prestamo.id_prestamo}")
        if recibo:
            fila_dato(inner_user, "ID Recibo:", f"#{recibo.id_recibo}")

        card_det = tk.Frame(body, bg="white", highlightthickness=1,
                            highlightbackground="#e2e8f0")
        card_det.pack(fill="x", pady=(0, 12))

        tk.Frame(card_det, bg="#1e40af", height=4).pack(fill="x")

        inner_det = tk.Frame(card_det, bg="white", padx=22, pady=16)
        inner_det.pack(fill="x")

        tk.Label(inner_det, text="DETALLES DEL PRÉSTAMO",
                 font=("Segoe UI", 10, "bold"),
                 bg="white", fg="#1e40af").pack(anchor="w", pady=(0, 12))

        fecha_sol = (str(prestamo.fecha_solicitud)[:10]
                     if prestamo.fecha_solicitud else "—")
        fecha_dev = (str(prestamo.fecha_devolucion_esperada)[:10]
                     if prestamo.fecha_devolucion_esperada else "—")

        fila_dato(inner_det, "Fecha de solicitud:", fecha_sol)
        fila_dato(inner_det, "Devolución esperada:", fecha_dev)

        fila_estado = tk.Frame(inner_det, bg="white")
        fila_estado.pack(fill="x", pady=4)

        tk.Label(fila_estado, text="Estado:",
                 font=("Segoe UI", 10),
                 bg="white", fg="#64748b",
                 width=20, anchor="w").pack(side="left")

        estado_txt = prestamo.estado_prestamo.capitalize()
        if prestamo.estado_prestamo == "activo":
            bg_est, fg_est = "#dbeafe", "#1e40af"
        elif prestamo.estado_prestamo == "devuelto":
            bg_est, fg_est = "#d1fae5", "#065f46"
        else:
            bg_est, fg_est = "#fee2e2", "#991b1b"

        tk.Label(fila_estado, text=f"  {estado_txt}  ",
                 font=("Segoe UI", 9, "bold"),
                 bg=bg_est, fg=fg_est,
                 padx=8, pady=3).pack(side="left")

        fila_dato(inner_det, "Ejemplares:", prestamo.ejemplares_count or 0)

        tk.Button(body, text="Imprimir Recibo",
                  font=("Segoe UI", 11, "bold"),
                  bg="#64748b", fg="white",
                  activebackground="#475569", activeforeground="white",
                  bd=0, cursor="hand2", padx=30, pady=10,
                  command=lambda: imprimir_pdf()).pack(pady=(5, 0))

        def imprimir_pdf():
            try:
                from reportlab.lib.pagesizes import letter
                from reportlab.pdfgen import canvas as pdf_canvas
                from reportlab.lib.utils import ImageReader
                from reportlab.lib.colors import HexColor
                from auth_manager import obtener_ruta_logo

                carpeta = os.path.join(os.path.expanduser("~"),
                                       "Documents", "FacturasBiblioteca")
                os.makedirs(carpeta, exist_ok=True)

                nombre_archivo = f"Recibo_{num_mostrar}.pdf"
                ruta_pdf = os.path.join(carpeta, nombre_archivo)

                c = pdf_canvas.Canvas(ruta_pdf, pagesize=letter)
                ancho, alto = letter
                ahora2 = datetime.now()

                c.setFillColor(HexColor("#1e40af"))
                c.rect(0, alto - 130, ancho, 130, fill=True, stroke=False)

                c.setFillColor(HexColor("#1e3a8a"))
                c.rect(0, alto - 140, ancho, 10, fill=True, stroke=False)

                x_texto = 50
                ruta_logo = obtener_ruta_logo()
                if ruta_logo:
                    try:
                        logo = ImageReader(ruta_logo)
                        c.drawImage(logo, 50, alto - 105, width=80, height=80,
                                    preserveAspectRatio=True, mask='auto')
                        x_texto = 150
                    except Exception:
                        pass

                c.setFillColor(HexColor("#ffffff"))
                c.setFont("Helvetica-Bold", 24)
                c.drawString(x_texto, alto - 55, "BIBLIOTECA UNI")

                c.setFillColor(HexColor("#bfdbfe"))
                c.setFont("Helvetica", 10)
                c.drawString(x_texto, alto - 75, "Sistema de Gestión Bibliotecaria")

                c.setFillColor(HexColor("#ffffff"))
                c.setFont("Helvetica-Bold", 14)
                c.drawString(x_texto, alto - 105, f"RECIBO N° {num_mostrar}")

                c.setFillColor(HexColor("#cbd5e1"))
                c.setFont("Helvetica", 9)
                c.drawRightString(ancho - 50, alto - 55,
                                  f"Emitido: {ahora2.strftime('%d/%m/%Y %H:%M')}")
                if recibo and recibo.fecha_emision:
                    c.drawRightString(ancho - 50, alto - 70,
                                      f"Registrado: {recibo.fecha_emision[:19]}")

                y = alto - 180

                c.setFillColor(HexColor("#1e40af"))
                c.rect(50, y, ancho - 100, 4, fill=True, stroke=False)

                c.setFillColor(HexColor("#ffffff"))
                c.rect(50, y - 130, ancho - 100, 130, fill=True, stroke=False)
                c.setStrokeColor(HexColor("#e2e8f0"))
                c.setLineWidth(1)
                c.rect(50, y - 130, ancho - 100, 130, fill=False, stroke=True)

                c.setFillColor(HexColor("#1e40af"))
                c.setFont("Helvetica-Bold", 11)
                c.drawString(70, y - 20, "DATOS DEL USUARIO")

                c.setStrokeColor(HexColor("#e2e8f0"))
                c.line(70, y - 28, ancho - 70, y - 28)

                c.setFillColor(HexColor("#64748b"))
                c.setFont("Helvetica", 10)
                c.drawString(70, y - 55, "Usuario:")
                c.drawString(70, y - 80, "ID Préstamo:")
                if recibo:
                    c.drawString(70, y - 105, "ID Recibo:")

                c.setFillColor(HexColor("#0f172a"))
                c.setFont("Helvetica-Bold", 10)
                c.drawString(220, y - 55, prestamo.nombre_usuario or "—")
                c.drawString(220, y - 80, f"#{prestamo.id_prestamo}")
                if recibo:
                    c.drawString(220, y - 105, f"#{recibo.id_recibo}")

                y -= 160

                c.setFillColor(HexColor("#1e40af"))
                c.rect(50, y, ancho - 100, 4, fill=True, stroke=False)

                c.setFillColor(HexColor("#ffffff"))
                c.rect(50, y - 180, ancho - 100, 180, fill=True, stroke=False)
                c.setStrokeColor(HexColor("#e2e8f0"))
                c.rect(50, y - 180, ancho - 100, 180, fill=False, stroke=True)

                c.setFillColor(HexColor("#1e40af"))
                c.setFont("Helvetica-Bold", 11)
                c.drawString(70, y - 20, "DETALLES DEL PRÉSTAMO")

                c.setStrokeColor(HexColor("#e2e8f0"))
                c.line(70, y - 28, ancho - 70, y - 28)

                c.setFillColor(HexColor("#64748b"))
                c.setFont("Helvetica", 10)
                c.drawString(70, y - 55, "Fecha de solicitud:")
                c.drawString(70, y - 80, "Devolución esperada:")
                c.drawString(70, y - 105, "Estado:")
                c.drawString(70, y - 130, "Ejemplares:")

                c.setFillColor(HexColor("#0f172a"))
                c.setFont("Helvetica-Bold", 10)
                c.drawString(220, y - 55, fecha_sol)
                c.drawString(220, y - 80, fecha_dev)
                c.drawString(220, y - 105, estado_txt)
                c.drawString(220, y - 130, str(prestamo.ejemplares_count or 0))

                c.setFillColor(HexColor("#94a3b8"))
                c.setFont("Helvetica", 8)
                c.drawCentredString(ancho / 2, 50,
                                    "Gracias por utilizar el Sistema de Biblioteca UNI")

                c.save()

                try:
                    os.startfile(ruta_pdf)
                    messagebox.showinfo("PDF generado",
                                        f"Recibo generado correctamente:\n\n{ruta_pdf}",
                                        parent=w)
                except Exception:
                    messagebox.showinfo("PDF generado",
                                        f"Recibo guardado en:\n\n{ruta_pdf}",
                                        parent=w)
            except ImportError:
                messagebox.showerror("Error",
                                     "Falta instalar 'reportlab':\n\npip install reportlab",
                                     parent=w)
            except Exception as e:
                messagebox.showerror("Error",
                                     f"No se pudo generar el PDF:\n\n{e}",
                                     parent=w)

    def historial(self):
        w = tk.Toplevel(self)
        w.title("Historial de Préstamos")
        w.geometry("1200x680")
        w.configure(bg="#f1f5f9")
        w.transient(self)
        w.grab_set()
        w.focus_force()
        quitar_boton_cerrar(w)

        es_admin = self.auth.es_admin()
        estado_actual = {"ver_papelera": False}

        header = tk.Frame(w, bg="#334155", height=90)
        header.pack(fill="x")
        header.pack_propagate(False)

        titulo_frame = tk.Frame(header, bg="#334155")
        titulo_frame.pack(side="left", padx=30, pady=15)

        titulo = "Historial de Préstamos" if es_admin else "Mi Historial"

        tk.Label(titulo_frame, text=titulo,
                 font=("Segoe UI", 20, "bold"),
                 bg="#334155", fg="#f8fafc").pack(anchor="w")

        lbl_subtitulo = tk.Label(
            titulo_frame,
            text="Todos los préstamos del sistema" if es_admin else "Tus préstamos registrados",
            font=("Segoe UI", 10), bg="#334155", fg="#cbd5e1")
        lbl_subtitulo.pack(anchor="w", pady=(2, 0))

        tk.Button(header, text="Cerrar",
                  font=("Segoe UI", 11, "bold"),
                  bg="#ef4444", fg="white",
                  activebackground="#dc2626", activeforeground="white",
                  bd=0, cursor="hand2", padx=25, pady=10,
                  command=w.destroy).pack(side="right", padx=30, pady=25)

        def imprimir_historial():
            en_papelera = estado_actual["ver_papelera"]
            try:
                if en_papelera:
                    prestamos = Prestamo.obtener_eliminados()
                else:
                    prestamos = Prestamo.obtener_historial()
                u_actual = self.auth.get_usuario_actual()
                if not es_admin and u_actual:
                    prestamos = [p for p in prestamos
                                 if p.nombre_usuario == u_actual.usuario_login]
            except Exception:
                prestamos = []

            if not prestamos:
                messagebox.showwarning("Sin datos",
                                       "No hay préstamos para imprimir.",
                                       parent=w)
                return

            try:
                columnas = ["ID", "Usuario", "Solicitud", "Devolución",
                            "Estado", "Ejemplares"]
                filas = []
                activos = devueltos = vencidos = 0
                hoy = datetime.now().date()

                for p in prestamos:
                    estado_texto = p.estado_prestamo.capitalize()
                    if (p.estado_prestamo == "activo"
                            and p.fecha_devolucion_esperada):
                        try:
                            fecha_dev = datetime.strptime(
                                str(p.fecha_devolucion_esperada)[:10],
                                "%Y-%m-%d").date()
                            if fecha_dev < hoy:
                                estado_texto = "VENCIDO"
                                vencidos += 1
                        except Exception:
                            pass

                    filas.append([
                        p.id_prestamo,
                        p.nombre_usuario or "—",
                        str(p.fecha_solicitud)[:10] if p.fecha_solicitud else "—",
                        str(p.fecha_devolucion_esperada)[:10] if p.fecha_devolucion_esperada else "—",
                        estado_texto,
                        p.ejemplares_count or 0,
                    ])

                    if p.estado_prestamo == "activo":
                        activos += 1
                    else:
                        devueltos += 1

                titulo_rep = ("HISTORIAL DE PRÉSTAMOS (PAPELERA)"
                              if en_papelera else "HISTORIAL DE PRÉSTAMOS")

                resumen = [
                    ("Total de préstamos", len(filas)),
                    ("Activos", activos),
                    ("Devueltos", devueltos),
                ]
                if vencidos > 0:
                    resumen.append(("Vencidos", vencidos))

                fecha_str = datetime.now().strftime("%Y%m%d_%H%M%S")
                ruta_pdf = generar_pdf_reporte(
                    titulo_reporte=titulo_rep,
                    columnas=columnas,
                    filas=filas,
                    resumen=resumen,
                    nombre_archivo=f"Historial_Prestamos_{fecha_str}.pdf"
                )

                try:
                    os.startfile(ruta_pdf)
                    messagebox.showinfo("PDF generado",
                                        f"Historial exportado:\n\n{ruta_pdf}",
                                        parent=w)
                except Exception:
                    messagebox.showinfo("PDF generado",
                                        f"Historial guardado en:\n\n{ruta_pdf}",
                                        parent=w)
            except ImportError as e:
                messagebox.showerror("Error", str(e), parent=w)
            except Exception as e:
                messagebox.showerror("Error",
                                     f"No se pudo generar el PDF:\n\n{e}",
                                     parent=w)

        tk.Button(header, text="Imprimir",
                  font=("Segoe UI", 11, "bold"),
                  bg="#8b5cf6", fg="white",
                  activebackground="#7c3aed", activeforeground="white",
                  bd=0, cursor="hand2", padx=20, pady=10,
                  command=imprimir_historial).pack(side="right", padx=(0, 10), pady=25)

        btn_papelera = btn_limpiar = btn_restaurar = btn_eliminar_def = None

        if es_admin:
            btn_papelera = tk.Button(
                header, text="Papelera",
                font=("Segoe UI", 11, "bold"),
                bg="#64748b", fg="white",
                activebackground="#475569", activeforeground="white",
                bd=0, cursor="hand2", padx=20, pady=10)
            btn_papelera.pack(side="right", padx=(0, 10), pady=25)

            btn_limpiar = tk.Button(
                header, text="Limpiar",
                font=("Segoe UI", 11, "bold"),
                bg="#f59e0b", fg="white",
                activebackground="#d97706", activeforeground="white",
                bd=0, cursor="hand2", padx=20, pady=10)
            btn_limpiar.pack(side="right", padx=(0, 10), pady=25)

            btn_restaurar = tk.Button(
                header, text="Restaurar Todo",
                font=("Segoe UI", 11, "bold"),
                bg="#10b981", fg="white",
                activebackground="#059669", activeforeground="white",
                bd=0, cursor="hand2", padx=20, pady=10)

            btn_eliminar_def = tk.Button(
                header, text="Eliminar Definitivo",
                font=("Segoe UI", 11, "bold"),
                bg="#dc2626", fg="white",
                activebackground="#b91c1c", activeforeground="white",
                bd=0, cursor="hand2", padx=20, pady=10)

        cuerpo = tk.Frame(w, bg="#f1f5f9")
        cuerpo.pack(fill="both", expand=True)

        def renderizar():
            for child in cuerpo.winfo_children():
                child.destroy()

            en_papelera = estado_actual["ver_papelera"]

            try:
                if en_papelera:
                    prestamos = Prestamo.obtener_eliminados()
                else:
                    prestamos = Prestamo.obtener_historial()
                u_actual = self.auth.get_usuario_actual()
                if not es_admin and u_actual:
                    prestamos = [p for p in prestamos
                                 if p.nombre_usuario == u_actual.usuario_login]
            except Exception:
                prestamos = []

            total = len(prestamos)
            activos = sum(1 for p in prestamos if p.estado_prestamo == "activo")
            devueltos = sum(1 for p in prestamos if p.estado_prestamo == "devuelto")

            if en_papelera:
                lbl_subtitulo.config(
                    text="Préstamos en papelera (no visibles en el historial)")
            else:
                lbl_subtitulo.config(
                    text=("Todos los préstamos del sistema" if es_admin
                          else "Tus préstamos registrados"))

            if es_admin:
                if en_papelera:
                    btn_papelera.config(text="Volver", bg="#64748b",
                                        activebackground="#475569")
                    btn_limpiar.pack_forget()
                    if not btn_restaurar.winfo_ismapped():
                        btn_restaurar.pack(side="right", padx=(0, 10),
                                           pady=25, before=btn_papelera)
                    if not btn_eliminar_def.winfo_ismapped():
                        btn_eliminar_def.pack(side="right", padx=(0, 10),
                                              pady=25, before=btn_restaurar)
                    btn_restaurar.config(
                        command=lambda: self._restaurar_todo_historial(
                            w, estado_actual, renderizar))
                    btn_eliminar_def.config(
                        command=lambda: self._eliminar_definitivo_todo(
                            w, renderizar))
                else:
                    btn_papelera.config(text="Papelera", bg="#64748b",
                                        activebackground="#475569")
                    btn_restaurar.pack_forget()
                    btn_eliminar_def.pack_forget()
                    if not btn_limpiar.winfo_ismapped():
                        btn_limpiar.pack(side="right", padx=(0, 10),
                                         pady=25, before=btn_papelera)

            cards = tk.Frame(cuerpo, bg="#f1f5f9")
            cards.pack(fill="x", padx=25, pady=(20, 15))
            for i in range(3):
                cards.grid_columnconfigure(i, weight=1)

            self._crear_card_historial(cards, "Total", total, "#3b82f6", 0)
            self._crear_card_historial(cards, "Activos", activos, "#1e293b", 1)
            self._crear_card_historial(cards, "Devueltos", devueltos, "#10b981", 2)

            buscar_frame = tk.Frame(cuerpo, bg="white", highlightthickness=1,
                                    highlightbackground="#e2e8f0")
            buscar_frame.pack(fill="x", padx=25, pady=(0, 15))

            tk.Label(buscar_frame, text="Buscar por usuario:",
                     font=("Segoe UI", 10, "bold"),
                     bg="white", fg="#334155").pack(side="left", padx=(20, 10))

            entry_buscar = ttk.Entry(buscar_frame, width=40, font=("Segoe UI", 10))
            entry_buscar.pack(side="left", padx=5, pady=15)

            tabla_frame = tk.Frame(cuerpo, bg="white", highlightthickness=1,
                                   highlightbackground="#e2e8f0")
            tabla_frame.pack(fill="both", expand=True, padx=25, pady=(0, 20))

            style = ttk.Style()
            style.theme_use("clam")

            style.configure("Historial.Treeview",
                            background="#ffffff",
                            foreground="#1e293b",
                            rowheight=35,
                            fieldbackground="#ffffff",
                            font=("Segoe UI", 10),
                            borderwidth=0)
            style.configure("Historial.Treeview.Heading",
                            background="#334155",
                            foreground="white",
                            font=("Segoe UI", 10, "bold"),
                            padding=10,
                            relief="flat")
            style.map("Historial.Treeview",
                      background=[("selected", "#bfdbfe")],
                      foreground=[("selected", "#0f172a")])

            columnas = ("ID", "Usuario", "Fecha Solicitud", "Devolución",
                        "Estado", "Ejemplares")
            tree = ttk.Treeview(tabla_frame, columns=columnas,
                                show="headings", style="Historial.Treeview")

            for col in columnas:
                tree.heading(col, text=col)
                tree.column(col, width=170, anchor="center")

            scroll = ttk.Scrollbar(tabla_frame, orient="vertical",
                                   command=tree.yview)
            tree.configure(yscrollcommand=scroll.set)

            tree.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
            scroll.pack(side="right", fill="y", padx=(0, 10), pady=10)

            tree.tag_configure("activo", foreground="#0f172a")
            tree.tag_configure("devuelto", foreground="#16a34a")
            tree.tag_configure("par", background="#ffffff")
            tree.tag_configure("impar", background="#f8fafc")

            def cargar_tabla(filtro=""):
                for item in tree.get_children():
                    tree.delete(item)

                filtro = filtro.strip().lower()
                contador = 0

                for p in prestamos:
                    usuario = str(p.nombre_usuario or "").lower()
                    if filtro and filtro not in usuario:
                        continue

                    tag_estado = ("activo" if p.estado_prestamo == "activo"
                                  else "devuelto")
                    tag_par = "par" if contador % 2 == 0 else "impar"

                    tree.insert("", "end", values=(
                        p.id_prestamo, p.nombre_usuario,
                        str(p.fecha_solicitud)[:10] if p.fecha_solicitud else "—",
                        str(p.fecha_devolucion_esperada)[:10] if p.fecha_devolucion_esperada else "—",
                        p.estado_prestamo.capitalize(), p.ejemplares_count),
                        tags=(tag_estado, tag_par))

                    contador += 1

            cargar_tabla()
            entry_buscar.bind("<Return>", lambda e: cargar_tabla(entry_buscar.get()))

            pie = tk.Frame(cuerpo, bg="#f1f5f9")
            pie.pack(fill="x", padx=25, pady=(0, 15))

            tk.Label(pie, text=f"Mostrando {len(prestamos)} préstamo(s)",
                     font=("Segoe UI", 9), bg="#f1f5f9",
                     fg="#64748b").pack(side="left")

            def toggle_papelera():
                estado_actual["ver_papelera"] = not estado_actual["ver_papelera"]
                renderizar()

            def abrir_limpiar():
                self._abrir_modal_limpiar(w, renderizar)

            if es_admin:
                btn_papelera.config(command=toggle_papelera)
                btn_limpiar.config(command=abrir_limpiar)

        renderizar()

    def _abrir_modal_limpiar(self, parent_window, callback_render):
        w = tk.Toplevel(parent_window)
        w.title("Limpiar Historial")
        w.geometry("580x540")
        w.configure(bg="#f1f5f9")
        w.transient(parent_window)
        w.grab_set()
        w.focus_force()
        quitar_boton_cerrar(w)

        header = tk.Frame(w, bg="#334155", height=70)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(header, text="Limpiar Historial",
                 font=("Segoe UI", 16, "bold"), bg="#334155",
                 fg="#f59e0b").pack(side="left", padx=25, pady=18)

        tk.Button(header, text="Cerrar",
                  font=("Segoe UI", 10, "bold"),
                  bg="#64748b", fg="white",
                  activebackground="#475569", activeforeground="white",
                  bd=0, cursor="hand2", padx=15, pady=6,
                  command=w.destroy).pack(side="right", padx=20, pady=15)

        body = tk.Frame(w, bg="white", padx=30, pady=25)
        body.pack(fill="both", expand=True, padx=15, pady=15)

        tk.Label(body, text="¿Qué préstamos deseas enviar a la papelera?",
                 font=("Segoe UI", 11, "bold"), bg="white",
                 fg="#0f172a", wraplength=480,
                 justify="left").pack(anchor="w", pady=(0, 15))

        tk.Label(body, text="Podrás restaurarlos después desde la papelera",
                 font=("Segoe UI", 9, "italic"), bg="white",
                 fg="#94a3b8", wraplength=480,
                 justify="left").pack(anchor="w", pady=(0, 20))

        def mover_devueltos():
            if not messagebox.askyesno("Confirmar",
                                       "¿Mover solo los préstamos DEVUELTOS "
                                       "a la papelera?\n\n"
                                       "Los activos se conservan.",
                                       parent=w):
                return
            ok, msg = Prestamo.mover_devueltos_a_papelera()
            if ok:
                messagebox.showinfo("Éxito", f"{msg}", parent=parent_window)
                w.destroy()
                callback_render()
            else:
                messagebox.showerror("Error", msg, parent=w)

        def mover_todo():
            if not messagebox.askyesno(
                    "Confirmar",
                    "¿Mover TODO el historial a la papelera?\n\n"
                    "Se moverán TODOS los préstamos (activos y devueltos).\n\n"
                    "Podrás restaurarlos, pero los ejemplares "
                    "prestados quedarán bloqueados hasta restaurar.",
                    icon="warning", parent=w):
                return
            ok, msg = Prestamo.mover_todo_a_papelera()
            if ok:
                messagebox.showinfo("Éxito", f"{msg}", parent=parent_window)
                w.destroy()
                callback_render()
            else:
                messagebox.showerror("Error", msg, parent=w)

        card1 = tk.Frame(body, bg="#f8fafc", highlightthickness=1,
                         highlightbackground="#e2e8f0", cursor="hand2")
        card1.pack(fill="x", pady=8)

        inner1 = tk.Frame(card1, bg="#f8fafc", padx=20, pady=18)
        inner1.pack(fill="x")

        tk.Label(inner1, text="Solo DEVUELTOS",
                 font=("Segoe UI", 12, "bold"), bg="#f8fafc",
                 fg="#1e40af").pack(anchor="w")

        tk.Label(inner1,
                 text="Mueve a la papelera solo los préstamos ya devueltos. "
                      "Los activos se conservan en el historial.",
                 font=("Segoe UI", 9), bg="#f8fafc",
                 fg="#64748b", justify="left",
                 wraplength=470).pack(anchor="w", pady=(6, 0))

        for widget in [card1, inner1] + list(inner1.winfo_children()):
            widget.bind("<Button-1>", lambda e: mover_devueltos())

        card2 = tk.Frame(body, bg="#fee2e2", highlightthickness=1,
                         highlightbackground="#fecaca", cursor="hand2")
        card2.pack(fill="x", pady=8)

        inner2 = tk.Frame(card2, bg="#fee2e2", padx=20, pady=18)
        inner2.pack(fill="x")

        tk.Label(inner2, text="TODO el historial",
                 font=("Segoe UI", 12, "bold"), bg="#fee2e2",
                 fg="#991b1b").pack(anchor="w")

        tk.Label(inner2,
                 text="Mueve TODOS los préstamos a la papelera. "
                      "Podrás restaurarlos después.",
                 font=("Segoe UI", 9), bg="#fee2e2",
                 fg="#7f1d1d", justify="left",
                 wraplength=470).pack(anchor="w", pady=(6, 0))

        for widget in [card2, inner2] + list(inner2.winfo_children()):
            widget.bind("<Button-1>", lambda e: mover_todo())

    def _restaurar_todo_historial(self, parent_window, estado_actual, callback_render):
        if not messagebox.askyesno("Confirmar",
                                   "¿Restaurar TODOS los préstamos de la papelera?",
                                   parent=parent_window):
            return
        ok, msg = Prestamo.restaurar_todo()
        if ok:
            estado_actual["ver_papelera"] = False
            messagebox.showinfo("Éxito", f"{msg}", parent=parent_window)
            callback_render()
        else:
            messagebox.showerror("Error", msg, parent=parent_window)

    def _eliminar_definitivo_todo(self, parent_window, callback_render):
        if not messagebox.askyesno(
                "Eliminar definitivamente",
                "¿Eliminar PERMANENTEMENTE todos los préstamos de la papelera?\n\n"
                "Esta acción NO se puede deshacer.",
                icon="warning", parent=parent_window):
            return
        ok, msg = Prestamo.eliminar_definitivo_todo()
        if ok:
            messagebox.showinfo("Éxito", f"{msg}", parent=parent_window)
            callback_render()
        else:
            messagebox.showerror("Error", msg, parent=parent_window)

    def _crear_card_historial(self, parent, titulo, valor, color, col):
        card = tk.Frame(parent, bg="white", highlightthickness=1,
                        highlightbackground="#e2e8f0")
        card.grid(row=0, column=col, padx=6, pady=6, sticky="nsew")

        tk.Frame(card, bg=color, height=4).pack(fill="x")

        inner = tk.Frame(card, bg="white")
        inner.pack(fill="both", expand=True, padx=18, pady=12)

        tk.Label(inner, text=titulo, font=("Segoe UI", 9),
                 bg="white", fg="#64748b").pack(anchor="w")

        tk.Label(inner, text=str(valor),
                 font=("Segoe UI", 20, "bold"),
                 bg="white", fg=color).pack(anchor="w", pady=(2, 0))