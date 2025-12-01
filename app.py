#import libraries
import pandas as pd
import geopandas as gpd
import plotly.graph_objects as go
import numpy as np
import json
import dash
from dash import Dash, dcc, html, Input, Output
import dash_bootstrap_components as dbc
from dash_breakpoints import WindowBreakpoints
import os

#read in processed data
gdf = gpd.read_file('data/processed.geojson')

#read in and then make list of dictionaries for dash dropdown component 
fips_df = pd.read_csv('data/fips.csv')
fips = [dict(label=fips_df['STATE_NAME'][i], value=fips_df['FIPS'][i]) for i in range(len(fips_df))]

#set static items
#colors for cong. district map
cdmap_discrete = [
    [0/12, '#1F505C'], [1/12, '#1F505C'],
    [1/12, '#2A6B80'], [2/12, '#2A6B80'],
    [2/12, '#3891A6'], [3/12, '#3891A6'],
    [3/12, '#76C6D6'], [4/12, '#76C6D6'],
    [4/12, '#C1F5FF'], [5/12, '#C1F5FF'],
    
    [5/12, '#FFFFFF'], [7/12, '#FFFFFF'],
    
    [7/12, '#FFC7C8'], [8/12, '#FFC7C8'],
    [8/12, '#F0999B'], [9/12, '#F0999B'],
    [9/12, '#DB5461'], [10/12, '#DB5461'],
    [10/12, '#AD3032'], [11/12, '#AD3032'],
    [11/12, '#96292B'], [12/12, '#96292B']
]

#cong. district map colorbar items
cdmap_tickvals = [-.30, -.20, -.10, 0, .10, .20, .30]
cdmap_ticktext = ['30% (D)', '20% (D)', '10% (D)', '0%', '10% (R)', '20% (R)', '30% (R)']


#pie chart items
pie_colors = {'D': '#3891A6', 'R': '#DB5461'}
pie_labels = {'D': 'Democratic Districts', 'R': 'Republican Districts'}


#histogram items
bins = [0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 1]
hist_bins = [float(x) for x in bins]


#pulls in required dash bootstrap sheet and custom Google fonts
external_stylesheets = [
    dbc.themes.BOOTSTRAP,
    'https://fonts.googleapis.com/css2?family=EB+Garamond&display=swap',
    'https://fonts.googleapis.com/css2?family=Anonymous+Pro&display=swap'
]

#begin app coding
#instantiate app and set layout
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

#set the browser tab text
app.title = 'Cong. District SNAP Explorer'

#this sets the layout of the application and default values
app.layout = dbc.Container(
    [
        html.Div(
            [
                html.Div(id='display'),
                WindowBreakpoints(
                    id='breakpoints',
                    # Define the breakpoint thresholds
                    widthBreakpointThresholdsPx=[1200],
                    # And their name, note that there is one more name than breakpoint thresholds
                    widthBreakpointNames=['sm', 'lg'],
                ),
                html.Header(
                    html.Img(
                        src='assets/Logo.svg',
                        style={'height': '5vh'}
                    )
                ),
                html.H1(
                    'Data Beheld'
                ),
                html.H2(
                    'Congressional District SNAP Benefits Explorer'
                ),
                html.H4(
                    'Geographic selection:'
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            dcc.Dropdown(
                                id='selection',
                                options=fips,
                                value='USA'
                            ),
                            xs=12,
                            md=4,
                        ),
                    ]
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            dcc.Loading(
                                dcc.Graph(id='pie', style={'height': '35vh'}), 
                                type='circle',
                                color='#4C5B5C'
                            ),
                            xs=12,
                            md=4,
                            className='graph-container'                            
                        ),
                        dbc.Col(
                            dcc.Loading(
                                dcc.Graph(id='hist', style={'height': '35vh'}), 
                                type='circle',
                                color='#4C5B5C'
                            ),
                            xs=12,
                            md=8,
                            className='graph-container'
                        ),
                    ]
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            dcc.Loading(
                                dcc.Graph(id='cdmap', config={"scrollZoom": False}, style={'height': '90vh'}),
                                type='circle',
                                color='#4C5B5C'
                            ),
                            className='graph-container'
                        ),
                    ]
                ),
                html.H4(
                    'Data sources:'
                ),
                html.P([
                    html.Br(),
                    'SNAP Data: US Census Bureau (2024). 2014-2023 American Community Survey 1-Year Public Use Data Tables. Retrieved from ',
                    html.A(    
                        'https://api.census.gov.',
                        href='https://api.census.gov',
                        style={'color': '#3891A6'}
                    )
                ]),
                html.P([
                    'Congressional District Geography: USDOT Bureau of Transportation Statistics (2023). Congressional Districts, Last updated December 10, 2023. National Transportation Atlas Database. Retrieved from ',
                    html.A(
                        'https://geodata.bts.gov/datasets/usdot::congressional-districts/about.',
                        href='https://geodata.bts.gov/datasets/usdot::congressional-districts/about',
                        target='_blank',
                        style={'color': '#3891A6'}
                    )
                ]),
                html.P([
                    'Election Data: MIT Election Data and Science Lab. 2017. “U.S. House 1976&ndash;2024.” Harvard Dataverse. ',
                    html.A(
                       'https://doi.org/10.7910/DVN/IG0UN2.',
                        href='https://doi.org/10.7910/DVN/IG0UN2',
                        style={'color': '#3891A6'}
                    ),
                    html.Br(),
                    html.Br()                     
                ]),
                html.H4(
                    'GitHub link:'
                ),
                html.P([
                    html.A(
                        'https://github.com/DataBeheld/SNAP-Election-Map',
                        href='https://github.com/DataBeheld/SNAP-Election-Map',
                        style={'color': '#3891A6'}
                    )
                ])
            ]
        )
    ],
    fluid=True
)


#callback function and figures
@app.callback(
    Output('cdmap', 'figure'),
    Output('pie', 'figure'),    
    Output('hist', 'figure'),
    Input('breakpoints', 'widthBreakpoint'),
    Input('selection', 'value'))
def display_choropleth(breakpoints, selection):

    #resize to vertical format based on threshold
    if(breakpoints=='sm'):
        cb_dict=dict(
            title=dict(
                text='SNAP Participation Rate',
                font=dict(
                    family='EB Garamond',
                    size=20
                ),
                side='top'
            ),
            orientation='h', 
            y=-0.125,
            tickvals=cdmap_tickvals,
            ticktext=cdmap_ticktext
        )
        hist_leg=False
    else:
        cb_dict=dict(
            title=dict(
                text='SNAP Participation Rate',
                font=dict(
                    family='EB Garamond',
                    size=20
                ),
            ),
            orientation='v',
            x=-0.125,
            tickvals=cdmap_tickvals,
            ticktext=cdmap_ticktext
        )
        hist_leg=True
    
    #dropdown selection
    user_input=selection   

    #this code block simplifies the geography filtering logic
    if(user_input == 'USA'):
        cd_select=gdf
        cd_bounds=None
        hist_select_d=gdf[(gdf['PARTY'] == 'D')]
        hist_select_r=gdf[(gdf['PARTY'] == 'R')]
    elif(user_input[:1] == 'R'):
        cd_select=gdf[gdf['reg_codes']==user_input]
        cd_bounds='geojson'
        hist_select_d=gdf[(gdf['PARTY'] == 'D') & (gdf['reg_codes'] == user_input)]
        hist_select_r=gdf[(gdf['PARTY'] == 'R') & (gdf['reg_codes'] == user_input)]   
    elif(user_input[:1] == 'D'):
        cd_select=gdf[gdf['div_codes']==user_input]
        cd_bounds='geojson'
        hist_select_d=gdf[(gdf['PARTY'] == 'D') & (gdf['div_codes'] == user_input)]
        hist_select_r=gdf[(gdf['PARTY'] == 'R') & (gdf['div_codes'] == user_input)]        
    elif((user_input == '02') | (user_input == '15')):
        cd_select=gdf[gdf['STATEFP']==user_input]
        cd_bounds=None
        hist_select_d=gdf[(gdf['PARTY'] == 'D') & (gdf['STATEFP'] == user_input)]
        hist_select_r=gdf[(gdf['PARTY'] == 'R') & (gdf['STATEFP'] == user_input)]
    else:
        cd_select=gdf[gdf['STATEFP']==user_input]
        cd_bounds='geojson'
        hist_select_d=gdf[(gdf['PARTY'] == 'D') & (gdf['STATEFP'] == user_input)]
        hist_select_r=gdf[(gdf['PARTY'] == 'R') & (gdf['STATEFP'] == user_input)]

    #cong. district map figure
    cdmap = go.Figure(go.Choropleth(
        geojson=json.loads(cd_select.to_json()),
        locations=cd_select['GEOID'],
        z=cd_select['hh_snap_pct']*cd_select['PARTYNUM'],
        featureidkey='properties.GEOID',
        colorscale=cdmap_discrete,
        zmin=-.30,
        zmax=.30,
        hovertemplate=
        '%{text}<br>' + 
        'SNAP HH Participation Rate: %{customdata}%<extra></extra>',
        text=(cd_select['state']+' '+cd_select['NAMELSAD']+' ('+cd_select['PARTY']+')'),
        customdata=abs(round(cd_select['hh_snap_pct']*100,2))
    ))
    
    cdmap.update_layout(
        font=dict(color='#4C5B5C'),
        title_text='Map of SNAP Participation by Congressional District in '+fips_df[fips_df['FIPS']==user_input]['STATE_NAME'].iloc[0],
        title_x=0.5,
        title_xanchor='center',
        title_font=dict(family='EB Garamond', size=24),
        paper_bgcolor='#F5F5F0',
        geo=dict(
            bgcolor='#F5F5F0',
            landcolor='#EBEBE8',
            showframe=False,
            showcoastlines=False,
            fitbounds=cd_bounds,
            scope='usa',
            projection_type='albers usa'
        ),
        margin=dict(
            l=20,
            r=20,
            t=50,
            b=20 
        ),
        autosize=True
    )

    cdmap.update_traces(colorbar=cb_dict, selector=dict(type='choropleth'))
     
    #pie chart figure
    pie = go.Figure(
        data=[
            go.Pie(
                labels=cd_select.groupby(by='PARTY')['PARTY'].first().map(pie_labels), 
                values=cd_select.groupby(by='PARTY')['hh_snap'].sum(),
                marker_colors=cd_select.groupby(by='PARTY')['PARTY'].first().map(pie_colors),
                hole=.4,
                sort=False
            )
        ]
    )

    #this sets the percentage used in the dynamic pie chart title
    try:
        pie_temp = round(100*cd_select.groupby(by='PARTY')['hh_snap'].sum()['R']/cd_select['hh_snap'].sum(),1).astype(str)
    except:
        pie_temp = '0.0'

    #removes text from the pie pieces
    pie.update_traces(textinfo='none')
    
    pie.update_layout(
        font=dict(color='#4C5B5C'),
        title_text=pie_temp+'% of '+fips_df[fips_df['FIPS']==user_input]['STATE_NAME'].iloc[0]+' SNAP<br>Households Live in Red Districts',
        title_x=0.5,
        title_xanchor='center',
        title_font=dict(family='EB Garamond', size=20),
        paper_bgcolor='#F5F5F0',
        margin=dict(
            l=20,
            r=20,
            t=70,
            b=20 
        ),
        showlegend=False,
        autosize=True
    )

    #the following code blocks set histogram axis parameters
    hist_counts_d, _ = np.histogram(hist_select_d['hh_snap_pct'], bins=hist_bins)
    hist_counts_r, _ = np.histogram(hist_select_r['hh_snap_pct'], bins=hist_bins)
    
    hist_labels = ['0%-5%', '5%-10%', '10%-15%', '15%-20%', '20%-25%', '25%-30%', '30%-35%', '35% & up']
    
    hist_max = max(max(hist_counts_d),max(hist_counts_r))
    
    if(hist_max >= 50):
        hist_tick=20
    elif(hist_max >= 25):
        hist_tick=10
    elif(hist_max >= 10):
        hist_tick=5
    elif(hist_max >= 6):
        hist_tick=2
    else:
        hist_tick=1

    #histogram figure
    hist = go.Figure()
    hist.add_trace(go.Bar(
        x=hist_labels,
        y=hist_counts_r,
        name='(R) Districts',
        marker_color='#DB5461'
    ))
    hist.add_trace(go.Bar(
        x=hist_labels,
        y=hist_counts_d,
        name='(D) Districts',
        marker_color='#3891A6'
    ))
    
    hist.update_layout(
        font=dict(color='#4C5B5C'),
        title_text='Distribution of (R) and (D) SNAP Participation Rates',
        title_x=0.5,
        title_xanchor='center',
        title_font=dict(family='EB Garamond', size=20),
        paper_bgcolor='#F5F5F0',
        plot_bgcolor='#EBEBE8',
        margin=dict(
            l=20,
            r=20,
            t=70,
            b=20 
        ),
        xaxis_title='← Lower SNAP Participation    |    Higher SNAP Participation →',
        xaxis_tickformat='.1%',
        xaxis=dict(
            title_font=dict(family='EB Garamond', size=17)
        ),
        yaxis_title='District Count',
        yaxis=dict(
            tickmode = 'linear',
            tick0 = 0,
            dtick = hist_tick,
            title_font=dict(family='EB Garamond', size=17)
        ),
        showlegend=hist_leg,
        legend=dict(orientation='v')
    )

    return cdmap, pie, hist

#set port for Render
port = int(os.environ.get('PORT', 8050)) 
app.run_server(host="0.0.0.0", port=port, debug=False)
