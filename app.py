import pandas as pd
import dash
from dash import dcc, html, Input, Output, dash_table
import plotly.express as px

# Load data
df = pd.read_csv("final_dataset.csv", encoding="ISO-8859-1")
df["published_date"] = pd.to_datetime(df["published_date"], errors="coerce")
df.dropna(subset=["published_date", "category", "cities"], inplace=True)
df["published_date_only"] = df["published_date"].dt.date

# Initialize app
app = dash.Dash(__name__)
app.title = "Hazard News Dashboard"

# Layout
app.layout = html.Div(style={"font-family": "Arial, sans-serif", "padding": "20px"}, children=[
    html.H1("Hazard News Intelligence Dashboard", style={"textAlign": "center", "color": "#2c3e50"}),

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
            html.Label("Select City:", style={"fontWeight": "bold"}),
            dcc.Dropdown(
                id="city-dropdown",
                options=[{"label": city, "value": city} for city in sorted(df["cities"].unique())],
                value=None,
                placeholder="All cities",
                multi=True
            ),
        ], style={"width": "24%", "display": "inline-block", "marginRight": "1%"}),

        html.Div([
            html.Label("Select Date Range:", style={"fontWeight": "bold"}),
            dcc.DatePickerRange(
                id="date-range-picker",
                start_date=df["published_date"].min().date(),
                end_date=df["published_date"].max().date(),
                display_format="YYYY-MM-DD"
            ),
        ], style={"width": "48%", "display": "inline-block"}),
    ], style={"marginBottom": "30px"}),

    # Bar Chart First
    html.Div([
        dcc.Graph(id="bar-category-counts")
    ], style={"marginBottom": "40px"}),

    # Then the two pie charts
    html.Div([
        html.Div([
            dcc.Graph(id="pie-cities-total")
        ], style={"width": "49%", "display": "inline-block", "paddingRight": "1%"}),

        html.Div([
            dcc.Graph(id="pie-cities-by-hazard")
        ], style={"width": "49%", "display": "inline-block"}),
    ], style={"marginBottom": "40px"}),

    # Filtered News Table
    html.H2("Filtered News Articles", style={"color": "#2c3e50", "paddingLeft": "10px"}),

    dash_table.DataTable(
        id="news-table",
        columns=[
            {"name": "Published Date", "id": "published_date"},
            {"name": "Title", "id": "title_link", "presentation": "markdown"},
            {"name": "City", "id": "cities"},
            {"name": "Category", "id": "category"},
            {"name": "Source", "id": "source"},
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
    Output("pie-cities-total", "figure"),
    Output("pie-cities-by-hazard", "figure"),
    Output("bar-category-counts", "figure"),
    Output("news-table", "data"),
    Input("category-dropdown", "value"),
    Input("city-dropdown", "value"),
    Input("date-range-picker", "start_date"),
    Input("date-range-picker", "end_date"),
)
def update_dashboard(selected_categories, selected_cities, start_date, end_date):
    filtered_df = df.copy()

    if selected_categories:
        filtered_df = filtered_df[filtered_df["category"].isin(selected_categories)]
    if selected_cities:
        filtered_df = filtered_df[filtered_df["cities"].isin(selected_cities)]
    if start_date and end_date:
        filtered_df = filtered_df[
            (filtered_df["published_date"] >= pd.to_datetime(start_date)) &
            (filtered_df["published_date"] <= pd.to_datetime(end_date))
        ]

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

    # Pie Chart 1: Top 10 Cities with Most Hazards
    city_counts = filtered_df["cities"].value_counts().nlargest(10)
    pie1 = px.pie(
        names=city_counts.index,
        values=city_counts.values,
        title="Top 10 Cities with Most Reported Hazards",
        color_discrete_sequence=px.colors.sequential.RdBu
    )

    # Pie Chart 2: Top 10 City–Hazard Combinations
    city_cat_group = filtered_df.groupby(["cities", "category"]).size().reset_index(name="count")
    top_city_cat = city_cat_group.sort_values("count", ascending=False).head(10)
    pie2 = px.pie(
        names=top_city_cat.apply(lambda row: f"{row['cities']} - {row['category']}", axis=1),
        values=top_city_cat["count"],
        title="Cities by Hazard Category Diversity",
        color_discrete_sequence=px.colors.sequential.Tealgrn
    )

    # Format news table
    filtered_df = filtered_df.sort_values("published_date", ascending=False).copy()
    filtered_df["published_date"] = filtered_df["published_date"].dt.strftime("%Y-%m-%d")
    filtered_df["title_link"] = filtered_df.apply(
        lambda row: f"[{row['title']}]({row['url']})", axis=1
    )
    table_data = filtered_df[[
        "published_date", "title_link", "cities", "category", "source"
    ]].to_dict("records")

    return pie1, pie2, bar, table_data

# Run
if __name__ == "__main__":
    app.run(debug=True)
