import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import traceback
from Secrets import secrets
import time
from selenium import webdriver
from Secrets import secrets
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
import logging
from flask import Flask, render_template, request

# Need to check with Dustin about how the 'Org' will be passed and then implement a mechanism for the preform_login function
# create file for login creds dict and import them there
# Create error reporting. Discuss with Dustin about if it should be teams message, email or both. 

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('input.html')
# If this works then copy all rationales from xlsx 
# If the denial mapping doesn't work are we ok with using the rationale of 'Other' and placing comment 'Unable to accept at this time' in the message box?
@app.route('/submit_referral', methods=['POST'])
def submit_referral():
    try:
        # Get form data from the request
        sChatMessage = request.form['chat_message']
        sReferralID = request.form['referral_id']
        sAllscriptsFacility = request.form['allscripts_facility']
        sRoute = request.form['route']
        sPatient = request.form['patient']
        sDenialRationale = request.form['denial_rationale']
        
        # Process the form data
        web_script = WebAutomationScript()
        web_script.initialize_driver()
        web_script.perform_login()
        
        # Assign form data to the script object
        web_script.sChatMessage = sChatMessage
        web_script.sReferralID = sReferralID
        web_script.sAllscriptsFacility = sAllscriptsFacility
        web_script.sRoute = sRoute
        web_script.sPatient = sPatient
        web_script.sDenialRationale = sDenialRationale
        
        # Proceed with the rest of the script execution
        web_script.search_and_update()
        time.sleep(5)
        web_script.enter_referral()
        time.sleep(10)
        web_script.find_community()

        return "Referral submitted successfully"
    except Exception as e:
        return f"Error processing referral: {str(e)}", 500


DENIAL_MAPPING = {
    "BED AVAILABILITY: No female beds": "No Available Bed",
    "BED AVAILABILITY: No ISO beds (required)": "No Available Bed",
    "BED AVAILABILITY: No LTC beds": "No Available Bed",
    "BED AVAILABILITY: No male beds": "No Available Bed",
    "BED AVAILABILITY: No private beds (requested)": "No Available Bed",
    "BUSINESS: Business Office - No SNF benefits": "Benefits Exhausted",
    "BUSINESS: Incarceration": "Care Needs Exceed Current Capacity",
    "BUSINESS: Megans law positive": "Other (see comments)",
    "BUSINESS: No contract with insurance": "Not a Covered Benefit",
    "BUSINESS: Out-of-network insurance": "Out of Network",
    "BUSINESS: Outstanding AR balance": "Not a Covered Benefit",
    "Hospice is not offered": "Care Needs Exceed Current Capacity",
    "BUSINESS: Transport": "Care Needs Exceed Current Capacity",
    "CLINICAL: Cannot meet clinical needs": "Care Needs Exceed Current Capacity",
    "CLINICAL: High cost medications/equipment": "Care Needs Exceed Current Capacity",
    "CLINICAL: Sitter needs": "Care Needs Exceed Current Capacity",
    "FINANCIAL": "Not a Covered Benefit",
    "FINANCIAL: MA Pending": "Not a Covered Benefit",
    "FINANCIAL: High risk": "Not a Covered Benefit",
    "SERVICE: Alcohol use/abuse": "Care Needs Exceed Current Capacity",
    "SERVICE: Bariatric": "Care Needs Exceed Current Capacity",
    "SERVICE: Behaviors, uncontrolled": "Care Needs Exceed Current Capacity",
    "SERVICE: Drug use & abuse": "Care Needs Exceed Current Capacity",
    "SERVICE: Homeless": "Other (see comments)",
    "Staffing: Lack of 24 hr RN coverage": "No Available Bed",
    "Staffing: Lack of other (non-RN) coverage": "No Available Bed",
}


class WebAutomationScript:
    def __init__(self):
        self.driver = None
        self.sChatMessage = None
        self.sReferralID = None
        self.sAllscriptsFacility = None
        self.sRoute = None
        self.sPatient = None
        self.sDenialRationale = None
        

    def initialize_driver(self):
        # options = webdriver.ChromeOptions()
        # options.add_argument("--log-level=3")
        # chrome_driver_path = r"C:\Users\mccoolro\Desktop\Scripts\chromedriver.exe"
        # self.driver = webdriver.Chrome(
        #     executable_path=chrome_driver_path, options=options
        # )
        # self.driver.get("https://www.extendedcare.com/professional/home/logon.aspx")
        # self.driver.maximize_window()
        options = webdriver.ChromeOptions()
        options.add_argument("--log-level=3")
        # Remove the chrome_driver_path assignment
        self.driver = webdriver.Chrome(ChromeDriverManager().install())  # Use ChromeDriverManager here
        self.driver.get("https://www.extendedcare.com/professional/home/logon.aspx")
        self.driver.maximize_window()


    def perform_login(self):
        password = secrets.get("DATABASE_PASSWORD")
        user_Name = secrets.get("DATABASE_USER")

        enter_username = self.driver.find_element(
            "xpath", "/html/body/form/div[2]/div[1]/div[4]/div/div[1]/div[1]/input"
        )
        enter_username.send_keys("RXMc001")

        time.sleep(2)

        enter_password = self.driver.find_element(
            "xpath", "/html/body/form/div[2]/div[1]/div[4]/div/div[1]/div[2]/input"
        )
        enter_password.click()
        enter_password.send_keys("Addalie3212!")

        time.sleep(1)

        enter_Button = self.driver.find_element(
            "xpath", "/html/body/form/div[2]/div[1]/div[5]/div"
        )
        enter_Button.click()

        time.sleep(3)
        print("Login was successful")

    def search_and_update(self):
        try:
            # Wait for the Referral ID input field to be present
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.ID, "ViewSearchBar_ReferralID"))
            )

            # Enter Referral ID
            referral_ID = self.driver.find_element(By.ID, "ViewSearchBar_ReferralID")
            referral_ID.clear()
            referral_ID.send_keys(self.sReferralID)
            print("entered the referral ID")

            # Select All Referral Status from dropdown
            referral_status = Select(
                self.driver.find_element(By.ID, "ViewSearchBar_ReferralStatus")
            )
            referral_status.select_by_visible_text("All Referral Status")
            print("Selected All Referral Status in filters")

            # Enter Site Name
            site_Name = self.driver.find_element(By.ID, "ViewSearchBar_SiteName")
            site_Name.clear()
            site_Name.send_keys(self.sAllscriptsFacility)
            print("entered the site name")

            # Select Response Name from dropdown
            response_Name = Select(
                self.driver.find_element(By.ID, "ViewSearchBar_ResponseName")
            )
            response_Name.select_by_index(0)  # Assuming index 0 is the desired option
            print("selected the response filter")

            # Enter Placement Info
            placement_info = Select(
                self.driver.find_element(By.ID, "ViewSearchBar_PlacementInfo")
            )
            placement_info.select_by_visible_text("All")

            print("selected filters for the placement info")

            # Wait for the search button to be visible
            search_button = WebDriverWait(self.driver, 6).until(
                EC.visibility_of_element_located(
                    (By.ID, "ViewSearchBar_ViewSearchButton")
                )
            )

            # Click the Search button
            search_button.click()

            # Wait for the search results to load (adjust the wait time as needed)
            WebDriverWait(self.driver, 7).until(
                EC.presence_of_element_located((By.ID, "ucViewGrid_dgView"))
            )

            logging.info("Search and update successful")

        except Exception as e:
            print(f"Error in search_and_update: {str(e)}")

    def enter_referral(self):
        table_present = WebDriverWait(self.driver, 7).until(
            EC.presence_of_element_located((By.CLASS_NAME, "clsView"))
        )
        self.driver.execute_script(
            "window.scrollTo(0, 0);"
        )  # scrolling the table element into view of the bot so it can be interacted with.

        table_rows = table_present.find_elements(By.TAG_NAME, "tr")
        table_length = len(table_rows)

        if table_length > 0:
            logging.info("FOUND THE TABLE!")

            first_record_row = table_rows[3]

            # Find elements using tag name
            cells = first_record_row.find_elements(By.TAG_NAME, "td")

            site_name_text = cells[0].text.strip()

            # Split the text into lines and get the last line that stores the community name.
            lines = site_name_text.split("\n")
            last_line = lines[-1].strip()

            patient_name = cells[3].text.strip()  # Correct index for patient name
            referral_id = cells[4].text.strip()  # Correct index for referral ID

            # showing referral info
            print(f"Site Name: {last_line}")
            print(f"Patient Name: {patient_name}")
            print(f"Referral ID: {referral_id}")

            referral_Action_Dropdown = self.driver.find_element(
                By.ID, "ucViewGrid_dgView_ctl03_Actions_0_0_0_ActionItems"
            )

            dropdown = Select(referral_Action_Dropdown)

            dropdown.select_by_value("202")
            time.sleep(3)

            go_button = self.driver.find_element(By.ID, "ActionButton_Button")
            go_button.click()

            time.sleep(17)

    def find_community(self):
        try:
            community_count = len(self.driver.find_elements(By.CLASS_NAME, "link.h8"))
            community_count_result = community_count // 2
            print(f"Total number of referred communities is: {community_count_result}")

            mat_select_elements = self.driver.find_elements(By.TAG_NAME, "mat-select")

            counter = -2
            textarea_counter = 1
            denial_counter = -1

            for i in range(community_count_result):
                response_text = (
                    mat_select_elements[2 * i]
                    .get_attribute("innerText")
                    .replace("\t", "")
                )
                print(f"Building {i + 1} - Response: {response_text}")
                counter += 2
                textarea_counter += 1
                denial_counter += 2

                print(f"Target facility: {self.sAllscriptsFacility}")
                current_facility = self.driver.find_elements(By.CLASS_NAME, "link.h8")[
                    counter
                ].text

                print(f"Current facility: {current_facility}")

                if current_facility == self.sAllscriptsFacility:
                    
                    time.sleep(2)
                    print("I found the correct community!")
                    print(f"Counter is {counter}")
                    print(f"Textarea counter is {textarea_counter}")
                    print(f"Denial counter is {denial_counter}")
                    print(f"Denial Rationale from REST: {self.sDenialRationale}")
                    # print(
                    #     f"Keys in the mapping dictionary: {list(DENIAL_MAPPING.keys())}"
                    # )

                    # Select 'No, unable to accept patient' from the dropdown
                    community_initial_Response_dropdown = self.driver.find_elements(
                        By.TAG_NAME, "mat-select"
                    )
                    community_initial_Response_dropdown[counter].click()
                    option_text = "No, unable to accept patient"
                    option_xpath = f"//span[contains(text(), '{option_text}')]/ancestor::mat-option"
                    interested_option = WebDriverWait(self.driver, 8).until(
                        EC.element_to_be_clickable((By.XPATH, option_xpath))
                    )
                    time.sleep(2)
                    interested_option.click()

                    time.sleep(1)

                    # Get the denial rationale text
                    denial_rationale_element = self.driver.find_elements(
                        By.TAG_NAME, "mat-select"
                    )[denial_counter]
                    time.sleep(1)
                    
                    denial_rationale_element.click()
                    time.sleep(2)
                    print(f"Denial counter is {denial_counter}")
                    # denial_rationale_text = denial_rationale_element.get_attribute(
                    #     "innerText"
                    # ).replace("\t", "")
                    # print(f"Denial Rationale: {denial_rationale_text}")

                    # Perform action based on denial mapping
                    print("Performing denial mapping action...")

                    # Map the denial rationale and select the corresponding option
                    mapped_option = DENIAL_MAPPING.get(self.sDenialRationale, "Other")
                    print(f"mapped option is {mapped_option}")
                    mapped_option_xpath = f"//span[contains(text(), '{mapped_option}')]/ancestor::mat-option"
                    mapped_option_element = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, mapped_option_xpath))
                    )
                    time.sleep(2)
                    #self.driver.execute_script("arguments[0].scrollIntoView(true);", mapped_option_element)
                    time.sleep(2) 
                    mapped_option_element.click()
                    print('Supposedly clicked the mapped')

                    time.sleep(2)

                    # Find the correct message box
                    textarea_xpath = f"/html/body/form/table/tbody/tr[4]/td[2]/table/tbody/tr/td[3]/table/tbody/tr[2]/td/div/div/app-root/view-online-referral/div[1]/div/div[2]/div[1]/form/div/div[{textarea_counter}]/referral-recipient-site/form/div[2]/div[2]/div/mat-form-field/div/div[1]/div[3]/textarea"
                    textarea_element = self.driver.find_element(
                        By.XPATH, textarea_xpath
                    )

                    time.sleep(2)

                    # Enter the string into the textarea
                    textarea_element.clear()  # Clear existing text
                    if self.sDenialRationale == "Business: Megans law positive":
                        textarea_element.send_keys(
                            "Patient is a registered sex offender, unable to accept at this time"
                        )
                    else:
                        textarea_element.send_keys(".")

                    time.sleep(5)
                    submit_button = self.driver.find_element(
                                            "xpath",
                                            '//button[@class="mat-focus-indicator mat-button mat-button-base mat-accent mat-raised-button ng-star-inserted" and contains(span/text(), "Send Response")]',
                                        )
                    submit_button.click()
                    time.sleep(3)

            print("Community mapping completed successfully")

        except Exception as e:
            print(f"Error in find_community: {str(e)}")


web_script = WebAutomationScript()
web_script.initialize_driver()
web_script.perform_login()

@app.route("/gcc_denials", methods=["POST"])
def process_json():
    try:
        json_data = request.get_json()

        web_script.sChatMessage = json_data["sChatMessage"]["string"]
        web_script.sReferralID = json_data["sReferralID"]["string"]
        web_script.sAllscriptsFacility = json_data["sAllscriptsFacility"]["string"]
        web_script.sRoute = json_data["sRoute"]["string"]
        web_script.sPatient = json_data["sPatient"]["string"]
        web_script.sDenialRationale = json_data["sDenialRationale"]["string"]
        print(f"Referral id:{web_script.sReferralID}")
        time.sleep(10)
        web_script.search_and_update()
        time.sleep(5)
        web_script.enter_referral()
        time.sleep(10)
        web_script.find_community()

        return "JSON processed successfully"
    except Exception as e:
        return f"Error processing JSON: {str(e)}", 400


if __name__ == "__main__":
    app.run()
