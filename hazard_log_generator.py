import pandas as pd

def generate_hazard_log():
    # Define the data structure based on the hazard log requirements
    data = [
        {
            "Hazard Title": "Medication Error",
            "Description": "Incorrect dosage administered to patient.",
            "Clinical Impact": "Potential for adverse drug reaction.",
            "Causes & Controls": "Cause: Staff fatigue\nControl: Double-check protocol",
            "Actions": "[Edit] [Delete]"
        },
        {
            "Hazard Title": "Equipment Failure",
            "Description": "Ventilator alarm malfunction during use.",
            "Clinical Impact": "Hypoxia risk.",
            "Causes & Controls": "Cause: Power surge\nControl: Battery backup check",
            "Actions": "[Edit] [Delete]"
        }
    ]

    # Create a DataFrame
    df = pd.DataFrame(data)

    # Convert to HTML with specific classes for table styling
    html_output = df.to_html(
        classes='table table-striped table-bordered', 
        index=False, 
        justify='left',
        border=0
    )

    # Wrap the table in a basic HTML structure
    full_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <style>
            table {{ width: 100%; border-collapse: collapse; font-family: sans-serif; }}
            th, td {{ padding: 12px; border: 1px solid #ddd; text-align: left; }}
            th {{ background-color: #f4f4f4; }}
            .actions {{ color: blue; cursor: pointer; text-decoration: underline; }}
        </style>
    </head>
    <body>
        <h2>Hazard Log</h2>
        {html_output}
    </body>
    </html>
    """

    with open("hazard_log.html", "w") as f:
        f.write(full_html)
    
    print("Hazard log generated as 'hazard_log.html'")

if __name__ == "__main__":
    generate_hazard_log()