#!/bin/bash

echo "========================================"
echo "EMONGDEEPFACEWEB - METRICS GENERATOR"
echo "========================================"
echo "Installing dependencies and running metrics..."
echo

# Install Python dependencies
echo "Installing Python dependencies..."
pip install matplotlib seaborn pandas numpy opencv-python

# Run the final metrics generator
echo
echo "Running metrics generator..."
python FINAL_RUN.py

echo
echo "========================================"
echo "METRICS GENERATION COMPLETED!"
echo "========================================"
echo "Check 'COMPETITION_READY' folder for all files"
echo
