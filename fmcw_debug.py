import math

# --- FMCW Radar Helper Functions ---
def calculate_range_fft(slope_hz_s, fs, n_fft, c=3e8):
    """Calculates range resolution and range per bin."""
    # Bandwidth for one bin
    bin_bw = fs / n_fft
    # Range for one bin (beat freq = bin_bw)
    # R = (c * fb) / (2 * S)
    range_per_bin = (c * bin_bw) / (2 * slope_hz_s)
    return range_per_bin

def calculate_max_range(fs, t_chirp, b_bw, f_if_max=None, c=3e8):
    """Calculates max unambiguous ranges."""
    slope = b_bw / t_chirp
    
    # 1. ADC Nyquist Limit
    # fb_max = fs / 2
    # R = (c * fb_max) / (2 * S) = (c * fs) / (4 * S)
    r_max_adc = (c * fs) / (4 * slope)
    
    # 2. IF Bandwidth Limit
    r_max_if = float('inf')
    if f_if_max:
        r_max_if = (c * f_if_max) / (2 * slope)
        
    # 3. Timing Limit (Round trip <= T_chirp)
    # 2R/c <= T_chirp => R <= c * T_chirp / 2
    r_max_timing = (c * t_chirp) / 2
    
    # Final Logic
    r_max_freq = min(r_max_adc, r_max_if)
    r_max_unamb = min(r_max_freq, r_max_timing)
    
    return {
        "slope": slope,
        "r_max_adc": r_max_adc,
        "r_max_if": r_max_if,
        "r_max_timing": r_max_timing,
        "r_max_unamb": r_max_unamb
    }

def calculate_near_field(fc, d_aperture, c=3e8):
    """Calculates near field boundary."""
    wavelength = c / fc
    # Fraunhofer distance: 2 * D^2 / lambda
    r_ff = (2 * (d_aperture ** 2)) / wavelength
    return wavelength, r_ff

def calculate_radar_range_cw(pt, gt, gr, fc, sigma, l_loss, p_min, c=3e8):
    """Calculates max range for CW radar."""
    wavelength = c / fc
    # R = [ (Pt * Gt * Gr * lambda^2 * sigma) / ((4pi)^3 * L * Pmin) ]^(1/4)
    numerator = pt * gt * gr * (wavelength ** 2) * sigma
    denominator = ((4 * math.pi) ** 3) * l_loss * p_min
    return (numerator / denominator) ** 0.25

def calculate_radar_range_fmcw(pt, gt, gr, fc, sigma, l_loss, nf_lin, t0, b_if, snr_min_lin, n_range, n_doppler, c=3e8):
    """Calculates max range for FMCW radar with processing gain."""
    wavelength = c / fc
    k_boltz = 1.38064852e-23
    
    # Noise Power Pn = k * T0 * NF * B_IF
    pn = k_boltz * t0 * nf_lin * b_if
    
    # Processing Gain
    g_proc = n_range * n_doppler
    
    # R = [ (Pt * Gt * Gr * lambda^2 * sigma * G_proc) / ((4pi)^3 * L * Pn * SNR_min) ]^(1/4)
    numerator = pt * gt * gr * (wavelength ** 2) * sigma * g_proc
    denominator = ((4 * math.pi) ** 3) * l_loss * pn * snr_min_lin
    
    r_max = (numerator / denominator) ** 0.25
    
    return r_max, pn, g_proc

if __name__ == "__main__":
    print("--- Debugging FMCW Radar Logic ---")
    
    # 1. Test Range FFT
    print("\n1. Range FFT")
    slope = 30e12 # 30 MHz/us
    fs = 10e6
    n_fft = 1024
    r_bin = calculate_range_fft(slope, fs, n_fft)
    print(f"Slope: {slope/1e12} MHz/us, Fs: {fs/1e6} MHz, N_fft: {n_fft}")
    print(f"Range per bin: {r_bin:.4f} m")
    
    # 2. Test Max Range
    print("\n2. Max Range")
    t_chirp = 50e-6
    bw = 2e9
    res = calculate_max_range(fs, t_chirp, bw)
    print(f"T_chirp: {t_chirp*1e6} us, BW: {bw/1e9} GHz")
    print(f"R_max_ADC: {res['r_max_adc']:.2f} m")
    print(f"R_max_Timing: {res['r_max_timing']:.2f} m")
    print(f"R_max_Unamb: {res['r_max_unamb']:.2f} m")
    
    # 3. Test Near Field
    print("\n3. Near Field")
    fc = 77e9
    d = 0.1
    lam, r_ff = calculate_near_field(fc, d)
    print(f"Fc: {fc/1e9} GHz, D: {d} m")
    print(f"Wavelength: {lam*1000:.2f} mm")
    print(f"Far Field Distance: {r_ff:.2f} m")
    
    # 4. Radar Equation
    print("\n4. Radar Equation")
    pt_dbm = 12
    gt_db = 10
    gr_db = 10
    sigma = 1
    loss_db = 2
    nf_db = 10
    t0 = 290
    b_if = 10e6
    snr_min_db = 15
    n_range = 1024
    n_doppler = 64
    
    # Conversions
    pt = 10**((pt_dbm-30)/10)
    gt = 10**(gt_db/10)
    gr = 10**(gr_db/10)
    loss = 10**(loss_db/10)
    nf = 10**(nf_db/10)
    snr_min = 10**(snr_min_db/10)
    
    # CW P_min equivalent
    k = 1.38064852e-23
    p_min = k * t0 * nf * b_if * snr_min
    
    r_cw = calculate_radar_range_cw(pt, gt, gr, fc, sigma, loss, p_min)
    r_fmcw, pn, g_proc = calculate_radar_range_fmcw(pt, gt, gr, fc, sigma, loss, nf, t0, b_if, snr_min, n_range, n_doppler)
    
    print(f"R_max CW: {r_cw:.2f} m")
    print(f"R_max FMCW: {r_fmcw:.2f} m (Gain: {10*math.log10(g_proc):.2f} dB)")
