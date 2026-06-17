from typing import List, Set
from loguru import logger


class RecommendationEngine:    
    @staticmethod
    def analyze_skill_gaps(required_skills: List[str], candidate_skills: List[str]) -> List[str]:
        if not required_skills:
            return []

        req_set: Set[str] = {skill.strip().lower() for skill in required_skills}
        cand_set: Set[str] = {skill.strip().lower() for skill in candidate_skills}

        missing_skills_lower = req_set - cand_set

        original_case_map = {skill.strip().lower(): skill.strip() for skill in required_skills}
        
        skill_gaps = [original_case_map[skill] for skill in missing_skills_lower]
        
        logger.debug(f"Analyzed skill gaps: found {len(skill_gaps)} missing out of {len(required_skills)} required.")
        return sorted(skill_gaps)