import dash
from dash import dcc, html, dash_table
import pandas as pd
import plotly.express as px
import dash_bootstrap_components as dbc

# ---------- Load and Clean Data ----------
df = pd.read_csv("data.csv", encoding="ISO-8859-1")
df.columns = df.columns.str.strip()  # Clean any whitespace in column names

# Parse date and time columns
df['published_date'] = pd.to_datetime(df['published_date'], dayfirst=True, errors='coerce')
df['published_time'] = pd.to_datetime(df['published_time'], format='%H:%M:%S', errors='coerce').dt.time

# Convert numeric columns
df['relevance_score'] = pd.to_numeric(df['relevance_score'], errors='coerce')
df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')

# Fill missing values
df['sentiment'] = df['sentiment'].fillna("unknown")
df['country'] = df['country'].fillna("Unknown")

# ---------- Summary Metrics ----------
total_articles = len(df)
unique_sources = df['source'].nunique()
unique_countries = df['country'].nunique()
top_keywords = df['keyword'].value_counts().nlargest(5)

# ---------- Figures ----------
# Sentiment Pie Chart
sentiment_pie = px.pie(df, names='sentiment', title='Sentiment Distribution')

# Country-wise Article Bar Chart
country_counts = df['country'].value_counts().nlargest(10).reset_index()
country_counts.columns = ['country', 'count']
country_bar = px.bar(country_counts, x='country', y='count', title='Top 10 Countries by Article Count')

# Time Series Chart
time_series = df.groupby('published_date').size().reset_index(name='count')
date_line = px.line(time_series, x='published_date', y='count', title='Articles Over Time')

# ---------- Dash App ----------
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server  # Required for deployment

app.layout = dbc.Container([
    html.H1("📰 Global News Dashboard", className="text-center my-4"),

    # Cards Row
    dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardHeader("Total Articles"),
            dbc.CardBody(html.H4(f"{total_articles}", className="card-title"))
        ]), width=4),
        dbc.Col(dbc.Card([
            dbc.CardHeader("Unique Sources"),
            dbc.CardBody(html.H4(f"{unique_sources}", className="card-title"))
        ]), width=4),
        dbc.Col(dbc.Card([
            dbc.CardHeader("Countries Covered"),
            dbc.CardBody(html.H4(f"{unique_countries}", className="card-title"))
        ]), width=4),
    ], className="mb-4"),

    # Charts Row
    dbc.Row([
        dbc.Col(dcc.Graph(figure=sentiment_pie), md=6),
        dbc.Col(dcc.Graph(figure=country_bar), md=6)
    ], className="mb-4"),

    # Time Series Chart
    dbc.Row([
        dbc.Col(dcc.Graph(figure=date_line), md=12)
    ], className="mb-4"),

    # Top Keywords
    html.H4("🔥 Top Keywords", className="mb-2"),
    html.Ul([html.Li(f"{k}: {v}") for k, v in top_keywords.items()]),

    html.Hr(),

    # Data Table
    html.H4("📋 News Table"),
    dash_table.DataTable(
        data=df.to_dict('records'),
        columns=[{"name": col, "id": col} for col in df.columns],
        page_size=10,
        filter_action="native",
        sort_action="native",
        style_table={'overflowX': 'auto'},
        style_cell={'textAlign': 'left', 'padding': '5px'}
    )
], fluid=True)

# ---------- Run App ----------
if __name__ == "__main__":
    app.run(debug=True)
