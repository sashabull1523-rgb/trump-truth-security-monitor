
import os
import requests
from dotenv import load_dotenv


# Load environment variables
load_dotenv()


TRUTH_API_KEY = os.environ.get("TRUTH_API_KEY")
TRUTH_API_URL = os.environ.get("TRUTH_API_URL")


def main():

    print("================================")
    print("TRUTH SOCIAL API MONITOR")
    print("================================")

    # Check that required secrets exist
    if not TRUTH_API_KEY:
        print("ERROR: TRUTH_API_KEY secret is missing")
        return

    if not TRUTH_API_URL:
        print("ERROR: TRUTH_API_URL secret is missing")
        return

    print("API credentials detected.")
    print("Connecting to authorized Truth Social data source...")

    # API headers
    headers = {
        "Authorization": f"Bearer {TRUTH_API_KEY}",
        "Accept": "application/json",
        "User-Agent": "Truth-Social-Monitor/1.0"
    }

    try:

        # Make API request
        response = requests.get(
            TRUTH_API_URL,
            headers=headers,
            timeout=30
        )

        print("--------------------------------")
        print("HTTP status:", response.status_code)
        print("--------------------------------")

        # Print API response so we can diagnose errors
        print("API response:")
        print(response.text[:5000])
        print("--------------------------------")

        # Handle errors
        if response.status_code >= 400:

            print("API REQUEST FAILED")
            print("The API rejected the request.")
            print("Status code:", response.status_code)

            if response.status_code == 401:
                print("The API key is invalid or unauthorized.")

            elif response.status_code == 403:
                print("The API key does not have permission to access this resource.")

            elif response.status_code == 404:
                print("The API endpoint was not found.")

            elif response.status_code == 422:
                print(
                    "The API understood the request but rejected "
                    "the parameters or request format."
                )

            return

        # Try to parse JSON
        try:

            data = response.json()

            print("JSON response received successfully.")
            print("--------------------------------")
            print(data)
            print("--------------------------------")

        except ValueError:

            print("WARNING: API response was not valid JSON.")
            print("Raw response:")
            print(response.text[:5000])

            return

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
