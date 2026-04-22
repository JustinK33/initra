import os

from flask import Flask, jsonify

app = Flask(__name__)


@app.get("/")
def health():
    return jsonify(status="ok", project="{{project_name}}")


if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG") == "1")
