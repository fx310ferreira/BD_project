Installation Process
2.1 Environment Setup:

Ensure that you have Python installed on your system. You can download Python from the official website: https://www.python.org/downloads/
Verify that pip, the package installer for Python, is also installed. You can check if pip is installed by running the following command in your terminal:
$ pip --version
If pip is not installed, you can install it by following the instructions provided on the official Python website.

2.3 Install Dependencies:

Open your terminal, navigate to the project directory, and execute the following command to install the required dependencies:

$ pip install -r requirements.txt
This command will install all the dependencies listed in the requirements.txt file.
Database Configuration

Make sure the .env refered above is created as instructed.

Open your terminal, navigate to the project directory, and execute the following command to start the Flask development server:
ruby
Copy code
$ python bdproj.py
The Flask development server will start, and your REST API will be accessible at the specified URL (e.g., http://localhost:8080).