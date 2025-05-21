"""
This script is for educational and authorized testing only.
Unauthorized access to systems you do not own is illegal.

Author assumes no liability for any misuse or damage.
"""

from bruteforcer import BruteForcer
import utils
from utils import die

if __name__ == "__main__":

    domain = utils.get_domain()
    bf = BruteForcer(domain)
    
    # function run will handle everything, from performing the checks, terminating the script...
    bf.run() 
