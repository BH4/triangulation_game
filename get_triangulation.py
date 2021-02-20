"""
Currently creates random vertices and shows a possible triangulation for them.
"""
import numpy as np
import matplotlib.pyplot as plt
from random import random, seed
from scipy.spatial import Delaunay
from itertools import combinations


def area(t, points):
    # Calculate area of triangle from its vertices
    p0 = points[t[0]]
    p1 = points[t[1]]
    p2 = points[t[2]]
    A = abs(p0[0]*(p1[1]-p2[1]) + p1[0]*(p2[1]-p0[1]) + p2[0]*(p0[1]-p1[1]))/2
    return A


def side_lengths(t, points):
    sl = []
    for ind in range(len(t)):
        p1 = points[t[ind]]
        p2 = points[t[(ind+1) % len(t)]]

        s = np.sqrt((p1[0]-p2[0])**2+(p1[1]-p2[1])**2)
        sl.append(s)
    return sl


def check_for_small_tri(tri, points, bad_const):
    bad_tri = []
    for t in tri:
        A = area(t, points)
        s = side_lengths(t, points)
        check = A/max(s)**2
        if check < bad_const:
            bad_tri.append(t)
    return bad_tri


def get_good_triangles(n, rand_seed=None, bad_const=0.03):
    """
    Make sure the ratio of the triangles area to the length of its longest side
    squared is greater than some constant.
    """
    if rand_seed is not None:
        seed(rand_seed)
    x = [random() for i in range(n)]
    y = [random() for i in range(n)]

    points = np.array(list(zip(x, y)))

    tri = Delaunay(points).simplices
    bad_tri = check_for_small_tri(tri, points, bad_const)
    check_removal = set()
    for t in bad_tri:
        check_removal |= set(t)
    # See if removing a single point from the bad triangles will make it so there are none.
    worked = len(bad_tri) == 0
    for r in check_removal:
        check_points = np.concatenate((points[:r], points[r+1:]))
        check_tri = Delaunay(check_points).simplices
        if len(check_for_small_tri(check_tri, check_points, bad_const)) == 0:
            points = check_points
            tri = check_tri
            worked = True
            break

    for rem_num in range(2, len(check_removal)):
        if not worked:
            for r in combinations(check_removal, 2):
                # check_points = np.concatenate((points[:r], points[r+1:]))
                check_points = np.delete(points, r, axis=0)
                check_tri = Delaunay(check_points).simplices
                if len(check_for_small_tri(check_tri, check_points, bad_const)) == 0:
                    points = check_points
                    tri = check_tri
                    worked = True
                    break
        if worked:
            break

    if not worked:
        print('Wasnt able to fix')
    return points, tri


if __name__ == '__main__':
    points, tri = get_good_triangles(30, rand_seed=154)
    plt.triplot(points[:, 0], points[:, 1], tri)

    plt.plot(points[:, 0], points[:, 1], 'o')
    for i, p in enumerate(points):
        plt.annotate(i, p)

    plt.show()
