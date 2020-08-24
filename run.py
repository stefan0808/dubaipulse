import dash
import dash_html_components as html
import dash_core_components as dcc
import pandas as pd
import overpy
import dash_leaflet as dl
import plotly.express as px

api = overpy.Overpass()
district_query = """
[out:json][timeout:90];
way
  [~"^name:"~"{}"]
  ["place"="suburb"];
out body;
>;
out skel qt;
"""

df = pd.read_csv(
    'input.csv',
    index_col=None,
    na_values=['NA'],
    low_memory=False)

df['instance_date'] = pd.to_datetime(df.instance_date)
sorted_df = df.sort_values(by=['instance_date'])
sorted_df.rename(columns={
    'Unnamed: 0': 'index'
    },
    inplace=True)
sorted_df['meter_sale_price'] = pd.to_numeric(sorted_df['meter_sale_price'])

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
sample_bounds = [
    [22.02454, 51.38305],
    [26.82407, 60.85327]
]


app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
area_names = df['area_name_en'].unique()
areas = [{'label': an, 'value': an} for an in area_names if not pd.isna(an)]

app.layout = html.Div(children=[
    html.Div([
            dcc.Dropdown(
                id='demo-dropdown',
                options=areas,
                searchable=True,
            )
        ],
        style={
            'margin': '20px auto'
        }
    ),
    html.Div([
            html.H2(
                "Home Prices & Values"
            ),
            dl.Map(
                [
                    dl.TileLayer(),
                    dl.LayerGroup(id="layer")
                ],
                id="map",
                style={
                    'height': r'calc(100% - 7.2rem)'
                }
            )
        ],
        style={
            'height': '75vh',
        }
    ),
    html.Div([
            html.H2(
                "Market Overview"
            ),
            dcc.Graph(id='overview-graph')
        ],
        style={
            'height': '75vh',
            'margin': '20px auto'
        }
    ),
    html.Div([
            html.H2(
                "Market Health"
            ),
            dcc.Graph(id='health-graph')
        ],
        style={
            'height': '75vh',
            'margin': '20px auto'
        }
    )
], style={
    'width': '75%',
    'margin': 'auto'
})


@app.callback(
    [
        dash.dependencies.Output("layer", "children"),
        dash.dependencies.Output("map", "bounds"),
        dash.dependencies.Output('overview-graph', 'figure'),
        dash.dependencies.Output('health-graph', 'figure')
    ],
    [
        dash.dependencies.Input('demo-dropdown', 'value')
    ]
)
def update_output(value):
    # print(sorted_df.area_name_en.str.contains(value))
    # filtered_df = sorted_df[sorted_df['area_name_en'].str.contains(value)]
    s = sorted_df
    sales_dt = sorted_df.groupby(['instance_date'])['index']\
        .count().reset_index(name="count_col")
    overview_x = sales_dt.instance_date.to_list()
    overview_y = sales_dt.count_col.to_list()
    average_sales = sorted_df.groupby('instance_date')['meter_sale_price']\
        .mean().reset_index(name="meter_sale_price")
    average_x = average_sales['instance_date'].to_list()
    average_y = average_sales['meter_sale_price'].to_list()
    if value:
        polyline = None
        pos_data = []
        s = sorted_df[sorted_df.area_name_en == value]

        sales_dt = s.groupby(['instance_date'])['index']\
            .count().reset_index(name="count_col")
        overview_x = sales_dt.instance_date.to_list()
        overview_y = sales_dt.count_col.to_list()

        average_sales = s.groupby('instance_date')['meter_sale_price']\
            .mean().reset_index(name="meter_sale_price")
        average_x = average_sales['instance_date'].to_list()
        average_y = average_sales['meter_sale_price'].to_list()

        res = api.query(district_query.format(value))
        if len(res.ways):
            for node in res.ways[0].nodes:
                pos_data.append([node.lat, node.lon])
            polyline = dl.Polyline(positions=pos_data)
        return polyline, pos_data, px.line(
            x=overview_x,
            y=overview_y,
            labels={'x': 'Date', 'y': 'Sales'}
        ), px.line(
            x=average_x,
            y=average_y,
            labels={'x': 'Date', 'y': 'Sales Price'}
        )
    return None, sample_bounds, px.line(
            x=overview_x,
            y=overview_y,
            labels={'x': 'Date', 'y': 'Sales'}
        ), px.line(
            x=average_x,
            y=average_y,
            labels={'x': 'Date', 'y': 'Sales Price'}
        )


if __name__ == '__main__':
    app.run_server(debug=True)
