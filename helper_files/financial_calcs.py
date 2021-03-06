import numpy as np
import pandas as pd
from scipy.stats import norm
from sigfig import round
import plotly.express as px
import plotly.graph_objects as go



class Calculator:
    def __init__(self, principal, ages, monthly, bond_prop, stock_exp, stock_sd, bond_exp, bond_sd):
        self.principal = principal
        self.ages = ages
        self.monthly = monthly
        self.bond_prop = bond_prop
        self.stock_exp = stock_exp
        self.stock_sd = stock_sd
        self.bond_exp = bond_exp
        self.bond_sd = bond_sd

        self.bond_changes, self.stock_changes = self.create_yearly_market_change()
        self.number_of_phases = len(ages) - 1

        self.phases = self.get_phase_data()

        self.df = self.concat_phase_dfs()


    def get_last_phase(self):
        return self.phases[-1]

    def get_df(self):
        return self.df

    def concat_phase_dfs(self):
        df_list = []
        for i, phase in enumerate(self.phases):
            df_list.append(phase.get_phase_df())
        concat_df = pd.concat(df_list)
        concat_df.reset_index(drop=True, inplace=True)
        return concat_df

    def create_yearly_market_change(self):
        # n years of change...
        n = self.ages[-1] - self.ages[0]

        # genertae the bond/stock changes for each year
        if self.bond_sd != 0:
            bond_changes = list(np.random.normal(self.bond_exp, self.bond_sd, n))
            bond_changes = [round_dp(float(num), 2) for num in bond_changes]
        else:
            bond_changes = [self.bond_exp] * n
        if self.bond_sd != 0:
            stock_changes = list(np.random.normal(self.stock_exp, self.stock_sd, n))
            stock_changes = [round_dp(float(num), 2) for num in stock_changes]
        else:
            stock_changes = [self.stock_exp] * n

        return bond_changes, stock_changes

    def get_bond_changes(self):
        return self.bond_changes

    def get_stock_changes(self):
        return self.stock_changes

    def get_summary(self):
        return 'Bond mean = ' + str(np.mean(self.get_bond_changes())) + '\n' \
               + 'Bond SD = ' + str(np.std(self.get_bond_changes())) + '\n' \
               + 'Stock mean = ' + str(np.mean(self.get_stock_changes())) + '\n' \
               + 'Stock SD = ' + str(np.std(self.get_stock_changes()))

    def get_number_of_phases(self):
        return self.number_of_phases

    def get_phase_data(self):
        phases = []
        for i in range(self.get_number_of_phases()):
            new_phase = Phase(self.ages[i], self.ages[i + 1],
                              self.principal if i == 0 else phases[-1].get_last_total(), self.monthly[i],
                              self.bond_prop[i], self.bond_changes[self.ages[i] - self.ages[0]: self.ages[i + 1] -
                                                                                                self.ages[0]],
                              self.stock_changes[self.ages[i] - self.ages[0]: self.ages[i + 1] - self.ages[0]])
            phases.append(new_phase)
        return phases


class Phase:
    def __init__(self, start_age, end_age, initial_val, monthly, bond_prop, bond_changes, stock_changes):
        self.start_age = start_age
        self.end_age = end_age
        self.length_of_phase = self.end_age - self.start_age
        self.initial_val = initial_val
        self.monthly = monthly
        self.bond_prop = bond_prop
        self.bond_changes = bond_changes
        self.stock_changes = stock_changes

        self.bond_values = self.calc_phase_data(self.bond_prop, self.bond_changes)
        self.stock_values = self.calc_phase_data(100 - self.bond_prop, self.stock_changes)
        # self.totals = [[sum(i[0]), sum(i[1])] for i in zip(*[self.bond_values, self.stock_values])]
        self.totals = self.make_total_list()

        self.first_bond_value = self.bond_values[0][1]
        self.first_stock_value = self.stock_values[0][1]
        self.first_total_value = self.totals[0][1]

        self.last_bond_value = self.bond_values[-1][1]
        self.last_stock_value = self.stock_values[-1][1]
        self.last_total_value = self.totals[-1][1]

        self.last_bond_interest = self.bond_values[-1][0]
        self.last_stock_interest = self.stock_values[-1][0]
        self.last_total_interest = self.totals[-1][0]

        self.phase_df = self.make_df()

    def get_last_total(self):
        return self.last_total_value

    def make_df(self):
        all_years = []
        for i in range(self.end_age - self.start_age):
            year_row = [self.start_age + i, self.monthly, self.bond_prop, self.bond_changes[i], 100 - self.bond_prop,
                        self.stock_changes[i], self.bond_values[i][1], self.bond_values[i][0], self.stock_values[i][1],
                        self.stock_values[i][0],  self.totals[i][1], self.totals[i][0]]
            all_years.append(year_row)
        df = pd.DataFrame(all_years, columns=['Age', 'Monthly', 'Bond %', 'Bond Change', 'Stock %', 'Stock Change',
                                              'Bond Value', 'Bond Int', 'Stock Value', 'Stock Int', 'Total Value',
                                              'Total Int'])
        return df

    def get_phase_df(self):
        return self.phase_df

    def make_total_list(self):
        totals = []
        for i, values in enumerate(zip(self.bond_values, self.stock_values)):
            interest = values[0][0] + values[1][0]
            value = values[0][1] + values[1][1]
            totals.append([round(interest, decimals=2), round(value, decimals=2)])
        return totals

    def calc_phase_data(self, prop, instrument_change):
        year_cont = self.monthly * 12 * prop / 100
        first_value = self.initial_val * prop / 100
        end_year_values = []
        for i in range(self.length_of_phase):
            previous_value = end_year_values[-1][1] + year_cont if i != 0 else first_value + year_cont
            # yearly interest .... increased value
            this_year_values = [round(float(previous_value * instrument_change[i] / 100), decimals=2),
                                round(float(previous_value * (1 + instrument_change[i] / 100)), decimals=2)]
            end_year_values.append(this_year_values)
        return end_year_values

    def get_daily_interest_rate(self, value, prop, bond_rate, stock_rate):
        return value * prop * bond_rate / 100 + value * (100 - prop) * stock_rate / 100

    def get_bond_values(self):
        return self.bond_values

    def get_stock_values(self):
        return self.stock_values

    def get_totals(self):
        return self.totals

    def get_last_bond_value(self):
        return self.last_bond_value

    def get_last_stock_value(self):
        return self.last_stock_value

    def get_last_total(self):
        return self.last_total_value


def get_table_conditions():
    conditions = [
        {'if': {
            'filter_query': '{Stock Change} > 0',
            'column_id': 'Stock Change'
        },
            'color': 'black'},
        {'if': {
            'filter_query': '{Stock Change} < 0',
            'column_id': 'Stock Change'
        },
            'color': 'red'},
        {'if': {
            'filter_query': '{Bond Change} > 0',
            'column_id': 'Bond Change'
        },
            'color': 'black'},
        {'if': {
            'filter_query': '{Bond Change} < 0',
            'column_id': 'Bond Change'
        },
            'color': 'red'}
    ]
    return conditions

def simple_calc(principal, strat_ages, monthly, bond_vals, stock_gain, stock_sd, bond_gain, bond_sd):
    yearly_totals = [principal]
    payment_coeffs = []
    number_of_phases = len(strat_ages) - 1
    total_paid_in = 0
    year = 0
    bond_changes, stock_changes = create_yearly_market_change(strat_ages[0], strat_ages[-1], bond_gain, bond_sd,
                                                              stock_gain, stock_sd)
    for i in range(number_of_phases):
        for j in range(strat_ages[i] - strat_ages[0], strat_ages[i + 1] - strat_ages[0]):
            # this represents each year
            bond_prop = ((yearly_totals[-1] + monthly[i] * 12) * bond_vals[i] / 100) * (1 + bond_changes[year] / 100)
            stock_prop = ((yearly_totals[-1] + monthly[i] * 12) * (100 - bond_vals[i]) / 100) * (1 + stock_changes[year] / 100)
            total = bond_prop + stock_prop
            yearly_totals.append(total)
            payment_coeffs.append(monthly[i]*12)
            total_paid_in += monthly[i] * 12
            year += 1
    payment_coeffs[0] = monthly[0]*12 + principal
    return yearly_totals, total_paid_in, payment_coeffs


def create_yearly_market_change(start_age, end_age, bond_exp, bond_sd, stock_exp, stock_sd):
    # n years of change...
    n = end_age - start_age

    # genertae the bond/stock changes for each year
    if bond_sd != 0:
        bond_changes = list(np.random.normal(bond_exp, bond_sd, n))
    else:
        bond_changes = [bond_exp] * n
    if stock_sd != 0:
        stock_changes = list(np.random.normal(stock_exp, stock_sd, n))
    else:
        stock_changes = [stock_exp] * n

    return bond_changes, stock_changes

colour = 'blue'
def make_histo(totals_list, totals_df, n_times):

    bins = np.histogram_bin_edges(totals_list, bins=20)

    # create the bins
    counts, bins = np.histogram(totals_df, bins=bins)

    hist_trace = go.Bar(x=bins,
                        y=counts,
                        opacity=0.75,
                        name='',
                        marker={
                           'line': {
                               'width': 0.8,
                               'color': 'black'},
                           'color': colour
                       })

    hist_layout = go.Layout(
        xaxis={
            'type': 'linear',
            'linewidth': 3,
            'showline': True,
            'linecolor': colour,
            'title': 'Portfolio value ($)',
            'automargin': True,
            'gridcolor': 'whitesmoke',
        },
        bargap=0,
        plot_bgcolor='rgb(255,255,255)',
        yaxis={
            'title': '',
            'gridcolor': 'whitesmoke',
        },
    )
    hist_traces = {'data': [hist_trace], 'layout': hist_layout}

    # fig = px.bar(x=bins[1:], y=counts, labels={'x': 'Portfolio value ($)', 'y': 'Frequency'})
    # fig.update_layout(bargap=0)
    return hist_traces

def make_box(totals_list):
    box_trace = go.Box(x=totals_list,
                       opacity=0.75,
                       name='',
                       marker={
                           'line': {
                               'width': 0.8,
                               'color': 'black'},
                           'color': colour
                       })

    box_layout = go.Layout(
        xaxis={
            'type': 'linear',
            'linewidth': 3,
            'showline': True,
            'linecolor': colour,
            'title': 'Portfolio value ($)',
            'automargin': True,
            'gridcolor': 'whitesmoke',
        },
        plot_bgcolor='rgb(255,255,255)',
        yaxis={
            'title': '',
            'gridcolor': 'whitesmoke',
        },
    )
    box_traces = {'data': [box_trace], 'layout': box_layout}
    return box_traces


def round_dp(num, dp):
    return round(num, decimals=dp)