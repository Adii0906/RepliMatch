import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class AIMatchmaker:
    def __init__(self):
        self.skill_weight = 0.4
        self.interest_weight = 0.3
        self.tech_stack_weight = 0.2
        self.coding_style_weight = 0.1
    
    def calculate_jaccard_similarity(self, set1, set2):
        """Calculate Jaccard similarity between two sets"""
        if not set1 or not set2:
            return 0.0
        
        set1 = set(set1)
        set2 = set(set2)
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0.0
    
    def calculate_text_similarity(self, text1, text2):
        """Calculate similarity between two text descriptions"""
        if not text1 or not text2:
            return 0.0
        
        vectorizer = TfidfVectorizer()
        try:
            tfidf_matrix = vectorizer.fit_transform([text1, text2])
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            return float(similarity)
        except Exception as e:
            print(f"Error calculating text similarity: {str(e)}")
            return 0.0
    
    def calculate_match_score(self, user1, user2):
        """Calculate overall match score between two users"""
        # Skills similarity
        skills_score = self.calculate_jaccard_similarity(
            user1.get('skills', []),
            user2.get('skills', [])
        )
        
        # Interests similarity
        interests_score = self.calculate_jaccard_similarity(
            user1.get('interests', []),
            user2.get('interests', [])
        )
        
        # Tech stack similarity
        tech_score = self.calculate_jaccard_similarity(
            user1.get('tech_stack', []),
            user2.get('tech_stack', [])
        )
        
        # Coding style similarity (based on bio or project descriptions)
        style_score = self.calculate_text_similarity(
            user1.get('bio', ''),
            user2.get('bio', '')
        )
        
        # Weighted total score
        total_score = (
            self.skill_weight * skills_score +
            self.interest_weight * interests_score +
            self.tech_stack_weight * tech_score +
            self.coding_style_weight * style_score
        )
        
        return total_score
    
    def find_matches(self, user_profile, all_users, top_n=10):
        """Find top N matches for a user"""
        matches = []
        
        for other_user in all_users:
            score = self.calculate_match_score(user_profile, other_user)
            matches.append({
                'user_id': other_user['id'],
                'username': other_user['username'],
                'score': score,
                'skills': other_user.get('skills', []),
                'interests': other_user.get('interests', []),
                'tech_stack': other_user.get('tech_stack', []),
                'bio': other_user.get('bio', '')
            })
        
        # Sort by score descending
        matches.sort(key=lambda x: x['score'], reverse=True)
        
        return matches[:top_n]
