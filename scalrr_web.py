import json
import base64
import StringIO
import pyfits
import pywcs
import uuid
import numpy

from flask import Flask, make_response, request, session, render_template
from flask import send_file

import scidb_server_interface as db_interface
import scalrr_vis
import SciDB
import zscale

app = Flask(__name__)

memcache = {}

default_StartingX = 272250
default_StartingY = 264250
default_StartingZ = 0

@app.route('/')
def index():
    return render_template('index.html') 

@app.route('/process/timeseries/', methods=['GET'])
def process_timeseries():
    query_text  = request.args['query']
    language = request.args['language']
    
    callback = request.args['callback']
    
    db_interface.connect()
    
    query_result = db_interface.executeQuery(str(query_text), str(language))
    if query_result is None: # error processing query
        return make_response(json.dumps({
                    'request': request.json,
                    'status': 'ERROR',
                    'message': "error processing query", 
                    }))
        
    data_json = db_interface.getDataInJson(query_result)
    
    db_interface.disconnect()
    
    # Make response
    json_message = {
                    'request': request.json,
                    'status': 'OK',
                    'data': data_json, 
                    }
    message = callback + "(" + json.dumps(json_message) + ")"
    response = make_response(message)
    
    return response

@app.route('/process/query/image/', methods=['GET'])
def process_query_image():
    if request.args['iterative']:
        query_text = request.args['query'].replace("@","@"+str(request.args['iteration']))
        title = "Iteration " + str(request.args['iteration'])
    else:
        query_text  = str(request.args['query'])
        title = query_text
        
    iterative = request.args['iterative']
    z_scale = request.args['z_scale']
    language = str(request.args['language'])
    
    callback = request.args['callback']
    
    query_lines = query_text.split("\n")
    
    db_interface.connect()
    
    # process all queries except for the last one
    for query_line in query_lines[:-1]: # process all lines except the last one
        db_interface.executeQuery(str(query_line), str(language))

    # process last query
    query_result = db_interface.executeQuery(str(query_lines[-1]), str(language))
    if query_result is None: # error processing query
        return make_response(json.dumps({
                    'request': request.json,
                    'status': 'ERROR',
                    'message': "error processing query", 
                    }))
      
    data_array, array_dim = db_interface.getFirstAttrArrFromQueryInNumPY(query_result)
    db_interface.disconnect()
    
    #print >> sys.stdout, response_json
    result = SciDB.SciDB_Result(data_array)
    
    # Get the image array
    if not iterative:
        img_array = result.get_data_array()
    elif request.args['iteration'] == 1:
        img_array = result.get_data_array()
    else:
        master = memcache.get(session.pop('previous_data_key', None), None)
        img_array = result.get_img_array(master)
    
    # Get z min and max   
    if z_scale == True:
            z_min, z_max = zscale.zscale(result.data_array, nsamples=2000, contrast=0.25) 
    else:
            z_min, z_max = (array_dim[2][0], array_dim[2][1]) #TODO fix this, currently zmin and zmax are unknown
            
    # Make figure   
    output = scalrr_vis.plot_image(img_array, z_min, z_max)
    
    encoded_image = base64.b64encode(output.getvalue())
    
    # Save session data
    memcache[query_text] = result.get_data_array()
    session['previous_data_key'] = query_text

    # Make response
    json_message = {
                    'request': request.args,
                    'status': 'OK',
                    'image': encoded_image, 
                    #"plot": {"title": title, "x_axis": result.x_name, "y_axis": result.y_name, "z_axis": result.z_name},
                    "dimensions": {
                                   "x":{"min": array_dim[0][0], "max": array_dim[0][1]}, 
                                   "y":{"min": array_dim[1][0], "max": array_dim[1][1]}, 
                                   "z":{"min": array_dim[2][0], "max": array_dim[2][1]}
                                   }
                    }
    message = callback + "(" + json.dumps(json_message) + ")"
    response = make_response(message)
    #print >> sys.stdout, json_message
    return response

@app.route('/process/query/fits/', methods=['GET'])
def process_query_fits():
    query_text  = str(request.args['query'])
    iterative = request.args['iterative']
    language = str(request.args['language'])
    callback = request.args['callback']
    
    if iterative:
        query_text = request.args['query'].replace("@","@"+str(request.args['iteration']))
    
    query_lines = query_text.split("\n")
    try:
        db_interface.connect()
    except:
        message = json.dumps({
                    'request': request.json,
                    'status': 'ERROR',
                    'message': "unable to connect to SciDB",
                    })
        return make_response(callback + "(" + message + ")")

    # process all queries except for the last one
    for query_line in query_lines[:-1]: # process all lines except the last one
        db_interface.executeQuery(str(query_line), str(language))

    # process last query
    query_result = db_interface.executeQuery(str(query_lines[-1]), str(language))
    if query_result is None: # error processing query
        message = json.dumps({
                    'request': request.json,
                    'status': 'ERROR',
                    'message': "error processing query", 
                    })
        return make_response(callback + "(" + message + ")")

    data_array, array_dim = db_interface.getFirstAttrArrFromQueryInNumPY(query_result)
    db_interface.disconnect()
    
    filename = uuid.uuid4().hex + ".fits"

    wcs = pywcs.WCS(naxis=2)
    try:
        sub_arr = query_text.split("subarray")[1].split(",")
        wcs.wcs.crpix = [440250-(int(sub_arr[3])-259750), 353595-(int(sub_arr[2])-247750)]
	#wcs.wcs.crpix = [440250-(int(sub_arr[3])-260250), 353595-(int(sub_arr[2])-248250)]
    except:
        wcs.wcs.crpix = [440250, 353595]
    wcs.wcs.cd = numpy.array([-.0000555555555, 0, 0, .000055555555]).reshape([2,2])
    wcs.wcs.crval = [60, 10.8123169635717]
    wcs.wcs.ctype = ["RA---STG", "DEC--STG"]

    header = wcs.to_header()    
    try:
    	sub_arr = query_text.split("subarray")[1].split(",")
        header.update("AbsPixX", int(sub_arr[2]))
        header.update("AbsPixY", int(sub_arr[3]))
        header.update("AbsPixZ", int(sub_arr[1]))
    except:
        header.update("AbsPixX", default_StartingX)
        header.update("AbsPixY", default_StartingY)
        header.update("AbsPixZ", default_StartingZ)
    header.update("CD1_2", 0)
    header.update("CD2_1", 0)
    header.update("CD1_1", -0.0000555555555)
    header.update("CD2_2", 0.0000555555555)

    hdu = pyfits.PrimaryHDU(data_array, header=header)    
    hdu.writeto(filename)
    
    #encoded_fits = base64.b64encode(output.getvalue())

    # Make response
    json_message = {
                    'request': request.args,
                    'status': 'OK',
                    'fits_file': filename
                    }

    message = callback + "(" + json.dumps(json_message) + ")"
    response = make_response(message)
    #print >> sys.stdout, json_message
    return response

def process_query():
    return 

@app.route('/get/<filename>', methods=['GET'])
def get_file(filename):
    
    file = send_file(filename,
                     attachment_filename="file.fits",
                     as_attachment=True)
    
    response = make_response(file)
    response.headers['Access-Control-Allow-Origin'] = "*"

    return response


import os
app.secret_key = os.urandom(24)
 
if __name__ == '__main__':
    app.run('vega.cs.washington.edu', 5551, debug=True)
