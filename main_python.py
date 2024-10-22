
import sqlite3
from flask import Flask, g
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import pandas as pd
from flask import Flask, g
from mlxtend.preprocessing import minmax_scaling
from pandas.api.types import CategoricalDtype
from scipy import stats
import matplotlib.pyplot as plt

# Database
DATABASE = "expenses.db"

def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

def close_db(e=None):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()

# Flask initialization
server = Flask(__name__)
server.config.from_mapping(
    DATABASE=DATABASE,
)

server.teardown_appcontext(close_db)

# Dash app initialization
app = dash.Dash(__name__, server=server, external_stylesheets=external_stylesheets)
#app = dash.Dash(__name__, server=server)
app.title = 'Expense Tracker and Financial Dashboard'




# Layout
app.layout = html.Div(children=[
    html.H1("Expense Tracker"),

    dcc.Tabs([
        dcc.Tab(label='New Expense', id="view", children=[
            html.Div([
                html.Label('Date of the Expense (yyyy-mm-dd):'),
                dcc.Input(id='Date', type='text', value='', placeholder="0000-00-00"), html.Br(),
                html.Label('Description of the Expense:'),
                dcc.Input(id='description', type='text', value="", placeholder="What did you buy?"), html.Br(),
                html.Label('Category:'),
                dcc.Input(id='CATEGORY', type='text', value="", placeholder='Category please!'), html.Br(),
                html.Label('Price of the Expense:'),
                dcc.Input(id='price', type="number", value="", placeholder="0.00"), html.Br(),
                html.Button('Track', id='submit-button', n_clicks=0),
            ])
            
        ]),
        dcc.Tab(label='View Expenses', id="view", children=[
            html.Div([
                dcc.RadioItems(id='view-selector',
                               options=[
                                   {'label': 'View all expenses', 'value': 'all'},
                                   {'label': 'View monthly expenses by category', 'value': 'monthly'},
                               ],
                               value='all'
                               ),
                html.Div(id='expense-table'),
                html.Div(id='some-output-element')
            ])
            
            
            

        ]),
        dcc.Tab(label='Yearly Tansactions', id="view", children=[
        html.Div([html.H1("Financial Transactions Dashboard"),
        dcc.Graph(id='graph_by_year', figure={'data': [], 'layout': {}})]),
        ]),
        dcc.Tab(label='Price based Line Chart ', id="view-line", children=[
        html.Div([html.H1("Financial Transactions Dashboard"),
        dcc.Graph(id='graph_by_price', figure={'data': [], 'layout': {}})]),
         ]),         
        dcc.Tab(label='Category Based Pie Chart', id="view", children=[
        html.Div([html.H1("Financial Transactions Dashboard"),
        dcc.Graph(id='pie_chart_category', figure={'data': [], 'layout': {}})]),
        ]),
    ]),

    
    
    ])



# Callback for updating the pie_chart_category
@app.callback(
    Output('pie_chart_category', 'figure'),
    [Input('view-selector', 'value')]
)
def update_pie_chart_category(view_selector):
    conn = get_db()
    cur = conn.cursor()

    if view_selector == 'all':
        cur.execute("""SELECT Category, COUNT(*) AS Transactions
                       FROM expenses
                       GROUP BY Category""")
        category_data = cur.fetchall()
    else:
        
        category_data = []

    labels = [category[0] for category in category_data]
    values = [category[1] for category in category_data]

    return {
        'data': [
            {
                'labels': labels,
                'values': values,
                'type': 'pie',
                'hoverinfo': 'label+percent',
                'textinfo': 'value+percent',
            },
        ],
        'layout': {
            'title': 'Transactions by Category (Pie Chart)',
        }
    }



@app.callback(
    Output('graph_by_year', 'figure'),
    [Input('view-selector', 'value')]
)
def update_graph_by_year(view_selector):
    conn = get_db()
    cur = conn.cursor()

    if view_selector == 'all':
        cur.execute("""SELECT strftime('%Y', Date) AS Year, COUNT(*) AS Transactions
                       FROM expenses
                       GROUP BY Year""")
        data = cur.fetchall()
        df = pd.DataFrame(data, columns=['Year', 'Transactions'])

        return {
            'data': [{'x': df['Year'], 'y': df['Transactions'], 'type': 'bar', 'name': 'Transactions by Year'}],
            'layout': {
                'title': 'Number of transactions by year',
                'xaxis': {'title': 'Year'},
                'yaxis': {'title': 'Number of transactions'},
            }
        }
    else:
        
        return {'data': [], 'layout': {}}


# Callback for updating the graph_by_price
@app.callback(
    Output('graph_by_price', 'figure'),
    [Input('view-selector', 'value')]
)
def update_graph_by_price(view_selector):
    conn = get_db()
    cur = conn.cursor()

    if view_selector == 'all':
        cur.execute("""SELECT strftime('%Y-%m', Date) AS Month, AVG(Price) AS AveragePrice
                       FROM expenses
                       GROUP BY Month""")
        data = cur.fetchall()
        df = pd.DataFrame(data, columns=['Month', 'AveragePrice'])

        return {
            'data': [{'x': df['Month'], 'y': df['AveragePrice'], 'type': 'scatter', 'mode': 'lines+markers', 'name': 'Average Price'}],
            'layout': {
                'title': 'Average Price of transactions by month',
                'xaxis': {'title': 'Month'},
                'yaxis': {'title': 'Average Price'},
            }
        }
    else:
       
        return {'data': [], 'layout': {}}


@app.callback(
    Output('expense-table', 'children'),
    [Input('view-selector', 'value')]
)
def update_expense_table(view_selector):
    conn = get_db()
    cur = conn.cursor()
    if view_selector == 'all':
        cur.execute("SELECT * FROM expenses ORDER BY Date DESC")
        expenses = cur.fetchall()
        df = pd.DataFrame(expenses, columns=['ID', 'Date', 'Description', 'Category', 'Price'])
        if df.empty:
            return 'No expenses to display.'
        table = html.Table(
            [html.Tr([html.Th(column) for column in df.columns])] +
            [html.Tr([html.Td(expense[column]) for column in df.columns]) for _, expense in df.iterrows()]
        )
        return table
    elif view_selector == 'monthly':
        cur.execute("""SELECT strftime('%m', Date) AS Month, Category, SUM(Price) AS Total
                       FROM expenses
                       GROUP BY Month, Category""")
        monthly_expenses = cur.fetchall()
        monthly_df = pd.DataFrame(monthly_expenses, columns=['Month', 'Category', 'Total'])
        if monthly_df.empty:
            return 'No monthly expenses to display.'
        table = html.Table(
            [html.Tr([html.Th(column) for column in monthly_df.columns])] +
            [html.Tr([html.Td(expense[column]) for column in monthly_df.columns]) for _, expense in monthly_df.iterrows()]
        )
        return table

@app.callback(
    [Output('some-output-element', 'children'),
     Output('Date', 'value'),
     Output('description', 'value'),
     Output('CATEGORY', 'value'),
     Output('price', 'value')],
    [Input('submit-button', 'n_clicks')],
    [State('Date', 'value'),
     State('description', 'value'),
     State('CATEGORY', 'value'),
     State('price', 'value')]
)
def handle_form_submission(n_clicks, date, description, category, price):
    if n_clicks > 0:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("INSERT INTO expenses (Date, description, CATEGORY, price) VALUES (?, ?, ?, ?)",
            (date, description, category, price))


        conn.commit()
        formatted_message = (
            f"Recent Expense:<br>"
            f"Date: {date}<br>"
            f"Description: {description}<br>"
            f"Category: {category}<br>"
            f"Price: {price}"
        )
        return (dcc.Markdown(formatted_message, dangerously_allow_html=True), '', '', '', 0)
    return ("", date, description, category, price)

if __name__ == '__main__':
    app.run_server(debug=True)
