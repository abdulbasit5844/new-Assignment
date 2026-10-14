"""Lab-06: Linear regression prediction REST API.

Student: Abdul Basit
Registration number: FA22-BAI-001
"""
import math
import random

from flask import Flask, jsonify, request

REGISTRATION_NUMBER = "FA22-BAI-001"
SEED = 22001  # numeric representation of FA22-BAI-001

# Coefficients are generated once at startup, in this exact order.
random.seed(SEED)
a1 = random.uniform(-5, 5)
a2 = random.uniform(-5, 5)
a3 = random.uniform(-5, 5)
b = random.uniform(-10, 10)

app = Flask(__name__)


def _parse_param(name):
    """Return (value, error) for a required finite float query parameter."""
    raw = request.args.get(name)
    if raw is None or raw.strip() == "":
        return None, f"missing required parameter '{name}'"
    try:
        value = float(raw)
    except ValueError:
        return None, f"parameter '{name}' must be a number, got '{raw}'"
    if not math.isfinite(value):
        return None, f"parameter '{name}' must be a finite number"
    return value, None


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


@app.route("/predict", methods=["GET"])
def predict():
    values = {}
    errors = []
    for name in ("x1", "x2", "x3"):
        value, error = _parse_param(name)
        if error:
            errors.append(error)
        else:
            values[name] = value

    if errors:
        return jsonify({
            "registration number": REGISTRATION_NUMBER,
            "error": "invalid input",
            "details": errors,
        }), 400

    y = a1 * values["x1"] + a2 * values["x2"] + a3 * values["x3"] + b
    return jsonify({
        "registration number": REGISTRATION_NUMBER,
        "prediction": round(y, 2),
    }), 200


if __name__ == "__main__":
    # Development server only; the container uses gunicorn.
    app.run(host="0.0.0.0", port=5000)
