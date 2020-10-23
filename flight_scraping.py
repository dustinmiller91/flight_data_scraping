import requests
from bs4 import BeautifulSoup as bs
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def get_table_df(url):
    '''
    A function to pull data from a  table on the flightaware webpage

    Parameters
    ----------
    url : String
        DESCRIPTION: a URL string for the web page we want to scrape

    Returns
    -------
    df : A pandas Dataframe
        DESCRIPTION: Data contained in the flights table on the web page

    '''
    # Basic bs4 web scraping
    ws_src = requests.get(url).content
    ws_soup = bs(ws_src, 'lxml')
    
    # Grab our table and split it into individual rows
    table = ws_soup.find_all('table', attrs = {'class' : 'prettyTable fullWidth'})[0]
    rows = table.find_all('tr')
    
    # Column Names for our dataframe
    cols = ['ID', 'TYPE', 'ORIGIN', 'DEST', 'DEPT', 'ETA', 'ETE']
    df = pd.DataFrame(columns = cols)
    
    # Iterate through each row and append it to the dataframe as a pd.Series
    for row in rows:
        d_ls = [d.text for d in row.find_all('td')]
        if len(d_ls) != 7:
            continue
        df = df.append(pd.Series(d_ls, index = cols), ignore_index = True)
        
    # Return our completed dataframe
    return df


# Aircraft we'll be collecting data on
aircraft = {
    'Pilatus PC-12' : 'PC12',
    'Cessna Caravan' : 'C208',
    'Beechcraft Super King Air 200' : 'BE20',
    'Cessna Citation Excel/XLS' : 'C56X'
}

# Instantiate an empty dict for storing our flight time data
avg_dict = {}

# Get data for each aircraft code
for ac, code in aircraft.items():
    print(f'Collecting data for {ac}: {code}')

    # The flightaware website only displays 20 results per page, so we have to
    # iterate through, appending our data each time in groups of 20 until we
    # get an empty dataframe, at which point we stop
    base_url = f'https://flightaware.com/live/aircrafttype/{code}'
    df_base = get_table_df(base_url)
    loop = True
    i = 20
    while loop:
        api_sfx = f'?;offset={i};order=actualdeparturetime;sort=DESC'
        df_temp = get_table_df(base_url + api_sfx)
        if len(df_temp) == 0:
            break;
        df_base = df_base.append(df_temp)
        i += 20
        
    # Output data to csv just in case
    df_base.to_csv(f'{code}_flight_data.csv')

    # Since we're not doing anything else with this data, it's safe to just
    # drop our rows without Estimated Time Enroute (ETE) values
    df_base = df_base.replace('', np.nan).dropna(subset = ['ETE'])

    # Convert our ETE column from hh:mm to a timedelta object
    df_base['ETE'] = df_base['ETE'] + ':00'
    df_base['ETE'] = pd.to_timedelta(df_base['ETE'], unit = 'm')
    
    # Calculate the mean flight time in mins (float) and save it to avg_dict
    avg_dict[code] = df_base['ETE'].mean().seconds / 60
    
# Basic bar chart
fig, ax = plt.subplots()
plt.bar(avg_dict.keys(), avg_dict.values(),
        color = ['red', 'green', 'blue', 'orange'],
        edgecolor = 'black', alpha = .75)
ax.set_xlabel('Aircraft Code')
ax.set_ylabel('Average Flight Time (Minutes)')
plt.show()