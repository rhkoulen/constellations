import json
import numpy as np
from typing import List, Optional, Tuple
import os
import argparse
import matplotlib.pyplot as plt

from visualization import show_layout

# Measurements

MOUNTING_PLATE_RAD = 110.0          # radius in which candidates must be fully bound (mm), the free area on the top integration plate
REAL_RR_BASE_RAD = 8.36             # the radius of the retroreflector mounting bases (mm)
RR_LIP_WIDTH = 2.0                  # width of the snap-in lip that the mounting base will snap into (mm), i want my thingy to look cool, if you're just doing to do an indent instead of a raised cup, 0.0 is fine
RR_BASE_RAD = REAL_RR_BASE_RAD + RR_LIP_WIDTH # effective radius of the retroreflector mounting bases (mm)
MOUNT_BOUNDS = (0, MOUNTING_PLATE_RAD - RR_BASE_RAD) # the range of radius coords that are valid for centers of retroreflectors

# Layout config

RETRIES = 100
NUM_RR_SLOTS = 12
ACTUAL_REQUIRED_SPACING = 14.0      # the REQUIRED spacing between retroreflectors
PREFERRED_ADDITIONAL_SPACING = 11.0 # any additional spacing you would prefer between retroreflectors (advisable not to make this negative)
MIN_RR_SPACING = 2*REAL_RR_BASE_RAD + ACTUAL_REQUIRED_SPACING + PREFERRED_ADDITIONAL_SPACING

# Utilities

def _convert_polar_to_euclidean(p_coords:np.ndarray):
    """
    Converts polar coordinates to euclidean coordinates.

    Args:
     - p_coords: np.ndarray(N,3); where [:, 0] are radii, [:, 1] are angles
    Returns:
     - e_coords: np.ndarray(N,3); where [:, 0] are x, [:, 1] are y
    """
    r = p_coords[:, [0]] # (N,1)
    theta = p_coords[:, [1]] # (N,1)

    x = r * np.cos(theta) # (N,1)
    y = r * np.sin(theta) # (N,1)
    e_coords = np.hstack([x, y])
    assert e_coords.shape == p_coords.shape

    return e_coords
def generate_random_points(num:int, max_rad:float=MOUNTING_PLATE_RAD - RR_BASE_RAD, seed:Optional[int]=None):
    """
    Generates random points in a disk in euclidean coordinates.

    Args:
     - num: int; the number of points to sample
     - max_rad: float; the radius of the disk to be sampling in
     - seed: int; passed into default_rng
    Returns:
     - e_coords: np.ndarray(N,2); the sampled points
    """
    rng = np.random.default_rng(seed)

    radii = max_rad * np.sqrt(rng.uniform(0, 1, (num, 1)))
    angles = rng.uniform(0, 2 * np.pi, (num, 1))

    p_coords = np.hstack([radii, angles])
    return _convert_polar_to_euclidean(p_coords)
def pairwise_dist(pts):
    diffs = pts[:, np.newaxis, :] - pts[np.newaxis, :, :]
    d = np.sqrt((diffs ** 2).sum(-1))
    return d

# Run

def main(num_retroreflector_slots):
    while True:
        # Find a good layout
        best_layout = None
        best_badness = np.inf # more positive means more bad
        for _ in range(RETRIES):
            # Generate a candidate layout
            while True:
                candidate_layout = generate_random_points(num_retroreflector_slots)
                pair_distances = pairwise_dist(candidate_layout)[np.triu_indices(n=candidate_layout.shape[0], k=1)]
                if (not np.any(pair_distances < MIN_RR_SPACING - PREFERRED_ADDITIONAL_SPACING)): break
            # Evaluate the layout
            spacing_violations = np.clip(MIN_RR_SPACING - pair_distances, 0, None) # penalize any pair that are too close
            spacing_badness = (spacing_violations ** 2).sum() * 10.0
            diversity_badness = -(pair_distances.std()) * 5.0
            badness = spacing_badness + diversity_badness
            if (best_badness > badness):
                best_badness = badness
                best_layout = candidate_layout
        # Ask the user which markers they'd like to elevate!
        layout_dict = {
            'plate_radius': MOUNTING_PLATE_RAD,
            'marker_radius': RR_BASE_RAD,
            'markers': [{'x':float(best_layout[i,0]), 'y':float(best_layout[i,1]), 'elevated':False} for i in range(best_layout.shape[0])],
        }
        with open(os.path.join('artifacts', 'temp.json'), 'w') as f:
            json.dump(layout_dict, f, indent=2)
        print('Here\'s a preview. Which ids would you like to elevate (comma separated)? You can also type "retry" to go again.')
        show_layout(os.path.join('artifacts', 'temp.json'))
        response = input()
        if response != 'retry':
            os.remove(os.path.join('artifacts', 'temp.json'))
            os.remove(os.path.join('artifacts', 'temp.png'))
            break
        else:
            plt.close()
    # Elevate those markers
    marker_ids = response.strip().split(',') # not really sanitized
    for id in marker_ids:
        i = int(id.strip())
        layout_dict['markers'][i]['elevated'] = True
    with open(os.path.join('artifacts', 'candidate_layout.json'), 'w') as f:
        json.dump(layout_dict, f, indent=2)
    print('Done.')
    show_layout(os.path.join('artifacts', 'candidate_layout.json'))

if __name__=='__main__':
    # New parser
    parser = argparse.ArgumentParser(description="CLI for generating constellation layout templates.")
    parser.add_argument('-n', '--num', type=int, default=NUM_RR_SLOTS, help='The number of retroreflector slots to put in the layout')
    # if I were a good dev I would put more args in this, just go edit the caps variables at the top
    args = parser.parse_args()
    main(args.num)