import numpy as np
import pandas as pd
from scipy.stats import norm
from sigfig import round
import time

def simple_calc(principal, strat_ages, monthly, bond_vals, stock_gain, stock_sd, bond_gain, bond_sd):
    yearly_totals = [principal]
    number_of_phases = len(strat_ages) - 1
    year = 0
    bond_changes, stock_changes = create_yearly_market_change(strat_ages[0], strat_ages[-1], bond_gain, bond_sd,
                                                              stock_gain, stock_sd)
    for i in range(number_of_phases):
        for j in range(strat_ages[i] - strat_ages[0], strat_ages[i + 1] - strat_ages[0]):
            bond_prop = ((yearly_totals[-1] + monthly[i] * 12) * bond_vals[i] / 100) * (1 + bond_changes[year] / 100)
            stock_prop = ((yearly_totals[-1] + monthly[i] * 12) * (100 - bond_vals[i]) / 100) * (1 + stock_changes[year] / 100)
            total = bond_prop + stock_prop
            yearly_totals. append(total)
            year += 1
    return yearly_totals


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

tic = time.time()
for i in range(100):
    dqw = simple_calc(1000, [30,40,50], [100, 100], [30, 70], 10, 20, 5, 5)
toc = time.time()
print('time', toc-tic)

# totals = simple_calc(2000, [19, 20, 30], [100, 50], [50, 40], 10, 20, 5, 5)
# all_totals = []
# for i in range(1000):
#     all_totals.append(simple_calc(2000, [19, 20, 30], [100, 50], [50, 40], 10, 20, 5, 5)[-1])
# print(all_totals)
