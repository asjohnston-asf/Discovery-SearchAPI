import argparse
import yaml
import requests

def api_type(user_input: str) -> str:
    user_input = str(user_input).lower()
    # If it's a url with a trailing '/', remove it:
    if user_input.endswith('/'):
        user_input = user_input[:-1]
    # Grab list of maturities, for available API's:
    with open("maturities.yml", "r") as ymlfile:
        maturities = yaml.safe_load( ymlfile.read() )
    api_info = None # Will be: ("api url: str", "is_flex_maturity: bool")
    for nickname, info in maturities.items():
        # If the url in maturities ends with '/', remove it. (Lets it match user input always):
        if info["this_api"].endswith('/'):
            info["this_api"] = info["this_api"][:-1]
        # If you gave it the nickname, or the url of a known api:
        if user_input in [ nickname.lower(), info["this_api"], ]:
            api_info = {
                "this_api": info["this_api"],
                "flexible_maturity": info["flexible_maturity"],
            }
            break
    # Make sure you hit an option in maturities.yml
    assert api_info is not None, f"Error: api '{user_input}' not found in maturities.yml file. Can pass in full url, or key of maturity."

    # Assume it's a url now, and try to connect:
    try:
        requests.get(api_info["this_api"]).raise_for_status()
    except (requests.ConnectionError, requests.exceptions.HTTPError) as e:
        raise argparse.ArgumentTypeError(f"ERROR: Could not connect to url '{user_input}'. Message: '{e}'.")

    # It connected!! You're good:
    return api_info

def pytest_addoption(parser):
    parser.addoption("--api", action="store", type=api_type, default="local",
        help = "Which API to hit when running tests (LOCAL/DEV/TEST/PROD, or url).")

