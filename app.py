import dash
from dash import dcc
from dash import html
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import pandas.io.sql as sqlio
from fetch_data_from_db import *

import psycopg2
from psycopg2 import OperationalError

## READ COVID DATA FROM OWID REPO
df, df_latest = fetch_entire_tables()

hist_feats = df.columns

latest_feats = df_latest.columns
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
def xy_plot():
    return html.Div(children=[
        html.Div(children=[
            html.H2(children='Target Variable Visualization'),
            dcc.Dropdown(
                id='x_feature_dd',
                options=[{'label': col, 'value': col} for col in df_latest.columns],
                multi=False,
                placeholder='Feature to Plot Over',
                value=df_latest.columns[0]
            ),
            dcc.Dropdown(
                id='y_feature_dd',
                options=[{'label': col, 'value': col} for col in df_latest.columns],
                multi=False,
                placeholder='Feature to Plot Over',
                value=df_latest.columns[6]
            ),
            html.Div(children=[
                dcc.Graph(id='xy_fig')]),
        ])
    ], className='row')


def timeline_comparator():
    return html.Div(children=[
        html.Div(children=[
            html.H2("Compare Trends of a Target for a Value"),
            dcc.Dropdown(
                id='feature_dd',
                options=[{'label': f, 'value': f} for f in hist_feats if df[f].dtype != 'object'],
                multi=False,
                placeholder='Historical Feature to Visualize',
                value='new_cases_smoothed'
            ),
            dcc.Dropdown(
                id='filter_feat_dd',
                options=[{'label': f, 'value': f} for f in hist_feats if df[f].dtype == 'object'],
                multi=False,
                placeholder='Feature to Filter',
                value='location'
            ),
            dcc.Dropdown(
                id='filter_val_dd',
                options=[],
                multi=True,
                placeholder='Value(s) to Filter By',
                value=[df.iloc[0]['location']] 
            ),
            html.Div(children=[
                dcc.Graph(id='timeline_fig')])
            ])
    ])

#def compare_features():
#    return html.Div(children=[
#        html.Div(children=[
#            html.H2("Historical Comparison"),
#            dcc.Dropdown(
#                id='date_to_compare_dd',
#                options=[{'label': d, 'value': d} for d in df_hist['date'].unique()],
#                multi=False,
#                placeholder='Date to Compare To',
#                value=df_hist.iloc[0]['date'] # put in db_info?
#            ),
#            dcc.Dropdown(
#                id='feats_to_compare_dd',
#                options=[{'label': f, 'value': f} for f in hist_feats],
#                multi=True,
#                placeholder='Features to Compare',
#                value=['new_tests', 'new_cases']
#            ),
#            html.Div(children=[
#                dcc.Graph(id='hist_comparison_fig')
#            ])
#        ])
#    ])

#def line_graph(stack=False):
    #df = df_latest
    #if df is None:
    #    return go.Figure()
    #sources = ['total_cases', 'new_cases', 'location', 'total_deaths_per_million']
    #x = df['date']
    #fig = go.Figure()
    #for i, s in enumerate(sources):
    #    fig.add_trace(go.Scatter(x=x, y=df[s], mode='lines', name=s,
    #                             line={'width': 2, 'color': COLORS[i]},
    #                             stackgroup='stack' if stack else None))
    #fig.add_trace(go.Scatter(x=x, y=df['Load'], mode='lines', name='Load',
    #                         line={'width': 2, 'color': 'orange'}))
    #title = ''
    #if stack:
    #    title += ' [Stacked]'
    #fig.update_layout(template='plotly_dark',
    #                  title=title,
    #                  plot_bgcolor='#23272c',
    #                  paper_bgcolor='#23272c',
    #                  yaxis_title='MW',
    #                  xaxis_title='Date/Time')
    #return fig


# Sequentially add page components to the app's layout
def dynamic_layout():
    return html.Div([
        xy_plot(),
        timeline_comparator(),
        #dcc.Graph(id='stacked-trend-graph', figure=line_graph(stack=True)),
    ], className='row', id='content')


# set layout to a function which updates upon reloading
app.layout = dynamic_layout


# Defines the dependencies of interactive components

# Updating Target Variable (new_cases) Visualization for Latest Data
@app.callback(
    dash.dependencies.Output('xy_fig', 'figure'),
    [dash.dependencies.Input('x_feature_dd', 'value'),
    dash.dependencies.Input('y_feature_dd', 'value')]
)
def update_target_visualization(feature_name, target_var):
    #target_var = 'new_cases_smoothed'
    fig = None
    if feature_name != target_var:
        if is_cont(df_latest, feature_name):
            fig = px.scatter(df_latest, x=feature_name, y=target_var, 
                             title=f"Scatter {target_var} over {feature_name}")
        else:
            fig = px.bar(df_latest, x = feature_name, y= target_var,
                         title=f"BoxPlot {target_var} over {feature_name}")

    fig.update_layout(template='plotly', title=f'Visualizing {target_var} v. {feature_name} for Latest Data',
                          plot_bgcolor='#D3D3D3', paper_bgcolor='#D3D3D3')
    return fig


# Updating Historical Data Visualization
@app.callback(
    [dash.dependencies.Output('filter_val_dd', 'options'),
     dash.dependencies.Output('filter_val_dd', 'value')],
    dash.dependencies.Input('filter_feat_dd', 'value')
)
def update_filter_val_options(filter_feat):
    not_null_mask = df[filter_feat].notnull()
    unique_vals = df[filter_feat][not_null_mask].unique()
    options = [{'label': val, 'value': val} for val in unique_vals]
    value = options[0]['value']
    return options, value


@app.callback(
    dash.dependencies.Output('timeline_fig', 'figure'),
    [dash.dependencies.Input('feature_dd', 'value'),
     dash.dependencies.Input('filter_feat_dd', 'value'),
     dash.dependencies.Input('filter_val_dd', 'value')]
)
def update_timeline_vis(plot_feature, filter_feature, filter_value):
    hist_time_feature = 'date' # can put in db_info
    toPlot = []
    for v in filter_value:
        #print(v)
        hist_filter_mask = df[filter_feature] == v
        df_filtered = df[hist_filter_mask]
        df_filtered = df_filtered.sort_values(by=[hist_time_feature], axis=0)
        toPlot.append(df_filtered)

    fig = go.Figure()
    for i, filtered in enumerate(toPlot):
        fig.add_trace(go.Scatter(x=df[hist_time_feature],y=filtered[plot_feature], mode="markers", name=str(filter_value[i])))

    fig.update_layout(template='plotly', title=f'Historical Timeline of {plot_feature} Over {filter_feature} for Selected Values',
                          plot_bgcolor='#D3D3D3', paper_bgcolor='#D3D3D3')
    return fig




if __name__ == '__main__':
    app.run_server(debug=True, port=1050, host='0.0.0.0')