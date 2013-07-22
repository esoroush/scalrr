import scidb_server_interface as db_interface
#import mysql_server_interface as mdbi

''' NO LONGER USED '''

def process_request(query, options):
    db_interface.connect()
    
    response = query_execute(query,options)
    
    db_interface.disconnect()
    
    return response

def query_execute(query, options):
    if options["afl"]:
        language = "afl"
    else:
        language = "aql"
   
    query_result = db_interface.executeQuery(query, language, options['return_result'])
    
    if options['return_result']:
        ans = db_interface.getNumPyArray(query_result)
    else:
        ans = None
    
    db_interface.completeQuery(query_result.queryID)
    
    return ans