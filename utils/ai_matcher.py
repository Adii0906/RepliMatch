import os
import json
import google.generativeai as genai
from typing import List, Dict, Any

class AIMatchmaker:
    def __init__(self):
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            print("Warning: GEMINI_API_KEY not found, using fallback matching")
            self.model = None
        else:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-pro')
    
    def calculate_jaccard_similarity(self, set1, set2):
        """Calculate Jaccard similarity between two sets (fallback method)"""
        if not set1 or not set2:
            return 0.0
        
        set1 = set(set1)
        set2 = set(set2)
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0.0
    
    def calculate_match_score_fallback(self, user1, user2):
        """Fallback matching when Gemini API is not available"""
        skills_score = self.calculate_jaccard_similarity(
            user1.get('skills', []),
            user2.get('skills', [])
        )
        
        interests_score = self.calculate_jaccard_similarity(
            user1.get('interests', []),
            user2.get('interests', [])
        )
        
        tech_score = self.calculate_jaccard_similarity(
            user1.get('tech_stack', []),
            user2.get('tech_stack', [])
        )
        
        total_score = (0.4 * skills_score + 0.4 * interests_score + 0.2 * tech_score)
        return total_score
    
    def find_matches_with_gemini(self, user_profile: Dict, all_users: List[Dict], top_n: int = 10) -> List[Dict]:
        """Use Gemini AI to intelligently match users based on comprehensive analysis"""
        try:
            # Prepare user profile summary
            user_summary = f"""
            User Profile:
            - Skills: {', '.join(user_profile.get('skills', []))}
            - Interests: {', '.join(user_profile.get('interests', []))}
            - Bio: {user_profile.get('bio', 'N/A')}
            """
            
            # Prepare candidates summary
            candidates_summary = []
            for idx, candidate in enumerate(all_users):
                candidates_summary.append(f"""
                Candidate {idx}:
                - Username: {candidate.get('username', 'Unknown')}
                - Skills: {', '.join(candidate.get('skills', []))}
                - Interests: {', '.join(candidate.get('interests', []))}
                - Bio: {candidate.get('bio', 'N/A')}
                """)
            
            # Create prompt for Gemini
            prompt = f"""
            You are an expert matchmaking AI for developers. Your task is to analyze the user profile and rank the candidates based on compatibility for coding collaboration.
            
            Consider:
            1. Complementary skills (different but synergistic skills score higher)
            2. Shared interests and goals
            3. Similar experience levels and working styles
            4. Potential for learning from each other
            
            {user_summary}
            
            Candidates:
            {''.join(candidates_summary)}
            
            Return ONLY a JSON array of candidate indices (0 to {len(all_users)-1}) ranked from best to worst match, with a compatibility score (0-100) and brief reason for each.
            Format: [[index, score, "reason"], [index, score, "reason"], ...]
            
            Example: [[2, 95, "Complementary skills and shared interest in web development"], [0, 78, "Similar skill level, good for peer learning"]]
            """
            
            response = self.model.generate_content(prompt)
            
            # Parse the response
            result_text = response.text.strip()
            # Extract JSON from markdown code blocks if present
            if '```json' in result_text:
                result_text = result_text.split('```json')[1].split('```')[0].strip()
            elif '```' in result_text:
                result_text = result_text.split('```')[1].split('```')[0].strip()
            
            rankings = json.loads(result_text)
            
            # Build matched results
            matches = []
            for rank_item in rankings[:top_n]:
                idx, score, reason = rank_item
                if 0 <= idx < len(all_users):
                    candidate = all_users[idx]
                    matches.append({
                        'user_id': candidate['id'],
                        'username': candidate.get('username', 'Unknown'),
                        'score': score / 100.0,  # Normalize to 0-1
                        'skills': candidate.get('skills', []),
                        'interests': candidate.get('interests', []),
                        'tech_stack': candidate.get('tech_stack', []),
                        'bio': candidate.get('bio', ''),
                        'match_reason': reason,
                        'profile_photo': candidate.get('profile_photo', None)
                    })
            
            return matches
            
        except Exception as e:
            print(f"Error using Gemini AI for matching: {str(e)}")
            print("Falling back to traditional matching...")
            return None
    
    def find_matches(self, user_profile: Dict, all_users: List[Dict], top_n: int = 10) -> List[Dict]:
        """Find top N matches for a user using Gemini AI or fallback method"""
        # Try Gemini AI first
        if self.model:
            gemini_matches = self.find_matches_with_gemini(user_profile, all_users, top_n)
            if gemini_matches:
                return gemini_matches
        
        # Fallback to traditional matching
        print("Using fallback matching algorithm...")
        matches = []
        
        for other_user in all_users:
            score = self.calculate_match_score_fallback(user_profile, other_user)
            matches.append({
                'user_id': other_user['id'],
                'username': other_user.get('username', 'Unknown'),
                'score': score,
                'skills': other_user.get('skills', []),
                'interests': other_user.get('interests', []),
                'tech_stack': other_user.get('tech_stack', []),
                'bio': other_user.get('bio', ''),
                'match_reason': 'Matched based on skill and interest overlap',
                'profile_photo': other_user.get('profile_photo', None)
            })
        
        # Sort by score descending
        matches.sort(key=lambda x: x['score'], reverse=True)
        
        return matches[:top_n]
