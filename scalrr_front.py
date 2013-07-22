import sys

import Queue

import Tkinter as tk

import matplotlib
matplotlib.use('TKAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

import SciDB
import scalrr_vis

import time
import zscale

HOST = 'vega.cs.washington.edu' # The remote host
PORT = 50007              # The same port as used by the server

ZSCALE = True  

class Visualizer:
    ui_root = None # ui_root for all ui objects
    frame = None
    _canvas = None
    
    scidb_connector = None
    master = None
    
    iterations = list()

    def __init__(self, root, host, port):
        self.ui_root = root
        self.host = host
        self.port = port
        
        self.init_UI()
    
    def init_UI(self):
        self.ui_root.title("SciDB Visualizer")
        
        self.frame=tk.Frame(self.ui_root)
        self.frame.pack()
        
        query_frame=tk.Frame(self.frame)
        query_frame.grid(row=0)
        
        tk.Label(query_frame, text='Enter Query:').pack(padx=10, pady=0, side=tk.LEFT, fill=tk.X)
        self.query_text_gui = tk.Text(query_frame, width=40, height=1, borderwidth=5, takefocus=1)
        self.query_text_gui.pack(padx=10, pady=0, side=tk.LEFT, fill=tk.X)
        
        iteration_frame = tk.Frame(query_frame)
        iteration_frame.pack()
        self.iterative_checked = tk.IntVar()
        tk.Checkbutton(iteration_frame, text="Iterative Query", variable=self.iterative_checked, command=self.toggleCheck).grid(row=0, column=0)
        self.num_of_iterations = tk.StringVar()
        self.iteration_num_entry = tk.Entry(iteration_frame, textvariable=self.num_of_iterations)
        self.iteration_num_entry.grid(row=0, column=1)
        self.iteration_num_entry.grid_remove()
        
        tk.Button(query_frame, text="Execute", command=self.execute_query).pack(padx=10, pady=0)
        
        self.graph_frame = tk.Frame(self.frame)
        self.graph_frame.grid(row=2)
        self.iteration_buttons = tk.Frame(self.frame)
        self.iteration_buttons.grid(row=3)
        
        #tk.Button(self.frame, text="Quit", command=self.frame.quit).grid(row=3, sticky=W, padx=10, pady=10)
        
        tk.Grid.rowconfigure(self.frame,1,weight=5)
        tk.Grid.columnconfigure(self.frame,0,weight=5)
        
        f = Figure()
        f.add_subplot(111)
        self.update_graph(f)
        
    def toggleCheck(self):
        if self.iterative_checked.get():
            self.iteration_num_entry.grid()
        else:
            self.iteration_num_entry.grid_remove()
    
    def execute_query(self):
        query_text  = self.query_text_gui.get(1.0, tk.END)
        #FOR TESTING#################################################
        query_text  = 'select sum(data) from CCDF_SAMPLE_SUB@ group by row,col'
        #############################################################
        if query_text  == None or query_text  == '' or query_text  == '\n':
            return
        
        self.iteration_buttons.destroy()
        self.iteration_buttons = tk.Frame(self.frame)
        self.iteration_buttons.grid(row=3)
        self.previous_result = None
        self.iterations = list()
        
        self.scidb_connector = SciDB.SciDB_Connector(self.host, self.port)
        if self.iterative_checked.get():
            self.scidb_connector.execute_query(query_text, iterative=True, iterations=int(self.num_of_iterations.get()))
        else:
            self.scidb_connector.execute_query(query_text)
        
        self.ui_root.after(1000, self.handle_result) # problem if button clicked many times....
        
    def handle_result(self):
        """
        Check every 100 ms if there is something new in the queue.
        Handle all the messages currently in the queue (if any).
        """
        if not self.scidb_connector.running and self.scidb_connector.result_queue.qsize() == 0:
            print >> sys.stdout, 'Stopping Image Loader...'
            return
        
        if self.scidb_connector.result_queue.qsize():
            try:
                print >> sys.stdout, 'Loading image...'
                start_time = time.clock()
                
                query_json = self.scidb_connector.result_queue.get(0)
                result = SciDB.SciDB_Result(query_json)
                
                # Make figure
                if query_json['request']['options']['iterative']:
                    scatter = scalrr_vis.plot_image(result, ZSCALE, master=self.master, title="Iteration " + str(len(self.iterations) + 1))
                    self.master = result.data_array
                    
                    self.add_graph(scatter)
                else:
                    self.master = None
                    scatter = scalrr_vis.plot_image(result, ZSCALE, title=query_json['request']['query'])
                    
                    self.update_graph(scatter)
                 
                end_time = time.clock()   
                print >> sys.stdout, 'Done... ', end_time-start_time
                
                self.ui_root.after(500, self.handle_result)
            except Queue.Empty:
                pass
            
        else:
            self.ui_root.after(1000, self.handle_result)
    def plot_image(self, result, title='ScatterPlot', grid=False):
        if ZSCALE == True:
                z_min, z_max = zscale.zscale(result.data_array, nsamples=2000, contrast=0.25) 
        else:
                z_min = result.zmin
                z_max = result.zmax
                
        fig, graph = plt.subplots()
        
        # define the colormap and norm
        #cmap = plt.get_cmap('RdYlBu_r')
        #cmap = plt.get_cmap('jet')
        cmap = plt.get_cmap('Greys_r')
        cmap.set_over('#FFFFFF')
        cmap.set_under('#000000')
        cmap.set_bad('#00FF00')
        image = graph.imshow(result.get_img_array(self.master), cmap=cmap, vmin=z_min, vmax=z_max, origin='lower',
                           interpolation='nearest',
                           extent=([result.xmin, result.xmax, result.ymin, result.ymax])
                           )

        graph.set_xlabel(result.x_name, fontsize=20)
        graph.set_ylabel(result.y_name, fontsize=20)
        graph.set_title(title)
        graph.grid(grid)
        colorbar = fig.colorbar(image)
        colorbar.set_label(result.z_name, fontsize=20)
        
        return fig
    
    def add_graph(self, scatterplot):
        self.iterations.append(scatterplot)
        
        tk.Button(self.iteration_buttons, text="Iteration " + str(len(self.iterations)), command=lambda: self.update_graph(scatterplot)).pack(side=tk.LEFT, fill=tk.X)
        self.update_graph(scatterplot)
        
    def update_graph(self, figure):
        self.graph_frame.destroy()
        self.graph_frame = tk.Frame(self.frame)
        self.graph_frame.grid(row=1)
        figure.set_size_inches(18.5,10.5)
        self._canvas = FigureCanvasTkAgg(figure, master=self.graph_frame)
        self._canvas.get_tk_widget().pack()
        self._canvas.show()

if __name__ == '__main__':
    root = tk.Tk()
    root.geometry("850x950+300+300")
    app = Visualizer(root, HOST, PORT)
    root.mainloop()
