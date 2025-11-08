import requests
from collections import Counter

class ReplAnalyzer:
    def __init__(self):
        self.replit_api_base = "https://replit.com/api/v1/repls"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'ReplMatch/1.0',
            'Accept': 'application/json'
        })
    
    def analyze_user_repls(self, username):
        """
        Analyze a user's public Repls to determine coding patterns
        Note: This is a simplified version. In production, use Replit's official API
        """
        try:
            # First try the v1 API
            url = f"{self.replit_api_base}/@{username}"
            response = self.session.get(url)
            
            # If v1 API fails, try the data API
            if response.status_code == 404:
                url = f"https://replit.com/data/profiles/@{username}/repls"
                response = self.session.get(url)
            
            response.raise_for_status()
            repls_data = response.json()
            
            languages = []
            project_types = []
            coding_patterns = []
            
            if isinstance(repls_data, list):
                for repl in repls_data:
                    if isinstance(repl, dict):
                        if 'language' in repl:
                            languages.append(repl['language'])
                        if 'project_type' in repl:
                            project_types.append(repl['project_type'])
            
            analysis = {
                'languages': list(set(languages)) if languages else ['Python'],  # Default to Python if no data
                'project_types': list(set(project_types)) if project_types else ['web'],  # Default to web if no data
                'coding_patterns': coding_patterns,
                'activity_level': 'active' if languages else 'new'  # Mark as new user if no repls found
            }
            
            return analysis
            
        except requests.exceptions.RequestException as e:
            print(f"Info: Could not fetch Replit data for user {username}: {str(e)}")
            # Return default values instead of empty lists
            return {
                'languages': ['Python'],  # Default to Python
                'project_types': ['web'],  # Default to web development
                'coding_patterns': [],
                'activity_level': 'new'  # Mark as new user
            }
    
    def analyze_repository(self, repo_url):
        """Analyze a GitHub or Replit repository"""
        # Simulated repository analysis
        analysis = {
            'languages': ['Python', 'JavaScript'],
            'frameworks': ['Flask', 'React'],
            'complexity': 'medium',
            'project_type': 'web-app'
        }
        
        return analysis
