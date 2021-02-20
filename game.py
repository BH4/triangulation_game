"""
To do:
Triangles be behind numbers and circles. And numbers and circles need to be different color.
Allow zoom and pan
"""

from get_triangulation import get_good_triangles
from collections import defaultdict
import numpy as np
import matplotlib.pyplot as plt
from copy import deepcopy
import tkinter as tk
from random import randint


def distance(p1, p2):
    return np.sqrt((p1[0]-p2[0])**2+(p1[1]-p2[1])**2)


def triangle_points_to_edges(t):
    edges = []
    for i in range(len(t)):
        edge = tuple(sorted([t[i], t[(i+1) % len(t)]]))
        edges.append(edge)
    return edges


class triangulation:
    def __init__(self, lvl_seed, n=30, verbose=False):
        # The number of points used can be less than n.
        self.verbose = verbose
        self.points = None
        self.triangles = None

        points, tri = get_good_triangles(n, rand_seed=lvl_seed, bad_const=0.03)

        # Data that will remain in the same order
        self.points = points
        self.triangles = tri
        self.tri_ids = []

        self.edge_count = defaultdict(int)
        self.shown_edges = []
        self.edge_ids = []
        self.remaining_edges = []  # deepcopy(self.edge_count)
        self.vertex_id_list = []
        self.text_ids = []

        # begin filling data
        self.edge_to_triangle = defaultdict(list)
        used_edges = set()
        for ind, t in enumerate(tri):
            # for i in range(len(t)):
            #    edge = tuple(sorted([t[i], t[(i+1) % len(t)]]))
            for edge in triangle_points_to_edges(t):
                self.edge_to_triangle[edge].append(ind)
                if edge not in used_edges:
                    used_edges.add(edge)
                    self.edge_count[edge[0]] += 1
                    self.edge_count[edge[1]] += 1
        self.remaining_edges = deepcopy(self.edge_count)

        # Set up graphics
        self.root = tk.Tk()
        self.setup()
        self.root.after(1, self.loop)
        self.root.mainloop()

    def show_solution(self):
        plt.triplot(self.points[:, 0], self.points[:, 1], self.triangles)

        plt.plot(self.points[:, 0], self.points[:, 1], 'o')
        for i, p in enumerate(self.points):
            ec = self.edge_count[i]
            plt.annotate(ec, p)

        plt.show()

    def scale_point(self, p):
        return (p[0]*self.canvas_width, p[1]*self.canvas_height)

    def show_nums(self):
        for i in range(len(self.remaining_edges)):
            x, y = self.scale_point(self.points[i])
            my_id = self.canvas.create_text(x, y, text=str(self.remaining_edges[i]), font="Times 7 bold")
            self.text_ids.append(my_id)

    def update_nums(self):
        for i in range(len(self.text_ids)):
            my_id = self.text_ids[i]
            num = self.remaining_edges[i]
            self.canvas.itemconfigure(my_id, text=str(num))

    def check_completed_triangles(self, edge):
        triangle_inds = self.edge_to_triangle[edge]
        if self.verbose:
            print('That edge belongs to these triangles:', triangle_inds)
        for ind in triangle_inds:
            edges = triangle_points_to_edges(self.triangles[ind])
            if all([(e in self.shown_edges) for e in edges]):
                # turn on this triangle
                rand_color = randint(1, 128)
                hex_str = '#'+hex(rand_color)[2:]*3
                self.canvas.itemconfig(self.tri_ids[ind], fill=hex_str)

    def draw_circle(self, center, radius):
        x0 = center[0]-radius
        x1 = center[0]+radius
        y0 = center[1]-radius
        y1 = center[1]+radius
        my_id = self.canvas.create_oval(x0, y0, x1, y1)
        return my_id

    def draw_triangle(self, vertex_inds):
        """
        Needs to be set to invisible initially.
        """
        points = []
        for ind in vertex_inds:
            p = self.scale_point(self.points[ind])
            points.append(p[0])
            points.append(p[1])

        my_id = self.canvas.create_polygon(points, fill='')
        return my_id

    def draw_line(self, p1, p2):
        my_id = self.canvas.create_line(p1[0], p1[1], p2[0], p2[1])
        return my_id

    def setup(self):
        self.canvas_height = 600
        self.canvas_width = 600
        self.canvas = tk.Canvas(self.root, bg="white", width=self.canvas_width, height=self.canvas_height)
        # Give the canvas keyboard focus when clicked. So key presses can fire events.
        self.canvas.focus_set()
        self.canvas.bind("<ButtonPress-1>", self.click)
        self.canvas.bind("<B1-Motion>", self.drag)
        self.canvas.bind("<BackSpace>", self.undo)
        self.canvas.pack()

        circle_radius = 5
        for pos in self.points:
            center = (pos[0]*self.canvas_width, pos[1]*self.canvas_height)
            my_id = self.draw_circle(center, circle_radius)
            self.vertex_id_list.append(my_id)

        self.selected = []

        for t in self.triangles:
            my_id = self.draw_triangle(t)
            self.tri_ids.append(my_id)

        self.show_nums()

    def click(self, event):
        click_pos = (event.x/self.canvas_width, event.y/self.canvas_height)
        dist = [distance(click_pos, x) for x in self.points]
        z = sorted(zip(dist, list(range(len(self.points)))))
        closest = z[0]
        if closest[0] < .03:
            my_id = self.vertex_id_list[closest[1]]
            self.canvas.itemconfig(my_id, fill="blue")

            if len(self.selected) == 0:
                self.selected.append(closest[1])
            else:
                other = self.selected[0]
                # clear selection
                self.selected = []
                self.canvas.itemconfig(my_id, fill="white")
                self.canvas.itemconfig(self.vertex_id_list[other], fill="white")

                edge = tuple(sorted([other, closest[1]]))

                if edge not in self.shown_edges and edge[0] != edge[1]:
                    self.shown_edges.append(edge)
                    p1 = self.scale_point(self.points[edge[0]])
                    p2 = self.scale_point(self.points[edge[1]])
                    line_id = self.draw_line(p1, p2)
                    self.edge_ids.append(line_id)

                    self.remaining_edges[edge[0]] -= 1
                    self.remaining_edges[edge[1]] -= 1
                    self.update_nums()

                    self.check_completed_triangles(edge)

    def undo(self, event):
        """
        Remove the most recent shown edge.

        - This means the edge needs to be deleted.
        - Fix the arrays this changed.
        - Increase the number of remaining edges.
        - Make any triangles that showed up transparent again.
        """
        if self.verbose:
            print('Trying to undo!!!')
        edge = self.shown_edges.pop(-1)

        edge_id = self.edge_ids.pop(-1)
        self.canvas.delete(edge_id)

        self.remaining_edges[edge[0]] += 1
        self.remaining_edges[edge[1]] += 1
        self.update_nums()

        # Any triangle which just had an edge removed will be transparent.
        # Even if it was already transparent.
        triangle_inds = self.edge_to_triangle[edge]
        for ind in triangle_inds:
            self.canvas.itemconfig(self.tri_ids[ind], fill='')

    def drag(self, event):
        # pan
        pass

    def loop(self):
        self.root.after(1, self.loop)


if __name__ == '__main__':
    g = triangulation(57, verbose=False)
    # g.show_solution()
