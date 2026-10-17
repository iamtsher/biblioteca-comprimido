import os
import io
import urllib.request
import threading
from datetime import datetime

import tkinter as tk
from tkinter import ttk, messagebox

from models import Libro, Ejemplar
from auth_manager import AuthManager, quitar_boton_cerrar, generar_pdf_reporte

try:
    from PIL import Image, ImageTk
    PIL_OK = True
except ImportError:
    PIL_OK = False


class LibrosView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="#f1f5f9")
        self.auth = AuthManager()
        self._cache_imagenes = {}
        self._libros_actuales = []
        self._build_ui()

    def on_show(self):
        self.cargar_libros()

    # ==========================================
    # UI
    # ==========================================
    def _build_ui(self):
        header = tk.Frame(self, bg="#f1f5f9", height=55)
        header.pack(fill="x", padx=25, pady=(12, 0))
        header.pack_propagate(False)

        es_admin = self.auth.es_admin()

        if es_admin:
            tk.Button(header, text="＋  Nuevo Libro",
                      font=("Segoe UI", 10, "bold"),
                      bg="#38bdf8", fg="#0f172a",
                      activebackground="#0ea5e9", activeforeground="white",
                      bd=0, cursor="hand2", padx=18, pady=8,
                      command=self.abrir_form).pack(side="right", pady=8)

        tk.Button(header, text="📄  Imprimir",
                  font=("Segoe UI", 10, "bold"),
                  bg="#8b5cf6", fg="white",
                  activebackground="#7c3aed", activeforeground="white",
                  bd=0, cursor="hand2", padx=18, pady=8,
                  command=self.imprimir_libros).pack(side="right", padx=(0, 10), pady=8)

        # Buscador
        search_container = tk.Frame(self, bg="#f1f5f9")
        search_container.pack(fill="x", padx=25, pady=(10, 10))

        search_card = tk.Frame(search_container, bg="white", highlightthickness=1,
                               highlightbackground="#e2e8f0")
        search_card.pack(fill="x")

        tk.Label(search_card, text="🔎", font=("Segoe UI", 14),
                 bg="white", fg="#64748b").pack(side="left", padx=(20, 8))

        self.entry_buscar = ttk.Entry(search_card, width=50, font=("Segoe UI", 10))
        self.entry_buscar.pack(side="left", padx=5, pady=15)
        self.entry_buscar.bind("<Return>", lambda e: self.buscar_libros())

        tk.Button(search_card, text="Buscar", font=("Segoe UI", 10, "bold"),
                  bg="#1e293b", fg="white", activebackground="#334155",
                  activeforeground="white", bd=0, cursor="hand2",
                  padx=18, pady=8, command=self.buscar_libros).pack(
            side="left", padx=5)

        tk.Button(search_card, text="Mostrar Todos", font=("Segoe UI", 10),
                  bg="#e2e8f0", fg="#1e293b", activebackground="#cbd5e1",
                  bd=0, cursor="hand2", padx=18, pady=8,
                  command=self.cargar_libros).pack(side="left", padx=5)

        self.lbl_total = tk.Label(self, text="", font=("Segoe UI", 10, "bold"),
                                  bg="#f1f5f9", fg="#475569")
        self.lbl_total.pack(anchor="w", padx=30, pady=(5, 8))

        # Contenedor scrollable
        container_outer = tk.Frame(self, bg="#f1f5f9")
        container_outer.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self.canvas = tk.Canvas(container_outer, bg="#f1f5f9", highlightthickness=0)
        scroll = tk.Scrollbar(container_outer, orient="vertical",
                              command=self.canvas.yview)
        self.frame_libros = tk.Frame(self.canvas, bg="#f1f5f9")

        self.canvas_window = self.canvas.create_window(
            (0, 0), window=self.frame_libros, anchor="nw")
        self.canvas.configure(yscrollcommand=scroll.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        self.frame_libros.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")))

        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width))

        self.frame_libros.grid_columnconfigure(0, weight=1, uniform="col")
        self.frame_libros.grid_columnconfigure(1, weight=1, uniform="col")

        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_mousewheel(self, event):
        try:
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        except Exception:
            pass

    # ==========================================
    # IMÁGENES
    # ==========================================
    def _cargar_imagen_url(self, url, size=(90, 130)):
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=4) as resp:
                data = resp.read()

            img = Image.open(io.BytesIO(data))

            if img.size[0] < 20 or img.size[1] < 20:
                return None

            img.thumbnail(size, Image.LANCZOS)

            fondo = Image.new("RGB", img.size, (241, 245, 249))
            if img.mode == "RGBA":
                fondo.paste(img, mask=img.split()[3])
            else:
                fondo.paste(img, (0, 0))

            return fondo
        except Exception:
            return None

    def _aplicar_imagen(self, label, img_pil):
        try:
            if not label.winfo_exists():
                return
            photo = ImageTk.PhotoImage(img_pil)
            label.config(image=photo, text="")
            label.image = photo
        except Exception:
            pass

    # ==========================================
    # TARJETAS
    # ==========================================
    def _limpiar_tarjetas(self):
        for w in self.frame_libros.winfo_children():
            w.destroy()

    def _crear_tarjeta(self, parent, libro, fila, columna):
        total, disponibles = libro.contar_ejemplares()
        es_admin = self.auth.es_admin()

        card = tk.Frame(parent, bg="white", highlightthickness=1,
                        highlightbackground="#e2e8f0")
        card.grid(row=fila, column=columna, padx=10, pady=8, sticky="nsew")

        inner = tk.Frame(card, bg="white")
        inner.pack(fill="both", expand=True, padx=15, pady=15)

        img_frame = tk.Frame(inner, bg="#f1f5f9", width=90, height=130,
                             highlightthickness=1, highlightbackground="#e2e8f0")
        img_frame.pack(side="left")
        img_frame.pack_propagate(False)

        lbl_img = tk.Label(img_frame, text="📖", font=("Segoe UI Emoji", 32),
                           bg="#f1f5f9", fg="#cbd5e1")
        lbl_img.pack(expand=True)

        if PIL_OK and libro.Image_URL_L:
            def cargar_en_thread():
                img_pil = self._cargar_imagen_url(libro.Image_URL_L)
                if img_pil:
                    try:
                        if lbl_img.winfo_exists():
                            self.after(0, lambda: self._aplicar_imagen(lbl_img, img_pil))
                    except Exception:
                        pass

            threading.Thread(target=cargar_en_thread, daemon=True).start()

        info = tk.Frame(inner, bg="white")
        info.pack(side="left", fill="both", expand=True, padx=(12, 0))

        titulo_txt = libro.Book_Title or "Sin título"
        if len(titulo_txt) > 30:
            titulo_txt = titulo_txt[:30] + "…"

        tk.Label(info, text=titulo_txt,
                 font=("Segoe UI", 12, "bold"), bg="white",
                 fg="#0f172a", anchor="w").pack(anchor="w")

        autor_txt = libro.Book_Author or "Autor desconocido"
        if len(autor_txt) > 25:
            autor_txt = autor_txt[:25] + "…"

        tk.Label(info, text=f"✍️  {autor_txt}",
                 font=("Segoe UI", 9), bg="white",
                 fg="#475569").pack(anchor="w", pady=(2, 0))

        tk.Frame(info, bg="#e2e8f0", height=1).pack(fill="x", pady=6)

        tk.Label(info, text=f"📅 {libro.Year_Of_Publication or '—'}",
                 font=("Segoe UI", 8), bg="white",
                 fg="#64748b", anchor="w").pack(anchor="w")

        if disponibles > 0:
            badge = tk.Label(info,
                             text=f"  ✅ {disponibles}/{total} disp.  ",
                             font=("Segoe UI", 8, "bold"),
                             bg="#d1fae5", fg="#065f46",
                             padx=6, pady=3)
        else:
            badge = tk.Label(info,
                             text="  ❌ Sin disponibles  ",
                             font=("Segoe UI", 8, "bold"),
                             bg="#fee2e2", fg="#991b1b",
                             padx=6, pady=3)
        badge.pack(anchor="w", pady=(6, 0))

        botones = tk.Frame(inner, bg="white")
        botones.pack(side="right", padx=(5, 0))

        tk.Button(botones, text="👁️", font=("Segoe UI Emoji", 9),
                  bg="#e2e8f0", fg="#0f172a", bd=0, cursor="hand2",
                  padx=6, pady=4, relief="flat",
                  command=lambda l=libro: self.ver_detalle_directo(l)
                  ).pack(pady=1)

        if es_admin:
            tk.Button(botones, text="✏️", font=("Segoe UI Emoji", 9),
                      bg="#e2e8f0", fg="#0f172a", bd=0, cursor="hand2",
                      padx=6, pady=4, relief="flat",
                      command=lambda l=libro: self.abrir_form(l)
                      ).pack(pady=1)

            tk.Button(botones, text="📦", font=("Segoe UI Emoji", 9),
                      bg="#dbeafe", fg="#1e40af", bd=0, cursor="hand2",
                      padx=6, pady=4, relief="flat",
                      command=lambda l=libro: self.gestionar_ejemplares(l)
                      ).pack(pady=1)

            tk.Button(botones, text="🗑️", font=("Segoe UI Emoji", 9),
                      bg="#fee2e2", fg="#991b1b", bd=0, cursor="hand2",
                      padx=6, pady=4, relief="flat",
                      command=lambda l=libro: self.eliminar_directo(l)
                      ).pack(pady=1)

    # ==========================================
    # CARGA / BÚSQUEDA
    # ==========================================
    def cargar_libros(self):
        self._limpiar_tarjetas()
        self.entry_buscar.delete(0, tk.END)

        try:
            libros = Libro.obtener_todos(limit=5000)
            self._libros_actuales = libros

            for i, libro in enumerate(libros):
                self._crear_tarjeta(self.frame_libros, libro, i // 2, i % 2)

            total = Libro.contar()
            self.lbl_total.config(text=f"📚  {total:,} libros registrados")
        except Exception as e:
            messagebox.showerror("Error",
                                 f"No se pudieron cargar los libros:\n\n{e}")

    def buscar_libros(self):
        texto = self.entry_buscar.get().strip()
        if not texto:
            self.cargar_libros()
            return

        self._limpiar_tarjetas()
        try:
            libros = Libro.buscar(texto)
            self._libros_actuales = libros

            for i, libro in enumerate(libros):
                self._crear_tarjeta(self.frame_libros, libro, i // 2, i % 2)

            self.lbl_total.config(text=f"🔎  {len(libros):,} resultado(s)")
        except Exception as e:
            messagebox.showerror("Error",
                                 f"No se pudo realizar la búsqueda:\n\n{e}")

    # ==========================================
    # IMPRIMIR
    # ==========================================
    def imprimir_libros(self):
        if not self._libros_actuales:
            messagebox.showwarning("Sin datos",
                                   "No hay libros para imprimir.\n\n"
                                   "Carga algunos libros primero.")
            return

        try:
            columnas = ["ID", "Título", "Autor", "Año", "Disponibles"]
            filas = []
            con_disponibles = 0
            sin_disponibles = 0

            for libro in self._libros_actuales:
                total, disponibles = libro.contar_ejemplares()
                if disponibles > 0:
                    con_disponibles += 1
                else:
                    sin_disponibles += 1

                filas.append([
                    libro.idLibro,
                    libro.Book_Title or "Sin título",
                    libro.Book_Author or "—",
                    libro.Year_Of_Publication or "—",
                    f"{disponibles}/{total}"
                ])

            resumen = [
                ("Total de libros", len(filas)),
                ("Con ejemplares disponibles", con_disponibles),
                ("Sin ejemplares disponibles", sin_disponibles),
            ]

            fecha_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            ruta_pdf = generar_pdf_reporte(
                titulo_reporte="REPORTE DE LIBROS",
                columnas=columnas,
                filas=filas,
                resumen=resumen,
                nombre_archivo=f"Reporte_Libros_{fecha_str}.pdf"
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
            messagebox.showerror("Error",
                                 f"No se pudo generar el PDF:\n\n{e}")

    # ==========================================
    # DETALLE DEL LIBRO
    # ==========================================
    def ver_detalle_directo(self, libro):
        w = tk.Toplevel(self)
        w.title(f"📖 {libro.Book_Title}")
        w.geometry("720x520")
        w.configure(bg="#f1f5f9")
        w.transient(self)
        w.grab_set()
        w.focus_force()
        quitar_boton_cerrar(w)

        header = tk.Frame(w, bg="#0f172a", height=80)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(header, text="📖  Detalle del Libro",
                 font=("Segoe UI", 18, "bold"), bg="#0f172a",
                 fg="#38bdf8").pack(side="left", padx=30, pady=20)

        tk.Button(header, text="✖  Cerrar",
                  font=("Segoe UI", 11, "bold"),
                  bg="#ef4444", fg="white",
                  activebackground="#dc2626", activeforeground="white",
                  bd=0, cursor="hand2", padx=20, pady=8,
                  command=w.destroy).pack(side="right", padx=30, pady=20)

        body = tk.Frame(w, bg="white", padx=25, pady=25)
        body.pack(fill="both", expand=True, padx=15, pady=15)

        left = tk.Frame(body, bg="white", width=250)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)

        img_frame = tk.Frame(left, bg="#f1f5f9", width=220, height=320,
                             highlightthickness=1, highlightbackground="#e2e8f0")
        img_frame.pack(pady=(0, 15))
        img_frame.pack_propagate(False)

        lbl_img = tk.Label(img_frame, text="📖", font=("Segoe UI Emoji", 80),
                           bg="#f1f5f9", fg="#cbd5e1")
        lbl_img.pack(expand=True)

        if PIL_OK and libro.Image_URL_L:
            def cargar_en_thread():
                img_pil = self._cargar_imagen_url(libro.Image_URL_L, size=(220, 320))
                if img_pil:
                    try:
                        if lbl_img.winfo_exists():
                            self.after(0, lambda: self._aplicar_imagen(lbl_img, img_pil))
                    except Exception:
                        pass

            threading.Thread(target=cargar_en_thread, daemon=True).start()

        total, disponibles = libro.contar_ejemplares()

        if disponibles > 0:
            estado_txt = f"✅  {disponibles} de {total} disponibles"
            color_estado, bg_estado = "#10b981", "#d1fae5"
        else:
            estado_txt = "❌  Sin ejemplares disponibles"
            color_estado, bg_estado = "#dc2626", "#fee2e2"

        estado_frame = tk.Frame(left, bg=bg_estado, padx=15, pady=8)
        estado_frame.pack(fill="x")
        tk.Label(estado_frame, text=estado_txt, font=("Segoe UI", 10, "bold"),
                 bg=bg_estado, fg=color_estado).pack()

        right = tk.Frame(body, bg="white")
        right.pack(side="left", fill="both", expand=True, padx=(25, 0))

        tk.Label(right, text=libro.Book_Title or "Sin título",
                 font=("Segoe UI", 18, "bold"), bg="white",
                 fg="#0f172a", wraplength=380, justify="left").pack(
            anchor="w", pady=(0, 5))

        tk.Label(right, text=f"✍️  {libro.Book_Author or 'Autor desconocido'}",
                 font=("Segoe UI", 12), bg="white",
                 fg="#475569").pack(anchor="w", pady=(0, 20))

        tk.Frame(right, bg="#e2e8f0", height=1).pack(fill="x", pady=10)

        def fila(label, valor):
            f = tk.Frame(right, bg="white")
            f.pack(fill="x", pady=6)

            tk.Label(f, text=label, font=("Segoe UI", 10),
                     bg="white", fg="#64748b",
                     width=16, anchor="w").pack(side="left")

            tk.Label(f, text=str(valor) if valor else "—",
                     font=("Segoe UI", 10, "bold"), bg="white",
                     fg="#1e293b", anchor="w", wraplength=250,
                     justify="left").pack(side="left")

        fila("ISBN:", libro.ISBN)
        fila("Año:", libro.Year_Of_Publication)
        fila("Editorial:", libro.Publisher)
        fila("Ejemplares:", f"{total} registrados")
        fila("Disponibles:", f"{disponibles}")

        if self.auth.es_admin():
            botones = tk.Frame(right, bg="white")
            botones.pack(side="bottom", fill="x", pady=(20, 0))

            tk.Button(botones, text="✏️  Editar",
                      font=("Segoe UI", 10, "bold"),
                      bg="#38bdf8", fg="#0f172a",
                      activebackground="#0ea5e9", activeforeground="white",
                      bd=0, cursor="hand2", padx=20, pady=8,
                      command=lambda: [w.destroy(), self.abrir_form(libro)]
                      ).pack(side="left", padx=3)

    # ==========================================
    # GESTIONAR EJEMPLARES
    # ==========================================
    def gestionar_ejemplares(self, libro):
        w = tk.Toplevel(self)
        w.title(f"📦 Ejemplares - {libro.Book_Title}")
        w.geometry("700x550")
        w.configure(bg="#f1f5f9")
        w.transient(self)
        w.grab_set()
        w.focus_force()
        quitar_boton_cerrar(w)

        header = tk.Frame(w, bg="#0f172a", height=80)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(header, text="📦  Gestión de Ejemplares",
                 font=("Segoe UI", 18, "bold"), bg="#0f172a",
                 fg="#38bdf8").pack(side="left", padx=30, pady=20)

        tk.Button(header, text="✖  Cerrar",
                  font=("Segoe UI", 11, "bold"),
                  bg="#ef4444", fg="white",
                  activebackground="#dc2626", activeforeground="white",
                  bd=0, cursor="hand2", padx=20, pady=8,
                  command=w.destroy).pack(side="right", padx=30, pady=20)

        body = tk.Frame(w, bg="white", padx=25, pady=20)
        body.pack(fill="both", expand=True, padx=15, pady=15)

        top = tk.Frame(body, bg="white")
        top.pack(fill="x", pady=(0, 15))

        tk.Button(top, text="＋  Agregar Ejemplar",
                  font=("Segoe UI", 11, "bold"),
                  bg="#10b981", fg="white",
                  activebackground="#059669", activeforeground="white",
                  bd=0, cursor="hand2", padx=20, pady=10,
                  command=lambda: self.agregar_ejemplar(libro, w)
                  ).pack(side="left")

        lbl_count = tk.Label(top, text="", font=("Segoe UI", 11),
                             bg="white", fg="#475569")
        lbl_count.pack(side="right")

        tabla = tk.Frame(body, bg="white")
        tabla.pack(fill="both", expand=True)

        cols = ("ID Ejemplar", "Estado", "Acciones")
        tree = ttk.Treeview(tabla, columns=cols, show="headings", height=12)

        tree.heading("ID Ejemplar", text="ID Ejemplar")
        tree.heading("Estado", text="Estado")
        tree.heading("Acciones", text="")

        tree.column("ID Ejemplar", width=150, anchor="center")
        tree.column("Estado", width=150, anchor="center")
        tree.column("Acciones", width=200, anchor="center")

        sb = ttk.Scrollbar(tabla, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=sb.set)

        tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        def recargar_tabla():
            for item in tree.get_children():
                tree.delete(item)

            ejemplares = Ejemplar.obtener_por_libro(libro.idLibro)
            for e in ejemplares:
                tree.insert("", "end",
                            values=(e.id_ejemplar, e.estado, "🗑️ Eliminar"))

            total, disponibles = libro.contar_ejemplares()
            lbl_count.config(
                text=f"📦 {total} ejemplares  |  ✅ {disponibles} disponibles")

        recargar_tabla()

        def cambiar_estado(event):
            seleccion = tree.selection()
            if not seleccion:
                return

            valores = tree.item(seleccion[0], "values")
            id_ej = int(valores[0])

            ejemplar = Ejemplar.obtener_por_id(id_ej)
            if not ejemplar:
                return

            estados = ["Disponible", "Prestado", "Perdido"]

            w2 = tk.Toplevel(w)
            w2.title(f"Cambiar Estado - Ejemplar #{id_ej}")
            w2.geometry("380x280")
            w2.configure(bg="#f1f5f9")
            w2.transient(w)
            w2.grab_set()
            w2.focus_force()
            quitar_boton_cerrar(w2)

            header2 = tk.Frame(w2, bg="#0f172a", height=60)
            header2.pack(fill="x")
            header2.pack_propagate(False)

            tk.Label(header2, text="🔄  Cambiar Estado",
                     font=("Segoe UI", 15, "bold"), bg="#0f172a",
                     fg="white").pack(side="left", padx=25, pady=15)

            tk.Button(header2, text="✖  Cerrar",
                      font=("Segoe UI", 10, "bold"),
                      bg="#ef4444", fg="white",
                      activebackground="#dc2626", activeforeground="white",
                      bd=0, cursor="hand2", padx=15, pady=6,
                      command=w2.destroy).pack(side="right", padx=15, pady=12)

            form = tk.Frame(w2, bg="white", padx=25, pady=20)
            form.pack(fill="both", expand=True, padx=15, pady=15)

            tk.Label(form, text=f"Estado actual: {ejemplar.estado}",
                     font=("Segoe UI", 10), bg="white",
                     fg="#64748b").pack(pady=(0, 10))

            combo = ttk.Combobox(form, state="readonly", values=estados,
                                 width=22, font=("Segoe UI", 10))
            combo.set(ejemplar.estado)
            combo.pack(pady=5)

            def guardar():
                ejemplar.cambiar_estado(combo.get())
                w2.destroy()
                recargar_tabla()

            tk.Button(form, text="💾 Guardar",
                      font=("Segoe UI", 10, "bold"),
                      bg="#38bdf8", fg="#0f172a", bd=0, cursor="hand2",
                      padx=20, pady=7, command=guardar).pack(pady=15)

        tree.bind("<Double-1>", cambiar_estado)

        def eliminar_seleccion():
            seleccion = tree.selection()
            if not seleccion:
                messagebox.showwarning("Selección",
                                       "Selecciona un ejemplar primero.", parent=w)
                return

            valores = tree.item(seleccion[0], "values")
            id_ej = int(valores[0])

            if messagebox.askyesno("Confirmar",
                                   f"¿Eliminar el ejemplar #{id_ej}?",
                                   parent=w):
                ejemplar = Ejemplar.obtener_por_id(id_ej)
                if ejemplar:
                    ejemplar.eliminar()
                    recargar_tabla()

        tk.Button(body, text="🗑️  Eliminar Ejemplar Seleccionado",
                  font=("Segoe UI", 10, "bold"),
                  bg="#fee2e2", fg="#991b1b",
                  activebackground="#fecaca", activeforeground="#991b1b",
                  bd=0, cursor="hand2", padx=15, pady=8,
                  command=eliminar_seleccion).pack(pady=(15, 0))

        tk.Label(body,
                 text="💡 Doble clic en un ejemplar para cambiar su estado",
                 font=("Segoe UI", 9, "italic"), bg="white",
                 fg="#94a3b8").pack(pady=(10, 0))

    def agregar_ejemplar(self, libro, parent_window):
        w = tk.Toplevel(parent_window)
        w.title("Agregar Ejemplares")
        w.geometry("480x480")
        w.configure(bg="#f1f5f9")
        w.transient(parent_window)
        w.grab_set()
        w.focus_force()
        quitar_boton_cerrar(w)

        header = tk.Frame(w, bg="#0f172a", height=70)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(header, text="📦  Agregar Ejemplares",
                 font=("Segoe UI", 15, "bold"), bg="#0f172a",
                 fg="white").pack(side="left", padx=25, pady=18)

        tk.Button(header, text="✖  Cerrar",
                  font=("Segoe UI", 10, "bold"),
                  bg="#ef4444", fg="white",
                  activebackground="#dc2626", activeforeground="white",
                  bd=0, cursor="hand2", padx=15, pady=6,
                  command=w.destroy).pack(side="right", padx=20, pady=15)

        form = tk.Frame(w, bg="white", padx=30, pady=25)
        form.pack(fill="both", expand=True, padx=15, pady=15)

        tk.Label(form, text=f"Libro: {libro.Book_Title}",
                 font=("Segoe UI", 11, "bold"), bg="white",
                 fg="#1e293b", wraplength=380,
                 justify="left").pack(anchor="w", pady=(0, 20))

        tk.Label(form, text="Cantidad de ejemplares:",
                 font=("Segoe UI", 10, "bold"), bg="white",
                 fg="#334155").pack(anchor="w", pady=(0, 5))

        entry_cantidad = tk.Entry(form, width=15, font=("Segoe UI", 12),
                                  bg="#f8fafc", bd=1, relief="solid")
        entry_cantidad.insert(0, "1")
        entry_cantidad.pack(anchor="w", ipady=8, pady=5)

        tk.Label(form, text="Estado inicial:",
                 font=("Segoe UI", 10, "bold"), bg="white",
                 fg="#334155").pack(anchor="w", pady=(20, 5))

        combo_estado = ttk.Combobox(form, state="readonly",
                                    values=["Disponible", "Prestado", "Perdido"],
                                    width=22, font=("Segoe UI", 10))
        combo_estado.set("Disponible")
        combo_estado.pack(anchor="w", pady=5)

        def guardar():
            try:
                cantidad = int(entry_cantidad.get().strip())
                if cantidad < 1 or cantidad > 100:
                    messagebox.showwarning("Cantidad",
                                           "Ingresa un número entre 1 y 100.",
                                           parent=w)
                    return
            except Exception:
                messagebox.showwarning("Cantidad",
                                       "Ingresa un número válido.", parent=w)
                return

            estado = combo_estado.get()
            from database import get_connection
            conn = get_connection()
            cursor = conn.cursor()

            try:
                cursor.execute(
                    "SELECT ISNULL(MAX(id_ejemplar), 667382) FROM Ejemplar")
                next_id = cursor.fetchone()[0] + 1

                for i in range(cantidad):
                    cursor.execute("""
                        INSERT INTO Ejemplar (id_ejemplar, id_libro, estado)
                        VALUES (?, ?, ?)
                    """, (next_id + i, libro.idLibro, estado))

                conn.commit()
                conn.close()

                messagebox.showinfo("Éxito",
                                    f"✅ {cantidad} ejemplar(es) agregado(s).",
                                    parent=w)
                w.destroy()
                parent_window.destroy()
                self.gestionar_ejemplares(libro)
            except Exception as e:
                conn.close()
                messagebox.showerror("Error",
                                     f"No se pudieron agregar:\n\n{e}",
                                     parent=w)

        tk.Button(form, text="💾 Guardar",
                  font=("Segoe UI", 12, "bold"),
                  bg="#38bdf8", fg="#0f172a",
                  activebackground="#0ea5e9", activeforeground="white",
                  bd=0, cursor="hand2", padx=30, pady=12,
                  command=guardar).pack(pady=20)

    # ==========================================
    # FORM NUEVO / EDITAR LIBRO
    # ==========================================
    def abrir_form(self, libro=None):
        if not self.auth.es_admin():
            messagebox.showwarning("Sin permisos",
                                   "Solo los administradores pueden editar libros.")
            return

        w = tk.Toplevel(self)
        w.title("Nuevo Libro" if libro is None else "Editar Libro")
        w.geometry("560x500")
        w.resizable(False, False)
        w.configure(bg="#f1f5f9")
        w.transient(self)
        w.grab_set()
        quitar_boton_cerrar(w)

        header = tk.Frame(w, bg="#0f172a", height=70)
        header.pack(fill="x")
        header.pack_propagate(False)

        titulo = "📖  Nuevo Libro" if libro is None else "✏️  Editar Libro"
        tk.Label(header, text=titulo,
                 font=("Segoe UI", 17, "bold"), bg="#0f172a",
                 fg="white").pack(side="left", padx=30, pady=20)

        tk.Button(header, text="✖  Cerrar",
                  font=("Segoe UI", 11, "bold"),
                  bg="#ef4444", fg="white",
                  activebackground="#dc2626", activeforeground="white",
                  bd=0, cursor="hand2", padx=20, pady=8,
                  command=w.destroy).pack(side="right", padx=30, pady=18)

        form = tk.Frame(w, bg="white", padx=30, pady=25)
        form.pack(fill="both", expand=True, padx=20, pady=15)

        campos = [
            ("ISBN", "ISBN"),
            ("Título", "Book_Title"),
            ("Autor", "Book_Author"),
            ("Año de publicación", "Year_Of_Publication"),
            ("Editorial", "Publisher"),
            ("URL de imagen", "Image_URL_L"),
        ]

        entries = {}
        for i, (label, key) in enumerate(campos):
            tk.Label(form, text=label, font=("Segoe UI", 10, "bold"),
                     bg="white", fg="#334155").grid(
                row=i, column=0, padx=(5, 15), pady=10, sticky="e")

            entry = tk.Entry(form, width=42, font=("Segoe UI", 10),
                             bg="#f8fafc", bd=1, relief="solid",
                             highlightthickness=0)
            entry.grid(row=i, column=1, padx=5, pady=10, sticky="w",
                       ipady=6)

            if libro:
                entry.insert(0, str(getattr(libro, key, "") or ""))

            entries[key] = entry

        def guardar():
            try:
                datos = {k: e.get().strip() for k, e in entries.items()}

                if not datos["Book_Title"]:
                    messagebox.showwarning("Campo requerido",
                                           "El título del libro es obligatorio.",
                                           parent=w)
                    entries["Book_Title"].focus()
                    return

                obj = Libro() if libro is None else libro
                obj.ISBN = datos["ISBN"] or None
                obj.Book_Title = datos["Book_Title"]
                obj.Book_Author = datos["Book_Author"] or None
                obj.Year_Of_Publication = (
                    int(datos["Year_Of_Publication"])
                    if datos["Year_Of_Publication"].isdigit() else None
                )
                obj.Publisher = datos["Publisher"] or None
                obj.Image_URL_L = datos["Image_URL_L"] or None

                obj.guardar()
                w.destroy()
                self.cargar_libros()
                messagebox.showinfo("Éxito", "📚 Libro guardado correctamente.")
            except Exception as e:
                messagebox.showerror("Error",
                                     f"No se pudo guardar:\n\n{e}",
                                     parent=w)

        tk.Button(w, text="💾 Guardar",
                  font=("Segoe UI", 11, "bold"),
                  bg="#38bdf8", fg="#0f172a",
                  activebackground="#0ea5e9", activeforeground="white",
                  bd=0, cursor="hand2", padx=25, pady=10,
                  command=guardar).pack(pady=10)

    def eliminar_directo(self, libro):
        if messagebox.askyesno("Confirmar eliminación",
                               f"¿Estás seguro de eliminar este libro?\n\n"
                               f"📖 {libro.Book_Title}\n\n"
                               f"Esta acción no se puede deshacer."):
            try:
                libro.eliminar()
                self.cargar_libros()
                messagebox.showinfo("Éxito", "🗑️ Libro eliminado.")
            except Exception as e:
                messagebox.showerror("Error",
                                     f"No se pudo eliminar:\n\n{e}")