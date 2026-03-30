import re
from typing import Dict, List, Optional, Tuple
from fuzzywuzzy import fuzz
from app.agent.config import AGENT_CONFIG


class IntentDetector:
    """Detect user intent from spoken or typed input."""
    
    def __init__(self):
        self.config = AGENT_CONFIG["intents"]
        self.faq_keywords = self._extract_faq_keywords()
        
    def _extract_faq_keywords(self) -> Dict[str, List[str]]:
        """Extract keywords from FAQ entries."""
        keywords = {}
        for i, faq in enumerate(AGENT_CONFIG["faq"]):
            keywords[f"faq_{i}"] = faq.get("keywords", [])
        return keywords
    
    def detect_intent(self, user_input: str) -> Tuple[str, float]:
        """
        Detect the intent from user input.
        Returns (intent_type, confidence_score)
        """
        if not user_input:
            return ("unknown", 0.0)
            
        user_input_lower = user_input.lower()
        
        # Check for emergency keywords first (highest priority)
        emergency_keywords = self.config["emergency"]["keywords"]
        for keyword in emergency_keywords:
            if keyword.lower() in user_input_lower:
                return ("emergency", 1.0)
        
        # Check for appointment booking keywords
        appointment_keywords = self.config["book_appointment"]["keywords"]
        for keyword in appointment_keywords:
            if keyword.lower() in user_input_lower:
                return ("book_appointment", 0.9)
        
        # Check for FAQ keywords
        for faq_key, keywords in self.faq_keywords.items():
            for keyword in keywords:
                if keyword.lower() in user_input_lower:
                    return ("faq", 0.8)
        
        # Fuzzy matching for better intent detection
        best_match = self._fuzzy_intent_match(user_input_lower)
        if best_match:
            return best_match
            
        return ("unknown", 0.0)
    
    def _fuzzy_intent_match(self, user_input: str) -> Optional[Tuple[str, float]]:
        """Use fuzzy matching to find best intent."""
        all_intents = []
        
        # Add appointment intent phrases
        for keyword in self.config["book_appointment"]["keywords"]:
            score = fuzz.partial_ratio(user_input, keyword.lower())
            if score > 75:
                all_intents.append(("book_appointment", score / 100))
        
        # Add FAQ intent phrases
        for faq in AGENT_CONFIG["faq"]:
            question = faq["question"].lower()
            score = fuzz.partial_ratio(user_input, question)
            if score > 80:
                all_intents.append(("faq", score / 100))
        
        if all_intents:
            return max(all_intents, key=lambda x: x[1])
        return None
    
    def match_faq(self, user_input: str) -> Optional[Dict]:
        """Find the best matching FAQ answer."""
        if not user_input:
            return None
            
        user_input_lower = user_input.lower()
        best_match = None
        best_score = 0
        
        for faq in AGENT_CONFIG["faq"]:
            # Check keywords first
            keywords = faq.get("keywords", [])
            for keyword in keywords:
                if keyword.lower() in user_input_lower:
                    return faq
            
            # Fuzzy match on question
            score = fuzz.partial_ratio(user_input_lower, faq["question"].lower())
            if score > best_score and score > 70:
                best_score = score
                best_match = faq
        
        return best_match
    
    def is_confirmation(self, user_input: str) -> bool:
        """Check if user input is a confirmation."""
        if not user_input:
            return False
        confirmation_words = ["yes", "yeah", "sure", "confirm", "book it", "okay", "ok", "that's right", "correct", "please do"]
        return any(word in user_input.lower() for word in confirmation_words)
    
    def is_rejection(self, user_input: str) -> bool:
        """Check if user input is a rejection."""
        if not user_input:
            return False
        rejection_words = ["no", "nope", "not", "cancel", "don't", "stop", "wrong", "incorrect"]
        return any(word in user_input.lower() for word in rejection_words)
    
    def is_goodbye(self, user_input: str) -> bool:
        """Check if user input indicates end of conversation."""
        if not user_input:
            return False
        goodbye_words = ["bye", "goodbye", "hang up", "that's all", "nothing else", "end call", "see you"]
        return any(word in user_input.lower() for word in goodbye_words)


intent_detector = IntentDetector()
