import tkinter as tk 
from tkinter import ttk 
import sv_ttk 
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.animation import FuncAnimation
import numpy as np
import cfg
import threading 
import warnings
from operator import itemgetter
import math
import serial
import serial.tools.list_ports
import time

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

                # place the com select box 
                self.com_select_box = ttk.Combobox(self, state='readonly')
                self.scan()
                self.com_select_box.grid(row=0, column=0, padx=0, pady=0, sticky='ew')
                self.com_select_box.bind("<<ComboboxSelected>>", self.update_selected)

                # place the scan button 
                self.scan_button = ttk.Button(self, text='Scan', command=self.scan)
                self.scan_button.grid(row=0, column=1, padx=0, pady=0)
        
        def scan(self):
                # get a list of all com ports 
                iterator = serial.tools.list_ports.comports()
                self.com_port_dev = ['<select>']
                self.com_port_descriptions = ['<select>']
                for x in iterator: 
                        self.com_port_dev.append(x.device)
                        self.com_port_descriptions.append(x.description)

                addToLog(f'Found {len(self.com_port_dev)-1} COM Port(s)')

                # update the entries
                combo_values = [f'{device}, {description}' for device, description in zip(self.com_port_dev, self.com_port_descriptions)]
                self.com_select_box['values'] = combo_values

                # if one matches the name of oven, switch to it
                reflow_oven_id = 'USB-SERIAL CH340'
                i = None
                for i, x in enumerate(combo_values):
                        if reflow_oven_id in x:
                                self.com_select_box.current(i)
                                break 
                        else: 
                                self.com_select_box.current(0)
                                i = 0
                cfg.COM_PORT_LOCK.acquire()
                cfg.SELECTED_SERIAL_PORT = self.com_port_dev[i]
                cfg.COM_PORT_LOCK.release() 
                addToLog(f'{self.com_port_dev[i]} Selected')
                return
        
        def update_selected(self, event):
                for i, x in enumerate(self.com_port_dev):
                        if x in self.com_select_box.get():
                                # i is the correct index
                                cfg.COM_PORT_LOCK.acquire()
                                cfg.SELECTED_SERIAL_PORT = x
                                cfg.COM_PORT_LOCK.release() 
                                addToLog(f'{x} Selected')
                                break 
                return 


class Log(ttk.LabelFrame):
        def __init__(self, parent):
                super().__init__(parent, text='Log', padding = 15)
                self.parent = parent

                # create a scrollbar and add to right side of 
                self.log_scrollbar = ttk.Scrollbar(self)
                self.log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

                # create text box and add the scrollbar
                self.log_text = tk.Text(self, yscrollcommand=self.log_scrollbar.set)
                self.log_text.pack(side=tk.LEFT, fill=tk.BOTH)

                # configure the scrollbar to move the box
                self.log_scrollbar.config(command=self.log_text.yview)

                # configure the task that will update the log
                self.parent.after(200, self.update_log)
                
                # disable the textbox so it cannot be edited through gui 
                self.log_text.config(state='disabled')
        
        def update_log(self):
                # enable the textbox so it can be edited 
                self.log_text.config(state='normal')

                # if the log buffer has entries add them to the log
                cfg.LOG_LOCK.acquire()
                if (len(cfg.LOG_BUF) > 0):
                        for x in cfg.LOG_BUF:
                                self.log_text.insert(tk.END, x)
                        cfg.LOG_BUF = [] # make it empty
                cfg.LOG_LOCK.release()

                # disable the textbox 
                self.log_text.config(state='disabled')

                self.parent.after(200, self.update_log)
                return 

class ControlButtons(ttk.Frame):
        def __init__(self, parent):
                super().__init__(parent, style="Card.TFrame", padding=15)

                self.last_start_time = time.time() 
                self.has_activated = False

                # configure the grid 
                self.columnconfigure(0, weight=1) # connect button
                self.columnconfigure(1, weight=4) # start button 
                self.rowconfigure(0, weight=1)

                # create the connect button 
                self.connect_button = ttk.Button(self, text='Connect', command=self.connect)
                self.connect_button.grid(row=0, column=0, padx=0, pady=0)

                # create the start button 
                self.start_button = ttk.Button(self, text='Start', style='Accent.TButton', command=self.start)
                self.start_button.grid(row=0, column=1, padx=0, pady=0, sticky='ew')
        
        def connect(self):
                cfg.COM_PORT_LOCK.acquire()
                cfg.TO_CONNECT = True
                cfg.COM_PORT_LOCK.release()
                return 
        
        def start(self):
                if ((time.time() - self.last_start_time) > 1):
                        cfg.ACTIVE_LOCK.acquire()
                        if (cfg.REFLOW_ACTIVE):
                                # already active, disable
                                cfg.REFLOW_ACTIVE = False
                                addToLog('Disabling')
                        else:
                                # need to activate
                                cfg.COM_PORT_LOCK.acquire()
                                if ((not self.has_activated) and cfg.HAS_CONNECTED):
                                        cfg.REFLOW_ACTIVE = True
                                        self.has_activated = True 
                                        addToLog('Activating')
                                else: 
                                        addToLog('Not Activating')
                                cfg.COM_PORT_LOCK.release()
                        cfg.ACTIVE_LOCK.release()
                return 

class Graph(ttk.Frame):
        def __init__(self, parent):
                super().__init__(parent, style="Card.TFrame", padding=15)
                warnings.filterwarnings('ignore', module='graphing')

                # Create a Figure 
                self.fig = Figure(figsize=(6, 4), dpi=300, facecolor='none')

                # Add a subplot to the figure 
                self.ax = self.fig.add_subplot(111)
                self.ax.tick_params(axis='both', labelsize=4)
                self.ax.grid(True)
                self.ax.xaxis.set_tick_params(width=0.5)
                self.ax.yaxis.set_tick_params(width=0.5)
                self.ax.set_aspect(1, adjustable='box')

                # Set the Axis limits
                # y_lim = max setpoint plus 10%, x_lim = max time plus 10%
                y_len = math.ceil((sorted(cfg.SETPOINT_LIST, key=itemgetter(1), reverse=True)[0][1])*1.1)
                y_range = (20, y_len)
                x_len = math.ceil(cfg.SETPOINT_LIST[-1][0]*1.1)
                x_range = (0, x_len)
                self.ax.set_ylim(y_range)
                self.ax.set_xlim(x_range)

                # add the setpoint line 
                xs_sp = []
                ys_sp = []
                for k in cfg.SETPOINT_LIST:
                        xs_sp.append(k[0])
                        ys_sp.append(k[1])
                self.setpoint_line, = self.ax.plot(xs_sp, ys_sp, color='xkcd:purple', linestyle=':')

                # create the temp line
                cfg.LOCK.acquire()
                self.tmp_line, = self.ax.plot(cfg.XS_TMP, cfg.YS_TMP, color='xkcd:red', linestyle='solid')
                cfg.LOCK.release() 

                # add labels
                self.ax.set_title('REFLOW TEMPERATURE', fontsize=6)
                self.ax.set_xlabel('Time (s)', fontsize=4)
                self.ax.set_ylabel('Temp (C)', fontsize=4)
                self.setpoint_line.set_label('Target')
                self.tmp_line.set_label('Actual')
                self.ax.legend(loc='upper left', fontsize=5)

                # Create a canvas for the figure 
                self.canvas = FigureCanvasTkAgg(self.fig, master=self)
                self.canvas.draw()

                # Get the Tkinter Canvas widget from the canvas object and pack into the frame
                self.canvas_widget = self.canvas.get_tk_widget()
                self.canvas_widget.pack(fill=tk.BOTH, expand=True)

                # Create the animation that will update the plot during runtime
                self.ani = FuncAnimation(self.fig, self.update, interval=100, 
                                        cache_frame_data=False, blit=True)
                
        def update(self, i):
                cfg.LOCK.acquire()
                self.tmp_line.set_xdata(cfg.XS_TMP)
                self.tmp_line.set_ydata(cfg.YS_TMP)
                cfg.LOCK.release()
                return self.tmp_line, 

def addToLog(message: str, end='\n'):
        # both print the message to console and add to the log box queue
        print(message, end=end)
        cfg.LOG_LOCK.acquire()
        cfg.LOG_BUF.append(message + end)
        cfg.LOG_LOCK.release()
        return

def run_gui():
        root = tk.Tk()
        root.title('Reflow Oven GUI')
        sv_ttk.set_theme('light')
        App(root).pack(expand=True, fill = 'both')
        root.mainloop()
        cfg.REFLOW_ACTIVE = False
        cfg.END_LOCK.acquire() 
        cfg.TO_END = True 
        cfg.END_LOCK.release() 
        
        return 

def main():
        run_gui()
        return

if __name__ == '__main__':
        main()
