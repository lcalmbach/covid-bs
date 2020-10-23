import pandas as pd
from datetime import date, datetime, timedelta

MONTH_DIC = {1: 'Jan', 2: 'Feb', 3: 'Mrz', 4: 'Apr', 5: 'Mai', 6: 'Jun', 7: 'Jul', 
    8: 'Aug', 9: 'Sep', 10: 'Okt', 11: 'Nov', 12: 'Dez'}
COLOR_SCHEMA = "set1"
CHART_DIC = {'inf': 'Info',
            'fields': 'Erklärung der Felder',
            'situation': 'Aktuelle Zahlen',
            'ts': 'Zeitreihe',
            'bc': 'Balkendiagramm',
             # improve or scrap
             # 'ani': 'Balkendiagramm (animiert)',
            'dist_bs': 'Sterbefälle nach Alter und Geschlecht (BS)',
            'comp_sf': 'Anteil Covid-Sterbefälle an den Gestorbenen (BS)'
            } 
CHART_GROUP_DIC = {'none': 'keine', 
                    'canton': 'Kanton',
                    'var': 'Variable'
                    }
DATE_LIST = pd.date_range(start='2020-02-25', end=date.today())
DATE_LIST = DATE_LIST.format(formatter=lambda x: x.strftime('%d/%m/%Y'))
CANTON_LIST = ['ZH','BE', 'LU','UR', 'SZ','OW', 'NW', 'GL', 'ZG', 'FR', 'SO', 'SH', 'AR', 'AI', 'SG',
        'GR','TG','TI','VD','VS','NE','GE','JU','BL','BS','AG']
CANTON_LIST.sort()
CANTON_LIST.insert(0, 'CH')
variable_dic = {'ncumul_tested': 'getestet kum.', 
                'ncumul_conf': 'bestätigt kum.', 
                'ncumul_hosp': 'hospitalisiert kum.', 
                'ncumul_ICU': 'Intensivstation kum.', 
                'ncumul_vent': 'künst. Beatm. kum.',
                'ncumul_released': 'Genesungen kum.', 
                'ncumul_deceased': 'Todesfälle kum.',
                'n_conf': 'neue Fälle (berechnet)',
                'n_active': 'aktive Fälle (berechnet)',
                'ncumul_tested_pro_einw': 'getestet kum. pro 100k Einw.', 
                'ncumul_conf_pro_einw': 'bestätigt kum. pro 100k Einw.', 
                'ncumul_hosp_pro_einw': 'hospitalisiert kum. pro 100k Einw.', 
                'ncumul_ICU_pro_einw': 'Intensivstation kum. pro 100k Einw.', 
                'ncumul_vent_pro_einw': 'künst. Beatm. kum. pro 100k Einw.',
                'ncumul_released_pro_einw': 'Spitalentlassungen kum. pro 100k Einw..', 
                'ncumul_deceased_pro_einw': 'Todesfälle kum. pro 100k Einw.'}
min_date = datetime.today()
MAX_FILE_AGE_HOURS = 12
STERBEFAELLE_URL = "https://data.bs.ch/explore/dataset/100079/download/?format=csv&timezone=Europe/Berlin&lang=en&use_labels_for_header=true&csv_separator=%3B"
VALUES_BS_URL = "https://data.bs.ch/explore/dataset/100073/download/?format=csv&timezone=Europe/Zurich&lang=en&use_labels_for_header=true&csv_separator=%3B"
COVID_FAELLE_CH_URL = 'https://raw.githubusercontent.com/openZH/covid_19/master/COVID19_Fallzahlen_CH_total.csv'
FALLZAHLEN_BS_URL = 'https://raw.githubusercontent.com/openZH/covid_19/master/fallzahlen_kanton_alter_geschlecht_csv/COVID19_Fallzahlen_Kanton_BS_alter_geschlecht.csv'
BEVOELKERUNG_CH_URL = 'https://raw.githubusercontent.com/daenuprobst/covid19-cases-switzerland/master/demographics.csv'