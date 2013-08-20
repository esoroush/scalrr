import sys
import re
import StringIO
sys.path.append('/project/db1/scidb_12_10_iteration/lib/')
#sys.path.append('/projects/db8/build/lib/')
#sys.path.append('/projects/db8/build/bin/')
import scidbapi as scidb
import numpy
import ctypes
from datetime import datetime


db = None
TILE_SIZE = 100
def connect():
	global db
	db = scidb.connect("vega.cs.washington.edu", 5555)

def disconnect():
	global db
	if db is not None:
		db.disconnect()
		db = None
		
def completeQuery(query_id):
	db.completeQuery(query_id)


def assignmentToStore(query):
        result = []
        query_split = re.split('\[|\]',query)
        if len(query_split) == 1:
                return query
        name = query_split[0].split("=")
        body = query_split[1].split("from")
        result.append(body[0])

        result.append(" into ")
        result.append(name[0])
        result.append(" from ")
        result.append(body[1])
        return ''.join(result)


def alignQuery(query_text):
	print "**** align query ****:", query_text, type(query_text)
	try:
        	trans_query = []
		sub_arr = query_text.split("subarray")
		between = False
		if len(sub_arr) == 1:
			sub_arr = query_text.split("between")
			
			if len(sub_arr) == 1:
				return {'query':query_text,'done':False}
			else:
				between = True
	
		trans_query.append(sub_arr[0])
		if between == True:
			trans_query.append("between")
		else:
			trans_query.append("subarray")
		param_array = re.split(',|\)',sub_arr[1],7)
		print param_array
		trans_query.append(param_array[0])
		trans_query.append(",")
		trans_query.append(param_array[1])
		trans_query.append(",")
		trans_query.append(str(int(param_array[2])-247750))
		trans_query.append(",")
		trans_query.append(str(int(param_array[3])-259750))
		trans_query.append(",")
		trans_query.append(param_array[4])
		trans_query.append(",")
		remainder_1 = (int(param_array[5]) - int(param_array[2]) + 1) % 10 
		remainder_2 = (int(param_array[6]) - int(param_array[3]) + 1) % 10 
		print remainder_1
		print remainder_2
		if remainder_1 != 0:
			new_param1 = int(param_array[5]) - 247750 + (10 -int(remainder_1))
		else:
			new_param1 = int(param_array[5]) - 247750
		
		if remainder_2 != 0:
			new_param2 = int(param_array[6]) - 259750 +(10 -int(remainder_2))
		else:
			new_param2 = int(param_array[6]) - 259750

		print new_param1,new_param2
		trans_query.append(str(new_param1))
		trans_query.append(",")
		trans_query.append(str(new_param2))
		trans_query.append(")")
		trans_query.append(param_array[7])    
		new_query = ''.join(trans_query)
		return {'query':new_query,'old_row':remainder_1,'old_col':remainder_2,'done':True} 
	except:	
		print "query cannot be translated:", query_text, type(query_text)
		print trans_query
		return query_text
def removeQuery(array_name):
	print "remove array:", array_name
	global db
	try:
		query = "remove("+array_name+")"
	        return_ans = db.executeQuery(query, "afl")
		db.completeQuery(return_ans.queryID)
	except:
		print "array "+array_name+" does not exist"
		
def executeQuery(query, language="aql",alignment=True,complete=True):
	print "Query: ", query, type(query)
	print "Language:", language, type(language)
	print "Executing Query ", datetime.now()
	
	return_ans = None
	
	global db
	try:
		#queryplan = queryAnalysis(query, language)
		#return parseQueryPlan(queryplan) #returns a dictionary
		query1 = None
		if language == "aql":
			query1 = assignmentToStore(query)
		else:
			query1 = query
		print "assignmentToStore:",query1
		#if alignment == True:
		query_translate = alignQuery(query1)		
		return_ans = db.executeQuery(query_translate['query'], language)
		#else:
		#	return_ans = db.executeQuery(query1, language)
	        if complete == True:	
			db.completeQuery(return_ans.queryID)
        except:
	#except Exception, inst:
		#handleException(inst, language, op= "Executing query: " + query)
		return_ans = None

	print "Finished Executing Query ", datetime.now()

	return return_ans
	
def getDataInJson(query_result):
	print  "Parsing query result into JSON", datetime.now()

	desc = query_result.array.getArrayDesc()
	
	# Dimensions
	dims = desc.getDimensions()
	dimnames = []
	for i in range(dims.size()):
		if dims[i].getBaseName() != "EmptyTag":
			dimnames.append(dims[i].getBaseName())

	arr = []
	its = []
	# Attributes
	attrs = desc.getAttributes()
	attrnames = []
	for i in range(attrs.size()):
		if attrs[i].getName() != "EmptyTag":
			its.append(query_result.array.getConstIterator(i))
			attrnames.append(attrs[i].getName())

	while not its[0].end():
		chunkiters = []
		for itindex in range(len(its)):
			currentchunk =its[itindex].getChunk()
			chunkiter = currentchunk.getConstIterator((scidb.swig.ConstChunkIterator.IGNORE_EMPTY_CELLS |
		                                       scidb.swig.ConstChunkIterator.IGNORE_OVERLAPS))
			chunkiters.append(chunkiter)

		while not chunkiters[0].end():
			dataobj = {}
			dimobj= {}
			currpos = chunkiters[0].getPosition()
			for dimindex in range(len(currpos)):
				#print dimindex
				dname = dimnames[dimindex]
				#print "dname" , dname
				dimobj[dname[:len(dname)]] = currpos[dimindex] # make sure you take off the array's name from each dimension
				dataobj["dims."+dname[:len(dname)]] = currpos[dimindex]
			attrobj = {} #empty dictionary for the attribute values
			#print  "start"
			for chunkiterindex in range(len(chunkiters)):
				dataitem = chunkiters[chunkiterindex].getItem()
				attrobj[attrnames[chunkiterindex]] = scidb.getTypedValue(dataitem, attrs[chunkiterindex].getType()) # TBD: eliminate 2nd arg, make method on dataitem
				dataobj["attrs."+attrnames[chunkiterindex]] = scidb.getTypedValue(dataitem, attrs[chunkiterindex].getType())
				chunkiters[chunkiterindex].increment_to_next() # OMG THIS INCREMENTS ALL THE CHUNK ITERATOR OBJECTS
			arr.append(dataobj)

		for itindex in range(len(its)):		
			its[itindex].increment_to_next()
			
	namesobj = []
	typesobj = {}
	for attri in range(len(attrnames)):
		attrname = attrnames[attri]
		namesobj.append({'name':"attrs."+attrname,'isattr':True})
		typesobj["attrs."+attrname] = attrs[attri].getType()
	for dimname in dimnames:
		ndimname = "dims."+dimname[:len(dimname)]
		namesobj.append({'name':ndimname,'isattr':False})
		typesobj[ndimname] = "int32"

	print  "Done parsing query results, returning dump-ready version", datetime.now()
	
	return {'data':arr, 'names': namesobj, 'types': typesobj}

def getFirstAttrArrFromQueryInNumPY(query_result,alignment,hack=False):
	print "Parsing Query Result into NumPY Array: ", datetime.now()
        global TILE_SIZE	
	desc = query_result.array.getArrayDesc()
	
	dims = desc.getDimensions()
	attrs = desc.getAttributes()
	array_dim_length = []
	array_dim = []
	chunkInterval = []
	print "Dimensions"
	offset = []
	end = []
	for i in range (dims.size()):
		start = dims[i].getCurrStart()
		end.append(dims[i].getCurrEnd())
		chunkInterval.append(dims[i].getChunkInterval())
		offset.append(start)
		print "    Dimension[%d] = %d:%d" % (i, start, end[i])
		
		array_dim_length.append(end[i] - int(alignment[i])  - start + 1)    # hack for demo 
		#array_dim_length.append(end  - start + 1)
		array_dim.append([start, end[i]])
	print "Chunk Interval:", chunkInterval
	print "Array Dimensions: ", array_dim_length
	print "alignment:",alignment
	print "end:",end 
	#array_dim_length = [4250,4250]	
	# make the data array
	data_array = numpy.empty([array_dim_length[0], array_dim_length[1]], order='C')
	#data_array[:] = None

	
	iters = []
	for i in range (attrs.size()): 
		attrid = attrs[i].getId()
		print "attrid:",attrid
		iters.append(query_result.array.getConstIterator(attrid))

	num_chunk = 0
	#data_index = 0
	while not iters[0].end():
		for i in range (attrs.size()):
			if (attrs[i].getName() == "EmptyTag"):
				continue
			attType = attrs[i].getType()
			print "Getting iterator for attribute %d, chunk %d." % (i, num_chunk), datetime.now()

			currentchunk = iters[i].getChunk()
			emptychunk = iters[attrs.size()-1].getChunk()
			
			currentdata = currentchunk.dump()
			emptydata = emptychunk.dump()
			
			print type(currentdata)
			print type(emptydata)
			
			currentCount = currentchunk.count()
			emptyCount = emptychunk.count()

			current_buf_type = ctypes.c_char * currentCount * 8
			empty_buf_type = ctypes.c_char * (emptyCount)
			
			current_address = long(currentdata)
		        empty_address = long(emptydata)

			print current_address," ",currentCount
			print empty_address," ",emptyCount
			
			lowPosition = currentchunk.getLowBoundary(False)
			highPosition = currentchunk.getHighBoundary(False)
		        logicalChunkSize = [highPosition[0]-lowPosition[0]+1,highPosition[1]-lowPosition[1]+1]	
			print "logicalChunkSize:",logicalChunkSize
			nika_array = numpy.ndarray(shape=(logicalChunkSize[0],logicalChunkSize[1]), dtype=numpy.dtype(float),buffer=current_buf_type.from_address(current_address))
			empty_array = numpy.ndarray(emptyCount, dtype=numpy.dtype(bool),buffer=empty_buf_type.from_address(empty_address))
			
			highPos = [0,0]
                        highPos[0] = min(highPosition[0]-offset[0],array_dim_length[0]-1)
                        highPos[1] = min(highPosition[1]-offset[1],array_dim_length[1]-1)

			lowPos = [0,0]
                        lowPos[0] = lowPosition[0]-offset[0]
                        lowPos[1] = lowPosition[1]-offset[1]

			logicalChunkSize = [highPos[0]-lowPos[0]+1,highPos[1]-lowPos[1]+1]	
			
			print lowPos," ",highPos
			#print nika_array
			#print empty_array

			#chunkiter = currentchunk.getConstIterator((scidb.swig.ConstChunkIterator.IGNORE_OVERLAPS)|(scidb.swig.ConstChunkIterator.IGNORE_EMPTY_CELLS))
			#remainder  = position[1] % chunkInterval[1]
			
			#threshold = min(position[1] + (chunkInterval[1] - remainder - 1),end[1])
			#print "threshold:",threshold	
			#origPosition = position[1]
			#threshold -= offset[1]
			#emptychunkiter = emptychunk.getConstIterator((scidb.swig.ConstChunkIterator.TILE_MODE)|(scidb.swig.ConstChunkIterator.IGNORE_OVERLAPS)|(scidb.swig.ConstChunkIterator.IGNORE_EMPTY_CELLS))
			
			if hack == True:
				print "nika array:",nika_array.shape
				print "data array:",data_array.shape
				print "logicalchunkSize:",logicalChunkSize
				print "array dim length:",array_dim_length
					
				data_array[lowPos[0]:highPos[0]+1,lowPos[1]:highPos[1]+1] = nika_array[0:logicalChunkSize[0],0:logicalChunkSize[1]]
				#current_index = 0
				#for ei in empty_array:
				#   if ei:
				#	if (position[0]) <  array_dim_length[0] and (position[1]) <  array_dim_length[1]: 
				#		data_array[position[0], position[1]] = nika_array[current_index]
				#	current_index += 1
				#
				#   position[1] += 1
				#   if position[1] > threshold:
				#	position[1] = origPosition
				#	position[0]+=1
				#print data_array	
				
				#while not chunkiter.end():
                                        #if not chunkiter.isEmpty(): 
                                        #dataitem = chunkiter.getItem()
                                        #position = chunkiter.getPosition()
                                        #if (position[0]-offset[0]) < array_dim_length[0] and (position[1]-offset[1]) < array_dim_length[1]: 
					#	data_array[position[0]-offset[0], position[1]-offset[1]] = scidb.getTypedValue(dataitem,attType)
                                        #chunkiter.increment_to_next()
	
		        else:
			       	current_index = 0
                                for ei in empty_array:
                                   if ei == True:
                                        data_array[position[0]-offset[0], position[1]-offset[1]] = float(nika_array[current_index])
                                        current_index += 1

                                   position[1] += 1
                                   if (position[1] % chunkInterval[1] == 0) or (position[1] > end[1]):
                                        position[1] = origPosition
                                        position[0]+=1

				#while not chunkiter.end():
                                        #if not chunkiter.isEmpty(): 
                                        #dataitem = chunkiter.getItem()
                                        #position = chunkiter.getPosition()
                                        #data_array[position[0]-offset[0], position[1]-offset[1]] = scidb.getTypedValue(dataitem,attType)
                                        #chunkiter.increment_to_next()
	
		num_chunk += 1;
		for i in range(attrs.size()):
			iters[i].increment_to_next();
	zmin = numpy.nanmin(data_array)
	zmax = numpy.nanmax(data_array)
	array_dim.append([zmin, zmax])
	print "zmin", zmin
	print "zmax", zmax
	
	print "Done Parsing Query Result into NumPY Array.", datetime.now()
	#print "NumPY Array: ", data_array
	return data_array, array_dim;




def queryAnalysis(query, language):
	'''
	function to do the resolution reduction when running queries
	get the queryplan for the given query and return the line with info about the result matrix
	'''
	query = re.sub("(\\')","\\\\\\1",query)
	# eventually want to be able to infer this

	queryplan_query = "explain_physical('" + query + "','" + language + "')"
	
	optimizer_answer = db.executeQuery(queryplan_query, 'afl')
	
	# flatten the list into one big string, and then split on '\n'
	optimizer_answer_array = getOneAttrArrFromQuery(optimizer_answer,"")[0].split('\n') #should return array with one item (the query plan)
	# find the line with the first instance of 'schema' in the front
	for i, s in enumerate(optimizer_answer_array):
		if(re.search("^\s*schema", s)):
			return s


# get the matrix size (across all dimensions) and the number of dimensions of the result matrix
def parseQueryPlan(queryplan):
	# get the text in between the square brackets
	queryplan = str(queryplan)
	dim_string = queryplan[queryplan.find("[")+1:queryplan.find("]")]
	dim_array = dim_string.split(',')
	#print  dim_array
	dims = 0
	size = 1
	names = []
	bases= {}
	widths = {}
	for i, s in enumerate(dim_array):
		if (i % 3) == 0:
			# split on equals, get the range, split on ':'
			#print  "s:",s
			range = s.split('=')[1]
			name = s.split('=')[0]
			if name.find("(") != -1:
				name = name[:name.find("(")]
				rangewidth = int(range)
				bases[name] = 1 #0 by default
			else:
				rangevals = range.split(':')
				rangewidth = int(rangevals[1]) - int(rangevals[0]) + 1
				bases[name]=rangevals[0];
			names.append(name)
			size *= rangewidth
			dims += 1
			widths[name] =rangewidth;
	return {'size': size, 'numdims': dims, 'dims': names, 'attrs':get_attrs(queryplan),'dimbases':bases,'dimwidths':widths}

# function used to build a python "array" out of the given
# scidb query result. attrname must be exact attribute 
# name or this defaults to first attribute
def getOneAttrArrFromQuery(query_result,attrname):
	desc = query_result.array.getArrayDesc()
	dims = desc.getDimensions() # list of DimensionDesc objects
	attrs = desc.getAttributes() # list of AttributeDesc objects

	dimlengths= []
	dimchunkintervals = []
	dimoverlaps = []
	dimindexes = []
	dimindexesbase = []

	if(dims.size() < 1):
		return [];

	for i in range(dims.size()):
		dimlengths.append(dims[i].getLength())
		dimchunkintervals.append(dims[i].getChunkInterval())
		dimoverlaps.append(dims[i].getChunkOverlap())
		dimindexes.append(0)
		dimindexesbase.append(0)

	# get arr ready
	arr = createArray(dimlengths)
	#print  "arr is initialized: ",str(arr)
	attrid = 0
	for i in range(attrs.size()): # find the right attrid
		if(attrs[i].getName() == attrname):
			attrid = i
			#print  "found attribute",attrname, ",id: %d" % attrid 
			break

	# get the iterator for this attrid
	it = query_result.array.getConstIterator(attrid)

	start = True
	while not it.end():
		#print  "iterating over items..."
		currentchunk = it.getChunk()
		# TODO: will have to fix this at some point, can't just ignore empty cells or overlaps
		chunkiter = currentchunk.getConstIterator((scidb.swig.ConstChunkIterator.IGNORE_EMPTY_CELLS |
                                               scidb.swig.ConstChunkIterator.IGNORE_OVERLAPS))

		if(not start): # don't update for the first chunk
			#update base indexes
			dimindexesbase = updateBaseIndex(dimindexesbase,dimlengths,dimchunkintervals)
			#printIndexes(dimindexesbase)
			verifyIndexes(dimindexesbase,dimlengths)

			#reset the indexes to new base indexes
			for i in range (dims.size()):
				dimindexes[i] = dimindexesbase[i]
		else:
			start = False

		while not chunkiter.end():
			#printIndexes(dimindexes)
			verifyIndexes(dimindexes,dimlengths)
			dataitem = chunkiter.getItem()
			# look up the value according to its attribute's typestring
			item = scidb.getTypedValue(dataitem, attrs[attrid].getType()) # TBD: eliminate 2nd arg, make method on dataitem
			#print  "Data: %s" % item

			#insert the item
			arr = insertItem(arr,item,dimindexes)
			#update the indexes
			dimindexes = updateIndexes(dimindexes,dimchunkintervals,dimindexesbase,dimlengths)
			lastpos = chunkiter.getPosition()
			#print  lastpos[0],",",lastpos[1], ",",lastpos[2]
			chunkiter.increment_to_next()
		#print  "current state of arr: ", str(arr)
		it.increment_to_next();
	return arr

#exterior function for initializing an array of the appropriate size
def createArray(dimlengths):
	return createArrayHelper(dimlengths,0,len(dimlengths))

#helper function for createArray to do the recursive building of the array to be initialized
def createArrayHelper(dimlengths,currdim,numdims):
	arr = [0]*dimlengths[currdim]
	if(currdim < (numdims-1)):
		for i in range(dimlengths[currdim]):
			arr[i] = createArrayHelper(dimlengths,currdim+1,numdims)
	return arr

# function that verifies that we are not trying to use indexes
# that are out of bounds
def verifyIndexes(dimlist,dimboundaries):
	for i in range(len(dimlist)):
		assert dimlist[i] < dimboundaries[i], "indexes out of range." #" index:",str(dimlist[i]),", boundary:",str(dimboundaries[i])

# function to update to the next appropriate index location after inserting 1 item
#not to be confused with the similar updateBaseIndex, which updates by chunk lengths
def updateIndexes(dimindexes,dimchunkintervals, dimindexesbase,dimlengths):
	i = len(dimindexes) - 1
	while i > 0:
		dimindexes[i] += 1
		if((dimindexes[i] - dimindexesbase[i]) >= dimchunkintervals[i]):
			dimindexes[i] = dimindexesbase[i]
			# next dimension up will be incremented in next iteration of the while loop
			i -= 1
		elif(dimindexes[i] >= dimlengths[i]): # edge case for odd chunks
			dimindexes[i]= dimindexesbase[i]
			i-= 1
		else:
			break
	if(i == 0):
		dimindexes[i] += 1
	return dimindexes

#function to recompute the base indexes when we've completed
#traversal of the current chunk
def updateBaseIndex(dimindexesbase,dimlengths,dimchunkintervals):
	i = len(dimindexesbase) - 1
	while i > 0:
		dimindexesbase[i] += dimchunkintervals[i]
		if(dimindexesbase[i] >= dimlengths[i]):
			dimindexesbase[i] = 0
			i -= 1
		else:
			break	
	if(i == 0):
		dimindexesbase[i] += dimchunkintervals[i]
	return dimindexesbase

#exterior function to insert the given item in the the array using the given indexes
def insertItem(arr,item,dimindexes):
	#print  "inserting item %d" % item
	return insertItemHelper(arr,item,dimindexes,0,len(dimindexes))

#helper function to recursively find the appropriate list to insert the item into in the array
def insertItemHelper(arr,item,dimindexes,currdim,numdims):
	if(currdim == (numdims-1)):
		arr[dimindexes[currdim]] = item
	else:
		arr[dimindexes[currdim]] = insertItemHelper(arr[dimindexes[currdim]],item,dimindexes,currdim + 1, numdims)
	return arr

#get all attributes of the result matrix
def get_attrs(queryplan):
	# get the text in between the angle brackets
	attr_string = queryplan[queryplan.find('<')+1:queryplan.find('>')]
	attr_array = attr_string.split(',')
	names = []
	types = []
	for i,s in enumerate(attr_array):
		name_type = (s.split(' ')[0]).split(':') # does this work?
		names.append(name_type[0])
		types.append(name_type[1])
	return {'names':names,'types':types}
