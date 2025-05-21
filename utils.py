import sys
from pprint import pprint

# Alias cuz FI
def die():
    sys.exit()



# Returns the domain we will work on.
# Get domain from CLI or prompt to user if not directly specified.
# Also prepend the protocol if needeed
def get_domain():
    if len(sys.argv) > 1:
        domain = sys.argv[1]
    else:
        domain = input("Enter the domain (e.g. example.com): ").strip()
    return normalize_domain(domain)


# Prepend the protocol to the domain if not already specified. HTTPS by default.
def normalize_domain(domain):
    if not domain.startswith("http://") and not domain.startswith("https://"):
        return "https://" + domain  # default to HTTPS
    return domain

# print for objects
def dump(var):
    pprint(vars(var))