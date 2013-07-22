import scidb_server_interface as idb
idb.connect()

language = "aql"
query = "select time, sum(data) from CCD where row > 308256 and row < 308273 and col > 277621 and col < 277637 group by time"

queryplan_query = "explain_physical('" + query + "','" + language + "')"

print  "queryplan query: "
print  queryplan_query

queryplan = idb.queryAnalysis(query, language)
oa = idb.parseQueryPlan(queryplan) #returns a dictionary
	
#oa = idb.executeQuery(queryplan_query, 'afl')

#qp = idb.verifyQuery("select sum(data) from CCD where row > 308256 and row < 308273 and col > 277621 and col < 277637 group by time", {'afl': False})

#qr = idb.executeQuery("select sum(data) from CCD where row > 308256 and row < 308273 and col > 277621 and col < 277637 group by time")

#desc = qr.array.getArrayDesc()
#dims = desc.getDimensions()
#attrs = desc.getAttributes()
