from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from openpyxl import Workbook
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from hvac_takeoff.calculations import CATEGORY_ORDER, calculate_line_total, format_money, summarize_items, unit_label
from hvac_takeoff.database import (
    add_item,
    create_project,
    delete_item,
    delete_pricing_record,
    get_project,
    initialize_db,
    list_items,
    list_pricing_records,
    list_projects,
    save_pricing_record,
    touch_project,
)


class HVACProjectApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        initialize_db()
        self.title("HVAC Takeoff Pro")
        self.geometry("1500x940")
        self.minsize(1280, 760)
        self.current_project_id = None
        self.project_name_entry = None
        self.unit_combo = None
        self.project_listbox = None
        self.summary_labels = {}
        self.entry_fields = {}
        self.tree = None
        self.pricing_fields = {}
        self.pricing_tree = None
        self.dashboard_cards = {}
        self.dashboard_text = None
        self.configure(bg="#f2f5fb")
        self.build_ui()
        self.refresh_projects()

    def build_ui(self) -> None:
        top = tk.Frame(self, bg="#f2f5fb", padx=18, pady=14)
        top.pack(fill="x")

        tk.Label(top, text="Project Name", font=("Segoe UI", 11, "bold"), bg="#f2f5fb").grid(row=0, column=0, sticky="w")
        self.project_name_entry = tk.Entry(top, width=28, font=("Segoe UI", 11))
        self.project_name_entry.insert(0, "Main HVAC Estimate")
        self.project_name_entry.grid(row=0, column=1, padx=(8, 18), pady=6)

        tk.Label(top, text="Unit System", font=("Segoe UI", 11, "bold"), bg="#f2f5fb").grid(row=0, column=2, sticky="w")
        self.unit_combo = ttk.Combobox(top, values=["Imperial", "Metric"], width=12, state="readonly")
        self.unit_combo.set("Imperial")
        self.unit_combo.grid(row=0, column=3, padx=(8, 18), pady=6)

        tk.Button(top, text="Create Project", command=self.create_project, bg="#1a73e8", fg="white", font=("Segoe UI", 10, "bold"), padx=14, pady=8).grid(row=0, column=4, padx=(0, 12))
        tk.Button(top, text="Export PDF", command=self.export_pdf, bg="#00796b", fg="white", font=("Segoe UI", 10, "bold"), padx=12, pady=8).grid(row=0, column=5, padx=(0, 12))
        tk.Button(top, text="Export Excel", command=self.export_excel, bg="#5b2c83", fg="white", font=("Segoe UI", 10, "bold"), padx=12, pady=8).grid(row=0, column=6)

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=18, pady=(0, 18))

        estimate_tab = tk.Frame(notebook, bg="#f2f5fb")
        pricing_tab = tk.Frame(notebook, bg="#f2f5fb")
        dashboard_tab = tk.Frame(notebook, bg="#f2f5fb")

        notebook.add(estimate_tab, text="Estimate")
        notebook.add(pricing_tab, text="Pricing Library")
        notebook.add(dashboard_tab, text="Dashboard")

        self.build_estimate_tab(estimate_tab)
        self.build_pricing_tab(pricing_tab)
        self.build_dashboard_tab(dashboard_tab)

    def build_estimate_tab(self, parent: tk.Frame) -> None:
        sidebar = tk.Frame(parent, bg="#ffffff", bd=1, relief="solid", padx=14, pady=16)
        sidebar.pack(side="left", fill="y", padx=(0, 18))
        sidebar.config(width=320)

        tk.Label(sidebar, text="Projects", font=("Segoe UI", 14, "bold"), bg="#ffffff").pack(anchor="w", pady=(0, 10))
        self.project_listbox = tk.Listbox(sidebar, width=30, height=18, font=("Segoe UI", 10), exportselection=False)
        self.project_listbox.bind("<<ListboxSelect>>", self.on_project_selected)
        self.project_listbox.pack(fill="both", expand=True)

        main = tk.Frame(parent, bg="#f2f5fb")
        main.pack(side="right", fill="both", expand=True)

        summary = tk.Frame(main, bg="#f2f5fb")
        summary.pack(fill="x", pady=(0, 14))

        for i, label in enumerate(["Material", "Labor", "Total", "Items"]):
            card = tk.Frame(summary, bg="#ffffff", bd=1, relief="solid", padx=16, pady=12)
            card.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 12, 0))
            summary.grid_columnconfigure(i, weight=1)
            tk.Label(card, text=label, font=("Segoe UI", 10, "bold"), bg="#ffffff").pack(anchor="w")
            value = tk.Label(card, text="$0.00", font=("Segoe UI", 18, "bold"), bg="#ffffff", fg="#1a73e8")
            value.pack(anchor="w", pady=(8, 0))
            self.summary_labels[label] = value

        form = tk.Frame(main, bg="#ffffff", bd=1, relief="solid", padx=16, pady=16)
        form.pack(fill="x", pady=(0, 14))

        fields = [
            ("Category", "category"),
            ("Description", "description"),
            ("Qty", "quantity"),
            ("Unit", "unit"),
            ("Unit Cost", "unit_cost"),
            ("Labor Rate", "labor_rate"),
            ("Adjustment Factor", "adjustment_factor"),
            ("Notes", "notes"),
        ]
        col = 0
        row = 0
        for label_text, key in fields:
            tk.Label(form, text=label_text, font=("Segoe UI", 10, "bold"), bg="#ffffff").grid(row=row, column=col, sticky="w", padx=(0, 10), pady=6)
            if key == "category":
                widget = ttk.Combobox(form, values=CATEGORY_ORDER, width=20, state="readonly")
                widget.set("Duct")
            elif key == "quantity":
                widget = tk.Entry(form, width=18)
            elif key == "unit":
                widget = tk.Entry(form, width=18)
                widget.insert(0, "LF")
            elif key == "adjustment_factor":
                widget = tk.Entry(form, width=18)
                widget.insert(0, "1")
            else:
                widget = tk.Entry(form, width=18)
            widget.grid(row=row, column=col + 1, padx=(0, 16), pady=6)
            self.entry_fields[key] = widget
            col += 2
            if col >= 6:
                col = 0
                row += 1

        row += 1
        tk.Button(form, text="Add Estimate Item", command=self.add_item, bg="#228B22", fg="white", font=("Segoe UI", 10, "bold"), padx=16, pady=8).grid(row=row, column=0, columnspan=2, sticky="w", pady=(12, 6))

        columns = ("id", "category", "description", "qty", "unit", "unit_cost", "labor_rate", "adjust_factor", "material", "labor", "total", "notes")
        self.tree = ttk.Treeview(main, columns=columns, show="headings")
        for heading, key in zip(["ID", "Category", "Description", "Qty", "Unit", "Unit Cost", "Labor Rate", "Factor", "Material", "Labor", "Total", "Notes"], columns):
            self.tree.heading(key, text=heading)
            if key in {"description", "notes"}:
                self.tree.column(key, width=180, anchor="w")
            elif key in {"id"}:
                self.tree.column(key, width=50, anchor="center")
            else:
                self.tree.column(key, width=100, anchor="center")
        self.tree.pack(fill="both", expand=True)

        actions = tk.Frame(main, bg="#f2f5fb")
        actions.pack(fill="x", pady=(8, 0))
        tk.Button(actions, text="Delete Selected", command=self.delete_selected_item, bg="#d93025", fg="white", font=("Segoe UI", 10, "bold"), padx=12, pady=8).pack(side="left")
        tk.Button(actions, text="Refresh", command=self.refresh_project_view, bg="#f1b500", fg="black", font=("Segoe UI", 10, "bold"), padx=12, pady=8).pack(side="left", padx=(12, 0))

    def build_pricing_tab(self, parent: tk.Frame) -> None:
        form = tk.Frame(parent, bg="#ffffff", bd=1, relief="solid", padx=16, pady=16)
        form.pack(fill="x", padx=18, pady=18)

        label_defs = [
            ("Category", "category"),
            ("Description", "description"),
            ("Unit", "unit"),
            ("Unit Cost", "unit_cost"),
            ("Labor Rate", "labor_rate"),
            ("Adjustment Factor", "adjustment_factor"),
            ("Notes", "notes"),
        ]
        col = 0
        row = 0
        for label_text, key in label_defs:
            tk.Label(form, text=label_text, font=("Segoe UI", 10, "bold"), bg="#ffffff").grid(row=row, column=col, sticky="w", padx=(0, 10), pady=6)
            if key == "category":
                widget = ttk.Combobox(form, values=CATEGORY_ORDER, width=18, state="readonly")
                widget.set("Duct")
            else:
                widget = tk.Entry(form, width=18)
                if key == "unit":
                    widget.insert(0, "LF")
                if key == "adjustment_factor":
                    widget.insert(0, "1")
            widget.grid(row=row, column=col + 1, padx=(0, 14), pady=6)
            self.pricing_fields[key] = widget
            col += 2
            if col >= 6:
                col = 0
                row += 1

        tk.Button(form, text="Save Pricing Item", command=self.save_pricing_item, bg="#1a73e8", fg="white", font=("Segoe UI", 10, "bold"), padx=16, pady=8).grid(row=row + 1, column=0, columnspan=2, sticky="w", pady=(12, 0))

        table = tk.Frame(parent, bg="#ffffff", bd=1, relief="solid")
        table.pack(fill="both", expand=True, padx=18, pady=(0, 18))

        cols = ("id", "category", "description", "unit", "unit_cost", "labor_rate", "factor", "notes")
        self.pricing_tree = ttk.Treeview(table, columns=cols, show="headings")
        for heading, key in zip(["ID", "Category", "Description", "Unit", "Unit Cost", "Labor Rate", "Factor", "Notes"], cols):
            self.pricing_tree.heading(key, text=heading)
            self.pricing_tree.column(key, width=100, anchor="center")
        self.pricing_tree.pack(fill="both", expand=True, padx=12, pady=12)

        tk.Button(table, text="Delete Selected", command=self.delete_selected_pricing_item, bg="#d93025", fg="white", font=("Segoe UI", 10, "bold"), padx=12, pady=8).pack(anchor="w", padx=12, pady=(0, 12))

    def build_dashboard_tab(self, parent: tk.Frame) -> None:
        metrics = tk.Frame(parent, bg="#f2f5fb")
        metrics.pack(fill="x", padx=18, pady=18)

        for index, label in enumerate(["Material", "Labor", "Total", "Projects"]):
            card = tk.Frame(metrics, bg="#ffffff", bd=1, relief="solid", padx=20, pady=16)
            card.grid(row=0, column=index, sticky="nsew", padx=(0 if index == 0 else 12, 0))
            metrics.grid_columnconfigure(index, weight=1)
            tk.Label(card, text=label, font=("Segoe UI", 10, "bold"), bg="#ffffff").pack(anchor="w")
            value = tk.Label(card, text="$0.00", font=("Segoe UI", 18, "bold"), bg="#ffffff", fg="#1a73e8")
            value.pack(anchor="w", pady=(8, 0))
            self.dashboard_cards[label] = value

        info = tk.Text(parent, wrap="word", height=18, width=120, font=("Segoe UI", 10))
        info.pack(fill="both", expand=True, padx=18, pady=(0, 18))
        info.insert("end", "HVAC Takeoff Pro dashboard\n\n")
        info.insert("end", "- Track project totals across each estimate\n")
        info.insert("end", "- Monitor labor and material values by category\n")
        info.insert("end", "- Manage reusable pricing records for standard HVAC assemblies\n")
        info.insert("end", "- Export estimate reports for stakeholder review\n")
        self.dashboard_text = info

    def refresh_projects(self) -> None:
        self.project_list = list_projects()
        self.project_listbox.delete(0, tk.END)
        for project in self.project_list:
            self.project_listbox.insert(tk.END, f"{project['name']} ({project['unit_system']})")

        if self.project_list:
            if self.current_project_id is None:
                self.current_project_id = self.project_list[0]["id"]
            for index, project in enumerate(self.project_list):
                if project["id"] == self.current_project_id:
                    self.project_listbox.selection_clear(0, tk.END)
                    self.project_listbox.select_set(index)
                    break

        self.refresh_project_view()
        self.refresh_pricing_library()
        self.refresh_dashboard()

    def on_project_selected(self, _event) -> None:
        selection = self.project_listbox.curselection()
        if not selection:
            return
        project = self.project_list[selection[0]]
        self.current_project_id = project["id"]
        self.project_name_entry.delete(0, tk.END)
        self.project_name_entry.insert(0, project["name"])
        self.unit_combo.set(project["unit_system"])
        self.refresh_project_view()

    def create_project(self) -> None:
        name = self.project_name_entry.get().strip() or "Main HVAC Estimate"
        unit_system = self.unit_combo.get() or "Imperial"
        self.current_project_id = create_project(name, unit_system)
        self.project_name_entry.delete(0, tk.END)
        self.project_name_entry.insert(0, name)
        self.unit_combo.set(unit_system)
        self.refresh_projects()

    def add_item(self) -> None:
        if not self.current_project_id:
            messagebox.showwarning("No project", "Create or select a project before adding an item.")
            return

        try:
            quantity = float(self.entry_fields["quantity"].get() or 0)
            unit_cost = float(self.entry_fields["unit_cost"].get() or 0)
            labor_rate = float(self.entry_fields["labor_rate"].get() or 0)
            factor = float(self.entry_fields["adjustment_factor"].get() or 1)
        except ValueError:
            messagebox.showerror("Invalid values", "Qty, unit cost, labor rate, and adjustment factor must be numeric.")
            return

        add_item(
            project_id=self.current_project_id,
            category=self.entry_fields["category"].get() if hasattr(self.entry_fields["category"], "get") else "Duct",
            description=self.entry_fields["description"].get(),
            quantity=quantity,
            unit=self.entry_fields["unit"].get() or "LF",
            unit_cost=unit_cost,
            labor_rate=labor_rate,
            adjustment_factor=factor,
            notes=self.entry_fields["notes"].get(),
        )
        touch_project(self.current_project_id)
        self.clear_estimate_form()
        self.refresh_project_view()

    def clear_estimate_form(self) -> None:
        self.entry_fields["description"].delete(0, tk.END)
        self.entry_fields["quantity"].delete(0, tk.END)
        self.entry_fields["unit"].delete(0, tk.END)
        self.entry_fields["unit"].insert(0, "LF")
        self.entry_fields["unit_cost"].delete(0, tk.END)
        self.entry_fields["labor_rate"].delete(0, tk.END)
        self.entry_fields["adjustment_factor"].delete(0, tk.END)
        self.entry_fields["adjustment_factor"].insert(0, "1")
        self.entry_fields["notes"].delete(0, tk.END)
        if "category" in self.entry_fields:
            try:
                self.entry_fields["category"].set("Duct")
            except AttributeError:
                pass

    def refresh_project_view(self) -> None:
        if self.current_project_id is None:
            return
        items = list_items(self.current_project_id)
        summary = summarize_items(items)

        self.summary_labels["Material"].config(text=format_money(summary["material"]))
        self.summary_labels["Labor"].config(text=format_money(summary["labor"]))
        self.summary_labels["Total"].config(text=format_money(summary["total"]))
        self.summary_labels["Items"].config(text=str(summary["items"]))

        for row in self.tree.get_children():
            self.tree.delete(row)

        for item in items:
            totals = calculate_line_total(item["quantity"], item["unit_cost"], item["labor_rate"], item["adjustment_factor"])
            self.tree.insert(
                "",
                tk.END,
                values=(
                    item["id"],
                    item["category"],
                    item["description"],
                    item["quantity"],
                    item["unit"],
                    format_money(item["unit_cost"]),
                    format_money(item["labor_rate"]),
                    item["adjustment_factor"],
                    format_money(totals["material_total"]),
                    format_money(totals["labor_total"]),
                    format_money(totals["total"]),
                    item["notes"],
                ),
            )

    def delete_selected_item(self) -> None:
        values = self.tree.selection()
        if not values:
            messagebox.showwarning("No selection", "Select an item to delete.")
            return
        item_id = int(self.tree.item(values[0], "values")[0])
        delete_item(item_id)
        touch_project(self.current_project_id)
        self.refresh_project_view()

    def save_pricing_item(self) -> None:
        category = self.pricing_fields["category"].get() if hasattr(self.pricing_fields["category"], "get") else "Duct"
        description = self.pricing_fields["description"].get()
        unit = self.pricing_fields["unit"].get() or "EA"
        try:
            unit_cost = float(self.pricing_fields["unit_cost"].get() or 0)
            labor_rate = float(self.pricing_fields["labor_rate"].get() or 0)
            factor = float(self.pricing_fields["adjustment_factor"].get() or 1)
        except ValueError:
            messagebox.showerror("Invalid values", "Pricing unit cost, labor rate, and factor must be numeric.")
            return

        save_pricing_record(category, description, unit, unit_cost, labor_rate, factor, self.pricing_fields["notes"].get())
        self.refresh_pricing_library()
        self.clear_pricing_form()

    def clear_pricing_form(self) -> None:
        self.pricing_fields["description"].delete(0, tk.END)
        self.pricing_fields["unit"].delete(0, tk.END)
        self.pricing_fields["unit"].insert(0, "LF")
        self.pricing_fields["unit_cost"].delete(0, tk.END)
        self.pricing_fields["labor_rate"].delete(0, tk.END)
        self.pricing_fields["adjustment_factor"].delete(0, tk.END)
        self.pricing_fields["adjustment_factor"].insert(0, "1")
        self.pricing_fields["notes"].delete(0, tk.END)
        try:
            self.pricing_fields["category"].set("Duct")
        except AttributeError:
            pass

    def refresh_pricing_library(self) -> None:
        for row in self.pricing_tree.get_children():
            self.pricing_tree.delete(row)
        for record in list_pricing_records():
            self.pricing_tree.insert(
                "",
                tk.END,
                values=(
                    record["id"],
                    record["category"],
                    record["description"],
                    record["unit"],
                    format_money(record["unit_cost"]),
                    format_money(record["labor_rate"]),
                    record["adjustment_factor"],
                    record["notes"],
                ),
            )

    def delete_selected_pricing_item(self) -> None:
        selected = self.pricing_tree.selection()
        if not selected:
            messagebox.showwarning("No selection", "Select a pricing record to delete.")
            return
        item_id = int(self.pricing_tree.item(selected[0], "values")[0])
        delete_pricing_record(item_id)
        self.refresh_pricing_library()

    def refresh_dashboard(self) -> None:
        projects = list_projects()
        total_material = 0.0
        total_labor = 0.0
        total_estimate = 0.0
        for project in projects:
            items = list_items(project["id"])
            summary = summarize_items(items)
            total_material += summary["material"]
            total_labor += summary["labor"]
            total_estimate += summary["total"]

        self.dashboard_cards["Material"].config(text=format_money(total_material))
        self.dashboard_cards["Labor"].config(text=format_money(total_labor))
        self.dashboard_cards["Total"].config(text=format_money(total_estimate))
        self.dashboard_cards["Projects"].config(text=str(len(projects)))
        self.dashboard_text.delete("1.0", "end")
        self.dashboard_text.insert("end", "HVAC Takeoff Pro dashboard\n\n")
        self.dashboard_text.insert("end", f"- Active projects: {len(projects)}\n")
        self.dashboard_text.insert("end", f"- Total material: {format_money(total_material)}\n")
        self.dashboard_text.insert("end", f"- Total labor: {format_money(total_labor)}\n")
        self.dashboard_text.insert("end", f"- Total estimate value: {format_money(total_estimate)}\n\n")
        self.dashboard_text.insert("end", "Operational summary\n")
        self.dashboard_text.insert("end", "- Review each category and item in the estimate tab\n")
        self.dashboard_text.insert("end", "- Reuse pricing records to accelerate repeat work\n")
        self.dashboard_text.insert("end", "- Export final estimates in workbook or PDF format\n")

    def export_excel(self) -> None:
        if self.current_project_id is None:
            messagebox.showwarning("No project", "Select a project before exporting.")
            return

        project = get_project(self.current_project_id)
        items = list_items(self.current_project_id)
        if not project:
            return

        output_path = filedialog.asksaveasfilename(defaultextension=".xlsx", initialfile=f"{project['name']}.xlsx", filetypes=[("Excel Workbook", "*.xlsx")])
        if not output_path:
            return

        workbook = Workbook()
        summary = workbook.active
        summary.title = "Summary"
        summary.append(["Project", project["name"]])
        summary.append(["Unit System", project["unit_system"]])
        summary.append([])
        summary.append(["Materials", format_money(summarize_items(items)["material"])])
        summary.append(["Labor", format_money(summarize_items(items)["labor"])])
        summary.append(["Total", format_money(summarize_items(items)["total"])])

        line_sheet = workbook.create_sheet("Line Items")
        line_sheet.append(["Category", "Description", "Qty", "Unit", "Unit Cost", "Labor Rate", "Factor", "Material", "Labor", "Total", "Notes"])
        for item in items:
            totals = calculate_line_total(item["quantity"], item["unit_cost"], item["labor_rate"], item["adjustment_factor"])
            line_sheet.append([
                item["category"],
                item["description"],
                item["quantity"],
                item["unit"],
                item["unit_cost"],
                item["labor_rate"],
                item["adjustment_factor"],
                totals["material_total"],
                totals["labor_total"],
                totals["total"],
                item["notes"],
            ])

        workbook.save(output_path)
        messagebox.showinfo("Export complete", f"Workbook saved to:\n{output_path}")

    def export_pdf(self) -> None:
        if self.current_project_id is None:
            messagebox.showwarning("No project", "Select a project before exporting.")
            return

        project = get_project(self.current_project_id)
        items = list_items(self.current_project_id)
        summary = summarize_items(items)
        if not project:
            return

        output_path = filedialog.asksaveasfilename(defaultextension=".pdf", initialfile=f"{project['name']}.pdf", filetypes=[("PDF", "*.pdf")])
        if not output_path:
            return

        story = []
        styles = getSampleStyleSheet()
        story.append(Paragraph(f"HVAC Takeoff Report - {project['name']}", styles["Title"]))
        story.append(Spacer(1, 12))
        story.append(Paragraph(f"Unit System: {project['unit_system']} | Default Measure: {unit_label(project['unit_system'])}", styles["BodyText"]))
        story.append(Paragraph(f"Material Total: {format_money(summary['material'])}", styles["BodyText"]))
        story.append(Paragraph(f"Labor Total: {format_money(summary['labor'])}", styles["BodyText"]))
        story.append(Paragraph(f"Overall Total: {format_money(summary['total'])}", styles["BodyText"]))
        story.append(Spacer(1, 16))

        rows = [["Category", "Description", "Qty", "Unit", "Material", "Labor", "Total"]]
        for item in items:
            totals = calculate_line_total(item["quantity"], item["unit_cost"], item["labor_rate"], item["adjustment_factor"])
            rows.append([
                item["category"],
                item["description"],
                str(item["quantity"]),
                item["unit"],
                format_money(totals["material_total"]),
                format_money(totals["labor_total"]),
                format_money(totals["total"]),
            ])

        table = Table(rows, colWidths=[70, 190, 50, 55, 90, 90, 90])
        table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a73e8")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("GRID", (0, 0), (-1, -1), 1, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
            ])
        )
        story.append(table)

        doc = SimpleDocTemplate(output_path, pagesize=letter)
        doc.build(story)
        messagebox.showinfo("Export complete", f"PDF saved to:\n{output_path}")


def main() -> None:
    app = HVACProjectApp()
    app.mainloop()
