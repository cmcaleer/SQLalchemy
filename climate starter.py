# imports
from flask import Flask
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func, inspect
import datetime as dt
import json
import pandas as pd

# initialize sqlalchemy engine and references
engine = create_engine("sqlite:///Resources/hawaii.sqlite")
Base = automap_base()
Base.prepare(engine, reflect=True)
Measurement = Base.classes.measurement
Station = Base.classes.station

# fetch and calculate one year prior to last date in measurement table
session = Session(engine)
last_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first()
last_date_ints = [int(s) for s in last_date[0].split('-')]
year_ago = dt.date(*last_date_ints) - dt.timedelta(days=364)

# Use Flask to create an app instance.
app = Flask(__name__)


# / Homepage: List all routes that are available.
@app.route("/")
def home():  # returns a series of clickable links to the valid urls in this api
    return (
        """
        <div>
         <h2>Valid Routes:</h2>
         <a href="/api/v1.0/precipitation">/api/v1.0/precipitation</a><br/>
         <a href="/api/v1.0/stations">/api/v1.0/stations</a><br/>
         <a href="/api/v1.0/tobs">/api/v1.0/tobs</a><br/>
         <a href="/api/v1.0/2012-02-28/">/api/v1.0/&lt;start&gt;</a><br/>
         <a href="/api/v1.0/2012-02-28/2012-03-05">/api/v1.0/&lt;start>/&lt;end&gt;</a><br/>
        </div>
        """
    )


@app.route("/api/v1.0/precipitation")
def precipitation():
    precipitation_session = Session(engine)  # start new engine session
    results = precipitation_session.query(Measurement.date, Measurement.prcp.label("Precipitation")).filter \
        (Measurement.date >= year_ago).order_by(Measurement.date).all()  # run query
    df = pd.DataFrame(results)  # convert results to pandas dataframe
    df.set_index('date', inplace=True)  # order by date
    return df.to_json(orient='values')  # return json values


@app.route("/api/v1.0/stations")
def stations():
    stations_session = Session(engine)  # start new engine session
    station_results = stations_session.query(Measurement.station).group_by(Measurement.station).all()  # run query
    df = pd.DataFrame(station_results)  # convert results to pandas dataframe
    return df.to_json()  # return json


@app.route("/api/v1.0/tobs")
def temp_obs():
    temp_obs_session = Session(engine)  # start new engine session
    tobs_results = temp_obs_session.query(Measurement.date, Measurement.tobs.label("Observed Temperature")).filter \
        (Measurement.date >= year_ago).order_by(Measurement.date).all()  # run query
    df = pd.DataFrame(tobs_results)  # convert results to pandas dataframe
    return df.to_json()  # return json


# add duplicate routes to account for the user possibly not adding a terminal slash in the url
# define default value for url parameter if it is not user-defined
@app.route("/api/v1.0/<start>", defaults={'end': None})
@app.route("/api/v1.0/<start>/", defaults={'end': None})
@app.route("/api/v1.0/<start>/<end>")
@app.route("/api/v1.0/<start>/<end>/")
def calc_temps(start, end):
    calc_temps_session = Session(engine)
    if end:
        temp_results = calc_temps_session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs),
                                                func.max(Measurement.tobs)).filter(Measurement.date >= start). \
            filter(Measurement.date <= end).all()
    else:
        temp_results = calc_temps_session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs),
                                                func.max(Measurement.tobs)).filter(Measurement.date >= start).all()

    output_dict = {'TMIN': temp_results[0][0], 'TAVG': temp_results[0][1], 'TMAX': temp_results[0][2]}
    return json.dumps(output_dict)


if __name__ == "__main__":  # run app
    app.debug = True
    app.run(host='0.0.0.0', port=5001)