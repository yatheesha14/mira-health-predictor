"main.py  —  MIRA Health Predictor"

import tkinter as tk
from tkinter import ttk , messagebox
import threading
import database as db
import validators as val
import ai_service as ai

#medical teal theme colour palette
CLR = {
      "bg":         "#F0F4F8",  
    "surface":    "#FFFFFF",   
    "nav":        "#0D4A4A",   
    "accent":     "#00B4A6",    
    "accent_dk":  "#009B8E",   
    "danger":     "#DC2626",   
    "warning":    "#D97706",   
    "success":    "#16A34A",   
    "text":       "#1A202C",   
    "muted":      "#64748B",   
    "border":     "#E2E8F0",   
    "row_alt":    "#F8FAFC",   
    "select":     "#E6F7F6", 
}

FONT_TITLE = ("Roboto", 18,"bold")
FONT_HEAD = ("Roboto", 11, "bold")
FONT_BODY = ("Roboto", 10)
FONT_SMALL = ("Roboto", 9)
FONT_MONO = ("Consolas", 9)

def styled_button(parent, text, command, color=None, text_color="white",
                  width=14, font=FONT_BODY):
    """Return a consistently styled tk.Button."""
    color = color or CLR["accent"]
    btn = tk.Button(
        parent, text=text, command=command,
        bg=color, fg=text_color, activebackground=CLR["accent_dk"],
        activeforeground="white", relief="flat", cursor="hand2",
        font=font, width=width, padx=8, pady=6, bd=0
     )
    btn.bind("<Enter>", lambda e: btn.config(bg=CLR["accent_dk"] if color == CLR["accent"] else color))
    btn.bind("<Leave>", lambda e: btn.config(bg=color))
    return btn

def label_entry(parent, label_text, row, col=0, width=28, show=None):
    """
    Place a Label + Entry pair in a grid.
    Returns the Entry widget so the caller can read/set its value.
    """
    tk.Label(parent, text=label_text, bg=CLR["surface"],
             fg=CLR["muted"], font=FONT_SMALL, anchor="w"
             ).grid(row=row, column=col, sticky="w", pady=(10, 2), padx=(0, 8))
    entry = tk.Entry(parent, width=width, font=FONT_BODY,
                     relief="solid", bd=1, bg="white",
                     fg=CLR["text"], show=show or "")
    entry.grid(row=row + 1, column=col, sticky="ew", ipady=5, padx=(0, 8))
    return entry

def section_label(parent, row, text):
    """A horizontal rule + title to separate form sections"""
    tk.Label(parent, text=text, bg=CLR["surface"],
             fg=CLR["accent"], font=("Roboto", 10, "bold")
             ).grid(row=row, column=0, columnspan=3,
                    sticky="w", pady=(18, 2))
    ttk.Separator(parent, orient="horizontal").grid(
        row=row + 1, column=0, columnspan=3, sticky="ew", pady=(0, 4))

# Patient Form  (shared by Add and Edit dialogs)
class PatientForm(tk.Toplevel):
     def __init__(self, parent, on_save, patient_data=None):
        super().__init__(parent)
        self.on_save    = on_save
        self.patient    = patient_data
        self.is_edit    = patient_data is not None
        self._ai_thread = None
        self.title("Edit Patient" if self.is_edit else "Add New Patient")
        self.resizable(True, True)
        self.configure(bg=CLR["surface"])
        #self.grab_set()           
        self.focus_set()
        self._build_ui()
        self._centre_window(600, 700)
        if self.is_edit:
            self._populate_fields()
#Layout 
     def _build_ui(self):
        # Header bar
        hdr = tk.Frame(self, bg=CLR["nav"], pady=14)
        hdr.pack(fill="x")
        title_text = "✏  Edit Patient" if self.is_edit else "＋  New Patient"
        tk.Label(hdr, text=title_text, bg=CLR["nav"], fg="white",
                 font=FONT_TITLE).pack(padx=20, anchor="w")
 # Scrollable body
        body = tk.Frame(self, bg=CLR["surface"], padx=24, pady=10)
        body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=1)
        body.columnconfigure(2, weight=1)
       # Personal section 
        section_label(body, 0, " Personal Information")
        self.e_name  = label_entry(body, "Full Name *",       row=2, col=0, width=24)
        self.e_dob   = label_entry(body, "Date of Birth * (DD/MM/YYYY)", row=2, col=1, width=18)
        self.e_email = label_entry(body, "Email Address *",   row=4, col=0, width=42)

        #email spans two columns
        self.e_email.grid(row=5, column=0, columnspan=2, sticky="ew", ipady=5, padx=(0, 8))

        #Blood test section
        section_label(body, 6, "Blood Test Results")
        self.e_glucose  = label_entry(body, "Glucose (mg/dL) *",     row=8,  col=0, width=14)
        self.e_hb       = label_entry(body, "Haemoglobin (g/dL) *",  row=8,  col=1, width=14)
        self.e_chol     = label_entry(body, "Cholesterol (mg/dL) *", row=8,  col=2, width=14)
 
        # Reference ranges hint
        hint = "Normal ranges  |  Glucose: 70–99  |  Haemoglobin: 12–17.5  |  Cholesterol: <200"
        tk.Label(body, text=hint, bg=CLR["surface"], fg=CLR["muted"],
                 font=FONT_SMALL).grid(row=10, column=0, columnspan=3,
                                       sticky="w", pady=(4, 0))
        #AI Remarks section
        section_label(body, 11, " AI Health Prediction (Remarks)")
        self.remarks_var = tk.StringVar(value="Will be generated automatically when you save.")
        self.remarks_box = tk.Text(
            body, height=5, width=60, font=FONT_SMALL,
            wrap="word", relief="solid", bd=1,
            bg="#F8FAFC", fg=CLR["muted"], state="disabled"
        )
        self.remarks_box.grid(row=13, column=0, columnspan=3,
                              sticky="ew", pady=(4, 0))
        # Status label (shows "Analysing…" while AI runs)
        self.status_var = tk.StringVar(value="")
        tk.Label(body, textvariable=self.status_var,
                 bg=CLR["surface"], fg=CLR["accent"],
                 font=FONT_SMALL).grid(row=14, column=0, columnspan=3, sticky="w")
        #validation errors
        self.error_var = tk.StringVar(value="")
        self.error_lbl = tk.Label(
            body, textvariable=self.error_var,
            bg = CLR["surface"], fg = CLR["danger"],
            font = FONT_SMALL, wraplength=500, justify="left"
        )
        self.error_lbl.grid(row = 15, column = 0, columnspan=3, sticky="w", pady=(8,0))
        
        #Buttons
        btn_row = tk.Frame(body, bg = CLR["surface"])
        btn_row.grid(row=16, column=0, columnspan=3, sticky="ew", pady=(16,8))
        styled_button(btn_row,"cancel", self.destroy,color="#64748B", width=10).pack(side = "right",pady=(16,8))
        self.save_btn = styled_button(btn_row, "save & Predict", self._on_save_click, width=18)
        self.save_btn.pack(side="right")
     def _populate_fields(self):
        """Fill all fields with existing patients data (Edit mode)."""
        p = self.patient
        self._set_entry(self.e_name,    p["full_name"])
        self._set_entry(self.e_dob,     p["dob"])
        self._set_entry(self.e_email,    p["email"])
        self._set_entry(self.e_glucose,  str(p["glucose"]))
        self._set_entry(self.e_hb,       str(p["haemoglobin"]))
        self._set_entry(self.e_chol,      str(p["cholesterol"]))
        self._set_remarks(p["remarks"] or "No prediction stored.")
        #Save logic
     def _on_save_click(self):
        self.error_var.set(" ")
        data = self._read_fields()
        errors = val.validate_patient(
            data["full_name"], data["dob"], data["email"],
            data["glucose"], data["haemoglobin"], data["cholesterol"]
          )
        if errors:
            self.error_var.set(" !" +"\n".join(errors))
            return
        self.save_btn.config(state="disabled", text="Analysing...")
        self.status_var.set("🔄 calling Ai health service, please wait...")
        self.update()
        def run_ai():
            remarks = ai.get_health_prediction(
                float(data["glucose"]),
                float(data["haemoglobin"]),
                float(data["cholesterol"])
            )
            data["remarks"] = remarks
            self.after(0, lambda: self._finish_save(data))
        threading.Thread(target=run_ai, daemon= True).start()
     def _finish_save(self, data):
         self._set_remarks(data["remarks"])
         self.status_var.set("✅  Prediction ready.")
         self.save_btn.config(state="normal", text="Save & Predict")
         self.on_save(data)
         self.destroy()
         #Helpers
     def _read_fields(self):
         return {
             "full_name":  self.e_name.get().strip(),
             "dob":        self.e_dob.get().strip(),
             "email":      self.e_email.get().strip(),
             "glucose":    self.e_glucose.get().strip(),
             "haemoglobin": self.e_hb.get().strip(),
             "cholesterol": self.e_chol.get().strip(),
         }
     def _set_entry(self, entry_widget, value):
         entry_widget.delete(0, "end")
         entry_widget.insert(0,value)
     def _set_remarks(self, text):
        self.remarks_box.config(state = "normal", fg=CLR["text"])
        self.remarks_box.delete("1.0", "end")
        self.remarks_box.insert("1.0", text)
        self.remarks_box.config(state="disabled")
     def _centre_window(self, w, h):
         self.update_idletasks()
         sw = self.winfo_screenwidth()
         sh = self.winfo_screenheight()
         x = (sw - w) // 2
         y = (sh - h) // 2
         self.geometry(f"{w}x{h}+{x}+{y}")

#Detail View Dialog
class PatientDetailView(tk.Toplevel):
    def __init__(self, parent, patient):
        super().__init__(patient)
        self.title(f"Patient -- {patient['full_name']}")
        self.resizable(False, False)
        self.configure(bg=CLR["surface"])
        self.grab_set()
        self._build(patient)
        self._centre(540, 480)
    def _build(self, p):
        #Header
        hdr = tk.Frame(self, bg=CLR["nav"], pady=14)
        hdr.pack(fill="x")
        initials = p["full_name"][0].upper()
        tk.Label(hdr, text=f"  {initials}  {p['full_name']}",
                 bg=CLR["nav"], fg="white", font=FONT_TITLE
                 ).pack(padx=20, anchor="w")
        tk.Label(hdr, text=p["email"],
                 bg=CLR["nav"], fg="#A0C4C4", font=FONT_SMALL
                 ).pack(padx=22, anchor="w")
        body = tk.Frame(self, bg=CLR["surface"], padx=24, pady=16)
        body.pack(fill="both", expand=True)
        def row(label, value,r):
            tk.Label(body, text=label, bg=CLR["surface"],
                     fg=CLR["muted"], font=FONT_SMALL, width=18, anchor="w"
                     ).grid(row=r, column=0, sticky="w", pady=3)
            tk.Label(body, text=value, bg=CLR["surface"],
                     fg=CLR["text"], font=FONT_BODY, anchor="w"
                     ).grid(row=r, column=1, sticky="w", pady=3)
        row("Date of Birth",  p["dob"],                     0)
        row("Glucose",        f"{p['glucose']} mg/dL",      1)
        row("Haemoglobin",    f"{p['haemoglobin']} g/dL",   2)
        row("Cholesterol",    f"{p['cholesterol']} mg/dL",  3)
        row("Recorded on",    p["created_at"],              4)
        # Remarks
        tk.Label(body, text="AI Remarks", bg=CLR["surface"],
                 fg=CLR["muted"], font = FONT_SMALL
                 ).grid(row=5, column=0,columnspan=2, sticky="w",pady=(14,4))
        txt = tk.Text(body, height=6, width=52, font=FONT_SMALL,
                      wrap = "word", relief="solid", bd=1,
                      bg="#F8FAFC", fg=CLR["text"])
        txt.insert("1.0", p["remarks"] or "No Prediction available.")
        txt.config(state="disabled")
        txt.grid(row=6, column=0, columnspan=2, sticky="ew")
        styled_button(body, "close", self.destroy,
                      color=CLR["muted"], width=10
                      ).grid(row=7, column=1, sticky="e", pady=(16,0))
        def _centre(self, w, h):
            self.update_idletaks()
            sw, sh = self.winfo_screenwidth(),self.winfo_screenheight()
            self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

#Main Application Window
class MIRAApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("MIRA -- Health Predictor")
        self.configure(bg=CLR["bg"])
        self.minsize(960, 580)
        self._centre_window(1100, 660)
        db.init_db()
        self._build_ui()
        self._load_patients()
        
        #Top-level layout
    def _build_ui(self):
        self._build_header()
        self._build_toolbar()
        self._build_table()
        self._build_statusbar()
    def _build_header(self):
        hdr = tk.Frame(self, bg=CLR["nav"], pady=12)
        hdr.pack(fill="x")
 
        tk.Label(hdr, text="  MIRA", bg=CLR["nav"], fg="white",
                 font=("Segoe UI", 20, "bold")).pack(side="left", padx=(16, 4))
        tk.Label(hdr, text="Medical Intelligence Robotic Automation",
                 bg=CLR["nav"], fg="#A0C4C4",
                 font=("Segoe UI", 10)).pack(side="left", padx=(0, 20))
        
        # Right side info
        tk.Label(hdr, text="Health Predictor v1.0",
                 bg=CLR["nav"], fg="#A0C4C4",
                 font=FONT_SMALL).pack(side="right", padx=20)
    def _build_toolbar(self):
        bar = tk.Frame(self, bg=CLR["bg"], pady=10, padx=16)
        bar.pack(fill="x")

        # Add button
        styled_button(bar, "＋  Add Patient", self._open_add_form,
                      width=16).pack(side="left", padx=(0, 8))
        
        # Search box
        tk.Label(bar, text="Search:", bg=CLR["bg"],
                 fg=CLR["muted"], font=FONT_SMALL).pack(side="left", padx=(16, 4))
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self._on_search)
        search_entry = tk.Entry(bar, textvariable=self.search_var,
                                width=24, font=FONT_BODY,
                                relief="solid", bd=1)
        search_entry.pack(side="left", ipady=4)
        styled_button(bar, "✕ Clear",
                      lambda: self.search_var.set(""),
                      color=CLR["muted"], width=8
                      ).pack(side="left", padx=(6, 0))

        # Refresh
        styled_button(bar, "↻ Refresh", self._load_patients,
                      color=CLR["muted"], width=10
                      ).pack(side="right")
    def _build_table(self):
        frame = tk.Frame(self, bg=CLR["bg"], padx=16, pady=0)
        frame.pack(fill="both", expand=True)

        # Column definitions: (id, header, width, anchor)
        columns = [
            ("id",          "ID",          40,  "center"),
            ("full_name",   "Full Name",   180, "w"),
            ("dob",         "Date of Birth", 100, "center"),
            ("email",       "Email",       200, "w"),
            ("glucose",     "Glucose",      80, "center"),
            ("haemoglobin", "Haemoglobin",  90, "center"),
            ("cholesterol", "Cholesterol",  90, "center"),
            ("remarks",     "AI Remarks",  320, "w"),
        ]

                # Style the Treeview
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Custom.Treeview",
                        font=FONT_BODY, rowheight=32,
                        background=CLR["surface"],
                        fieldbackground=CLR["surface"],
                        foreground=CLR["text"],
                        borderwidth=0)
        style.configure("Custom.Treeview.Heading",
                        font=("Segoe UI", 9, "bold"),
                        background=CLR["nav"],
                        foreground="white",
                        relief="flat", padding=6)
        style.map("Custom.Treeview",
                  background=[("selected", CLR["select"])],
                  foreground=[("selected", CLR["text"])])
        col_ids = [c[0] for c in columns]
        self.tree = ttk.Treeview(frame, columns=col_ids,
                                 show="headings", style="Custom.Treeview",
                                 selectmode="browse")
        for col_id, heading, width, anchor in columns:
            self.tree.heading(col_id, text=heading,
                              command=lambda c=col_id: self._sort_column(c))
            self.tree.column(col_id, width=width, anchor=anchor,
                             minwidth=40, stretch=(col_id == "remarks"))

        # Alternating row colours
        self.tree.tag_configure("even", background=CLR["surface"])
        self.tree.tag_configure("odd",  background=CLR["row_alt"])
        self.tree.tag_configure("high_glucose",  foreground=CLR["danger"])
        self.tree.tag_configure("high_chol",     foreground=CLR["warning"])

        # Scrollbars
        v_scroll = ttk.Scrollbar(frame, orient="vertical",   command=self.tree.yview)
        h_scroll = ttk.Scrollbar(frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

         # Double-click to view details
        self.tree.bind("<Double-1>", self._on_row_double_click)

        # Right-click context menu
        self._build_context_menu()
        self.tree.bind("<Button-3>", self._show_context_menu)

        # Action buttons below table
        btn_frame = tk.Frame(self, bg=CLR["bg"], pady=10, padx=16)
        btn_frame.pack(fill="x")
        styled_button(btn_frame, "👁  View",   self._view_selected,
                      color=CLR["muted"], width=12).pack(side="left", padx=(0, 6))
        styled_button(btn_frame, "✏  Edit",   self._edit_selected,
                      color="#2563EB", width=12).pack(side="left", padx=(0, 6))
        styled_button(btn_frame, "🗑  Delete", self._delete_selected,
                      color=CLR["danger"], width=12).pack(side="left")
        
    def _build_context_menu(self):
        self.ctx_menu = tk.Menu(self, tearoff=0)
        self.ctx_menu.add_command(label="👁  View Details",  command=self._view_selected)
        self.ctx_menu.add_command(label="✏  Edit Patient",  command=self._edit_selected)
        self.ctx_menu.add_separator()
        self.ctx_menu.add_command(label="🗑  Delete Patient", command=self._delete_selected)
    def _build_statusbar(self):
        bar = tk.Frame(self, bg=CLR["nav"], pady=4)
        bar.pack(fill="x", side="bottom")
        self.status_var = tk.StringVar(value="Ready.")
        tk.Label(bar, textvariable=self.status_var,
                 bg=CLR["nav"], fg="#A0C4C4",
                 font=FONT_SMALL).pack(side="left", padx=12)
    def _build_statusbar(self):
        bar = tk.Frame(self, bg=CLR["nav"], pady=4)
        bar.pack(fill="x", side="bottom")
        self.status_var = tk.StringVar(value="Ready.")
        tk.Label(bar, textvariable=self.status_var,
                 bg=CLR["nav"], fg="#A0C4C4",
                 font=FONT_SMALL).pack(side="left", padx=12)
        
        #Data loading
    def _load_patients(self, patients=None):
        """Refresh the Treeview with (optionally filtered) patient rows."""
        for row in self.tree.get_children():
            self.tree.delete(row)
        if patients is None:
            patients = db.get_all_patients()
        for i, p in enumerate(patients):
            tag = "even" if i % 2 == 0 else "odd"
            # Truncate long remarks for table display
            remarks_short = (p["remarks"] or "")[:100]
            if len(p["remarks"] or "") > 100:
                remarks_short += "…"
            self.tree.insert("", "end", iid=str(p["id"]), tags=(tag,),
                             values=(
                                 p["id"],
                                 p["full_name"],
                                 p["dob"],
                                 p["email"],
                                 f"{p['glucose']} mg",
                                 f"{p['haemoglobin']} g",
                                 f"{p['cholesterol']} mg",
                                 remarks_short,
                             ))
            count = len(patients)
            self.status_var.set(f"{count} patient{'s' if count != 1 else ''} loaded.")

        #CRUD actions
    def _open_add_form(self):
        def on_save(data):
            db.add_patient(
                data["full_name"], data["dob"], data["email"],
                data["glucose"], data["haemoglobin"], data["cholesterol"],
                data["remarks"]
            )
            self._load_patients()
            self.status_var.set(f"✅  Patient '{data['full_name']}' added successfully.")
        PatientForm(self, on_save=on_save)
    def _view_selected(self):
        patient = self._get_selected_patient()
        if patient:
            PatientDetailView(self, patient)
    def _edit_selected(self):
        patient = self._get_selected_patient()
        if not patient:
            return
        def on_save(data):
            db.update_patient(
                patient["id"],
                data["full_name"], data["dob"], data["email"],
                data["glucose"], data["haemoglobin"], data["cholesterol"],
                data["remarks"]
            )
            self._load_patients()
            self.status_var.set(f"✅  Patient '{data['full_name']}' updated.")
        PatientForm(self, on_save=on_save, patient_data=patient)
    def _delete_selected(self):
        patient = self._get_selected_patient()
        if not patient:
            return
        confirm = messagebox.askyesno(
            "Confirm Deletion",
            f"Are you sure you want to delete:\n\n"
            f"  {patient['full_name']}  ({patient['email']})\n\n"
            f"This action cannot be undone.",
            icon="warning"
        )
        if confirm:
            db.delete_patient(patient["id"])
            self._load_patients()
            self.status_var.set(f"🗑  Patient '{patient['full_name']}' deleted.")

        #Search 
    def _on_search(self, *_):
        keyword = self.search_var.get().strip()
        if keyword:
            results = db.search_patients(keyword)
            self._load_patients(results)
        else:
            self._load_patients()

    #Sort columns
    _sort_state = {}
    def _sort_column(self, col):
        reverse = self._sort_state.get(col, False)
        data = [(self.tree.set(k, col), k) for k in self.tree.get_children("")]
        try:
            data.sort(key=lambda t: float(t[0].replace(" mg", "").replace(" g", "")),
                      reverse=reverse)
        except ValueError:
            data.sort(reverse=reverse)
        for index, (_, k) in enumerate(data):
            self.tree.move(k, "", index)
        self._sort_state[col] = not reverse


        #Helpers 
    def _get_selected_patient(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("No Selection", "Please select a patient first.")
            return None
        patient_id = int(selected[0])
        return db.get_patient_by_id(patient_id)
    def _on_row_double_click(self, event):
        self._view_selected()
    def _show_context_menu(self, event):
        row = self.tree.identify_row(event.y)
        if row:
            self.tree.selection_set(row)
            self.ctx_menu.post(event.x_root, event.y_root)
    def _centre_window(self, w, h):
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")


# Entry point
if __name__ == "__main__":
    app = MIRAApp()
    app.mainloop()



 
        

 

 