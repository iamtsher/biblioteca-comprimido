import os
from datetime import datetime

import tkinter as tk
from tkinter import ttk, messagebox

from models import Ejemplar, Libro
from auth_manager import AuthManager, quitar_boton_cerrar, generar_pdf_reporte


class EjemplaresView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="#f1f5f9")
        self.auth = AuthManager()
        self._ejemplares_actuales = []
        self._build_ui()

    def on_show(self):
        self.cargar_ejemplares()

    def _build_ui(self):
        header = tk.Frame(self, bg="#f1f5f9", height=55)
        header.pack(fill="x", padx=25, pady=(12, 0))
        header.pack_propagate(False)

        if self.auth.es_admin():
            tk.Button(header, text="＋  Agregar Ejemplar",
                      font=("Segoe UI", 11, "bold"),
                      bg="#38bdf8", fg="#0f172a",
                      activebackground="#0ea5e9", activeforeground="white",
                      bd=0, cursor="hand2", padx=20, pady=8,
                      command=self.abrir_form).pack(side="right", pady=8)

        tk.Button(header, text="📄  Imprimir",
                  font=("Segoe UI", 11, "bold"),
                  bg="#8b5cf6", fg="white",
                  activebackground="#7c3aed", activeforeground="white",
                  bd=0, cursor="hand2", padx=20, pady=8,
                  command=self.imprimir_ejemplares).pack(side="right", padx=(0, 10), pady=8)

        filtros = tk.Frame(self, bg="#f1f5f9")
        filtros.pack(fill="x", padx=25, pady=(10, 10))

        filtro_card = tk.Frame(filtros, bg="white", highlightthickness=1,
                               highlightbackground="#e2e8f0")
        filtro_card.pack(fill="x")

        tk.Label(filtro_card, text="🔍", font=("Segoe UI", 14),
                 bg="white", fg="#64748b").pack(side="left", padx=(20, 8))

        tk.Label(filtro_card, text="Buscar por libro:",
                 font=("Segoe UI", 10, "bold"),
                 bg="white", fg="#334155").pack(side="left", padx=(0, 10))

        self.entry_buscar = ttk.Entry(filtro_card, width=45, font=("Segoe UI", 10))
        self.entry_buscar.pack(side="left", padx=5, pady=15)
        self.entry_buscar.bind("<Return>", lambda e: self.filtrar_por_libro())

        tk.Button(filtro_card, text="Filtrar",
                  font=("Segoe UI", 10, "bold"),
                  bg="#1e293b", fg="white",
                  activebackground="#334155", activeforeground="white",
                  bd=0, cursor="hand2", padx=18, pady=8,
                  command=self.filtrar_por_libro).pack(side="left", padx=5)

        tk.Button(filtro_card, text="Mostrar Todos",
                  font=("Segoe UI", 10),
                  bg="#e2e8f0", fg="#1e293b",
                  activebackground="#cbd5e1",
                  bd=0, cursor="hand2", padx=18, pady=8,
                  command=self.cargar_ejemplares).pack(side="left", padx=5)

        self.lbl_total = tk.Label(self, text="",
                                  font=("Segoe UI", 10, "bold"),
                                  bg="#f1f5f9", fg="#475569")
        self.lbl_total.pack(anchor="w", padx=30, pady=(5, 8))

        container_outer = tk.Frame(self, bg="#f1f5f9")
        container_outer.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self.canvas = tk.Canvas(container_outer, bg="#f1f5f9", highlightthickness=0)
        scroll = tk.Scrollbar(container_outer, orient="vertical",
                              command=self.canvas.yview)
        self.frame_ejemplares = tk.Frame(self.canvas, bg="#f1f5f9")

        self.canvas_window = self.canvas.create_window(
            (0, 0), window=self.frame_ejemplares, anchor="nw")
        self.canvas.configure(yscrollcommand=scroll.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        self.frame_ejemplares.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width))

        for i in range(3):
            self.frame_ejemplares.grid_columnconfigure(i, weight=1, uniform="col")

        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_mousewheel(self, event):
        try:
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        except Exception:
            pass

    def _limpiar_tarjetas(self):
        for w in self.frame_ejemplares.winfo_children():
            w.destroy()

    def _crear_tarjeta(self, parent, ejemplar, fila, columna):
        es_admin = self.auth.es_admin()

        if ejemplar.estado == "Disponible":
            color_estado, bg_estado, fg_estado, icono_estado = (
                "#10b981", "#d1fae5", "#065f46", "✅")
        elif ejemplar.estado == "Prestado":
            color_estado, bg_estado, fg_estado, icono_estado = (
                "#f59e0b", "#fed7aa", "#9a3412", "🔄")
        else:
            color_estado, bg_estado, fg_estado, icono_estado = (
                "#ef4444", "#fee2e2", "#991b1b", "❌")

        card = tk.Frame(parent, bg="white", highlightthickness=1,
                        highlightbackground="#e2e8f0")
        card.grid(row=fila, column=columna, padx=8, pady=8, sticky="nsew")

        tk.Frame(card, bg=color_estado, height=4).pack(fill="x")

        inner = tk.Frame(card, bg="white")
        inner.pack(fill="both", expand=True, padx=18, pady=15)

        top = tk.Frame(inner, bg="white")
        top.pack(fill="x")

        icono_frame = tk.Frame(top, bg=color_estado, width=44, height=44)
        icono_frame.pack(side="left")
        icono_frame.pack_propagate(False)

        tk.Label(icono_frame, text="📦",
                 font=("Segoe UI Emoji", 18),
                 bg=color_estado, fg="white").pack(expand=True)

        info_top = tk.Frame(top, bg="white")
        info_top.pack(side="left", padx=(12, 0), fill="x", expand=True)

        tk.Label(info_top, text=f"#{ejemplar.id_ejemplar}",
                 font=("Segoe UI", 14, "bold"),
                 bg="white", fg="#0f172a").pack(anchor="w")

        tk.Label(info_top, text=f"ID Libro: {ejemplar.id_libro}",
                 font=("Segoe UI", 9),
                 bg="white", fg="#64748b").pack(anchor="w")

        tk.Frame(inner, bg="#e2e8f0", height=1).pack(fill="x", pady=12)

        titulo = ejemplar.titulo_libro or "Sin título"
        if len(titulo) > 35:
            titulo = titulo[:35] + "…"

        tk.Label(inner, text=f"📖 {titulo}",
                 font=("Segoe UI", 11, "bold"),
                 bg="white", fg="#0f172a",
                 anchor="w", justify="left",
                 wraplength=250).pack(anchor="w")

        badge_frame = tk.Frame(inner, bg="white")
        badge_frame.pack(fill="x", pady=(12, 0))

        tk.Label(badge_frame,
                 text=f"  {icono_estado}  {ejemplar.estado}  ",
                 font=("Segoe UI", 10, "bold"),
                 bg=bg_estado, fg=fg_estado,
                 padx=10, pady=5).pack(side="left")

        botones = tk.Frame(inner, bg="white")
        botones.pack(fill="x", pady=(12, 0))

        if es_admin:
            tk.Button(botones, text="🔄  Cambiar Estado",
                      font=("Segoe UI", 9, "bold"),
                      bg="#dbeafe", fg="#1e40af",
                      activebackground="#bfdbfe", activeforeground="#1e40af",
                      bd=0, cursor="hand2", padx=10, pady=6,
                      command=lambda e=ejemplar: self.cambiar_estado(e)
                      ).pack(side="left", padx=2)

            tk.Button(botones, text="🗑️",
                      font=("Segoe UI Emoji", 10),
                      bg="#fee2e2", fg="#991b1b",
                      activebackground="#fecaca", activeforeground="#991b1b",
                      bd=0, cursor="hand2", padx=10, pady=6,
                      command=lambda e=ejemplar: self.eliminar(e)
                      ).pack(side="right", padx=2)
        else:
            tk.Button(botones, text="👁️  Ver detalles",
                      font=("Segoe UI", 9),
                      bg="#e2e8f0", fg="#334155",
                      activebackground="#cbd5e1",
                      bd=0, cursor="hand2", padx=10, pady=6).pack(side="left")

    def cargar_ejemplares(self):
        self.entry_buscar.delete(0, tk.END)
        self._limpiar_tarjetas()

        try:
            ejemplares = Ejemplar.obtener_todos(limit=5000)
            self._ejemplares_actuales = ejemplares

            for i, ejemplar in enumerate(ejemplares):
                self._crear_tarjeta(self.frame_ejemplares, ejemplar,
                                    i // 3, i % 3)

            total = Ejemplar.contar()
            self.lbl_total.config(text=f"📦  {total:,} ejemplares registrados")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar:\n\n{e}")

    def filtrar_por_libro(self):
        texto = self.entry_buscar.get().strip().lower()
        if not texto:
            self.cargar_ejemplares()
            return

        self._limpiar_tarjetas()

        try:
            todos = Ejemplar.obtener_todos(limit=5000)
            filtrados = [e for e in todos
                         if texto in (e.titulo_libro or "").lower()]
            self._ejemplares_actuales = filtrados

            for i, ejemplar in enumerate(filtrados):
                self._crear_tarjeta(self.frame_ejemplares, ejemplar,
                                    i // 3, i % 3)

            self.lbl_total.config(
                text=f"🔎  {len(filtrados)} ejemplar(es) encontrado(s)")

            if not filtrados:
                tk.Label(self.frame_ejemplares,
                         text="🔎 No se encontraron ejemplares",
                         font=("Segoe UI", 12),
                         bg="#f1f5f9", fg="#94a3b8").pack(pady=40)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo filtrar:\n\n{e}")

    def imprimir_ejemplares(self):
        if not self._ejemplares_actuales:
            messagebox.showwarning("Sin datos",
                                   "No hay ejemplares para imprimir.\n\n"
                                   "Carga algunos ejemplares primero.")
            return

        try:
            columnas = ["ID", "Libro", "Estado"]
            filas = []
            disponibles = prestados = perdidos = 0

            for ejemplar in self._ejemplares_actuales:
                filas.append([
                    ejemplar.id_ejemplar,
                    ejemplar.titulo_libro or "Sin título",
                    ejemplar.estado
                ])

                if ejemplar.estado == "Disponible":
                    disponibles += 1
                elif ejemplar.estado == "Prestado":
                    prestados += 1
                elif ejemplar.estado == "Perdido":
                    perdidos += 1

            resumen = [
                ("Total de ejemplares", len(filas)),
                ("Disponibles", disponibles),
                ("Prestados", prestados),
                ("Perdidos", perdidos),
            ]

            fecha_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            ruta_pdf = generar_pdf_reporte(
                titulo_reporte="REPORTE DE EJEMPLARES",
                columnas=columnas,
                filas=filas,
                resumen=resumen,
                nombre_archivo=f"Reporte_Ejemplares_{fecha_str}.pdf"
            )

            try:
                os.startfile(ruta_pdf)
                messagebox.showinfo("PDF generado",
                                    f"✅ Reporte generado correctamente:\n\n{ruta_pdf}")
            except Exception:
                messagebox.showinfo("PDF generado",
                                    f"✅ Reporte guardado en:\n\n{ruta_pdf}")
        except ImportError as e:
            messagebox.showerror("Error", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo generar el PDF:\n\n{e}")

    def abrir_form(self):
        if not self.auth.es_admin():
            messagebox.showwarning("Sin permisos",
                                   "Solo administradores pueden agregar ejemplares.")
            return

        w = tk.Toplevel(self)
        w.title("Agregar Ejemplar")
        w.geometry("500x400")
        w.configure(bg="#f1f5f9")
        w.transient(self)
        w.grab_set()
        w.focus_force()
        quitar_boton_cerrar(w)

        header = tk.Frame(w, bg="#0f172a", height=70)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(header, text="📦  Agregar Nuevo Ejemplar",
                 font=("Segoe UI", 16, "bold"), bg="#0f172a",
                 fg="#38bdf8").pack(side="left", padx=25, pady=18)

        tk.Button(header, text="✖  Cerrar",
                  font=("Segoe UI", 10, "bold"),
                  bg="#ef4444", fg="white",
                  activebackground="#dc2626", activeforeground="white",
                  bd=0, cursor="hand2", padx=15, pady=6,
                  command=w.destroy).pack(side="right", padx=20, pady=15)

        form = tk.Frame(w, bg="white", padx=30, pady=25)
        form.pack(fill="both", expand=True, padx=20, pady=15)

        tk.Label(form, text="📖 Libro:",
                 font=("Segoe UI", 10, "bold"),
                 bg="white", fg="#334155").pack(anchor="w", pady=(0, 5))

        combo = ttk.Combobox(form, width=45, state="readonly",
                             font=("Segoe UI", 10))
        libros = Libro.obtener_todos(limit=1000)
        combo["values"] = [f"{l.idLibro} - {l.Book_Title}" for l in libros]
        combo.pack(anchor="w", pady=(0, 20))

        tk.Label(form, text="🎫 Estado inicial:",
                 font=("Segoe UI", 10, "bold"),
                 bg="white", fg="#334155").pack(anchor="w", pady=(0, 5))

        combo_estado = ttk.Combobox(form, width=30, state="readonly",
                                    values=["Disponible", "Prestado", "Perdido"],
                                    font=("Segoe UI", 10))
        combo_estado.set("Disponible")
        combo_estado.pack(anchor="w", pady=(0, 20))

        def guardar():
            lsel = combo.get()
            if not lsel or " - " not in lsel:
                messagebox.showwarning("Campo requerido",
                                       "Selecciona un libro.", parent=w)
                return

            lid = int(lsel.split(" - ")[0])
            from database import get_connection
            conn = get_connection()
            cursor = conn.cursor()

            try:
                cursor.execute(
                    "SELECT ISNULL(MAX(id_ejemplar), 667382) FROM Ejemplar")
                next_id = cursor.fetchone()[0] + 1

                cursor.execute("""
                    INSERT INTO Ejemplar (id_ejemplar, id_libro, estado)
                    VALUES (?, ?, ?)
                """, (next_id, lid, combo_estado.get()))

                conn.commit()
                conn.close()

                w.destroy()
                self.cargar_ejemplares()
                messagebox.showinfo("Éxito", "✅ Ejemplar agregado correctamente.")
            except Exception as e:
                conn.close()
                messagebox.showerror("Error",
                                     f"No se pudo agregar:\n\n{e}",
                                     parent=w)

        tk.Button(w, text="💾 Guardar",
                  font=("Segoe UI", 11, "bold"),
                  bg="#38bdf8", fg="#0f172a",
                  activebackground="#0ea5e9", activeforeground="white",
                  bd=0, cursor="hand2", padx=25, pady=10,
                  command=guardar).pack(pady=15)

    def cambiar_estado(self, ejemplar):
        estados = ["Disponible", "Prestado", "Perdido"]

        w = tk.Toplevel(self)
        w.title(f"Cambiar Estado - #{ejemplar.id_ejemplar}")
        w.geometry("400x300")
        w.configure(bg="#f1f5f9")
        w.transient(self)
        w.grab_set()
        w.focus_force()
        quitar_boton_cerrar(w)

        header = tk.Frame(w, bg="#0f172a", height=65)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(header, text="🔄  Cambiar Estado",
                 font=("Segoe UI", 15, "bold"), bg="#0f172a",
                 fg="#38bdf8").pack(side="left", padx=25, pady=16)

        tk.Button(header, text="✖  Cerrar",
                  font=("Segoe UI", 10, "bold"),
                  bg="#ef4444", fg="white",
                  activebackground="#dc2626", activeforeground="white",
                  bd=0, cursor="hand2", padx=15, pady=6,
                  command=w.destroy).pack(side="right", padx=20, pady=14)

        form = tk.Frame(w, bg="white", padx=25, pady=20)
        form.pack(fill="both", expand=True, padx=15, pady=15)

        tk.Label(form, text=f"📦 Ejemplar #{ejemplar.id_ejemplar}",
                 font=("Segoe UI", 11, "bold"),
                 bg="white", fg="#0f172a").pack(anchor="w")

        tk.Label(form, text=f"📖 {ejemplar.titulo_libro}",
                 font=("Segoe UI", 10),
                 bg="white", fg="#64748b").pack(anchor="w", pady=(2, 15))

        tk.Label(form, text=f"Estado actual: {ejemplar.estado}",
                 font=("Segoe UI", 10, "bold"),
                 bg="white", fg="#334155").pack(anchor="w", pady=(0, 10))

        combo = ttk.Combobox(form, state="readonly", values=estados,
                             width=22, font=("Segoe UI", 10))
        combo.set(ejemplar.estado)
        combo.pack(anchor="w", pady=(0, 20))

        def guardar():
            ejemplar.cambiar_estado(combo.get())
            w.destroy()
            self.cargar_ejemplares()
            messagebox.showinfo("Éxito", "✅ Estado actualizado.")

        tk.Button(form, text="💾 Guardar",
                  font=("Segoe UI", 10, "bold"),
                  bg="#38bdf8", fg="#0f172a",
                  activebackground="#0ea5e9", activeforeground="white",
                  bd=0, cursor="hand2", padx=20, pady=8,
                  command=guardar).pack()

    def eliminar(self, ejemplar):
        if messagebox.askyesno("Confirmar eliminación",
                               f"¿Eliminar el ejemplar #{ejemplar.id_ejemplar}?\n\n"
                               f"📖 {ejemplar.titulo_libro}"):
            try:
                ejemplar.eliminar()
                self.cargar_ejemplares()
                messagebox.showinfo("Éxito", "🗑️ Ejemplar eliminado.")
            except Exception as e:
                messagebox.showerror("Error",
                                     f"No se pudo eliminar:\n\n{e}")