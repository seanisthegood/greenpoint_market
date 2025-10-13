from flask import Flask, jsonify, request

app = Flask(__name__)

# temporary in-memory markets
markets = [
    {"id": 1, "question": "Will the G train run on time this weekend?", "yes": 50.0, "no": 50.0},
    {"id": 2, "question": "Will it rain at McCarren Park on Sunday?", "yes": 50.0, "no": 50.0},
]

@app.route("/api/markets")
def get_markets():
    return jsonify(markets)

@app.route("/api/trade", methods=["POST"])
def trade():
    data = request.get_json()
    m = next((m for m in markets if m["id"] == data["market_id"]), None)
    if not m:
        return jsonify({"error": "Market not found"}), 404

    side = data.get("side")
    amount = float(data.get("amount", 0))
    if side not in ("yes", "no"):
        return jsonify({"error": "side must be 'yes' or 'no'"}), 400

    m[side] += amount
    total = m["yes"] + m["no"]
    m["yes_price"] = round(m["yes"] / total, 2)
    m["no_price"] = round(m["no"] / total, 2)
    return jsonify(m)

if __name__ == "__main__":
    app.run(debug=True)
