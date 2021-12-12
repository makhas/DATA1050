import dash
from dash import dcc
from dash import html
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import pandas.io.sql as sqlio

import psycopg2
from psycopg2 import OperationalError


## READ COVID DATA FROM OWID REPO
latest_url = 'https://github.com/owid/covid-19-data/raw/master/public/data/latest/owid-covid-latest.csv'
df_cov = pd.read_csv(latest_url)


hist_url = 'https://covid.ourworldindata.org/data/owid-covid-data.csv'
df_hist = pd.read_csv(hist_url)
hist_feats = df_hist.columns
#df_cov = USA=df_hist.loc[df_hist['iso_code'] == 'USA']
latest_feats = df_cov.columns

## Determining if feature is continuous
THRESH = 0.01
def is_cont(data, cat_name):
    if data[cat_name].dtype != 'float64':
        return False
    if data[cat_name].nunique() / data[cat_name].count() < THRESH:
        return False
    return True
    

# Definitions of constants. This projects uses extra CSS stylesheet at `./assets/style.css`
COLORS = ['rgb(67,67,67)', 'rgb(115,115,115)', 'rgb(49,130,189)', 'rgb(189,189,189)']
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css', '/assets/style.css']

# Define the dash app first
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)


# Define component functions
def target_vis():
    return html.Div(children=[
        html.Div(children=[
            html.H2(children='Target Variable Visualization'),
            dcc.Dropdown(
                id='regressor_feature_dd',
                options=[{'label': col, 'value': col} for col in df_cov.columns],
                multi=False,
                placeholder='Feature to Plot Over',
                value=df_cov.columns[0]
            ),
            html.Div(children=[
                dcc.Graph(id='target_var_fig')]),
        ])
    ], className='row')


def timeline_vis():
    return html.Div(children=[
        html.Div(children=[
            html.H2("Timeline"),
            dcc.Dropdown(
                id='hist_feature_dd',
                options=[{'label': f, 'value': f} for f in hist_feats if df_hist[f].dtype != 'object'],
                multi=False,
                placeholder='Historical Feature to Visualize',
                value='new_cases_smoothed'
            ),
            # @TODO: remove 'date' as a label/value option
            dcc.Dropdown(
                id='hist_filter_feat_dd',
                options=[{'label': f, 'value': f} for f in hist_feats if df_hist[f].dtype == 'object'],
                multi=False,
                placeholder='Feature to Filter',
                value='location'
            ),
            dcc.Dropdown(
                id='hist_filter_val_dd',
                options=[],
                multi=True,
                placeholder='Value to Filter By',
                value=[df_hist.iloc[0]['location']] # Doesn't do anything, pretty sure. Since returned from callback immediately
            ),
            html.Div(children=[
                dcc.Graph(id='hist_timeline_fig')])
            ])
    ])


def history_compare():
    return html.Div(children=[
        html.Div(children=[
            html.H2("Historical Comparison"),
            dcc.Dropdown(
                id='date_to_compare_dd',
                options=[{'label': d, 'value': d} for d in df_hist['date'].unique()],
                multi=False,
                placeholder='Date to Compare To',
                value=df_hist.iloc[0]['date'] # put in db_info?
            ),
            dcc.Dropdown(
                id='feats_to_compare_dd',
                options=[{'label': f, 'value': f} for f in hist_feats],
                multi=True,
                placeholder='Features to Compare',
                value=['new_tests', 'new_cases']
            ),
            html.Div(children=[
                dcc.Graph(id='hist_comparison_fig')
            ])
        ])
    ])


# Sequentially add page components to the app's layout
def dynamic_layout():
    return html.Div([
        target_vis(),
        timeline_vis(),
        history_compare(),
    ], className='row', id='content')


# set layout to a function which updates upon reloading
app.layout = dynamic_layout


# Defines the dependencies of interactive components

# Updating Target Variable (new_cases) Visualization for Latest Data
@app.callback(
    dash.dependencies.Output('target_var_fig', 'figure'),
    dash.dependencies.Input('regressor_feature_dd', 'value')
)
def update_target_visualization(feature_name):
    # if feature_name != None:
    target_var = 'new_cases_smoothed'
    fig = None
    if feature_name != target_var:
        if is_cont(df_cov, feature_name):
            fig = px.scatter(df_cov, x=feature_name, y=target_var, 
                             title=f"Scatter {target_var} over {feature_name}")
        else:
            fig = px.bar(df_cov, x = feature_name, y= target_var,
                         title=f"BoxPlot {target_var} over {feature_name}")

    fig.update_layout(template='plotly_dark', title='Visualizing Target Variable for Latest Data',
                          plot_bgcolor='#23262c', paper_bgcolor='#23262c')
    return fig


# Updating Historical Data Visualization
@app.callback(
    [dash.dependencies.Output('hist_filter_val_dd', 'options'),
     dash.dependencies.Output('hist_filter_val_dd', 'value')],
    dash.dependencies.Input('hist_filter_feat_dd', 'value')
)
def update_filter_val_options(filter_feat):
    not_null_mask = df_hist[filter_feat].notnull()
    unique_vals = df_hist[filter_feat][not_null_mask].unique()
    options = [{'label': val, 'value': val} for val in unique_vals]
    value = options[0]['value']
    return options, value


@app.callback(
    dash.dependencies.Output('hist_timeline_fig', 'figure'),
    [dash.dependencies.Input('hist_feature_dd', 'value'),
     dash.dependencies.Input('hist_filter_feat_dd', 'value'),
     dash.dependencies.Input('hist_filter_val_dd', 'value')]
)
def update_timeline_vis(plot_feature, filter_feature, filter_value):
    hist_time_feature = 'date' # can put in db_info
    toPlot = []
    print(filter_value)
    for v in filter_value:
        #print(v)
        hist_filter_mask = df_hist[filter_feature] == v
        df_hist_filtered = df_hist[hist_filter_mask]
        df_hist_filtered = df_hist_filtered.sort_values(by=[hist_time_feature], axis=0)
        toPlot.append(df_hist_filtered)

    fig = go.Figure()
    for i, filtered in enumerate(toPlot):
        fig.add_trace(go.Scatter(x=df_hist[hist_time_feature],y=filtered[plot_feature], mode="lines", name=str(filter_value[i])))

    fig.update_layout(template='plotly_dark', title=f'Historical Timeline of {plot_feature} Over {filter_feature}',
                          plot_bgcolor='#23262c', paper_bgcolor='#23262c')
    return fig


# Updating Historical Comparison Visualization
@app.callback(
    dash.dependencies.Output('hist_comparison_fig', 'figure'),
    [dash.dependencies.Input('date_to_compare_dd', 'value'),
     dash.dependencies.Input('feats_to_compare_dd', 'value')]
)
def update_history_compare_vis(hist_date, features):
    print("FEATURES:")
    print(features)
    # Historical DF to compare to
    hist_date_mask = df_hist['date'] == hist_date
    df_hist_date = df_hist[df_hist['date']==hist_date]

    # Concatenating historical and latest DF
    df_cov_new = df_cov.rename(columns = {'last_updated_date':'date'})
    df_compare = pd.concat([df_cov_new, df_hist_date], sort=False).reset_index()

    feats_to_plot = ['date', 'location'] + features
    df_compare = df_compare[feats_to_plot]

    # Setting up DF to plot, 'grouped stacked' bar plot
    df_total = pd.DataFrame(columns=feats_to_plot)
    df_total['feature'] = None
    df_total['feature_val'] = None
    for f in features:
        feats_to_remove = set(features).difference(set([f]))
        df_new = df_compare.rename(columns={f:'feature_val'}).drop(feats_to_remove, axis=1)
        df_new['feature'] = f
        df_total = pd.concat([df_total, df_new])
    
    #print(df_total.shape)

    # Creating figure
    fig = go.Figure()
    # Color setup
    rgb=[55, 83, 109]
    signs = np.random.randint(3, size=(df_total.shape[0], 3))

    # By location (@TODO: make location a dropdown option as well)
    for i, loc in enumerate(df_total['location'].unique()):
        df_row = df_total[df_total['location']==loc]
        # print("DF ROW")
        # print(df_row)
        rgb_i = [(c + signs[i, j] * i * 15)%256 for j, c in enumerate(rgb)]
        # if df_total.iloc[i]['date'] >= '2021-12-10' or df_total.iloc[i]['date'] == '2020-06-03': # @TODO: change latest date
        fig.add_trace(go.Bar(x=[df_row.feature, df_row.date],
                        y = df_row.feature_val,
                        marker_color=f'rgb({rgb_i[0]}, {rgb_i[1]}, {rgb_i[2]})', name=loc
                    ))

    fig.update_layout(
        barmode='stack',
        bargap=0.15, # gap between bars of adjacent location coordinates.
        bargroupgap=0.1 # gap between bars of the same location coordinate.
    )
    fig.update_layout(template='plotly_dark', title=f'Historical Comparison by Feature and Location',
                          plot_bgcolor='#23272c', paper_bgcolor='#23272c')

    return fig

if __name__ == '__main__':
    app.run_server(debug=True, port=1050, host='0.0.0.0')