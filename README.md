 **MIRA Health Predictor**

MIRA Health Predictor is a desktop application developed using Python and Tkinter. It stores patient information and predicts possible health risks based on blood test values.

 **Features**

Add patient records  
Edit patient details  
Delete patient records  
Search patients  
AI generated health predictions  
SQLite database integration  
Input validation  
User-friendly GUI

 **Technologies Used**

Python  
Tkinter  
SQLite  
OpenAI API  
Threading

 **Project Structure**

main.py          \-Main GUI application

database.py      \- Database operations

validators.py    \- Input validations

ai\_service.py    \- AI health prediction service

config.py        \- API key configuration

**How to Use**

Add a patient — click "Add New Patient", fill in name, date of birth, email, and blood test values, then click "Save & Predict". The AI will generate a health prediction in the Remarks field.  
View patients — all records are shown in the main table. Double-click any row to view full details.  
Edit a patient — select a row and click "Edit", update the fields, and save.  
Delete a patient — select a row and click "Delete". A confirmation prompt will appear.  
Search — type in the search bar to filter patients by name or email in real time.