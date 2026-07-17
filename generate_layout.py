import json
import numpy as np
from typing import List, Optional, Tuple

# Measurements

MOUNTING_PLATE_RAD = 110.0          # radius in which candidates must be fully bound (mm), the free area on the top integration plate
RAISED_PLATE_RAD = 30.0             # radius in which raised candidates must be fully bound (mm), the free area on the raised section of the print
RAISED_PLATE_HEIGHT = 20.0          # Z height of the raised section of the print (mm)
REAL_RR_BASE_RAD = 8.36             # the radius of the retroreflector mounting bases (mm)
RR_LIP_WIDTH = 2.0                  # width of the snap-in lip that the mounting base will snap into (mm), i want my thingy to look cool, if you're just doing to do an indent instead of a raised cup, 0.0 is fine
RR_BASE_RAD = REAL_RR_BASE_RAD + RR_LIP_WIDTH # effective radius of the retroreflector mounting bases (mm)
RAISED_BOUNDS = (0, RAISED_PLATE_RAD - RR_BASE_RAD) # the range of radius coords that are valid for centers of raised retroreflectors
OUTER_BOUNDS = (RAISED_PLATE_RAD + RR_BASE_RAD, MOUNTING_PLATE_RAD - RR_BASE_RAD) # the range of radius coords that are valid for centers of outer retroreflectors

# Layout config

N_RAISED = 3                        # number of retroreflectors to go in the central raised plate
N_OUTER = 9                         # number of retroreflectors to go around it
ACTUAL_REQUIRED_SPACING = 14.0      # the REQUIRED spacing between retroreflectors
PREFERRED_ADDITIONAL_SPACING = 11.0 # any additional spacing you would prefer between retroreflectors (advisable not to make this negative)
MIN_RR_SPACING = ACTUAL_REQUIRED_SPACING

# Utilities

def convert_cylindrical_to_euclidean(c_coords:np.ndarray):
    """
    Converts cylindrical coordinates to euclidean coordinates.

    Args:
     - c_coords: np.ndarray(N,3); where [:, 0] are radii, [:, 1] are angles, [:, 2] are z
    Returns:
     - e_coords: np.ndarray(N,3); where [:, 0] are x, [:, 1] are y, [:, 2] are z
    """
    r = c_coords[:, [0]] # (N,1)
    theta = c_coords[:, [1]] # (N,1)
    z = c_coords[:, [2]] # (N,1)

    x = r * np.cos(theta) # (N,1)
    y = r * np.sin(theta) # (N,1)
    e_coords = np.hstack([x, y, z])
    assert e_coords.shape == c_coords.shape

    return e_coords
def generate_random_points(num:int, r_range:Tuple[float], z_value:float, seed:Optional[int]=None):
    """
    Generates candidates in cylindrical coordinates.
    NOTE: this is not geodesically uniformly random, it's uniform over the r,theta space, so it's gonna be thinner farther out
    I'm just lazy.

    Args:
     - num: int; the number of points to sample
     - r_range: List; a two element tuple denoting the low and high range for the radius
     - z_value: float; the shared z_value among all points
     - seed: int; passed into default_rng
    Returns:
     - c_coords: np.ndarray(N,3); the cylindrically sampled points
    """
    rng = np.random.default_rng(seed)

    radii = rng.uniform(r_range[0], r_range[1], (num, 1))
    angles = rng.uniform(0, 2 * np.pi, (num, 1))
    z = np.full((num, 1), z_value)

    c_coords = np.hstack([radii, angles, z])
    return c_coords
def generate_optimal_points(num:int, r_value:float, z_value:float):
    """
    The best case for intermarker distance is a circle with evenly spaced members.

    Args:
     - num: int; the number of points to sample
     - r_value: float; the radius of the ring
     - z_value: float; the shared z_value among all points
    Returns:
     - c_coords: np.ndarray(N,3); the ring of points
    """
    radii = np.fill((num, 1), r_value)
    angles = np.linspace(0, 2 * np.pi, num=num, endpoint=False).reshape((-1, 1))
    z = np.full((num, 1), z_value)

    c_coords = np.hstack([radii, angles, z])
    return c_coords
def pairwise_dist(pts):
    diffs = pts[:, None, :] - pts[None, :, :]
    d = np.sqrt((diffs ** 2).sum(-1))
    return d

# Run

def main():
    pass

if __name__=='__main__': main()