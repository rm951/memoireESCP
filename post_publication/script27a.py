import pandas as pd
import eurostat

def analyze_budget_data(date_analysis):
    print(f"\nStarting analysis for {date_analysis}")
    
    # Reading CSV file
    print("Reading CSV file...")
    df = pd.read_csv('BDF/Csv/C05.csv', sep=";", index_col="IDENT_MEN")

    # Dropping non-relevant columns
    print("Dropping non-relevant columns...")
    columns_to_delete = df.columns[df.columns.str.startswith('C13') | df.columns.str.startswith('C14')]
    df = df.drop(columns=columns_to_delete)
    df = df.drop(columns=["CTOT", "pondmen"])

    # Calculating proportions
    print("Calculating proportions...")
    df_prop = df.divide(df.sum(axis=1), axis=0)
    df_prop.rename(columns=lambda x: x.replace('C', ''), inplace=True)

    # Fetching inflation data
    print("Fetching inflation data...")
    df_inflation_raw = eurostat.get_data_df(code="PRC_HICP_MANR", filter_pars={'geo': 'FR', 'startPeriod': "2021-03"})
    df_inflation_raw = df_inflation_raw.rename(columns={'geo\TIME_PERIOD': 'geo'})
    df_correspondances = pd.read_csv("correspondances.csv", dtype="str", sep=";")
    df_correspondances.set_index('colonnes de df_prop', inplace=True)
    df_inflation = df_inflation_raw[df_inflation_raw['coicop'].str.startswith('CP')]
    df_inflation['coicop'] = df_inflation['coicop'].str.replace('CP', '')
    df_inflation = df_inflation.loc[:, ["coicop", date_analysis]]
    df_inflation = df_inflation.set_index('coicop')

    # Calculating inflation per cell
    print("Calculating inflation per cell...")
    def cell_func(cell_value, col_name):
        coicop = df_correspondances.loc[col_name]['colonnes de df_inflation correspondante']
        return df_inflation.loc[coicop][date_analysis] * cell_value

    def col_func(col):
        column_name = col.name
        return col.apply(cell_func, args=(column_name,))

    # Calculating inflation per household
    print("Calculating inflation per household...")
    df_inflations = df_prop.apply(col_func)
    df_inflation_by_household = pd.DataFrame(df_inflations.sum(axis=1))
    df_inflation_by_household = df_inflation_by_household.rename(columns={0: "inflation"})

    # Saving results to a CSV file
    print("Saving results to a CSV file...")
    df_inflation_by_household.to_csv(f"BDF/computed_inflation_by_household_{date_analysis}.csv")

    print(f"Analysis for {date_analysis} completed.")


dates = pd.date_range(start="2023-03", end="2023-04", freq='M')

for date in dates:
    date_str = date.strftime('%Y-%m')
    analyze_budget_data(date_str)
