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
    """Applies known promo codes (SAVE10, SAVE20, SAVE50, VIP50) to a subtotal."""
    if not promo_code:
        return round(subtotal, 2)

    code = promo_code.strip().upper()
    
    if code == "VIP50":
        if subtotal < 200.0:
            raise ValueError("VIP50 requires a minimum subtotal of $200.")
        return round(subtotal * 0.50, 2)

    if code == "SAVE50":
        return round(subtotal * 0.50, 2)
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
        return jsonify({"error": str(exc)}), 400


# Pydantic models for sponsor matching
from pydantic import BaseModel, ValidationError
from typing import List

class Student(BaseModel):
    name: str
    gpa: float
    major: str

class Sponsor(BaseModel):
    company_name: str
    min_gpa: float
    target_majors: list[str]

class MatchRequest(BaseModel):
    student: Student
    sponsors: list[Sponsor]

@app.route("/api/sponsor-match", methods=["POST"])
def sponsor_match():
    """Matches a student with eligible sponsors based on GPA and major."""
    data = request.get_json(silent=True) or {}
    try:
        req = MatchRequest(**data)
    except ValidationError as e:
        return jsonify({"error": e.errors()}), 400

    eligible = [
        sponsor.model_dump()
        for sponsor in req.sponsors
        if req.student.gpa >= sponsor.min_gpa and req.student.major in sponsor.target_majors
    ]
    return jsonify(eligible), 200