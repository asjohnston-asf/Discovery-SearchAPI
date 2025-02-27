import argparse
import requests
import warnings

from SearchAPI.asf_env import load_config_file

def api_type(user_input: str) -> str:
    # If it's a url with a trailing '/', remove it:
    if user_input.endswith('/'):
        user_input = user_input[:-1]
    # Grab list of maturities, for available API's:
    maturities = load_config_file()
    api_info = None # Will be: ("api url: str", "is_flex_maturity: bool")
    assert user_input.lower() != "default", "This is used when the URL isn't on this list. Don't call directly! Just make `url <Your actuall url>` to use."
    for nickname, info in maturities.items():
        if nickname.lower() == "default":
            continue
        # If the url in maturities ends with '/', remove it. (Lets it match user input always):
        if info["this_api"].endswith('/'):
            info["this_api"] = info["this_api"][:-1]
        # If you gave it the nickname, or the url of a known api:
        if user_input.lower() in [ nickname.lower(), info["this_api"].lower(), ]:
            api_info = {
                "this_api": info["this_api"],
                "flexible_maturity": info["flexible_maturity"],
            }
            break
    # If you don't hit an option in maturities.yml, assume what was passed IS the url:
    if api_info is None:
        warnings.warn(f"API url not found in 'maturities.yml'. Using it directly. ({user_input}).")

        api_info = maturities["default"]
        api_info["this_api"] = user_input

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

