import os
import subprocess
import time
from playwright.sync_api import sync_playwright, expect

def run_verification():
    # Start a simple HTTP server in the background
    server_process = subprocess.Popen(["python", "-m", "http.server", "8000"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Give the server a moment to start
    time.sleep(2)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            # Go to the local server URL
            page.goto("http://localhost:8000")

            # Wait for the main title to be visible
            expect(page.locator("h2.title")).to_be_visible(timeout=20000)

            # Wait for a specific endpoint category to appear to ensure the content is loaded
            expect(page.locator("#operations-tag-Tickets")).to_be_visible(timeout=20000)

            # Take a screenshot
            page.screenshot(path="jules-scratch/verification/swagger_ui.png")

            browser.close()
    finally:
        # Ensure the server is terminated
        server_process.terminate()

if __name__ == "__main__":
    run_verification()