import streamlit as st
import pandas as pd
import requests
import altair as alt
import time
from datetime import date, datetime, timedelta
import os

import tools
import config as cn

# refresh if cache older than 1 hour
@st.cache(ttl = 3600)
def read_files() -> pd.DataFrame:
    """
    Reads the number of cases from a csv file into a panda. todo make sure that the file is reread at least once
    a day to  assure that the data is refreshed. The file content is cached 1 hour to make sure data updates are
    taken into account quickly.
    """

    numbers_df = pd.read_csv(cn.COVID_FAELLE_CH_URL)
    # read BS data
    bs_df = pd.read_csv(cn.FALLZAHLEN_BS_URL)
    bs_df = prepare_bs_covid_death_data(bs_df)
    # read population table and merge with cases
    filename = cn.BEVOELKERUNG_CH_URL
    einw_df = pd.read_csv(filename)
    einw_df.rename(columns = {'Canton':'abbreviation_canton_and_fl'}, inplace=True)
    #remove non required columns
    einw_df = einw_df[['abbreviation_canton_and_fl','Population']]
    df_merged = pd.merge(numbers_df, einw_df, on='abbreviation_canton_and_fl')

    df_merged['date'] =  pd.to_datetime(df_merged['date'], format='%Y-%m-%d')
    # remove non required columns so it is easier to merge with the ch-dataframe 
    
    # calculate CH total values as sum of all cantons
    ch_df = prepare_ch_data(einw_df, df_merged)
    frames = [df_merged, ch_df]
    df_merged = pd.concat(frames, axis=0)
    df_merged['ncumul_conf_pro_einw'] = df_merged.ncumul_conf / df_merged.Population * 1e5
    df_merged['ncumul_tested_pro_einw'] = df_merged.ncumul_tested / df_merged.Population * 1e5
    df_merged['ncumul_hosp_pro_einw'] = df_merged.ncumul_hosp / df_merged.Population * 1e5
    df_merged['ncumul_ICU_pro_einw'] = df_merged.ncumul_ICU / df_merged.Population * 1e5
    df_merged['ncumul_vent_pro_einw'] = df_merged.ncumul_vent / df_merged.Population * 1e5
    df_merged['ncumul_released_pro_einw'] = df_merged.ncumul_released / df_merged.Population * 1e5
    df_merged['ncumul_deceased_pro_einw'] = df_merged.ncumul_deceased / df_merged.Population * 1e5
    df_merged = get_calculated_rows(df_merged)
    df_merged['date'] =  pd.to_datetime(df_merged['date'], format='%Y-%m-%d')
    df_melted = pd.melt(df_merged,
        id_vars=['date', 'abbreviation_canton_and_fl', 'Population'],
        value_vars=['ncumul_conf', 'ncumul_tested','ncumul_hosp','ncumul_ICU',
            'ncumul_vent','ncumul_released','ncumul_deceased',
            'ncumul_conf_pro_einw', 'ncumul_tested_pro_einw','ncumul_hosp_pro_einw','ncumul_ICU_pro_einw',
            'ncumul_vent_pro_einw','ncumul_released_pro_einw','ncumul_deceased_pro_einw','n_active','n_conf'
            ])
    df_melted = df_melted.rename(columns={"abbreviation_canton_and_fl": "Kanton"})
    
    return df_melted, bs_df, datetime.now().strftime('%x %H:%M')


def get_bs_population():
    return 194766
    st.write(data)

@st.cache(ttl = 3600, suppress_st_warning=True)
def read_values_bs() -> pd.DataFrame:
    """
    Reads the bs dataset for covid cases, which includes more information than the swiss dataset. 
    The function also calculates the incidence for bs residents
    """

    def calculate_incidence(df, days, column_name)->pd.DataFrame:
        """
        Calculates for each day the sum of 7 and 14 previous days cases and stores the result in column
        {column_name}. Divided by population/100'000 this will result in the {days} incidence value
        
        Returns:
        updated dataframe
        most recent date for reported cases
        """
        
        
        _df = df[['Datum', 'Fälle mit Wohnsitz BS']]
        _df['datum_start_interval'] = _df['Datum'] + timedelta(days=-(days-1))
        df.set_index('Datum', inplace=True)
        for index, row in _df.iterrows():
            _today = row['Datum']
            _df_filt = df[( df.index <= _today ) & ( df.index >= row['datum_start_interval'] )]
            _df_s = _df_filt.sum()
            df.at[_today, column_name] = _df_s['Fälle mit Wohnsitz BS']
        df.reset_index(inplace=True)
        return df

    _df = pd.read_csv(cn.VALUES_BS_URL, sep = ';').sort_values(by='Zeitstempel',ascending=False)
    _df = _df[['Datum','Zeit','Differenz Fälle mit Wohnsitz BS', 'Differenz Fälle mit Wohnsitz ausserhalb BS', 'Isolierte', 'Kontaktpersonen in Quarantäne'
        ,'Reiserückkehrer in Quarantäne','In Quarantäne total', 'Fälle mit Wohnsitz BS','Fälle mit Wohnsitz ausserhalb BS','Fälle auf Intensivstation',
        'Genesene', 'Differenz Genesene', 'Verstorbene', 'Differenz Verstorbene']]
    # _df['Datum'] = pd.to_datetime(_df['Datum'])
    _df.rename(columns = {'Differenz Fälle mit Wohnsitz BS':'Fälle mit Wohnsitz BS',
        'Differenz Fälle mit Wohnsitz ausserhalb BS': 'Fälle mit Wohnsitz ausserhalb BS',
        'Fälle mit Wohnsitz BS': 'Fälle mit Wohnsitz BS kumuliert',
        'Fälle mit Wohnsitz ausserhalb BS': 'Fälle mit Wohnsitz ausserhalb BS',
        'Verstorbene': 'Verstorbene kumuliert',
        'Differenz Verstorbene': 'Verstorbene',
        'Genesene': 'Genesene kumuliert',
        'Differenz Genesene': 'Genesene',
        }, inplace = True) 
    # last 14 days
    _df = _df.head(21)

    _df['Datum'] = _df['Datum'].astype('datetime64[ns]')
    _df['Fälle letzte 7 Tage'] = 0
    _df['Fälle letzte 14 Tage'] = 0
    _df = calculate_incidence(_df, 7, 'Fälle letzte 7 Tage')
    _df = calculate_incidence(_df, 14, 'Fälle letzte 14 Tage')
    _most_recent_date = _df.max()['Datum']
    _pop = get_bs_population()
    _df = _df.set_index('Datum')
    _df['7 Tage Inzidenz'] =  (_df['Fälle letzte 7 Tage'] / _pop * 100000).round(1)
    _df['14 Tage Inzidenz'] = (_df['Fälle letzte 14 Tage'] / _pop * 100000).round(1)
    _df = _df.head(7)
    return _df.transpose(), _most_recent_date

@st.cache(ttl = 3600)
def get_values_bs_comment(df:pd.DataFrame, reporting_date)-> str:
    sentence = {}
    _weekday = cn.WEEK_DIC[reporting_date.weekday()]

    _new = int(df.at['Fälle mit Wohnsitz BS', reporting_date])
    _cumul =  int(df.at['Fälle mit Wohnsitz BS kumuliert', reporting_date])
    _cured = int(df.at['Genesene kumuliert', reporting_date])
    _inc7 = df.at['7 Tage Inzidenz', reporting_date]
    _inc14 = df.at['14 Tage Inzidenz', reporting_date]
    _sum7 = int(df.at['Fälle letzte 7 Tage', reporting_date])
    _sum14 = int(df.at['Fälle letzte 14 Tage', reporting_date])
    _dead = int(df.at['Verstorbene', reporting_date])
    _dead_cumul = int(df.at['Verstorbene kumuliert', reporting_date])

    sentence['rising_falling'] = f'Die Zahl der COVID-19 Todesfälle stieg um {_dead} auf insgesamt {_dead_cumul}' if _dead > 0 else f'Die Zahl der COVID-19 Todesfälle blieb konstant bei insgesamt {_dead_cumul}'

    _text = f"""
    Am {_weekday} gab es in Basel-Stadt weitere {_new} bestätigte Infektionen mit dem Coronavirus. Damit {'erhöhte sich'} die Zahl der Infizierten 
    im Kanton auf {_cumul}. Ungefähr {_cured} Personen sind seit Beginn der Epidemie wieder genesen. Insgesamt infizierten sich in den vergangenen 7 Tagen {_sum7} Personen, in den vergangenen 14 Tagen waren es {_sum14}. 
    Die 7-Tage Inzidenz beträgt zur Zeit {_inc7}. 
    {sentence['rising_falling']}.<br><br>Einige wichtige publizierte Zahlen der letzten sieben Tage sind in untenstehender Tabelle zusammengefasst.  
    """
    return _text

def get_incidence_comment()-> str:
    _pop = get_bs_population()
    _pop = f"{_pop:,}"
    _text = f"""
    <sub>n-Tage Inzidenz = Anzahl Fälle pro 100'000 Einwohner über die letzten n Tage. Je nach Quelle, Stichtag und Definition der Einwohnerzahl 
    kann dieser Wert also leicht schwanken. Die Einwohnerzahl des Kantons ist in der Regel z.B. etwas höher als diejenige des BFS, da sie auch die Wochenaufenthalter beinhaltet. Daraus ergibt sich dann eine geringfügig tiefere Inzidenz.
    Die Inzidenzen in CovEx wird mit einer Einwohnerzahl von {_pop} gerechnet, gemäss [Demografische Bilanz Nach Kanton](https://www.bfs.admin.ch/bfs/de/home/statistiken/bevoelkerung.assetdetail.14087712.html) des 
    BFS. Dieser Datenbestand wird in CovEx-bs für alle pro Kopf Quoten verwendet.</sub>
    """
    return _text


@st.cache(ttl = 3600)
def read_sterbefaelle_bs() -> pd.DataFrame:

    def calc_ueberige(row, total_col, covid_col):
        result = row[total_col] - row[covid_col] if row[total_col] > row[covid_col] else 0
        return result

    filename = './100079.csv'
    # if file older than 12 hours then read it again, otherwise use local copy
    if tools.file_age(filepath=filename, time_unit='h') > cn.MAX_FILE_AGE_HOURS:
        url = cn.VALUES_BS_URL
        myfile = requests.get(url)
        open(filename, 'wb').write(myfile.content)

    df_all_deaths = pd.read_csv(filename, sep = ';')
    jahr = 'Jahr'
    total = 'Anzahl Gestorbene total'
    kw = 'Kalenderwoche'
    dat = 'Sterbedatum'
    datw = 'Startdatum Woche'
    month = 'Monat'
    year = 'Jahr'
    df_all_deaths[dat] = pd.to_datetime(df_all_deaths[dat], format='%Y-%m-%d')
    df_all_deaths[datw] = pd.to_datetime(df_all_deaths[datw], format='%Y-%m-%d')
    
    # aggregate weekly death rates
    # df_week_cum = df_all_deaths[df_all_deaths[dat] >= '2020-03-01']
    df_week_cum = df_all_deaths.groupby([datw]).sum().reset_index()
    df_week_cum = df_week_cum[[datw, total]]

    # aggregate monthly death rates since 2005
    df_month_cum = df_all_deaths[df_all_deaths[dat] >= '2005-01-01']
    df_month_cum['year_month'] = df_month_cum.apply(lambda row: tools.calc_year_month(row, year, month, '-'), axis=1)
    df_month_cum = df_month_cum.groupby(['year_month', month], as_index=False).agg({total: "sum"})
    df_month_cum = df_month_cum.sort_values(by=[month, total])
    df_month_cum["Monat"] = df_month_cum["Monat"].map(cn.MONTH_DIC)
    
    max_date = df_all_deaths[dat].max()
    bs_data_cum =  bs_data.groupby(['Date']).sum().reset_index()
    df_deaths_since_March2020 = df_all_deaths[df_all_deaths[dat] >= '2020-03-01']
    df_merged = pd.merge(df_deaths_since_March2020, bs_data_cum, left_on=dat, right_on='Date', how='left')
    df_merged = df_merged[[dat, total,'n_deceased']]
    df_merged['n_deceased'] = df_merged['n_deceased'].fillna(0, axis = 0)
    # calculate total deaths-covid death
    df_merged['Überige Gestorbene'] = 0
    df_merged['Überige Gestorbene'] = df_merged.apply(lambda row: calc_ueberige(row, total,'n_deceased'), axis=1)
    df_merged = df_merged.rename(columns={'n_deceased': "Covid Fälle"})
    df_merged = pd.melt(df_merged, id_vars=[dat], value_vars=['Covid Fälle', 'Überige Gestorbene'])
    df_merged['value'] = df_merged['value'].fillna(0, axis = 0)
    df_merged = df_merged.rename(columns={'variable': "Todesursache", 'value': "Fälle"})

    return df_merged, df_week_cum, df_month_cum


@st.cache(ttl = 3600)
def prepare_bs_covid_death_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Returns the data frame with covid case data for basel with added columns sec and age used for plotting
    """

    default_sex = 'F'

    # add defaultrows with ndeceased = 0 so all groups are forced to show up
    df_def = pd.DataFrame({"Date":['2020-03-01','2020-03-01','2020-03-01','2020-03-01'], 
        'Gender':['F','F','M','M'], 'AgeYear': [80,60,80,60], 'NewDeaths': [0,0,0,0]})
    df = df.append(df_def).reset_index()

    df['age_group'] = '>= 65'
    df['age_gender_agg'] = 'undef'
    df = complete_age_column(df, 'AgeYear', 'age_numeric')
    df = df.rename(columns={"NewDeaths": "n_deceased"})
    df['Gender'] = df['Gender'].fillna(default_sex, axis = 0)
    df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m-%d')
    df['month_year'] = df['Date'].apply(lambda x: x.strftime('%Y-%m'))
    df['month'] = df['Date'].dt.month
    df['week'] = df['Date'].dt.dayofweek
    df['week_id'] = df['Date'].dt.week
    df.loc[df['age_numeric'].astype(int) < 65, 'age_group'] = '< 65'

    cols = ['age_gender_agg']
    df.loc[(df['age_group'] == '< 65') & (df['Gender'] == 'M'), cols] = 'Männer, < 65'
    df.loc[(df['age_group'] == '>= 65') & (df['Gender'] == 'M'), cols] = 'Männer, >= 65'
    df.loc[(df['age_group'] == '< 65') & (df['Gender'] != 'M'), cols] = 'Frauen, < 65'
    df.loc[(df['age_group'] == '>= 65') & (df['Gender'] != 'M'), cols] = 'Frauen, >= 65'
    return df


@st.cache(ttl = 3600)
def complete_age_column(df: pd.DataFrame, age_col_string:str, age_col_numeric: str):
    """
    Generates a new numeric age column where string values such as 20-40 or > 60 are converted into the minimum 
    numeric values as follows:
    10-30: 10
    > 60: 61
    """
    default_age = 80
    df[age_col_string] = df[age_col_string].fillna(default_age, axis = 0)
    df[age_col_numeric] = pd.to_numeric(df[age_col_string], errors='coerce')
    df = df.astype({age_col_string: 'str'})
    cols = 'age_numeric'
    df.loc[df[age_col_string].str.contains('>', regex = False),age_col_numeric] = df[age_col_string].apply(lambda x: int(x[-2:])+1)
    df.loc[df[age_col_string].str.contains('-', regex = False),age_col_numeric] = df[age_col_string].apply(lambda x: x[:2])
    df[age_col_numeric] = df[age_col_numeric].astype(int)
    return df


@st.cache(ttl = 3600)
def get_calculated_rows(df: pd.DataFrame) -> pd.DataFrame:
    df['n_active'] = df['ncumul_conf'] - df['ncumul_released']
    df['n_conf'] = 0
    frames = []
    for canton in cn.CANTON_LIST:
        result = df[df['abbreviation_canton_and_fl'] == canton]
        result['n_conf'] = result['ncumul_conf'] - result['ncumul_conf'].shift(1, axis = 0)
        frames.append(result)

    return pd.concat(frames)


@st.cache(ttl = 3600)
def prepare_ch_data(df_pop: pd.DataFrame, cant_df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds the data from all cantons and generates a dataframe that can be added to the cantons 
    to represent the countries total cases
    """

    pop_ch = df_pop['Population'][df_pop['abbreviation_canton_and_fl'] == 'CH']
    # todo: change this to: last date where all cantons have reported cases
    cant_df = cant_df[cant_df['date'] < (pd.Timestamp('today') - timedelta(days=2))]
    pop_ch = pop_ch.tolist()[0]
    ch_df = pd.DataFrame(cant_df.groupby(['date'])[['ncumul_conf','ncumul_hosp','ncumul_ICU','ncumul_vent','ncumul_released','ncumul_deceased']].sum())
    ch_df['abbreviation_canton_and_fl'] = 'CH'
    ch_df['Population'] = pop_ch
    return ch_df.reset_index()


def filter_data():
    """
    Returns a filtered dataframe based on the selection of cantons and variables
    """

    if len(cantons) > 0 and len(variables) > 0:
        data_filtered = data[(data['Kanton'].isin(cantons)) & (data['variable'].isin(list(variables)))]
    elif len(cantons) > 0:
        data_filtered = data[data['Kanton'].isin(cantons)]
    elif len(variables) > 0:
        data_filtered = data[data['variable'].isin(list(variables))]

    if plot_type == 'bc':
        comp_date = datetime.strptime(selected_date, '%d/%m/%Y').strftime('%Y-%m-%d')
        data_filtered = data_filtered[data_filtered['date'] == comp_date]
        data_filtered["value"].fillna(0)
        # data_filtered = data_filtered.sort_values(by='value', ascending=True)
    
    return data_filtered


def rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Renames column names and labels to make them more userfriendly where they appear on the plot 
    """

    if len(cantons) == 1 and len(variables) >= 1:
        marker_col = 'Fälle'
        df['variable'].replace(cn.variable_dic, inplace=True)
        df.rename(columns = {'variable':marker_col}, inplace=True)
    elif len(cantons) > 1 and len(variables) == 1:
        marker_col = 'Kanton'
    elif len(cantons) > 1 and len(variables) > 1:
        marker_col = 'Fälle'
        df['variable'].replace(cn.variable_dic, inplace=True)
        df['variable'] = df['variable']+ ' (' + data['Kanton'] + ')'
        df.rename(columns = {'variable':marker_col}, inplace=True)

    return df


def get_titles():
    """
    Returns the titles for the y axis and the plot based on the selected cantons and variables 
    and depending wether the plots are grouped. E.g. if the plots are grouped by cantons, the 
    plot title is automatically the canton accronym
    """

    if len(cantons) == 1 and len(variables) >= 1:
        plot_title = cantons[0]
        ax_title = 'Fälle'
        marker_col = 'Fälle'
    elif len(cantons) > 1 and len(variables) == 1:
        plot_title = cn.variable_dic[variables[0]]
        ax_title = 'Fälle'
        marker_col = 'Kanton'
    elif len(cantons) > 1 and len(variables) > 1:
        plot_title = ''
        ax_title = 'Fälle'
        marker_col = 'Fälle'

    value_col = 'value'
    if plot_type == 'bc':
        plot_title += ', Datum: ' + selected_date
        
    return plot_title, ax_title, marker_col, value_col


def show_group_plot():
    """
    Function is called if plot grouped by is set to a value other than none. in this case, for 
    each distinct value of the grouper (either variable or canton) a seperate plot is generated.
    """

    group_list = []
    df = data[['Kanton','date','variable','value']].copy(deep=True)
    if group_plot == 'canton':
        df = df[df['variable'].isin(variables)]
        filter_field = 'Kanton'
        marker_col = 'Fälle'
        df['variable'].replace(cn.variable_dic, inplace=True)
        df.rename(columns = {'variable': marker_col}, inplace=True)
        if len(cantons) > 0:
            group_list = cantons
        else:
            group_list = cn.CANTON_LIST
    if group_plot == 'var':
        df = df[df['Kanton'].isin(cantons)]
        filter_field = 'variable'
        marker_col = 'Kanton'
        data.rename(columns = {'Kanton':marker_col}, inplace=True)
        if len(variables) > 0:
            group_list = variables
        else:
            group_list =cn.variable_dic.keys()
    
    ax_title = 'Fälle'
    for group in group_list:
        if group_plot == 'var':
            plot_title = cn.variable_dic[group]
            value_col = cn.variable_dic[group]
        else:
            plot_title = group
            value_col = group
        data_filtered = df[data[filter_field] == group]
        show_time_series(data_filtered, plot_title, ax_title, marker_col, 'value', 'date')


def show_result():
    """
    Renders the results on the result panel.
    """

    global data
    global y_max
    global y_log
    
    def show_info():
        min_date = data.min(axis = 0)['date']
        max_date = data.max(axis = 0)['date']
        st.markdown('## Covid-19 Data Explorer')
        st.markdown(f'Letzter Abgleich mit Datenquellen: {last_refresh_date}')
        text = open(r"info.md", encoding="utf-8").read()
        st.markdown(text.format(min_date.strftime('%d/%m/%Y'),max_date.strftime('%d/%m/%Y')), unsafe_allow_html=True)
        
        text = """Diese Applikation wurde von [Lukas Calmbach](mailto:lcalmbach@gmail.com) \
        in [Python](https://www.python.org/) entwickelt. Als Frameworks wurden [Streamlit](https://streamlit.io/) \
        und [Altair](https://altair-viz.github.io/) eingesetzt. Der Quellcode ist auf [github](https://github.com/lcalmbach/covid-bs) publiziert"""
        st.sidebar.info(text)

    def show_current_numbers():   
        _df, _most_recent_date = read_values_bs()
        st.markdown(f'### Aktuelle COVID-19 Fallzahlen in Basel-Stadt ({_most_recent_date.strftime("%d.%m.%Y")})')
        st.markdown(get_values_bs_comment(_df, _most_recent_date),unsafe_allow_html = True)
        st.dataframe(_df)
        st.markdown(get_incidence_comment(),unsafe_allow_html=True)
        

    def show_metadata():
        text=open(r"fields.md", encoding="utf-8").read()
        st.markdown(text, unsafe_allow_html=True)

    df = pd.DataFrame()
    if  plot_type == 'dist_bs':
        df = bs_data.copy(deep=True)
    else:
        df = filter_data()
        if  plot_type in ('bc','ani'):
            df = df[df['Kanton'] != 'CH']#.copy(deep=True)
            df = df[['Kanton','date','variable','value']]
        else:
            df = df[['Kanton','date','variable','value']]#.copy(deep=True)
    if plot_type == 'inf':
        show_info()
    elif plot_type == 'situation':
        show_current_numbers()
    elif plot_type == 'fields':
        show_metadata()
    elif plot_type == 'ts' and group_plot == 'none':
        plot_title, ax_title, marker_col, value_col = get_titles()
        df = rename_columns(df)
        show_time_series(df, plot_title, ax_title, marker_col, value_col, 'date')
    elif plot_type == 'ts':
        show_group_plot()
    elif plot_type == 'bc':
        # remove CH from data
        plot_title, ax_title, marker_col, value_col = get_titles()
        df = rename_columns(df)
        chart = get_bar_chart(df, plot_title, ax_title, marker_col, value_col, 'Kanton')
        st.altair_chart(chart)
    elif plot_type == 'dist_bs':
        plot_title = 'Verstorbene nach Alter und Geschlecht, Kanton BS'
        marker_col = 'age_gender_agg'
        value_col = 'n_deceased'
        ax_title = 'Verstorbene'
        df = bs_data.groupby(['age_gender_agg']).sum()
        df = df.reset_index()
        
        chart = get_bar_chart(df, plot_title, ax_title, marker_col, value_col, 'age_gender_agg')
        st.altair_chart(chart)

        plot_title = 'Verstorbene nach Geschlecht, Kanton BS'
        ax_title = 'Verstorbene'
        df = bs_data[bs_data['n_deceased'].astype(int) > 0].groupby(['Date', 'Gender']).sum().reset_index()
        df['date_gender_agg'] = df['Date'].astype(str) + df['Gender']
        marker_col = 'Date'
        y_max = 6
        chart = get_bar_chart(df, plot_title, ax_title, marker_col, value_col, 'Gender')
        st.altair_chart(chart)
        y_max = 0
        show_time_series(df, plot_title, ax_title, 'Gender', 'n_deceased', 'Date')
        
        ax_title = 'Verstorbene kumuliert'
        df = bs_data[bs_data['n_deceased'].astype(int) > 0].groupby(['Gender','Date']).sum().groupby(level=0).cumsum().reset_index()
        show_time_series(df, plot_title, ax_title, 'Gender', 'n_deceased', 'Date')
    elif plot_type == 'ani':
        generate_animation(df)
    elif plot_type == 'comp_sf':
        # calling read_sterbefaelle_bs so the initial load does not take too long
        df_sterbefaelle, df_sterbefaelle_week, df_sterbefaelle_month = read_sterbefaelle_bs()
        marker_col = 'Sterbedatum'
        group_col = 'Todesursache'
        value_col = 'Fälle'
        ax_title = 'Verstorbene'
        plot_title = 'Anteil Covid-Fälle an Anzahl der Verstorbenen in BS'
        chart = get_bar_chart(df_sterbefaelle, plot_title, ax_title, marker_col, value_col, group_col)
        st.altair_chart(chart)
        text = """Der Vergleich kann nur bis zum Datum heute - 15 Tagen durchgeführt werden, da die Zahl der Verstorbenen 
        in der Regel mit einigen Tagen Verspätung eintreffen und in den vergangenen 2 Wochen ein Teil 
        der Nicht-Covid-Sterbefälle noch nicht gemeldet wurde. Covid-Sterbefälle werden hingegen tagesgenau rapportiert."""
        st.markdown(text)
        plot_title = 'Total Gestorbene in Basel-Stadt pro Woche'
        value_col = 'Anzahl Gestorbene total'
        ax_title = 'Anzahl'
        time_col = 'Startdatum Woche'
        from_year, to_year = st.slider('Eingrenzung Zeitintervall:',1991, 2020, (1991, 2020))
        data_filtered = df_sterbefaelle_week[(df_sterbefaelle_week[time_col].dt.year >= from_year) & (df_sterbefaelle_week[time_col].dt.year <= to_year)]
        show_time_series_sterbefaelle(data_filtered, plot_title, ax_title, value_col, time_col)
        text = """Im März 2020 - mit den meisten Covid-Todesfällen in Basel-Stadt - zeichnet sich zwar deutlich eine Spitze ab, ähnlich hohe wöchentliche 
        Sterberaten traten aber auch im Feb. 2017, Januar 2009 und März 2004, sowie recht häufig vor dem Jahr 2004 auf. Die Wohnbevölkerung von Basel-Stadt lag
        im 1990 bei 199,411 Einwohner und war somit tiefer als Ende 2019, sodass die tendenziell höhere Sterberate vor 2004 nicht mit einer 
        höheren Einwohnerzahl erklärt werden kann.<br>Die rote Linie glättet die wöchentlichen Daten in einem Zeitfenster von 30 Tagen (moving average) und erlaubt es,
        Trends besser zu erkennen."""
        st.markdown(text, unsafe_allow_html=True)
        
        plot_title = 'Box-Plot der monatlichen Sterberaten in Basel-Stadt seit 2005'
        show_box_plot(df_sterbefaelle_month, plot_title, ax_title, 'Monat', value_col)
        
        text = """Die Box-Plot zeigt die statistische Verteilung der Sterberaten für jeden Monat seit 2005. Ein Box-Plot vermittelt einen Eindruck darüber, 
        in welchem Bereich die Daten liegen und wie sie sich über diesen Bereich verteilen. Der weisse Strich in der Mitte repräsentiert den Median,
        der Kasten das Intervall zwischen dem 25 und 75% Perzentil und die vertiklen Striche das 1,5-Fache des Interquartilsabstands. Werte, die über 
        oder unter den vertikalen Strichen (Whisker) zu liegen kommen, werden als Ausreisser bezeichnet: Sie heben sich deutlich von der Grundverteilung ab und 
        deuten auf eine Anomalie hin, in obiger Grafik auf eine Übersterblichkeit.<br> 
        Gemäss dieser graphischen Darstellung liegt die Sterberate im März 2020 mit 221 Gestorben zwar über den Normalwerten für den Monat (75% Perzentil: 209) ist aber 
        kein deutlicher Ausreisser. Es ist naheliegend, dass die eingeleiteten Massnahmen (Lockdown, Social Distancing) wesentlich dazu beigetragen haben, 
        dass sich die Sterberate im Kanton Basel-Stadt auch während der Spitze der Corona-Todesfälle nicht signifikant vom Normalwert entfernen konnte. 
        """
        st.markdown(text, unsafe_allow_html=True)
        show_data = st.checkbox('Tabellen-Werte anzeigen?')
        if show_data:
            st.write(df_sterbefaelle_month)


def generate_animation(df: pd.DataFrame):
    global y_max

    dates = df.date.unique()
    ls = [type(item) for item in dates]
    plot_title, ax_title, marker_col, value_col = get_titles()
    # data_filtered = data[data['date'] == dates[0]]
    marker_col = 'Kanton'
    progress_bar = st.progress(0)
    progress_timestep_inc = 1 / len(dates) * 100
    progress_timestep = 0
    anim = st.empty()
    y_max = df.max(axis = 0)['value']
    value_col = 'value'
    data.fillna(0)
    i=1
    for dt in dates:
        data_filtered = df[df['date'] == dt]
        ts = pd.to_datetime(str(dt))
        plot_title = cn.variable_dic[variables[0]] + ', Datum: ' + ts.strftime('%d.%m.%Y')
        chart = get_bar_chart(data_filtered, plot_title, ax_title, marker_col, value_col, 'Kanton')
        anim.altair_chart(chart)
        # chart.bar_chart(data_filtered)
        if dt == cn.DATE_LIST[-1] or progress_timestep > 100:
            progress_timestep = 100
        progress_bar.progress(progress_timestep)
        progress_timestep = int(i * progress_timestep_inc)
        time.sleep(0.8)
        i += 1

def show_side_bar(version: str):
    """
    Renders the navigation and filter controls on the sidebar. The controls are context sensitive:
    e.g. for bar charts there is a selection box for dates, not no canton selection, for time 
    series plots there is not date selection, but a selection of cantons.
    """
    
    button_clicked = False
    cantons = ['BS']
    variables = ['ncumul_conf']
    group_plot = 'canton'
    selected_date = ''
    plot_width = 800
    plot_height = 400
    y_max = 0
    y_log = False

    st.sidebar.markdown("### 🦠COVEX v" + version)

    plot_type = st.sidebar.selectbox(label='Wähle eine Darstellung', options = list(cn.CHART_DIC.keys()),
        format_func=lambda x: cn.CHART_DIC[x], index = 0)
    if plot_type == 'ts':
        cantons = st.sidebar.multiselect(label='Wähle Kantone', options=cn.CANTON_LIST, default=['BS', 'BL'])
        group_plot = st.sidebar.selectbox(label='Gruppiere Plots nach', options = list(cn.CHART_GROUP_DIC.keys()),
            format_func=lambda x: cn.CHART_GROUP_DIC[x], index = 1)
        variables = st.sidebar.multiselect(label='Wähle Variable', options = list(cn.variable_dic.keys()),
            format_func=lambda x: cn.variable_dic[x], default = ['ncumul_conf','ncumul_released','n_active'])
        selected_date = None
    elif plot_type == 'bc':
        cantons = cn.CANTON_LIST
        variables[0] = st.sidebar.selectbox(label='Wähle Variable', options = list(cn.variable_dic.keys()),
            format_func=lambda x: cn.variable_dic[x], index = 1)
        # go back 7 days to be sure that there is any data
        selected_date = st.sidebar.selectbox(label='Wähle Datum', options = cn.DATE_LIST, index = len(cn.DATE_LIST)-7) 
    elif plot_type == 'ani':
        cantons = cn.CANTON_LIST
        variables[0] = st.sidebar.selectbox(label='Wähle Variable', options = list(cn.variable_dic.keys()),
            format_func=lambda x: cn.variable_dic[x], index = 1)
        button_clicked = st.sidebar.button('Animation Starten')

    if plot_type in ('bc','ts','ani','dist_bs'):  
        st.sidebar.markdown('---')
        if plot_type == 'ts':
            y_log = st.sidebar.checkbox('Y Achse logarithmisch')
        y_max = st.sidebar.number_input('Y Achse Maximum (Auto = 0)')
        plot_width = st.sidebar.number_input('Plot Breite (Pixel)', value = plot_width)
        plot_height = st.sidebar.number_input('Plot Höhe (Pixel)', value = plot_height)
    return cantons, plot_type, variables, group_plot, plot_width, plot_height, y_max, selected_date, button_clicked, y_log


def show_box_plot(data: pd.DataFrame, plot_title: str, ax_title: str, marker_col: str, value_col: str):
    chart = alt.Chart(data).mark_boxplot().encode(
        x=alt.X(f'{marker_col}:O', sort=list(cn.MONTH_DIC.values())),
        y=f'{value_col}:Q'
    )
    #df = pd.DataFrame({'Monat': [3], 'Wert': [220]})
    #comp = alt.Chart(df).mark_circle(size=60, color = 'red').encode(
    #    x=alt.X('Monat', scale = alt.Scale(domain=[0.4, 12.5]), axis=alt.Axis(tickCount=0)), 
    #    y='Wert',
    #    tooltip=['Monat', 'Wert']).interactive()
    chart = (chart).properties(width=plot_width, height=plot_height, title=plot_title)
    st.altair_chart(chart)


def get_bar_chart(data: pd.DataFrame, plot_title: str, ax_title: str, marker_col: str, value_col: str, color_col:str):
    """Returns a altair barchart object"""

    tooltips = [value_col, marker_col]
    if 'Kanton' in data.columns:
        tooltips.append('Kanton')
        xax_title = 'Kantone'
    else:
        xax_title = ''
    # remove CH total 
    if y_max == 0:
        scy = alt.Scale()
    else:
        scy = alt.Scale(domain=(0, y_max))

    if marker_col == 'Date':
        xax=alt.X(f'{marker_col}:T', axis=alt.Axis(title='', labelAngle = 30, format="%d.%m"))
    elif marker_col == 'Sterbedatum':
        xax=alt.X(f'{marker_col}:T', axis=alt.Axis(title='', labelAngle = 30, format="%d.%m")) 
    else:
        xax = alt.X(f"{marker_col}:O", axis = alt.Axis(title=xax_title))
    
    if 'Kanton' in data.columns:
        clr = alt.condition(
            alt.datum[color_col] == 'BS',
            alt.value('orange'),
            alt.value('steelblue'))
    else:
        clr = alt.Color(color_col,
                scale=alt.Scale(scheme=cn.COLOR_SCHEMA))
    bar = alt.Chart(data).mark_bar().encode(
        x=xax,
        y=alt.Y(f'{value_col}:Q',
            title=ax_title, 
            scale=scy
            ),
        color = clr,
        order=alt.Order(value_col, sort='ascending'),
        tooltip=tooltips)

    # not sure why the mean is sometime lower than the minimum bar mean
    # rule = alt.Chart(data).mark_rule(color='red').encode(
    # y='mean({}):Q'.format(val_par)

    chart = bar.properties(width=plot_width, height=plot_height, title=plot_title)

    return chart

def show_time_series(data, plot_title: str, ax_title: str, marker_col: str, value_col: str, time_col: str):
    """
    Plots a time series plot. for time series plots the marker group by unit is automatically set to the
    station.

    units:
    -----------
    :param title:
    :param df:
    :param par:
    :return:
    """

    x_lab = ''
    y_lab = ax_title
    if y_log:
        # remove 0 values for log 
        data = data[data[value_col] > 0]
        if y_max == 0:
            scy = alt.Scale(type='log',base=10)
        else:
            scy = alt.Scale(type='log',base=10, domain=(1, y_max))
    else:
        if y_max == 0:
            scy = alt.Scale()
        else:
            scy = alt.Scale(domain=(0, y_max))
    
    #all_dates = data['date'].unique().tolist()
    #all_dates.format(formatter=lambda x: x.strftime('%Y-%m-%d'))
    line = alt.Chart(data).mark_line(point=True, clip=True).encode(
        x=alt.X(f'{time_col}:T',
                axis=alt.Axis(title=x_lab, labelAngle = 30, format="%d.%m.%y")),  # https://github.com/d3/d3-time-format#locale_format
        y=alt.Y(f'{value_col}:Q',
                axis=alt.Axis(title=y_lab),
                scale=scy
                ),
        color = alt.Color(marker_col,
                scale=alt.Scale(scheme=cn.COLOR_SCHEMA)),
        tooltip=[alt.Tooltip(f'{marker_col}:O'),
              alt.Tooltip(f'{time_col}:T', format='%A, %B %e'),
              alt.Tooltip(f'{value_col}:Q', format='.1f'),
              ],
    )
    
    chart = line.properties(title=plot_title, width = plot_width, height = plot_height)
    st.altair_chart(chart)
    # st.table(data)


def show_time_series_sterbefaelle(data, plot_title: str, ax_title: str, value_col: str, time_col: str):
    """
    Plots a time series plot. for time series plots the marker group by unit is automatically set to the
    station.

    units:
    -----------
    :param title:
    :param df:
    :param par:
    :return:
    """

    x_lab = ''
    y_lab = ax_title

    if y_max == 0:
        scy = alt.Scale()
    else:
        scy = alt.Scale(domain=(0, y_max))
    
    #all_dates = data['date'].unique().tolist()
    #all_dates.format(formatter=lambda x: x.strftime('%Y-%m-%d'))
    window = 15
    mov_avg = alt.Chart(data).mark_line(
        color='red',
        size=2
    ).transform_window(
        rolling_mean=f'mean({value_col})',
        frame=[-window, window]
    ).encode(
        x=f'{time_col}:T',
        y='rolling_mean:Q'
    )

    line = alt.Chart(data).mark_line(point=False, clip=True).encode(
        x=alt.X(f'{time_col}:T',
                axis=alt.Axis(title=x_lab, labelAngle = 30, format="%d.%m.%y")),  # https://github.com/d3/d3-time-format#locale_format
        y=alt.Y(f'{value_col}:Q',
                axis=alt.Axis(title=y_lab),
                scale=scy
                ),
         tooltip=[alt.Tooltip(f'{time_col}:T', format='%d.%m.%y'),
              alt.Tooltip(f'{value_col}:Q', format='.1f'),
              ],
    )
    chart = (line + mov_avg).properties(title=plot_title, width = plot_width, height = plot_height)
    st.altair_chart(chart)