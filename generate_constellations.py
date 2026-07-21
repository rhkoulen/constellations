import json
import numpy as np
import os
import argparse
from visualization import show_constellations
from itertools import permutations, combinations


def constellation_distance(constellation_1, constellation_2):
    """
    Distance metric between two configurations of N indistinguishable retroreflective markers (ignoring the elevation because im not good at math)

    Constellation distance is relatively well defined when the markers have a correspondence. We don't have a correspondence.
    This code simply iterates over all possible correspondences. This is O(N!)!!!
    I read that you can do iterative closest point to search the permutation space, but I'm only doing 6 (720 perms), so I don't wanna. Make a fork :p
    
    Args:
     - constellation_1: np.ndarray(N,2); points as rows
     - constellation_2: np.ndarray(N,2); points as rows
    Returns:
     - distance: a "metric" between the two constellations
    """
    def kabsch_2d_no_reflection(P, Q):
        """
        Find the optimal proper rotation R (2x2, det(R) = +1) that rotates
        centered point set P onto centered point set Q, minimizing RMSD.

        Args:
         - P: np.ndarray(N,2); points as rows
         - Q: np.ndarray(N,2); points as rows
           - These need to be centered arrays.
           - This also assumes these points are correspondent.
        Returns:
         - R: np.ndarray(2, 2); rotation matrix such that P @ R.T best approximates Q
         - rmsd : root-mean-square distance between P @ R.T and Q after alignment
        """
        H = P.T @ Q                      # 2x2 cross-covariance
        U, S, Vt = np.linalg.svd(H)
        V = Vt.T

        # Since we don't have 4 spatial dimensions, it's not possible to get a mirror image of the constellation.
        # Reflection guard: force det(R) = +1 (proper rotation only)
        d = np.sign(np.linalg.det(V @ U.T))
        if d == 0: d = 1.0  # degenerate case, those who nose
    
        R = V @ np.diag([1.0, d]) @ U.T
        P_rot = P @ R.T
    
        rmsd = np.sqrt(np.mean(np.sum((P_rot - Q) ** 2, axis=1)))
        return R, rmsd

    assert constellation_1.shape == constellation_2.shape, f"Must be the same shape, {constellation_1.shape} =/= {constellation_2.shape}"

    c1_centered = constellation_1 - constellation_1.mean(axis=0)
    c2_centered = constellation_2 - constellation_2.mean(axis=0)

    best_rmsd = np.inf
    for perm in permutations(range(constellation_1.shape[0])):
        c2_centered_permuted = c2_centered[list(perm)]
        _, rmsd = kabsch_2d_no_reflection(c1_centered, c2_centered_permuted)
        best_rmsd = min(best_rmsd, rmsd)
    return best_rmsd

def greedy_maxmin(D:np.ndarray, M:int):
    """
    Greedy farthest-point insertion. 2-approximation for max-min dispersion.
    
    Args:
     - D: np.ndarray(N, N); pairwise distances
     - M: int; number of points to pick (ideally M<<N)
    Returns:
     - selected: List[int]; a list of indices to D indicating the max-min
    """
    # TODO: I could improve this search with a clique solver or local search to a true min? i don't mind the greedy soln for now
    N = D.shape[0]
    i, j = np.unravel_index(np.argmax(D), D.shape)
    selected = [int(i), int(j)]
    remaining = set(range(N)) - set(selected)
 
    while len(selected) < M:
        # for each candidate, its score is the min distance to the selected set
        best, best_score = None, -np.inf
        for c in remaining:
            score = D[c, selected].min()
            if score > best_score:
                best, best_score = c, score
        selected.append(best)
        remaining.remove(best)
 
    return selected



def main(args):
    with open(args.json_path, 'r') as f:
        data = json.load(f)

    # Confirm args
    num_total = args.num_elevated + args.num_normal
    if (num_total >= 9): print(f'WARNING: Watch out buster, my terrible distance metric is O(N!), and your constellations are N={num_total}')

    elevated_slots, normal_slots = [], []
    for i, marker in enumerate(data['markers']):
        if marker['elevated']: elevated_slots.append(i)
        else: normal_slots.append(i)
    assert len(elevated_slots) >= args.num_elevated, f'There are not enough elevated slots ({len(elevated_slots)}) for {args.num_elevated} elevated markers.'
    assert len(normal_slots) >= args.num_normal, f'There are not enough normal slots ({len(normal_slots)}) for {args.num_normal} normal markers.'

    # Construct all constellations with the specified number of elevated and normal slots.
    all_constellations = []
    for elevated_set in combinations(elevated_slots, args.num_elevated):
        for normal_set in combinations(normal_slots, args.num_normal):
            all_constellations.append(list(elevated_set) + list(normal_set))
    if (len(all_constellations) >= 10000): print(f'WARNING: There are a lot of valid constellations for your layout {all_constellations}, and we are now going to do an expensive pairwise distance...')

    # Do pairwise distance between the constellations.
    pairwise_dist = np.zeros((len(all_constellations), len(all_constellations)))
    for i in range(len(all_constellations)):
        for j in range(i+1, len(all_constellations)):
            constellation_1 = np.array([[data['markers'][marker_ind]['x'], data['markers'][marker_ind]['y']] for marker_ind in all_constellations[i]])
            constellation_2 = np.array([[data['markers'][marker_ind]['x'], data['markers'][marker_ind]['y']] for marker_ind in all_constellations[j]])
            d = constellation_distance(constellation_1, constellation_2)
            pairwise_dist[i,j] = d
            pairwise_dist[j,i] = d
            print(f'[{i}, {j}] = {d}')

    # Now, find the most isolated subset of constellations.
    selected_constellations = greedy_maxmin(pairwise_dist, args.num_constellations)
    constellation_dict = {
        'num_elevated': args.num_elevated,
        'num_normal': args.num_normal,
        'constellations': [all_constellations[i] for i in selected_constellations]
    }
    with open(os.path.join('artifacts', 'candidate_constellations.json'), 'w') as f:
        json.dump(constellation_dict, f, indent=2)
    print('Done.')
    show_constellations(args.json_path, os.path.join('artifacts', 'candidate_constellations.json'))


if __name__=='__main__':
    # New parser
    parser = argparse.ArgumentParser(description='CLI for generating constellations.')
    parser.add_argument("json_path", type=str, help='Path to the layout json.')
    parser.add_argument("num_constellations", type=int, help='The number of constellations to generate from that layout.')
    parser.add_argument("num_elevated", type=int, help='The number of markers to be put in elevated slots.')
    parser.add_argument("num_normal", type=int, help='The number of markers to be put in normal low slots.')
    args = parser.parse_args()
    main(args)
