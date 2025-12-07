# Yuval HW Tool (Rev 2)

A collection of hardware calculation tools including Voltage Divider, Feedback Resistor, dB Calculator, and RADAR Calculator.

## Installation

1.  Ensure you have Python installed.
2.  Install the required dependencies:

    ```bash
    pip install -r requirements.txt
    ```

## How to Run

To start the application, run the following command in your terminal:

```bash
streamlit run streamlit_app.py
```

**Note:** Do not run it as a standard Python script (e.g., `python streamlit_app.py`). It requires the `streamlit run` command to launch the web server.

## Features

*   **Voltage Divider**: Calculate E-series or custom resistors.
*   **Feedback Resistor**: Design DC/DC feedback networks.
*   **dB Calculator**: RF/Power conversions.
*   **RADAR Calculator**:
    *   Near Field Calculator
    *   FMCW Range Resolver
    *   AWR2243 Chirp Designer
    *   **T-Shape Array Visualizer** (Protected: `Gideon#1`)
