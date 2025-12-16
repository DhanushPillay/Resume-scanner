import datetime
from typing import List, Dict, Any


class RiskEngine:
    """
    The BS Detector - Combines all verification data to generate a comprehensive
    trust score and identify potential red flags.
    """
    
    def __init__(self):
        # Scoring weights
        self.weights = {
            "company_registered": 20,      # Companies legally registered
            "github_verified": 15,         # GitHub profile exists and valid
            "github_activity": 10,         # GitHub has meaningful activity
            "github_age": 10,              # GitHub account is not brand new
            "github_skill_match": 10,      # Skills match GitHub repos
            "linkedin_verified": 10,       # LinkedIn profile exists
            "linkedin_name_match": 5,      # LinkedIn name matches resume
            "no_unregistered": 20,         # No unregistered companies
        }
    
    def calculate_trust_score(self, candidate_data, company_verifications, candidate_verification):
        """
        Calculate a comprehensive trust score (0-100) based on verified data points.
        """
        score = 0
        max_possible = 100
        details = []
        
        # === COMPANY REGISTRATION SCORING ===
        registered_companies = 0
        unregistered_companies = 0
        total_companies = len(company_verifications) if company_verifications else 0
        
        for cv in company_verifications:
            # Use new company validator format
            if cv.get('status') == 'REGISTERED' or cv.get('is_registered'):
                registered_companies += 1
            elif cv.get('status') == 'LIKELY_REGISTERED':
                registered_companies += 0.5
            elif cv.get('status') == 'NOT_FOUND':
                unregistered_companies += 1
        
        if total_companies > 0:
            company_score = (registered_companies / total_companies) * self.weights['company_registered']
            score += company_score
            details.append({
                "category": "Company Registration",
                "points": round(company_score, 1),
                "max": self.weights['company_registered'],
                "message": f"{registered_companies}/{total_companies} companies found in registries"
            })
            
            # Unregistered company penalty
            if unregistered_companies == 0:
                score += self.weights['no_unregistered']
                details.append({
                    "category": "No Unregistered Companies",
                    "points": self.weights['no_unregistered'],
                    "max": self.weights['no_unregistered'],
                    "message": "All listed companies verified in registries"
                })
            else:
                details.append({
                    "category": "No Unregistered Companies",
                    "points": 0,
                    "max": self.weights['no_unregistered'],
                    "message": f"{unregistered_companies} company(ies) not found in registries"
                })
        
        # === GITHUB VERIFICATION SCORING ===
        gh = candidate_verification.get('github', {})
        
        if gh.get('valid'):
            # GitHub exists and is valid
            score += self.weights['github_verified']
            details.append({
                "category": "GitHub Profile",
                "points": self.weights['github_verified'],
                "max": self.weights['github_verified'],
                "message": f"GitHub profile verified (@{gh.get('username')})"
            })
            
            # Account age scoring
            account_age = gh.get('account_age_days', 0)
            if account_age >= 365:
                score += self.weights['github_age']
                details.append({
                    "category": "GitHub Account Age",
                    "points": self.weights['github_age'],
                    "max": self.weights['github_age'],
                    "message": f"Established account ({gh.get('account_age_months')} months)"
                })
            elif account_age >= 180:
                partial = self.weights['github_age'] * 0.5
                score += partial
                details.append({
                    "category": "GitHub Account Age",
                    "points": round(partial, 1),
                    "max": self.weights['github_age'],
                    "message": f"Fairly new account ({gh.get('account_age_months')} months)"
                })
            else:
                details.append({
                    "category": "GitHub Account Age",
                    "points": 0,
                    "max": self.weights['github_age'],
                    "message": f"Very new account ({account_age} days old)"
                })
            
            # Activity scoring
            repos = gh.get('public_repos', 0)
            original_repos = gh.get('original_repos', repos)
            recent_activity = gh.get('recent_activity_count', 0)
            
            if original_repos >= 10 and recent_activity >= 3:
                score += self.weights['github_activity']
                details.append({
                    "category": "GitHub Activity",
                    "points": self.weights['github_activity'],
                    "max": self.weights['github_activity'],
                    "message": f"Active profile ({original_repos} original repos, {recent_activity} recent)"
                })
            elif original_repos >= 5 or recent_activity >= 1:
                partial = self.weights['github_activity'] * 0.5
                score += partial
                details.append({
                    "category": "GitHub Activity",
                    "points": round(partial, 1),
                    "max": self.weights['github_activity'],
                    "message": f"Moderate activity ({original_repos} original repos)"
                })
            else:
                details.append({
                    "category": "GitHub Activity",
                    "points": 0,
                    "max": self.weights['github_activity'],
                    "message": f"Low activity ({original_repos} original repos)"
                })
            
            # Skill matching scoring
            skill_matches = len(gh.get('skill_matches', []))
            skill_mismatches = len(gh.get('skill_mismatches', []))
            total_skills = skill_matches + skill_mismatches
            
            if total_skills > 0:
                match_ratio = skill_matches / total_skills
                skill_score = match_ratio * self.weights['github_skill_match']
                score += skill_score
                details.append({
                    "category": "Resume-GitHub Skill Match",
                    "points": round(skill_score, 1),
                    "max": self.weights['github_skill_match'],
                    "message": f"{skill_matches}/{total_skills} claimed skills verified in GitHub"
                })
            else:
                # No skills to match
                score += self.weights['github_skill_match'] * 0.5
                details.append({
                    "category": "Resume-GitHub Skill Match",
                    "points": self.weights['github_skill_match'] * 0.5,
                    "max": self.weights['github_skill_match'],
                    "message": "No specific skills to verify"
                })
        else:
            details.append({
                "category": "GitHub Profile",
                "points": 0,
                "max": self.weights['github_verified'],
                "message": f"GitHub not verified: {gh.get('error', 'Not provided')}"
            })
        
        # === LINKEDIN VERIFICATION SCORING ===
        li = candidate_verification.get('linkedin', {})
        
        if li and li.get('valid'):
            score += self.weights['linkedin_verified']
            details.append({
                "category": "LinkedIn Profile",
                "points": self.weights['linkedin_verified'],
                "max": self.weights['linkedin_verified'],
                "message": "LinkedIn profile accessible"
            })
            
            if li.get('slug_match'):
                score += self.weights['linkedin_name_match']
                details.append({
                    "category": "LinkedIn Name Match",
                    "points": self.weights['linkedin_name_match'],
                    "max": self.weights['linkedin_name_match'],
                    "message": f"Name matches URL (score: {li.get('name_match_score', 0)})"
                })
            else:
                details.append({
                    "category": "LinkedIn Name Match",
                    "points": 0,
                    "max": self.weights['linkedin_name_match'],
                    "message": "Name doesn't match LinkedIn URL"
                })
        else:
            details.append({
                "category": "LinkedIn Profile",
                "points": 0,
                "max": self.weights['linkedin_verified'],
                "message": f"LinkedIn not verified: {li.get('error', 'Not provided') if li else 'Not provided'}"
            })
        
        return {
            "score": round(min(score, 100)),
            "max_score": max_possible,
            "percentage": round((min(score, 100) / max_possible) * 100),
            "details": details
        }
    
    def detect_risk_flags(self, candidate_data, company_verifications, candidate_verification):
        """
        Comprehensive risk flag detection.
        """
        flags = []
        
        # === COMPANY RED FLAGS ===
        for cv in company_verifications:
            # Handle new company validator format
            if cv.get('status') == 'NOT_FOUND':
                flags.append({
                    "type": "UNREGISTERED_COMPANY",
                    "severity": "HIGH",
                    "category": "Company",
                    "message": f"'{cv['company']}' not found in any company registry"
                })
            
            # Also check red_flags if provided
            for flag in cv.get('red_flags', []):
                flags.append({
                    "type": flag['type'],
                    "severity": flag['severity'],
                    "category": "Company",
                    "message": flag['message'],
                    "company": cv['company']
                })
        
        # === GITHUB RED FLAGS ===
        gh = candidate_verification.get('github', {})
        
        if gh.get('valid'):
            # Hyper-inflation flags from GitHub
            for hf in gh.get('hyper_inflation_flags', []):
                flags.append({
                    "type": hf['type'],
                    "severity": hf.get('severity', 'MEDIUM'),
                    "category": "GitHub",
                    "message": hf['message']
                })
            
            # Skill mismatches
            for sm in gh.get('skill_mismatches', []):
                flags.append({
                    "type": "SKILL_MISMATCH",
                    "severity": "MEDIUM",
                    "category": "Skills",
                    "message": sm['message']
                })
            
            # Senior role claim with new GitHub
            job_titles = [t.lower() for t in candidate_data.get('job_titles', [])]
            senior_titles = ['senior', 'lead', 'principal', 'architect', 'manager', 'director', 'head', 'vp', 'chief']
            
            has_senior_claim = any(any(st in jt for st in senior_titles) for jt in job_titles)
            
            if has_senior_claim:
                if gh.get('account_age_days', 0) < 180 or gh.get('original_repos', 0) < 5:
                    flags.append({
                        "type": "HYPER_INFLATION",
                        "severity": "HIGH",
                        "category": "Experience",
                        "message": f"Claims senior role but GitHub is {gh.get('account_age_days')} days old with {gh.get('original_repos', 0)} original repos"
                    })
        
        elif gh.get('status') == 'not_found':
            flags.append({
                "type": "INVALID_GITHUB",
                "severity": "MEDIUM",
                "category": "GitHub",
                "message": "Provided GitHub profile does not exist"
            })
        
        # === LINKEDIN RED FLAGS ===
        li = candidate_verification.get('linkedin', {})
        
        if li:
            if li.get('status') == 'not_found':
                flags.append({
                    "type": "INVALID_LINKEDIN",
                    "severity": "MEDIUM",
                    "category": "LinkedIn",
                    "message": "Provided LinkedIn profile does not exist (404)"
                })
            elif li.get('valid') and not li.get('slug_match'):
                flags.append({
                    "type": "NAME_MISMATCH",
                    "severity": "LOW",
                    "category": "LinkedIn",
                    "message": f"Name '{candidate_data.get('name')}' doesn't match LinkedIn URL slug"
                })
        
        # Sort flags by severity
        severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        flags.sort(key=lambda x: severity_order.get(x['severity'], 4))
        
        return flags
    
    def get_risk_level(self, trust_score, flags):
        """
        Determine overall risk level based on score and flags.
        """
        critical_flags = sum(1 for f in flags if f['severity'] == 'CRITICAL')
        high_flags = sum(1 for f in flags if f['severity'] == 'HIGH')
        
        if critical_flags > 0 or trust_score < 30:
            return {
                "level": "CRITICAL",
                "color": "#ff4444",
                "icon": "🚫",
                "message": "High risk - Multiple serious verification failures"
            }
        elif high_flags >= 2 or trust_score < 50:
            return {
                "level": "HIGH",
                "color": "#ff8800",
                "icon": "⚠️",
                "message": "Elevated risk - Proceed with caution"
            }
        elif len(flags) > 3 or trust_score < 70:
            return {
                "level": "MEDIUM",
                "color": "#ffcc00",
                "icon": "⚡",
                "message": "Moderate risk - Some verification issues"
            }
        else:
            return {
                "level": "LOW",
                "color": "#00cc66",
                "icon": "✅",
                "message": "Low risk - Most claims verified"
            }
    
    def generate_summary(self, candidate_data, company_verifications, candidate_verification):
        """
        Generate a natural language summary of the analysis.
        """
        name = candidate_data.get('name', 'The candidate')
        gh = candidate_verification.get('github', {})
        li = candidate_verification.get('linkedin', {})
        
        summary_parts = []
        
        # GitHub summary
        if gh.get('valid'):
            summary_parts.append(
                f"GitHub profile verified with {gh.get('public_repos', 0)} repos "
                f"({gh.get('original_repos', 0)} original) and {gh.get('account_age_months', 0)} months age."
            )
            
            skill_matches = len(gh.get('skill_matches', []))
            skill_mismatches = len(gh.get('skill_mismatches', []))
            if skill_matches > 0:
                summary_parts.append(f"{skill_matches} claimed skills verified in GitHub repos.")
            if skill_mismatches > 0:
                summary_parts.append(f"{skill_mismatches} claimed skills NOT found in GitHub.")
        else:
            summary_parts.append("GitHub profile could not be verified.")
        
        # LinkedIn summary
        if li and li.get('valid'):
            match_text = "matches" if li.get('slug_match') else "doesn't match"
            summary_parts.append(f"LinkedIn accessible, name {match_text} URL.")
        
        # Company summary
        registered = sum(1 for cv in company_verifications if cv.get('status') == 'REGISTERED')
        not_found = sum(1 for cv in company_verifications if cv.get('status') == 'NOT_FOUND')
        total = len(company_verifications)
        
        if total > 0:
            summary_parts.append(f"{registered}/{total} companies verified in registries.")
            if not_found > 0:
                summary_parts.append(f"⚠️ {not_found} company(ies) not found in any registry.")
        
        return " ".join(summary_parts)
    
    def analyze_risk(self, candidate_data, company_verifications, candidate_verification):
        """
        Complete risk analysis combining all modules.
        """
        # Calculate trust score
        trust_score_data = self.calculate_trust_score(
            candidate_data, company_verifications, candidate_verification
        )
        
        # Detect risk flags
        risk_flags = self.detect_risk_flags(
            candidate_data, company_verifications, candidate_verification
        )
        
        # Determine risk level
        risk_level = self.get_risk_level(trust_score_data['score'], risk_flags)
        
        # Generate summary
        summary = self.generate_summary(
            candidate_data, company_verifications, candidate_verification
        )
        
        return {
            "trust_score": trust_score_data['score'],
            "trust_score_details": trust_score_data['details'],
            "risk_flags": risk_flags,
            "risk_level": risk_level,
            "summary": summary,
            "flag_counts": {
                "critical": sum(1 for f in risk_flags if f['severity'] == 'CRITICAL'),
                "high": sum(1 for f in risk_flags if f['severity'] == 'HIGH'),
                "medium": sum(1 for f in risk_flags if f['severity'] == 'MEDIUM'),
                "low": sum(1 for f in risk_flags if f['severity'] == 'LOW')
            }
        }
