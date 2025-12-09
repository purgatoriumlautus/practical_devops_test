from flask import Flask,jsonify
import datetime

app = Flask(__name__)

@app.route("/health")
def get_health():
    return jsonify({"status":"ok"})

@app.route("/time")
def get_time():
    return jsonify({"time":str(datetime.datetime.now())})


if __name__ == "__main__":
    app.run(host="0.0.0.0",port=8000, debug=True)
