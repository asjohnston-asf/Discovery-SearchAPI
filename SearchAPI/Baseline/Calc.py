from math import sqrt, cos, sin, radians
import numpy as np
import dateparser

# WGS84 constants
a = 6378137
f = pow((1.0 - 1 / 298.257224), 2)
# Technically f is normally considered to just be that 298... part but this is all we ever use, so
# pre-calc and cache and call it all f anyhow


def calculate_perpendicular_baselines(reference, stack):
    for product in stack:
        if None in [product['sv_t_pos_pre'], product['sv_t_pos_post'], product['sv_pos_pre'], product['sv_pos_post']]:
            product['noStateVectors'] = True
            continue

        asc_node_time = dateparser.parse(product['ascendingNodeTime']).timestamp()

        start = dateparser.parse(product['startTime']).timestamp()
        end = dateparser.parse(product['stopTime']).timestamp()
        center = start + ((end - start) / 2)
        product['relative_start_time'] = start - asc_node_time
        product['relative_center_time'] = center - asc_node_time
        product['relative_end_time'] = end - asc_node_time

        t_pre = dateparser.parse(product['sv_t_pos_pre']).timestamp()
        t_post = dateparser.parse(product['sv_t_pos_post']).timestamp()
        product['relative_sv_pre_time'] = t_pre - asc_node_time
        product['relative_sv_post_time'] = t_post - asc_node_time

    for product in stack:
        if product['granuleName'] == reference:
            reference = product
            reference['perpendicularBaseline'] = 0
            # Cache these values
            reference['granulePosition'] = get_granule_position(reference['centerLat'], reference['centerLon'])
            break

    for secondary in stack:
        if secondary.get('noStateVectors'):
            secondary['perpendicularBaseline'] = None
            continue

        shared_rel_time = get_shared_sv_time(reference, secondary)

        reference_shared_pos = get_pos_at_rel_time(reference, shared_rel_time)
        reference_shared_vel = get_vel_at_rel_time(reference, shared_rel_time)
        secondary_shared_pos = get_pos_at_rel_time(secondary, shared_rel_time)
        #secondary_shared_vel = get_vel_at_rel_time(secondary, shared_rel_time) # unused

        # need to get sat pos and sat vel at center time
        reference['alongBeamVector'] = get_along_beam_vector(reference_shared_pos, reference['granulePosition'])
        reference['upBeamVector'] = get_up_beam_vector(reference_shared_vel, reference['alongBeamVector'])

        perpendicular_baseline = get_paired_granule_baseline(
            reference['granulePosition'],
            reference['upBeamVector'],
            secondary_shared_pos)
        if abs(perpendicular_baseline) > 100000:
            perpendicular_baseline = None
        secondary['perpendicularBaseline'] = perpendicular_baseline

    return stack

# Convert granule center lat/lon to fixed earth coordinates in meters using WGS84 ellipsoid.
def get_granule_position(scene_center_lat, scene_center_lon):
    lat = radians(float(scene_center_lat))
    lon = radians(float(scene_center_lon))
    coslat = cos(lat) # This value gets used a couple times, cache it
    sinlat = sin(lat) # This value gets used a couple times, cache it
    C = 1.0 / (sqrt(pow(coslat, 2) + f * pow(sinlat, 2)))
    S = f * C
    aC = a * C
    granule_position = np.array([aC * coslat * cos(lon), aC * coslat * sin(lon), a * S * sinlat])
    return(granule_position)

# Calculate along beam vector from sat pos and granule pos
def get_along_beam_vector(satellite_position, granule_position):
    along_beam_vector = np.subtract(satellite_position, granule_position)
    along_beam_vector = np.divide(along_beam_vector, np.linalg.norm(along_beam_vector)) # normalize
    return(along_beam_vector)

# Calculate up beam vector from sat velocity and along beam vector
def get_up_beam_vector(satellite_velocity, along_beam_vector):
    up_beam_vector = np.cross(satellite_velocity, along_beam_vector)
    up_beam_vector = np.divide(up_beam_vector, np.linalg.norm(up_beam_vector)) # normalize
    return(up_beam_vector)

# Calculate baseline between reference and paired granule
def get_paired_granule_baseline(reference_granule_position, reference_up_beam_vector, paired_satellite_position):
    posd = np.subtract(paired_satellite_position, reference_granule_position)
    baseline = np.dot(reference_up_beam_vector, posd)
    return(int(round(baseline)))

# Find a relative orbit time covered by both granules' SVs
def get_shared_sv_time(reference, secondary):
    start = max(reference['relative_sv_pre_time'], secondary['relative_sv_pre_time'])
    end = max(reference['relative_sv_post_time'], secondary['relative_sv_post_time'])

    # Favor the start/end SV time of the reference so we can use that SV directly without interpolation
    if start == reference['relative_sv_pre_time']:
        return start
    if end == reference['relative_sv_post_time']:
        return end

    return start

# Interpolate a position SV based on relative time
def get_pos_at_rel_time(granule, relative_time):
    if relative_time == granule['relative_sv_pre_time']:
        return granule['sv_pos_pre']
    if relative_time == granule['relative_sv_post_time']:
        return granule['sv_pos_post']

    duration = granule['relative_sv_post_time'] - granule['relative_sv_pre_time']
    factor = (relative_time - granule['relative_sv_pre_time']) / duration

    vec_a = granule['sv_pos_pre']
    vec_b = granule['sv_pos_post']

    v = [
        interpolate(vec_a[0], vec_b[0], factor),
        interpolate(vec_a[1], vec_b[1], factor),
        interpolate(vec_a[2], vec_b[2], factor)]

    return radius_fix(granule, v, relative_time)

# Interpolate a velocity SV based on relative time
def get_vel_at_rel_time(granule, relative_time):
    if relative_time == granule['relative_sv_pre_time']:
        return granule['sv_vel_pre']
    if relative_time == granule['relative_sv_post_time']:
        return granule['sv_vel_post']

    duration = granule['relative_sv_post_time'] - granule['relative_sv_pre_time']
    factor = (relative_time - granule['relative_sv_pre_time']) / duration

    vec_a = granule['sv_vel_pre']
    vec_b = granule['sv_vel_post']

    v = [
        interpolate(vec_a[0], vec_b[0], factor),
        interpolate(vec_a[1], vec_b[1], factor),
        interpolate(vec_a[2], vec_b[2], factor)]

    return v

# convenience 1d linear interp
def interpolate(p0, p1, x):
    return (p0 * (1.0 - x)) + (p1 * x)

# Bump the provided sat pos out to a radius interpolated between the start and end sat pos vectors
def radius_fix(granule, sat_pos, relative_time):
    pre_l = np.linalg.norm(granule['sv_pos_pre'])
    post_l = np.linalg.norm(granule['sv_pos_post'])
    sat_pos_l = np.linalg.norm(sat_pos)
    dt = relative_time - granule['relative_sv_pre_time']
    new_l = pre_l + (post_l - pre_l) * dt / (granule['relative_sv_post_time'] - granule['relative_sv_pre_time'])
    sat_pos[0] = sat_pos[0] * new_l / sat_pos_l
    sat_pos[1] = sat_pos[1] * new_l / sat_pos_l
    sat_pos[2] = sat_pos[2] * new_l / sat_pos_l
    return sat_pos
