# import packages
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import shutil
import glob
import os
from unicodedata import *
import time
# open a chrome browser using selenium 
#driver = webdriver.Chrome(ChromeDriverManager().install())
driver = webdriver.Chrome(executable_path='../../home/gitpod/.pyenv/versions/3.8.12/lib/python3.8/site-packages/selenium/webdriver/chromium/webdriver.py')
# got to web page where excel file links are located
driver.get("https://www.dshs.texas.gov/coronavirus/additionaldata/")
# these options allow selenium to download files 
options = Options()
options.add_experimental_option("browser.download.folderList",2)
options.add_experimental_option("browser.download.manager.showWhenStarting", False)
options.add_experimental_option("browser.helperApps.neverAsk.saveToDisk", "application/octet-stream,application/vnd.ms-excel")

# initialize an object to the location on the web page and click on it to download
link = driver.find_element_by_xpath('/html/body/form/div[4]/div/div[3]/div[2]/div/div/ul[1]/li[1]/a')
link.click()
# Wait for 15 seconds to allow chrome to download file
time.sleep(15)


# locating most recent .xlsx downloaded file 
list_of_files = glob.glob('/Users/tsbloxsom/Downloads/*.xlsx') 
latest_file = max(list_of_files, key=os.path.getmtime)
# replace "\" with "/" so file path can be located by python
latest_file = latest_file.replace("\\", "/")
latest_file
# we need to locate the old .xlsx file(s) in the dir we want to store the new xlsx file in
list_of_files = glob.glob('/Users/tsbloxsom/Documents/GitHub/Texas-census-county-data-project/Automate collecting of data notebooks/*.xlsx') 
# need to delete old xlsx file(s) so if we download new xlsx file with same name we do not get an error while moving it
for file in list_of_files:
    print("deleting old xlsx file:", file)
    os.remove(file)
# Move the new file from the download dir to the github dir 
shutil.move(latest_file,'/Users/tsbloxsom/Documents/GitHub/Texas-census-county-data-project/Automate collecting of data notebooks/')

import pandas as pd
import re
pd.set_option('display.max_rows', 500)
pd.options.display.max_colwidth = 150
# again we need to locate the .xlsx file 
list_of_files = glob.glob('/Users/tsbloxsom/Documents/GitHub/Texas-census-county-data-project/Automate collecting of data notebooks/*.xlsx') 
latest_file = max(list_of_files, key=os.path.getctime)
print(latest_file.split("\\")[-1])
df = pd.read_excel("{}".format(latest_file),header=None)

# print out latest COVID data datetime and notes
date = re.findall("- [0-9]+/[0-9]+/[0-9]+ .+", df.iloc[0, 0])
#print("COVID cases latest update:", date[0][2:])
#print(df.iloc[1, 0])
#print(str(df.iloc[262:266, 0]).lstrip().rstrip())
#drop non-data rows
df2 = df.drop([0, 1, 258, 260, 261, 262, 263, 264, 265, 266, 267])
# clean column names
df2.iloc[0,:] = df2.iloc[0,:].apply(lambda x: x.replace("\r", ""))
df2.iloc[0,:] = df2.iloc[0,:].apply(lambda x: x.replace("\n", ""))
df2.columns = df2.iloc[0]
clean_df = df2.drop(df2.index[0])
clean_df = clean_df.set_index("County Name")
# convert clean_df to a .csv file
clean_df.to_csv("Texas county COVID cases data clean.csv")

import plotly.express as px
list_of_files = glob.glob('/Users/tsbloxsom/Documents/GitHub/Texas-census-county-data-project/Automate collecting of data notebooks/*.csv') 
latest_file = max(list_of_files, key=os.path.getmtime)
latest_file.split("\\")[-1]
df = pd.read_csv(latest_file.split("\\")[-1])

# convert df into time series where rows are each date and clean up
df_t = df.T
df_t.columns = df_t.iloc[0]
df_t = df_t.iloc[1:]
df_t = df_t.iloc[:,:-2]
# next lets convert the index to a date time, must clean up dates first
def clean_index(s):
    s = s.replace("*","")
    s = s[-5:]
    s = s + "-2020"
    #print(s)
    return s
df_t.index = df_t.index.map(clean_index)
df_t.index = pd.to_datetime(df_t.index)

# initalize df with three columns: Date, Case Count, and County
anderson = df_t.T.iloc[0,:]
ts = anderson.to_frame().reset_index()
ts["County"] = "Anderson"
ts = ts.rename(columns = {"Anderson": "Case Count", "index": "Date"})

# This while loop adds all counties to the above ts so we can input it into plotly
x = 1
while x < 254:
    new_ts = df_t.T.iloc[x,:]
    new_ts = new_ts.to_frame().reset_index()
    new_ts["County"] = new_ts.columns[1]
    new_ts = new_ts.rename(columns = {new_ts.columns[1]: "Case Count", "index": "Date"})
    ts = pd.concat([ts, new_ts])
    x += 1
#save long form df for dash app
ts.to_csv("time_series_plotly.csv")


import dash
import dash_core_components as dcc
import dash_html_components as html
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
colors = {
    'background': '#F0F8FF',
    'text': '#00008B'
}
# assume you have a "long-form" data frame
# see https://plotly.com/python/px-arguments/ for more options
df = pd.read_csv("time_series_plotly.csv")
fig = px.scatter(df, x='Date', y='Case Count', color='County')
fig.update_layout(
    plot_bgcolor=colors['background'],
    paper_bgcolor=colors['background'],
    font_color=colors['text']
)
markdown_text = '''
### Texas COVID-19 Dashboard
Creator: Truett Bloxsom, [LinkedIn](https://www.linkedin.com/in/truett-bloxsom/), [github](https://github.com/tsbloxsom)
This is my first interactive dashboard using Dash! Hope you like it!
This first plot is Texas COVID-19 accumulated cases by county over time
Source for data: [dshs.texas.gov](https://www.dshs.texas.gov/coronavirus/additionaldata/)
'''
app.layout = html.Div([
    dcc.Markdown(children=markdown_text,
        style={
            'backgroundColor': colors['background'],
            'textAlign': 'center',
            'color': colors['text']
        }),
    
    dcc.Graph(
        id='example-graph',
        figure=fig
    )
])
if __name__ == '__main__':
    app.run_server(debug=True)