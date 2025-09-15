from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
import time

LOGIN_URL = "http://localhost:8502/login"
VALID_EMAIL = "peaceselem@gmail.com"
VALID_PASSWORD = "validpassword"

def login(driver, email, password):
    driver.get(LOGIN_URL)
    time.sleep(1)
    driver.find_element(By.NAME, "email").send_keys(email)
    driver.find_element(By.NAME, "password").send_keys(password)
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    time.sleep(1)

def logout_if_possible(driver):
    try:
        logout_link = driver.find_element(By.PARTIAL_LINK_TEXT, "Logout")
        logout_link.click()
        print("[TC5.0] Logged out previous session.")
        time.sleep(1)
    except Exception:
        pass

def test_cancel_event_permissions():
    print("\n[TC5.1] Cancel Event Test: Start")
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.binary_location = "/usr/bin/chromium"
    service = Service("/usr/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=options)
    try:
        driver.get(LOGIN_URL)
        logout_if_possible(driver)
        login(driver, VALID_EMAIL, VALID_PASSWORD)
        print("[TC5.1] Logged in successfully.")
        # Wait for start agent button to be enabled
        for _ in range(20):
            start_btn = driver.find_element(By.ID, "start-agent")
            if start_btn.is_enabled():
                break
            time.sleep(0.5)
        else:
            print("[TC5.1] Start Agent button did not become enabled.")
            driver.quit()
            return
        start_btn.click()
        print("[TC5.1] Clicked Start Agent button. Waiting for agent to initialize...")
        time.sleep(60)
        # Wait for chat input to be enabled
        for _ in range(40):
            chat_input = driver.find_element(By.ID, "chat-input")
            if chat_input.is_enabled():
                break
            time.sleep(0.5)
        else:
            print("[TC5.1] Chat input did not become enabled.")
            driver.quit()
            return
        # Main flow: cancel Graham's test event
        chat_input.send_keys("Cancel Graham's test event")
        send_btn = driver.find_element(By.ID, "send-message")
        send_btn.click()
        print("[TC5.1] Sent event cancellation request. Waiting for confirmation...")
        found = False
        for _ in range(60):
            chat_output = driver.find_element(By.ID, "chat-output").text.lower()
            if any(word in chat_output for word in ["cancelled", "canceled", "deleted", "removed", "success"]):
                found = True
                break
            time.sleep(1)
        if found:
            print("[TC5.1] System confirmed the event cancellation. Test passed.")
        else:
            print("[TC5.1] System did not confirm the event cancellation. Test failed.")
        # Alternative flow: try to cancel event without permission
        chat_input.clear()
        chat_input.send_keys("Cancel Maintenance: HVAC inspection")
        send_btn.click()
        print("[TC5.2] Sent unauthorized event cancellation request. Waiting for permission error...")
        found_error = False
        for _ in range(30):
            chat_output = driver.find_element(By.ID, "chat-output").text.lower()
            if any(word in chat_output for word in ["permission", "not allowed", "not authorized", "cannot", "denied"]):
                found_error = True
                break
            time.sleep(1)
        if found_error:
            print("[TC5.2] System denied cancellation due to permissions. Test passed.")
        else:
            print("[TC5.2] System did not deny cancellation due to permissions. Test failed.")
    except Exception as e:
        print("[TC5.1/TC5.2] Test failed:", e)
    finally:
        driver.quit()

if __name__ == "__main__":
    test_cancel_event_permissions()
