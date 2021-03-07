# -*- coding: utf-8 -*-

# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

import dash
import dash_bootstrap_components as dbc
import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import Input, Output, State
from dash.dependencies import Output,Input,State, MATCH, ALL, ALLSMALLER
import dash._callback_context as call_back
import plotly.express as px
from dash.exceptions import PreventUpdate
from dash import no_update
import dash_table
import numpy as np
from textwrap import dedent

import json

from helper_files.div_templates import input_card, gain_card, strategy_card, strategy_row, get_concluding_statement, \
    get_summary_of_sim
from helper_files import alerts as alts
from meta import meta
from helper_files.financial_calcs import Calculator, get_table_conditions, make_histo, make_box

# dash.Dash.index = index

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.SANDSTONE],  meta_tags=meta)
app.title = 'Investment simulator'
server = app.server


app.layout = html.Div([
    dcc.Store(id='strat-row-index', data=1),

    dbc.Container(
        [
            dbc.Row(
                dbc.Col(
                    dbc.Jumbotron(
                        [
                            html.H1("Investment Portfolio Simulator", className="display-3"),
                            html.P('Explore different combinations of bond and equity ratios...',
                                className="lead",
                            ),
                            html.Hr(className="my-2"),
                            dcc.Markdown('''
                            * The volatility of the markets are simulated
                            * Change the ratio of bonds/equities over time
                            * Monthly contributions can be changed over time 
                            * Simulate the portfolio 10,000 times
                            ''')
                        ]
                    )
                )
            ),
            dbc.Row(
                    dbc.Col(
                        dbc.Checklist(
                            options=[
                                {"label": "See  model assumptions", "value": 'see'},
                            ],
                            value=[],
                            id="assumptions-check",
                        ),
                    )
            ),
            dbc.Row(
                dbc.Col([
                    dcc.Markdown('''Assumptions of model...'''),
                    dcc.Markdown('''
                            * Each yearly bond or stock gain is assumed to be normally distributed
                            * Each yearly gain is independent of any previous year
                            * The entire value of the portfolio is fully invested in the chosen ratio
                                ''')]
                        ), id='assumptions-list'
                ),
        dbc.Row(
            [
                dbc.Col([strategy_card('Strategy', 'secondary')], width=6, className='mt-4'),
                dbc.Col(
                    [dbc.Row(
                        [dbc.Col(gain_card('Gain (%)', 'Yearly bond gain...', 'Type the yearly bond gain above', 4.5,
                                          'Yearly stock gain...', 'Type the yearly stock gain above', 10, 'primary',
                                          True),
                                width=6, className='mt-4'),
                        dbc.Col(gain_card('Volatility (%)', 'Bond stand dev...', 'Type the yearly bond SD above', 4.5,
                                          'Yearly stock gain...', 'Type the yearly stock SD above', 20, 'primary',
                                          False),
                                width=6, className='mt-4'),
                         ]
                    ),
                    dbc.Row(
                        [dbc.Col(dbc.Card(
                                        dbc.CardBody(
                                            [
                                                dbc.Row(
                                                    [
                                                        dbc.Col(html.Div(['Simulate portfolio 10,000 times...']), width=6,
                                                                className='mt-4'),
                                                        dbc.Col(html.Div([dbc.Button('Simulate', color="dark",
                                                                                     id='simulate', n_clicks=0)]),
                                                                width=6, className='mt-4'),
                                                    ]
                                                )
                                            ]
                                        ),  color='danger', inverse=True
                                    ), width=6),
                                        dbc.Col(dbc.Card(
                                        dbc.CardBody(
                                            [
                                                dbc.Row(
                                                    [
                                                        dbc.Col(html.H5(['Please wait while I calculate...']), width=12,
                                                                className='mt-4'),
                                                    ]
                                                )
                                            ]
                                        ),  color='info', inverse=True, id='wait-message', style={'display': 'block'}
                                    ), width=6),
                        ]
                    ),
                    ]
                ),
             ]
        ),
            dbc.Row(
                dbc.Col(
                    dbc.Jumbotron(id='concluding-statement'), width=12, className='mt-4'
                ), style={'display': 'none'}, id='conc-statement'
            ),
            dbc.Row(
                dbc.Col(
                        dbc.Card(
                        dbc.CardBody(
                            [
                                html.H4("Data by year", className="card-title"),
                                dash_table.DataTable(id='data-table',
                                                     columns=[],
                                                     data=[],
                                                     style_data_conditional=[]
                                                     )
                            ]
                        ),
                        className='mt-4',
                    ), width=12
                ), style={'display': 'none'}, id='year-data'
            ),
            dbc.Row(
                [
                    dbc.Col(dbc.Jumbotron([
                        dbc.Row([
                            dbc.Col(dcc.Graph(id='histo'), width=6),
                            dbc.Col(dcc.Graph(id='box'), width=6),
                        ])
                    ]), width=12, className='mt-4')
                ], style={'display': 'none'}, id='sim-graphs'),
                dbc.Row(style={'padding-bottom': '500px'}),
        ],
        className='mt-4'),
])

# checklist for assumuptions check
@app.callback(
    Output('assumptions-list', 'style'),
    [Input('assumptions-check', 'value')]
)
def assumptions_check(value):
    if 'see' in value:
        return {'display': 'block'}
    else:
        return {'display': 'none'}


# this adds rows to the strategy
@app.callback(
    [Output('strategy-rows', 'children'),
     Output('strat-row-index', 'data'),
     Output('strategy-row-alert', 'children')],
    [Input('add-strat-row', 'n_clicks'),
     Input('remove-strat-row', 'n_clicks')],
    [State('strategy-rows', 'children'),
     State('strat-row-index', 'data'),
     State('monthly-main', 'value')]
)
def add_strategy_rows_on_click(add_strat_click, remove_strat_click, existing_rows, index, monthly_main):
    ctx = call_back.callback_context
    alert = None
    strategy_rows = None
    if ctx.triggered:
        prop_id = ctx.triggered[0]['prop_id'].split('.')[0]
        if prop_id == 'add-strat-row':
            # add a strat row
            strategy_rows = strategy_row(index, None, monthly_main) + existing_rows
            index += 1
        elif prop_id == 'remove-strat-row':
            # remove the first (last added row - if theres more than 1!)
            if len(existing_rows) > 1:
                strategy_rows = existing_rows[1:]
            else:
                strategy_rows = existing_rows
        return strategy_rows, index, alert
    else:
        raise PreventUpdate

# update the monhtly in the first row only...
@app.callback(
    Output({'type': 'monthly-value', 'index': 0}, 'value'),
    [Input('monthly-main', 'value')]
)
def update_monthly_vals_in_strat_row(monthly_main):
    return monthly_main

# add the wartning when simulate is clicked
@app.callback(
    Output('wait-message', 'style'),
    [Input('simulate', 'n_clicks'),
     Input('calculate', 'n_clicks')],

)
def update_bond_values(sim_click, calc_click):
    ctx = call_back.callback_context
    prop_id = None
    if ctx.triggered:
        prop_id = ctx.triggered[0]['prop_id'].split('.')[0]
        if prop_id == 'simulate':
            return {'display': 'block'}
        else:
            return {'display': 'none'}
    else:
        return {'display': 'none'}

# this updates the bonds ratio for each input in the strategy
@app.callback(
    [Output({'type': 'stock-value', 'index': MATCH}, 'value'),
     Output({'type': 'bond-value-alert', 'index': MATCH}, 'children')],
    [Input({'type': 'bond-value', 'index': MATCH}, 'value')],
)
def update_bond_values(bond_val):
    alert = None
    try:
        stock_value = 100 - bond_val
    except TypeError:
        stock_value = 0
    if stock_value > 100 or stock_value < 0:
        alert = alts.stock_value_error
        stock_value = 0
    return stock_value, alert

# do the calculation here and make validation checks....
@app.callback(
    [Output('strategy-alert', 'children'),
     Output('data-table', 'columns'),
     Output('data-table', 'data'),
     Output('data-table', 'style_data_conditional'),
     Output('concluding-statement', 'children'),
     Output('histo', 'figure'),
     Output('box', 'figure'),
     Output('conc-statement', 'style'),
     Output('sim-graphs', 'style'),
     Output('year-data', 'style')],
    [Input('calculate', 'n_clicks'),
     Input('simulate', 'n_clicks')],
    [State('principal', 'value'),
     State({'type': 'age-strategy', 'index': ALL}, 'value'),
     State({'type': 'monthly-value', 'index': ALL}, 'value'),
     State({'type': 'bond-value', 'index': ALL}, 'value'),
     State({'type': 'stock-value', 'index': ALL}, 'value'),
     State('end-age', 'value'),
     State('bond-gain', 'value'),
     State('bond-sd', 'value'),
     State('stock-gain', 'value'),
     State('stock-sd', 'value')]
)
def update_bond_values(calc_click, sim_click, principal, strat_ages, monthly_vals, bond_vals, stock_vals, end_age, bond_gain,
                       bond_sd, stock_gain, stock_sd):
    ctx = call_back.callback_context
    prop_id = None
    if ctx.triggered:
        prop_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if calc_click > 0 or sim_click > 0:
        alert = alts.invalid_entry
        # check if any entry in of the lists is None
        if any(elem is None for elem in monthly_vals + bond_vals + strat_ages):
            return [alert], no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update
        if '' in monthly_vals:
            return [alert], no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update
        if end_age is None or principal is None:
            return [alert], no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update

        # now check ages are in correct order
        strat_ages.append(end_age)
        removed_dupes = sorted(list(set(strat_ages)))
        sorted_list = sorted(strat_ages)
        visible = {'display': 'block'}
        invisible = {'display': 'none'}
        if strat_ages == sorted_list and strat_ages == removed_dupes:
            if prop_id == 'calculate':
                monthly = [float(i) for i in monthly_vals]
                financial_data = Calculator(float(principal), strat_ages, monthly, bond_vals, stock_gain, stock_sd, bond_gain, bond_sd)
                df = financial_data.get_df()
                columns = [{"name": i, "id": i} for i in df.columns]
                data = df.to_dict('records')
                conditions = get_table_conditions()
                concluding_statement = get_concluding_statement(financial_data, end_age)
                return no_update, columns, data, conditions, concluding_statement, no_update, no_update, visible, invisible, visible
            elif prop_id == 'simulate':
                strat_ages.append(end_age)
                monthly = [float(i) for i in monthly_vals]
                num_trials = 10000
                concluding_statement, totals_df, largest_val, totals_list = \
                    get_summary_of_sim(num_trials, float(principal), strat_ages, monthly, bond_vals, stock_gain,
                                       stock_sd, bond_gain, bond_sd)
                totals_list.sort()
                totals_list = totals_list[int(num_trials / 20): int(num_trials - num_trials / 20)]
                hist = make_histo(totals_list, totals_df, num_trials)
                box = make_box(totals_list)

                return no_update, no_update, no_update, no_update, concluding_statement, hist, box, visible, visible, invisible
        else:
            alert = alts.error_with_ages
            return [alert], no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update
    else:
        raise PreventUpdate



if __name__ == '__main__':
    app.run_server(debug=True)