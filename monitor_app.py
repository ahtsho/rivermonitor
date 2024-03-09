import pandas as pd
import plotly.utils
from flask import Flask, render_template_string, make_response, render_template
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta
# import plotly.graph_objs as go
import plotly.express as px

import json

app = Flask(__name__)


@app.route("/hello")
def hi():
    return "I'm fine thanks!"


class HydroMeasure:
    def __init__(self, id, date, level):
        self.id = id
        self.date = date
        self.level = level


hydro_measure_list: [HydroMeasure] = []
last_update = datetime.now() - timedelta(minutes=15)


@app.route("/")
def home():
    global last_update, hydro_measure_list
    now = datetime.now()
    if last_update < now - timedelta(minutes=10):
        hydro_measure_list = extract_data_from_source_site()
        last_update = datetime.now()

    if len(hydro_measure_list) > 0:
        df = pd.DataFrame([{'date': measure.date, 'level': measure.level} for measure in hydro_measure_list])
        fig = px.bar(df, x='date', y='level',
                     hover_data=['date', 'level'],
                     color='level',
                     color_continuous_scale='reds',
                     labels={'Livello (m)': 'Livello del fiume in metri'},
                     height=600,text_auto='.2s')
        fig.update_layout(title="Bisenzio a S.Piero a Pinti - Signa (FI)",
                          xaxis_title="Data di misurazione",
                          yaxis_title="Altezza idrometrica (m)")

        fig.update_traces(textfont_size=10, textangle=0, textposition="outside", cliponaxis=False)
        tickvals = df['date'][::3]  # Select every 2nd hour
        ticktext = tickvals.dt.strftime('%H:%M')  # Format the labels as desired

        fig.update_xaxes(
            tickvals=tickvals,
            ticktext=ticktext,
        )

        """
          fig.update_xaxes(
            tickmode='array',
            tickvals=df['date'],
            ticktext=df['date'].dt.strftime('%Y-%m-%d %H:%M'),  # Format date labels including hours and minutes
        )
        fig.update_xaxes(tickangle=90)
        fig.update_xaxes(
            tickvals=df['date'].dt.floor('D'),  # Date labels
            ticktext=df['date'].dt.strftime('%Y-%m-%d'),  # Format date labels
            tickangle=0,  # Do not rotate date labels
        )
        """
        return render_template("index.html", graph_json=json.loads(fig.to_json()))
    return "No data"


def extract_data_from_source_site():
    response = requests.get("https://www.cfr.toscana.it/monitoraggio/dettaglio.php?id=TOS01004791&title=&type=idro")
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    script_tag = soup.find("map").contents[1].text
    pattern = re.compile(r'VALUES\[\d+]\s+=\s+new\s+Array\((.*?)\);', re.DOTALL)
    arrays = pattern.findall(script_tag)
    data = []
    for array in arrays:
        array_elements = re.findall(r'"(.*?)"', array)
        data.append(HydroMeasure(int(array_elements[0]), datetime.strptime(array_elements[1], "%d/%m/%Y %H.%M"),
                                 float(array_elements[2])))
        print(array_elements)
    return data


if __name__ == "__main__":
    app.run(debug=True)
