import os, time

def file_age(filepath, time_unit: str):
    """
    returns age of file in specified time unit, if file does not exist: returns negative number
    """

    result = -1
    if os.path.exists(filepath):
        result = time.time() - os.path.getmtime(filepath)
        print(result)
        if time_unit == 'm':
            result /= 60
        elif time_unit == 'h':
            result /= 3600
        elif time_unit == 'd':
            result /= (3600 * 24)
    return result

def calc_year_month(row, year_col: str, month_col: str, sep: str):
    """ generates year month expressions in a panda column: 2020-03"""
    result = f'{row[year_col]}{sep}{row[month_col]}'
    return result
