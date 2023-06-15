import pandas as pd
import statsmodels.api as sm
import eurostat


def analyze_inflation(date_analysis, df_to_merge):
    df_inflation_by_household = pd.read_csv(
        f'BDF/computed_inflation_by_household_{date_analysis}.csv', index_col="IDENT_MEN")

    df_menage = pd.read_csv("BDF/Csv/MENAGE.csv", sep=";", encoding='latin1')
    df_menage = df_menage.set_index("IDENT_MEN")

    df_dep_men = pd.read_csv("BDF/Csv/DEPMEN.csv", sep=";", encoding='latin1')
    df_dep_men = df_dep_men.set_index("IDENT_MEN")

    df_menage = pd.merge(left=df_menage, right=df_dep_men,
                         left_index=True, right_index=True)

    variables = ["AGEPR", "TUU", "DNIVIE1", "Stalog",
                 "NENFANTS", "COUPLEPR", "Chaufp", "TYPVOIS"]
    df_filtered = df_menage.loc[:, variables]

    def clean_variable(df, variable, variable_ref, numerical, labels=[], bins=[]):
        df[f'{variable}_category'] = pd.cut(
            x=df[variable], bins=bins, labels=labels, right=False) if numerical else df[variable]
        df = pd.concat(
            [df, pd.get_dummies(data=df[f"{variable}_category"])], axis=1)
        df = df.drop([variable, f"{variable}_category", variable_ref], axis=1)
        return df

    df_filtered = clean_variable(df=df_filtered, variable="AGEPR", labels=[
                                 "Moins de 30 ans", "De 30 à 44 ans", "De 45 à 59 ans", "De 60 à 74 ans", "75 ans et plus"], variable_ref="De 45 à 59 ans", bins=[0, 30, 45, 60, 75, 102], numerical=True)
    df_filtered = clean_variable(df=df_filtered, variable="TUU", variable_ref="Ville moyenne", numerical=True, bins=[
                                 0, 3, 5, 9], labels=["Rural et petite ville", "Ville moyenne", "Grande ville"])
    df_filtered = clean_variable(df=df_filtered, variable="DNIVIE1", variable_ref="Moyen", numerical=True, bins=[
                                 0, 3, 9, 11], labels=["Pauvre", "Moyen", "Riche"])
    df_filtered = clean_variable(df=df_filtered, variable="COUPLEPR", variable_ref="N'habite pas en couple", numerical=True, bins=[
                                 0, 3, 4], labels=["Habite en couple", "N'habite pas en couple"])
    df_filtered = clean_variable(df=df_filtered, variable="Stalog", variable_ref="Locataire", numerical=True, bins=[
                                 0, 4, 7], labels=["Propriétaire", "Locataire"])
    df_filtered = clean_variable(df=df_filtered, variable="Chaufp", variable_ref="Chauffage central ou mixte", numerical=True, bins=[
                                 0, 4, 5, 8], labels=["Chauffage central ou mixte", "Chauffage électrique individuel", "Chauffage non-électrique"])
    df_filtered = clean_variable(df=df_filtered, variable="TYPVOIS", variable_ref="Immeubles", numerical=True, labels=[
                                 "Pavillonnaire", "Immeubles"], bins=[0, 3, 6])

    df_filtered = pd.merge(
        df_filtered, df_inflation_by_household, left_index=True, right_index=True)
    df_filtered = df_filtered.dropna()

    y = df_filtered['inflation']
    df_filtered = df_filtered.drop(columns=['inflation'])
    X = df_filtered
    X = sm.add_constant(X)

    model = sm.OLS(y, X)
    results = model.fit()

    coef_df = pd.DataFrame(
        {f'{date_analysis}': results.params}, index=X.columns)
    df_to_merge = pd.concat([coef_df, df_to_merge], axis=1)

    return df_to_merge


df = pd.DataFrame()

end_date = "2023-06"
dates = pd.date_range(start="2021-03", end=end_date, freq='M')

for date in dates:
    date_str = date.strftime('%Y-%m')
    df = analyze_inflation(date_str, df)

df_inflation_raw = eurostat.get_data_df(code="PRC_HICP_MANR", filter_pars={
                                        'geo': 'FR', 'startPeriod': "2021-03"})
df_inflation_raw = df_inflation_raw.rename(columns={'geo\TIME_PERIOD': 'geo'})
df_inflation_raw = df_inflation_raw[df_inflation_raw['coicop'] == "CP00"]
df = pd.concat([df, df_inflation_raw], join='inner')
df.rename(index={5: 'inflationMoyenne'}, inplace=True)

df.to_csv(f"inflationAnalysis_up_to{end_date}.csv")
df.to_json(f"inflationAnalysis_up_to{end_date}.json")
