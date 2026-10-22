"""
Pytest configuration for the test suite.

Puts src/ on sys.path so the test modules can `from db_config import ...`
the same way app.py does, without each file needing its own shim.
"""
import os
import sys

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src')
if SRC not in sys.path:
    sys.path.insert(0, SRC)
