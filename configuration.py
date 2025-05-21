import configparser

conf = configparser.ConfigParser()
conf.read('config.conf')

# Function to handle values and types
def convert_type(value):
    # Try to cast to boolean
    if value.lower() in ("true", "yes", "on"):
        return True
    if value.lower() in ("false", "no", "off"):
        return False

    # Try to cast to int
    try:
        return int(value)
    except ValueError:
        pass

    # Try to cast to float
    try:
        return float(value)
    except ValueError:
        pass

    # Default: return as string
    return value


def getConf(param):
    try:
        section, key = param.split('.', 1)
        raw_value = conf[section][key]
        return convert_type(raw_value)
    except ValueError:
        raise ValueError("Parameter must be in the format 'section.key'")
    except KeyError as e:
        raise KeyError(f"Configuration '{param}' not found: {e}")