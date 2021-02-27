from get_triangulation import get_good_triangles
from collections import defaultdict
import numpy as np
from copy import deepcopy
import tkinter as tk
from random import randint, random


def distance(p1, p2):
    return np.sqrt((p1[0]-p2[0])**2+(p1[1]-p2[1])**2)


def triangle_points_to_edges(t):
    edges = []
    for i in range(len(t)):
        edge = tuple(sorted([t[i], t[(i+1) % len(t)]]))
        edges.append(edge)
    return edges


class triangulation(tk.Frame):
    def __init__(self, lvl_seed=randint(0, 10**8), n=30, grayscale=True, verbose=False, auto_solve=False):
        print('Level seed:', lvl_seed)

        self.root = tk.Tk()
        tk.Frame.__init__(self, self.root)
        # The number of points used can be less than n.
        self.verbose = verbose
        self.points = None
        self.triangles = None
        self.grayscale = grayscale
        self.auto_solve = auto_solve

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

        # Coloration
        if not grayscale:
            self.color_pattern = [random(), random(), random()]
            s = sum(self.color_pattern)
            self.color_pattern = [x/s for x in self.color_pattern]
            self.color_origin = [random(), random()]
            self.color_edge_dist = max([distance(p, self.color_origin) for p in self.points])

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
        self.setup()
        self.root.after(1, self.loop)
        self.root.mainloop()

    def show_solution(self):
        for t in self.triangles:
            for e in triangle_points_to_edges(t):
                self.selection_event(e[0])
                self.selection_event(e[1])

    def scale_point(self, p):
        # This function only scales the points down to a 0-1 by 0-1 grid.
        # The scale here is unrelated to the zoom.
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

    def check_completed_vertex(self, ind):
        point_done = True
        for i, t in enumerate(self.triangles):
            if ind in t:
                f_color = self.canvas.itemcget(self.tri_ids[i], 'fill')
                if len(f_color) == 0:
                    point_done = False
                    return point_done

        my_id = self.vertex_id_list[ind]
        my_num_id = self.text_ids[ind]
        self.canvas.tag_lower(my_num_id)
        self.canvas.tag_lower(my_id)
        self.canvas.itemconfigure(my_num_id, fill='white')
        self.canvas.itemconfigure(my_id, outline='white')
        return point_done

    def check_completed_triangles(self, edge):
        triangle_inds = self.edge_to_triangle[edge]
        if self.verbose:
            print('That edge belongs to these triangles:', triangle_inds)
        for ind in triangle_inds:
            edges = triangle_points_to_edges(self.triangles[ind])
            if all([(e in self.shown_edges) for e in edges]):
                # Turn on this triangle
                if self.grayscale:
                    rand_color = randint(30, 128)
                    hex_str = '#'+hex(rand_color)[2:]*3
                else:
                    tri_center = self.triangle_centroid(self.triangles[ind])
                    dist = distance(self.color_origin, tri_center)
                    dist_ratio = dist/self.color_edge_dist
                    my_color = [int(255*dist_ratio*x) for x in self.color_pattern]
                    hex_str = '#'
                    for x in my_color:
                        h = hex(x)[2:]
                        if len(h) == 1:
                            h = '0'+h
                        hex_str += h


                self.canvas.itemconfig(self.tri_ids[ind], fill=hex_str)

                # Check each vertex connected to the triangle
                for v in self.triangles[ind]:
                    self.check_completed_vertex(v)

    def draw_circle(self, center, radius):
        x0 = center[0]-radius
        x1 = center[0]+radius
        y0 = center[1]-radius
        y1 = center[1]+radius
        my_id = self.canvas.create_oval(x0, y0, x1, y1, fill='white')
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

    def triangle_centroid(self, tri):
        tri_center = [0, 0]
        for p in tri:
            pi = self.points[p]
            tri_center[0] += pi[0]
            tri_center[1] += pi[1]
        tri_center[0] /= 3
        tri_center[1] /= 3
        return tri_center

    def draw_line(self, p1, p2):
        my_id = self.canvas.create_line(p1[0], p1[1], p2[0], p2[1])
        self.canvas.tag_lower(my_id)
        return my_id

    def setup(self):
        self.canvas_height = 600
        self.canvas_width = 600
        self.canvas = tk.Canvas(self.root, bg="white", width=self.canvas_width, height=self.canvas_height)
        # Scrolling
        self.xsb = tk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)
        self.ysb = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.ysb.set, xscrollcommand=self.xsb.set)
        self.canvas.configure(scrollregion=(-400, -400, 1000, 1000))
        self.xsb.grid(row=1, column=0, sticky="ew")
        self.ysb.grid(row=0, column=1, sticky="ns")
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        # Give the canvas keyboard focus when clicked. So key presses can fire events.
        self.canvas.focus_set()
        self.canvas.bind("<ButtonPress-1>", self.click)
        self.canvas.bind("<ButtonRelease-1>", self.click)
        self.canvas.bind("<B1-Motion>", self.drag)
        self.canvas.bind("<ButtonPress-3>", self.undo)
        # windows scroll
        self.canvas.bind("<MouseWheel>", self.zoomer)
        self.scale = 1
        self.canvas.pack()

        for t in self.triangles:
            my_id = self.draw_triangle(t)
            self.tri_ids.append(my_id)

        circle_radius = 5
        for pos in self.points:
            center = (pos[0]*self.canvas_width, pos[1]*self.canvas_height)
            my_id = self.draw_circle(center, circle_radius)
            self.vertex_id_list.append(my_id)

        self.show_nums()

        self.selected = []
        self.current_line_id = None
        self.last_click = None

        if self.auto_solve:
            self.show_solution()

    def selection_event(self, vertex_ind):
        my_id = self.vertex_id_list[vertex_ind]
        self.canvas.itemconfig(my_id, fill="blue")

        if len(self.selected) == 0:
            self.selected.append(vertex_ind)
            p = self.scale_point(self.points[vertex_ind])
            self.current_line_id = self.draw_line(p, p)
        else:
            self.canvas.delete(self.current_line_id)
            self.current_line_id = None

            other = self.selected[0]
            # clear selection
            self.selected = []
            self.canvas.itemconfig(my_id, fill="white")
            self.canvas.itemconfig(self.vertex_id_list[other], fill="white")

            edge = tuple(sorted([other, vertex_ind]))

            if edge not in self.shown_edges and edge[0] != edge[1]:
                self.shown_edges.append(edge)
                p1 = [v*self.scale for v in self.scale_point(self.points[edge[0]])]
                p2 = [v*self.scale for v in self.scale_point(self.points[edge[1]])]
                line_id = self.draw_line(p1, p2)
                self.edge_ids.append(line_id)

                self.remaining_edges[edge[0]] -= 1
                self.remaining_edges[edge[1]] -= 1
                self.update_nums()

                self.check_completed_triangles(edge)

    def click(self, event):
        x = self.canvas.canvasx(event.x)/self.scale
        y = self.canvas.canvasy(event.y)/self.scale
        click_pos = (x/self.canvas_width, y/self.canvas_height)
        dist = [distance(click_pos, x) for x in self.points]
        z = sorted(zip(dist, list(range(len(self.points)))))
        closest = z[0]
        if closest[0] < .03 or len(self.selected) == 1:
            self.selection_event(closest[1])
        else:
            self.canvas.scan_mark(event.x, event.y)

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

            # Any triangle which just became transparent (or already was) will
            # have vertices that need to be on top instead of hidden at the
            # bottom.
            for v in self.triangles[ind]:
                my_id = self.vertex_id_list[v]
                my_num_id = self.text_ids[v]
                self.canvas.tag_raise(my_id)
                self.canvas.tag_raise(my_num_id)
                self.canvas.itemconfigure(my_num_id, fill='black')
                self.canvas.itemconfigure(my_id, outline='black')

    def drag(self, event):
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        if len(self.selected) == 1:
            p1 = self.scale_point(self.points[self.selected[0]])
            p2 = (x, y)
            self.canvas.coords(self.current_line_id, p1[0]*self.scale, p1[1]*self.scale, p2[0], p2[1])
        else:
            self.canvas.scan_dragto(event.x, event.y, gain=1)

    # windows zoom
    def zoomer(self, event):
        # x = self.canvas.canvasx(event.x)
        # y = self.canvas.canvasy(event.y)
        # Coordinates get too messed up when zooming from mouse.
        x = 0
        y = 0
        if (event.delta > 0):
            self.canvas.scale("all", x, y, 1.1, 1.1)
            self.scale *= 1.1
        elif (event.delta < 0):
            self.canvas.scale("all", x, y, 0.9, 0.9)
            self.scale *= 0.9
        bb = self.canvas.bbox("all")
        new_bb = (bb[0]-500, bb[1]-500, bb[2]+500, bb[3]+500)
        self.canvas.configure(scrollregion=new_bb)

    def loop(self):
        self.root.after(1, self.loop)


if __name__ == '__main__':
    g = triangulation(grayscale=False)
    # g.show_solution()
