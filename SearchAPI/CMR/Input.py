import dateparser
import re
from WKTUtils.Input import parse_wkt_util

# Parse and validate a string: "abc"
def parse_string(v):
    if not len(v) > 0:
        raise ValueError(f'Invalid string: Empty string: {v}')
    try:
        return f'{v}'
    except ValueError as e: # If this happens, the following line would fail as well...
        raise ValueError(f'Invalid string: {v}') from e

# Parse and validate an int: "10"
def parse_int(v):
    try:
        return int(v)
    except ValueError as e:
        raise ValueError(f'Invalid int: {v}') from e

# Parse and validate a float: "1.2"
def parse_float(v):
    try:
        return float(v)
    except ValueError as e:
        raise ValueError(f'Invalid number: {v}') from e

# Parse and validate a date: "1991-10-01T00:00:00Z"
def parse_date(v):
    d = dateparser.parse(v)
    if d is None:
        raise ValueError(f'Invalid date: {v}')
    return dateparser.parse(v).strftime('%Y-%m-%dT%H:%M:%SZ')

# Parse and validate a date range: "1991-10-01T00:00:00Z,1991-10-02T00:00:00Z"
def parse_date_range(v):
    dates = v.split(',')
    if len(dates) != 2:
        raise ValueError('Invalid date range: must be two comma-separated dates')
    return f'{parse_date(dates[0])},{parse_date(dates[1])}'

# Parse and validate a numeric value range, using h() to validate each value: "3-5", "1.1-12.3"
def parse_range(v, h):
    try:
        v = v.replace(' ', '')
        m = re.search(r'^(-?\d+(\.\d*)?)-(-?\d+(\.\d*)?)$', v)
        if m is None:
            raise ValueError(f'Invalid range: {v}')
        a = [h(m.group(1)), h(m.group(3))]
        if a[0] > a[1]:
            raise ValueError()
        if a[0] == a[1]:
            a = a[0]
    except ValueError as e:
        raise ValueError(f'Invalid range: {e}') from e
    return a

# Parse and validate an integer range: "3-5"
def parse_int_range(v):
    try:
        return parse_range(v, parse_int)
    except ValueError as e:
        raise ValueError(f'Invalid int range: {e}') from e

# Parse and validate a float range: "1.1-12.3"
def parse_float_range(v):
    try:
        return parse_range(v, parse_float)
    except ValueError as e:
        raise ValueError(f'Invalid float range: {e}') from e

# Parse and validate a list of values, using h() to validate each value: "a,b,c", "1,2,3", "1.1,2.3"
def parse_list(v, h):
    try:
        return [h(a) for a in v.split(',')]
    except ValueError as e:
        raise ValueError(f'Invalid list: {e}') from e

# Parse and validate a list of strings: "foo,bar,baz"
def parse_string_list(v):
    try:
        return parse_list(v, parse_string)
    except ValueError as e:
        raise ValueError(f'Invalid string list: {e}') from e

# Parse and validate a list of integers: "1,2,3"
def parse_int_list(v):
    try:
        return parse_list(v, parse_int)
    except ValueError as e:
        raise ValueError(f'Invalid int list: {e}') from e

# Parse and validate a list of floats: "1.1,2.3,4.5"
def parse_float_list(v):
    try:
        return parse_list(v, parse_float)
    except ValueError as e:
        raise ValueError(f'Invalid float list: {e}') from e

# Parse and validate a number or a range, using h() to validate each value: "1", "4.5", "3-5", "10.1-13.4"
def parse_number_or_range(v, h):
    try:
        m = re.search(r'^(-?\d+(\.\d*)?)$', v)
        if m is not None:
            return h(v)
        return parse_range(v, h)
    except ValueError as e:
        raise ValueError(f'Invalid number or range: {e}') from e

# Parse and validate a list of numbers or number ranges, using h() to validate each value: "1,2,3-5", "1.1,1.4,5.1-6.7"
def parse_number_or_range_list(v, h):
    try:
        v = v.replace(' ', '')
        return [parse_number_or_range(x, h) for x in v.split(',')]
    except ValueError as e:
        raise ValueError(f'Invalid number or range list: {e}') from e

# Parse and validate a list of integers or integer ranges: "1,2,3-5"
def parse_int_or_range_list(v):
    try:
        return parse_number_or_range_list(v, parse_int)
    except ValueError as e:
        raise ValueError(f'Invalid int or range list: {e}') from e

# Parse and validate a list of float or float ranges: "1.0,2.0,3.0-5.0"
def parse_float_or_range_list(v):
    try:
        return parse_number_or_range_list(v, parse_float)
    except ValueError as e:
        raise ValueError(f'Invalid float or range list: {e}') from e

# Parse and validate a coordinate string
def parse_coord_string(v):
    v = v.split(',')
    for c in v:
        try:
            float(c)
        except ValueError as e:
            raise ValueError(f'Invalid coordinate: {c}') from e
    if len(v) % 2 != 0:
        raise ValueError(f'Invalid coordinate list, odd number of values provided: {v}')
    return ','.join(v)

# Parse and validate a bbox coordinate string
def parse_bbox_string(v):
    try:
        v = parse_coord_string(v)
    except ValueError as e:
        raise ValueError(f'Invalid bbox: {e}') from e
    if len(v.split(',')) != 4:
        raise ValueError(f'Invalid bbox, must be 4 values: {v}')
    return v

# Parse and validate a point coordinate string
def parse_point_string(v):
    try:
        v = parse_coord_string(v)
    except ValueError as e:
        raise ValueError(f'Invalid point: {e}') from e
    if len(v.split(',')) != 2:
        raise ValueError(f'Invalid point, must be 2 values: {v}')
    return v

# Parse a WKT and convert it to a coordinate string
# NOTE: If given an empty ("POINT EMPTY") shape, will return "point:". Should it throw instead?
def parse_wkt(v):
    # The utils library needs this function for repairWKT.
    return parse_wkt_util(v)
