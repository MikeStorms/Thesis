from tkinter import *
import pickle

class Cell():
    FILLED_COLOR_BG = "black"
    EMPTY_COLOR_BG = "white"
    FILLED_COLOR_BORDER = "green"
    EMPTY_COLOR_BORDER = "red"

    def __init__(self, master, x, y, size):
        """ Constructor of the object called by Cell(...) """
        self.master = master
        self.abs = x
        self.ord = y
        self.size= size
        self.fill= False

    def _switch(self):
        """ Switch if the cell is filled or not. """
        self.fill= not self.fill

    def draw(self):
        """ order to the cell to draw its representation on the canvas """
        if self.master != None :
            fill = Cell.FILLED_COLOR_BG
            outline = Cell.FILLED_COLOR_BORDER

            if not self.fill:
                fill = Cell.EMPTY_COLOR_BG
                outline = Cell.EMPTY_COLOR_BORDER

            xmin = self.abs * self.size
            xmax = xmin + self.size
            ymin = self.ord * self.size
            ymax = ymin + self.size

            self.master.create_rectangle(xmin, ymin, xmax, ymax, fill = fill, outline = outline)

    def draw_colored(self):
        if self.master != None :
            colors = ["blue4", "cyan2", "green2", "OliveDrab2", "yellow2", "DarkOrange2", "red3", "violet red", "purple4", "SlateBlue1"]
            outline = "black"
            if self.fill == 0:
                fill = "white"
            else:
                fill = colors[self.fill % 10]

            xmin = self.abs * self.size
            xmax = xmin + self.size
            ymin = self.ord * self.size
            ymax = ymin + self.size

            self.master.create_rectangle(xmin, ymin, xmax, ymax, fill = fill, outline = outline)

    def draw_edges(self, edge):
        """ order to the cell to draw its representation on the canvas """
        if self.master != None :
            fill = Cell.FILLED_COLOR_BG
            outline = Cell.FILLED_COLOR_BORDER

            if not self.fill:
                fill = Cell.EMPTY_COLOR_BG
                outline = Cell.EMPTY_COLOR_BORDER

            if edge:
                fill = "red"
                outline = "yellow"
            xmin = self.abs * self.size
            xmax = xmin + self.size
            ymin = self.ord * self.size
            ymax = ymin + self.size

            self.master.create_rectangle(xmin, ymin, xmax, ymax, fill = fill, outline = outline)

class CellGrid(Canvas):
    def __init__(self,master, rowNumber, columnNumber, cellSize, *args, **kwargs):
        Canvas.__init__(self, master, width = cellSize * columnNumber , height = cellSize * rowNumber, *args, **kwargs)

        self.cellSize = cellSize

        self.grid = []
        self.grid_bin = []
        for row in range(rowNumber):
            line_bin = []
            line = []
            for column in range(columnNumber):
                line.append(Cell(self, column, row, cellSize))
                line_bin.append(0)
            self.grid.append(line)
            self.grid_bin.append(line_bin)
            #print('initial grid', self.grid_bin)


        #memorize the cells that have been modified to avoid many switching of state during mouse motion.
        self.switched = []

        #bind click action
        self.bind("<Button-1>", self.handleMouseClick)
        #bind moving while clicking
        self.bind("<B1-Motion>", self.handleMouseMotion)
        #bind release button action - clear the memory of midified cells.
        self.bind("<ButtonRelease-1>", self.handleRelease)

        self.draw()





    def draw(self):
        for row in self.grid:
            for cell in row:
                cell.draw()

    def draw_colored(self):
        for row in self.grid:
            for cell in row:
                cell.draw_colored()

    def draw_edges(self, edges):
        for iy, row in enumerate(self.grid):
            for ix, cell in enumerate(row):
                cell.draw_edges(edges[iy][ix])

    def _eventCoords(self, event):
        row = int(event.y / self.cellSize)
        column = int(event.x / self.cellSize)
        return row, column

    def handleMouseClick(self, event):
        row, column = self._eventCoords(event)
        cell = self.grid[row][column]
        cell._switch()
        cell.draw()
        #add the cell to the list of cell switched during the click
        self.switched.append(cell)

    def handleMouseMotion(self, event):
        row, column = self._eventCoords(event)
        cell = self.grid[row][column]

        if cell not in self.switched:
            cell._switch()
            cell.draw()
            self.switched.append(cell)

    def handleRelease(self,event):
        for value in self.switched:
            for idx, line in enumerate(self.grid):
                if value in line:
                    if self.grid_bin[idx][line.index(value)] == 1:
                        self.grid_bin[idx][line.index(value)] = 0
                    else:
                        self.grid_bin[idx][line.index(value)] = 1
        self.switched.clear()
        update_percentage()


def save_state(self):
    print(self.grid_bin)
    f = open('map', 'wb')
    pickle.dump(self.grid_bin, f, 2)
    f.close


def load_state():

    f = open('map', 'rb')
    grid.grid_bin = pickle.load(f)
    f.close

    #print('grid_bin', grid.grid_bin)
    for idx, line in enumerate(grid.grid_bin):
        for idy, val in enumerate(line):
            if val == True:
                grid.grid[idx][idy].fill = True
            else:
                grid.grid[idx][idy].fill = False
    grid.draw()
    update_percentage()
    #print(grid.grid_bin)

def load_state_1():

    f = open('map_1', 'rb')
    grid.grid_bin = pickle.load(f)
    f.close
    #print('grid_bin', grid.grid_bin)
    for idx, line in enumerate(grid.grid_bin):
        for idy, val in enumerate(line):
            if val == True:
                grid.grid[idx][idy].fill = True
            else:
                grid.grid[idx][idy].fill = False
    grid.draw()
    update_percentage()
    #print(grid.grid_bin)

def load_state_2():

    f = open('map_2', 'rb')
    grid.grid_bin = pickle.load(f)
    f.close
    #print('grid_bin', grid.grid_bin)
    for idx, line in enumerate(grid.grid_bin):
        for idy, val in enumerate(line):
            if val == True:
                grid.grid[idx][idy].fill = True
            else:
                grid.grid[idx][idy].fill = False
    grid.draw()
    update_percentage()
    #print(grid.grid_bin)

def load_buffer_deterministic():
    f = open('map_deterministic', 'rb')
    grid.grid_bin = pickle.load(f)
    f.close

    for idx, line in enumerate(grid.grid_bin):
        for idy, val in enumerate(line):
            grid.grid[idx][idy].fill = val
    grid.draw_colored()

def load_buffer_stochastic():
    f = open('map_stochastic', 'rb')
    grid.grid_bin = pickle.load(f)
    f.close

    for idx, line in enumerate(grid.grid_bin):
        for idy, val in enumerate(line):
            grid.grid[idx][idy].fill = val
    grid.draw_colored()

def load_buffer_stochastic_edges():
    f = open('map_stochastic_edges', 'rb')
    grid.grid_bin = pickle.load(f)
    f.close

    for idx, line in enumerate(grid.grid_bin):
        for idy, val in enumerate(line):
            grid.grid[idx][idy].fill = val
    grid.draw_colored()

def load_edges():
    f = open('map_edges', 'rb')
    edges = pickle.load(f)
    f.close

    f = open('map', 'rb')
    grid.grid_bin = pickle.load(f)
    f.close

    for idx, line in enumerate(grid.grid_bin):
        for idy, val in enumerate(line):
            grid.grid[idx][idy].fill = val
    grid.draw_edges(edges)

def pressed():
    save_state(grid)


def update_percentage():
    number_true = len([item for row in grid.grid_bin for item in row if item==True])
    percentage = number_true/(grid_y*grid_x)
    Percentage.configure(text = percentage)


if __name__ == "__main__" :
    app = Tk()
    buttonPressed = False
    grid_x = 56
    grid_y = 56
    pixels = 950//max(grid_y, grid_x)
    grid = CellGrid(app, grid_x, grid_y, pixels)
    #for regular load: load_state
    #for the map extension: load_state_1 & load_state_2
    #for the buffer allocation: load_buffer_deterministic & load_buffer_stochastic & load_buffer_stochastic_edges
    Button1 = Button(app, text="Save", font=("Helvetica", "56"), command=pressed)
    Button2 = Button(app, text="Load", font=("Helvetica", "56"), command=load_state)
    # Button3 = Button(app, text="Map1", command=load_buffer_stochastic)
    # Button4 = Button(app, text="Map2", command=load_buffer_stochastic_edges)
    Percentage = Label(text="", fg="Red", font=("Helvetica", "56"))
    Button1.pack()
    Button2.pack()
    # Button3.pack()
    # Button4.pack()
    Percentage.pack()
    grid.pack()
    app.mainloop()
