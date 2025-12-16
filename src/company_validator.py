import requests
import datetime
from urllib.parse import quote
import re


class CompanyValidator:
    """
    Company verification focused on REGISTRATION status using FREE APIs.
    Priority: Check if company is legally registered, not just if it has a website.
    
    FREE Sources:
    1. UK Companies House (UK companies)
    2. SEC EDGAR (US public companies)
    3. India MCA via search (Indian companies)
    4. Google/DuckDuckGo for general verification
    """
    
    def __init__(self, opencorporates_api_token=None):
        self.api_token = opencorporates_api_token
        self.cache = {}
    
    def search_uk_companies_house(self, company_name):
        """
        Search UK Companies House - FREE API.
        This is a government registry, so results here mean legally registered.
        """
        try:
            search_url = f"https://find-and-update.company-information.service.gov.uk/search?q={quote(company_name)}"
            headers = {'User-Agent': 'Mozilla/5.0'}
            
            response = requests.get(search_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                content = response.text.lower()
                company_lower = company_name.lower()
                
                # Look for company match in results
                if company_lower in content or any(word in content for word in company_lower.split() if len(word) > 3):
                    # Try to extract company number if present
                    company_number_match = re.search(r'/company/(\d+)', response.text)
                    
                    return {
                        "registered": True,
                        "source": "UK Companies House",
                        "country": "United Kingdom",
                        "company_number": company_number_match.group(1) if company_number_match else None,
                        "search_url": search_url,
                        "confidence": "HIGH"
                    }
            
            return {"registered": False, "source": "UK Companies House", "checked": True}
            
        except Exception as e:
            return {"registered": False, "error": str(e), "source": "UK Companies House"}
    
    def search_sec_edgar(self, company_name):
        """
        Search SEC EDGAR for US public companies - FREE.
        If found here, company is definitely registered and public.
        """
        try:
            url = f"https://www.sec.gov/cgi-bin/browse-edgar?company={quote(company_name)}&type=&dateb=&owner=include&count=10&action=getcompany"
            headers = {'User-Agent': 'ResumeScanner/1.0'}
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                content = response.text.lower()
                company_lower = company_name.lower()
                
                # Look for CIK (SEC company identifier)
                if 'cik=' in content or company_lower in content:
                    cik_match = re.search(r'CIK=(\d+)', response.text, re.IGNORECASE)
                    
                    return {
                        "registered": True,
                        "source": "SEC EDGAR",
                        "country": "United States",
                        "company_type": "Public Company",
                        "cik": cik_match.group(1) if cik_match else None,
                        "search_url": url,
                        "confidence": "HIGH"
                    }
            
            return {"registered": False, "source": "SEC EDGAR", "checked": True}
            
        except Exception as e:
            return {"registered": False, "error": str(e), "source": "SEC EDGAR"}
    
    def search_india_mca(self, company_name):
        """
        Search for Indian companies via MCA/Zauba heuristics.
        """
        try:
            # Zauba Corp is a free company lookup for India
            url = f"https://www.zaubacorp.com/company-list/{quote(company_name[0].upper())}/{quote(company_name)}.html"
            headers = {'User-Agent': 'Mozilla/5.0'}
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                content = response.text.lower()
                company_lower = company_name.lower()
                
                if company_lower in content or 'cin' in content:
                    # CIN is Corporate Identification Number in India
                    cin_match = re.search(r'[UL]\d{5}[A-Z]{2}\d{4}[A-Z]{3}\d{6}', response.text)
                    
                    return {
                        "registered": True,
                        "source": "MCA India (via Zauba)",
                        "country": "India",
                        "cin": cin_match.group(0) if cin_match else None,
                        "confidence": "MEDIUM"
                    }
            
            return {"registered": False, "source": "India MCA", "checked": True}
            
        except Exception as e:
            return {"registered": False, "error": str(e), "source": "India MCA"}
    
    def search_opencorporates(self, company_name):
        """
        OpenCorporates API (if token available) - covers 140+ jurisdictions.
        """
        if not self.api_token or self.api_token.strip() == "":
            return {"registered": False, "source": "OpenCorporates", "skipped": True}
        
        try:
            url = f"https://api.opencorporates.com/v0.4/companies/search?q={quote(company_name)}&api_token={self.api_token}"
            
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('results', {}).get('total_count', 0) > 0:
                    company = data['results']['companies'][0]['company']
                    return {
                        "registered": True,
                        "source": "OpenCorporates",
                        "country": company.get('jurisdiction_code', 'Unknown'),
                        "name_matched": company.get('name'),
                        "incorporation_date": company.get('incorporation_date'),
                        "status": company.get('current_status'),
                        "company_number": company.get('company_number'),
                        "confidence": "HIGH"
                    }
            
            return {"registered": False, "source": "OpenCorporates", "checked": True}
            
        except Exception as e:
            return {"registered": False, "error": str(e), "source": "OpenCorporates"}
    
    def search_duckduckgo(self, company_name):
        """
        DuckDuckGo for general verification - if company has significant web presence.
        Lower confidence but useful as fallback.
        """
        try:
            url = f"https://api.duckduckgo.com/?q={quote(company_name + ' company')}&format=json&no_redirect=1"
            headers = {'User-Agent': 'Mozilla/5.0'}
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                abstract = data.get('Abstract', '')
                heading = data.get('Heading', '')
                
                if abstract or heading:
                    return {
                        "registered": True,  # Has web presence
                        "source": "Web Search (DuckDuckGo)",
                        "abstract": abstract[:200] if abstract else None,
                        "confidence": "LOW",
                        "note": "Found in web search, but not confirmed in official registry"
                    }
            
            return {"registered": False, "source": "DuckDuckGo", "checked": True}
            
        except Exception as e:
            return {"registered": False, "error": str(e), "source": "DuckDuckGo"}

    def verify_company(self, company_name):
        """
        MAIN: Verify if company is legally registered.
        Checks multiple FREE registries and returns a report.
        """
        cache_key = f"company_{company_name.lower()}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Check all sources
        results = {
            "company": company_name,
            "registrations_found": [],
            "sources_checked": [],
            "is_registered": False,
            "confidence": "NONE",
            "red_flags": []
        }
        
        # 1. Check UK Companies House
        uk_result = self.search_uk_companies_house(company_name)
        results["sources_checked"].append("UK Companies House")
        if uk_result.get("registered"):
            results["registrations_found"].append(uk_result)
            results["is_registered"] = True
            results["confidence"] = "HIGH"
        
        # 2. Check SEC EDGAR (US)
        sec_result = self.search_sec_edgar(company_name)
        results["sources_checked"].append("SEC EDGAR (US)")
        if sec_result.get("registered"):
            results["registrations_found"].append(sec_result)
            results["is_registered"] = True
            results["confidence"] = "HIGH"
        
        # 3. Check India MCA
        india_result = self.search_india_mca(company_name)
        results["sources_checked"].append("India MCA")
        if india_result.get("registered"):
            results["registrations_found"].append(india_result)
            results["is_registered"] = True
            if results["confidence"] != "HIGH":
                results["confidence"] = "MEDIUM"
        
        # 4. Check OpenCorporates (if available)
        oc_result = self.search_opencorporates(company_name)
        if not oc_result.get("skipped"):
            results["sources_checked"].append("OpenCorporates")
            if oc_result.get("registered"):
                results["registrations_found"].append(oc_result)
                results["is_registered"] = True
                results["confidence"] = "HIGH"
        
        # 5. Fallback: DuckDuckGo
        if not results["is_registered"]:
            ddg_result = self.search_duckduckgo(company_name)
            results["sources_checked"].append("Web Search")
            if ddg_result.get("registered"):
                results["registrations_found"].append(ddg_result)
                # Only mark as "possibly registered" with low confidence
                results["confidence"] = "LOW"
                results["note"] = "Found in web search but not in official registries"
        
        # Generate red flags
        if not results["is_registered"] and results["confidence"] == "NONE":
            results["red_flags"].append({
                "type": "UNREGISTERED_COMPANY",
                "severity": "HIGH",
                "message": f"'{company_name}' not found in any company registry"
            })
        elif results["confidence"] == "LOW":
            results["red_flags"].append({
                "type": "UNVERIFIED_REGISTRATION",
                "severity": "MEDIUM",
                "message": f"'{company_name}' has web presence but not found in official registries"
            })
        
        # Create summary
        if results["is_registered"] and results["confidence"] == "HIGH":
            results["status"] = "REGISTERED"
            results["status_message"] = f"Legally registered ({results['registrations_found'][0]['source']})"
        elif results["is_registered"] and results["confidence"] in ["MEDIUM", "LOW"]:
            results["status"] = "LIKELY_REGISTERED"
            results["status_message"] = "Likely exists but registration not fully confirmed"
        else:
            results["status"] = "NOT_FOUND"
            results["status_message"] = "Not found in any company registry - potential ghost company"
        
        # For backward compatibility
        results["legal_check"] = {
            "status": "Registered" if results["is_registered"] else "Not Found",
            "sources_checked": results["sources_checked"],
            "confidence": results["confidence"]
        }
        
        results["verification_summary"] = {
            "legal_verified": results["is_registered"] and results["confidence"] in ["HIGH", "MEDIUM"],
            "registries_found": len(results["registrations_found"]),
            "total_red_flags": len(results["red_flags"])
        }
        
        self.cache[cache_key] = results
        return results
