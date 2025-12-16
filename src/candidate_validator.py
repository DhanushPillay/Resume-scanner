import requests
import datetime
import re
from difflib import SequenceMatcher


class CandidateValidator:
    def __init__(self, github_token=None):
        self.github_token = github_token
        self.headers = {"Authorization": f"token {github_token}"} if github_token else {}

    def verify_github(self, github_url, claimed_skills=None):
        """
        Deep GitHub verification with repo-level analysis:
        - User validity
        - Account age
        - Activity metrics
        - DEEP REPO SCAN: Check each repo for languages and match against resume skills
        """
        if not github_url:
            return {"valid": False, "error": "No GitHub URL provided", "status": "missing"}

        # Extract username from URL
        username = github_url.rstrip('/').split('/')[-1]
        username = username.split('?')[0]
        
        if not username or username in ['github.com', '']:
            return {"valid": False, "error": "Invalid GitHub URL format", "status": "invalid_url"}

        api_url = f"https://api.github.com/users/{username}"
        
        try:
            response = requests.get(api_url, headers=self.headers, timeout=10)
            
            if response.status_code == 404:
                return {
                    "valid": False, 
                    "error": f"GitHub user '{username}' not found",
                    "status": "not_found",
                    "username": username
                }
            
            if response.status_code == 403:
                return {
                    "valid": False,
                    "error": "GitHub API rate limit exceeded",
                    "status": "rate_limited",
                    "username": username
                }
            
            if response.status_code != 200:
                return {
                    "valid": False,
                    "error": f"GitHub API error: {response.status_code}",
                    "status": "api_error",
                    "username": username
                }
            
            user_data = response.json()
            
            # Calculate account age
            created_at = user_data.get("created_at")
            account_age_days = 0
            if created_at:
                created_date = datetime.datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ")
                account_age_days = (datetime.datetime.utcnow() - created_date).days
            
            # ============ DEEP REPO ANALYSIS ============
            repos_url = user_data.get("repos_url")
            repos_analysis = []
            languages = {}
            total_commits = 0
            recent_activity = []
            all_repo_languages = []
            
            if repos_url:
                # Get all repos (up to 100)
                repos_response = requests.get(
                    repos_url + "?sort=updated&per_page=100", 
                    headers=self.headers, 
                    timeout=15
                )
                
                if repos_response.status_code == 200:
                    repos = repos_response.json()
                    
                    for repo in repos[:30]:  # Analyze top 30 repos
                        repo_info = {
                            "name": repo.get("name"),
                            "description": repo.get("description", ""),
                            "language": repo.get("language"),
                            "stars": repo.get("stargazers_count", 0),
                            "forks": repo.get("forks_count", 0),
                            "created_at": repo.get("created_at"),
                            "updated_at": repo.get("updated_at"),
                            "is_fork": repo.get("fork", False),
                            "size": repo.get("size", 0)
                        }
                        
                        # Count languages
                        lang = repo.get("language")
                        if lang:
                            languages[lang] = languages.get(lang, 0) + 1
                            all_repo_languages.append(lang.lower())
                        
                        # Get detailed language breakdown for each repo
                        if repo.get("languages_url"):
                            try:
                                lang_response = requests.get(
                                    repo["languages_url"], 
                                    headers=self.headers, 
                                    timeout=5
                                )
                                if lang_response.status_code == 200:
                                    repo_languages = lang_response.json()
                                    repo_info["languages_breakdown"] = repo_languages
                                    # Add all languages to tracking
                                    for l in repo_languages.keys():
                                        all_repo_languages.append(l.lower())
                            except:
                                pass
                        
                        repos_analysis.append(repo_info)
                        
                        # Check recent activity
                        updated_at = repo.get("updated_at")
                        if updated_at:
                            updated_date = datetime.datetime.strptime(updated_at, "%Y-%m-%dT%H:%M:%SZ")
                            days_ago = (datetime.datetime.utcnow() - updated_date).days
                            if days_ago < 180:
                                recent_activity.append({
                                    "name": repo.get("name"),
                                    "language": lang,
                                    "days_ago": days_ago
                                })
            
            # Sort languages by usage
            top_languages = sorted(languages.items(), key=lambda x: x[1], reverse=True)
            top_languages_list = [l[0] for l in top_languages]
            
            # ============ SKILL MATCHING ============
            skill_matches = []
            skill_mismatches = []
            unique_repo_languages = list(set(all_repo_languages))
            
            if claimed_skills:
                claimed_skills_lower = [s.lower() for s in claimed_skills]
                
                # Language/Framework mappings
                skill_to_language = {
                    "react": ["javascript", "typescript", "jsx"],
                    "react.js": ["javascript", "typescript"],
                    "node.js": ["javascript", "typescript"],
                    "nodejs": ["javascript", "typescript"],
                    "vue": ["javascript", "vue", "typescript"],
                    "angular": ["typescript", "javascript"],
                    "django": ["python"],
                    "flask": ["python"],
                    "fastapi": ["python"],
                    "spring": ["java", "kotlin"],
                    "spring boot": ["java", "kotlin"],
                    "rails": ["ruby"],
                    "ruby on rails": ["ruby"],
                    "express": ["javascript", "typescript"],
                    "next.js": ["javascript", "typescript"],
                    "tensorflow": ["python", "jupyter notebook"],
                    "pytorch": ["python", "jupyter notebook"],
                    "pandas": ["python", "jupyter notebook"],
                    "numpy": ["python"],
                    "machine learning": ["python", "jupyter notebook", "r"],
                    "data science": ["python", "jupyter notebook", "r"],
                }
                
                for skill in claimed_skills_lower:
                    # Direct language match
                    if skill in unique_repo_languages:
                        skill_matches.append({
                            "skill": skill.title(),
                            "found": True,
                            "evidence": f"Found {languages.get(skill.title(), 0)} repos with {skill.title()}"
                        })
                    # Framework/tool match
                    elif skill in skill_to_language:
                        expected_langs = skill_to_language[skill]
                        found_any = any(lang in unique_repo_languages for lang in expected_langs)
                        if found_any:
                            skill_matches.append({
                                "skill": skill.title(),
                                "found": True,
                                "evidence": f"Found related language ({', '.join(expected_langs)})"
                            })
                        else:
                            skill_mismatches.append({
                                "skill": skill.title(),
                                "found": False,
                                "message": f"Claims '{skill.title()}' but no {'/'.join(expected_langs)} repos found"
                            })
                    # Check if it's a programming language claim
                    elif skill in ['python', 'java', 'javascript', 'typescript', 'go', 'rust', 
                                   'c++', 'c#', 'ruby', 'php', 'swift', 'kotlin', 'scala']:
                        if skill not in unique_repo_languages:
                            skill_mismatches.append({
                                "skill": skill.title(),
                                "found": False,
                                "message": f"Claims '{skill.title()}' expertise but no repos with this language"
                            })

            # ============ HYPER-INFLATION FLAGS ============
            hyper_inflation_flags = []
            
            if account_age_days < 30:
                hyper_inflation_flags.append({
                    "type": "VERY_NEW_ACCOUNT",
                    "severity": "HIGH",
                    "message": f"Account created only {account_age_days} days ago"
                })
            elif account_age_days < 180:
                hyper_inflation_flags.append({
                    "type": "NEW_ACCOUNT",
                    "severity": "MEDIUM",
                    "message": f"Account is only {round(account_age_days/30, 1)} months old"
                })
            
            if user_data.get("public_repos", 0) == 0:
                hyper_inflation_flags.append({
                    "type": "ZERO_REPOS",
                    "severity": "HIGH",
                    "message": "Account has zero public repositories"
                })
            elif user_data.get("public_repos", 0) < 3:
                hyper_inflation_flags.append({
                    "type": "LOW_REPOS",
                    "severity": "MEDIUM",
                    "message": f"Only {user_data.get('public_repos')} public repositories"
                })
            
            # Check for mostly forked repos
            fork_count = sum(1 for r in repos_analysis if r.get('is_fork'))
            original_count = len(repos_analysis) - fork_count
            if len(repos_analysis) > 5 and fork_count > original_count:
                hyper_inflation_flags.append({
                    "type": "MOSTLY_FORKS",
                    "severity": "MEDIUM",
                    "message": f"{fork_count}/{len(repos_analysis)} repos are forks, not original work"
                })
            
            if not recent_activity:
                hyper_inflation_flags.append({
                    "type": "NO_RECENT_ACTIVITY",
                    "severity": "MEDIUM",
                    "message": "No repository activity in the last 6 months"
                })

            return {
                "valid": True,
                "status": "verified",
                "username": username,
                "profile_url": f"https://github.com/{username}",
                "name": user_data.get("name"),
                "bio": user_data.get("bio"),
                "created_at": created_at,
                "account_age_days": account_age_days,
                "account_age_months": round(account_age_days / 30, 1),
                "public_repos": user_data.get("public_repos", 0),
                "followers": user_data.get("followers", 0),
                "following": user_data.get("following", 0),
                "top_languages": top_languages_list,
                "language_breakdown": dict(top_languages[:10]),
                "all_languages_found": unique_repo_languages,
                "repos_analyzed": len(repos_analysis),
                "repos_details": repos_analysis[:10],  # Top 10 repos with details
                "original_repos": original_count,
                "forked_repos": fork_count,
                "recent_activity_count": len(recent_activity),
                "skill_matches": skill_matches,
                "skill_mismatches": skill_mismatches,
                "hyper_inflation_flags": hyper_inflation_flags
            }

        except requests.exceptions.Timeout:
            return {"valid": False, "error": "Request timeout", "status": "timeout", "username": username}
        except Exception as e:
            return {"valid": False, "error": str(e), "status": "error", "username": username}

    def verify_linkedin(self, linkedin_url, candidate_name):
        """LinkedIn verification with name matching."""
        if not linkedin_url:
            return {"valid": False, "error": "No LinkedIn URL provided", "status": "missing"}
        
        if "linkedin.com/in/" not in linkedin_url.lower():
            return {
                "valid": False,
                "error": "Invalid LinkedIn profile URL format",
                "status": "invalid_format",
                "url": linkedin_url
            }
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(linkedin_url, timeout=10, headers=headers, allow_redirects=True)
            
            status_code = response.status_code
            
            if status_code == 404:
                return {
                    "valid": False,
                    "status": "not_found",
                    "error": "LinkedIn profile not found (404)",
                    "url": linkedin_url
                }
            
            url_accessible = status_code in [200, 999]
            
            # Name matching
            slug = linkedin_url.rstrip('/').split('/')[-1]
            slug_clean = re.sub(r'-[a-f0-9]{5,}$', '', slug.lower())
            
            name_parts = candidate_name.lower().split() if candidate_name else []
            slug_parts = slug_clean.split('-')
            
            matches_found = 0
            for part in name_parts:
                if len(part) > 2:
                    for slug_part in slug_parts:
                        if part in slug_part or slug_part in part:
                            matches_found += 1
                            break
            
            match_score = matches_found / len(name_parts) if name_parts else 0
            slug_match = match_score >= 0.5
            
            return {
                "valid": url_accessible,
                "status": "verified" if url_accessible else "blocked",
                "url": linkedin_url,
                "url_accessible": url_accessible,
                "status_code": status_code,
                "slug": slug,
                "slug_match": slug_match,
                "name_match_score": round(match_score, 2),
                "name_match_details": {
                    "candidate_name": candidate_name,
                    "slug_clean": slug_clean,
                    "parts_matched": matches_found,
                    "parts_total": len(name_parts)
                }
            }
            
        except requests.exceptions.Timeout:
            return {"valid": False, "status": "timeout", "error": "Request timeout", "url": linkedin_url}
        except Exception as e:
            return {"valid": False, "status": "error", "error": str(e), "url": linkedin_url}

    def verify_portfolio(self, portfolio_url):
        """Basic portfolio verification."""
        if not portfolio_url:
            return None
        
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(portfolio_url, timeout=10, headers=headers)
            
            return {
                "valid": response.status_code == 200,
                "status": "accessible" if response.status_code == 200 else "not_accessible",
                "url": portfolio_url,
                "status_code": response.status_code
            }
        except Exception as e:
            return {"valid": False, "status": "error", "error": str(e), "url": portfolio_url}

    def verify_candidate(self, candidate_data):
        """Complete candidate verification with skill matching."""
        # Get claimed skills from resume
        claimed_skills = candidate_data.get('skills', [])
        
        # GitHub verification with skill matching
        github_analysis = self.verify_github(
            candidate_data['urls'].get('github'),
            claimed_skills
        )
        
        # LinkedIn verification
        linkedin_analysis = self.verify_linkedin(
            candidate_data['urls'].get('linkedin'),
            candidate_data.get('name')
        )
        
        # Portfolio verification
        portfolio_analysis = self.verify_portfolio(
            candidate_data['urls'].get('portfolio')
        )
        
        # Summary
        verification_summary = {
            "github_verified": github_analysis.get('valid', False),
            "linkedin_verified": linkedin_analysis.get('valid', False),
            "portfolio_verified": portfolio_analysis.get('valid', False) if portfolio_analysis else None,
            "skills_matched": len(github_analysis.get('skill_matches', [])),
            "skills_mismatched": len(github_analysis.get('skill_mismatches', [])),
            "total_platforms_verified": sum([
                github_analysis.get('valid', False),
                linkedin_analysis.get('valid', False),
                portfolio_analysis.get('valid', False) if portfolio_analysis else False
            ])
        }
        
        return {
            "github": github_analysis,
            "linkedin": linkedin_analysis,
            "portfolio": portfolio_analysis,
            "summary": verification_summary
        }
