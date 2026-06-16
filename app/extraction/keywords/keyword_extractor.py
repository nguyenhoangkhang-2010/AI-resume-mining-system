import re
from typing import List
from collections import Counter
from loguru import logger


class KeywordExtractor:
    STOPWORDS = {
        "and", "the", "with", "from", "that", "this", "have", "been", "were", 
        "what", "which", "their", "about", "would", "these", "other", "into",
        "has", "more", "her", "two", "like", "him", "see", "could", "no", "make"
    }
    
    @staticmethod
    def extract(text: str, top_n: int = 15) -> List[str]:
        if not text:
            return []
            
        logger.debug("Starting keyword extraction.")
        
        words = re.findall(r'\b[a-z]{3,}\b', text.lower())
        
        filtered_words = [w for w in words if w not in KeywordExtractor.STOPWORDS]
        
        word_counts = Counter(filtered_words)
        
        top_keywords = [word for word, count in word_counts.most_common(top_n)]
        
        logger.debug(f"Extracted top {len(top_keywords)} keywords.")
        return top_keywords