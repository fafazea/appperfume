# main.py
# Perfume Lab (Ultimate, PC stable) – Kivy 2.3.0 + KivyMD 1.1.1

# 1) Backend ANGLE pour stabilité Windows (AVANT tout import Kivy/KivyMD)
import os
os.environ.setdefault("KIVY_GL_BACKEND", "angle_sdl2")

from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import ListProperty
from kivy.core.window import Window

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.snackbar import Snackbar
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.button import MDFlatButton, MDRaisedButton, MDIconButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.textfield import MDTextField
from kivymd.uix.list import TwoLineListItem
from kivymd.uix.card import MDCard
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.dialog import MDDialog

import sqlite3, csv, json
from datetime import datetime

# 2) Couleur de fond fenêtre (gris sombre)
Window.clearcolor = (0.05, 0.05, 0.06, 1)

# ---------- UI (KV) ----------
KV = '''
# Couleurs fixes (pour compat KivyMD 1.1.1)
#:set COLOR_BG 0.05, 0.05, 0.06, 1
#:set COLOR_BG2 0.08, 0.08, 0.09, 1
#:set COLOR_TEXT 1, 1, 1, 1

<MField@MDTextField>:
    mode: "fill"             # (pas "filled" en 1.1.1)
    hint_text_color_normal: 1, 0.75, 0.2, 1
    text_color_normal: COLOR_TEXT

<TitleCard@MDCard>:
    md_bg_color: COLOR_BG2
    radius: dp(18)
    padding: dp(14)
    spacing: dp(12)
    orientation: "vertical"

<HeaderBar@MDBoxLayout>:
    size_hint_y: None
    height: dp(56)
    padding: dp(10)
    spacing: dp(10)
    md_bg_color: COLOR_BG2

MDScreen:
    md_bg_color: COLOR_BG
    MDBoxLayout:
        orientation: "vertical"

        HeaderBar:
            MDLabel:
                text: "Perfume Lab — Accord & Formulation"
                font_style: "H6"
                bold: True
                halign: "left"
                theme_text_color: "Custom"
                text_color: COLOR_TEXT
            MDIconButton:
                icon: "file-export-outline"
                tooltip_text: "Exporter CSV"
                on_release: app.export_all_csv()
            MDIconButton:
                icon: "cog-outline"
                tooltip_text: "Aide"
                on_release: app.show_help()

        MDBottomNavigation:
            panel_color: COLOR_BG2

            # ---------- MATIERES ----------
            MDBottomNavigationItem:
                name: "materials"
                text: "Matières"
                icon: "flask-outline"
                MDBoxLayout:
                    orientation: "vertical"
                    padding: dp(10)
                    spacing: dp(10)

                    TitleCard:
                        MDLabel:
                            text: "Ajouter / éditer une matière"
                            font_style: "H6"
                            bold: True
                            theme_text_color: "Custom"
                            text_color: COLOR_TEXT
                        MDBoxLayout:
                            spacing: dp(10)
                            MField:
                                id: mat_name
                                hint_text: "Nom"
                            MField:
                                id: mat_family
                                hint_text: "Famille (floral, boisé, aldéhydé, gourmand...)"
                            MField:
                                id: mat_dilution
                                hint_text: "Dilution %"
                                text: "100"
                                input_filter: "float"
                        MField:
                            id: mat_notes
                            hint_text: "Notes (facettes, IFRA, fournisseur...)"
                            multiline: True
                        MDBoxLayout:
                            spacing: dp(10)
                            MDRaisedButton:
                                text: "Enregistrer matière"
                                on_release: app.save_material()
                            MDFlatButton:
                                text: "Réinitialiser"
                                on_release: app.clear_material_form()

                    TitleCard:
                        MDBoxLayout:
                            spacing: dp(10)
                            MField:
                                id: mat_search
                                hint_text: "Recherche matière..."
                                on_text: app.refresh_materials()
                            MDIconButton:
                                icon: "magnify"
                                on_release: app.refresh_materials()
                        MDScrollView:
                            MDList:
                                id: mat_list

            # ---------- ACCORDS ----------
            MDBottomNavigationItem:
                name: "accords"
                text: "Accords"
                icon: "puzzle-outline"
                MDBoxLayout:
                    orientation: "vertical"
                    padding: dp(10)
                    spacing: dp(10)

                    TitleCard:
                        MDLabel:
                            text: "Créer un accord (liste d’ingrédients + %)"
                            font_style: "H6"
                            bold: True
                            theme_text_color: "Custom"
                            text_color: COLOR_TEXT
                        MField:
                            id: acc_name
                            hint_text: "Nom de l’accord (ex: Accord Tabac Miel)"
                        MField:
                            id: acc_notes
                            hint_text: "Notes d’usage (facettes, contexte, limites...)"
                            multiline: True
                        MDBoxLayout:
                            spacing: dp(10)
                            MField:
                                id: acc_mat
                                hint_text: "Matière (ou accord)"
                                on_focus: app.open_material_menu(self) if self.focus else None
                            MField:
                                id: acc_pct
                                hint_text: "% (0-100)"
                                input_filter: "float"
                            MDRaisedButton:
                                text: "Ajouter ingrédient"
                                on_release: app.add_acc_ingredient()
                        MDBoxLayout:
                            MDLabel:
                                id: acc_preview
                                text: "Ingrédients: (vide)"
                                theme_text_color: "Secondary"
                        MDBoxLayout:
                            spacing: dp(10)
                            MDRaisedButton:
                                text: "Enregistrer accord"
                                on_release: app.save_accord()
                            MDFlatButton:
                                text: "Reset"
                                on_release: app.clear_accord_form()

                    TitleCard:
                        MDBoxLayout:
                            spacing: dp(10)
                            MField:
                                id: acc_search
                                hint_text: "Recherche accord..."
                                on_text: app.refresh_accords()
                            MDIconButton:
                                icon: "magnify"
                                on_release: app.refresh_accords()
                        MDScrollView:
                            MDList:
                                id: acc_list

            # ---------- FORMULES ----------
            MDBottomNavigationItem:
                name: "formulas"
                text: "Formules"
                icon: "beaker-outline"
                MDBoxLayout:
                    orientation: "vertical"
                    padding: dp(10)
                    spacing: dp(10)

                    TitleCard:
                        MDLabel:
                            text: "Créer une formule (ingrédients + % / versions)"
                            font_style: "H6"
                            bold: True
                            theme_text_color: "Custom"
                            text_color: COLOR_TEXT
                        MDBoxLayout:
                            spacing: dp(10)
                            MField:
                                id: f_name
                                hint_text: "Nom de la formule"
                            MField:
                                id: f_version
                                hint_text: "Version (V1, V2, V3...)"
                                text: "V1"
                        MField:
                            id: f_notes
                            hint_text: "Notes (pyramide, cible, comparaisons...)"
                            multiline: True
                        MDBoxLayout:
                            spacing: dp(10)
                            MField:
                                id: f_mat
                                hint_text: "Matière ou Accord"
                                on_focus: app.open_material_or_accord_menu(self) if self.focus else None
                            MField:
                                id: f_pct
                                hint_text: "% (0-100)"
                                input_filter: "float"
                            MDRaisedButton:
                                text: "Ajouter ingrédient"
                                on_release: app.add_formula_ingredient()
                        MDBoxLayout:
                            MDLabel:
                                id: f_preview
                                text: "Ingrédients: (vide)"
                                theme_text_color: "Secondary"
                        MDBoxLayout:
                            spacing: dp(10)
                            MDRaisedButton:
                                text: "Enregistrer formule (version)"
                                on_release: app.save_formula()
                            MDFlatButton:
                                text: "Reset"
                                on_release: app.clear_formula_form()

                    TitleCard:
                        MDBoxLayout:
                            spacing: dp(10)
                            MField:
                                id: f_search
                                hint_text: "Recherche formule..."
                                on_text: app.refresh_formulas()
                            MDIconButton:
                                icon: "magnify"
                                on_release: app.refresh_formulas()
                        MDScrollView:
                            MDList:
                                id: f_list

            # ---------- BATCHES ----------
            MDBottomNavigationItem:
                name: "batches"
                text: "Batches"
                icon: "bottle-tonic-outline"
                MDBoxLayout:
                    orientation: "vertical"
                    padding: dp(10)
                    spacing: dp(10)

                    TitleCard:
                        MDLabel:
                            text: "Créer un batch depuis une formule"
                            font_style: "H6"
                            bold: True
                            theme_text_color: "Custom"
                            text_color: COLOR_TEXT
                        MDBoxLayout:
                            spacing: dp(10)
                            MField:
                                id: b_formula_name
                                hint_text: "Nom de la formule (sélectionner)"
                                on_focus: app.open_formula_menu(self) if self.focus else None
                            MField:
                                id: b_size
                                hint_text: "Taille du batch (g)"
                                text: "10"
                                input_filter: "float"
                        MField:
                            id: b_comment
                            hint_text: "Commentaire (olfactif, tenue, corrections...)"
                            multiline: True
                        MDBoxLayout:
                            spacing: dp(10)
                            MDRaisedButton:
                                text: "Calculer & Enregistrer Batch"
                                on_release: app.save_batch()
                            MDFlatButton:
                                text: "Reset"
                                on_release: app.clear_batch_form()

                    TitleCard:
                        MDBoxLayout:
                            spacing: dp(10)
                            MField:
                                id: b_search
                                hint_text: "Recherche batch (par formule)"
                                on_text: app.refresh_batches()
                            MDIconButton:
                                icon: "magnify"
                                on_release: app.refresh_batches()
                        MDScrollView:
                            MDList:
                                id: b_list

            # ---------- NOTES ----------
            MDBottomNavigationItem:
                name: "notes"
                text: "Notes"
                icon: "notebook-outline"
                MDBoxLayout:
                    orientation: "vertical"
                    padding: dp(10)
                    spacing: dp(10)

                    TitleCard:
                        MDLabel:
                            text: "Notes créatives / journal"
                            font_style: "H6"
                            bold: True
                            theme_text_color: "Custom"
                            text_color: COLOR_TEXT
                        MField:
                            id: n_title
                            hint_text: "Titre note"
                        MField:
                            id: n_link
                            hint_text: "Lien (formule/accord/matière) — optionnel"
                        MField:
                            id: n_body
                            hint_text: "Contenu"
                            multiline: True
                        MDBoxLayout:
                            spacing: dp(10)
                            MDRaisedButton:
                                text: "Enregistrer note"
                                on_release: app.save_note()
                            MDFlatButton:
                                text: "Reset"
                                on_release: app.clear_note_form()

                    TitleCard:
                        MDBoxLayout:
                            spacing: dp(10)
                            MField:
                                id: n_search
                                hint_text: "Recherche note..."
                                on_text: app.refresh_notes()
                            MDIconButton:
                                icon: "magnify"
                                on_release: app.refresh_notes()
                        MDScrollView:
                            MDList:
                                id: n_list
'''

# ---------- DB ----------
class DB:
    def __init__(self, path):
        self.path = path
        self._init()

    def _conn(self):
        return sqlite3.connect(self.path)

    def _init(self):
        con = self._conn(); cur = con.cursor()
        cur.execute('''CREATE TABLE IF NOT EXISTS materials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            family TEXT,
            dilution REAL,
            notes TEXT,
            created_at TEXT
        )''')
        cur.execute('''CREATE TABLE IF NOT EXISTS accords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            ingredients_json TEXT,
            notes TEXT,
            created_at TEXT
        )''')
        cur.execute('''CREATE TABLE IF NOT EXISTS formulas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            version TEXT,
            ingredients_json TEXT,
            notes TEXT,
            created_at TEXT
        )''')
        cur.execute('''CREATE TABLE IF NOT EXISTS batches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            formula_name TEXT,
            version TEXT,
            batch_size REAL,
            composition_json TEXT,
            comment TEXT,
            created_at TEXT
        )''')
        cur.execute('''CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            link TEXT,
            body TEXT,
            created_at TEXT
        )''')
        con.commit(); con.close()

    # Materials
    def add_material(self, name, family, dilution, notes):
        con = self._conn(); cur = con.cursor()
        cur.execute('''INSERT OR REPLACE INTO materials (name,family,dilution,notes,created_at)
                       VALUES (?,?,?,?,?)''',
                    (name, family, dilution, notes, datetime.utcnow().isoformat()))
        con.commit(); con.close()

    def get_materials(self, q=''):
        con = self._conn(); cur = con.cursor()
        if q:
            cur.execute("""SELECT id,name,family,dilution,notes,created_at
                           FROM materials
                           WHERE name LIKE ? OR family LIKE ?
                           ORDER BY name""", (f'%{q}%', f'%{q}%'))
        else:
            cur.execute("""SELECT id,name,family,dilution,notes,created_at
                           FROM materials
                           ORDER BY name""")
        rows = cur.fetchall(); con.close()
        return rows

    def delete_material(self, mid):
        con = self._conn(); cur = con.cursor()
        cur.execute("DELETE FROM materials WHERE id=?", (mid,))
        con.commit(); con.close()

    # Accords
    def add_accord(self, name, ingredients_list, notes):
        con = self._conn(); cur = con.cursor()
        cur.execute('''INSERT OR REPLACE INTO accords (name,ingredients_json,notes,created_at)
                       VALUES (?,?,?,?)''',
                    (name, json.dumps(ingredients_list, ensure_ascii=False), notes, datetime.utcnow().isoformat()))
        con.commit(); con.close()

    def get_accords(self, q=''):
        con = self._conn(); cur = con.cursor()
        if q:
            cur.execute("""SELECT id,name,ingredients_json,notes,created_at
                           FROM accords
                           WHERE name LIKE ?
                           ORDER BY name""", (f'%{q}%',))
        else:
            cur.execute("""SELECT id,name,ingredients_json,notes,created_at
                           FROM accords
                           ORDER BY name""")
        rows = cur.fetchall(); con.close()
        return rows

    def delete_accord(self, aid):
        con = self._conn(); cur = con.cursor()
        cur.execute("DELETE FROM accords WHERE id=?", (aid,))
        con.commit(); con.close()

    # Formulas
    def add_formula(self, name, version, ingredients_list, notes):
        con = self._conn(); cur = con.cursor()
        cur.execute('''INSERT INTO formulas (name,version,ingredients_json,notes,created_at)
                       VALUES (?,?,?,?,?)''',
                    (name, version, json.dumps(ingredients_list, ensure_ascii=False), notes, datetime.utcnow().isoformat()))
        con.commit(); con.close()

    def get_formulas(self, q=''):
        con = self._conn(); cur = con.cursor()
        if q:
            cur.execute("""SELECT id,name,version,ingredients_json,notes,created_at
                           FROM formulas
                           WHERE name LIKE ? OR version LIKE ?
                           ORDER BY created_at DESC""",
                        (f'%{q}%', f'%{q}%'))
        else:
            cur.execute("""SELECT id,name,version,ingredients_json,notes,created_at
                           FROM formulas
                           ORDER BY created_at DESC""")
        rows = cur.fetchall(); con.close()
        return rows

    def get_formula_versions(self, name):
        con = self._conn(); cur = con.cursor()
        cur.execute("""SELECT id,name,version,ingredients_json,notes,created_at
                       FROM formulas WHERE name=?
                       ORDER BY created_at DESC""", (name,))
        rows = cur.fetchall(); con.close()
        return rows

    def delete_formula(self, fid):
        con = self._conn(); cur = con.cursor()
        cur.execute("DELETE FROM formulas WHERE id=?", (fid,))
        con.commit(); con.close()

    # Batches
    def add_batch(self, formula_name, version, batch_size, composition_list, comment):
        con = self._conn(); cur = con.cursor()
        cur.execute('''INSERT INTO batches (formula_name,version,batch_size,composition_json,comment,created_at)
                       VALUES (?,?,?,?,?,?)''',
                    (formula_name, version, batch_size,
                     json.dumps(composition_list, ensure_ascii=False),
                     comment, datetime.utcnow().isoformat()))
        con.commit(); con.close()

    def get_batches(self, q=''):
        con = self._conn(); cur = con.cursor()
        if q:
            cur.execute("""SELECT id,formula_name,version,batch_size,composition_json,comment,created_at
                           FROM batches
                           WHERE formula_name LIKE ?
                           ORDER BY created_at DESC""", (f'%{q}%',))
        else:
            cur.execute("""SELECT id,formula_name,version,batch_size,composition_json,comment,created_at
                           FROM batches ORDER BY created_at DESC""")
        rows = cur.fetchall(); con.close()
        return rows

    def delete_batch(self, bid):
        con = self._conn(); cur = con.cursor()
        cur.execute("DELETE FROM batches WHERE id=?", (bid,))
        con.commit(); con.close()

    # Notes
    def add_note(self, title, link, body):
        con = self._conn(); cur = con.cursor()
        cur.execute('''INSERT INTO notes (title,link,body,created_at)
                       VALUES (?,?,?,?)''', (title, link, body, datetime.utcnow().isoformat()))
        con.commit(); con.close()

    def get_notes(self, q=''):
        con = self._conn(); cur = con.cursor()
        if q:
            cur.execute("""SELECT id,title,link,body,created_at
                           FROM notes
                           WHERE title LIKE ? OR body LIKE ?
                           ORDER BY created_at DESC""",
                        (f'%{q}%', f'%{q}%'))
        else:
            cur.execute("""SELECT id,title,link,body,created_at
                           FROM notes ORDER BY created_at DESC""")
        rows = cur.fetchall(); con.close()
        return rows

    def delete_note(self, nid):
        con = self._conn(); cur = con.cursor()
        cur.execute("DELETE FROM notes WHERE id=?", (nid,))
        con.commit(); con.close()

# ---------- APP ----------
class PerfumeApp(MDApp):
    acc_ing = ListProperty([])
    f_ing = ListProperty([])

    # Patch Thonny: empêcher la recherche auto d’un .kv sur disque (évite OSError "<string>")
    def load_kv(self, filename=None):
        return

    def build(self):
        self.title = "Perfume Lab — Accord & Formulation"
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Amber"
        # (pas de self.theme_cls.material_style = "M3" en 1.1.1)

        # DB path
        data_dir = self.user_data_dir
        os.makedirs(data_dir, exist_ok=True)
        self.db_path = os.path.join(data_dir, "perfume_lab.db")
        self.db = DB(self.db_path)

        # debug simple (optionnel)
        print("KV about to load…")
        root = Builder.load_string(KV)
        print("KV loaded ->", root)
        return root

    # -------- Snackbar helper --------
    def toast(self, txt):
        Snackbar(text=txt, snackbar_x="10dp", snackbar_y="10dp", size_hint_x=.95, duration=2).open()

    # ---------- Materials ----------
    def save_material(self):
        name = self.root.ids.mat_name.text.strip()
        family = self.root.ids.mat_family.text.strip()
        dilution = self.root.ids.mat_dilution.text.strip() or "100"
        notes = self.root.ids.mat_notes.text.strip()
        if not name:
            self.toast("Nom requis.")
            return
        try:
            dilution = float(dilution)
        except:
            dilution = 100.0
        self.db.add_material(name, family, dilution, notes)
        self.toast(f"Matière '{name}' enregistrée.")
        self.clear_material_form()
        self.refresh_materials()

    def clear_material_form(self):
        self.root.ids.mat_name.text = ""
        self.root.ids.mat_family.text = ""
        self.root.ids.mat_dilution.text = "100"
        self.root.ids.mat_notes.text = ""

    def refresh_materials(self, *args):
        q = self.root.ids.mat_search.text.strip()
        items = self.db.get_materials(q)
        lst = self.root.ids.mat_list
        lst.clear_widgets()
        for (mid, name, family, dilution, notes, created) in items:
            txt = f"{name} — {family or '—'} ({dilution:.0f}%)"
            it = TwoLineListItem(text=txt, secondary_text=(notes or "")[:120])
            def _bind(mid=mid):
                self.confirm_delete("Supprimer cette matière ?", lambda *_: (self.db.delete_material(mid), self.refresh_materials()))
            it.on_release = _bind
            lst.add_widget(it)

    def open_material_menu(self, field):
        mats = [m[1] for m in self.db.get_materials()]
        if not mats:
            self.toast("Aucune matière enregistrée.")
            return
        menu_items = [{"text": m, "on_release": (lambda x=m: self._fill_field(field, x))} for m in mats]
        self._menu = MDDropdownMenu(caller=field, items=menu_items, width_mult=4)
        self._menu.open()

    def _fill_field(self, field, value):
        field.text = value
        if hasattr(self, "_menu"):
            self._menu.dismiss()

    # ---------- Accords ----------
    def add_acc_ingredient(self):
        name = self.root.ids.acc_mat.text.strip()
        pct = self.root.ids.acc_pct.text.strip()
        if not name or not pct:
            self.toast("Matière + % requis.")
            return
        try:
            pctv = float(pct)
        except:
            self.toast("Pourcentage invalide.")
            return
        self.acc_ing.append({"name": name, "pct": pctv})
        self.root.ids.acc_mat.text = ""
        self.root.ids.acc_pct.text = ""
        self._update_acc_preview()

    def _update_acc_preview(self):
        if not self.acc_ing:
            self.root.ids.acc_preview.text = "Ingrédients: (vide)"
        else:
            s = ", ".join([f"{i['name']}({i['pct']}%)" for i in self.acc_ing])
            self.root.ids.acc_preview.text = f"Ingrédients: {s}"

    def save_accord(self):
        name = self.root.ids.acc_name.text.strip()
        notes = self.root.ids.acc_notes.text.strip()
        if not name or not self.acc_ing:
            self.toast("Nom + au moins 1 ingrédient.")
            return
        self.db.add_accord(name, self.acc_ing, notes)
        self.toast(f"Accord '{name}' enregistré.")
        self.clear_accord_form()
        self.refresh_accords()

    def clear_accord_form(self):
        self.root.ids.acc_name.text = ""
        self.root.ids.acc_notes.text = ""
        self.acc_ing = []
        self._update_acc_preview()

    def refresh_accords(self, *args):
        q = self.root.ids.acc_search.text.strip()
        rows = self.db.get_accords(q)
        lst = self.root.ids.acc_list
        lst.clear_widgets()
        for (aid, name, ing_json, notes, created) in rows:
            ings = json.loads(ing_json or "[]")
            prev = ", ".join([f"{i['name']}({i['pct']}%)" for i in ings])[:80]
            it = TwoLineListItem(text=f"{name}", secondary_text=prev or "")
            def _bind(aid=aid):
                self.confirm_delete("Supprimer cet accord ?", lambda *_: (self.db.delete_accord(aid), self.refresh_accords()))
            it.on_release = _bind
            lst.add_widget(it)

    # ---------- Formules ----------
    def open_material_or_accord_menu(self, field):
        mats = [("M", m[1]) for m in self.db.get_materials()]
        accs = [("A", a[1]) for a in self.db.get_accords()]
        items = mats + accs
        if not items:
            self.toast("Ajoute d'abord des matières/accords.")
            return
        menu_items = [{"text": f"{k} │ {v}", "on_release": (lambda x=v: self._fill_field(field, x))} for (k, v) in items]
        self._menu = MDDropdownMenu(caller=field, items=menu_items, width_mult=4)
        self._menu.open()

    def add_formula_ingredient(self):
        name = self.root.ids.f_mat.text.strip()
        pct = self.root.ids.f_pct.text.strip()
        if not name or not pct:
            self.toast("Matière/Accord + % requis.")
            return
        try:
            pctv = float(pct)
        except:
            self.toast("Pourcentage invalide.")
            return
        self.f_ing.append({"name": name, "pct": pctv})
        self.root.ids.f_mat.text = ""
        self.root.ids.f_pct.text = ""
        self._update_f_preview()

    def _update_f_preview(self):
        if not self.f_ing:
            self.root.ids.f_preview.text = "Ingrédients: (vide)"
        else:
            s = ", ".join([f"{i['name']}({i['pct']}%)" for i in self.f_ing])
            self.root.ids.f_preview.text = f"Ingrédients: {s}"

    def save_formula(self):
        name = self.root.ids.f_name.text.strip()
        version = self.root.ids.f_version.text.strip() or "V1"
        notes = self.root.ids.f_notes.text.strip()
        if not name or not self.f_ing:
            self.toast("Nom + au moins 1 ingrédient.")
            return
        self.db.add_formula(name, version, self.f_ing, notes)
        self.toast(f"Formule '{name} {version}' enregistrée.")
        self.clear_formula_form()
        self.refresh_formulas()

    def clear_formula_form(self):
        self.root.ids.f_name.text = ""
        self.root.ids.f_version.text = "V1"
        self.root.ids.f_notes.text = ""
        self.f_ing = []
        self._update_f_preview()

    def refresh_formulas(self, *args):
        q = self.root.ids.f_search.text.strip()
        rows = self.db.get_formulas(q)
        lst = self.root.ids.f_list
        lst.clear_widgets()
        for (fid, name, version, ing_json, notes, created) in rows:
            ings = json.loads(ing_json or "[]")
            prev = ", ".join([f"{i['name']}({i['pct']}%)" for i in ings])[:80]
            it = TwoLineListItem(text=f"{name}  —  {version}", secondary_text=prev or "")
            def _bind(fid=fid):
                self.confirm_delete("Supprimer cette version ?", lambda *_: (self.db.delete_formula(fid), self.refresh_formulas()))
            it.on_release = _bind
            lst.add_widget(it)

    def open_formula_menu(self, field):
        rows = self.db.get_formulas()
        names_versions = [f"{r[1]} │ {r[2]}" for r in rows]
        if not names_versions:
            self.toast("Aucune formule enregistrée.")
            return
        menu_items = [{"text": nv, "on_release": (lambda x=nv: self._fill_field(field, x.split('│')[0].strip()))} for nv in names_versions]
        self._menu = MDDropdownMenu(caller=field, items=menu_items, width_mult=4)
        self._menu.open()

    # ---------- Batches ----------
    def save_batch(self):
        f_name = self.root.ids.b_formula_name.text.strip()
        if not f_name:
            self.toast("Choisis une formule.")
            return
        versions = self.db.get_formula_versions(f_name)
        if not versions:
            self.toast("Formule introuvable.")
            return
        (fid, name, version, ing_json, notes, created) = versions[0]  # dernière version
        try:
            size = float(self.root.ids.b_size.text.strip() or "10")
        except:
            size = 10.0
        ings = json.loads(ing_json or "[]")
        comp = []
        for ing in ings:
            grams = round(size * (ing['pct'] / 100.0), 3)
            comp.append({"name": ing['name'], "pct": ing['pct'], "g": grams})
        comment = self.root.ids.b_comment.text.strip()
        self.db.add_batch(name, version, size, comp, comment)
        self.toast(f"Batch {name} {version} — {size} g enregistré.")
        self.clear_batch_form()
        self.refresh_batches()

    def clear_batch_form(self):
        self.root.ids.b_formula_name.text = ""
        self.root.ids.b_size.text = "10"
        self.root.ids.b_comment.text = ""

    def refresh_batches(self, *args):
        q = self.root.ids.b_search.text.strip()
        rows = self.db.get_batches(q)
        lst = self.root.ids.b_list
        lst.clear_widgets()
        for (bid, fname, ver, size, comp_json, comment, created) in rows:
            sub = f"{fname} {ver} • {size} g • {created.split('T')[0]}"
            if comment:
                sub += f"\n{(comment or '')[:80]}"
            it = TwoLineListItem(text=f"Batch {fname}", secondary_text=sub)
            def _bind(bid=bid):
                self.confirm_delete("Supprimer ce batch ?", lambda *_: (self.db.delete_batch(bid), self.refresh_batches()))
            it.on_release = _bind
            lst.add_widget(it)

    # ---------- Notes ----------
    def save_note(self):
        title = self.root.ids.n_title.text.strip()
        link = self.root.ids.n_link.text.strip()
        body = self.root.ids.n_body.text.strip()
        if not title and not body:
            self.toast("Note vide.")
            return
        self.db.add_note(title, link, body)
        self.toast("Note enregistrée.")
        self.clear_note_form()
        self.refresh_notes()

    def clear_note_form(self):
        self.root.ids.n_title.text = ""
        self.root.ids.n_link.text = ""
        self.root.ids.n_body.text = ""

    def refresh_notes(self, *args):
        q = self.root.ids.n_search.text.strip()
        rows = self.db.get_notes(q)
        lst = self.root.ids.n_list
        lst.clear_widgets()
        for (nid, title, link, body, created) in rows:
            title = title or "(Sans titre)"
            sec = f"{created.split('T')[0]}  ·  {link or ''}\n{(body or '')[:80]}"
            it = TwoLineListItem(text=title, secondary_text=sec)
            def _bind(nid=nid):
                self.confirm_delete("Supprimer cette note ?", lambda *_: (self.db.delete_note(nid), self.refresh_notes()))
            it.on_release = _bind
            lst.add_widget(it)

    # ---------- Export CSV ----------
    def export_all_csv(self):
        base = self.user_data_dir
        os.makedirs(base, exist_ok=True)

        def _dump(table, cols, filename):
            con = sqlite3.connect(self.db_path)
            cur = con.cursor()
            cur.execute(f"SELECT {','.join(cols)} FROM {table}")
            rows = cur.fetchall()
            con.close()
            path = os.path.join(base, filename)
            with open(path, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(cols)
                for r in rows:
                    w.writerow(r)
            return path

        _dump("materials", ["id","name","family","dilution","notes","created_at"], "materials.csv")
        _dump("accords", ["id","name","ingredients_json","notes","created_at"], "accords.csv")
        _dump("formulas", ["id","name","version","ingredients_json","notes","created_at"], "formulas.csv")
        _dump("batches", ["id","formula_name","version","batch_size","composition_json","comment","created_at"], "batches.csv")
        _dump("notes", ["id","title","link","body","created_at"], "notes.csv")

        self.toast("Exports CSV créés dans le dossier de l’app.")

    # ---------- Helper Dialog ----------
    def confirm_delete(self, text, on_yes):
        self._dlg = MDDialog(
            title="Confirmation",
            text=text,
            buttons=[
                MDFlatButton(text="Annuler", on_release=lambda *_: self._dlg.dismiss()),
                MDRaisedButton(text="Supprimer", on_release=lambda *_: (self._dlg.dismiss(), on_yes())),
            ],
        )
        self._dlg.open()

    def show_help(self):
        dlg = MDDialog(
            title="Aide",
            text=(
                "• Ajoute matières & accords, puis construis des formules.\n"
                "• Un batch prend la DERNIÈRE version de la formule.\n"
                "• Exports CSV dans le dossier de l’application.\n"
                "• Mode sombre + backend ANGLE (Windows)."
            ),
            buttons=[MDFlatButton(text="OK", on_release=lambda *_: dlg.dismiss())],
        )
        dlg.open()

if __name__ == "__main__":
    PerfumeApp().run()
