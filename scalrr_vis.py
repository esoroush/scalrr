import StringIO

import matplotlib
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas



def plot_image(img_array, z_min, z_max):
    fig = Figure(frameon=False)
    fig.set_size_inches(12, 12, forward=True)
    graph = fig.add_subplot(1, 1, 1)

    # define the colormap and norm
    #cmap = plt.get_cmap('RdYlBu_r')
    #cmap = plt.get_cmap('jet')
    cmap = matplotlib.cm.get_cmap('Greys_r')
    cmap.set_over('#FFFFFF')
    cmap.set_under('#000000')
    cmap.set_bad('#00FF00')

    graph.imshow(img_array, cmap=cmap, vmin=z_min, vmax=z_max, origin='lower', interpolation='nearest') 
    
    FigureCanvas(fig)
    fig.set_size_inches(12, 12, forward=True)

    # Get encoded image
    output = StringIO.StringIO()
    extent = graph.get_window_extent().transformed(fig.dpi_scale_trans.inverted())
    fig.savefig(output, format='png', bbox_inches=extent, dpi=200)
    
    return output
