import numpy
   
class SciDB_Result():
    def __init__(self, data_array):
        self.zmin = 1
        self.zmax = 2

        #special values
        self.delta_value = numpy.NAN
        self.empty_value = int(self.zmin - 1)
        
        # make the data array
        self.data_array = data_array
        self.img_array = None
        
    def get_data_array(self):
        return self.data_array
    
    
    def get_img_array(self, master=None):
        # No master, img = data
        if master is None and self.img_array is None:
            self.img_array = self.data_array
            return self.img_array
        
        # Make the img array with deltas compared to the master
        if self.img_array is None:
            self.img_array = numpy.copy(self.data_array)
            for (x,y), z in numpy.ndenumerate(self.img_array):
                if abs(master[x,y] - z) >= 0.1:
                    self.img_array[x,y] = self.delta_value
        
        return self.img_array
