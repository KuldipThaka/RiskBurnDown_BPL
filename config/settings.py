import os

EXCEL_FILE = r"E:\Code\BPL_Risk_Burndown\BPL_Risk_Structure\risks.xlsx"

USERS = {
    'tech_manager': {'password': 'techpass', 'type': 'tech'},
    'upper_manager': {'password': 'upperpass', 'type': 'upper'}
}

ALL_STANDARD_COLUMNS = [
    'Risk ID', 'Risk Description', 'Risk Open Date', 
    'Expected End Date (DD-MMM-YY)', 'Closure Date (DD-MMM-YY)', 
    'Risk Type', 'Probability', 'Impact', 'Difficulty', 
    'Priority', 'Action Plan', 'Owner'
]

RISK_TYPE_OPTIONS = ['Quality', 'External', 'Cost', 'Technical']
PROBABILITY_OPTIONS = ['Low', 'Medium', 'High', 'Very High']
IMPACT_OPTIONS = ['Low', 'Medium', 'High', 'Very High']
DIFFICULTY_OPTIONS = ['Low', 'Medium', 'High', 'Very High']
PRIORITY_OPTIONS = ['Low', 'Medium', 'High', 'Critical']

DATE_FORMAT = "%d-%b-%y"