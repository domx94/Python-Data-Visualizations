"""
Scenario 1: Healthcare Cost & Outcome Analytics (Enhanced UI)
Features: Dark Mode Toggle, Download to Excel, Animated Chart Transitions
"""
import pandas as pd
import numpy as np
import plotly.express as px
import dash
from dash import Dash, dcc, html, Input, Output, State, ctx, dash_table
import dash_bootstrap_components as dbc
from datetime import timedelta
from io import BytesIO
import base64
import openpyxl


# --- 1. Synthetic Healthcare Data ---
np.random.seed(42)
n_patients = 5000
start_date = pd.to_datetime('2022-01-01')
end_date = pd.to_datetime('2023-12-31')
dates = pd.to_datetime(np.random.choice(pd.date_range(start_date, end_date), n_patients))
genders = np.random.choice(['Male', 'Female', 'Other'], n_patients, p=[0.48, 0.48, 0.04])
diag_groups = np.random.choice(['Cardio', 'Neuro', 'Ortho', 'Respiratory', 'Gastro'], n_patients)
costs = np.random.normal(loc=8000, scale=2500, size=n_patients)
costs = np.round(np.clip(costs, 1000, 25000), 2)
outcomes = np.random.choice(['Recovered', 'Readmitted', 'Complication', 'Deceased'], n_patients, p=[0.75, 0.12, 0.1, 0.03])

patients = pd.DataFrame({
    'PatientID': np.arange(1, n_patients+1),
    'AdmissionDate': dates,
    'Gender': genders,
    'Diagnosis': diag_groups,
    'Cost': costs,
    'Outcome': outcomes
})

# --- 2. Theme Helper (colors, dropdowns, etc.) ---
def get_theme(dark):
    kpi_value_light = {
        "color": "#21243d",  # nearly black for light mode
        "fontWeight": 800,
        "fontSize": "2rem",
        "letterSpacing": "0.01em",
        "marginBottom": "0.1rem",
        "marginTop": "-0.15rem",
        "fontFamily": "'Segoe UI', 'Roboto', 'Arial', sans-serif"
    }
    kpi_value_dark = {
        "color": "#fff",  # white for dark mode
        "fontWeight": 800,
        "fontSize": "2rem",
        "letterSpacing": "0.01em",
        "marginBottom": "0.1rem",
        "marginTop": "-0.15rem",
        "fontFamily": "'Segoe UI', 'Roboto', 'Arial', sans-serif"
    }
    dropdown_light = {
        "backgroundColor": "#fff",
        "color": "#21243d",  # nearly black
        "fontWeight": 600,
        "border": "2px solid #1564bf",
        "borderRadius": "0.8rem",
        "fontFamily": "'Segoe UI', 'Roboto', 'Arial', sans-serif",
        "padding": "0.6rem",
        "minHeight": "46px",
        "boxShadow": "0 1px 10px rgba(21,100,191,0.08)",
        "caretColor": "#1564bf"
    }
    dropdown_dark = {
        "backgroundColor": "#181e28",
        "color": "#f8fafc",
        "fontWeight": 600,
        "border": "2px solid #38bdf8",
        "borderRadius": "0.8rem",
        "fontFamily": "'Segoe UI', 'Roboto', 'Arial', sans-serif",
        "padding": "0.6rem",
        "minHeight": "46px",
        "boxShadow": "0 1px 10px rgba(56,189,248,0.15)",
        "caretColor": "#38bdf8"
    }
    if dark:
        return {
            'bg_color': '#12151d',
            'card_color': '#23272f',
            'header_color': '#38bdf8',
            'accent_color': '#fff',
            'font_family': "'Segoe UI', 'Roboto', 'Arial', sans-serif",
            'theme_colors': px.colors.qualitative.Prism,
            'dropdown': dropdown_dark,
            'kpi_value': kpi_value_dark,  # <--- THIS IS NEW
        }
    else:
        return {
            'bg_color': '#f4f8fb',
            'card_color': '#fff',
            'header_color': '#0A2540',
            'accent_color': '#12151d',
            'font_family': "'Segoe UI', 'Roboto', 'Arial', sans-serif",
            'theme_colors': px.colors.qualitative.Prism,
            'dropdown': dropdown_light,
            'kpi_value': kpi_value_light,  # <--- THIS IS NEW
        }

def make_summary_table(df):
    summary = df.groupby(['Diagnosis', 'Outcome']).agg(
        Count=('PatientID', 'count'),
        AvgCost=('Cost', 'mean')
    ).reset_index()
    return summary

# --- 3. Dash App Layout ---
app = Dash(__name__, external_stylesheets=[dbc.themes.FLATLY, dbc.themes.DARKLY])
app.title = "Healthcare Cost & Outcome Analytics"

app.layout = html.Div([
    dcc.Store(id='dark-mode', data=False),
    dbc.Container([
        html.Div([
            html.H2("📝 Healthcare Cost & Outcome Analytics", id="main-header", style={"fontWeight": 800, "letterSpacing": "0.02em", "marginTop": "2rem"}),
            html.H6("Interactive dashboard demo | Python, Plotly Dash", id="subtitle", style={"marginBottom": "1rem"}),
            dbc.Button(
                ["🌙 ", "Dark Mode"], id="dark-toggle", color="info", size="sm", style={"float": "right", "marginTop": "-3.5rem"}
            ),
        ]),
        # --- KPI Cards (All ids must be unique!) ---
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Avg Cost ($)"),
                    dbc.CardBody([
                        html.H4(id="kpi-avg-cost"),   # <-- unique id
                        html.Div("Filtered sample only.", style={"fontSize": 13, "opacity": 0.7})
                    ])
                ], id="kpi-card1", style={"marginBottom": "1.1rem"})
            ]),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Recovery Rate (%)"),
                    dbc.CardBody([
                        html.H4(id="kpi-recovery"),   # <-- unique id
                        html.Div("Filtered sample only.", style={"fontSize": 13, "opacity": 0.7})
                    ])
                ], id="kpi-card2", style={"marginBottom": "1.1rem"})
            ]),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Readmission Rate (%)"),
                    dbc.CardBody([
                        html.H4(id="kpi-readmit"),    # <-- unique id
                        html.Div("Filtered sample only.", style={"fontSize": 13, "opacity": 0.7})
                    ])
                ], id="kpi-card3", style={"marginBottom": "1.1rem"})
            ]),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Total Patients"),
                    dbc.CardBody([
                        html.H4(id="kpi-total"),      # <-- unique id
                        html.Div("Filtered sample only.", style={"fontSize": 13, "opacity": 0.7})
                    ])
                ], id="kpi-card4", style={"marginBottom": "1.1rem"})
            ]),
        ]),
        # --- Filtering Controls (unchanged) ---
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("📚 Diagnosis Group"),
                    dbc.CardBody([
                        dcc.Dropdown(
                            options=[{"label": d, "value": d} for d in sorted(patients['Diagnosis'].unique())],
                            value=[], multi=True, id="diag-dropdown",
                            placeholder="Filter by diagnosis..."
                        ),
                    ]),
                ], id="diag-card"),
            ], md=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("♀♂ Gender"),
                    dbc.CardBody([
                        dcc.Dropdown(
                            options=[{"label": g, "value": g} for g in sorted(patients['Gender'].unique())],
                            value=[], multi=True, id="gender-dropdown",
                            placeholder="Filter by gender..."
                        ),
                    ]),
                ], id="gender-card"),
            ], md=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("📅 Date Range"),
                    dbc.CardBody([
                        dcc.DatePickerRange(
                            id='date-picker',
                            min_date_allowed=patients['AdmissionDate'].min(),
                            max_date_allowed=patients['AdmissionDate'].max(),
                            start_date=patients['AdmissionDate'].min(),
                            end_date=patients['AdmissionDate'].max(),
                            display_format='MMM D, YYYY',
                            style={"width": "100%"}
                        )
                    ]),
                ], id="date-card"),
            ], md=6)
        ], className="mb-2"),
        # --- Visuals (Unchanged) ---
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Average Cost per Patient"),
                    dbc.CardBody([
                        dcc.Graph(id="avg-cost-chart", config={"displayModeBar": False, "staticPlot": False})
                    ]),
                ], id="avg-cost-card"),
            ], md=6),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Patient Outcomes Breakdown"),
                    dbc.CardBody([
                        dcc.Graph(id="outcome-pie", config={"displayModeBar": False, "staticPlot": False})
                    ]),
                ], id="outcome-pie-card"),
            ], md=6)
        ]),
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Outcomes & Avg Cost per Diagnosis"),
                    dbc.CardBody([
                        dcc.Graph(id="summary-table", config={"displayModeBar": False, "staticPlot": False})
                    ]),
                ], id="summary-card"),
            ]),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Cost Trend Over Time (Monthly Avg)", style={"fontWeight": 600}),
                    dbc.CardBody([
                        dcc.Graph(id="trend-line", config={"displayModeBar": False, "staticPlot": False})
                    ]),
                ], id="trend-card"),
            ])
        ]),
        dbc.Row([
            dbc.Col([
                dbc.Button(
                    ["⬇️ ", "Download Filtered Data (Excel)"], id="download-btn", color="success", className="mt-4"),
                dcc.Download(id="download-data")
            ], width=12, style={"textAlign": "right"}),
        ]),
        html.Div("✨ Sample portfolio dashboard. Created with Dash, Plotly & Bootstrap.", id="footer", style={"textAlign": "center", "marginTop": "2rem", "letterSpacing": "0.02em"}),
    ], fluid=True, id="main-container")
])


# --- 4. Callbacks ---
@app.callback(
    Output('dark-mode', 'data'),
    [Input('dark-toggle', 'n_clicks')],
    [State('dark-mode', 'data')]
)
def toggle_dark_mode(n, current):
    if n is None:
        return False
    return not current

@app.callback(
    [Output("main-container", "style"),
     Output("main-header", "style"),
     Output("subtitle", "style"),
     Output("footer", "style"),
     Output("diag-card", "style"),
     Output("gender-card", "style"),
     Output("date-card", "style"),
     Output("avg-cost-card", "style"),
     Output("outcome-pie-card", "style"),
     Output("summary-card", "style"),
     Output("trend-card", "style"),
     Output("kpi-card1", "style"),
     Output("kpi-card2", "style"),
     Output("kpi-card3", "style"),
     Output("kpi-card4", "style")],
    [Input('dark-mode', 'data')]
)
def set_theme(dark):
    t = get_theme(dark)
    card_style = {"background": t['card_color'], "marginBottom": "1rem", "boxShadow": "0 2px 12px rgba(0,0,0,0.10)", "borderRadius": "1.5rem", "border": "none"}
    header_style = {"color": t['accent_color'], "fontWeight": 900, "fontSize": "2.6rem", "letterSpacing": "0.01em", "marginTop": "2rem", "fontFamily": t['font_family'], "textShadow": "0 1px 0 rgba(0,0,0,0.06)"}
    subtitle_style = {"color": t['header_color'], "marginBottom": "1rem", "fontFamily": t['font_family'], "fontSize": "1.1rem"}
    footer_style = {"textAlign": "center", "marginTop": "2rem", "color": t['header_color'], "letterSpacing": "0.02em", "fontFamily": t['font_family']}
    return [
        {"background": t['bg_color'], "fontFamily": t['font_family'], "paddingBottom": "2rem"},
        header_style,
        subtitle_style,
        footer_style,
        card_style, card_style, card_style, card_style, card_style, card_style, card_style, card_style, card_style, card_style, card_style
    ]

# NEW: KPI Value Styling Callback
@app.callback(
    [Output("kpi-avg-cost", "style"),
     Output("kpi-recovery", "style"),
     Output("kpi-readmit", "style"),
     Output("kpi-total", "style")],
    [Input('dark-mode', 'data')]
)
def style_kpi_values(dark):
    t = get_theme(dark)
    return t['kpi_value'], t['kpi_value'], t['kpi_value'], t['kpi_value']

@app.callback(
    [Output("diag-dropdown", "style"),
     Output("gender-dropdown", "style")],
    [Input('dark-mode', 'data')]
)
def style_dropdowns(dark):
    t = get_theme(dark)
    return t['dropdown'], t['dropdown']



@app.callback(
    [Output("avg-cost-chart", "figure"),
     Output("outcome-pie", "figure"),
     Output("summary-table", "figure"),
     Output("trend-line", "figure"),
     Output("kpi-avg-cost", "children"),
     Output("kpi-recovery", "children"),
     Output("kpi-readmit", "children"),
     Output("kpi-total", "children")],
    [Input("diag-dropdown", "value"),
     Input("gender-dropdown", "value"),
     Input("date-picker", "start_date"),
     Input("date-picker", "end_date"),
     Input('dark-mode', 'data')]
)
def update_dashboard(diag_sel, gender_sel, start_date, end_date, dark):
    t = get_theme(dark)
    df = patients.copy()
    if diag_sel:
        df = df[df['Diagnosis'].isin(diag_sel)]
    if gender_sel:
        df = df[df['Gender'].isin(gender_sel)]
    df = df[(df['AdmissionDate'] >= pd.to_datetime(start_date)) & (df['AdmissionDate'] <= pd.to_datetime(end_date))]
    # Animations: animate on data change
    transition = {'duration': 700, 'easing': 'cubic-in-out'}
    # --- Avg Cost ---
    avg_cost = df.groupby(['Diagnosis', 'Gender'])['Cost'].mean().reset_index()
    avg_cost_fig = px.bar(
        avg_cost, x='Diagnosis', y='Cost', color='Gender', barmode='group',
        labels={"Cost": "Avg Cost ($)"},
        color_discrete_sequence=t['theme_colors'],
    )
    avg_cost_fig.update_layout(
        plot_bgcolor=t['card_color'], paper_bgcolor=t['card_color'],
        font=dict(family=t['font_family'], size=15, color="#f5f5f5" if dark else "#263238"),
        showlegend=True, legend=dict(orientation="h", y=-0.2),
        margin=dict(l=24, r=24, t=28, b=12),
        xaxis=dict(title=None),
        yaxis=dict(gridcolor="#23272e" if dark else "#e0e7ef"),
        transition=transition
    )
    # Pie chart
    outcome_fig = px.pie(
        df, names='Outcome', hole=0.47,
        color_discrete_sequence=t['theme_colors'],
    )
    outcome_fig.update_traces(
        textinfo='percent+label',
        pull=[0.08 if o=="Deceased" else 0 for o in df['Outcome'].unique()],
        marker=dict(line=dict(color="#23272e" if dark else "#fff", width=2)),
    )
    outcome_fig.update_layout(
        plot_bgcolor=t['card_color'], paper_bgcolor=t['card_color'],
        font=dict(family=t['font_family'], size=15, color="#f5f5f5" if dark else "#263238"),
        margin=dict(l=24, r=24, t=24, b=12),
        showlegend=False,
        transition=transition
    )
    # Bubble Table
    summary = make_summary_table(df)
    summary_fig = px.scatter(
        summary, x="Diagnosis", y="AvgCost", size="Count", color="Outcome",
        color_discrete_sequence=t['theme_colors'], hover_data=["Count"],
    )
    summary_fig.update_layout(
        plot_bgcolor=t['card_color'], paper_bgcolor=t['card_color'],
        font=dict(family=t['font_family'], size=14, color="#f5f5f5" if dark else "#263238"),
        legend=dict(title="Outcome", orientation="h", y=-0.2),
        xaxis=dict(title=None),
        yaxis=dict(title="Avg Cost ($)", gridcolor="#23272e" if dark else "#e0e7ef"),
        margin=dict(l=12, r=16, t=16, b=18),
        transition=transition
    )
    # Trend line (Monthly avg)
    if len(df):
        df['Month'] = df['AdmissionDate'].dt.to_period("M").dt.to_timestamp()
        monthly = df.groupby("Month")["Cost"].mean().reset_index()
        trend_fig = px.line(
            monthly, x="Month", y="Cost",
            labels={"Cost": "Avg Cost ($)", "Month": "Month"},
            color_discrete_sequence=[t['accent_color']],
            markers=True
        )
        trend_fig.update_layout(
            plot_bgcolor=t['card_color'], paper_bgcolor=t['card_color'],
            font=dict(family=t['font_family'], size=15, color="#f5f5f5" if dark else "#263238"),
            margin=dict(l=22, r=22, t=28, b=12),
            yaxis=dict(gridcolor="#23272e" if dark else "#e0e7ef"),
            transition=transition
        )
    else:
        trend_fig = px.line(title="No data for current filters")
    # --- KPIs ---
    avg_cost_val = f"${df['Cost'].mean():,.0f}" if len(df) else "N/A"
    total = f"{len(df):,}" if len(df) else "0"
    recov = f"{100*df['Outcome'].value_counts(normalize=True).get('Recovered',0):.1f}" if len(df) else "0.0"
    readm = f"{100*df['Outcome'].value_counts(normalize=True).get('Readmitted',0):.1f}" if len(df) else "0.0"
    return avg_cost_fig, outcome_fig, summary_fig, trend_fig, avg_cost_val, recov, readm, total

@app.callback(
    Output("download-data", "data"),
    [Input("download-btn", "n_clicks")],
    [State("diag-dropdown", "value"),
     State("gender-dropdown", "value"),
     State("date-picker", "start_date"),
     State("date-picker", "end_date")]
)
def download_filtered_data(n, diag_sel, gender_sel, start_date, end_date):
    if not n:
        return dash.no_update
    df = patients.copy()
    if diag_sel:
        df = df[df['Diagnosis'].isin(diag_sel)]
    if gender_sel:
        df = df[df['Gender'].isin(gender_sel)]

    df = df[(df['AdmissionDate'] >= pd.to_datetime(start_date)) & (df['AdmissionDate'] <= pd.to_datetime(end_date))]
    output = BytesIO()
    df.to_excel(output, index=False)
    data = base64.b64encode(output.getvalue()).decode()
    return dict(content=data, filename="filtered_healthcare_data.xlsx", base64=True)


if __name__ == "__main__":
    app.run(debug=True)
