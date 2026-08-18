import os
import requests


TRUTH_API_KEY = os.environ.get("TRUTH_API_KEY")
TRUTH_API_URL = os.environ.get("TRUTH_API_URL")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")


def main():

    print("================================")
    print("TRUTH SOCIAL API MONITOR")
    print("================================")

    # Check required credentials
    if not TRUTH_API_KEY:
        print("ERROR: TRUTH_API_KEY secret is missing")
        return

    if not TRUTH_API_URL:
        print("ERROR: TRUTH_API_URL secret is missing")
        return

    if not OPENAI_API_KEY:
        print("ERROR: OPENAI_API_KEY secret is missing")
        return

    print("API credentials detected.")
    print("Connecting to authorized Truth Social data source...")

    headers = {
        "Authorization": f"Bearer {TRUTH_API_KEY}",
        "Accept": "application/json",
    }

    try:

        response = requests.get(
            TRUTH_API_URL,
            headers=headers,
            timeout=30
        )

        print("HTTP status:", response.status_code)

        response.raise_for_status()

        data = response.json()

        print("API connection successful.")

        print("--------------------------------")
        print("API RESPONSE:")
        print("--------------------------------")

        print(data)

        print("--------------------------------")
        print("MONITOR COMPLETE")
        print("--------------------------------")

    except requests.exceptions.RequestException as e:

        print("API REQUEST ERROR:")
        print(str(e))

    except ValueError:

        print("ERROR: API did not return valid JSON.")

    except Exception as e:

        print("UNEXPECTED ERROR:")
        print(str(e))


if __name__ == "__main__":
    main()
