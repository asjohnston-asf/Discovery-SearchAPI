import os           # Generic imports
import shapely.wkt, geomet.wkt      # For comparing wkt's

from helpers import make_request, request_to_json

class test_filesToWKT():
    def __init__(self, **args):
        self.error_msg = "Reason: {0}"

        test_info = args["test_info"]
        test_api = args["config"].getoption("--api")["this_api"]

        # Join the url 'start' to the endpoint, even if they both/neither have '/' between them:
        url_parts = [ test_api, args["test_type_vars"]["endpoint"] ]
        full_url = '/'.join(s.strip('/') for s in url_parts)
        test_info = self.applyDefaultValues(test_info)
        # Make a request, and turn it into json. Helpers should handle if something goes wrong:
        response_server = make_request(full_url, files=test_info["file wkt"] ).content.decode("utf-8")
        response_json = request_to_json(response_server, full_url, test_info["title"]) # The last two params are just for helpfull error messages        

        if test_info["print"] == True:
            print()
            print("Title: " + str(test_info["title"]))
            print("  -- API returned:\n{0}".format(response_json))
            print()
            
        # Make sure the response matches what is expected from the test:
        self.runAssertTests(test_info, response_json)

    def applyDefaultValues(self, test_info):
        # Figure out what test is 'expected' to do:
        pass_assertions = ["parsed wkt"]
        fail_assertions = ["errors"]
        # True if at least one of the above is in the test, False otherwise:
        pass_assertions_used = 0 != len([k for k,_ in test_info.items() if k in pass_assertions])
        fail_assertions_used = 0 != len([k for k,_ in test_info.items() if k in fail_assertions])
        assertions_used = (pass_assertions_used or fail_assertions_used)

        # Default Print the result to screen if tester isn't asserting anything. Else just run the test:
        if "print" not in test_info:
            test_info["print"] = not assertions_used

        if not isinstance(test_info["file wkt"], type([])):
            test_info["file wkt"] = [ test_info["file wkt"] ]

        # If you should check errors. (Will check if you assert something will happen. Checks empty case by default then.)
        if "check errors" not in test_info:
            test_info["check errors"] = assertions_used
        # Setup errors:
        if "errors" not in test_info:
            test_info["errors"] = []
        if not isinstance(test_info["errors"], type([])):
            test_info["errors"] = [ test_info["errors"] ]

        # Load the files:
        resources_dir = os.path.join(os.path.realpath(os.path.dirname(__file__)), "Resources")
        files_that_exist = []
        for file in test_info["file wkt"]:
            file_path = os.path.join(resources_dir, file)
            if os.path.isfile(file_path):
                # Save it in the format the api is expecting:
                files_that_exist.append(('files', open(file_path, 'rb')))
            else:
                assert False, self.error_msg.format("File in 'file wkt' not found: {0}.".format(file_path))
        # Override with the new files:
        test_info["file wkt"] = files_that_exist
        return test_info

    def runAssertTests(self, test_info, response_json):
        if "parsed wkt" in test_info:
            if "parsed wkt" in response_json:
                lhs = geomet.wkt.loads(response_json["parsed wkt"])
                rhs = geomet.wkt.loads(test_info["parsed wkt"])
                assert lhs == rhs, self.error_msg.format("Parsed wkt returned from API did not match 'parsed wkt'.")
            else:
                # Here, I want content to be last. sometimes it explodes in length...                
                assert False, self.error_msg.format("API did not return a WKT.") + "\n - Content: "+str(response_json)
        if test_info["check errors"] == True:
            # Give errors a value to stop key-errors, and force the len() test to always happen:
            if "errors" not in response_json:
                response_json["errors"] = []
            for error in test_info["errors"]:
                assert str(error) in str(response_json["errors"]), self.error_msg.format("Response did not contain expected error.\nExpected: '{0}'\nNot found in:\n{1}\n".format(error, response_json["errors"]))
            assert len(test_info["errors"]) == len(response_json["errors"]), self.error_msg.format("Number of errors declared did not line up with number of expected errors.\nWarnings in response:\n{0}\n".format(response_json["errors"]))



class test_repairWKT():
    def __init__(self, **args):
        self.error_msg = "Reason: {0}"

        test_info = args["test_info"]
        test_api = args["config"].getoption("--api")["this_api"]

        # Join the url 'start' to the endpoint, even if they both/neither have '/' between them:
        url_parts = [ test_api, args["test_type_vars"]["endpoint"] ]
        full_url = '/'.join(s.strip('/') for s in url_parts)
        test_info = self.applyDefaultValues(test_info)
        # Make a request, and turn it into json. Helpers should handle if something goes wrong:
        response_server = make_request(full_url, data={"wkt": test_info["test wkt"]} ).content.decode("utf-8")
        response_json = request_to_json(response_server, full_url, test_info["title"]) # The last two params are just for helpfull error messages
        # Make sure the response matches what is expected from the test:
        self.runAssertTests(test_info, response_json)
        if test_info["print"] == True:
            print(test_info["title"])
            print("  -- Returned: {0}".format(response_json))

    def applyDefaultValues(self, test_info):
        # Copy 'repaired wkt' to the wrapped/unwrapped versions if used:
        if "repaired wkt" in test_info:
            for i in ["repaired wkt wrapped", "repaired wkt unwrapped"]:
                if i not in test_info:
                    test_info[i] = test_info["repaired wkt"]
            del test_info["repaired wkt"]
    
        # Figure out what test is 'expected' to do:
        pass_assertions = ["repaired wkt wrapped", "repaired wkt unwrapped", "repair"]
        fail_assertions = ["repaired error msg"]
        # True if at least one of the above is used, False otherwise:
        pass_assertions_used = 0 != len([k for k,_ in test_info.items() if k in pass_assertions])
        fail_assertions_used = 0 != len([k for k,_ in test_info.items() if k in fail_assertions])

        # Default Print the result to screen if tester isn't asserting anything:
        if "print" not in test_info:
            test_info["print"] = False if (pass_assertions_used or fail_assertions_used) else True
        # If they expect something to pass, check if it needed repairing too:
        if "check repair" not in test_info:
            test_info["check repair"] = pass_assertions_used

        # Add the repair if needed. Make sure it's a list:
        if "repair" not in test_info:
            test_info["repair"] = []
        elif not isinstance(test_info["repair"], type([])):
            test_info["repair"] = [test_info["repair"]]
        
        # If they passed more than one wkt, combine them:
        if isinstance(test_info["test wkt"], type([])):
            test_info["test wkt"] = "GEOMETRYCOLLECTION({0})".format(",".join(test_info['test wkt']))
        return test_info

    def runAssertTests(self, test_info, response_json):
        if "repaired wkt wrapped" in test_info:
            if "wkt" in response_json:
                assert shapely.wkt.loads(response_json["wkt"]["wrapped"]) == shapely.wkt.loads(test_info["repaired wkt wrapped"]), self.error_msg.format("WKT wrapped failed to match the result.\nExpected: {0}\nActual: {1}\n".format(test_info["repaired wkt wrapped"], response_json["wkt"]["wrapped"]))
            else:
                assert False, "WKT not found in response from API. Test: '{0}'. Response: {1}.".format(test_info["title"], response_json)
        if "repaired wkt unwrapped" in test_info:
            if "wkt" in response_json:
                assert shapely.wkt.loads(response_json["wkt"]["unwrapped"]) == shapely.wkt.loads(test_info["repaired wkt unwrapped"]), self.error_msg.format("WKT unwrapped failed to match the result.\nExpected: {0}\nActual: {1}\n".format(test_info["repaired wkt wrapped"], response_json["wkt"]["wrapped"]))
            else:
                assert False, self.error_msg.format("WKT not found in response from API. Response: {0}.".format(response_json))

        if test_info["check repair"]:
            if "repairs" in response_json:
                for repair in test_info["repair"]:
                    assert repair in str(response_json["repairs"]), self.error_msg.format("Expected repair was not found in results. Repairs done: {0}".format(response_json["repairs"]))
                assert len(response_json["repairs"]) == len(test_info["repair"]), self.error_msg.format("Number of repairs doesn't equal number of repaired repairs. Repairs done: {0}.".format(response_json["repairs"]))
            else:
                assert False, "Unexpected WKT returned: {0}. Test: '{1}'".format(response_json, test_info["title"])
        if "repaired error msg" in test_info:
            if "errors" in response_json:
                assert test_info["repaired error msg"] in response_json["errors"]["report"], self.error_msg.format("Got different error message than expected. Error returned: {0}".format(response_json["errors"]["report"]))
            else:
                assert False, self.error_msg.format("Unexpected WKT returned. Response: {0}.".format(response_json))
