# SearchAPI

Search API for talking with CMR.

- [SearchAPI](#searchapi)
  - [First Time Setup](#first-time-setup)
  - [Starting the SearchAPI](#starting-the-searchapi)
  - [Developing](#developing)
  - [Testing](#testing)
    - [Setting up PytestAutomation](#setting-up-pytestautomation)
    - [Running the Tests](#running-the-tests)
  - [Production](#production)

## First Time Setup

If cloning for the first time, follow these steps to get all the requirements installed.

- Works for: Ubuntu, MacBook, and Windows subsystem for linux (Ubuntu app)).

1. Update your package list:

   ```bash
   sudo apt update
   ```

2. Install missing libraries from apt:

   ```bash
   sudo apt install python3-pip python3-testresources libgeos-dev
   ```

3. Clone a local copy of this repo:

   ```bash
   git clone git@github.com:asfadmin/Discovery-SearchAPI.git
   ```

   ```bash
   cd Discovery-SearchAPI
   ```

4. Create a virtual environment:

   ```bash
   virtualenv --python=python3 ~/SearchAPI-env
   ```

5. Activate the virtual environment:

   ```bash
   source ~/SearchAPI-env/bin/activate
   ```

   - If it works, you should see "(SearchAPI-env)" appear at the beginnning of your prompt.


6. Use pip to install requirements:

   ```bash
   pip install -r requirements.txt --update
   ```

   - At the time of this writing, in some situations you may encounter an SSL certificate error. If that happens, re-install pip using the following command and try step 4 again.

      ```bash
      curl https://bootstrap.pypa.io/get-pip.py | python
      ```

## Starting the SearchAPI

Once installed, this is how you run the api.

1. If not already started, activate the enviornment:

   ```bash
   source ~/SearchAPI-env/bin/activate
   ```

2. Run the dev server

   ```bash
   python application.py
   ```

## Developing

1. After making changes, pylint your code

   ```bash
   pylint --rcfile=pylintrc <changed files>
   ```

2. If you install new modules with pip, update requirements.txt:

   ```bash
   pip freeze > requirements.txt
   ```

## Testing

Testing is done using the [Discovery-PytestAutomation](https://github.com/asfadmin/Discovery-PytestAutomation) repo.

### Setting up PytestAutomation

   1. Clone the repository:

   ```bash
   git clone https://github.com/asfadmin/Discovery-PytestAutomation
   ```

### Running the Tests

1. Make sure you're in the PytestAutomation repo.

   ```bash
   cd Discovery-PytestAutomation
   ```

2. Run the suite.

   ```bash
   pytest {pytest flags here} . {PytestAutomation flags here}
   ```

   - See [here](https://github.com/asfadmin/Discovery-PytestAutomation) for filters/flags for PytestAutomation. (How to run specific tests, etc.)
   - See [here](https://github.com/asfadmin/Discovery-SearchAPI/tree/devel/yml_tests) for custom flags unique to this project, and how to write tests for the API.

## Production
To deploy to prod, merge changes to the prod branch.
