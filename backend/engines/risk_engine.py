"""
Risk Engine - Re-export from risk_management.py
================================================

This module provides backward compatibility by re-exporting
the risk_engine instance from risk_management.py.
"""

from .risk_management import risk_engine

__all__ = ['risk_engine']
