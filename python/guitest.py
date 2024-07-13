import tkinter as tk 
from tkinter import ttk 
import sv_ttk 
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

class App(ttk.Frame):
        def __init__(self, parent):
                super().__init__(parent, padding=15)

                # configure the grid, 1x2
                self.columnconfigure(0, weight=1) # set the other elements to 1x wider
                self.columnconfigure(1, weight=2) # set the graph 2x wider than first
                self.rowconfigure(0, weight=1) # allow the height to automatically expand

                # place the log and button object in the left grid
                ButtonsAndLog(self).grid(row=0, column=0, padx=(0, 0), pady=(0,0), sticky='nsew')

                # place the graph in the right grid
                Graph(self).grid(row=0, column=1, padx=0, pady=0, sticky='nsew')

class ButtonsAndLog(ttk.Frame):
        def __init__(self, parent):
                super().__init__(parent, padding=15)

                # configure the grid
                self.rowconfigure(0, weight=1) # com port select 
                self.rowconfigure(1, weight=8) # info box
                self.rowconfigure(2, weight=1) # button row 
                self.columnconfigure(0, weight=1) # allow width to expand

                # create and place in box
                ComPort(self).grid(row=0, column=0, padx=10, pady=10, sticky='nsew')
                Log(self).grid(row=1, column=0, padx=10, pady=10, sticky='nsew')
                ControlButtons(self).grid(row=2, column=0, padx=10, pady=10, sticky='nsew')

class ComPort(ttk.LabelFrame):
        def __init__(self, parent):
                super().__init__(parent, text='Select Com Port', padding=15)

                # configure the grid, 1x2
                self.columnconfigure(0, weight=4) # box for com port select
                self.columnconfigure(1, weight=1) # box for scan button
                self.rowconfigure(0, weight=1)

                # place the entry box
                combo_values = ['test1', 'test2', 'test3']
                self.com_select_box = ttk.Combobox(self, state='readonly', values=combo_values)
                self.com_select_box.current(0)
                self.com_select_box.grid(row=0, column=0, padx=0, pady=0, sticky='ew')

                # place the scan button 
                self.scan_button = ttk.Button(self, text='Scan')
                self.scan_button.grid(row=0, column=1, padx=0, pady=0)

class Log(ttk.LabelFrame):
        def __init__(self, parent):
                super().__init__(parent, text='Log', padding = 15)

                # create a scrollbar and add to right side of 
                self.log_scrollbar = ttk.Scrollbar(self)
                self.log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

                # create text box and add the scrollbar
                self.log_text = tk.Text(self, yscrollcommand=self.log_scrollbar.set)
                self.log_text.pack(side=tk.LEFT, fill=tk.BOTH)

                # configure the scrollbar to move the box
                self.log_scrollbar.config(command=self.log_text.yview)

                #! add some placehold entries
                for i in range(100):
                        self.log_text.insert('end', f'Log #{i}\n')
                
                # disable the textbox so it cannot be edited through gui 
                self.log_text.config(state='disabled')

class ControlButtons(ttk.Frame):
        def __init__(self, parent):
                super().__init__(parent, style="Card.TFrame", padding=15)

                # configure the grid 
                self.columnconfigure(0, weight=1) # connect button
                self.columnconfigure(1, weight=4) # start button 
                self.rowconfigure(0, weight=1)

                # create the connect button 
                self.connect_button = ttk.Button(self, text='Connect')
                self.connect_button.grid(row=0, column=0, padx=0, pady=0)

                # create the start button 
                self.start_button = ttk.Button(self, text='Start', style='Accent.TButton')
                self.start_button.grid(row=0, column=1, padx=0, pady=0, sticky='ew')

class Graph(ttk.Frame):
        def __init__(self, parent):
                super().__init__(parent, style="Card.TFrame", padding=15)

                # Create a Figure 
                self.fig = Figure(figsize=(6, 4), dpi=300, facecolor='none')

                # Add a subplot to the figure 
                self.ax = self.fig.add_subplot(111)
                self.ax.set_title('Example Plot', fontsize=6)
                self.ax.tick_params(axis='both', labelsize=4)
                self.ax.set_xlabel('X Axis', fontsize=4)
                self.ax.set_ylabel('Y Axis', fontsize=4)
                self.ax.grid(True)
                self.ax.xaxis.set_tick_params(width=0.5)
                self.ax.yaxis.set_tick_params(width=0.5)
                self.ax.set_aspect(2, adjustable='box')

                # Generate example data 
                x = np.linspace(0, 2*np.pi, 100)
                y = np.sin(x)

                # Plot the data on the subplot
                self.ax.plot(x, y)

                # Create a canvas for the figure 
                self.canvas = FigureCanvasTkAgg(self.fig, master=self)
                self.canvas.draw()

                # Get the Tkinter Canvas widget from the canvas object and pack into the frame
                self.canvas_widget = self.canvas.get_tk_widget()
                self.canvas_widget.pack(fill=tk.BOTH, expand=True)


def main():
        root = tk.Tk()
        root.title('Reflow Oven Gui')
        sv_ttk.set_theme('light')
        App(root).pack(expand=True, fill='both') # add the app into the window
        root.mainloop()
        return 

if __name__ == '__main__':
        main()
