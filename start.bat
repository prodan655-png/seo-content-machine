@echo off
set PYTHONIOENCODING=utf-8
chcp 65001 > nul
python -m streamlit run app.py
