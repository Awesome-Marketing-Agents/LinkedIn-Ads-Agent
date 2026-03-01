"""Resolve LinkedIn URN identifiers to human-readable names.

LinkedIn's analytics API returns raw URNs like ``urn:li:geo:103644278``
for demographic segments.  This module contains static lookup maps for
the most common entity types so we can display friendly names without
extra API calls.
"""

from __future__ import annotations

_SENIORITY_MAP = {
    "1": "Unpaid", "2": "Training", "3": "Entry", "4": "Senior",
    "5": "Manager", "6": "Director", "7": "VP", "8": "CXO",
    "9": "Partner", "10": "Owner",
}

_COMPANY_SIZE_MAP = {
    "A": "Self-employed (1)", "B": "2-10 employees", "C": "11-50 employees",
    "D": "51-200 employees", "E": "201-500 employees", "F": "501-1,000 employees",
    "G": "1,001-5,000 employees", "H": "5,001-10,000 employees", "I": "10,001+ employees",
}

_JOB_FUNCTION_MAP = {
    "1": "Accounting", "2": "Administrative", "3": "Arts and Design",
    "4": "Business Development", "5": "Community & Social Services", "6": "Consulting",
    "7": "Education", "8": "Engineering", "9": "Entrepreneurship", "10": "Finance",
    "11": "Healthcare Services", "12": "Human Resources", "13": "Information Technology",
    "14": "Legal", "15": "Marketing", "16": "Media & Communications",
    "17": "Military & Protective Services", "18": "Operations", "19": "Product Management",
    "20": "Program & Project Management", "21": "Purchasing", "22": "Quality Assurance",
    "23": "Real Estate", "24": "Research", "25": "Sales", "26": "Customer Success & Support",
}

# LinkedIn geo URNs — countries & major regions
_GEO_MAP = {
    "100994331": "Egypt", "101009982": "Algeria", "101165590": "United Kingdom",
    "101174742": "Canada", "101282230": "Germany", "101355337": "Pakistan",
    "101452733": "Philippines", "101620260": "Turkey", "102095887": "Colombia",
    "102098153": "South Korea", "102221843": "Argentina", "102257491": "Sweden",
    "102454443": "Ireland", "102713980": "India", "102890719": "France",
    "102974008": "Bangladesh", "103035651": "Mexico", "103350119": "Israel",
    "103588929": "Chile", "103644278": "United States", "103698695": "Nigeria",
    "103883259": "Belgium", "104035573": "Kenya", "104042275": "Portugal",
    "104305776": "Japan", "104514572": "Poland", "104621616": "Saudi Arabia",
    "104738515": "Netherlands", "104769905": "South Africa",
    "104878862": "Denmark", "104934075": "Russia", "104996005": "Greece",
    "105015875": "Australia", "105072130": "Singapore", "105117694": "Thailand",
    "105149562": "Czech Republic", "105327284": "Norway", "105490917": "Austria",
    "105646813": "Switzerland", "105763813": "Morocco", "105912832": "China",
    "106057199": "Brazil", "106155005": "Spain", "106693272": "Italy",
    "106834578": "Vietnam", "107534077": "New Zealand", "107862105": "Taiwan",
    "108166956": "Romania", "108301978": "Peru",
}

# LinkedIn industry URNs (standard LinkedIn industry taxonomy)
_INDUSTRY_MAP = {
    "1": "Defense & Space", "3": "Computer Hardware", "4": "Computer Software",
    "5": "Computer Networking", "6": "Internet", "7": "Semiconductors",
    "8": "Telecommunications", "10": "Law Practice", "11": "Legal Services",
    "12": "Management Consulting", "13": "Biotechnology", "14": "Medical Practice",
    "15": "Hospital & Health Care", "16": "Pharmaceuticals", "17": "Veterinary",
    "18": "Medical Devices", "19": "Cosmetics", "20": "Apparel & Fashion",
    "21": "Sporting Goods", "22": "Tobacco", "23": "Supermarkets",
    "24": "Food Production", "25": "Consumer Electronics", "26": "Consumer Goods",
    "27": "Furniture", "28": "Retail", "29": "Entertainment",
    "30": "Gambling & Casinos", "31": "Leisure, Travel & Tourism",
    "32": "Hospitality", "33": "Restaurants", "34": "Sports",
    "35": "Food & Beverages", "36": "Motion Pictures and Film",
    "37": "Broadcast Media", "38": "Museums and Institutions",
    "39": "Fine Art", "40": "Performing Arts", "41": "Recreational Facilities",
    "42": "Banking", "43": "Insurance", "44": "Financial Services",
    "45": "Real Estate", "46": "Investment Banking", "47": "Investment Management",
    "48": "Accounting", "49": "Construction", "50": "Building Materials",
    "51": "Architecture & Planning", "52": "Civil Engineering",
    "53": "Aviation & Aerospace", "54": "Automotive", "55": "Chemicals",
    "56": "Machinery", "57": "Mining & Metals", "58": "Oil & Energy",
    "59": "Shipbuilding", "60": "Utilities", "61": "Textiles",
    "62": "Paper & Forest Products", "63": "Railroad Manufacture",
    "64": "Farming", "65": "Ranching", "66": "Dairy",
    "67": "Fishery", "68": "Primary/Secondary Education", "69": "Higher Education",
    "70": "Education Management", "71": "Research", "72": "Military",
    "73": "Legislative Office", "74": "Judiciary", "75": "International Affairs",
    "76": "Government Administration", "77": "Executive Office",
    "78": "Law Enforcement", "79": "Public Safety", "80": "Public Policy",
    "81": "Marketing and Advertising", "82": "Newspapers",
    "83": "Publishing", "84": "Printing", "85": "Information Services",
    "86": "Libraries", "87": "Environmental Services", "88": "Package/Freight Delivery",
    "89": "Individual & Family Services", "90": "Religious Institutions",
    "91": "Civic & Social Organization", "92": "Consumer Services",
    "93": "Transportation/Trucking/Railroad", "94": "Warehousing",
    "95": "Airlines/Aviation", "96": "Maritime", "97": "Information Technology and Services",
    "98": "Market Research", "99": "Public Relations and Communications",
    "100": "Design", "101": "Nonprofit Organization Management",
    "102": "Fund-Raising", "103": "Program Development",
    "104": "Writing and Editing", "105": "Staffing and Recruiting",
    "106": "Professional Training & Coaching", "107": "Venture Capital & Private Equity",
    "108": "Political Organization", "109": "Translation and Localization",
    "110": "Computer Games", "111": "Events Services",
    "112": "Arts and Crafts", "113": "Electrical/Electronic Manufacturing",
    "114": "Online Media", "115": "Nanotechnology", "116": "Music",
    "117": "Logistics and Supply Chain", "118": "Plastics",
    "119": "Computer & Network Security", "120": "Wireless",
    "121": "Alternative Dispute Resolution", "122": "Security and Investigations",
    "123": "Facilities Services", "124": "Outsourcing/Offshoring",
    "125": "Health, Wellness and Fitness", "126": "Alternative Medicine",
    "127": "Media Production", "128": "Animation", "129": "Commercial Real Estate",
    "130": "Capital Markets", "131": "Think Tanks", "132": "Philanthropy",
    "133": "E-Learning", "134": "Wholesale", "135": "Import and Export",
    "136": "Mechanical or Industrial Engineering", "137": "Photography",
    "138": "Human Resources", "139": "Business Supplies and Equipment",
    "140": "Mental Health Care", "141": "Graphic Design",
    "142": "International Trade and Development", "143": "Wine and Spirits",
    "144": "Luxury Goods & Jewelry", "145": "Renewables & Environment",
    "146": "Glass, Ceramics & Concrete", "147": "Packaging and Containers",
    "148": "Industrial Automation", "149": "Government Relations",
    "150": "Horticulture",
    "1029": "Technology, Information and Internet",
}

# LinkedIn standardized job title URNs
_TITLE_MAP = {
    "39": "CEO", "100": "VP", "134": "Engineer", "137": "Consultant",
    "143": "Analyst", "173": "Marketing Manager", "245": "Project Manager",
    "268": "CTO", "280": "Director of Operations",
    "340": "Account Executive", "382": "Software Developer",
    "474": "HR Manager", "577": "Business Analyst",
    "662": "Sales Manager", "681": "Financial Analyst",
    "776": "Operations Manager", "879": "Data Analyst",
    "919": "Account Manager", "1006": "Product Manager",
    "1059": "Founder", "1181": "Program Manager",
    "1335": "Managing Director", "1469": "Sales Director",
    "1558": "Co-Founder", "1712": "Director of Sales",
    "2169": "Head of Marketing", "2447": "Data Scientist",
    "3813": "Growth Manager", "4687": "Head of Sales",
    "5665": "Revenue Operations", "6038": "Demand Generation Manager",
    "8114": "Customer Success Manager", "8534": "SDR Manager",
    "9533": "Head of Growth", "10724": "Partnerships Manager",
    "11726": "Chief Revenue Officer", "12491": "VP of Sales",
    "13057": "Sales Development Representative",
}


def resolve_urn(urn: str) -> str:
    """Resolve a LinkedIn URN to a human-readable name.

    Returns the resolved name, or empty string if unknown.
    """
    parts = str(urn).split(":")
    if len(parts) < 4:
        return ""
    entity_type, entity_id = parts[2], parts[3]
    if entity_type == "seniority":
        return _SENIORITY_MAP.get(entity_id, "")
    if entity_type in ("companySizeRange", "companySize"):
        return _COMPANY_SIZE_MAP.get(entity_id, "")
    if entity_type == "function":
        return _JOB_FUNCTION_MAP.get(entity_id, "")
    if entity_type == "geo":
        return _GEO_MAP.get(entity_id, "")
    if entity_type == "industry":
        return _INDUSTRY_MAP.get(entity_id, "")
    if entity_type == "title":
        return _TITLE_MAP.get(entity_id, "")
    return ""
