import numpy as np
import pandas as pd

import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html

from helper_files.financial_calcs import simple_calc


def input_card(title,text, colour, id):
    card = dbc.Card(
        dbc.CardBody(
            [
                html.H5(title, className="card-title"),
                html.Div(id='strat-row-alert') if id == 'age' else None,
                dbc.Input(
                    placeholder=text, bs_size="lg", className="mb-3", id=id
                ),
            ]
        ),  color=colour, inverse=True
    )
    return card

def sim_card(title,text, colour, id):
    card = dbc.Card(
        dbc.CardBody(
            [
                html.H5(title, className="card-title"),
                html.Div(id='strat-row-alert') if id == 'age' else None,
                dbc.Input(
                    placeholder=text, bs_size="lg", className="mb-3", id=id
                ),
            ]
        ),  color=colour, inverse=True
    )
    return card

def gain_card(title, pl_1, ft_1, val_1, pl_2, ft_2, val_2, colour, is_gain):
    card = dbc.Card(
        dbc.CardBody(
            [
                html.H5(title, className="card-title"),
                dbc.FormGroup(
                    [
                        dbc.Label('Bonds'),
                        dbc.Input(value=val_1, placeholder=pl_1, type="number", id='bond-gain' if is_gain else 'bond-sd'),
                        dbc.FormText(ft_1),
                    ]
                ),
                dbc.FormGroup(
                    [
                        dbc.Label('Stocks'),
                        dbc.Input(value=val_2, placeholder=pl_2, type="number", id='stock-gain' if is_gain else 'stock-sd'),
                        dbc.FormText(ft_2),
                    ]
                ),
            ]
        ),  color=colour, inverse=True
    )
    return card

def strategy_card(title, colour):
    card = dbc.Card(
        dbc.CardBody(
            [
                html.H5(title, className="card-title"),
                dbc.Row([
                    dbc.Col(
                        dbc.FormGroup(
                            [
                                dbc.Label("Principal"),
                                dbc.Input(placeholder="$", type="text", id='principal'),
                            ]
                        ), width=8
                    ),
                    dbc.Col(
                        dbc.FormGroup(
                            [
                                dbc.Label("Monthly contribution"),
                                dbc.Input(placeholder="$", type="text", id='monthly-main'),
                            ]
                        ), width=4
                    )
                ]),
                html.Div(id='strategy-alert'),
                dbc.FormGroup(
                    [
                        dbc.Label('Add row...'),
                        html.Div([
                            dbc.Row([
                                    dbc.Col(dbc.Button('Add', color="light", id='add-strat-row', n_clicks=0), width=3),
                                    dbc.Col(dbc.Button('Remove', color="dark", id='remove-strat-row', n_clicks=0), width=3)
                                ]),
                        ])
                    ]
                ),
                dbc.Row(
                    [
                        dbc.Col('Age'),
                        dbc.Col('Monthly $'),
                        dbc.Col('Bonds (%)'),
                        dbc.Col('Stock (%)')
                     ],
                ),
                dbc.Row(dbc.Col(html.Div(strategy_row(0, None, 0), id='strategy-rows'))),
                dbc.Row(
                    [

                        dbc.Col(html.Div([dbc.Input(type="number", placeholder='End age..', min=0, max=120,
                                                    step=1, id='end-age')]), width=3, className='mt-4'),
                        dbc.Col(html.Div(['Calculate a single sample portfolio...']), width=6, className='mt-4'),
                        dbc.Col(html.Div([dbc.Button('Calculate', color="dark", id='calculate', n_clicks=0)]),
                                width=3, className='mt-4'),
                    ]
                ),
            ]
        ),  color=colour, inverse=True
    )
    return card

def strategy_row(index, age, monthly):
    row = [html.Div(
        [
            html.Div([], id={'type': 'bond-value-alert', 'index': index}),
            html.Div([], id='strategy-row-alert'),
         dbc.Row(
        [
            dbc.Col(dbc.Input(type="number", placeholder='Years...', min=0, max=120, step=1,
                              id={'type': 'age-strategy', 'index': index},
                              value=age if age is not None else None)),
            dbc.Col(dbc.Input(type="number", placeholder='$', min=0, value=monthly, id={'type': 'monthly-value', 'index': index})),
            dbc.Col(dbc.Input(type="number", placeholder='Bond %..', value=50, min=0.0, max=100.0, step=1,
                              id={'type': 'bond-value', 'index': index})),
            dbc.Col(dbc.Input(type="number", disabled=True, id={'type': 'stock-value', 'index': index})),
        ], id='start-row' + str(index), className='mt-3'
    )])]
    return row


def get_concluding_statement(financial_data, end_age):
    last_phase_value = financial_data.get_last_phase().get_last_total()
    monthly_int = last_phase_value * 0.05 / 12
    top = '{}'.format(end_age)
    value = '${:,.2f}'.format(last_phase_value)
    interest = '${:,.2f}'.format(monthly_int)
    conc = html.Div([
        html.Span('At age...'),
        html.Span([html.Span(top, id='age-statement',  style={'color': 'green', 'font-size': '20px'})]),
        html.Span(dcc.Markdown('...your portfolio __**could**__ be worth...')),
        html.Span(value, className="display-5", id='final-statement', style={'color': 'green', 'font-size': '30px'}),
        html.Hr(className="my-2"),
        html.Span('This generates a monthly income (assume 5% p.a. of investment) of around...'),
        html.Span(interest, id='interest-statement', style={'color': 'green', 'font-size': '20px'}),
        html.Div(dcc.Markdown('Click __simulate__ to get a better understanding of what this type of portfolio could be worth...'))
    ])
    return conc

def get_summary_of_sim(n_times, principal, strat_ages, monthly, bond_vals, stock_gain, stock_sd, bond_gain, bond_sd):
    totals = []
    total_paid_in = 0
    for i in range(n_times):
        yearly_totals, total_paid_in, payment_coeffs = simple_calc(float(principal), strat_ages, monthly, bond_vals, stock_gain, stock_sd, bond_gain, bond_sd)
        payment_coeffs.append(yearly_totals[-1] * -1)
        totals.append([yearly_totals[-1], payment_coeffs])
    paid_in_plus_principal = total_paid_in + principal

    just_totals = []
    just_interest = []
    for total in totals:
        just_totals.append(total[0])
        just_interest.append(total[1])
    just_totals.sort(reverse=True)
    just_interest.sort(key=lambda x: x[-1])

    median = np.percentile(just_totals, 50)
    median_apr = get_apr(just_interest[5000])
    median_apr = '{:,.2f}%'.format(median_apr)

    tenth = np.percentile(just_totals, 10)
    tenth_apr = '{:,.2f}%'.format(get_apr(just_interest[1000]))

    lower_q = np.percentile(just_totals, 25)
    lower_q_apr = '{:,.2f}%'.format(get_apr(just_interest[2500]))

    upper_q = np.percentile(just_totals, 75)
    upper_q_apr = '{:,.2f}%'.format(get_apr(just_interest[7500]))

    ninety = np.percentile(just_totals, 90)
    ninety_apr = '{:,.2f}%'.format(get_apr(just_interest[9000]))

    median_int = int(median) - paid_in_plus_principal
    median_income = float(median) * 0.05 / 12
    median_income = human_format(median_income)
    median = human_format(median)
    median_int = human_format(median_int)


    iqr_lower = human_format(lower_q)
    iqr_upper = human_format(upper_q)
    iqr_l_income = lower_q * 0.05 / 12
    iqr_u_income = upper_q * 0.05 / 12
    iqr_l = human_format(iqr_l_income)
    iqr_u = human_format(iqr_u_income)
    iqr_income_string = iqr_l + '  -  ' + iqr_u
    iqr_string = iqr_lower + '  -  ' + iqr_upper
    iqr_int_1 = int(lower_q) - paid_in_plus_principal
    iqr_int_2 = int(upper_q) - paid_in_plus_principal
    iqr_int_l = human_format(iqr_int_1)
    iqr_int_u = human_format(iqr_int_2)
    iqr_int_string = iqr_int_l + '  -  ' + iqr_int_u
    iqr_apr_string = upper_q_apr + '  -  ' + lower_q_apr


    lower_10 = human_format(tenth)
    lower_10_income = float(tenth) * 0.05 / 12
    lower_10_income = human_format(lower_10_income)
    lower_10_int = int(tenth) - paid_in_plus_principal
    lower_10_int = human_format(lower_10_int)


    upper_10 = human_format(ninety)
    upper_10_income = float(ninety) * 0.05 / 12
    upper_10_income = human_format(upper_10_income)
    upper_10_int = int(ninety) - paid_in_plus_principal
    upper_10_int = human_format(upper_10_int)

    total_paid_in = human_format(total_paid_in)
    paid_in_plus_principal = human_format(paid_in_plus_principal)
    n_times = '{:,.2f}'.format(int(n_times))

    totals_df = pd.DataFrame(just_totals)

    concluding_statement = html.Div([
        dbc.Row([
            dbc.Col(
                [html.Span('The simulation was ran...'),
                 html.Span([html.Span(n_times, id='age-statement', style={'color': 'green', 'font-size': '20px'})]),
                 ], width=4
            ),
            dbc.Col(
                feedback_card(median, median_int, dcc.Markdown('The median (50th percentile) portfolio value is:'), 'Total',
                              total_paid_in, paid_in_plus_principal, median_income, median_apr, strat_ages[-1]), width=6
            )
        ]),
        html.Hr(className="my-2"),
        dbc.Row(
            dbc.Col(
                feedback_card(iqr_string, iqr_int_string, dcc.Markdown('There is a __50%__ chance your portfolio will be worth:'),
                              'Between...',
                              total_paid_in, paid_in_plus_principal, iqr_income_string, iqr_apr_string, strat_ages[-1]), width={'size': 6, 'offset': 3}
            ),
        ),
        dbc.Row([
            dbc.Col(
                feedback_card(lower_10, lower_10_int, dcc.Markdown('There is a __10%__ chance your portfolio will be worth:'), 'Less than...',
                              total_paid_in, paid_in_plus_principal, lower_10_income, ninety_apr, strat_ages[-1]), width=6
            ),
            dbc.Col(
                feedback_card(upper_10, upper_10_int, dcc.Markdown('There is a __10%__ chance your portfolio will be worth:'),
                              'More than...',
                              total_paid_in, paid_in_plus_principal, upper_10_income, tenth_apr, strat_ages[-1]), width=6
            )
        ]),
    ])

    return concluding_statement, totals_df, max(just_totals), just_totals


def feedback_card(value, interest, text1, text2, monthly, prin_plus_month, income, apr, end_age):
    age_string = 'From age __'+str(end_age)+'__...this is 5% of the total value...'
    width = 4
    div = html.Div([
                    dbc.Row(
                        dbc.Col(html.Div(text1), width=12),
                        ),
                    dbc.Row(
                        [dbc.Col(html.Div(text2, style={'color': 'green', 'text-align': 'right', 'font-size': '18px'}), width=width),
                        dbc.Col(html.Div(value, style={'color': 'black', 'font-size': '22px'}), width=12 - width)],
                    ),
                    dbc.Row(
                        [dbc.Col(html.Div('Monthly', style={'text-align': 'right'}), width=width),
                        dbc.Col(html.Div(monthly, style={'color': 'red', 'font-size': '15px'}), width=12- width)]
                    ),
                    dbc.Row(
                        [dbc.Col(html.Div('Principal + Monthly', style={'text-align': 'right'}), width=width),
                        dbc.Col(html.Div(prin_plus_month, style={'color': 'red', 'font-size': '15px'}), width=12- width)]
                    ),
                    dbc.Row(
                        [dbc.Col(html.Div('Interest earned', style={'text-align': 'right'}), width=width),
                        dbc.Col(html.Div(interest,  style={'color': 'black', 'font-size': '17px'}), width=12 - width)]
                    ),
                    dbc.Row(
                        [dbc.Col(html.Div('Annualised', style={'text-align': 'right'}), width=width),
                         dbc.Col(html.Div(apr, style={'color': 'blue', 'font-size': '17px'}), width=12 - width)]
                    ),
                    dbc.Row(
                        [dbc.Col(html.Div('Income ($ / month)', style={'text-align': 'right'}), width=width),
                         dbc.Col(html.Div(income, style={'color': 'blue', 'font-size': '17px'}), width=12 - width)]
                    ),
                    dbc.Row(
                        [dbc.Col(html.Div(dcc.Markdown(age_string), style={'text-align': 'right', 'font-size': '12px'}), width=width)]
                    ),
                 ])
    return div


def human_format(num):
    num = float(num)
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
    # add more suffixes if you need them
    return '$%.1f%s' % (num, ['', 'k', 'M', 'B'][magnitude])

def annual_interest(n_years, total_in, total_out):
    factor = np.exp(np.log(total_in/total_out)/n_years)
    apr = (factor - 1) * 100
    apr = '{:,.1f}%'.format(apr)
    return apr


def calc_avg_apr(yearly_totals):
    yearly_apr = []
    for i, years_total in enumerate(yearly_totals):
        if i < len(yearly_totals):
            factor = yearly_totals[i+1] / yearly_totals[i]
            apr = (factor - 1) * 100
            yearly_apr.append(apr)
    return np.mean(yearly_apr)

def get_apr(payment_coeffs):
    roots = np.roots(payment_coeffs)
    real_roots = roots.real[abs(roots.imag) < 1e-5]
    closest_to_one = min(real_roots, key=lambda x: abs(x - 1))
    return (closest_to_one - 1) * 100
    # real_roots.sort()
    # # return the answer which is larger but closest to 1
    # for root in real_roots:
    #     if root < 1:
    #         continue
    #     else:
    #         return
