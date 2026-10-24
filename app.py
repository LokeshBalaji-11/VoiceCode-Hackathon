from fastapi import FastAPI
from flask import Flask, jsonify, request
from pydantic import BaseModel, ValidationError
from werkzeug.exceptions import BadRequest
from statistics import mean, median

# --- App Initialization ---
fastapi_app = FastAPI()
app = Flask(__name__)

# --- Pydantic Models ---
class RegisterRequest(BaseModel):
    username: str
    age: int

# ... (keep all your routes below this exactly the same)

# --- App Initialization ---
fastapi_app = FastAPI()
app = Flask(__name__)

# --- Pydantic Models ---
class RegisterRequest(BaseModel):
    username: str
    age: int

# ... (keep all your routes below this exactly the same)

# --- Pydantic Models ---
class RegisterRequest(BaseModel):
    username: str
    age: int

# --- FastAPI Routes ---
@fastapi_app.get("/fastapi-health")
async def fastapi_health_check_v2():
    """FastAPI health check endpoint returning JSON status."""
    return {"status": "ok"}

@fastapi_app.get("/ping")
async def ping():
    """Basic health check endpoint."""
    return {"status": "ok"}

@fastapi_app.get("/healthz")
async def healthz():
    """FastAPI health check endpoint indicating service is healthy."""
    return {"status": "healthy"}

# --- Flask Routes ---
@app.route("/health", methods=["GET"])
def health_check():
    """Returns service health status."""
    return jsonify({"status": "ok"}), 200

@app.route("/register", methods=["POST"])
def register():
    """Registers a new user with age validation."""
    data = request.get_json(silent=True) or {}
    try:
        payload = RegisterRequest(**data)
    except ValidationError as e:
        return jsonify({"error": e.errors()}), 400
        
    if payload.age < 18:
        return jsonify({"error": "User must be at least 18 years old."}), 400
        
    return jsonify({"message": f"User {payload.username} registered successfully."}), 200

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

@app.route("/stats", methods=["GET"]) 
def stats():
    """Computes statistics (mean, median, max) for a list of integers provided via the 'numbers' query parameter."""
    numbers_str = request.args.get("numbers", "")
    if not numbers_str:
        raise BadRequest("Query parameter 'numbers' is required.")
    try:
        numbers = [int(x) for x in numbers_str.split(",") if x.strip() != ""]
    except ValueError:
        raise BadRequest("All values in 'numbers' must be integers.")
    if not numbers:
        raise BadRequest("No valid numbers provided.")
    result = {
        "mean": mean(numbers),
        "median": median(numbers),
        "max": max(numbers)
    }
    return jsonify(result), 200