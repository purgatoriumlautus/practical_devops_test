from flask import Flask,jsonify
import datetime
import os
import psycopg2

#configs
DB_HOST = os.environ["DB_HOST"]
DB_PORT = os.environ["DB_PORT"]
DB_NAME = os.environ["DB_NAME"]
##secrets
DB_USER = os.environ["DB_USER"]
DB_PASSWORD = os.environ["DB_PASSWORD"]
#




app = Flask(__name__)

@app.route("/health")
def get_health():
    return jsonify({"status":"ok"})

@app.route("/time")
def get_time():
    return jsonify({"time":str(datetime.datetime.now())})

@app.route("/db-check")
def check_db():
    try:
        conn = psycopg2.connect(database=DB_NAME,
                                user=DB_USER,
                                password=DB_PASSWORD,
                                host=DB_HOST,
                                port=DB_PORT)
        return jsonify({"db":"ok"})
    except Exception as e:
        print(e)
        return jsonify({"db":"error"})



if __name__ == "__main__":
    app.run(host="0.0.0.0",port=8000, debug=True)
