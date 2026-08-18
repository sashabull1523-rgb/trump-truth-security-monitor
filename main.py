import os
import requests
from dotenv import load_dotenv


load_dotenv()


TRUTH_API_KEY = os.environ.get("TRUTH_API_KEY")
TRUTH_API_URL = os.environ.get("TRUTH_API_URL")

TARGET_URL = "https://truthsocial.com/@realDonaldTrump"


def main():

    print("================================")
    print("TRUTH SOCIAL API MONITOR")
    print("================================")

    if not TRUTH_API_KEY:
        print("ERROR: TRUTH_API_KEY secret is missing")
        return

    if not TRUTH_API_URL:
        print("ERROR: TRUTH_API_URL secret is missing")
        return

    print("API credentials detected.")
    print("Connecting to authorized Truth Social data source...")

    headers = {
        "Authorization": f"Bearer {TRUTH_API_KEY}",
        "Accept": "application/json",
        "User-Agent": "Truth-Social-Monitor/1.0"
    }

    params = {
        "url": TARGET_URL
    }

    try:

        response = requests.get(
            TRUTH_API_URL,
            headers=headers,
            params=params,
            timeout=30
        )

        print("--------------------------------")
        print("HTTP status:", response.status_code)
        print("--------------------------------")

        print("Requested URL:")
        print(TARGET_URL)

        print("--------------------------------")
        print("API response:")
        print(response.text[:10000])
        print("--------------------------------")

        if response.status_code >= 400:

            print("API REQUEST FAILED")
            print("Status code:", response.status_code)

            if response.status_code == 401:
                print("The API key is invalid or unauthorized.")

            elif response.status_code == 403:
                print("The API key does not have permission.")

            elif response.status_code == 404:
                print("The API endpoint was not found.")

            elif response.status_code == 422:
                print("The API rejected the request parameters.")

            return

        try:

            data = response.json()

            print("JSON response received successfully.")

            print("--------------------------------")
            print("DATA:")
            print(data)
            print("--------------------------------")

        except ValueError:

            print("WARNING: Response was not valid JSON.")

        print("================================")
        print("API REQUEST SUCCESSFUL")
        print("================================")

    except requests.exceptions.Timeout:

        print("ERROR: The API request timed out.")

    except requests.exceptions.ConnectionError:

        print("ERROR: Could not connect to the API.")

    except requests.exceptions.RequestException as e:

        print("ERROR: API request failed.")
        print(str(e))

    except Exception as e:

        print("UNEXPECTED ERROR:")
        print(str(e))


if __name__ == "__main__":
    main()
