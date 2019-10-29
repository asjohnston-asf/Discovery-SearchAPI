
import os, sys, yaml, json, re
import pytest, warnings
import requests
import glob
import itertools
import argparse

# Let python discover other modules, starting one dir behind this one (project root):
project_root = os.path.realpath(os.path.join(os.path.dirname(__file__),".."))
sys.path.insert(0, project_root)
import conftest as helpers

class RunSingleURLFromFile():
    def __init__(self, json_dict, url_api):
        # DONT add these to url. (Used for tester). Add ALL others to allow testing keywords that don't exist
        reserved_keys = ["expected file","expected code", "title"]
        keywords = []
        for key,val in json_dict.items():
            # If it's reserved, move on:
            if key in reserved_keys:
                continue
            # IF val is None, just add the key. Else add "key=val"
            if val == "None":
                keywords.append(str(key))
            # If you're testing multiple SAME params, add each key-val pair:
            elif isinstance(val, type([])):
                keywords.append(str(key)+"="+",".join(val))
            else:
                keywords.append(str(key)+"="+str(val))
        self.query = url_api + "&".join(keywords)
        status_code, returned_file = self.runQuery()

        if "expected code" in json_dict:
            assert json_dict["expected code"] == status_code, "Status codes is different than expected. Test: {0}".format(json_dict["title"])
        if "expected file" in json_dict:
            assert json_dict["expected file"] == returned_file, "Different file type returned than expected. Test: {0}".format(json_dict["title"])

        if "expected file" not in json_dict and "expected code" not in json_dict:
            print()
            print("URL: {0}".format(self.query))
            print("Status Code: {0}. File returned: {1}".format(status_code, returned_file))
            print()


    def runQuery(self):
        h = requests.head(self.query)
        # text/csv; charset=utf-8
        content_type = h.headers.get('content-type').split('/')[1]
        # Take out the "csv; charset=utf-8", without crahsing on things without charset
        content_type = content_type.split(';')[0] if ';' in content_type else content_type
        file_content = requests.get(self.query).content.decode("utf-8")
        # print(file_content)

        ## COUNT / HTML:
        if content_type == "html":
            content_type = "count"
            if file_content == '0\n':
                content_type = "blank count"
        ## CSV
        elif content_type == "csv":
            blank_csv = '"Granule Name","Platform","Sensor","Beam Mode","Beam Mode Description","Orbit","Path Number","Frame Number","Acquisition Date","Processing Date","Processing Level","Start Time","End Time","Center Lat","Center Lon","Near Start Lat","Near Start Lon","Far Start Lat","Far Start Lon","Near End Lat","Near End Lon","Far End Lat","Far End Lon","Faraday Rotation","Ascending or Descending?","URL","Size (MB)","Off Nadir Angle","Stack Size","Baseline Perp.","Doppler","GroupID"\n'
            if file_content == blank_csv:
                content_type = "blank csv"
        ## DOWNLOAD / PLAIN
        elif content_type == "plain":
            content_type = "download"
            # Check if download script contains this, without granuals in the list:
            match = re.search(r'self\.files\s*=\s*\[\s*\]', str(file_content))
            # If you find it, it's the blank script. If not, There's something there to be downloaded:
            if match:
                content_type = "blank download"
            else:
                content_type = "download"

        ## GEOJSON
        elif content_type == "geojson":
            if file_content == '{\n  "features": [],\n  "type": "FeatureCollection"\n}':
                content_type = "empty geojson"
        ## JSON / JSONLITE
        elif content_type == "json":
            file_content = json.loads(file_content)
            ## ERROR
            if "error" in file_content:
                content_type = "error json"
            ## JSONLITE
            elif "results" in file_content:
                if len(file_content["results"]) > 0:
                    content_type = "jsonlite"
                else:
                    content_type = "blank jsonlite"
            ## JSON
            elif file_content == [[]]:
                content_type = "blank json"
        ## KML
        elif content_type == "vnd.google-earth.kml+xml":
            content_type = "kml"
            blank_kml = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<kml xmlns="http://www.opengis.net/kml/2.2">\n<Document>\n<name>ASF Datapool Search Results</name>\n<description>Search Performed: </description>\n<Style id="yellowLineGreenPoly">\n<LineStyle>\n<color>30ff8800</color>\n<width>4</width>\n</LineStyle>\n<PolyStyle>\n<color>7f00ff00</color>\n</PolyStyle>\n</Style>\n</Document>\n</kml>'.replace(" ", "")
            if file_content.replace(" ", "") == blank_kml:
                content_type = "blank kml"
        ## METALINK
        elif content_type == "metalink+xml":
            content_type = "metalink"
            blank_metalink = '<?xml version="1.0"?>\n<metalink xmlns="http://www.metalinker.org/" version="3.0">\n<publisher><name>Alaska Satellite Facility</name><url>http://www.asf.alaska.edu/</url></publisher>\n<files>\n</files>\n</metalink>'.replace(" ","")
            if file_content.replace(" ","") == blank_metalink:
                content_type = "blank metalink"

        return h.status_code, content_type




# Can't do __name__ == __main__ trick. list_of_tests needs to be declared for the @pytest.mark.parametrize:
project_root = os.path.realpath(os.path.join(os.path.dirname(__file__),".."))
list_of_tests = []

# Get the tests from all *yml* files:
tests_root = os.path.join(project_root, "test","**","test_*.yml")
list_of_tests.extend(helpers.loadTestsFromDirectory(tests_root, recurse=True))

# Same, but with *yaml* files now:
tests_root = os.path.join(project_root, "test","**","test_*.yaml")
list_of_tests.extend(helpers.loadTestsFromDirectory(tests_root, recurse=True))


@pytest.mark.parametrize("json_test", list_of_tests)
def test_EachURLInYaml(json_test, get_cli_args):
    test_info = json_test[0]
    file_config = json_test[1]

    # Load command line args:
    api_cli = get_cli_args["api"]
    only_run_cli = get_cli_args["only run"]

    test_info = helpers.moveTitleIntoTest(test_info)

    if test_info == None:
        pytest.skip("Test does not have a title.")

    # If they passed '--only-run val', and val not in test title:
    if only_run_cli != None and only_run_cli not in test_info["title"]:
        pytest.skip("Title of test did not match --only-run param")

    api_url = api_cli if api_cli != None else file_config['api']
    # Change any keywords for api to the api's url itself:
    api_url = helpers.getAPI(api_url, default="TEST", params="/services/search/param?")

    RunSingleURLFromFile(test_info, api_url)