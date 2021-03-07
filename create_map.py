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
    print('grid_bin', grid.grid_bin)
    for idx, line in enumerate(grid.grid_bin):
        for idy, val in enumerate(line):
            if val == True:
                grid.grid[idx][idy].fill = True
            else:
                grid.grid[idx][idy].fill = False
    grid.draw()
    update_percentage()
    #print(grid.grid_bin)


def pressed():
    save_state(grid)

def update_percentage():
    number_true = len([item for row in grid.grid_bin for item in row if item==True])
    percentage = number_true/(grid_y*grid_x)
    Percentage.configure(text = percentage)

def view_maps(map1, map2, size):
    app = Tk()
    pixels = 950//max(size[0], size[1])
    grid = CellGrid(app, size[0], size[1], pixels)
    Button1 = Button(app, text="Map1", command=pressed)
    Button2 = Button(app, text="Map2", command=load_state)

if __name__ == "__main__" :
    app = Tk()
    buttonPressed = False
    grid_x = 58
    grid_y = 58
    pixels = 950//max(grid_y, grid_x)
    grid = CellGrid(app, grid_x, grid_y, pixels)
    Button1 = Button(app, text="Save", command=pressed)
    Button2 = Button(app, text="Load", command=load_state)
    Percentage = Label(text="", fg="Red", font=("Helvetica", "18"))
    Button1.pack()
    Button2.pack()
    Percentage.pack()
    grid.pack()
    app.mainloop()
