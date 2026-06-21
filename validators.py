"""
validators.py
Pure validation function -- no UI or database code here.
Each function returns a list of error strings(empty list = all good).
"""
import re
from datetime import date,datetime
"""
validators.py
Pure validation function -- no UI or database code here.
Each function returns a list of error strings (empty list = all good).
"""

import re
from datetime import date, datetime
def _check_full_name(full_name):
    errors = []
    if not full_name or not full_name.strip():
        errors.append("Full name is required.")
    elif len(full_name.strip()) < 2:
        errors.append("Full name must be at least 2 characters.")
    return errors

def _check_dob(dob):
    errors = []
    if not dob:
        errors.append("Date of birth is required.")
        return errors
    try:
        dob_date = datetime.strptime(dob, "%Y-%m-%d").date()
        if dob_date >= date.today():
            errors.append("Date of birth cannot be today or a future date.")
    except ValueError:
        errors.append("Date of birth must be in YYYY-MM-DD format.")
    return errors

def _check_email(email):
    errors = []
    if not email or not email.strip():
        errors.append("Email address is required.")
    elif not re.match(r"^[\w\.-]+@[\w\.-]+\.\w{2,}$", email):
        errors.append("Enter a valid email address.")
    return errors

def _check_blood_value(value, field_name, min_val, max_val):
    errors = []
    if value is None or value == "":
        errors.append(f"{field_name} is required.")
        return errors
    try:
        num = float(value)
        if num < min_val or num > max_val:
            errors.append(f"{field_name} must be between {min_val} and {max_val}.")
    except ValueError:
        errors.append(f"{field_name} must be a numeric value.")
    return errors

def validate_patient(full_name, dob, email, glucose, haemoglobin, cholesterol):
    """
    Validate all six patient fields.
    Parameters: All parameters are strings (as they come from input fields).
    Returns: list of error strings — empty list means all valid.
    """
    errors = []
    errors.extend(_check_full_name(full_name))
    errors.extend(_check_dob(dob))
    errors.extend(_check_email(email))
    errors.extend(_check_blood_value(glucose,      "Glucose",      0, 700))
    errors.extend(_check_blood_value(haemoglobin,  "Haemoglobin",  0,  30))
    errors.extend(_check_blood_value(cholesterol,  "Cholesterol",  0, 700))
    return errors  
if __name__ == "__main__":
    errs = validate_patient("sita", "2004-05-10", "sita@email.com", "90", "13", "180")
    print("Errors:", errs)  # Should print: Errors: []