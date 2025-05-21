"""
This script is for educational and authorized testing only.
Unauthorized access to systems you do not own is illegal.

Author assumes no liability for any misuse or damage.
"""

from bruteforcer import BruteForcer
import utils
import sys
from utils import die



if __name__ == "__main__":

    args = utils.parse_args()

    print('⚠️ This is for local pentesting and educationnal use only. You are responsible for your actions and hacking is NOT encouraged. ⚠️\n')

    bf = BruteForcer(domain=args.domain)
    
    # function run will handle everything, from performing the checks, terminating the script...
    bf.run() 
