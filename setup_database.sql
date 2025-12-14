-- PostgreSQL + pgvector setup script for Face Recognition System
-- Run this script to create the database

-- Create the database (run as postgres superuser)
CREATE DATABASE face_recognition;

-- Connect to the database
\c face_recognition

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify pgvector is installed
SELECT * FROM pg_extension WHERE extname = 'vector';

-- The tables will be automatically created by SQLAlchemy when the application runs
-- But you can verify the connection with:
SELECT version();
