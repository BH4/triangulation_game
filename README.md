# triangulation_game
Inspired by the New York Times Vertex game. This is a procedurally generated version.

Current controls:
Start the game by running the file "game.py" using python 3.

Clicking near a point and dragging near another will drop an edge between them. Right click will undo. Left click away from any points and dragging will pan the view. Scroll wheel will zoom.

By default the levels are changed randomly. To choose a particular level add "lvl_seed=YOUR_NUMBER" as a parameter in the line "g = triangulation()". The new line should read "g = triangulation(lvl_seed=YOUR_NUMBER)" potentially with other parameters.
