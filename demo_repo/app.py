"""
Demo Target Application for VoiceCode Autopilot.
A simple shopping cart calculator with discount codes.
"""
from flask import Flask, jsonify, request

app = Flask(__name__)


def calculate_subtotal(items: list[dict]) -> float:
    """Calculates the subtotal of items: [{'price': 10.0, 'qty': 2}]."""
    total = 0.0
    for item in items:
        price = float(item.get("price", 0.0))
        qty = int(item.get("qty", 1))
        if price < 0 or qty < 0:
            raise ValueError("Price and quantity must be non-negative.")
        total += price * qty
    return round(total, 2)


def apply_discount(subtotal: float, promo_code: str | None = None) -> float:
    """Applies known promo codes (SAVE10, SAVE20, SAVE50) to a subtotal."""
    if promo_code and promo_code.strip().upper() == "SAVE50":
        return round(subtotal * 0.50, 2)
    if not promo_code:
        return round(subtotal, 2)

    code = promo_code.strip().upper()
    if code == "SAVE10":
        return round(subtotal * 0.90, 2)
    if code == "SAVE20":
        return round(subtotal * 0.80, 2)

    return round(subtotal, 2)


@app.route("/health", methods=["GET"])
def health_check():
    """Returns service health status."""
    return jsonify({"status": "ok", "service": "demo-checkout-api"}), 200


@app.route("/checkout", methods=["POST"])
def checkout():
    """Calculates final total for a cart payload."""
    data = request.get_json(silent=True) or {}
    items = data.get("items", [])
    promo_code = data.get("promo_code")

    try:
        subtotal = calculate_subtotal(items)
        final_total = apply_discount(subtotal, promo_code)
        return jsonify({
            "subtotal": subtotal,
            "promo_code": promo_code,
            "final_total": final_total,
        }), 200
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 