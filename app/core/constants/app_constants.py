"""
Application constants for the Resume Mining System.
"""

# File processing constants
ALLOWED_EXTENSIONS = {".pdf", ".docx"}
MAX_FILE_SIZE_MB = 10
CHUNK_SIZE = 512

# Matching & AI constants
DEFAULT_TOP_K = 5
SIMILARITY_THRESHOLD = 0.65

# Embedding dimension (depends on sentence-transformers/all-MiniLM-L6-v2)
EMBEDDING_DIMENSION = 384