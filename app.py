"""Entry point for Oficina Pro."""

import sys
import os

# Ensure the project root is on sys.path so 'src.*' imports resolve correctly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import customtkinter as ctk

from src.mecanica.app import AppOficina

ctk.set_appearance_mode("Light")

if __name__ == "__main__":
    app = AppOficina()
    app.mainloop()
