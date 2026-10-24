app = FastAPI()

@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok"}

@app.get("/health")
def health_check():
    """Basic health check endpoint."""
    return {"status": "ok"}

# --- Agent Auto-Patch ---
from fastapi import FastAPI

app = FastAPI()


@app.get("/health")
async def health_check():
    """
    Basic health check endpoint.
    Returns a JSON response indicating service health.
    """
    return {"status": "ok"}


# --- Agent Auto-Patch ---
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

app = FastAPI()


class Student(BaseModel):
    name: str
    gpa: float
    major: str


class Sponsor(BaseModel):
    company_name: str
    min_gpa: float
    target_majors: List[str]


class SponsorMatchRequest(BaseModel):
    student: Student
    sponsors: List[Sponsor]


@app.post("/api/sponsor-match")
def sponsor_match(request: SponsorMatchRequest):
    """Match a student with suitable sponsors based on GPA and major.

    Returns a list of sponsors that satisfy:
    - student.gpa >= sponsor.min_gpa
    - student.major is one of sponsor.target_majors
    """
    student = request.student
    matching = [
        sponsor for sponsor in request.sponsors
        if student.gpa >= sponsor.min_gpa and student.major in sponsor.target_majors
    ]
    return {"matching_sponsors": [s.dict() for s in matching]}


# --- Agent Auto-Patch ---
from flask import Flask, jsonify, request
from pydantic import BaseModel
from werkzeug.exceptions import BadRequest


class Student(BaseModel):
    """Student model for sponsor matching."""
    name: str
    gpa: float
    major: str


class Sponsor(BaseModel):
    """Sponsor model for sponsor matching."""
    company_name: str
    min_gpa: float
    target_majors: list[str]


class SponsorMatchRequest(BaseModel):
    """Payload containing a student and a list of sponsors."""
    student: Student
    sponsors: list[Sponsor]

app = Flask(__name__)


@app.route("/api/sponsor-match", methods=["POST"])
def sponsor_match():
    """Matches a student with suitable sponsors based on GPA and major.

    Expects a JSON payload matching SponsorMatchRequest schema.
    Returns a list of matching sponsors.
    """
    data = request.get_json(silent=True) or {}
    try:
        payload = SponsorMatchRequest(**data)
    except Exception as exc:
        raise BadRequest(str(exc))
    student = payload.student
    matching = [
        sponsor for sponsor in payload.sponsors
        if sponsor.min_gpa <= student.gpa and student.major in sponsor.target_majors
    ]
    return jsonify({"matching_sponsors": [s.dict() for s in matching]}), 200


if __name__ == "__main__":
    app.run(debug=True)


# --- Agent Auto-Patch ---
from flask import Flask, jsonify, request
from pydantic import BaseModel
from werkzeug.exceptions import BadRequest

app = Flask(__name__)


class Student(BaseModel):
    """Student model for sponsor matching."""
    name: str
    gpa: float
    major: str


class Sponsor(BaseModel):
    """Sponsor model for sponsor matching."""
    company_name: str
    min_gpa: float
    target_majors: list[str]


class SponsorMatchRequest(BaseModel):
    """Payload containing a student and a list of sponsors."""
    student: Student
    sponsors: list[Sponsor]


@app.route("/api/sponsor-match", methods=["POST"])
def sponsor_match():
    """Matches a student with suitable sponsors based on GPA and major.

    Expects a JSON payload matching SponsorMatchRequest schema.
    Returns a list of matching sponsors.
    """
    data = request.get_json(silent=True) or {}
    try:
        payload = SponsorMatchRequest(**data)
    except Exception as exc:
        raise BadRequest(str(exc))
    student = payload.student
    matching = [
        sponsor for sponsor in payload.sponsors
        if sponsor.min_gpa <= student.gpa and student.major in sponsor.target_majors
    ]
    return jsonify({"matching_sponsors": [s.dict() for s in matching]}), 200


# --- Agent Auto-Patch ---
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List


class Student(BaseModel):
    """Student model for sponsor matching."""
    name: str
    gpa: float
    major: str


class Sponsor(BaseModel):
    """Sponsor model for sponsor matching."""
    company_name: str
    min_gpa: float
    target_majors: List[str]


class SponsorMatchRequest(BaseModel):
    """Payload containing a student and a list of sponsors."""
    student: Student
    sponsors: List[Sponsor]

app = FastAPI()


@app.post("/api/sponsor-match")
def sponsor_match(request: SponsorMatchRequest):
    """Match a student with suitable sponsors based on GPA and major.

    Returns a JSON object with a list of matching sponsors under the key
    ``matching_sponsors``.
    """
    student = request.student
    matching = [
        sponsor for sponsor in request.sponsors
        if sponsor.min_gpa <= student.gpa and student.major in sponsor.target_majors
    ]
    return {"matching_sponsors": matching}
