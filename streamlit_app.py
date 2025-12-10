import streamlit as st
import numpy as np
import math
import schemdraw
import schemdraw.elements as elm
import matplotlib.pyplot as plt
import io
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import urllib.parse

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
def format_eng(value):
    """Formats a number in engineering notation (m, k, M, G)."""
    if value == 0:
        return "0"
    
    abs_val = abs(value)
    if abs_val < 1e-9: # Too small, just return as is or 0
        return f"{value:.4g}"
        
    exp = math.floor(math.log10(abs_val))
    eng_exp = exp - (exp % 3)
    
    # Clamp to supported range if needed
    suffixes = {
        -12: "p", -9: "n", -6: "u", -3: "m", 
        0: "", 
        3: "k", 6: "M", 9: "G", 12: "T"
    }
    
    if eng_exp in suffixes:
        mantissa = value / (10 ** eng_exp)
        return f"{mantissa:.4g}{suffixes[eng_exp]}"
    else:
        return f"{value:.4e}"

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

def generate_e_series_range(series_name, min_val=10.0, max_val=1000000.0):
    """Generates a full list of E-series resistors within a range."""
    series = SERIES_DICT[series_name]
    result = []
    
    start_exp = math.floor(math.log10(min_val))
    end_exp = math.ceil(math.log10(max_val))
    
    for exponent in range(start_exp, end_exp + 1):
        for mantissa in series:
            val = mantissa * (10 ** exponent)
            if min_val <= val <= max_val:
                result.append(val)
                
    return sorted(list(set(result)))

def draw_voltage_divider(r1, r2, vin, vout):
    with schemdraw.Drawing() as d:
        d.config(unit=2.0, fontsize=12, lw=2)
        
        # Vin
        d += elm.Dot().label(f'Vin\n{vin:.2f}V' if vin else 'Vin', loc='left')
        
        # R1
        d += elm.Resistor().down().label(f'R1\n{r1:.2f}Ω' if r1 else 'R1')
        
        # Vout Tap
        d += elm.Line().right().length(1.5)
        d += elm.Dot().label(f'Vout\n{vout:.2f}V' if vout else 'Vout', loc='right')
        d += elm.Line().left().length(1.5)
        
        # R2
        d += elm.Resistor().down().label(f'R2\n{r2:.2f}Ω' if r2 else 'R2')
        
        # Ground
        d += elm.Ground()
        
        return d

def draw_feedback_schematic(r1, r2, vout, vfb):
    with schemdraw.Drawing() as d:
        d.config(unit=2.0, fontsize=12, lw=2)
        
        # Vout Pin
        d += elm.Line().right().length(1.5).label('Vout Pin', loc='left')
        d += elm.Dot().label(f'Vout\n{vout:.2f}V' if vout else 'Vout', loc='top')
        
        # R1
        d += elm.Resistor().down().label(f'R1\n{r1:.2f}Ω' if r1 else 'R1')
        
        # FB Node
        d += elm.Dot()
        d.push()
        d += elm.Line().left().length(1.5)
        d += elm.Label().label(f'Vfb\n{vfb:.2f}V' if vfb else 'Vfb', loc='left')
        d.pop()
        
        # R2
        d += elm.Resistor().down().label(f'R2\n{r2:.2f}Ω' if r2 else 'R2')
        
        # Ground
        d += elm.Ground()
        
        return d

# --- Constants ---
APP_VERSION = "Rev 2.2"

# --- Near Field Helper Function ---
def calculate_near_field(d_aperture, wavelength):
    """Calculates near field boundary."""
    # Fraunhofer distance: 2 * D^2 / lambda
    r_ff = (2 * (d_aperture ** 2)) / wavelength
    return r_ff

# --- Main App ---
st.set_page_config(page_title="Yuval HW Tool", layout="wide")
st.title("Yuval HW Tool")

# --- Custom CSS for Styling ---
st.markdown(
    """
    <style>
    /* Target the main navigation radio button group by its label "Go to" */
    div[role="radiogroup"][aria-label="Go to"] {
        background-color: #f0f2f6; /* Light gray background for the container */
        padding: 10px;
        border-radius: 10px;
        border: 1px solid #d6d6d8;
    }
    
    div[role="radiogroup"][aria-label="Go to"] label {
        background-color: #ffffff !important;
        padding: 8px 16px !important;
        border-radius: 5px !important;
        margin-right: 8px !important;
        border: 1px solid #e0e0e0 !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05) !important;
    }

    div[role="radiogroup"][aria-label="Go to"] label:hover {
        background-color: #e6f7ff !important; /* Light blue on hover */
        border-color: #1890ff !important;
    }
    
    div[role="radiogroup"][aria-label="Go to"] p {
        font-weight: bold !important;
        font-size: 16px !important;
        color: #333333 !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Main Navigation ---
# st.title("Yuval HW Tool") # Already there
selected_tool = st.radio(
    "Go to",
    ["Voltage Divider", "Feedback Resistor", "dB Calculator", "RADAR Calculator"],
    horizontal=True
)
st.sidebar.markdown(f"**Version:** {APP_VERSION}")

# --- Dynamic Sidebar Help ---
st.sidebar.markdown("---")
st.sidebar.header("Help / Info")

if selected_tool == "Voltage Divider":
    st.sidebar.info(
        r"""
        **Voltage Divider Calculator**
        
        *Theory*: $V_{out} = V_{in} \times \frac{R_2}{R_1 + R_2}$
        
        **Modes**:
        1. **E-Series Mode**: Enter any 3 values to find the 4th using standard resistors.
        2. **Resistor List Mode**: Find best pair from your list for target Vout.
        """
    )
elif selected_tool == "Feedback Resistor":
    st.sidebar.info(
        r"""
        **Feedback Resistor (DC/DC & LDO)**
        
        *Theory*: $V_{out} = V_{fb} \times (1 + \frac{R_1}{R_2})$
        
        **Usage**:
        - Enter Target Vout and Reference Vfb.
        - Set **Min/Max Resistor Values** to constrain the search.
        - **Calculation Method**:
            - **Fix One Resistor**: You specify R1 or R2, tool finds the other.
            - **Find Best Pair**: Tool searches for the best pair (closest Vout) within limits.
        """
    )
elif selected_tool == "dB Calculator":
    st.sidebar.info(
        r"""
        **dB Calculator**
        
        - **Ratio to dB**: Convert Power or Voltage ratios to dB.
        - **Power Conversion**: dBm $\leftrightarrow$ mW.
        - **Voltage Conversion**: dB $\leftrightarrow$ V/mV/uV.
        """
    )
elif selected_tool == "RADAR Calculator":
    st.sidebar.info(
        r"""
        **RADAR Calculator**
        
        **Near Field Calculator**
        - Calculate boundary $R_{FF} = 2D^2/\lambda$.
        
        **FMCW Range Resolver**
        - Calculate Range from Beat Frequency.
        - $R = \frac{c \cdot f_{beat}}{2 \cdot S}$
        
        **AWR2243 Chirp Designer**
        - Design chirp parameters for TI AWR2243.
        - Calculates Bandwidth, Resolution, Max Range.
        
        **T-Shape Array Visualizer**
        - Visualize T-Shape virtual arrays.
        - Fixed aperture vs. Fixed element modes.
        - (Password Protected)
        
        **Monostatic Power Budget**
        - General Radar Equation SNR.
        - Editable Link Budget & Loss Tables.
        - Explicit Formulas ($P_t$, $RCS$, $T_{sys}$).
        """
    )

st.sidebar.markdown("---")
st.sidebar.write("**Contact**: uv.peleg@gmail.com")
st.sidebar.write(f"**{APP_VERSION}**")


# --- Tool Logic ---

if selected_tool == "Voltage Divider":
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

            figure = draw_voltage_divider(final_r1, final_r2, final_vin, final_vout).draw()
            st.pyplot(figure.fig, dpi=150)
        else:
             figure = draw_voltage_divider(None, None, None, None).draw()
             st.pyplot(figure.fig, dpi=150)

elif selected_tool == "Feedback Resistor":
    st.header("Feedback Resistor Calculator (DC/DC & LDO)")
    st.write("Formula: Vout = Vfb * (1 + R1/R2)")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        fb_mode = st.radio("Mode", ["E-Series", "Resistor List"], horizontal=True, key="fb_mode")
        
        with st.form("fb_form"):
            fb_vout = st.number_input("Target Vout (V)", min_value=0.0, step=0.1)
            fb_vfb = st.number_input("Reference Vfb (V)", min_value=0.0, step=0.01)
            
            st.markdown("### Constraints")
            c1, c2 = st.columns(2)
            with c1:
                fb_r_min = st.number_input("Min Resistor (Ω)", min_value=0.0, value=10.0, step=10.0)
            with c2:
                fb_r_max = st.number_input("Max Resistor (Ω)", min_value=0.0, value=1000000.0, step=1000.0)
            
            fb_calc_method = "Find Best Pair"
            fb_known = None
            fb_res_val = None
            fb_series = "E24"
            fb_res_list_str = ""
            
            if fb_mode == "E-Series":
                fb_series = st.selectbox("Resistor Series", ["E24", "E48", "E96"], key="fb_series")
                fb_calc_method = st.radio("Calculation Method", ["Fix One Resistor", "Find Best Pair"], horizontal=True)
                if fb_calc_method == "Fix One Resistor":
                    fb_known = st.radio("Known Resistor", ["R1", "R2"], horizontal=True)
                    fb_res_val = st.number_input(f"Value for {fb_known} (Ω)", min_value=0.0, step=100.0)
            else:
                fb_res_list_str = st.text_area("Resistor List (comma sep)", "100, 220, 330, 470, 1000, 2200, 4700, 10000", key="fb_list")
                fb_calc_method = "Find Best Pair"
                
            fb_submitted = st.form_submit_button("Calculate")
            
    with col2:
        if fb_submitted:
            final_r1, final_r2 = None, None
            
            if fb_vout <= fb_vfb:
                 st.error("Vout must be greater than Vfb.")
            elif fb_r_min > fb_r_max:
                st.error("Min Resistor value cannot be greater than Max Resistor value.")
            else:
                if fb_calc_method == "Fix One Resistor":
                    if fb_res_val <= 0:
                        st.error("Resistor value must be positive.")
                    elif not (fb_r_min <= fb_res_val <= fb_r_max):
                        st.error(f"Known resistor value {fb_res_val} Ω is outside limits [{fb_r_min}, {fb_r_max}].")
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
                            
                        calculated_res = final_r2 if fb_known == "R1" else final_r1
                        if not (fb_r_min <= calculated_res <= fb_r_max):
                             st.warning(f"Calculated resistor {calculated_res} Ω is outside limits [{fb_r_min}, {fb_r_max}].")

                        actual_vout = fb_vfb * (1 + final_r1 / final_r2)
                        st.success(f"Calculated {'R2' if fb_known == 'R1' else 'R1'}: {calc_r2 if fb_known == 'R1' else calc_r1:.2f} Ω")
                        st.info(f"Nearest Standard: {final_r2 if fb_known == 'R1' else final_r1:.2f} Ω")
                        st.write(f"Actual Vout: {actual_vout:.4f} V")

                else:
                    candidates = []
                    if fb_mode == "E-Series":
                        candidates = generate_e_series_range(fb_series, fb_r_min, fb_r_max)
                    else:
                        raw_list = parse_resistor_list(fb_res_list_str)
                        candidates = [r for r in raw_list if fb_r_min <= r <= fb_r_max]
                    
                    if not candidates:
                        st.error(f"No resistor candidates available in range [{fb_r_min}, {fb_r_max}].")
                    else:
                        best_r1, best_r2 = None, None
                        min_error = float('inf')
                        
                        for r1 in candidates:
                            for r2 in candidates:
                                calc_vout = fb_vfb * (1 + r1 / r2)
                                error = abs(calc_vout - fb_vout)
                                
                                if error < min_error:
                                    min_error = error
                                    best_r1, best_r2 = r1, r2
                        
                        if best_r1:
                            final_r1, final_r2 = best_r1, best_r2
                            actual_vout = fb_vfb * (1 + final_r1 / final_r2)
                            error_pct = (min_error / fb_vout) * 100
                            
                            st.success(f"Best Match: R1={best_r1}Ω, R2={best_r2}Ω")
                            st.write(f"Actual Vout: {actual_vout:.4f} V (Error: {error_pct:.2f}%)")
                        else:
                            st.error("No valid combination found.")

            figure = draw_feedback_schematic(final_r1, final_r2, fb_vout, fb_vfb).draw()
            st.pyplot(figure.fig, dpi=150)
        else:
             figure = draw_feedback_schematic(None, None, None, None).draw()
             st.pyplot(figure.fig, dpi=150)

elif selected_tool == "dB Calculator":
    st.header("dB Calculator")
    st.markdown("Convert Power and Voltage between dB and Linear scales.")
    
    # --- Ratio to dB (Moved to Top) ---
    st.subheader("Ratio to dB Calculator")
    
    col_r1, col_r2 = st.columns(2)
    with col_r1:
        ratio_mode = st.radio("Ratio Type", ["Power Ratio", "Voltage Ratio"], horizontal=True)
        
    with col_r2:
        val1 = st.number_input("Value 1", value=10.0, format="%.4f")
        val2 = st.number_input("Value 2 (Reference)", value=1.0, format="%.4f")
        
    if val1 > 0 and val2 > 0:
        ratio = val1 / val2
        if ratio_mode == "Power Ratio":
            db_val = 10 * math.log10(ratio)
            st.latex(r"dB = 10 \cdot \log_{10}\left(\frac{P_1}{P_2}\right)")
        else:
            db_val = 20 * math.log10(ratio)
            st.latex(r"dB = 20 \cdot \log_{10}\left(\frac{V_1}{V_2}\right)")
            
        st.success(f"Ratio ({val1:.4f} / {val2:.4f}) = **{db_val:.4f} dB**")
    else:
        if val2 == 0:
            st.error("Reference value (Value 2) cannot be zero.")
        elif val1 <= 0:
             st.error("Value 1 must be positive for log calculation.")
             
    st.markdown("---")
    
    # --- Conversions ---
    col_db1, col_db2 = st.columns(2)
    
    with col_db1:
        st.subheader("Power Conversion")
        st.latex(r"P_{dBm} = 10 \cdot \log_{10}(P_{mW})")
        st.latex(r"P_{mW} = 10^{(P_{dBm}/10)}")
        
        p_mode = st.radio("Convert Power:", ["dBm to mW", "mW to dBm"], horizontal=True)
        if p_mode == "dBm to mW":
            p_val = st.number_input("Power (dBm)", value=0.0)
            p_res_mw = 10 ** (p_val / 10)
            st.success(f"{p_val} dBm = **{format_eng(p_res_mw / 1000.0)}W**")
        else:
            p_val_mw = st.number_input("Power (mW)", value=1.0, min_value=1e-12, format="%.4f")
            if p_val_mw > 0:
                p_res_dbm = 10 * math.log10(p_val_mw)
                st.success(f"{format_eng(p_val_mw / 1000.0)}W = **{p_res_dbm:.4f} dBm**")
            else:
                st.error("Power must be > 0")

    with col_db2:
        st.subheader("Voltage Conversion")
        st.latex(r"V_{dB\mu V} = 20 \cdot \log_{10}(V_{\mu V})")
        st.latex(r"V_{\mu V} = 10^{(V_{dB\mu V}/20)}")
        
        v_mode = st.radio("Convert Voltage:", ["dB to Linear", "Linear to dB"], horizontal=True)
        
        v_unit = st.selectbox("Voltage Unit", ["V", "mV", "uV"])
        
        if v_mode == "dB to Linear":
            v_val_db = st.number_input(f"Voltage (dB{v_unit})", value=60.0)
            v_res_lin = 10 ** (v_val_db / 20)
            st.success(f"{v_val_db} dB{v_unit} = **{format_eng(v_res_lin)}{v_unit}**")
        else:
            v_val_lin = st.number_input(f"Voltage ({v_unit})", value=1.0, min_value=1e-12, format="%.4f")
            if v_val_lin > 0:
                v_res_db = 20 * math.log10(v_val_lin)
                st.success(f"{format_eng(v_val_lin)}{v_unit} = **{v_res_db:.4f} dB{v_unit}**")
            else:
                st.error("Voltage must be > 0")

elif selected_tool == "RADAR Calculator":
    st.header("RADAR Calculator")
    
    radar_tool = st.radio("Select Tool", ["Near Field Calculator", "FMCW Range Resolver", "AWR2243 Chirp Designer", "T-Shape Array Visualizer", "Monostatic Power Budget Calculator"], horizontal=True)
    
    if radar_tool == "Near Field Calculator":
        st.subheader("Near Field Calculator")
        st.markdown("Calculate the Near Field (Fresnel) to Far Field (Fraunhofer) boundary distance.")
        
        col_nf1, col_nf2 = st.columns([1, 1])
        
        with col_nf1:
            d_ant = st.number_input("Antenna Size D (m)", value=0.1, min_value=0.001, format="%.4f")
            
            # Using 77 GHz for calculation as logic implies or generic lambda
            # "Logic: Calculate R = 2 D^2 / lambda (Use 77 GHz)" - Use 77GHz fixed?
            # Prompt says "Use 77 GHz". So we default to that or just use it.
            # But the existing tool had "Input Mode" for Wavelength vs Freq.
            # The prompt says: "Input: Antenna size (D) in meters. Logic: Calculate R = 2 D^2 / lambda (Use 77 GHz)."
            # This sounds like a simplified tool.
            # However, "Maintain Existing" usually implies keeping the existing UI if it works.
            # But "Logic ... (Use 77 GHz)" suggests simplification.
            # I will stick to "Maintain Existing" for features but ensure 77GHz is default/used if user doesn't specify.
            # Actually, "Maintain Existing" is strong. I'll keep the flexibility but ensure 77GHz is the default.
            
            freq_val = 77.0
            wavelength = 3e8 / (freq_val * 1e9)
            
            st.write(f"Frequency: **{freq_val} GHz** (Fixed for this tool based on Rev 2 Spec if strictly followed, else keep flexible)")
            # Let's keep it simple as per prompt "Input: Antenna Size (D)". Logic: Use 77GHz.
            # So I will remove the frequency input to match "Input: Antenna Size" strictly.
            
            r_ff = (2 * d_ant**2) / wavelength
            
            st.latex(r"R_{FF} = \frac{2 D^2}{\lambda}")
            st.success(f"**Near Field Boundary:** {r_ff:.4f} m")
            st.info(f"**In Kilometers:** {r_ff/1000:.6f} km")
                
        with col_nf2:
            try:
                st.image("near_field_diagram.png", caption="Near Field vs Far Field")
            except:
                st.warning("Image not found.")
                
    elif radar_tool == "FMCW Range Resolver":
        st.subheader("FMCW Range Resolver")
        st.markdown("Calculate Range from Beat Frequency and Chirp Slope.")
        
        col_fmcw1, col_fmcw2 = st.columns([1, 1])
        
        with col_fmcw1:
            # Inputs: Chirp Slope & Beat Freq
            slope = st.number_input("Chirp Slope (MHz/us)", value=29.98, min_value=0.001, format="%.4f")
            f_beat_mhz = st.number_input("Beat Frequency (MHz)", value=10.0, min_value=0.0, format="%.4f")
            
            if slope > 0:
                c_speed = 300.0 # m/us for MHz/us units
                range_m = (c_speed * f_beat_mhz) / (2 * slope)
                
                st.latex(r"R = \frac{c \cdot f_{beat}}{2 \cdot S}")
                st.success(f"**Calculated Range:** {range_m:.4f} m")
                
                # Visualization
                f_max = f_beat_mhz * 2 if f_beat_mhz > 0 else 20.0
                f_vals = np.linspace(0, f_max, 100)
                r_vals = (c_speed * f_vals) / (2 * slope)
                
                df = pd.DataFrame({"Beat Frequency (MHz)": f_vals, "Range (m)": r_vals})
                
                fig = px.line(df, x="Beat Frequency (MHz)", y="Range (m)", title="Range vs Beat Frequency")
                fig.add_scatter(x=[f_beat_mhz], y=[range_m], mode='markers', marker=dict(size=10, color='red'), name='Current Point')
                
                with col_fmcw2:
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.error("Slope must be positive.")

    elif radar_tool == "AWR2243 Chirp Designer":
        st.subheader("AWR2243 Chirp Designer")
        st.markdown("Design and analyze a single chirp for TI AWR2243.")

        # --- Input Panel ---
        with st.container():
            st.markdown("#### Chirp Parameters")
            col_in1, col_in2, col_in3 = st.columns(3)
            
            with col_in1:
                slope = st.number_input("Slope (MHz/µs)", value=150.0, min_value=0.1, format="%.3f", help="Chirp slope in MHz/µs")
                adc_sampling = st.number_input("ADC sampling (Msps)", value=22.5, min_value=0.1, format="%.2f", help="Complex output sampling rate")
            
            with col_in2:
                sampling_mode = st.selectbox("Sampling mode", ["complex_1x", "complex_2x", "real"], index=2)
                n_samples = st.number_input("Number of samples per chirp", value=450, min_value=1, step=1)
                
            with col_in3:
                c_speed = st.number_input("Speed of light c (m/s)", value=3e8, format="%.2e")

        # --- Calculations ---
        # Unit conversions
        S = slope * 1e12 # Hz/s
        Fs = adc_sampling * 1e6 # Hz
        
        # Chirp duration
        if Fs > 0:
            T_chirp = n_samples / Fs # seconds
        else:
            T_chirp = 0
            
        # Effective bandwidth
        BW = S * T_chirp # Hz
        
        # Range resolution
        if BW > 0:
            dR = c_speed / (2 * BW) # meters
        else:
            dR = 0
            
        # FFT bin spacing
        if n_samples > 0:
            df = Fs / n_samples # Hz
        else:
            df = 0
            
        # AWR2243 IF / FIR bandwidth logic
        if sampling_mode == "complex_1x":
            if_max_mode = 0.9 * Fs
            mode_desc = "0.9 × Fs"
        else: # complex_2x or real
            if_max_mode = 0.9 * Fs / 2
            mode_desc = "0.9 × Fs / 2"
            
        if_device_limit = 20e6 # 20 MHz
        if_max = min(if_max_mode, if_device_limit)
        
        # Max range limits
        # ADC Nyquist limit
        fb_max_adc = Fs / 2
        if S > 0:
            r_max_adc = (c_speed * fb_max_adc) / (2 * S)
        else:
            r_max_adc = 0
            
        # FIR / IF limit
        fb_max_fir = if_max
        if S > 0:
            r_max_fir = (c_speed * fb_max_fir) / (2 * S)
        else:
            r_max_fir = 0
            
        # Final max range
        r_max = min(r_max_adc, r_max_fir)
        
        limiting_factor = "ADC" if r_max_adc < r_max_fir else "FIR / IF"

        # --- GUI Layout: Derived Parameters ---
        st.markdown("---")
        col_res1, col_res2 = st.columns(2)
        
        with col_res1:
            st.markdown("#### Derived Parameters")
            st.write(f"**T_chirp:** {T_chirp*1e6:.2f} µs")
            st.write(f"**Bandwidth (BW):** {BW/1e9:.3f} GHz ({BW/1e6:.1f} MHz)")
            st.write(f"**Bin Spacing (Δf):** {df/1e3:.2f} kHz")
            st.write(f"**Range Resolution (ΔR):** {dR*100:.2f} cm ({dR:.4f} m)")
            
        with col_res2:
            st.markdown("#### Range Limits")
            st.write(f"**IF_max,mode:** {if_max_mode/1e6:.2f} MHz ({mode_desc})")
            st.write(f"**IF_max (clipped):** {if_max/1e6:.2f} MHz")
            st.write(f"**R_max (ADC limit):** {r_max_adc:.2f} m")
            st.write(f"**R_max (FIR limit):** {r_max_fir:.2f} m")
            st.markdown(f"**Final R_max:** `{r_max:.2f} m`")
            
            if limiting_factor == "ADC":
                st.info(f"Limiting factor: **{limiting_factor}**")
            else:
                st.warning(f"Limiting factor: **{limiting_factor}**")
                
            if r_max < 5.0:
                st.error("Warning: Max range is very small (< 5m). Consider lowering slope or increasing sampling rate.")

        # --- Formulas Panel ---
        with st.expander("Formulas & Definitions", expanded=True):
            st.markdown("### Definitions")
            st.markdown(r"""
            *   $S = \text{slope\_MHz\_per\_us} \times 10^{12}$ [Hz/s]
            *   $F_s = \text{ADCsampling\_Msps} \times 10^6$ [Hz]
            *   $T_{chirp} = N / F_s$
            *   $BW = S \times T_{chirp}$
            *   $\Delta R = c / (2 \times BW)$
            *   $\Delta f = F_s / N$
            *   $R(k) = k \times \Delta R$
            """)
            
            st.markdown("### AWR2243 IF / FIR Bandwidth")
            st.markdown(r"""
            *   $IF_{max,mode} = 0.9 \times F_s$ (for complex 1x)
            *   $IF_{max,mode} = 0.9 \times F_s / 2$ (for complex 2x and real)
            *   $IF_{max} = \min(IF_{max,mode}, 20 \text{ MHz})$
            """)
            
            st.markdown("### Max Range Limits")
            st.markdown(r"""
            **ADC Nyquist Limit:**
            *   $f_{b,max,ADC} = F_s / 2$
            *   $R_{max,ADC} = c \times f_{b,max,ADC} / (2 \times S)$
            
            **FIR / IF Limit:**
            *   $f_{b,max,FIR} = IF_{max}$
            *   $R_{max,FIR} = c \times f_{b,max,FIR} / (2 \times S)$
            
            **Final Limit:**
            *   $R_{max} = \min(R_{max,ADC}, R_{max,FIR})$
            """)

    elif radar_tool == "T-Shape Array Visualizer":
        st.subheader("T-Shape Array Visualizer")
        
        # --- Password Protection ---
        password = st.text_input("Enter Password to Access Tool", type="password")
        
        if password != "Gideon#1":
            st.warning("Access Denied. Please enter the correct password.")

            # --- Access Request Form ---
            with st.expander("Don't have a password? Request Access"):
                st.write("Please fill out the form below to request access via email.")
                req_name = st.text_input("Name")
                req_org = st.text_input("Organization / Reason")
                
                if req_name:
                    subject = "Request Access: T-Shape Visualizer"
                    body = f"Hi Yuval,\n\nI would like to request access to the T-Shape Visualizer.\n\nName: {req_name}\nOrganization: {req_org}\n\nThank you."
                    
                    safe_subject = urllib.parse.quote(subject)
                    safe_body = urllib.parse.quote(body)
                    mailto_link = f"mailto:uv.peleg@gmail.com?subject={safe_subject}&body={safe_body}"
                    
                    st.markdown(f"[**Click here to send email request**]({mailto_link})", unsafe_allow_html=True)

        else:
            st.success("Access Granted.")
            st.info("""
            **T-Shape Array Visualizer**
            This tool simulates the beam pattern of a T-shape MIMO array source.
            
            *   **Blue Line (Real)**: The pattern of your specific array configuration (including Grating Lobes).
            *   **Gray Dashed Line (Theoretical)**: A reference pattern from a "perfect" high-density array ($N=1000$) with the **same aperture length and windowing**. It shows the ideal pattern without grating lobes.
            """)

            # A. Inputs (Moved to Main Window)
            with st.expander("Configuration", expanded=True):
                # 1. Top Level Config
                c_conf1, c_conf2 = st.columns(2)
                with c_conf1:
                    ts_freq = st.number_input("Frequency (GHz)", value=77.0, step=0.1, format="%.2f")
                with c_conf2:
                    design_mode = st.radio("Design Mode", ["Hardware (Fixed Elements)", "Theoretical (Fixed Aperture)"], horizontal=True)

                st.markdown("---")

                c1, c2, c3, c4 = st.columns(4)
                
                # Initialize variables to ensure scope
                num_rx_mods = 1
                num_tx_mods = 1
                rx_aperture_m = 0.5
                tx_aperture_m = 0.5
                
                if design_mode == "Hardware (Fixed Elements)":
                     with c1:
                        num_rx_mods = st.number_input("RX Modules", value=3, min_value=1, step=1, help="Horizontal Array")
                     with c2:
                        rx_spacing_mm = st.number_input("RX Spacing (mm)", value=2.50, step=0.01, format="%.2f", key="rx_space_hw")
                     with c3:
                        num_tx_mods = st.number_input("TX Modules", value=3, min_value=1, step=1, help="Vertical Array")
                     with c4:
                        tx_spacing_mm = st.number_input("TX Spacing (mm)", value=4.074, step=0.001, format="%.3f", key="tx_space_hw")
                     
                     st.caption(f"**Physical Module Size (Fixed):** RX = 440 mm | TX = 440 mm")
                else:
                     with c1:
                        rx_aperture_m = st.number_input("RX Aperture (m)", value=0.5, min_value=0.01, step=0.01, format="%.3f")
                     with c2:
                        rx_spacing_mm = st.number_input("RX Spacing (mm)", value=2.50, step=0.01, format="%.2f", key="rx_space_th")
                     with c3:
                        tx_aperture_m = st.number_input("TX Aperture (m)", value=0.5, min_value=0.01, step=0.01, format="%.3f")
                     with c4:
                        tx_spacing_mm = st.number_input("TX Spacing (mm)", value=4.074, step=0.001, format="%.3f", key="tx_space_th")

                st.markdown("---")
                c_mode1, c_mode2, c_mode3 = st.columns(3)
                with c_mode1:
                    sim_mode = st.selectbox("Radio Mode", ["Physical Geometry", "Beam Pattern (Azimuth)", "Beam Pattern (Elevation)"])
                with c_mode2:
                    window_type = st.selectbox("Windowing", ["None (Rectangular)", "Hamming", "Hanning", "Blackman"])
                with c_mode3:
                    sim_res = st.number_input("Simulation Resolution (deg)", value=0.1, min_value=0.01, max_value=1.0, step=0.01, format="%.2f")

            # B. Architecture Logic
            # B. Architecture Logic
            if design_mode == "Hardware (Fixed Elements)":
                # Fixed Module Dimensions (mm)
                RX_MOD_LEN_MM = 440.0
                TX_MOD_LEN_MM = 440.0

                # RX Calculations
                if rx_spacing_mm <= 0: rx_spacing_mm = 0.001
                elements_per_rx_mod = int(math.floor(RX_MOD_LEN_MM / rx_spacing_mm))
                rx_elements_total = num_rx_mods * elements_per_rx_mod
                rx_awr_count = math.ceil(rx_elements_total / 4) # 4 channels per AWR2243

                # TX Calculations
                if tx_spacing_mm <= 0: tx_spacing_mm = 0.001
                elements_per_tx_mod = int(math.floor(TX_MOD_LEN_MM / tx_spacing_mm))
                tx_elements_total = num_tx_mods * elements_per_tx_mod
                tx_awr_count = math.ceil(tx_elements_total / 3) # 3 channels per AWR2243 (typ) OR 4? User said "based on channels per AWR2243 as already defined". 
                # Old code had: rx_ant_per_chip = 4, tx_ant_per_chip = 3. So 3 is correct.

                # Display Hardware Summary
                st.info(f"**Hardware Logic (Fixed {RX_MOD_LEN_MM:.0f}mm Modules):**\n\n"
                        f"**RX Array:** {num_rx_mods} Mods $\\times$ {elements_per_rx_mod} elems = **{rx_elements_total} Total Elements**\n"
                        f"Requires **{rx_awr_count}** AWR2243 Devices (4 ch/chip)\n\n"
                        f"**TX Array:** {num_tx_mods} Mods $\\times$ {elements_per_tx_mod} elems = **{tx_elements_total} Total Elements**\n"
                        f"Requires **{tx_awr_count}** AWR2243 Devices (3 ch/chip)")
            else:
                # Theoretical Mode
                d_rx = rx_spacing_mm / 1000.0
                d_tx = tx_spacing_mm / 1000.0
                
                if d_rx > 0:
                    rx_elements_total = int(rx_aperture_m / d_rx) + 1
                    # Ensure at least 2 elements
                    if rx_elements_total < 2: rx_elements_total = 2
                else:
                    rx_elements_total = 2
                    
                if d_tx > 0:
                    tx_elements_total = int(tx_aperture_m / d_tx) + 1
                    if tx_elements_total < 2: tx_elements_total = 2
                else:
                    tx_elements_total = 2
                    
                # Mock module definition for visualization
                elements_per_rx_mod = rx_elements_total
                num_rx_mods = 1
                elements_per_tx_mod = tx_elements_total
                num_tx_mods = 1
            
            # C. Physics & Math Engine
            d_rx = rx_spacing_mm / 1000.0 # meters
            d_tx = tx_spacing_mm / 1000.0 # meters
            wavelength = 3e8 / (ts_freq * 1e9)
            
            # Grating Lobe Check
            gl_issues = []
            theta_gr_rx = None
            theta_gr_tx = None
            
            if d_rx > wavelength / 2:
                val = wavelength / d_rx
                if val <= 1:
                    theta_gr_rx = np.degrees(np.arcsin(val))
                    gl_issues.append(f"RX Array (Azimuth): Grating Lobes at ±{theta_gr_rx:.1f}°")
            
            if d_tx > wavelength / 2:
                val = wavelength / d_tx
                if val <= 1:
                    theta_gr_tx = np.degrees(np.arcsin(val))
                    gl_issues.append(f"TX Array (Elevation): Grating Lobes at ±{theta_gr_tx:.1f}°")

            # D. Visualization
            if sim_mode == "Physical Geometry":
                st.markdown("#### Physical Geometry")
                
                fig = go.Figure()
                
                # RX Elements (Blue, X-axis, Y=0ish)
                # Center the array
                rx_coords = (np.arange(rx_elements_total) - (rx_elements_total - 1)/2) * d_rx
                rx_y_pos = 0.0
                
                # Module Outline (Dynamic Sizing)
                # Assume RX modules are arranged horizontally, side-by-side.
                # Total width = num_rx_mods * elements_per_rx_mod * d_rx (approx)
                # Actually, physical module size should probably wrap the elements.
                # Elements per mod = 176.
                # Width = 176 * d_rx. Height = ??? (Fixed or scaling?)
                # User's complaint: "different antenna density of same size".
                # Means if spacing changes, the dots move but the box stays same size => density visually changes.
                # We want the box to shrink/grow with the dots.
                
                # Dynamic Width based on spacing
                # 4 chips/board * 4 ants/chip = 16 ants/board? No.
                # Logic says: 4 rx_ant_per_chip, 11 rx_chips_per_board, 4 rx_boards_per_mod.
                # Total 176 elements horizontal.
                
                # In Design Mode, elements_per_rx_mod is set.
                # Width = Fixed 440mm per module in Hardware mode
                if design_mode == "Hardware (Fixed Elements)":
                    mod_w_rx = 0.440 # 440 mm
                else:
                    mod_w_rx = elements_per_rx_mod * d_rx
                
                # Height is structural, let's keep it fixed or proportional. 
                # Let's keep height fixed as spacing usually affects the array axis.
                mod_h_rx = 0.15
                
                # Calculate centers of RX modules
                # They are centered around 0.
                # i counts 0 to num-1
                # Center(i) = (i - (num-1)/2) * mod_w_rx
                for i in range(num_rx_mods):
                    cx = (i - (num_rx_mods - 1)/2) * mod_w_rx
                    cy = rx_y_pos
                    fig.add_shape(type="rect",
                        x0=cx - mod_w_rx/2, y0=cy - mod_h_rx/2,
                        x1=cx + mod_w_rx/2, y1=cy + mod_h_rx/2,
                        line=dict(color="blue", width=2, dash="dash"),
                        fillcolor="rgba(0,0,255,0.1)"
                    )
                
                # Add Dummy Scatter for Legend
                fig.add_trace(go.Scatter(x=[None], y=[None], mode='lines', line=dict(color='blue', dash='dash'), name='RX Module'))
                
                # TX Elements (Red, Y-axis, below RX)
                # "RX array is above the TX"
                # So TX starts below RX.
                # TX Modules: likely Vertical. (150mm x 440mm) ?
                # Or 440mm x 150mm rotated?
                # Let's assume they form the vertical stem.
                # Size per module
                # TX: 3 * 9 * 4 = 108 elements.
                # elements_per_tx_mod is set in logic block above

                
                # Vertical array: dim is determined by tx spacing.
                # Height = 108 * d_tx
                # Height = Fixed 440mm per module in Hardware mode
                if design_mode == "Hardware (Fixed Elements)":
                    mod_h_tx = 0.440 # 440 mm
                else:
                    mod_h_tx = elements_per_tx_mod * d_tx
                mod_w_tx = 0.15 # Fixed width

                # Gap below RX
                gap = 0.05
                tx_start_y = -mod_h_rx/2 - gap
                
                # TX Coords
                tx_coords_y = (np.arange(tx_elements_total)) * d_tx
                # make them go DOWN from tx_start_y
                tx_coords_y = tx_start_y - tx_coords_y 
                
                # Draw TX Module Outlines
                # Stacked vertically downwards
                # Center X = 0
                for i in range(num_tx_mods):
                    cx = 0
                    # i=0 is top one.
                    # Center Y = tx_start_y - (i * mod_h_tx) - mod_h_tx/2 ?
                    # Depends on element coverage.
                    # Let's center them on the element clusters if possible.
                    # Simplest: Just stack them below each other.
                    cy = tx_start_y - i * mod_h_tx - mod_h_tx/2
                    fig.add_shape(type="rect",
                        x0=cx - mod_w_tx/2, y0=cy - mod_h_tx/2,
                        x1=cx + mod_w_tx/2, y1=cy + mod_h_tx/2,
                        line=dict(color="red", width=2, dash="dash"),
                        fillcolor="rgba(255,0,0,0.1)"
                    )
                
                # Add Dummy Scatter for Legend
                fig.add_trace(go.Scatter(x=[None], y=[None], mode='lines', line=dict(color='red', dash='dash'), name='TX Module'))

                # Layout updates
                # Determine range to show everything nicely
                # Handle potential empty arrays if counts are 0 (unlikely with min=1)
                all_x = rx_coords if len(rx_coords)>0 else [0]
                if len(all_x) == 0: all_x = [0]
                # Include module bounds in ranges
                all_x = np.concatenate([all_x, [-mod_w_rx*num_rx_mods/2, mod_w_rx*num_rx_mods/2, -mod_w_tx/2, mod_w_tx/2]])
                
                all_y = np.concatenate([[rx_y_pos], tx_coords_y]) if len(tx_coords_y)>0 else [0]
                # Include module bounds
                # Lowest Y is approx tx_start_y - num_tx_mods * mod_h_tx
                all_y = np.concatenate([all_y, [mod_h_rx/2, -mod_h_rx/2, tx_start_y, tx_start_y - num_tx_mods*mod_h_tx]])
                
                margin_x = (max(all_x) - min(all_x)) * 0.1 + 0.1
                margin_y = (max(all_y) - min(all_y)) * 0.1 + 0.1
                
                fig.update_layout(title=f"T-Shape Array Layout (RX={rx_elements_total}, TX={tx_elements_total})",
                                  xaxis_title="X (m)", yaxis_title="Y (m)",
                                  yaxis=dict(scaleanchor="x", scaleratio=1),
                                  xaxis_range=[min(all_x)-margin_x, max(all_x)+margin_x],
                                  yaxis_range=[min(all_y)-margin_y, max(all_y)+margin_y],
                                  height=600,
                                  showlegend=True)
                st.plotly_chart(fig, use_container_width=True)
                
            else: # Beam Pattern
                st.markdown(f"#### {sim_mode}")
                
                # --- Dual View Layout ---
                # We want Math on top or side? 
                # Let's put Math in an expander to save space for the rich plots
                
                is_azimuth = "Azimuth" in sim_mode
                N = rx_elements_total if is_azimuth else tx_elements_total
                d = d_rx if is_azimuth else d_tx
                theta_gr = theta_gr_rx if is_azimuth else theta_gr_tx

                with st.expander("Math & Formulas", expanded=False):
                    st.markdown("**Array Factor (AF):**")
                    st.latex(r"AF(\theta) = \left| \sum_{n=0}^{N-1} w_n \cdot e^{j \frac{2\pi}{\lambda} n d \sin(\theta)} \right|")
                    st.markdown(f"**N**: {N} elements")
                    st.markdown(f"**d**: {d*1000:.2f} mm")
                    
                    st.markdown("**Windowing Function ($w_n$):**")
                    if "Hamming" in window_type:
                        st.latex(r"w_n = 0.54 - 0.46 \cos\left(\frac{2\pi n}{N-1}\right)")
                    elif "Hanning" in window_type:
                        st.latex(r"w_n = 0.5 \left(1 - \cos\left(\frac{2\pi n}{N-1}\right)\right)")
                    elif "Blackman" in window_type:
                        st.latex(r"w_n = 0.42 - 0.5 \cos\left(\frac{2\pi n}{N-1}\right) + 0.08 \cos\left(\frac{4\pi n}{N-1}\right)")
                    else:
                        st.latex(r"w_n = 1 \quad \text{(Rectangular)}")
                
                # --- Calculation ---
                # 1. Weights for "Real" (Windowed) Pattern
                if "Hamming" in window_type:
                    weights_real = np.hamming(N)
                elif "Hanning" in window_type:
                    weights_real = np.hanning(N)
                elif "Blackman" in window_type:
                    weights_real = np.blackman(N)
                else:
                    weights_real = np.ones(N)

                # 2. Weights for "Theoretical" (Virtual High-Density Array)
                # Goal: Match Aperture Length L but use N=1000 to kill Grating Lobes.
                L_real = (N - 1) * d
                if L_real <= 0: L_real = 0.001 # Safety

                N_virtual = 1000
                d_virtual = L_real / (N_virtual - 1) if N_virtual > 1 else L_real

                if "Hamming" in window_type:
                    weights_theory = np.hamming(N_virtual)
                elif "Hanning" in window_type:
                    weights_theory = np.hanning(N_virtual)
                elif "Blackman" in window_type:
                    weights_theory = np.blackman(N_virtual)
                else:
                    weights_theory = np.ones(N_virtual)
                    
                # Theta Array with user resolution
                # theta_deg = np.linspace(-90, 90, 1000) # Old
                theta_deg = np.arange(-90, 90 + sim_res/2, sim_res)
                theta_rad = np.deg2rad(theta_deg)
                
                k = 2 * np.pi / wavelength
                
                # Vectorized AF Calculation Helper
                def compute_af_db(w, th_rad, n_elems, spacing):
                    # phases = k * d * n * sin(theta)
                    n_idx = np.arange(n_elems)
                    u = np.sin(th_rad)
                    phases = k * spacing * n_idx[:, np.newaxis] * u[np.newaxis, :]
                    
                    # Sum
                    af_c = np.abs(np.sum(w[:, np.newaxis] * np.exp(1j * phases), axis=0))
                    
                    # Normalize
                    af_max_val = np.max(af_c)
                    if af_max_val > 0:
                        af_n = af_c / af_max_val
                        return 20 * np.log10(af_n + 1e-12)
                    else:
                        return np.zeros_like(af_c) - 60

                af_db_real = compute_af_db(weights_real, theta_rad, N, d)
                af_db_theory = compute_af_db(weights_theory, theta_rad, N_virtual, d_virtual)
                
                # --- Visualization (Dual View) ---
                col_polar, col_rect = st.columns(2)
                
                # 1. Polar Plot (Radar View)
                # Helper for Polar DB: Shift so -60 is center (0) and 0 is edge (60)
                def to_polar_db(db_vals, min_db=-60):
                    return np.maximum(db_vals, min_db) - min_db

                with col_polar:
                    fig_polar = go.Figure()
                    
                    # Theory (Gray Dashed)
                    fig_polar.add_trace(go.Scatterpolar(
                        r=to_polar_db(af_db_theory), 
                        theta=theta_deg,
                        mode='lines',
                        line=dict(color='gray', dash='dash', width=1),
                        name='Theoretical'
                    ))
                    
                    # Real (Blue Filled)
                    fig_polar.add_trace(go.Scatterpolar(
                        r=to_polar_db(af_db_real),
                        theta=theta_deg,
                        mode='lines', 
                        fill='toself',
                        line=dict(color='blue', width=2),
                        name='Real Pattern'
                    ))
                    
                    # Grating Lobes
                    if theta_gr is not None:
                         # Radial lines at theta_gr
                         # r goes from 0 to 60 (representing -60 to 0)
                         fig_polar.add_trace(go.Scatterpolar(
                             r=[0, 60], theta=[theta_gr, theta_gr],
                             mode='lines', line=dict(color='red', dash='dash', width=2),
                             name='Grating Lobe'
                         ))
                         fig_polar.add_trace(go.Scatterpolar(
                             r=[0, 60], theta=[-theta_gr, -theta_gr],
                             mode='lines', line=dict(color='red', dash='dash', width=2),
                             showlegend=False
                         ))

                    fig_polar.update_layout(
                        title="Polar View",
                        polar=dict(
                            radialaxis=dict(
                                visible=True, 
                                range=[0, 60],
                                tickmode='array',
                                tickvals=[0, 15, 30, 45, 60],
                                ticktext=['-60dB', '-45dB', '-30dB', '-15dB', '0dB']
                            ),
                            angularaxis=dict(direction="clockwise", rotation=90)
                        ),
                        height=500,
                        margin=dict(l=30, r=30, t=30, b=30),
                        showlegend=True,
                        legend=dict(x=0.5, y=-0.15, xanchor='center', orientation='h')
                    )
                    st.plotly_chart(fig_polar, use_container_width=True)

                # 2. Rectangular Plot (Engineering View)
                with col_rect:
                    fig_rect = go.Figure()
                    
                    # Theory
                    fig_rect.add_trace(go.Scatter(
                        x=theta_deg, y=af_db_theory,
                        mode='lines',
                        line=dict(color='gray', dash='dash'),
                        name='Theoretical'
                    ))
                    
                    # Real
                    fig_rect.add_trace(go.Scatter(
                        x=theta_deg, y=af_db_real,
                        mode='lines',
                        line=dict(color='blue'),
                        name='Real Pattern'
                    ))
                    
                    # Grating Lobes
                    if theta_gr is not None:
                        fig_rect.add_vline(x=theta_gr, line_dash="dash", line_color="red", annotation_text="GL")
                        fig_rect.add_vline(x=-theta_gr, line_dash="dash", line_color="red", annotation_text="GL")

                    fig_rect.update_layout(
                        title="Rectangular View (Engineering)",
                        xaxis_title="Angle (deg)",
                        yaxis_title="Amplitude (dB)",
                        xaxis=dict(range=[-90, 90], dtick=30),
                        yaxis=dict(range=[-60, 0]),
                        height=500,
                        margin=dict(l=30, r=30, t=30, b=30),
                        showlegend=True,
                        legend=dict(x=0.5, y=-0.15, xanchor='center', orientation='h'),
                        hovermode="x unified"
                    )
                    st.plotly_chart(fig_rect, use_container_width=True)

            # E. GUI Outputs
            st.markdown("---")
            m1, m2 = st.columns(2)
            
            # Theoretical Resolution (lambda / L)
            L_az = (rx_elements_total - 1) * d_rx
            L_el = (tx_elements_total - 1) * d_tx
            
            res_az_deg = np.degrees(wavelength / L_az) if L_az > 0 else 0
            res_el_deg = np.degrees(wavelength / L_el) if L_el > 0 else 0
            
            # Windowed broadening factor
            w_factor = 1.0
            if "Hamming" in window_type: w_factor = 1.3
            elif "Hanning" in window_type: w_factor = 1.44
            elif "Blackman" in window_type: w_factor = 1.6
            
            m1.metric("Azimuth Resolution (Theoretical)", f"{res_az_deg:.2f}°", help="lambda / D_rx")
            m1.markdown(r"$\text{Res}_{AZ} = \frac{\lambda}{D_{RX}}$")
            m1.write(f"Windowed: **{res_az_deg * w_factor:.2f} °**")
            
            m2.metric("Elevation Resolution (Theoretical)", f"{res_el_deg:.2f}°", help="lambda / D_tx")
            m2.markdown(r"$\text{Res}_{EL} = \frac{\lambda}{D_{TX}}$")
            m2.write(f"Windowed: **{res_el_deg * w_factor:.2f} °**")
            
            # Warnings
            if gl_issues:
                for issue in gl_issues:
                    st.warning(issue)

    elif radar_tool == "Monostatic Power Budget Calculator":
        st.subheader("Monostatic Power Budget Calculator")
        st.write("General monostatic radar SNR calculation.")


        # --- Layout: 2 Columns ---
        col_main_inputs, col_main_results = st.columns([1, 2])
        
        # --- 1. Inputs (Left Column) ---
        with col_main_inputs:
            st.markdown("### Inputs")
            
            # A. Frequency
            with st.expander("1. Frequency / Wavelength", expanded=True):
                freq_input_mode = st.radio("Input Mode", ["Start/Stop Frequencies", "Manual Wavelength (mm)"], horizontal=True)
                
                if freq_input_mode == "Start/Stop Frequencies":
                    f_start = st.number_input("Start Frequency (GHz)", value=76.0, step=0.1, format="%.2f")
                    f_stop = st.number_input("Stop Frequency (GHz)", value=79.0, step=0.1, format="%.2f")
                    
                    f_c = (f_start + f_stop) / 2.0
                    if f_c > 0:
                        wavelength_m = 3e8 / (f_c * 1e9) 
                    else:
                        wavelength_m = 0
                    
                    st.write(f"$f_c$: **{f_c:.2f} GHz**")
                    st.write(f"$\\lambda$: **{wavelength_m * 1000:.2f} mm**")
                    st.caption(f"Formula: $\\lambda = c / f_c$")
                    
                else: # Manual Wavelength
                    lambda_mm = st.number_input("Wavelength $\\lambda$ (mm)", value=3.90, step=0.01, format="%.3f")
                    wavelength_m = lambda_mm / 1000.0
                    
                    if wavelength_m > 0:
                        f_c = 3e8 / wavelength_m / 1e9
                    else:
                        f_c = 0
                        
                    st.write(f"$\\lambda$: **{lambda_mm:.3f} mm**")
                    st.write(f"Derived $f_c$: **{f_c:.2f} GHz**")
                    st.caption(f"Formula: $f_c = c / \\lambda$")
                
            # B. Transmit Chain
            with st.expander("2. Transmit Chain", expanded=True):
                # Default 10.4 dBm per spec
                P_t_dbm = st.number_input("Transmit Power P_t (dBm)", value=10.4, step=0.1) 
                
                # Formula Display
                P_t_dbw = P_t_dbm - 30.0
                st.latex(r"P_t[dBW] = P_t[dBm] - 30")
                st.info(f"{P_t_dbm} dBm → **{P_t_dbw:.1f} dBW**")
                
                # Updated Default: 5.5
                G_elm_db = st.number_input("Antenna Element Gain G_elm (dB)", value=5.5, step=0.1)
                
                # Processing Gain
                col_g1, col_g2 = st.columns(2)
                with col_g1:
                    N_tx = st.number_input("N_Tx", value=324, step=1)
                with col_g2:
                    N_rx = st.number_input("N_Rx", value=528, step=1)
                    
                G_proc_lin = N_tx * N_rx
                G_proc_db = 10 * math.log10(G_proc_lin) if G_proc_lin > 0 else 0
                
                st.caption(f"$G_{{proc}}$: **{G_proc_db:.1f} dB**")
                st.caption("Formula: $10 \\log_{10}(N_{Tx} N_{Rx})$")

            # C. Target
            with st.expander("3. Target Properties", expanded=True):
                tgt_mode = st.radio("Target Mode", ["Disc", "Manual RCS"])
                
                if tgt_mode == "Disc":
                    disc_diam_cm = st.number_input("Disc Diameter (cm)", value=2.15, step=0.1) # Default 2.15
                    apply_imp = st.checkbox("Apply -3dB Imperfection", value=True)
                    
                    st.latex(r"A = \pi (D/2)^2")
                    st.latex(r"\sigma = \frac{4\pi A^2}{\lambda^2}")
                    if apply_imp:
                        st.latex(r"\sigma_{dBsm} = 10 \log_{10}(\sigma) - 3")
                    
                    area = math.pi * ((disc_diam_cm / 100.0) / 2)**2
                    if wavelength_m > 0:
                        sigma_lin = (4 * math.pi * area**2) / (wavelength_m**2)
                    else:
                        sigma_lin = 0
                        
                    sigma_dbsm_raw = 10 * math.log10(sigma_lin) if sigma_lin > 0 else -100
                    
                    if apply_imp:
                        sigma_lin *= 0.5
                        sigma_dbsm = sigma_dbsm_raw - 3.0
                    else:
                        sigma_dbsm = sigma_dbsm_raw
                        
                    st.write(f"RCS $\\sigma_t$: **{sigma_dbsm:.1f} dBsm**")
                else:
                    sigma_dbsm = st.number_input("RCS $\\sigma_t$ (dBsm)", value=20.0, step=1.0)
            
            # D. Range & Environment
            with st.expander("4. Range & Environment", expanded=True):
                # Updated Default: 8.0 m
                R_m = st.number_input("Range R (m)", value=8.0, step=0.5)
                
                # Noise
                NF_db = st.number_input("Noise Figure NF (dB)", value=15.0, step=0.1) # Default 15.0
                
                # Formula helper
                st.latex(r"T_{sys}[dBK] = 10 \log_{10}(300) + NF")
                st.latex(r"(1/T_{sys})[dB] = -T_{sys}[dBK]")
                
                use_manual_noise = st.checkbox("Manual T_sys")
                
                if use_manual_noise:
                     T_sys_K = st.number_input("System Temp T_sys (K)", value=9486.0) # approx 300*10^1.5
                else:
                     # T_sys = 300 * 10^(NF/10) per prompt requirement
                     T_sys_K = 300.0 * (10**(NF_db/10.0))
                
                T_sys_dbk = 10 * math.log10(T_sys_K) if T_sys_K > 0 else 0
                st.info(f"For NF={NF_db} dB: **$T_{{sys}} = {T_sys_dbk:.1f}$ dBK**, **$1/T_{{sys}} = {-T_sys_dbk:.1f}$ dB**")
                
                # Bandwidth
                # Updated Default: 50.0 kHz
                W_bb_khz = st.number_input("Receiver Bandwidth W_BB (kHz)", value=50.0, step=10.0)
                W_bb_hz = W_bb_khz * 1000.0
                W_bb_dbhz = 10 * math.log10(W_bb_hz) if W_bb_hz > 0 else 0
                st.write(f"$W_{{BB}}$: **{W_bb_dbhz:.1f} dBHz**")
                st.caption(f"Formula: $10 \\log_{{10}}(W_{{BB}})$")
        
        # --- 2. Results (Right Column) ---
        with col_main_results:
            
            # --- Pre-calculation for Totals ---
            # Default Data
            loss_data_default = pd.DataFrame([
                {"Loss parameter": "Tx antenna pattern", "Loss dB": 1.5, "Description": "Off-boresight"},
                {"Loss parameter": "Rx antenna pattern", "Loss dB": 1.5, "Description": "Off-boresight"},
                {"Loss parameter": "Sampling & straddling", "Loss dB": 1.0, "Description": "Processing"},
                {"Loss parameter": "FFT & weighting", "Loss dB": 5.0, "Description": "Windowing"},
                {"Loss parameter": "Field degradation", "Loss dB": 3.0, "Description": "Env/HW"},
                {"Loss parameter": "Coherency degradation", "Loss dB": 0.5, "Description": "Phase noise"}
            ])
            
            # --- Link Budget Calculation ---
            # Constants
            k_db = -228.6 # dBW/K/Hz
            
            # Calculation Terms (dB)
            # P_t (dBm - 30)
            P_t_dbw = P_t_dbm - 30.0
            
            G_elm_sq_db = 2 * G_elm_db
            
            Lambda_sq_db = 20 * math.log10(wavelength_m) if wavelength_m > 0 else 0
            
            Sigma_db = sigma_dbsm
            
            # G_proc_db already calculated
            
            # Constant Term 1/(4pi)^3
            Const_term_db = -10 * math.log10((4 * math.pi)**3)
            
            # Range Term 1/R^4
            Range_term_db = -40 * math.log10(R_m) if R_m > 0 else 0
            
            # Boltzmann 1/k
            Boltzmann_term_db = 228.6
            
            # Noise Temp 1/T_sys (Negative in dB sum)
            Temp_term_db = -T_sys_dbk
            
            # Bandwidth 1/W_BB (Negative in dB sum)
            BW_term_db = -W_bb_dbhz
            
            # Use placeholder for L_sys until user edits
            # But we need to define the editor first? 
            # Solution: We render the EDITOR at the bottom, but we need the value for the TOP table.
            # Streamlit reruns on change. We can initialize the dataframe outside or just calculate?
            # Actually st.data_editor returns the edited df immediately.
            
            # But we want to display the Equation Table FIRST. 
            # We can calculate with "current" loss, render Equation Table, then render Loss Table.
            # However, if we put data_editor AFTER, will it update the BEFORE table on same run?
            # Yes, because Streamlit reruns the whole script on interaction.
            # BUT, we need the `edited_loss_df` variable available BEFORE we calculate `SNR_db`.
            # So we must CALL data_editor before we use its output. 
            # But we want to DISPLAY it below.
            # Trick: Use a container? Or just call it but display it later?
            # You cannot "call it but display later". The call places the element.
            # So we must use a container for the TOP part (Equation Table) and fill it later?
            # No, standard practice: Layout order in code determines display order.
            
            # If user wants Loss Table BELOW Radar Table:
            # Code structure:
            # 1. Calculate everything EXCEPT Loss.
            # 2. Render Loss Table (so we get the value). -> This places it in UI.
            # 3. Calculate Final SNR.
            # 4. Render Radar Table. -> This places it in UI.
            # Result: Loss Table is ABOVE Radar Table. This is NOT receiving what user wants.
            
            # To get Loss Table BELOW:
            # We need the value of Loss to calculate the table.
            # But we can only get the value by rendering the editor.
            # This is a Streamlit dependency cycle if we want visual order != logical order.
            # However, `st.data_editor` state is preserved across reruns. 
            # We can persist the loss value in session_state?
            # Simplest approach: Render Loss Table in an Expander or just at the bottom, 
            # but we accept that to get the value for the calculation we might need to render it.
            
            # Wait, `st.container` allows out-of-order rendering? 
            # "You can insert elements into a container at any time."
            
            container_radar_table = st.container()
            st.markdown("---") # Separator
            st.markdown("### Loss Table")
            
            edited_loss_df = st.data_editor(loss_data_default, num_rows="dynamic", use_container_width=True)
            L_sys_db = edited_loss_df["Loss dB"].sum()
            st.metric("Total Losses (dB)", f"{L_sys_db:.2f} dB")
            
            Loss_term_db = -L_sys_db
            
            # Now calculate SNR
            SNR_db = (P_t_dbw + G_elm_sq_db + Lambda_sq_db + Sigma_db + G_proc_db + 
                      Const_term_db + Range_term_db + Boltzmann_term_db + 
                      Temp_term_db + BW_term_db + Loss_term_db)
            
            # Construct DataFrame for Radar Table
            # Pre-calculate linear values for display
            P_t_lin = 10**(P_t_dbm/10.0) / 1000.0 # Watts
            G_elm_sq_lin = 10**(G_elm_sq_db/10.0)
            Lambda_sq_lin = wavelength_m**2 # m^2
            Sigma_lin = 10**(Sigma_db/10.0) # m^2
            G_proc_lin = 10**(G_proc_db/10.0)
            Const_term_lin = 1 / ((4 * math.pi)**3)
            Range_term_lin = 1 / (R_m**4)
            Boltzmann_lin = 1.380649e-23 # J/K
            # Boltzmann term in DB was +228.6 which is -10*log(k). So k = 10^(-228.6/10) ??
            # Wait, 10*log10(k) = 10*log10(1.38e-23) = -228.6.
            # So -10*log10(k) = +228.6.
            # Term is CONSTANT TERM + ... + BOLTZMANN
            # Radar Equation: SNR = (Pt * G^2 * lambda^2 * sigma * G_proc) / ((4pi)^3 * R^4 * k * T * B * L)
            # In dB: Pt + G^2 + lam^2 + sig + G_proc - (4pi)^3 - R^4 - k - T - B - L
            # - k_db = - ( -228.6 ) = +228.6. Correct.
            
            Temp_lin = T_sys_K
            BW_lin = W_bb_hz
            Loss_lin = 10**(L_sys_db/10.0)

            # RCS Comment
            if tgt_mode == "Disc":
                sigma_comment = r"Calculated ($\sigma \propto 1/\lambda^2$)"
            else:
                sigma_comment = "User input"
            
            lb_data = [
                ["Transmit Power", "$P_t$", f"{P_t_dbw:.1f} dBW", f"{format_eng(P_t_lin)}W", "User input (converted)"],
                ["Antenna Gain Sq.", "$G_{elm}^2$", f"{G_elm_sq_db:.1f} dB", f"{format_eng(G_elm_sq_lin)}", "2 * G_elm"],
                ["Wavelength Term", "$\lambda^2$", f"{Lambda_sq_db:.1f} dB", f"{format_eng(Lambda_sq_lin)}m²", "20 * log10(lambda)"],
                ["Target RCS", "$\sigma_t$", f"{Sigma_db:.1f} dBsm", f"{format_eng(Sigma_lin)}m²", sigma_comment],
                ["Processing Gain", "$G_{proc}$", f"{G_proc_db:.1f} dB", f"{format_eng(G_proc_lin)}", "10 * log10(N_tx * N_rx)"],
                ["Constant Term", "$1/(4\pi)^3$", f"{Const_term_db:.1f} dB", f"{format_eng(Const_term_lin)}", "-33 dB"],
                ["Range Term", "$1/R^4$", f"{Range_term_db:.1f} dB", f"{format_eng(Range_term_lin)}m⁻⁴", "-40 * log10(R)"],
                ["Boltzmann", "$1/k$", f"+228.6 dB", f"{format_eng(1/Boltzmann_lin)} J⁻¹K⁻¹", "Constant"],
                ["Noise Temperature", "$1/T_{sys}$", f"{Temp_term_db:.1f} dB", f"{format_eng(1/Temp_lin)} K⁻¹", "-10 * log10(T_sys)"],
                ["Bandwidth Term", "$1/W_{BB}$", f"{BW_term_db:.1f} dB", f"{format_eng(1/BW_lin)} Hz⁻¹", "-10 * log10(W_BB)"],
                ["Loss Term", "$1/L_{sys}$", f"{Loss_term_db:.1f} dB", f"{format_eng(1/Loss_lin)}", "- Sum(Losses)"],
                ["Final SNR", "SNR", f"**{SNR_db:.2f} dB**", f"{format_eng(10**(SNR_db/10.0))}", "Sum of all terms"]
            ]
            lb_df = pd.DataFrame(lb_data, columns=["Term", "Symbol", "Value (dB)", "Value (Lin)", "Formula / Comment"])
            
            # Render into the container (which is physically above the Loss Table)
            with container_radar_table:
                # Add Full Equation
                st.markdown("### Radar Equation")
                st.latex(r"SNR = \frac{P_t G_{elm}^2 \lambda^2 \sigma G_{proc}}{(4\pi)^3 R^4 k T_{sys} W_{BB} L_{sys}}")
                
                st.markdown("### Radar Equation Table")
                st.table(lb_df)
                st.success(f"**Calculated SNR: {SNR_db:.2f} dB**")
                st.caption("Formula: $SNR_{dB} = 10 \\log_{10}(SNR_{lin})$")
                


