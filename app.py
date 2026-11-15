"""Vercel FastAPI entrypoint for AETHERIS.

AETHERIS contains its API and frontend in the same ASGI application.
"""
from aetheris.server import app
