import streamlit as st
import math
import schemdraw
import schemdraw.elements as elm
import matplotlib.pyplot as plt
import io
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

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

# --- Near Field Helper Function ---
def calculate_near_field(d_aperture, wavelength):
    """Calculates near field boundary."""
    # Fraunhofer distance: 2 * D^2 / lambda
    r_ff = (2 * (d_aperture ** 2)) / wavelength
    return r_ff

# --- Main App ---
st.set_page_config(page_title="Yuval HW Tool", layout="wide")
st.title("Yuval HW Tool")

# --- Sidebar Navigation ---
st.sidebar.header("Navigation")
selected_tool = st.sidebar.radio(
    "Go to",
    ["Voltage Divider", "Feedback Resistor", "dB Calculator", "RADAR Calculator"]
)

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
        """
    )

st.sidebar.markdown("---")
st.sidebar.write("**Contact**: uv.peleg@gmail.com")
st.sidebar.write("**Rev 1.16**")


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
    
    radar_tool = st.radio("Select Tool", ["Near Field Calculator", "FMCW Range Resolver", "AWR2243 Chirp Designer"], horizontal=True)
    
    if radar_tool == "Near Field Calculator":
        st.subheader("Near Field Calculator")
        st.markdown("Calculate the Near Field (Fresnel) to Far Field (Fraunhofer) boundary distance.")
        
        col_nf1, col_nf2 = st.columns([1, 1])
        
        with col_nf1:
            d_ant = st.number_input("Antenna Size D (m)", value=0.1, min_value=0.001, format="%.4f")
            
            input_mode = st.radio("Input Mode", ["Wavelength", "Frequency"], horizontal=True)
            
            wavelength = 0.0
            
            if input_mode == "Wavelength":
                c_wl1, c_wl2 = st.columns([2, 1])
                with c_wl1:
                    wl_val = st.number_input("Wavelength", value=3.9, min_value=1e-6, format="%.4f")
                with c_wl2:
                    wl_unit = st.selectbox("Unit", ["mm", "cm", "m"])
                
                if wl_unit == "mm":
                    wavelength = wl_val / 1000.0
                elif wl_unit == "cm":
                    wavelength = wl_val / 100.0
                else:
                    wavelength = wl_val
                    
            else: # Frequency
                c_f1, c_f2 = st.columns([2, 1])
                with c_f1:
                    freq_val = st.number_input("Frequency", value=77.0, format="%.4f")
                with c_f2:
                    freq_unit = st.selectbox("Unit", ["Hz", "kHz", "MHz", "GHz"], index=3)
                
                if freq_unit == "Hz":
                    freq_hz = freq_val
                elif freq_unit == "kHz":
                    freq_hz = freq_val * 1e3
                elif freq_unit == "MHz":
                    freq_hz = freq_val * 1e6
                else: # GHz
                    freq_hz = freq_val * 1e9
                    
                if freq_hz > 0:
                    wavelength = 3e8 / freq_hz
                    st.info(f"Calculated Wavelength: **{wavelength*1000:.2f} mm**")
            
            if d_ant > 0 and wavelength > 0:
                r_ff = calculate_near_field(d_ant, wavelength)
                
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
            # Slope Input
            slope_mode = st.radio("Slope Input Mode", ["Direct Input", "Calculate from BW & Time"], horizontal=True)
            
            slope = 0.0 # MHz/us
            
            if slope_mode == "Direct Input":
                slope = st.number_input("Chirp Slope (MHz/us)", value=29.98, min_value=0.001, format="%.4f")
            else:
                bw_ghz = st.number_input("Bandwidth (GHz)", value=4.0, min_value=0.001)
                ramp_us = st.number_input("Ramp Time (us)", value=50.0, min_value=0.1)
                
                if ramp_us > 0:
                    # Slope = BW / T
                    # BW in MHz = bw_ghz * 1000
                    # T in us
                    slope = (bw_ghz * 1000) / ramp_us
                    st.info(f"Calculated Slope: **{slope:.4f} MHz/us**")
            
            # Beat Frequency Input
            f_beat_mhz = st.number_input("Beat Frequency (MHz)", value=10.0, min_value=0.0, format="%.4f")
            
            if slope > 0:
                # Range = (c * f_beat) / (2 * slope)
                # c = 300 m/us (approx for MHz/us units cancellation)
                # f_beat in MHz
                # slope in MHz/us
                # R = (300 * f_beat) / (2 * slope)
                
                c_speed = 300.0 # m/us
                range_m = (c_speed * f_beat_mhz) / (2 * slope)
                
                st.latex(r"R = \frac{c \cdot f_{beat}}{2 \cdot S}")
                
                st.success(f"**Calculated Range:** {range_m:.4f} m")
                st.info(f"**In Centimeters:** {range_m*100:.2f} cm")
                
                # Visualization Data
                # Generate a small plot around the point
                f_max = f_beat_mhz * 2 if f_beat_mhz > 0 else 20.0
                f_vals = [i * (f_max / 100) for i in range(101)]
                r_vals = [(c_speed * f) / (2 * slope) for f in f_vals]
                
                df = pd.DataFrame({"Beat Frequency (MHz)": f_vals, "Range (m)": r_vals})
                
                fig = px.line(df, x="Beat Frequency (MHz)", y="Range (m)", title="Range vs Beat Frequency")
                fig.add_scatter(x=[f_beat_mhz], y=[range_m], mode='markers', marker=dict(size=10, color='red'), name='Current Point')
                
                with col_fmcw2:
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.error("Slope must be positive.")

    else: # AWR2243 Chirp Designer
        st.subheader("AWR2243 Chirp Designer")
        st.markdown("Design chirp parameters and calculate performance metrics.")
        
        # Inputs
        col_des1, col_des2 = st.columns(2)
        with col_des1:
            f_start = st.number_input("Start Frequency (GHz)", value=77.0, format="%.2f")
            slope = st.number_input("Frequency Slope (MHz/us)", value=29.982, format="%.3f")
        with col_des2:
            adc_samples = st.number_input("ADC Samples (N)", value=256, step=1)
            sample_rate = st.number_input("Sample Rate (Msps)", value=10.0, format="%.1f")
            
        if sample_rate > 0 and slope > 0:
            # Calculations
            t_ramp = adc_samples / sample_rate # us
            bw_ghz = (slope * t_ramp) / 1000.0 # GHz
            
            # Resolution: c / (2 * B)
            # c = 3e8 m/s
            # B in Hz = bw_ghz * 1e9
            # Res = 3e8 / (2 * bw_ghz * 1e9) = 0.15 / bw_ghz (meters)
            res_m = 0.15 / bw_ghz if bw_ghz > 0 else 0
            res_cm = res_m * 100
            
            # Max IF
            max_if = 0.9 * sample_rate / 2.0 # MHz
            
            # Max Range
            # R = (c * f_if) / (2 * S)
            # c = 300 m/us
            # f_if in MHz
            # S in MHz/us
            max_range = (300.0 * max_if) / (2 * slope)
            
            # Metric Cards
            m1, m2, m3 = st.columns(3)
            m1.metric("Resolution", f"{res_cm:.2f} cm")
            m2.metric("Max Range", f"{max_range:.2f} m")
            m3.metric("Sweep Bandwidth", f"{bw_ghz:.3f} GHz")
            
            # Warnings
            if bw_ghz > 4.0:
                st.warning(f"Warning: Bandwidth ({bw_ghz:.3f} GHz) exceeds AWR2243 limit of 4 GHz.")
            if max_if > 15.0:
                st.warning(f"Warning: Max IF Frequency ({max_if:.2f} MHz) exceeds typical 15 MHz limit.")
                
            # Plotly Sawtooth
            st.markdown("### Chirp Visualization")
            
            # Points: (0, f_start), (t_ramp, f_start + bw)
            df_chirp = pd.DataFrame({
                "Time (us)": [0, t_ramp],
                "Frequency (GHz)": [f_start, f_start + bw_ghz]
            })
            
            fig_chirp = px.line(df_chirp, x="Time (us)", y="Frequency (GHz)", title="Chirp Frequency vs Time")
            fig_chirp.update_layout(showlegend=False)
            st.plotly_chart(fig_chirp, use_container_width=True)
            
        else:
            st.error("Sample Rate and Slope must be positive.")
