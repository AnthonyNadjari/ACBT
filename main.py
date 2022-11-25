import dash
from dash.dependencies import Input,Output,State

import dash
from dash import Dash, dcc, html, Input, Output

from dash import html,dcc,callback_context
import dash_bootstrap_components as dbc
import ac_bt_interface
#import backtest_strat_test

import json

import plotly.graph_objs as go
import pandas as pd

app = dash.Dash(__name__,external_stylesheets=[dbc.themes.CERULEAN])
app.title = 'Barclays EQD Backtesting'
#app._favicon = ("/Users/anthonadj/PycharmProjects/dash_autocalls/assets/logo-barclays2.ico")

navbar= dbc.NavbarSimple(
    children=[
        html.Div(dbc.Button('Menu',outline=True,id='btn_sidebar',
                            color='secondary'))
        ],className='dash-bootstrap',
        brand_href = "#",
    color='#2fa4e7',
    fluid = True,
    links_left = True,
)
# the style arguments for the sidebar. We use position:fixed and a fixed width
SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 62.5,
    "left": 0,
    "bottom": 0,
    "width": "16rem",
    "height": "100%",
    "z-index": 1,
    "overflow-x": "hidden",
    "transition": "all 0.5s",
    #"padding": "0.5rem 1rem",
    "padding": "4rem 1rem 2rem",

    "background-color": "#f8f9fa",
}

SIDEBAR_HIDEN = {
    "position": "fixed",
    "top": 62.5,
    "left": "-16rem",
    "bottom": 0,
    "width": "16rem",
    "height": "100%",
    "z-index": 1,
    "overflow-x": "hidden",
    "transition": "all 0.5s",
    "padding": "0rem 0rem",
    "background-color": "#f8f9fa",
}

# the styles for the main content position it to the right of the sidebar and
# add some padding.
CONTENT_STYLE = {
    "transition": "margin-left .5s",
    "margin-left": "18rem",
    "margin-right": "2rem",
    "padding": "2rem 1rem",
    "background-color": "#f8f9fa",
}

CONTENT_STYLE1 = {
    "transition": "margin-left .5s",
    "margin-left": "2rem",
    "margin-right": "2rem",
    "padding": "2rem 1rem",
    "background-color": "#f8f9fa",
}

sidebar = html.Div(
    children=[
        html.H2('MSc. 203',style={'font':'Arial','color':'#2fa4e7'},
#         html.H2('Barclays',style={'font':'Arial','color':'#2fa4e7'},
                ),
        html.Hr(),
        html.P('Welcome to the backtest center.',
               className='lead'),
        dbc.Nav(
            [
                dbc.NavLink('Autocall (Athena/Phoenix)',
                            href='/page-1',
                            id='page-1-link',
                            active='exact'),
                dbc.NavLink('Dispersion',
                            href='/page-2',
                            id='page-2-link',
                            active='exact'),

                dbc.NavLink('Incoming',
                            href='/page-3',
                            id='page-3-link',
                            active='exact'),

            ],
            vertical=True,
            pills=True

            ),
        ],
        id='sidebar',
        style=SIDEBAR_STYLE,
)

content = html.Div(

    id="page-content",
    style=CONTENT_STYLE)


app.layout = html.Div(
    [
        dcc.Store(id='side_click'),
        dcc.Location(id="url"),
        navbar,
        sidebar,
        content,
    ],
)


@app.callback(
    [
        Output("sidebar", "style"),
        Output("page-content", "style"),
        Output("side_click", "data"),
    ],

    [Input("btn_sidebar", "n_clicks")],
    [
        State("side_click", "data"),
    ]
)
def toggle_sidebar(n, nclick):
    if n:
        if nclick == "SHOW":
            sidebar_style = SIDEBAR_HIDEN
            content_style = CONTENT_STYLE1
            cur_nclick = "HIDDEN"
        else:
            sidebar_style = SIDEBAR_STYLE
            content_style = CONTENT_STYLE
            cur_nclick = "SHOW"
    else:
        sidebar_style = SIDEBAR_STYLE
        content_style = CONTENT_STYLE
        cur_nclick = 'SHOW'
    return sidebar_style, content_style, cur_nclick

@app.callback(
    [Output(f"page-{i}-link","active") for i in range(1,4)],
    [Input('url','pathname')],
)
def toggle_active(pathname):
    if pathname == "/":
        return True,False,False
    return [pathname == f"/page{i}" for i in range(1,4)]


@app.callback(Output('page-content','children'),
              [Input('url','pathname')])

def render_page_content(pathname):
    if pathname in ["/","/page-1"]:
        return ac_bt_interface.app_template_layout
        #return html.P("cc")
    elif pathname == '/page-2':
        return html.P('Incoming!')
    elif pathname == '/page-3':
        return html.P('Incoming!')
    return dbc.Jumbotron(
        [html.H1('404: Not found', className='text-danger'),
         html.Hr(),
         html.P(f"The pathname {pathname} was not recognised...")]
    )

if __name__=="__main__":
    app.run_server(debug=False,port=4220)












