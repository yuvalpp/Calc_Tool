import tkinter as tk
from tkinter import ttk, messagebox
import math

class VoltageDividerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Yuval Tool Rev 1.13")
        self.root.geometry("800x600")  # Widen for schematic
        
        # E-Series Data
        self.e24 = [
            1.0, 1.1, 1.2, 1.3, 1.5, 1.6, 1.8, 2.0, 2.2, 2.4, 2.7, 3.0,
            3.3, 3.6, 3.9, 4.3, 4.7, 5.1, 5.6, 6.2, 6.8, 7.5, 8.2, 9.1
        ]
        self.e48 = [
            1.00, 1.05, 1.10, 1.15, 1.21, 1.27, 1.33, 1.40, 1.47, 1.54, 1.62, 1.69,
            1.78, 1.87, 1.96, 2.05, 2.15, 2.26, 2.37, 2.49, 2.61, 2.74, 2.87, 3.01,
            3.16, 3.32, 3.48, 3.65, 3.83, 4.02, 4.22, 4.42, 4.64, 4.87, 5.11, 5.36,
            5.62, 5.90, 6.19, 6.49, 6.81, 7.15, 7.50, 7.87, 8.25, 8.66
        ]
        self.e96 = [
            1.00, 1.02, 1.05, 1.07, 1.10, 1.13, 1.15, 1.18, 1.21, 1.24, 1.27, 1.30,
            1.33, 1.37, 1.40, 1.43, 1.47, 1.50, 1.54, 1.58, 1.62, 1.65, 1.69, 1.74,
            1.78, 1.82, 1.87, 1.91, 1.96, 2.00, 2.05, 2.10, 2.15, 2.21, 2.26, 2.32,
            2.37, 2.43, 2.49, 2.55, 2.61, 2.67, 2.74, 2.80, 2.87, 2.94, 3.01, 3.09,
            3.16, 3.24, 3.32, 3.40, 3.48, 3.57, 3.65, 3.74, 3.83, 3.92, 4.02, 4.12,
            4.22, 4.32, 4.42, 4.53, 4.64, 4.75, 4.87, 4.99, 5.11, 5.23, 5.36, 5.49,
            5.62, 5.76, 5.90, 6.04, 6.19, 6.34, 6.49, 6.65, 6.81, 6.98, 7.15, 7.32,
            7.50, 7.68, 7.87, 8.06, 8.25, 8.45, 8.66, 8.87, 9.09, 9.31, 9.53, 9.76
        ]
        
        self.resistor_vars = [] # List of (value, BooleanVar) tuples
        self.fb_resistor_vars = [] # List for Feedback tab

        self.setup_ui()

    def setup_ui(self):
        # Header
        header_frame = ttk.Frame(self.root, padding="10")
        header_frame.pack(fill=tk.X)
        
        title_frame = ttk.Frame(header_frame)
        title_frame.pack(fill=tk.X)
        ttk.Label(title_frame, text="Yuval Tool Rev 1.13", font=("Arial", 14, "bold")).pack(side=tk.LEFT)
        ttk.Button(title_frame, text="Help / Info", command=self.show_help).pack(side=tk.RIGHT)
        
        # Notebook (Tabs)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Tab 1: Voltage Divider
        self.tab1 = ttk.Frame(self.notebook)
        self.notebook.add(self.tab1, text="Voltage Divider")
        self.setup_voltage_divider_tab(self.tab1)
        
        # Tab 2: Feedback Resistor
        self.tab2 = ttk.Frame(self.notebook)
        self.notebook.add(self.tab2, text="Feedback Resistor (DC/DC & LDO)")
        self.setup_feedback_tab(self.tab2)

    def setup_voltage_divider_tab(self, parent):
        # Instructions specific to this tab
        ttk.Label(parent, text="Enter any 3 values to calculate the missing one.\nChoose mode and resistor set.", 
                 justify=tk.CENTER).pack(pady=5)

        # Main Content Split (Left: Controls, Right: Schematic)
        content_frame = ttk.Frame(parent, padding="10")
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        left_frame = ttk.Frame(content_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        right_frame = ttk.Frame(content_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(10, 0))

        # --- Left Side: Controls ---
        
        # Mode Selection
        mode_frame = ttk.LabelFrame(left_frame, text="Mode Selection", padding="10")
        mode_frame.pack(fill=tk.X, pady=5)
        
        self.mode_var = tk.StringVar(value="E-Series")
        ttk.Radiobutton(mode_frame, text="E-Series Mode", variable=self.mode_var, 
                       value="E-Series", command=self.toggle_mode).pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(mode_frame, text="Resistor List Mode", variable=self.mode_var, 
                       value="Resistor List", command=self.toggle_mode).pack(side=tk.LEFT, padx=10)

        # Inputs Frame
        input_frame = ttk.LabelFrame(left_frame, text="Parameters", padding="10")
        input_frame.pack(fill=tk.X, pady=10)

        # Grid for inputs
        ttk.Label(input_frame, text="R1 (Ω):").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.r1_entry = ttk.Entry(input_frame)
        self.r1_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(input_frame, text="R2 (Ω):").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.r2_entry = ttk.Entry(input_frame)
        self.r2_entry.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(input_frame, text="Vin (V):").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.vin_entry = ttk.Entry(input_frame)
        self.vin_entry.grid(row=2, column=1, padx=5, pady=5)

        ttk.Label(input_frame, text="Vout (V):").grid(row=3, column=0, padx=5, pady=5, sticky=tk.W)
        self.vout_entry = ttk.Entry(input_frame)
        self.vout_entry.grid(row=3, column=1, padx=5, pady=5)

        # Mode Specific Options
        self.options_frame = ttk.LabelFrame(left_frame, text="Configuration", padding="10")
        self.options_frame.pack(fill=tk.X, pady=5)
        
        # E-Series specific
        self.series_frame = ttk.Frame(self.options_frame)
        ttk.Label(self.series_frame, text="Resistor Series:").pack(side=tk.LEFT, padx=5)
        self.series_var = tk.StringVar(value="E24")
        self.series_combo = ttk.Combobox(self.series_frame, textvariable=self.series_var, 
                                       values=["E24", "E48", "E96"], state="readonly")
        self.series_combo.pack(side=tk.LEFT, padx=5)
        
        # Resistor List specific
        self.list_frame = ttk.Frame(self.options_frame)
        
        # Input area for list
        input_subframe = ttk.Frame(self.list_frame)
        input_subframe.pack(fill=tk.X)
        
        ttk.Label(input_subframe, text="Add/Update List (comma sep):").pack(anchor=tk.W)
        self.res_list_entry = ttk.Entry(input_subframe)
        self.res_list_entry.pack(fill=tk.X, pady=2)
        self.res_list_entry.insert(0, "100, 220, 330, 470, 1000, 2200, 4700, 10000")
        
        ttk.Button(input_subframe, text="Update & Sort List", command=self.update_resistor_list_ui).pack(fill=tk.X, pady=2)
        
        # Scrollable area for checkboxes
        list_container = ttk.LabelFrame(self.list_frame, text="Select Resistors to Use")
        list_container.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.canvas_list = tk.Canvas(list_container, height=150)
        self.scrollbar_list = ttk.Scrollbar(list_container, orient="vertical", command=self.canvas_list.yview)
        self.scrollable_frame = ttk.Frame(self.canvas_list)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas_list.configure(scrollregion=self.canvas_list.bbox("all"))
        )
        
        self.canvas_list.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas_list.configure(yscrollcommand=self.scrollbar_list.set)
        
        self.canvas_list.pack(side="left", fill="both", expand=True)
        self.scrollbar_list.pack(side="right", fill="y")
        
        # Initial population
        self.update_resistor_list_ui()

        # Calculate Button
        ttk.Button(left_frame, text="Calculate", command=self.calculate).pack(pady=15)

        # Results
        result_frame = ttk.LabelFrame(left_frame, text="Results", padding="10")
        result_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.result_text = tk.Text(result_frame, height=10, width=40)
        self.result_text.pack(fill=tk.BOTH, expand=True)

        # --- Right Side: Schematic ---
        schematic_frame = ttk.LabelFrame(right_frame, text="Schematic", padding="10")
        schematic_frame.pack(fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(schematic_frame, width=250, height=400, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.draw_schematic()

        # Initialize view
        self.toggle_mode()

    def setup_feedback_tab(self, parent):
        # Instructions
        ttk.Label(parent, text="Calculate Feedback Resistors for DC/DC & LDO.\nFormula: Vout = Vfb * (1 + R1/R2)", 
                 justify=tk.CENTER).pack(pady=5)

        content_frame = ttk.Frame(parent, padding="10")
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        left_frame = ttk.Frame(content_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        right_frame = ttk.Frame(content_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(10, 0))

        # --- Left Side: Controls ---
        
        # Mode Selection
        mode_frame = ttk.LabelFrame(left_frame, text="Mode Selection", padding="10")
        mode_frame.pack(fill=tk.X, pady=5)
        
        self.fb_mode_var = tk.StringVar(value="E-Series")
        ttk.Radiobutton(mode_frame, text="E-Series Mode", variable=self.fb_mode_var, 
                       value="E-Series", command=self.toggle_fb_mode).pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(mode_frame, text="Resistor List Mode", variable=self.fb_mode_var, 
                       value="Resistor List", command=self.toggle_fb_mode).pack(side=tk.LEFT, padx=10)

        # Inputs Frame
        input_frame = ttk.LabelFrame(left_frame, text="Parameters", padding="10")
        input_frame.pack(fill=tk.X, pady=10)

        # Common Inputs
        ttk.Label(input_frame, text="Vout (Target) [V]:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.fb_vout_entry = ttk.Entry(input_frame)
        self.fb_vout_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(input_frame, text="Vfb (Reference) [V]:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.fb_vfb_entry = ttk.Entry(input_frame)
        self.fb_vfb_entry.grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(input_frame, text="Min Total R (Ω):").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.fb_min_total_entry = ttk.Entry(input_frame)
        self.fb_min_total_entry.grid(row=2, column=1, padx=5, pady=5)
        self.fb_min_total_entry.insert(0, "0")

        # E-Series Specific Inputs
        self.fb_eseries_input_frame = ttk.Frame(input_frame)
        self.fb_eseries_input_frame.grid(row=3, column=0, columnspan=2, sticky=tk.EW)
        
        ttk.Label(self.fb_eseries_input_frame, text="Known Resistor:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.fb_known_res_var = tk.StringVar(value="R1")
        res_select_frame = ttk.Frame(self.fb_eseries_input_frame)
        res_select_frame.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        ttk.Radiobutton(res_select_frame, text="R1", variable=self.fb_known_res_var, value="R1", command=self.update_fb_inputs).pack(side=tk.LEFT)
        ttk.Radiobutton(res_select_frame, text="R2", variable=self.fb_known_res_var, value="R2", command=self.update_fb_inputs).pack(side=tk.LEFT)

        self.fb_res_label = ttk.Label(self.fb_eseries_input_frame, text="R1 Value (Ω):")
        self.fb_res_label.grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.fb_res_entry = ttk.Entry(self.fb_eseries_input_frame)
        self.fb_res_entry.grid(row=1, column=1, padx=5, pady=5)

        # Configuration Frame
        self.fb_config_frame = ttk.LabelFrame(left_frame, text="Configuration", padding="10")
        self.fb_config_frame.pack(fill=tk.X, pady=5)
        
        # E-Series Config
        self.fb_series_frame = ttk.Frame(self.fb_config_frame)
        ttk.Label(self.fb_series_frame, text="Resistor Series:").pack(side=tk.LEFT, padx=5)
        self.fb_series_var = tk.StringVar(value="E24")
        self.fb_series_combo = ttk.Combobox(self.fb_series_frame, textvariable=self.fb_series_var, 
                                       values=["E24", "E48", "E96"], state="readonly")
        self.fb_series_combo.pack(side=tk.LEFT, padx=5)
        
        # List Config
        self.fb_list_frame = ttk.Frame(self.fb_config_frame)
        
        # Input area for list
        fb_input_subframe = ttk.Frame(self.fb_list_frame)
        fb_input_subframe.pack(fill=tk.X)
        
        ttk.Label(fb_input_subframe, text="Add/Update List (comma sep):").pack(anchor=tk.W)
        self.fb_res_list_entry = ttk.Entry(fb_input_subframe)
        self.fb_res_list_entry.pack(fill=tk.X, pady=2)
        self.fb_res_list_entry.insert(0, "100, 220, 330, 470, 1000, 2200, 4700, 10000")
        
        ttk.Button(fb_input_subframe, text="Update & Sort List", command=self.update_fb_resistor_list_ui).pack(fill=tk.X, pady=2)
        
        # Scrollable area for checkboxes
        fb_list_container = ttk.LabelFrame(self.fb_list_frame, text="Select Resistors to Use")
        fb_list_container.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.fb_canvas_list = tk.Canvas(fb_list_container, height=150)
        self.fb_scrollbar_list = ttk.Scrollbar(fb_list_container, orient="vertical", command=self.fb_canvas_list.yview)
        self.fb_scrollable_frame = ttk.Frame(self.fb_canvas_list)
        
        self.fb_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.fb_canvas_list.configure(scrollregion=self.fb_canvas_list.bbox("all"))
        )
        
        self.fb_canvas_list.create_window((0, 0), window=self.fb_scrollable_frame, anchor="nw")
        self.fb_canvas_list.configure(yscrollcommand=self.fb_scrollbar_list.set)
        
        self.fb_canvas_list.pack(side="left", fill="both", expand=True)
        self.fb_scrollbar_list.pack(side="right", fill="y")
        
        # Initial population
        self.update_fb_resistor_list_ui()

        # Calculate Button
        ttk.Button(left_frame, text="Calculate", command=self.calculate_feedback).pack(pady=15)

        # Results
        result_frame = ttk.LabelFrame(left_frame, text="Results", padding="10")
        result_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.fb_result_text = tk.Text(result_frame, height=10, width=40)
        self.fb_result_text.pack(fill=tk.BOTH, expand=True)

        # --- Right Side: Schematic ---
        schematic_frame = ttk.LabelFrame(right_frame, text="Schematic", padding="10")
        schematic_frame.pack(fill=tk.BOTH, expand=True)
        
        self.fb_canvas = tk.Canvas(schematic_frame, width=350, height=450, bg="white")
        self.fb_canvas.pack(fill=tk.BOTH, expand=True)
        self.draw_feedback_schematic()
        
        # Initialize view
        self.toggle_fb_mode()

    def toggle_fb_mode(self):
        mode = self.fb_mode_var.get()
        if mode == "E-Series":
            self.fb_list_frame.pack_forget()
            self.fb_series_frame.pack(fill=tk.X)
            self.fb_eseries_input_frame.grid(row=3, column=0, columnspan=2, sticky=tk.EW)
        else:
            self.fb_series_frame.pack_forget()
            self.fb_list_frame.pack(fill=tk.X)
            self.fb_eseries_input_frame.grid_remove()

    def update_fb_resistor_list_ui(self):
        # Clear existing
        for widget in self.fb_scrollable_frame.winfo_children():
            widget.destroy()
        self.fb_resistor_vars = []

        list_str = self.fb_res_list_entry.get()
        try:
            raw_values = [float(x.strip()) for x in list_str.split(',') if x.strip()]
            # Sort ascending
            raw_values.sort()
        except ValueError:
            messagebox.showerror("Error", "Invalid format in resistor list")
            return

        for val in raw_values:
            var = tk.BooleanVar(value=True)
            chk = ttk.Checkbutton(self.fb_scrollable_frame, text=f"{val} Ω", variable=var)
            chk.pack(anchor=tk.W)
            self.fb_resistor_vars.append((val, var))

    def update_fb_inputs(self):
        if self.fb_known_res_var.get() == "R1":
            self.fb_res_label.config(text="R1 Value (Ω):")
        else:
            self.fb_res_label.config(text="R2 Value (Ω):")

    def calculate_feedback(self):
        self.fb_result_text.delete(1.0, tk.END)
        
        vout = self.get_float(self.fb_vout_entry)
        vfb = self.get_float(self.fb_vfb_entry)
        min_total = self.get_float(self.fb_min_total_entry)
        
        if vout is None or vfb is None:
            self.fb_result_text.insert(tk.END, "Error: Please enter Vout and Vfb.")
            return

        if min_total is None:
            min_total = 0

        if vfb >= vout:
             self.fb_result_text.insert(tk.END, "Error: Vout must be greater than Vfb.")
             return

        mode = self.fb_mode_var.get()
        
        final_r1 = None
        final_r2 = None
        
        try:
            if mode == "E-Series":
                known_res_val = self.get_float(self.fb_res_entry)
                if known_res_val is None:
                    self.fb_result_text.insert(tk.END, "Error: Please enter the known resistor value.")
                    return
                if known_res_val <= 0:
                    self.fb_result_text.insert(tk.END, "Error: Resistor value must be positive.")
                    return

                series = self.fb_series_var.get()
                known_res_type = self.fb_known_res_var.get() # "R1" or "R2"
                
                calc_r1 = None
                calc_r2 = None
                
                if known_res_type == "R1":
                    # Vout = Vfb * (1 + R1/R2)  =>  Vout/Vfb - 1 = R1/R2  => R2 = R1 / (Vout/Vfb - 1)
                    r1 = known_res_val
                    calc_r2 = r1 / ((vout / vfb) - 1)
                    nearest_r2 = self.find_nearest_e_series(calc_r2, series)
                    
                    final_r1 = r1
                    final_r2 = nearest_r2
                    
                else: # Known is R2
                    # Vout = Vfb * (1 + R1/R2) => R1 = R2 * (Vout/Vfb - 1)
                    r2 = known_res_val
                    calc_r1 = r2 * ((vout / vfb) - 1)
                    nearest_r1 = self.find_nearest_e_series(calc_r1, series)
                    
                    final_r1 = nearest_r1
                    final_r2 = r2

                # Calculate actuals
                actual_vout = vfb * (1 + final_r1 / final_r2)
                error_v = actual_vout - vout
                error_pct = (error_v / vout) * 100
                total_r = final_r1 + final_r2
                
                result_str = (f"Mode: E-Series ({series})\n"
                              f"Fixed {known_res_type} = {known_res_val} Ω\n"
                              f"Calculated {'R2' if known_res_type == 'R1' else 'R1'} = {calc_r2 if known_res_type == 'R1' else calc_r1:.2f} Ω\n"
                              f"Nearest Standard {'R2' if known_res_type == 'R1' else 'R1'} = {final_r2 if known_res_type == 'R1' else final_r1:.2f} Ω\n\n"
                              f"Results:\n"
                              f"R1 = {final_r1:.2f} Ω\n"
                              f"R2 = {final_r2:.2f} Ω\n"
                              f"Total Resistance = {total_r:.2f} Ω\n"
                              f"Actual Vout = {actual_vout:.4f} V\n"
                              f"Error = {error_v:.4f} V ({error_pct:.2f}%)")
                
                if total_r < min_total:
                    result_str += f"\n\nWARNING: Total Resistance ({total_r:.2f} Ω) is below minimum ({min_total} Ω)!"

                self.fb_result_text.insert(tk.END, result_str)
                self.draw_feedback_schematic(final_r1, final_r2, vout, vfb)
            
            else: # Resistor List Mode
                resistors = [val for val, var in self.fb_resistor_vars if var.get()]
                
                if not resistors:
                    self.fb_result_text.insert(tk.END, "Error: No resistors selected.")
                    return

                best_r1 = None
                best_r2 = None
                min_diff = float('inf')
                
                for r1 in resistors:
                    for r2 in resistors:
                        if r1 + r2 < min_total: continue # Check min total constraint
                        
                        calc_vout = vfb * (1 + r1 / r2)
                        diff = abs(vout - calc_vout)
                        
                        if diff < min_diff:
                            min_diff = diff
                            best_r1 = r1
                            best_r2 = r2
                
                if best_r1 is not None:
                    actual_vout = vfb * (1 + best_r1 / best_r2)
                    error_v = actual_vout - vout
                    error_pct = (error_v / vout) * 100
                    total_r = best_r1 + best_r2
                    
                    result_str = (f"Mode: Resistor List\n"
                                f"Best Match from List:\n"
                                f"R1 = {best_r1} Ω\n"
                                f"R2 = {best_r2} Ω\n"
                                f"Total Resistance = {total_r:.2f} Ω\n"
                                f"Actual Vout = {actual_vout:.4f} V\n"
                                f"Error = {error_v:.4f} V ({error_pct:.2f}%)")
                    self.fb_result_text.insert(tk.END, result_str)
                    self.draw_feedback_schematic(best_r1, best_r2, vout, vfb)
                else:
                    self.fb_result_text.insert(tk.END, "Error: Could not find a valid combination satisfying constraints.")

        except ZeroDivisionError:
             self.fb_result_text.insert(tk.END, "Error: Division by zero.")
        except Exception as e:
             self.fb_result_text.insert(tk.END, f"Error: {str(e)}")

    def draw_feedback_schematic(self, r1=None, r2=None, vout=None, vfb=None):
        c = self.fb_canvas
        c.delete("all")
        w = 350
        h = 450
        cx = w // 2 - 20 # Shift slightly left to make room for right-side text
        
        # Styles
        line_width = 2
        res_width = 20
        res_height = 60
        
        # Points
        reg_top = 40
        reg_bot = 120
        reg_left = cx - 60
        reg_right = cx + 60
        
        r1_top = 160
        r1_bot = r1_top + res_height
        
        fb_node_y = 250
        
        r2_top = 280
        r2_bot = r2_top + res_height
        
        gnd_y = 380
        
        # Helper to format text
        def fmt(val, unit):
            return f"\n{val:.2f}{unit}" if val is not None else ""
        
        # Draw Regulator Box
        c.create_rectangle(reg_left, reg_top, reg_right, reg_bot, width=line_width)
        c.create_text(cx, (reg_top + reg_bot) // 2, text="LDO / DC-DC", font=("Arial", 10, "bold"))
        
        # Pin Coordinates
        vout_pin_y = reg_top + 20
        fb_pin_y = reg_bot - 20
        
        # Vout Pin (Right side of box)
        c.create_line(reg_right, vout_pin_y, cx + 100, vout_pin_y, width=line_width) # Out to right
        c.create_line(cx + 100, vout_pin_y, cx + 100, r1_top, width=line_width) # Down to R1
        c.create_text(reg_right - 5, vout_pin_y, text="VOUT", anchor=tk.E, font=("Arial", 8))
        
        # FB Pin (Right side of box, lower)
        c.create_line(reg_right, fb_pin_y, cx + 80, fb_pin_y, width=line_width) # Out to right
        c.create_line(cx + 80, fb_pin_y, cx + 80, fb_node_y, width=line_width) # Down to FB Node level
        c.create_line(cx + 80, fb_node_y, cx + 100, fb_node_y, width=line_width) # Connect to divider
        c.create_text(reg_right - 5, fb_pin_y, text="FB", anchor=tk.E, font=("Arial", 8))

        # Divider Chain (at x = cx + 100)
        div_x = cx + 100
        
        # R1
        c.create_rectangle(div_x - 10, r1_top, div_x + 10, r1_bot, fill="white", width=line_width)
        c.create_text(div_x + 15, (r1_top + r1_bot) // 2, text=f"R1{fmt(r1, 'Ω')}", anchor=tk.W, font=("Arial", 10, "bold"))
        
        # Wire R1 bot to R2 top (FB Node)
        c.create_line(div_x, r1_bot, div_x, r2_top, width=line_width)
        c.create_oval(div_x - 3, fb_node_y - 3, div_x + 3, fb_node_y + 3, fill="black") # Node dot
        
        # R2
        c.create_rectangle(div_x - 10, r2_top, div_x + 10, r2_bot, fill="white", width=line_width)
        c.create_text(div_x + 15, (r2_top + r2_bot) // 2, text=f"R2{fmt(r2, 'Ω')}", anchor=tk.W, font=("Arial", 10, "bold"))
        
        # GND
        c.create_line(div_x, r2_bot, div_x, gnd_y, width=line_width)
        c.create_line(div_x - 15, gnd_y, div_x + 15, gnd_y, width=line_width)
        c.create_line(div_x - 10, gnd_y + 5, div_x + 10, gnd_y + 5, width=line_width)
        c.create_line(div_x - 5, gnd_y + 10, div_x + 5, gnd_y + 10, width=line_width)
        
        # Labels
        c.create_text(div_x + 40, vout_pin_y, text=f"Vout{fmt(vout, 'V')}", anchor=tk.W, font=("Arial", 10, "bold"))
        c.create_text(div_x - 50, fb_node_y + 10, text=f"Vfb{fmt(vfb, 'V')}", anchor=tk.E, font=("Arial", 10, "bold"))
        
        # Formula
        c.create_text(w // 2, h - 20, text="Vout = Vfb * (1 + R1 / R2)", font=("Arial", 12, "italic"), fill="blue")

    def draw_schematic(self, r1=None, r2=None, vin=None, vout=None):
        c = self.canvas
        c.delete("all")
        w = 250
        h = 400
        cx = w // 2
        
        # Styles
        line_width = 2
        res_width = 20
        res_height = 60
        
        # Points
        top_y = 40
        r1_top = 80
        r1_bot = r1_top + res_height
        mid_y = 200
        r2_top = mid_y + 40
        r2_bot = r2_top + res_height
        gnd_y = 360
        
        # Helper to format text
        def fmt(val, unit):
            return f"\n{val:.2f}{unit}" if val is not None else ""
        
        # Draw Wires
        c.create_line(cx, top_y, cx, r1_top, width=line_width) # Vin to R1
        c.create_line(cx, r1_bot, cx, r2_top, width=line_width) # R1 to R2
        c.create_line(cx, r2_bot, cx, gnd_y, width=line_width) # R2 to Gnd
        
        # Draw Resistor 1
        c.create_rectangle(cx - res_width, r1_top, cx + res_width, r1_bot, fill="white", width=line_width)
        label_r1 = f"R1{fmt(r1, 'Ω')}"
        c.create_text(cx + res_width + 10, (r1_top + r1_bot) // 2, text=label_r1, anchor=tk.W, font=("Arial", 12, "bold"))
        
        # Draw Resistor 2
        c.create_rectangle(cx - res_width, r2_top, cx + res_width, r2_bot, fill="white", width=line_width)
        label_r2 = f"R2{fmt(r2, 'Ω')}"
        c.create_text(cx + res_width + 10, (r2_top + r2_bot) // 2, text=label_r2, anchor=tk.W, font=("Arial", 12, "bold"))
        
        # Draw Vin Label
        label_vin = f"Vin{fmt(vin, 'V')}"
        c.create_text(cx, top_y - 25, text=label_vin, font=("Arial", 12, "bold"), justify=tk.CENTER)
        c.create_oval(cx-3, top_y-3, cx+3, top_y+3, fill="black") # Dot
        
        # Draw Vout Tap
        c.create_line(cx, mid_y, cx + 60, mid_y, width=line_width)
        c.create_oval(cx + 60 - 3, mid_y - 3, cx + 60 + 3, mid_y + 3, fill="black") # Dot
        label_vout = f"Vout{fmt(vout, 'V')}"
        c.create_text(cx + 70, mid_y, text=label_vout, anchor=tk.W, font=("Arial", 12, "bold"))
        
        # Draw Ground
        c.create_line(cx - 20, gnd_y, cx + 20, gnd_y, width=line_width)
        c.create_line(cx - 12, gnd_y + 5, cx + 12, gnd_y + 5, width=line_width)
        c.create_line(cx - 4, gnd_y + 10, cx + 4, gnd_y + 10, width=line_width)

    def show_help(self):
        help_text = (
            "Voltage Divider Calculator Help\n\n"
            "Tab 1: Voltage Divider\n"
            "Theory: Vout = Vin * R2 / (R1 + R2)\n"
            "Modes:\n"
            "1. E-Series Mode: Enter any 3 values to find the 4th using standard resistors.\n"
            "2. Resistor List Mode: Find best pair from your list for target Vout.\n\n"
            "Tab 2: Feedback Resistor (DC/DC & LDO)\n"
            "Theory: Vout = Vfb * (1 + R1 / R2)\n"
            "Usage:\n"
            "- Enter Target Vout and Reference Vfb.\n"
            "- Choose one resistor (R1 or R2) to fix and enter its value.\n"
            "- Set Minimum Total Resistance (R1+R2) to limit current.\n"
            "- The tool calculates the other resistor using standard values."
        )
        messagebox.showinfo("Help / Info", help_text)

    def toggle_mode(self):
        mode = self.mode_var.get()
        if mode == "E-Series":
            self.list_frame.pack_forget()
            self.series_frame.pack(fill=tk.X)
            self.r1_entry.config(state='normal')
            self.r2_entry.config(state='normal')
        else:
            self.series_frame.pack_forget()
            self.list_frame.pack(fill=tk.X)
            self.r1_entry.delete(0, tk.END)
            self.r2_entry.delete(0, tk.END)
            self.r1_entry.config(state='disabled')
            self.r2_entry.config(state='disabled')

    def get_float(self, entry):
        val = entry.get().strip()
        if not val:
            return None
        try:
            return float(val)
        except ValueError:
            return None

    def find_nearest_e_series(self, value, series_name):
        if value <= 0:
            return value
        
        series = getattr(self, series_name.lower())
        
        # Normalize value to 1.0 - 9.99...
        exponent = math.floor(math.log10(value))
        mantissa = value / (10 ** exponent)
        
        # Find closest in series
        closest_mantissa = min(series, key=lambda x: abs(x - mantissa))
        
        return closest_mantissa * (10 ** exponent)

    def update_resistor_list_ui(self):
        # Clear existing
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.resistor_vars = []

        list_str = self.res_list_entry.get()
        try:
            raw_values = [float(x.strip()) for x in list_str.split(',') if x.strip()]
            # Sort ascending
            raw_values.sort()
        except ValueError:
            messagebox.showerror("Error", "Invalid format in resistor list")
            return

        for val in raw_values:
            var = tk.BooleanVar(value=True)
            chk = ttk.Checkbutton(self.scrollable_frame, text=f"{val} Ω", variable=var)
            chk.pack(anchor=tk.W)
            self.resistor_vars.append((val, var))

    def calculate(self):
        self.result_text.delete(1.0, tk.END)
        mode = self.mode_var.get()
        
        vin = self.get_float(self.vin_entry)
        vout = self.get_float(self.vout_entry)
        
        # Variables to hold final values for schematic
        final_r1 = None
        final_r2 = None
        final_vin = vin
        final_vout = vout
        
        if mode == "E-Series":
            r1 = self.get_float(self.r1_entry)
            r2 = self.get_float(self.r2_entry)
            
            inputs = [x for x in [r1, r2, vin, vout] if x is not None]
            if len(inputs) != 3:
                self.result_text.insert(tk.END, "Error: Please enter exactly 3 values.")
                return

            try:
                result_str = ""
                
                if vout is None:
                    calc_vout = vin * (r2 / (r1 + r2))
                    result_str = f"Calculated Vout = {calc_vout:.4f} V"
                    final_r1 = r1
                    final_r2 = r2
                    final_vout = calc_vout
                
                elif vin is None:
                    calc_vin = vout * (r1 + r2) / r2
                    result_str = f"Calculated Vin = {calc_vin:.4f} V"
                    final_r1 = r1
                    final_r2 = r2
                    final_vin = calc_vin
                
                elif r1 is None:
                    if vout == 0:
                         self.result_text.insert(tk.END, "Error: Vout cannot be 0 for R1 calculation.")
                         return
                    calc_r1 = r2 * (vin - vout) / vout
                    if calc_r1 < 0:
                        self.result_text.insert(tk.END, "Error: Calculated R1 is negative. Check voltages.")
                        return
                        
                    series = self.series_var.get()
                    nearest_r1 = self.find_nearest_e_series(calc_r1, series)
                    
                    result_str = (f"Calculated R1 = {calc_r1:.2f} Ω\n"
                                f"Nearest {series} Value = {nearest_r1:.2f} Ω\n\n"
                                f"Actual Vout with {nearest_r1:.2f} Ω = {vin * r2 / (nearest_r1 + r2):.4f} V")
                    final_r1 = nearest_r1
                    final_r2 = r2
                    final_vout = vin * r2 / (nearest_r1 + r2)

                elif r2 is None:
                    if vin == vout:
                        self.result_text.insert(tk.END, "Error: Vin equals Vout, implies R1=0 or R2=inf.")
                        return
                    calc_r2 = vout * r1 / (vin - vout)
                    if calc_r2 < 0:
                        self.result_text.insert(tk.END, "Error: Calculated R2 is negative. Check voltages.")
                        return
                        
                    series = self.series_var.get()
                    nearest_r2 = self.find_nearest_e_series(calc_r2, series)
                    
                    result_str = (f"Calculated R2 = {calc_r2:.2f} Ω\n"
                                f"Nearest {series} Value = {nearest_r2:.2f} Ω\n\n"
                                f"Actual Vout with {nearest_r2:.2f} Ω = {vin * nearest_r2 / (r1 + nearest_r2):.4f} V")
                    final_r1 = r1
                    final_r2 = nearest_r2
                    final_vout = vin * nearest_r2 / (r1 + nearest_r2)

                self.result_text.insert(tk.END, result_str)
                self.draw_schematic(final_r1, final_r2, final_vin, final_vout)

            except ZeroDivisionError:
                self.result_text.insert(tk.END, "Error: Division by zero.")
            except Exception as e:
                self.result_text.insert(tk.END, f"Error: {str(e)}")

        else: # Resistor List Mode
            if vin is None or vout is None:
                self.result_text.insert(tk.END, "Error: Please enter Vin and Vout.")
                return
            
            # Use filtered list
            resistors = [val for val, var in self.resistor_vars if var.get()]
                
            if not resistors:
                self.result_text.insert(tk.END, "Error: No resistors selected.")
                return

            best_r1 = None
            best_r2 = None
            min_diff = float('inf')
            
            for r1 in resistors:
                for r2 in resistors:
                    if r1 + r2 == 0: continue
                    
                    calc_vout = vin * r2 / (r1 + r2)
                    diff = abs(vout - calc_vout)
                    
                    if diff < min_diff:
                        min_diff = diff
                        best_r1 = r1
                        best_r2 = r2
            
            if best_r1 is not None:
                actual_vout = vin * best_r2 / (best_r1 + best_r2)
                result_str = (f"Best Match from List:\n"
                            f"R1 = {best_r1} Ω\n"
                            f"R2 = {best_r2} Ω\n"
                            f"Calculated Vout = {actual_vout:.4f} V\n"
                            f"Error = {min_diff:.4f} V")
                self.result_text.insert(tk.END, result_str)
                self.draw_schematic(best_r1, best_r2, vin, actual_vout)
            else:
                self.result_text.insert(tk.END, "Error: Could not find a valid combination.")

if __name__ == "__main__":
    root = tk.Tk()
    app = VoltageDividerApp(root)
    root.mainloop()
