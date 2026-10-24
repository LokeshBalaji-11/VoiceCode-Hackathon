from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()


class FibRequest(BaseModel):
    n: int


def fibonacci(n: int) -> int:
    """Return the n-th Fibonacci number (0-indexed).

    Args:
        n (int): Non‑negative index of the Fibonacci sequence.
    Returns:
        int: The Fibonacci number at position n.
    Raises:
        ValueError: If ``n`` is negative.
    """
    if n < 0:
        raise ValueError("n must be non-negative")
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a


@app.post("/fib")
def compute_fib(request: FibRequest):
    """FastAPI endpoint that computes the Fibonacci number for the given ``n``.

    Returns a JSON object with a success message, the input ``n`` and the computed ``value``.
    """
    try:
        result = fibonacci(request.n)
        return {"message": "success", "n": request.n, "value": result}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


# --- Agent Auto-Patch ---
"""
fib.py - Simple FastAPI service exposing Fibonacci sequence computation.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Fibonacci Service")

class FibRequest(BaseModel):
    n: int

def compute_fibonacci(n: int) -> list[int]:
    """
    Compute the Fibonacci sequence of length n.
    Returns a list containing the first n Fibonacci numbers.
    """
    if n < 0:
        raise ValueError("n must be non‑negative")
    if n == 0:
        return []
    if n == 1:
        return [0]
    seq = [0, 1]
    while len(seq) < n:
        seq.append(seq[-1] + seq[-2])
    return seq

@app.post("/fib")
def get_fibonacci(req: FibRequest):
    """
    FastAPI endpoint that returns the Fibonacci sequence up to the requested length.
    """
    try:
        sequence = compute_fibonacci(req.n)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"message": "success", "sequence": sequence}


# --- Agent Auto-Patch ---
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()


def fibonacci(n: int) -> list[int]:
    """Return a list of the first n Fibonacci numbers (n >= 0)."""
    if n < 0:
        raise ValueError("n must be non-negative")
    seq: list[int] = []
    a, b = 0, 1
    for _ in range(n):
        seq.append(a)
        a, b = b, a + b
    return seq


class FibRequest(BaseModel):
    n: int


@app.post("/fib")
def compute_fib(req: FibRequest):
    """Compute Fibonacci sequence for the provided n and return a success message."""
    try:
        sequence = fibonacci(req.n)
        return {"message": "success", "sequence": sequence}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
