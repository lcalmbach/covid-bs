import streamlit as st
import pandas as pd
import covex

__version__ = '1.1.0'
__author__ = 'Lukas Calmbach'

covex.data, covex.bs_data, covex.last_refresh_date = covex.read_files()
covex.cantons, covex.plot_type, covex.variables, covex.group_plot, covex.plot_width, covex.plot_height, covex.y_max, covex.selected_date, covex.button_clicked, covex.y_log = covex.show_side_bar(__version__)
if covex.button_clicked:
    covex.show_result()
elif len(covex.variables)==0 and covex.group_plot != 'var':
    st.info("Wählen sie mindestens eine Variable aus der Variablen-Liste")
elif len(covex.cantons)==0  and covex.group_plot != 'canton':
    st.info("Wählen sie mindestens einen Kanton aus")
else:
    covex.show_result()


