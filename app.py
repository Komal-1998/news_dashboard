import pandas as pd
import dash
from dash import dcc, html, Input, Output, dash_table
import plotly.express as px

# Load data
df = pd.read_csv("news article_with_coordinates.csv", encoding="ISO-8859-1")
df["publish_date"] = pd.to_datetime(df["publish_date"], errors="coerce")
df.dropna(subset=["publish_date", "category", "counties", "media"], inplace=True)
df["publish_date_only"] = df["publish_date"].dt.date

# Initialize app
app = dash.Dash(__name__)
app.title = "Hazard News Dashboard"

# Layout
app.layout = html.Div(style={"font-family": "Arial, sans-serif", "padding": "20px"}, children=[
    html.H1("UK Hazard Intelligence Dashboard", style={"textAlign": "center", "color": "#2c3e50"}),

    html.Div(id="media-count", style={
        "textAlign": "center",
        "fontSize": "18px",
        "color": "#34495e",
        "marginBottom": "20px"
    }),

    # Filters
    html.Div([
        html.Div([
            html.Label("Select Hazard Category:", style={"fontWeight": "bold"}),
            dcc.Dropdown(
                id="category-dropdown",
                options=[{"label": cat, "value": cat} for cat in sorted(df["category"].unique())],
                value=None,
                placeholder="All categories",
                multi=True
            ),
        ], style={"width": "24%", "display": "inline-block", "marginRight": "1%"}),

        html.Div([
            html.Label("Select County:", style={"fontWeight": "bold"}),
            dcc.Dropdown(
                id="county-dropdown",
                options=[{"label": county, "value": county} for county in sorted(df["counties"].unique())],
                value=None,
                placeholder="All counties",
                multi=True
            ),
        ], style={"width": "24%", "display": "inline-block", "marginRight": "1%"}),

        html.Div([
            html.Label("Select Date Range:", style={"fontWeight": "bold"}),
            dcc.DatePickerRange(
                id="date-range-picker",
                start_date=df["publish_date"].min().date(),
                end_date=df["publish_date"].max().date(),
                display_format="YYYY-MM-DD"
            ),
        ], style={"width": "48%", "display": "inline-block"}),
    ], style={"marginBottom": "30px"}),

    # Bar Chart
    html.Div([
        dcc.Graph(id="bar-category-counts")
    ], style={"marginBottom": "40px"}),

    # Pie + Line Plot
    html.Div([
        html.Div([
            dcc.Graph(id="pie-media-by-county")
        ], style={"width": "49%", "display": "inline-block", "paddingRight": "1%"}),

        html.Div([
            dcc.Graph(id="line-county-time-series")
        ], style={"width": "49%", "display": "inline-block"}),
    ], style={"marginBottom": "40px"}),

    # Filtered News Table
    html.H2("Filtered News Articles", style={"color": "#2c3e50", "paddingLeft": "10px"}),

    dash_table.DataTable(
        id="news-table",
        columns=[
            {"name": "Published Date", "id": "publish_date"},
            {"name": "Title", "id": "title_link", "presentation": "markdown"},
            {"name": "County", "id": "counties"},
            {"name": "Category", "id": "category"},
            {"name": "Media", "id": "media"},
        ],
        page_size=20,
        style_table={"overflowX": "auto", "border": "1px solid #ccc", "borderRadius": "8px"},
        style_cell={
            "textAlign": "left",
            "padding": "12px",
            "fontFamily": "Arial, sans-serif",
            "fontSize": "14px",
        },
        style_header={
            "backgroundColor": "#2c3e50",
            "fontWeight": "bold",
            "color": "white",
            "border": "1px solid #ccc",
        },
        style_data={
            "backgroundColor": "#ffffff",
            "border": "1px solid #ddd",
        },
        style_data_conditional=[
            {"if": {"row_index": "odd"}, "backgroundColor": "#f9f9f9"},
            {"if": {"state": "active"}, "backgroundColor": "#d0e7f5", "border": "1px solid #7ec0ee"},
            {"if": {"state": "selected"}, "backgroundColor": "#cce5ff", "border": "1px solid #3399ff"},
        ],
    )
])

# Callback
@app.callback(
    Output("media-count", "children"),
    Output("pie-media-by-county", "figure"),
    Output("line-county-time-series", "figure"),
    Output("bar-category-counts", "figure"),
    Output("news-table", "data"),
    Input("category-dropdown", "value"),
    Input("county-dropdown", "value"),
    Input("date-range-picker", "start_date"),
    Input("date-range-picker", "end_date"),
)
def update_dashboard(selected_categories, selected_counties, start_date, end_date):
    filtered_df = df.copy()

    if selected_categories:
        filtered_df = filtered_df[filtered_df["category"].isin(selected_categories)]
    if selected_counties:
        filtered_df = filtered_df[filtered_df["counties"].isin(selected_counties)]
    if start_date and end_date:
        filtered_df = filtered_df[
            (filtered_df["publish_date"] >= pd.to_datetime(start_date)) &
            (filtered_df["publish_date"] <= pd.to_datetime(end_date))
        ]

    # Media count
    media_count = filtered_df["media"].nunique()
    media_text = f"Number of unique news medias: {media_count}"

    # Bar Chart: Number of Articles per Hazard
    cat_counts = filtered_df["category"].value_counts().reset_index()
    cat_counts.columns = ["category", "count"]
    bar = px.bar(
        cat_counts,
        x="category",
        y="count",
        title="Number of Articles per Hazard Type",
        color="category",
        color_discrete_sequence=px.colors.qualitative.Set2
    )

    # Pie Chart: Media by Counties
    county_media_counts = filtered_df.groupby("counties")["media"].nunique().reset_index(name="unique_medias")
    county_media_counts = county_media_counts.sort_values("unique_medias", ascending=False).head(10)
    pie = px.pie(
        county_media_counts,
        names="counties",
        values="unique_medias",
        title="Top 10 Counties by Number of Unique News Medias",
        color_discrete_sequence=px.colors.sequential.RdBu
    )

    # Line Plot: Time Series of Articles per County
    line_data = filtered_df.groupby(["publish_date_only", "counties"]).size().reset_index(name="article_count")
    line = px.line(
        line_data,
        x="publish_date_only",
        y="article_count",
        color="counties",
        title="Time Series of Articles by County",
        labels={"publish_date_only": "Date", "article_count": "Number of Articles"},
        color_discrete_sequence=px.colors.qualitative.Set2
    )

    # Format news table
    filtered_df = filtered_df.sort_values("publish_date", ascending=False).copy()
    filtered_df["publish_date"] = filtered_df["publish_date"].dt.strftime("%Y-%m-%d")
    filtered_df["title_link"] = filtered_df.apply(
        lambda row: f"[{row['title']}]({row['url']})", axis=1
    )
    table_data = filtered_df[[
        "publish_date", "title_link", "counties", "category", "media"
    ]].to_dict("records")

    return media_text, pie, line, bar, table_data

# Run the app locally
if __name__ == '__main__':
    app.run(debug=True)

# For deployment
server = app.server
