import json, sys, csv
from tqdm import tqdm
import seaborn as sns
import pandas as pd


with open('profile_dict.json', 'r') as f:
		data_=f.read()
		data_dict = dict(json.loads(data_))
		# print(data_dict)
		df = (pd.DataFrame
			.from_dict(data_dict, orient='index')
			.reset_index()
			.rename(columns = {'index':'attribute', 0:'frequency'})
			.sort_values(by=['frequency'], ascending = False)
			.reset_index()
			.drop(labels=['index'], axis=1))
		df.to_csv('metagenome_profile.csv')


# plot a fancy graph here