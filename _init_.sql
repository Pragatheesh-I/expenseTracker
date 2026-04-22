-- 1. Enable the Vector extension (The AI Brain)
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Transactions Table
CREATE TABLE IF NOT EXISTS transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    date DATE NOT NULL,
    merchant TEXT NOT NULL,
    amount DECIMAL(12,2) NOT NULL,
    currency TEXT DEFAULT 'INR',
    category TEXT NOT NULL,
    embedding vector(768), -- For Gemini text-embedding-004
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Categories Table for consistent grouping
CREATE TABLE IF NOT EXISTS user_categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    category_name TEXT NOT NULL,
    embedding vector(768),
    UNIQUE(user_id, category_name)
);