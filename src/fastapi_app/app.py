import logging
import os
import pathlib
from datetime import datetime

from azure.monitor.opentelemetry import configure_azure_monitor
from fastapi import Depends, FastAPI, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse

import requests
import json
import time
import sys
from datetime import datetime

#from .models import Restaurant, Review, engine

# Setup logger and Azure Monitor:
logger = logging.getLogger("app")
logger.setLevel(logging.INFO)
if os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING"):
    configure_azure_monitor()


# Setup FastAPI app:
app = FastAPI()
parent_path = pathlib.Path(__file__).parent.parent
app.mount("/mount", StaticFiles(directory=parent_path / "static"), name="static")
templates = Jinja2Templates(directory=parent_path / "templates")
templates.env.globals["prod"] = os.environ.get("RUNNING_IN_PRODUCTION", False)
# Use relative path for url_for, so that it works behind a proxy like Codespaces
templates.env.globals["url_for"] = app.url_path_for


# Dependency to get the database session


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    logger.info("root called")
    

@app.get("/create", response_class=HTMLResponse)
async def create_restaurant(request: Request):
    logger.info("Request for add restaurant page received")
    return templates.TemplateResponse("create_restaurant.html", {"request": request})


@app.post("/processCode", response_class=RedirectResponse)
async def processCode(
    request: Request
):
    try:
        # Get JSON data from request body
        data = await request.json()
       
        # Process the data (example: extract a field)
        PCEXEmail = data.get("PCEXEmail", "support@randomtechi.com")
        PCEXPassword = data.get("PCEXPassword", "support@randomtechi.com")
        PCEXCode = data.get("PCEXEmail", "support@randomtechi.com")
       
        result = process_user(PCEXEmail, PCEXPassword, PCEXCode)
        return JSONResponse(content=result, status_code=200)
    
    except Exception as e:
       
        result = {
            "statusCode": 201,
            "PCEXCode": PCEXCode,
            "quantity": None,
            "PCEXEmailaddress": PCEXEmail,
            "success_message": "",
            "error_message": f"Internal Error: {e}",
            "ExecutionStartTimestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "ExecutionEndTimestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        print("Error withAPI: " ,str(e),str(result))
         # Return JSON response
        return JSONResponse(content=result, status_code=201)
    
    

# Constants
LOGIN_URL = "https://api.pcex.com/api/app/user/login"
FUNDS_OVERVIEW_URL = "https://api.pcex.com/api/app/funds/overview"
FOLLOW_CODE_URL = "https://api.pcex.com/api/app/second/share/user/follow/code"

PERCENT = 0.01

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Function to get 1% value of usdtTotal from fund overview
def get_usdt_total_1_percent(fund_overview):
    if fund_overview and 'data' in fund_overview and 'usdtTotal' in fund_overview['data']:
        usdt_total = fund_overview['data']['usdtTotal']
        one_percent_value = usdt_total * PERCENT  # 1% value of usdtTotal
        rounded_value = round(one_percent_value, 2)
        return rounded_value
    else:
        return None

# Step 1: Call the login API to get the app-login-token
def get_app_login_token(email, password):
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
        "sec-ch-ua-platform": "Windows",
        "sec-ch-ua": "\"Chromium\";v=\"134\", \"Not:A-Brand\";v=\"24\", \"Google Chrome\";v=\"134\"",
        "app-analog": "false",
        "sec-ch-ua-mobile": "?0",
        "set-aws": "true",
        "set-language": "ENGLISH"
    }
    data = {
        "email": email,
        "password": password
    }

    response = requests.post(LOGIN_URL, headers=headers, json=data)

    if response.status_code == 200:
        # Extract the app-login-token from the response
        response_data = response.json()
        return response_data.get("data", "")
    else:
        return None

# Step 2: Get Fund Overview using the app-login-token
def get_fund_overview(app_login_token):
    headers = {
        "accept": "application/json",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "en-US,en;q=0.9",
        "app-analog": "false",
        "app-login-token": f"{app_login_token}",
        "Content-Length": "0",
        "origin": "https://pcex.com",
        "referer": "https://pcex.com/",
        "sec-ch-ua": "\"Chromium\";v=\"134\", \"Not:A-Brand\";v=\"24\", \"Google Chrome\";v=\"134\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "Windows",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "set-aws": "true",
        "set-language": "ENGLISH",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
    }
    
    response = requests.post(FUNDS_OVERVIEW_URL, headers=headers)
    print("This has started now", response.json())
    if response.status_code == 200:
        return response.json()
    else:
        return None

# Step 3: Follow code using the app-login-token
def follow_code(app_login_token, quantity, code):
    headers = {
        "accept": "application/json",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "en-US,en;q=0.9",
        "app-analog": "false",
        "app-login-token": f"{app_login_token}",
        "content-type": "application/json",
        "Host": "api.pcex.com",
        "origin": "https://pcex.com",
        "priority": "u=1, i",
        "referer": "https://pcex.com/",
        "sec-ch-ua": "\"Chromium\";v=\"134\", \"Not:A-Brand\";v=\"24\", \"Google Chrome\";v=\"134\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "Windows",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "set-aws": "true",
        "set-language": "ENGLISH",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
    }
    data = {
        "code": code,  # Use the dynamically extracted code here
        "quantity": f"{quantity}"
    }
    response = requests.post(FOLLOW_CODE_URL, headers=headers, json=data)

    if response.status_code == 200:
        response_data = response.json()
        # Check if the resultCode is true and errCode is 0
        if response_data.get("resultCode") == True and response_data.get("errCode") == 0:
            return True, response_data
        else:
            return False, response_data
    else:
        return False, {"message": "Failed to follow code."}

# Main function to process the user using the parameters
def process_user(email, password, code):
    execution_start_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Step 1: Login to get the app-login-token
    app_login_token = get_app_login_token(email, password)
    
    # Default messages
    success_message = ""
    error_message = ""

    if app_login_token:
        # Step 2: Get Fund Overview
        fund_overview = get_fund_overview(app_login_token)
       
        if fund_overview:
            # Step 2: Calculate and get the 1% of usdtTotal
            quantity = get_usdt_total_1_percent(fund_overview)
            
            # Step 3: Follow Code
            success, follow_response = follow_code(app_login_token, quantity, code)

            # End time for execution
            execution_end_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # Prepare success or error message
            if success:
                statusCode: 200
                success_message = f"Success for {email} - Follow Code succeeded."
                error_message = ""  # Clear error message if successful
            else:
                statusCode: 201
                success_message = ""
                error_message = f"Failure for {email} - Follow Code failed. Reason: {follow_response.get('errCodeDes', 'Unknown error')}"
            
            return {
                "statusCode": statusCode,
                "PCEXCode": code,
                "quantity": quantity,
                "PCEXEmailaddress": email,
                "success_message": success_message,
                "error_message": error_message,
                "ExecutionStartTimestamp": execution_start_timestamp,
                "ExecutionEndTimestamp": execution_end_timestamp
            }
        else:
            execution_end_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            error_message = f"Failed to get fund overview for {email}."
            return {
                "statusCode": 201,
                "PCEXCode": code,
                "quantity": None,
                "PCEXEmailaddress": email,
                "success_message": success_message,
                "error_message": error_message,
                "ExecutionStartTimestamp": execution_start_timestamp,
                "ExecutionEndTimestamp": execution_end_timestamp
            }
    else:
        execution_end_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        error_message = f"Login failed for {email}. Cannot proceed with other API calls."
        return {
            "statusCode": 201,
            "PCEXCode": code,
            "quantity": None,
            "PCEXEmailaddress": email,
            "success_message": success_message,
            "error_message": error_message,
            "ExecutionStartTimestamp": execution_start_timestamp,
            "ExecutionEndTimestamp": execution_end_timestamp
        }


