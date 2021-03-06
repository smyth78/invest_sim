import dash_bootstrap_components as dbc

stock_value_error = dbc.Alert(
    'Invalid entry...',
    color='dark',
    dismissable=True
)


error_with_ages = dbc.Alert(
    'Ages must increase for each new row...',
    color='success',
    dismissable=True
)

invalid_entry = dbc.Alert(
    'Some values are misssing...',
    color='info',
    dismissable=True
)

some_time = dbc.Alert(
    'Please wait while I run the simulation...',
    color='info',
    dismissable=True
)