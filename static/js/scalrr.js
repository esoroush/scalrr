num_of_figures = 0;
current_figure_displayed = 0;


function displayLoading() {
    $('#ajax-laoding').removeClass('hidden')
}

function hideLoading() {
    $('#ajax-laoding').addClass('hidden')
}

function ajaxError(jqXHR, textStatus, errorThrown ) {
    alert(textStatus);
    if(errorThrown) {
      alert(errorThrown);  
    }
}

function toggleIterative() {
    if($('#iterative').attr('checked')) {
        $('#iterations').removeClass('hidden');
    } else {
        $('#iterations').addClass('hidden');
    }
}


function executeQuery() {
    query_text = $('#query-text').attr('value');
    request = { 'query':  query_text };
    
    if($('#iterative').attr('checked')) {
        request['iterative']  = true;
    } else {
    	request['iterative'] = false;
    }
    
    if($('#afl').attr('checked')) {
        request['afl']  = true;
    } else {
    	request['afl'] = false;
    }
    
    request['z_scale'] = true;
    
    console.log('Sending Request:' + JSON.stringify(request));
    
    resetCanvas();
    
    if(request['iterative']) {
        executeIterativeQuery(request, 1);
    } else {
        executeSingleQuery(request);
    }
}

function executeSingleQuery(request) {
    $.ajax({
        url: "./process/query/",
        type: "POST",
        contentType: "application/json",
        dataType: "json",
        data: JSON.stringify(request),
        beforeSend: displayLoading,
        complete: hideLoading,
        error: ajaxError,
        success: function(result) {
            console.log("Received Result:");
	    console.log(result);
            if (result['status'] === 'OK') {
                img_id = addFigure(result['image']);
                showFigure(img_id);
            }
        }
    });
}

function executeIterativeQuery(request, iteration) {
	request['iteration'] = iteration
	
    $.ajax({
        url: "./process/query/",
        type: "POST",
        contentType: "application/json",
        dataType: "json",
        data: JSON.stringify(request),
        beforeSend: displayLoading,
        complete: hideLoading,
        error: ajaxError,
        success: function(result) {
            console.log(result);
	    if (result['status'] === 'OK') {
                img_id = addFigure(result['image']);
                showFigure(img_id);
            }
            
            if(iteration != 3) { // !result['done']
            	executeIterativeQuery(request, iteration+1);
            }
        }
    });
}

function resetCanvas() {
	$('#plot').attr('html', "");
	num_if_figures = 0;
	current_figure_displayed = 0;
}

function addFigure(image_data) {
	id = num_of_figures++;
	console.log(image_data);
	alert('here');
	img = $('<img></img>');
	img.attr('src',"data:image/png;base64, " + image_data);
	img.attr('id', id);
	
	$('#plot').append(img);
	
	return id;
}

function showFigure(image_id) {
	console.log("showing figure: " + image_id);
	show_img = $('#' + image_id);
	img = $('#' + current_figure_displayed);
	
	if(show_img) {
		if(img) {
			img.addClass('hidden');
		}
		
		show_img.removeClass('hidden');
		current_figure_displayed = image_id;
	}
}

function nextFigure() {
	showFigure(current_figure_displayed + 1);
}

function previousFigure() {
	showFigure(current_figure_displayed - 1);
}

function executeTest() {
    request = {};
    request['query']  = 'select sum(data) from CCDF_SAMPLE_SUB@ group by row, col';
    request['iteration'] = 1;
    request['iterative'] = true;
    request['z_scale'] = true;
    request['iterations'] = 3;
    request['afl'] = false;
    request['language'] = 'aql';

    executeIterativeQuery(request, 1);
    
}



