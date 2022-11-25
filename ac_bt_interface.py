import dash
from dash import html, dcc,dash_table,callback
import dash_bootstrap_components as dbc
import pandas as pd
from dash import Output,Input,State,callback_context
import dash_daq as daq
from dash_bootstrap_templates import load_figure_template
import plotly.graph_objs as go
import numpy as np
#import backtest_strat_test
import json
global df

def get_companies():
    with open('tickers.json') as f:
        return json.load(f)

params=[
    'Autocall Barrier', 'Autocall Coupon', 'Coupon Barrier', 'Coupon'
]

load_figure_template('cerulean')
app_template_layout = dbc.Container([
    html.H1(
        className='body',
        children = 'Autocall Backtesting',
        style={'textAlign': 'center','color':'#2fa4e7','fontSize': 28, 'font-weight':'normal'},
    ),
    dbc.Row([
        dbc.Col([
            html.Br(),
            html.Br(),
            dcc.DatePickerRange(
                start_date_placeholder_text='Start Date',
                end_date_placeholder_text='End Period',
                calendar_orientation='vertical',
                display_format='DD/MM/YYYY',
                id='date_range',
                clearable=True)
            ],width='auto'),
        ],justify='center'),
    dbc.Row([
        dbc.Col([
            html.Div(
                children=[
                    html.Br(),
                    html.P('Underlyings'),
                    dcc.Dropdown(options=get_companies(),
                                 value='',
                                 id='udls',
                                 multi=True)]
            )
        ])
    ]),
    dbc.Row([
        dbc.Col([
            html.Div(
                children=[
                    html.Br(),
                    html.P('Basket Type'),
                    dcc.Dropdown(options=['Worst-of','Best-of','Equally-weighted'],
                                 value='',
                                 id='bskt',
                                 multi=False)]
            )
        ]),

        dbc.Col([
            html.Div(
                children=[
                    html.Br(),
                    html.P('Maturity'),
                    dcc.Input(id='matu',
                              placeholder='Enter the maturity in months',
                              )
                    ])
            ]),
        dbc.Col([
            html.Div(
                children=[
                    html.Br(),
                    html.P('Frequency'),
                    dcc.Input(id='freq',
                              placeholder='Enter the frequency in months',
                              )
                ])
            ]),
                ],justify='center'),
    dbc.Row([
        dbc.Col([
            html.Br(),
            html.Br(),
            html.Div(children=[
                html.P('Short Leg'),
                ]),
            ]),
        ]),
    dbc.Row([
        html.Br(),
        dbc.Col([
            html.Div(children=[
                html.P('Barrier (%)'),
                dcc.Input(id='pdi_barrier',
                          placeholder='Enter the barrier in %')
                ]),
            ]),
        dbc.Col([
            html.Div(children=[
                html.P('Strike (%)'),
                dcc.Input(id='pdi_strike',
                          placeholder='Enter the strike in %')
            ]),
        ]),
        dbc.Col([
            html.Div(children=[
                html.P('Leverage (%)'),
                dcc.Input(id='pdi_leverage',
                          placeholder='Enter the leverage in %')
            ]),
        ]),

    ]),
    html.Div(id='page-1-content'),
    html.Br(),
    dbc.Row([
        dbc.Col([
            html.Div([
                daq.BooleanSwitch(id='mem_effect',
                                  on=False,
                                  label='Memory Effect',
                                  children='test'),
                html.Div(id='boolean-switch-output-1')
                ])
            ]),
        ]),
    dbc.Row([
        dbc.Col([
            html.Div([
                dash_table.DataTable(id='table-editing-simple',
                                     columns=([{'id':p, 'name':p} for p in params]),
                                     data=[dict(Model=i,**{param: 0 for param in params}) for i in range(1,5)],
                                     editable=True,
                                     row_deletable=True)
                ]),
                dbc.Button('Submit',
                           id='submit-button',
                           n_clicks=0,
                           color="primary"),
                dcc.Store(id='table-editing-simple-output'),
            ]),
        ]),
    dbc.Row([
        dcc.Loading(id='loading-1',
                    type="default",
                    children = dbc.Col(id="graph_output")),
        html.Br(),
        html.Br(),
        ]),
    dbc.Row([
        html.Div([dcc.Dropdown(id='dropdown-to-show_or_hide_element',
                               options=[
                                   {'label':'Maturity Twin-Win','value':'on'},
                                   {'label':'None','value':'off'},
                                   {'label':html.Div([
                                       html.Img(src='/assets/images/star.svg',height=20),
                                       html.Div("One Star", style={'font-size':15,'padding-left':10}),
                                       ],style={'display':'flex','align-items':'center','justify-content':'center'},
                                        )
                                       ,'value':'also_off'},
                                   ],
                               #value='off',
                               searchable=False,
                               placeholder='Add a bullet feature'
                               ),
                  ]),
        ]),
    dbc.Row([
        ##to place a conditional visible element
        html.Div([
            dbc.Row([
                dbc.Col([
                    html.Div(
                        children=[
                            html.P('Strike (%)'),
                            dcc.Input(id='matu_strike',
                                      placeholder='Enter the strike in %'),
                            ]),
                    ]),
                dbc.Col([
                    html.Div(
                        children=[
                            html.P('Leverage (%)'),
                            dcc.Input(id='matu_leverage',
                                      placeholder='Enter the leverage in %'),
                        ]),
                    ]),
                ]),

        ##create a component to hide '''remember to put all the values to not existing if hidden'''''

        ],style={'display':'None'},
            id='element-to-hide')
            ]),
    ])
        ##create a component to hide '''remember to put all the values to not existing if hidden'''''
@callback(Output(component_id='element-to-hide',component_property="style"),
          [Input('dropdown-to-show_or_hide_element','value')])
def show_hide_element(value):
    if value=='on':
        return {'display':'block'}
    else:
        return {'display':'none'}

"""
    if value=='off':
        return {'display':'none'}
    if value== 'also_off':
        return {'display':'none'}
"""


@callback(Output('table-editing-simple-output','data'),
          Input('table-editing-simple','data'),
          Input('table-editing-simple','columns'))
def display_output(rows,columns):
    df = pd.DataFrame(rows,columns=[c['name'] for c in columns])
    print(df)
    print(df.to_json(date_format = 'iso',orient='split'))
    return df.to_json(date_format = 'iso',orient='split')


@callback(Output('boolean-switch-output-1','children'),
          Input('mem_effect','on'))

def update_output(on):
    global mem_effect
    mem_effect="{}".format(on)
    mem_effect=(mem_effect=='True')
    return None
computing=False
@callback(Output('graph_output','children'),
          [Input('submit-button','n_clicks'),
           Input('mem_effect','on'),
           Input('udls','value'),
           Input('bskt', 'value'),
           Input('matu', 'value'),
           Input('freq', 'value'),
           Input('pdi_barrier', 'value'),
           Input('pdi_strike', 'value'),
           Input('pdi_leverage', 'value'),
           Input('table-editing-simple-output-1','data'),
           Input('date_range','start_date'),
           Input('date_range','end_date')])
def update_datatable(n_clicks,memo_effect,tickers,basket_type,matu,freq,pdi_barrier,pdi_strike,pdi_leverage,df,start_date,end_date):
    change_id = [p['prop_id'] for p in callback_context.triggered[0]]
    if 'submit-button' in change_id:
        print('freq',int(freq))
        df_converted = pd.read_json(df,orient = 'split').apply(pd.to_numeric,errors='coerce')
        print(df,df_converted/100)
        """
        results of the backtest function 
    
        
        df = backtest_strat_test.backtest_global(df_converted/100,int(freq),tickers,int(matu),start_date,end_date,memo_effect,basket_type,float(pdi_barrier)/100,float(pdi_leverage)/100,float(pdi_strike)/100)
        data_result = pd.DataFrame([x[0] for x in df],index=[x[1] for x in df],columns=["Results"])
        fig1=go.Figure(go.Scatter(x=data_result.index,y=data["Results"],mode='markers',name='Redemption amounts'))
        fig1.update_layout(title_text='Redemption')
        return dcc.Graph(figure = fig1)
        """

        return None










