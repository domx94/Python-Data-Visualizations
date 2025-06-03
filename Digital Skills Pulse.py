import dash
from dash import dcc, html, Input, Output, State, dash_table
from dash.dash_table.Format import Format, Scheme, Symbol
from dash.dash_table import FormatTemplate
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np
import plotly.express as px
import seaborn as sns
import matplotlib.pyplot as plt
import base64
from io import BytesIO
import os
import datetime

# ----------- FILE PATHS -----------
ONET_DIR = "Project2_Digital_Skills_Pulse_Dash/data/db_29_1_text/"
ITU_CSV = "Project2_Digital_Skills_Pulse_Dash/data/ITU_DH.csv"
BLS_XLSX = "Project2_Digital_Skills_Pulse_Dash/data/oesm24nat/national_M2024_dl.xlsx"

# ----------- LOAD DATA & CLEANING -----------

# O*NET Data
onet_occ = pd.read_csv(ONET_DIR + "Occupation Data.txt", sep="\t", low_memory=False)
onet_tech = pd.read_csv(ONET_DIR + "Technology Skills.txt", sep="\t", low_memory=False)
onet_occ.columns = [c.strip() for c in onet_occ.columns]
onet_tech.columns = [c.strip() for c in onet_tech.columns]

onet_digital = onet_tech[onet_tech['Commodity Title'].str.contains("Computer|Software|Python|AI", na=False, case=False)]
top_onet_digital = onet_digital['O*NET-SOC Code'].value_counts().head(10)
top_onet_jobs = onet_occ[onet_occ['O*NET-SOC Code'].isin(top_onet_digital.index)]

# World Bank/ITU
itu = pd.read_csv(ITU_CSV)
itu.columns = [c.strip().upper() for c in itu.columns]
if 'REF_AREA_LABEL' in itu.columns and 'TIME_PERIOD' in itu.columns:
    latest_itu = itu.sort_values(['REF_AREA_LABEL', 'TIME_PERIOD']).drop_duplicates(['REF_AREA_LABEL'], keep='last')
else:
    raise Exception("Missing columns in ITU data: check that 'REF_AREA_LABEL' and 'TIME_PERIOD' exist.")
if 'OBS_VALUE' in itu.columns:
    latest_itu['OBS_VALUE'] = pd.to_numeric(latest_itu['OBS_VALUE'], errors='coerce')
else:
    raise Exception("Missing 'OBS_VALUE' column in ITU data.")

# BLS Data
bls = pd.read_excel(BLS_XLSX)
bls.columns = [c.strip().upper() for c in bls.columns]
for col in ["A_MEDIAN", "TOT_EMP"]:
    bls[col] = pd.to_numeric(bls[col], errors="coerce")
bls = bls.dropna(subset=["A_MEDIAN", "TOT_EMP"])
bls = bls[bls["A_MEDIAN"] > 0]
bls = bls[bls["TOT_EMP"] > 0]
grouped_bls = bls.groupby('OCC_TITLE').agg({'TOT_EMP': 'sum', 'A_MEDIAN': 'median'}).reset_index()

# ----------- DASH APP INIT -----------
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.FLATLY, dbc.themes.DARKLY],
    suppress_callback_exceptions=True   # <--- ADD THIS!
)

app.title = "Digital Skills Pulse: Global Workforce Visualizer"

# Sort options for BLS
# ---- Sorting options for dropdown ----
sort_options = [
    {'label': 'Top by Employment', 'value': 'TOT_EMP'},
    {'label': 'Top by Median Salary', 'value': 'A_MEDIAN'}
]


# --- BLS Markdown explainer ---
bls_explainer = dcc.Markdown("""
**About US Occupational Data (BLS):**
- Data reflects major US occupation groups and their national employment and median annual salary (BLS OEWS 2024).
- _"Total Employed"_ is the estimated number of jobs in the occupation group.
- _"Median Salary"_ is the annual median wage for that group.
- Only the top 15 groups by size are shown.
""", style={"marginBottom": "1rem"})

def boxplot_img(sorted_bls):
    fig, ax = plt.subplots(figsize=(14, 8))
    sns.boxplot(data=sorted_bls, y="OCC_TITLE", x="A_MEDIAN", ax=ax, color='#2563eb')
    ax.set_title("Salary Distribution by Occupation Group", fontsize=18, pad=18)
    ax.set_xlabel("Median Salary ($)", fontsize=15)
    ax.set_ylabel("")
    ax.tick_params(axis="y", labelsize=13)
    ax.tick_params(axis="x", labelsize=13)
    plt.tight_layout()
    buf = BytesIO()
    plt.savefig(buf, format="png", bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    img_b64 = base64.b64encode(buf.read()).decode('utf-8')
    return "data:image/png;base64," + img_b64

SIDEBAR_STYLE = {
    "position": "fixed", "top": 0, "left": 0, "bottom": 0,
    "width": "19rem", "padding": "2rem 1rem", "backgroundColor": "#0a2540", "color": "#f8fafc", "zIndex": 100,
}
CONTENT_STYLE = {"marginLeft": "21rem", "marginRight": "2rem", "padding": "2rem 1rem"}

sidebar = html.Div([
    html.H2("🌐 Digital Skills Pulse", style={"fontWeight": 900, "fontSize": "1.9rem", "marginBottom": "1.5rem"}),
    html.Hr(),
    html.P("Explore digital skill trends and jobs across the globe", style={"fontSize": "1.1rem", "color": "#f8fafc"}),
    dbc.Nav([
        dbc.NavLink("Overview", href="/", active="exact", id="nav-overview"),
        dbc.NavLink("US Jobs (BLS)", href="/us-jobs", active="exact", id="nav-bls"),
        dbc.NavLink("World Digital Skills", href="/global-skills", active="exact", id="nav-itu"),
        dbc.NavLink("O*NET Tech Skills", href="/onet", active="exact", id="nav-onet"),
    ], vertical=True, pills=True),
    html.Hr(),
], style=SIDEBAR_STYLE, id="sidebar")

def overview_layout():
    return html.Div([
        html.H2("🌍 Digital Skills & Workforce Analytics", style={"fontWeight": 800}),
        html.P("Data sources: US BLS, O*NET, World Bank ITU. Explore workforce trends in digital skills and job demand."),
        dbc.Row([
            dbc.Col(dbc.Card([
                dbc.CardHeader("US Total Jobs"),
                dbc.CardBody([html.H4(f"{int(bls['TOT_EMP'].sum()):,}", id="kpi-total-usjobs", style={"fontWeight": 800})])
            ], color="primary", inverse=True)),
            dbc.Col(dbc.Card([
                dbc.CardHeader("World: Median Digital Adoption (ITU)"),
                dbc.CardBody([html.H4(f"{latest_itu['OBS_VALUE'].median():.2f}", id="kpi-itu", style={"fontWeight": 800})])
            ], color="info", inverse=True)),
            dbc.Col(dbc.Card([
                dbc.CardHeader("Top O*NET Digital Jobs"),
                dbc.CardBody([html.H4(top_onet_jobs['Title'].iloc[0] if len(top_onet_jobs) else "N/A", id="kpi-onet", style={"fontWeight": 800})])
            ], color="success", inverse=True)),
        ], className="mb-4"),
        html.Hr(),
        html.H5("Quick Preview: US Job Market"),
        dcc.Graph(figure=px.bar(
            grouped_bls.sort_values("TOT_EMP", ascending=False).head(15), x="OCC_TITLE", y="TOT_EMP",
            labels={"OCC_TITLE": "Occupation Group", "TOT_EMP": "Total Employed"},
            title="Top US Occupational Groups by Employment",
            template="seaborn"
        )),
        html.H5("Quick Preview: Global Digital Skills"),
        dcc.Graph(figure=px.choropleth(
            latest_itu, locations="REF_AREA_LABEL", locationmode="country names", color="OBS_VALUE",
            color_continuous_scale="Blues", title="Latest Digital Skill Indicator by Country",
            labels={"OBS_VALUE": "Digital Skill Index"}
        )),
        html.H5("Quick Preview: O*NET Digital Skills"),
        dcc.Graph(figure=px.bar(
            top_onet_jobs, x="Title", y="O*NET-SOC Code",
            labels={"Title": "Job Title", "O*NET-SOC Code": "Job Code"},
            title="Top O*NET Computer-Related Occupations",
            template="seaborn"
        )),
        html.Hr(),
        html.Div("Data: O*NET, US BLS, World Bank ITU | App by Dom Weber", style={"opacity": 0.75, "fontSize": "0.9rem"}),
    ])

def bls_layout():
    return html.Div([
        html.H2("🇺🇸 US Jobs & Digital Occupations (BLS)", style={"fontWeight": 800}),
        bls_explainer,
        dcc.Dropdown(
            id='bls-sort-dropdown',
            options=sort_options,
            value='TOT_EMP',
            clearable=False,
            style={"maxWidth": "320px", "marginBottom": "1.2rem"}
        ),
        html.Span(
            [
                html.I(className="bi bi-info-circle", id="bls-sort-help",
                       style={"cursor": "pointer", "fontSize": 20, "marginLeft": "10px"})
            ]
        ),
        dbc.Tooltip(
            "Choose how to sort the Top 15 groups: by Employment (most jobs) or by Median Salary (highest paid).",
            target="bls-sort-help",
            placement="right"
        ),
        dbc.Tooltip(
            "Choose how to sort the top 15 occupations: by number of jobs or by highest median salary.",
            target='bls-sort-dropdown',
            placement="right"
        ),
        html.Div(id='bls-dynamic-content')
    ]),


def itu_layout():
    return html.Div([
        html.H2("🌐 Global Digital Skills (World Bank ITU)", style={"fontWeight": 800}),
        html.P("Compare digital skill adoption, workforce digitization, and technology access by country."),
        dcc.Dropdown(
            id="itu-topn-dropdown",
            options=[{"label": f"Top {n} Countries", "value": n} for n in [10, 20, 30, 50]],
            value=20,
            clearable=False,
            style={"maxWidth": "320px", "marginBottom": "1.2rem"}
        ),
        dcc.Graph(id="itu-choropleth"),
        html.H5("Preview: Top Countries by Digital Skill Index"),
        html.Div(id="itu-table"),
        html.Hr(),
        html.Div(
            f"Last updated: {datetime.datetime.now().strftime('%Y-%m-%d')}",
            style={"fontSize": "0.95rem", "color": "#64748b", "marginBottom": "10px"}
        ),
        html.Div("Source: ITU/World Bank"),
    ])


def onet_layout():
    return html.Div([
        html.H2("🖥️ O*NET: Digital & Technology Skills", style={"fontWeight": 800}),
        html.P("Explore digital and technology skills required for US jobs, using O*NET crosswalk."),
        dcc.Dropdown(
            id="onet-topn-dropdown",
            options=[{"label": f"Top {n} Digital Jobs", "value": n} for n in [10, 20, 30]],
            value=10,
            clearable=False,
            style={"maxWidth": "320px", "marginBottom": "1.2rem"}
        ),
        dcc.Graph(id="onet-bar"),
        html.H5("Preview: Top Digital Occupations"),
        html.Div(id="onet-table"),
        html.Hr(),
        html.Div(
            f"Last updated: {datetime.datetime.now().strftime('%Y-%m-%d')}",
            style={"fontSize": "0.95rem", "color": "#64748b", "marginBottom": "10px"}
        ),
        html.Div("Source: US O*NET Database v29.1"),
    ])


# ----------- SET APP LAYOUT (move this here BEFORE any callback definitions!) -----------
app.layout = html.Div([
    dcc.Location(id="url"),
    sidebar,
    html.Div(id="page-content", style=CONTENT_STYLE)
])

# ----------- CALLBACKS (MUST come AFTER app.layout is set) -----------
@app.callback(
    Output('bls-dynamic-content', 'children'),
    Input('bls-sort-dropdown', 'value')
)

def update_bls_section(sort_by):
    sorted_bls = grouped_bls[~grouped_bls["OCC_TITLE"].str.contains("All Occupations", case=False, na=False)].copy()
    sorted_bls = sorted_bls.sort_values(sort_by, ascending=False).head(15)
    if sorted_bls.empty:
        sorted_bls = pd.DataFrame(columns=["OCC_TITLE", "TOT_EMP", "A_MEDIAN"])

    table_columns = [
        {"name": "Occupation Title", "id": "OCC_TITLE"},
        {"name": "Total Employed", "id": "TOT_EMP", "type": "numeric",
         "format": Format(group=True, scheme=Scheme.fixed, precision=0)},
        {
            "name": "Median Salary ($)",
            "id": "A_MEDIAN",
            "type": "numeric",
            "format": FormatTemplate.money(0)  # No decimals, $ symbol, comma-separators
        }
    ]

    if not sorted_bls.empty:
        top_occ = sorted_bls.iloc[0]['OCC_TITLE']
        top_occ_jobs = int(sorted_bls.iloc[0]['TOT_EMP'])
        top_occ_salary = int(sorted_bls.iloc[0]['A_MEDIAN'])
    else:
        top_occ = "N/A"
        top_occ_jobs = 0
        top_occ_salary = 0

    # ---- QUICK FIX GOES HERE ----
    sorted_bls.columns = [c.strip().upper() for c in sorted_bls.columns]
    # -----------------------------

    return [
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        "Largest US Job Group ",
                        dbc.Badge(
                            "Top Salary" if sort_by == "A_MEDIAN" else "Top Job",
                            color="success" if sort_by == "A_MEDIAN" else "primary",
                            className="ml-2", style={"fontSize": "1em"}
                        )
                    ])
                    ,
                    dbc.CardBody([
                        html.H3(f"{top_occ}", id="kpi-top-occ", style={"fontWeight": 800}),
                        html.Div(f"Total Employed: {top_occ_jobs:,}", style={"fontSize": 18}),
                        html.Div(f"Median Salary: ${top_occ_salary:,}", style={"fontSize": 18, "color": "#2563eb"}),
                        dbc.Tooltip("The occupation group with the highest number of jobs by your selection.", target="kpi-top-occ"),
                    ])
                ], color="primary", inverse=True, className="mb-4")
            ], md=7),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Download as CSV"),
                    dbc.CardBody([
                        dbc.Button("⬇️ Download Data", id="bls-download-btn", color="success", className="mb-2"),
                        dcc.Download(id="bls-download-data"),
                    ])
                ], color="success", inverse=False, className="mb-4")
            ], md=5),
        ], className="mb-2"),

        html.Hr(),
        html.Div(
            f"Last updated: {datetime.datetime.now().strftime('%Y-%m-%d')}",
            style={"fontSize": "0.95rem", "color": "#64748b", "marginBottom": "10px"}
        ),

        html.H5(f"Top 15 US Occupational Groups by {'Employment' if sort_by=='TOT_EMP' else 'Median Salary'}"),
        dcc.Graph(
            figure=px.bar(
                sorted_bls, x="OCC_TITLE", y=sort_by,
                labels={"OCC_TITLE": "Occupation Group", sort_by: ("Total Employed" if sort_by == "TOT_EMP" else "Median Salary ($)")},
                color=sort_by, color_continuous_scale="Blues" if sort_by=="TOT_EMP" else "Viridis",
                template="seaborn"
            ),
            style={"height": "480px"}
        ),

        html.Div([
            html.H5("Salary Distribution (Boxplot)"),
            html.Img(src=boxplot_img(sorted_bls), style={
                "width": "99%", "maxWidth": "1200px", "marginBottom": "1.5rem", "borderRadius": "10px",
                "boxShadow": "0 2px 12px rgba(0,0,0,0.12)"
            }),
        ]),

        html.H5("Preview: Top 15 Job Groups"),
        dash_table.DataTable(
            data=sorted_bls.to_dict('records'),
            columns=table_columns,
            page_size=15,
            style_table={"overflowX": "auto"},
            style_cell={
                "fontFamily": "Segoe UI,Roboto,Arial,sans-serif",
                "fontSize": 15,
                "color": "#101828",  # <--- ADD THIS LINE!
                "backgroundColor": "#fff"  # (Optional, to force cell bg to white, ensures contrast)
            },
            style_header={
                "fontWeight": "bold",
                "backgroundColor": "#0a2540",
                "color": "#fff"
            },
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': '#f9fafb'
                }
            ]
        )
        ,
        html.Hr(),
        html.Div("Source: US Bureau of Labor Statistics (BLS OEWS 2024)", style={"fontSize": "1rem", "opacity": 0.85}),

    ]

@app.callback(
    Output("bls-download-data", "data"),
    Input("bls-download-btn", "n_clicks"),
    State('bls-sort-dropdown', 'value'),
    prevent_initial_call=True
)
def download_bls_top15(n_clicks, sort_by):
    sorted_bls = grouped_bls[~grouped_bls["OCC_TITLE"].str.contains("All Occupations", case=False, na=False)]
    sorted_bls = sorted_bls.sort_values(sort_by, ascending=False).head(15)
    return dcc.send_data_frame(sorted_bls.to_csv, "bls_top15.csv", index=False)

# --- ITU Callback for Global Digital Skills Page ---
@app.callback(
    [Output("itu-choropleth", "figure"),
     Output("itu-table", "children")],
    [Input("itu-topn-dropdown", "value")]
)
def update_itu_section(top_n):
    top_countries = latest_itu.sort_values("OBS_VALUE", ascending=False).head(top_n)
    fig = px.choropleth(
        latest_itu, locations="REF_AREA_LABEL", locationmode="country names", color="OBS_VALUE",
        color_continuous_scale="Viridis", title="Global Digital Skills (ITU Indicator)",
        labels={"OBS_VALUE": "Digital Skill Index"}
    )
    table = dash_table.DataTable(
        data=top_countries[["REF_AREA_LABEL", "OBS_VALUE"]].rename(
            columns={"REF_AREA_LABEL": "Country", "OBS_VALUE": "Digital Skill Index"}
        ).to_dict('records'),
        columns=[
            {"name": "Country", "id": "Country"},
            {"name": "Digital Skill Index", "id": "Digital Skill Index"}
        ],
        page_size=top_n,
        style_table={"overflowX": "auto"},
        style_cell={
            "fontFamily": "Segoe UI,Roboto,Arial,sans-serif",
            "fontSize": 15,
            "color": "#101828",  # <--- ADD THIS LINE!
            "backgroundColor": "#fff"  # (Optional, to force cell bg to white, ensures contrast)
        },
        style_header={"fontWeight": "bold", "backgroundColor": "#0a2540", "color": "#fff"},
        style_data_conditional=[
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': '#f9fafb'
            }
        ]
    )
    return fig, table

# --- O*NET Callback for Digital Jobs Page ---
@app.callback(
    [Output("onet-bar", "figure"),
     Output("onet-table", "children")],
    [Input("onet-topn-dropdown", "value")]
)
def update_onet_section(top_n):
    digital_counts = onet_tech[onet_tech['Commodity Title'].str.contains(
        "Computer|Software|Python|AI", na=False, case=False)
    ]['O*NET-SOC Code'].value_counts().reset_index()
    digital_counts.columns = ['O*NET-SOC Code', 'Count']

    merged = pd.merge(digital_counts, onet_occ, left_on='O*NET-SOC Code', right_on='O*NET-SOC Code', how='left')
    merged = merged[['Title', 'O*NET-SOC Code', 'Count']].head(top_n)

    fig = px.bar(
        merged, x='Title', y='Count',
        labels={'Title': 'Job Title', 'Count': 'Digital Skills Mentioned'},
        title=f"Top {top_n} O*NET Digital Occupations",
        template="seaborn"
    )
    table = dash_table.DataTable(
        data=merged.to_dict('records'),
        columns=[
            {"name": "Job Title", "id": "Title"},
            {"name": "O*NET Code", "id": "O*NET-SOC Code"},
            {"name": "Skill Mentions", "id": "Count"},
        ],
        page_size=top_n,
        style_table={"overflowX": "auto"},
        style_cell={
            "fontFamily": "Segoe UI,Roboto,Arial,sans-serif",
            "fontSize": 15,
            "color": "#101828",  # <--- ADD THIS LINE!
            "backgroundColor": "#fff"  # (Optional, to force cell bg to white, ensures contrast)
        },
        style_header={"fontWeight": "bold", "backgroundColor": "#0a2540", "color": "#fff"},
        style_data_conditional=[
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': '#f9fafb'
            }
        ]
    )
    return fig, table



@app.callback(Output("page-content", "children"), [Input("url", "pathname")])
def render_page(pathname):
    if pathname == "/" or pathname is None:
        return overview_layout()
    elif pathname == "/us-jobs":
        return bls_layout()
    elif pathname == "/global-skills":
        return itu_layout()
    elif pathname == "/onet":
        return onet_layout()
    else:
        return html.Div([html.H2("404: Page Not Found")])

if __name__ == "__main__":
    app.run(debug=True)
