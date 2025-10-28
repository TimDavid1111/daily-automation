from datetime import datetime
import pytz


def get_formatted_date():
    """Returns tuple: (page_title_date, full_date_string)"""
    detroit_tz = pytz.timezone('America/Detroit')
    now = datetime.now(detroit_tz)
    
    # For page title: "Sunday [10/27/25]"
    day_of_week = now.strftime("%A")
    short_date = now.strftime("%m/%d/%y")
    
    # For Claude prompt: "October 27, 2025"
    full_date = now.strftime("%B %d, %Y")
    
    return f"{day_of_week} [{short_date}]", full_date

