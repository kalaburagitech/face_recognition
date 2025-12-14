#!/bin/bash

echo "=========================================="
echo "Face Recognition System - PostgreSQL Setup"
echo "=========================================="
echo ""

# Step 1: Install Python dependencies
echo "Step 1: Installing Python dependencies..."
pip install psycopg2-binary>=2.9.9 pgvector>=0.2.4

echo ""
echo "Step 2: Setting up PostgreSQL database..."
echo "Please ensure PostgreSQL is running."
echo ""

# Create database
echo "Creating database 'face_recognition'..."
sudo -u postgres psql -c "CREATE DATABASE face_recognition;" 2>/dev/null || echo "Database may already exist"

# Enable pgvector extension
echo "Enabling pgvector extension..."
sudo -u postgres psql -d face_recognition -c "CREATE EXTENSION IF NOT EXISTS vector;"

echo ""
echo "Step 3: Verifying setup..."
sudo -u postgres psql -d face_recognition -c "SELECT extname, extversion FROM pg_extension WHERE extname='vector';"

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Configuration in config.json:"
echo "  Database URL: postgresql://postgres:postgres@localhost:5432/face_recognition"
echo ""
echo "IMPORTANT: Update the database password in config.json if needed!"
echo ""
echo "Next steps:"
echo "  1. Update config.json with your PostgreSQL credentials"
echo "  2. Run: python main.py"
echo "  3. The tables will be created automatically on first run"
echo ""
