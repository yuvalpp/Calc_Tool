import streamlit as st
import math
import schemdraw
import schemdraw.elements as elm
import matplotlib.pyplot as plt

# --- E-Series Data ---
E24 = [
    1.0, 1.1, 1.2, 1.3, 1.5, 1.6, 1.8, 2.0, 2.2, 2.4, 2.7, 3.0,
    3.3, 3.6, 3.9, 4.3, 4.7, 5.1, 5.6, 6.2, 6.8, 7.5, 8.2, 9.1
]
E48 = [
    1.00, 1.05, 1.10, 1.15, 1.21, 1.27, 1.33, 1.40, 1.47, 1.54, 1.62, 1.69,
    1.78, 1.87, 1.96, 2.05, 2.15, 2.26, 2.37, 2.49, 2.61, 2.74, 2.87, 3.01,
    3.16, 3.32, 3.48, 3.65, 3.83, 4.02, 4.22, 4.42, 4.64, 4.87, 5.11, 5.36,
    5.62, 5.90, 6.19, 6.49, 6.81, 7.15, 7.50, 7.87, 8.25, 8.66
]
E96 = [
    1.00, 1.02, 1.05, 1.07, 1.10, 1.13, 1.15, 1.18, 1.21, 1.24, 1.27, 1.30,
    1.33, 1.37, 1.40, 1.43, 1.47, 1.50, 1.54, 1.58, 1.62, 1.65, 1.69, 1.74,
    1.78, 1.82, 1.87, 1.91, 1.96, 2.00, 2.05, 2.10, 2.15, 2.21, 2.26, 2.32,
    2.37, 2.43, 2.49, 2.55, 2.61, 2.67, 2.74, 2.80, 2.87, 2.94, 3.01, 3.09,
    3.16, 3.24, 3.32, 3.40, 3.48, 3.57, 3.65, 3.74, 3.83, 3.92, 4.02, 4.12,
    4.22, 4.32, 4.42, 4.53, 4.64, 4.75, 4.87, 4.99, 5.11, 5.23, 5.36, 5.49,
    5.62, 5.76, 5.90, 6.04, 6.19, 6.34, 6.49, 6.65, 6.81, 6.98, 7.15, 7.32,
    7.50, 7.68, 7.87, 8.06, 8.25, 8.45, 8.66, 8.87, 9.09, 9.31, 9.53, 9.76
]

SERIES_DICT = {"E24": E24, "E48": E48, "E96": E96}

# --- Helper Functions ---
def find_nearest_e_series(value, series_name):
    if value <= 0:
        return value
    
    series = SERIES_DICT[series_name]
    
    exponent = math.floor(math.log10(value))
    mantissa = value / (10 ** exponent)
    
    closest_mantissa = min(series, key=lambda x: abs(x - mantissa))
    
    return closest_mantissa * (10 ** exponent)

def parse_resistor_list(list_str):
    try:
        return sorted([float(x.strip()) for x in list_str.split(',') if x.strip()])
    except ValueError:
        return []

def draw_voltage_divider(r1, r2, vin, vout):
    with schemdraw.Drawing() as d:
        d.config(unit=2.5)
        
        # Vin
        d += elm.Dot().label(f'Vin\n{vin:.2f}V' if vin else 'Vin', loc='left')
        
        # R1
        d += elm.Resistor().down().label(f'R1\n{r1:.2f}Ω' if r1 else 'R1')
        
        # Vout Tap
        d += elm.Line().right().length(1)
        d += elm.Dot().label(f'Vout\n{vout:.2f}V' if vout else 'Vout', loc='right')
        d += elm.Line().left().length(1) # Go back
        
        # R2
        d += elm.Resistor().down().label(f'R2\n{r2:.2f}Ω' if r2 else 'R2')
        
        # Ground
        d += elm.Ground()
        
        return d

def draw_feedback_schematic(r1, r2, vout, vfb):
    with schemdraw.Drawing() as d:
        d.config(unit=2.5)
        
        # Regulator Box (Abstract representation)
        # We'll just draw the pins coming out
        
        # Vout Pin
        d += elm.Line().right().length(1).label('Vout Pin', loc='left')
        d += elm.Dot().label(f'Vout\n{vout:.2f}V' if vout else 'Vout', loc='top')
        
        # R1
        d += elm.Resistor().down().label(f'R1\n{r1:.2f}Ω' if r1 else 'R1')
        
        # FB Node
        d += elm.Dot()
        d.push()
        d += elm.Line().left().length(1).label('FB Pin', loc='left')
        d += elm.Label().label(f'Vfb\n{vfb:.2f}V' if vfb else 'Vfb', loc='left')
        d.pop()
        
        # R2
        d += elm.Resistor().down().label(f'R2\n{r2:.2f}Ω' if r2 else 'R2')
        
        # Ground
        d += elm.Ground()
        
        return d

# --- Main App ---
st.set_page_config(page_title="Yuval Tool Rev 1.12", layout="wide")
st.title("Yuval Tool Rev 1.12")

tab1, tab2 = st.tabs(["Voltage Divider", "Feedback Resistor (DC/DC & LDO)"])

# --- Tab 1: Voltage Divider ---
with tab1:
    st.header("Voltage Divider Calculator")
    st.write("Enter any 3 values to calculate the missing one.")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        mode = st.radio("Mode", ["E-Series", "Resistor List"], horizontal=True, key="vd_mode")
        
        with st.form("vd_form"):
            r1_input = st.text_input("R1 (Ω)")
            r2_input = st.text_input("R2 (Ω)")
            vin_input = st.text_input("Vin (V)")
            vout_input = st.text_input("Vout (V)")
            
            if mode == "E-Series":
                series = st.selectbox("Resistor Series", ["E24", "E48", "E96"], key="vd_series")
            else:
                res_list_str = st.text_area("Resistor List (comma sep)", "100, 220, 330, 470, 1000, 2200, 4700, 10000")
                
            submitted = st.form_submit_button("Calculate")
            
    with col2:
        if submitted:
            # Parse inputs
            r1 = float(r1_input) if r1_input else None
            r2 = float(r2_input) if r2_input else None
            vin = float(vin_input) if vin_input else None
            vout = float(vout_input) if vout_input else None
            
            final_r1, final_r2, final_vin, final_vout = r1, r2, vin, vout
            
            if mode == "E-Series":
                inputs = [x for x in [r1, r2, vin, vout] if x is not None]
                if len(inputs) != 3:
                    st.error("Please enter exactly 3 values.")
                else:
                    try:
                        if vout is None:
                            final_vout = vin * (r2 / (r1 + r2))
                            st.success(f"Calculated Vout = {final_vout:.4f} V")
                        elif vin is None:
                            final_vin = vout * (r1 + r2) / r2
                            st.success(f"Calculated Vin = {final_vin:.4f} V")
                        elif r1 is None:
                            calc_r1 = r2 * (vin - vout) / vout
                            nearest_r1 = find_nearest_e_series(calc_r1, series)
                            final_r1 = nearest_r1
                            final_vout = vin * r2 / (nearest_r1 + r2)
                            st.success(f"Calculated R1 = {calc_r1:.2f} Ω")
                            st.info(f"Nearest {series} = {nearest_r1:.2f} Ω")
                            st.write(f"Actual Vout = {final_vout:.4f} V")
                        elif r2 is None:
                            calc_r2 = vout * r1 / (vin - vout)
                            nearest_r2 = find_nearest_e_series(calc_r2, series)
                            final_r2 = nearest_r2
                            final_vout = vin * nearest_r2 / (r1 + nearest_r2)
                            st.success(f"Calculated R2 = {calc_r2:.2f} Ω")
                            st.info(f"Nearest {series} = {nearest_r2:.2f} Ω")
                            st.write(f"Actual Vout = {final_vout:.4f} V")
                    except Exception as e:
                        st.error(f"Error: {e}")
            
            else: # Resistor List Mode
                if vin is None or vout is None:
                    st.error("Please enter Vin and Vout.")
                else:
                    resistors = parse_resistor_list(res_list_str)
                    if not resistors:
                        st.error("Invalid resistor list.")
                    else:
                        best_r1, best_r2 = None, None
                        min_diff = float('inf')
                        
                        for r1_val in resistors:
                            for r2_val in resistors:
                                if r1_val + r2_val == 0: continue
                                calc_vout = vin * r2_val / (r1_val + r2_val)
                                diff = abs(vout - calc_vout)
                                if diff < min_diff:
                                    min_diff = diff
                                    best_r1, best_r2 = r1_val, r2_val
                        
                        if best_r1:
                            final_r1, final_r2 = best_r1, best_r2
                            final_vout = vin * best_r2 / (best_r1 + best_r2)
                            st.success(f"Best Match: R1={best_r1}Ω, R2={best_r2}Ω")
                            st.write(f"Actual Vout = {final_vout:.4f} V")
                        else:
                            st.error("Could not find valid combination.")

            # Draw Schematic
            figure = draw_voltage_divider(final_r1, final_r2, final_vin, final_vout).draw()
            st.pyplot(figure.fig)
        else:
             figure = draw_voltage_divider(None, None, None, None).draw()
             st.pyplot(figure.fig)

# --- Tab 2: Feedback Resistor ---
with tab2:
    st.header("Feedback Resistor Calculator (DC/DC & LDO)")
    st.write("Formula: Vout = Vfb * (1 + R1/R2)")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        fb_mode = st.radio("Mode", ["E-Series", "Resistor List"], horizontal=True, key="fb_mode")
        
        with st.form("fb_form"):
            fb_vout = st.number_input("Target Vout (V)", min_value=0.0, step=0.1)
            fb_vfb = st.number_input("Reference Vfb (V)", min_value=0.0, step=0.01)
            fb_min_total = st.number_input("Min Total R (Ω)", min_value=0.0, step=100.0)
            
            if fb_mode == "E-Series":
                fb_series = st.selectbox("Resistor Series", ["E24", "E48", "E96"], key="fb_series")
                fb_known = st.radio("Known Resistor", ["R1", "R2"], horizontal=True)
                fb_res_val = st.number_input(f"Value for {fb_known} (Ω)", min_value=0.0, step=100.0)
            else:
                fb_res_list_str = st.text_area("Resistor List (comma sep)", "100, 220, 330, 470, 1000, 2200, 4700, 10000", key="fb_list")
                
            fb_submitted = st.form_submit_button("Calculate")
            
    with col2:
        if fb_submitted:
            final_r1, final_r2 = None, None
            
            if fb_vout <= fb_vfb:
                 st.error("Vout must be greater than Vfb.")
            else:
                if fb_mode == "E-Series":
                    if fb_res_val <= 0:
                        st.error("Resistor value must be positive.")
                    else:
                        if fb_known == "R1":
                            r1 = fb_res_val
                            calc_r2 = r1 / ((fb_vout / fb_vfb) - 1)
                            nearest_r2 = find_nearest_e_series(calc_r2, fb_series)
                            final_r1, final_r2 = r1, nearest_r2
                        else:
                            r2 = fb_res_val
                            calc_r1 = r2 * ((fb_vout / fb_vfb) - 1)
                            nearest_r1 = find_nearest_e_series(calc_r1, fb_series)
                            final_r1, final_r2 = nearest_r1, r2
                            
                        actual_vout = fb_vfb * (1 + final_r1 / final_r2)
                        st.success(f"Calculated {'R2' if fb_known == 'R1' else 'R1'}: {calc_r2 if fb_known == 'R1' else calc_r1:.2f} Ω")
                        st.info(f"Nearest Standard: {final_r2 if fb_known == 'R1' else final_r1:.2f} Ω")
                        st.write(f"Actual Vout: {actual_vout:.4f} V")
                        
                else: # Resistor List
                    resistors = parse_resistor_list(fb_res_list_str)
                    best_r1, best_r2 = None, None
                    min_diff = float('inf')
                    
                    for r1 in resistors:
                        for r2 in resistors:
                            if r1 + r2 < fb_min_total: continue
                            calc_vout = fb_vfb * (1 + r1 / r2)
                            diff = abs(fb_vout - calc_vout)
                            if diff < min_diff:
                                min_diff = diff
                                best_r1, best_r2 = r1, r2
                                
                    if best_r1:
                        final_r1, final_r2 = best_r1, best_r2
                        actual_vout = fb_vfb * (1 + final_r1 / final_r2)
                        st.success(f"Best Match: R1={best_r1}Ω, R2={best_r2}Ω")
                        st.write(f"Actual Vout: {actual_vout:.4f} V")
                    else:
                        st.error("No valid combination found.")
            
            # Draw Schematic
            figure = draw_feedback_schematic(final_r1, final_r2, fb_vout, fb_vfb).draw()
            st.pyplot(figure.fig)
        else:
             figure = draw_feedback_schematic(None, None, None, None).draw()
             st.pyplot(figure.fig)
