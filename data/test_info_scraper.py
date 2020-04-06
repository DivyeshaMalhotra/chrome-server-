import pandas as pd

from info_scraper import getCoronaCharities

charities_df = pd.read_json('Data/all_charities.json')
charities_list = charities_df.to_dict(orient="records")

print (getCoronaCharities(charities_list))