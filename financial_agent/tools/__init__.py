"""Client-side tool implementations backing the specialist agents.

Every function here returns a JSON string (not a Python object) — that's the
content type Claude tool results expect, and it keeps output bounded and
predictable for the model to parse.
"""
