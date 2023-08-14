import dash
from dash import dcc
from dash import html
import dash_bootstrap_components as dbc
from datetime import datetime as dt
from dateutil.relativedelta import relativedelta
from dash_bootstrap_templates import load_figure_template

# Import callbacks
from callbacks import register_callbacks_stock
from callbacks import register_callbacks_portfolio
from callbacks import register_callbacks_riskFreeRate
from callbacks import register_callbacks_add_to_portfolio

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.LUX])
load_figure_template('LUX')

app.layout = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        dbc.InputGroup(
                                            [
                                                dbc.InputGroupText("Enter Stock Ticker:"),
                                                dbc.Input(id='ticker-input', type='text', value='',
                                                          placeholder='AAPL', debounce=True),
                                                dbc.Alert(id='stock-error-alert', is_open=False, color="danger")
                                            ]
                                        ),
                                        dbc.Row(dbc.InputGroup(
                                            [
                                                dbc.Button("Add stock to Porfolio : #", id="addPortfolio-button"),
                                                dbc.Input(id='share-input', type='number', value='10', debounce=True),
                                            ])
                                        ),
                                    ], md=6, className="p-2"
                                ),
                                dbc.Col(dbc.Card([
                                    dbc.CardBody([
                                        html.H6('Current Price'),
                                        html.P(id='currentPrice-display', className='p-custom')
                                    ])
                                ]), md=4, className="p-2", style={'marginLeft': '50px'}),
                            ]
                        ),
                        dbc.Row(
                            [
                                dbc.Col(
                                    dbc.InputGroup(
                                        [
                                            dbc.InputGroupText("Select Date Range:"),
                                            dcc.DatePickerRange(
                                                id='date-range-stock',
                                                min_date_allowed=dt(1990, 1, 1),
                                                max_date_allowed=dt.now(),
                                                initial_visible_month=dt.now(),
                                                start_date=dt.now() - relativedelta(years=5),
                                                end_date=dt.now())
                                        ]), md=8, className="p-2"
                                )
                            ]
                        ),
                        dbc.Row(
                            [
                                dbc.Col(dbc.Card([
                                    dbc.CardBody([
                                        html.H6('Market Cap.:'),
                                        html.P(id='marketCap-display', className='p-custom')
                                    ])
                                ]), md=4, className="p-2"),
                                dbc.Col(dbc.Card([
                                    dbc.CardBody([
                                        html.H6('Avg. Volume:'),
                                        html.P(id='avgVolume-display', className='p-custom')
                                    ])
                                ]), md=4, className="p-2"),
                                dbc.Col(dbc.Card([
                                    dbc.CardBody([
                                        html.H6('P/E Ratio:'),
                                        html.P(id='peRatio-display', className='p-custom')
                                    ])
                                ]), md=4, className="p-2"),
                            ]
                        ),
                        dbc.Row(
                            [
                                dbc.Col(
                                    dbc.InputGroup(
                                        [
                                            dbc.Button("Get Risk-Free Rate", id="riskFreeButton", color="primary", n_clicks=0),
                                            dbc.InputGroupText(id='riskFreeRate-display'),
                                            dbc.Select(
                                                id="riskFreeCountry",
                                                options=[
                                                    {"label": "United States (6-Month)", "value": "YC/USA6M"},
                                                    {"label": "United States (1-Year)", "value": "YC/USA1Y"},
                                                    {"label": "United States (2-Year)", "value": "YC/USA2Y"},
                                                    {"label": "United States (5-Year)", "value": "YC/USA5Y"},
                                                    {"label": "United States (10-Year)", "value": "YC/USA10Y"},
                                                    {"label": "United States (20-Year)", "value": "YC/USA20Y"},
                                                    {"label": "United States (30-Year)", "value": "YC/USA30Y"},
                                                ],
                                                value="YC/USA10Y",
                                            ),
                                        ],
                                    ), className="p-2", style={'marginTop': '20px'}
                                )
                            ],
                        )
                    ],
                    md=5  # size of the column on medium devices and above
                ),
                dbc.Col(
                    [
                        dcc.Graph(id='stock-chart'),
                    ],
                    md=7  # size of the column on medium devices and above
                ),
            ], className="p-2"
        ),
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        dbc.Card(
                                            [
                                                dbc.CardBody([
                                                    html.H6('Portfolio:\n(Ticker,#)'),
                                                    dbc.Textarea(
                                                        id='portfolio-input',
                                                        placeholder='AAPL, 10\nGOOG, 5\nGM, 25\n...',
                                                        style={'width': '100%', 'height': 325}),
                                                    dbc.Button('Submit', id='submit-button', n_clicks=0, color="primary", className="mt-2"),
                                                    dbc.Alert(id='portfolio-error-alert', is_open=False, color="danger")
                                                ])
                                            ]
                                        )
                                    ], md=4, className="p-2"
                                ),
                                dbc.Col(
                                    [
                                        dbc.Row(
                                            dbc.InputGroup(
                                                [
                                                    dbc.InputGroupText("Select Date Range:"),
                                                    dcc.DatePickerRange(
                                                        id='date-range-portfolio',
                                                        min_date_allowed=dt(1990, 1, 1),
                                                        max_date_allowed=dt.now(),
                                                        initial_visible_month=dt.now(),
                                                        start_date=dt.now() - relativedelta(years=5),
                                                        end_date=dt.now())
                                                ]), className="p-2"
                                        ),
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    dbc.Select(
                                                        id='marketPortfolio',
                                                        options=[
                                                            {'label': 'S&P 500',
                                                             'value': '^GSPC'},
                                                            {'label': 'MSCI World',
                                                             'value': 'URTH'},
                                                            {'label': 'DAX',
                                                             'value': '^GDAXI'},
                                                            {'label': 'Nikkei 225',
                                                             'value': '^N225'},
                                                            {'label': 'Hang Seng',
                                                             'value': '^HSI'},
                                                            {'label': 'Shang. Comp. Ind.',
                                                             'value': '000001.SS'},
                                                            {'label': 'FTSE 100',
                                                             'value': '^FTSE'},
                                                            {'label': 'CAC 40',
                                                             'value': '^FCHI'},
                                                            {'label': 'BSE SENSEX',
                                                             'value': '^BSESN'},
                                                            {'label': 'ASX 200',
                                                             'value': '^AXJO'},
                                                        ],
                                                        value='^GSPC',  # Default value
                                                    ), md=6, className="p-2"
                                                ),
                                                dbc.Col(
                                                    dbc.InputGroup(
                                                        [
                                                            dbc.InputGroupText("RFR:"),
                                                            dbc.Input(id='riskFreeRate-input', type='number', value='3.50', debounce=True),
                                                            dbc.InputGroupText("%", className='custom-inputGroupText-percent'),
                                                        ]), md=6, className="p-2"
                                                ),
                                            ]
                                        ),
                                        dbc.Row(
                                            [
                                                dbc.Col(dbc.Card([
                                                    dbc.CardBody([
                                                        html.H6('Cum. Return:'),
                                                        html.P(id='return-display', className='p-custom')
                                                    ])
                                                ]), md=6, className="p-2"),
                                                dbc.Col(dbc.Card([
                                                    dbc.CardBody([
                                                        html.H6('Dollar Return:'),
                                                        html.P(id='dollarReturn-display', className='p-custom')
                                                    ])
                                                ]), md=6, className="p-2"),
                                            ]
                                        ),
                                        dbc.Row(
                                            [
                                                dbc.Col(dbc.Card([
                                                    dbc.CardBody([
                                                        html.H6('Sharpe Ratio:'),
                                                        html.P(id='sharpeRatio-display', className='p-custom')
                                                    ])
                                                ]), md=6, className="p-2"),
                                                dbc.Col(dbc.Card([
                                                    dbc.CardBody([
                                                        html.H6('Sortino Ratio:'),
                                                        html.P(id='sortinoRatio-display', className='p-custom')
                                                    ])
                                                ]), md=6, className="p-2"),
                                            ]
                                        ),
                                        dbc.Row(
                                            [
                                                dbc.Col(dbc.Card([
                                                    dbc.CardBody([
                                                        html.H6('Alpha:'),
                                                        html.P(id='alpha-display', className='p-custom')
                                                    ])
                                                ]), md=6, className="p-2"),
                                                dbc.Col(dbc.Card([
                                                    dbc.CardBody([
                                                        html.H6('Beta:'),
                                                        html.P(id='beta-display', className='p-custom')
                                                    ])
                                                ]), md=6, className="p-2"),
                                            ]
                                        ),
                                    ],
                                    md=8,
                                )
                            ]
                        )
                    ],
                    md=5
                ),
                dbc.Col(
                    [
                        dcc.Graph(id='portfolio-chart'),
                    ],
                    md=7
                ),
            ], className="p-2"
        ),
        dcc.Store(id='portfolio-store'),
        dcc.Store(id='marketPortfolio-store'),
        dcc.Store(id='exchangeRate-store')
    ],
    fluid=True,
)


# Register the callbacks
register_callbacks_stock(app)
register_callbacks_riskFreeRate(app)
register_callbacks_portfolio(app)
register_callbacks_add_to_portfolio(app)

if __name__ == '__main__':
    app.run_server(debug=False, dev_tools_ui=False, dev_tools_props_check=False)
