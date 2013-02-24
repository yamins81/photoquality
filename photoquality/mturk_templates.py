html_template="""<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
<title>Category Counting</title>

<style>
body { margin:0; padding: 0; font-family: 'trebuchet ms', trebuchet, verdana }
div,pre { margin:0; padding:0 }
h2 { margin: 20px 0 5px 0; padding: 0 }
p.intro { margin: 0; padding: 15px; background: #eee; font-size: small; }
.thumbs { position: absolute; width: 100px; height: 100px;}
div.thumb { position:absolute; float:left; padding: 1px; width: 64px; height: 64px;}
div.thumb img { border: 2px solid white; width:64px; height:64px; }

div#tutorial {
position:relative; 
background-color: white;  
padding: 10px;
}

</style>

<script type="text/javascript" src="http://ajax.googleapis.com/ajax/libs/jquery/1.4.2/jquery.min.js"></script>
<script src="http://ajax.googleapis.com/ajax/libs/jqueryui/1.8/jquery-ui.min.js"></script>
<script type="text/javascript" language="JavaScript" src="http://web.mit.edu/esolomon/www/browserdetect.js"></script>
<script type="text/javascript" src="http://web.mit.edu/esolomon/www/javascripts/jQueryRotate.2.2.js"></script>
<script type="text/javascript" src="http://web.mit.edu/esolomon/www/javascripts/jQuery.mousewheel.js"></script>
<script type="text/javascript" src="http://web.mit.edu/esolomon/www/javascripts/jquery.zoom-min.js"></script>
<script type="text/javascript" src="http://web.mit.edu/yamins/www/%{JSPATH}_subsets.js"></script>
<script type="text/javascript" src="http://web.mit.edu/esolomon/www/zen.js"></script>
<script type="text/javascript" src="http://esolomon.scripts.mit.edu/ip.php"></script>
<script src="http://web.mit.edu/esolomon/www/javascripts/detect-zoom.js" type="text/javascript"></script>
<script src="http://cdnjs.cloudflare.com/ajax/libs/underscore.js/1.4.4/underscore-min.js"></script>
<link href="http://ajax.googleapis.com/ajax/libs/jqueryui/1.8/themes/base/jquery-ui.css" rel="stylesheet" type="text/css"/>

<script type="text/javascript">

shuffle = function(o) { 
	for(var j, x, i = o.length; i; j = parseInt(Math.random() * i), x = o[--i], o[i] = o[j], o[j] = x);
	return o;
  };
  
Array.prototype.flatten = function flatten(){
   var flat = [];
   for (var i = 0, l = this.length; i < l; i++){
       var type = Object.prototype.toString.call(this[i]).split(' ').pop().split(']').shift().toLowerCase();
       if (type) { flat = flat.concat(/^(array|collection|arguments|object)$/.test(type) ? flatten.call(this[i]) : this[i]); }
   }
   return flat;
};


//!!==BEGIN DYNAMIC TRIAL CODE==!!//

function checkCorrect(vls){
    var v = vls.slice(0); 
    var rn = _.map(_.range(1, numImages + 1), String)
    v.sort();
    if (_.isEqual(v, rn)){
        return true
    } else {
        console.log(v, rn);
        return false
    };

};

function checkCorrectppl(vls){
    var v = vls.slice(0); 
    if (_.isEmpty(_.without(v, "0", "1", "2", "3", "m"))){
        return true
    } else {
        console.log(v, _.without(v, "0", "1", "2", "3", "m"));
        return false
    };

};

function beginExp() {
	console.log('beginExp');
	$("#begintask").hide(), $("#_preload").hide();
	$('#boxes').show() 
	$('#nextTrial').show() 	
	$('.inputcount').bind('click', function(event) { event.stopPropagation() });
	$('#nextTrial').click(function(){
							   
							   var vals = [];
							   $('.inputorder').each(function() {
							   							vals.push($(this).val())
							   									});

							   var vals2 = [];
							   $('.numppl').each(function() {
							   							vals2.push($(this).val())
							   									});
							   		
							    
							   if (!(checkCorrect(vals))){
							       alert("Your ranking response (first row) has not been completed properly.\\n\\nYou must annotate the images with quality rankings, 1 through " + numImages + ", with 1 being the best and " + numImages + " being the least good. No ranking ties are allowed, so each image gets a unique quality ranking.");
							   };
							   if (!(checkCorrectppl(vals2))){
							       alert("Your number of people response (second row) has not been completed properly.\\n\\n You must annotate the number of people in each image.  If you see 3 or fewer people in a given image, just type the number of people in the image.  But since we don't want you to spend to much time on this task, if you see more than 3 people, do not count them and instead, just type 'm', for 'many'.");
							   };							   
							   	
							    if (checkCorrect(vals) && checkCorrectppl(vals2)){                                
                                    trialEndTime = new Date();
                                    $('#group_container').hide();				   
                                    clicked(vals, vals2); 
                                    
                                };

							   });
	
	$('#group_container').hide();
	
	//set stimuli
	showStim();
}

function init_boxes(){
   var im;
   T = $('#boxes').append('<table style="border-spacing:8px" id="imgtable"><tr id="row1"></tr><tr id="row2"></tr><tr id="row3"></tr></table>')
   for (var i = 0; i < numImages; i++){
        im = new Image;
        imarray.push(im);
        $('#row1').append('<td><div><img id="image_' + String(i) + '" src=""/><br/></div></td>');
        $('#row2').append('<td><div><input style="height:20px; width:30px;" class="inputorder" value="" type="text" maxlength="3" /> rank out of ' + numImages + '.</div></td>');
        $('#row3').append('<td><div><input style="height:20px; width:30px;" class="numppl" value="" type="text" maxlength="3"/> person(s) present.</div></td>');
   };
}

function setStimuli(tn){
   x = img_files[tn]; 
   for (var i = 0; i < numImages; i++){
        im = imarray[i];
        im.src = "http://pics-from-sam.s3.amazonaws.com/small_tr_pics/" + x[i];
        $('#image_' + String(i)).attr('src', im.src)
        $('.inputorder').val("");
        $('.numppl').val("");
   };  
}

function showStim() {
	console.log('showStim');
	$('.inputcount').each(function() {$(this).val(0);});
	$('#group_container').show();
	$('#totalSeen').html('Total Objects Seen: 0');
	$('#trialCounter').html('Progress: '+trialNumber+' of '+totalTrials);
	trialStartTime = new Date();
	// set images
	setStimuli(trialNumber)	
}

function clicked(myval, myval2) {
	console.log('clicked');
 pushData(myval, myval2)

 endTrial();
	
}


function pushData(myval, myval2) {
	console.log('pushData');
StimDone.push(img_files[trialNumber]);
response.push(_.zip(myval, myval2));
trialDurations.push(trialEndTime - trialStartTime);
}

function endTrial() {
  if (trialNumber >= (totalTrials-1))
  {
	var resultsobj = [];
	resultsobj.push({
					Response:response,
					ImgOrder:img_files,
					StimShown:StimDone,
					RT:trialDurations,
					Zoom:zoom,
					IPaddress:user_IP,
					Browser:BrowserDetect.browser,
					Version:BrowserDetect.version,
					OpSys:BrowserDetect.OS,
					WindowHeight:winH,
					WindowWidth:winW,
					ScreenHeight:vertical,
					ScreenWidth:horizontal
					});	  
	  
	document.getElementById("assignmentId").value = aID;
	document.getElementById("data").value = JSON.stringify(resultsobj);
	document.getElementById("postdata").submit();	
  }
    else if (jQuery.inArray(trialNumber,BreakTimes) > -1) {
	  takeABreak();
  }
  else
  {
    trialNumber++;
    showStim();
  }
}

function takeABreak() {
	$('#main_test').attr('src',breakscreen.src);
	$('.test').show()
	$('#_preload').html("<font color=red style=background-color:white>You have completed "+Math.round((trialNumber/totalTrials)*100)+" percent of the experiment. Be sure to pay attention so that you know you can finish on time!");
	$('#_preload').show();
	document.onkeypress = function(e){  
			var evtobj = window.event? event : e;
			var unicode = evtobj.charCode? evtobj.charCode : evtobj.keyCode;
			var actualKey = String.fromCharCode(unicode);
				if (actualKey=='z'){
					trialNumber++;
					$('.test').hide()
					$('#_preload').hide();	
					showStim();
					};
		};
	
}

//!!==END DYNAMIC TRIAL CODE==!!//



function gup( name )
{
  name = name.replace(/[\[]/,"\\\[").replace(/[\]]/,"\\\]");
  var regexS = "[\\?&]"+name+"=([^&#]*)";
  var regex = new RegExp( regexS );
  var param = regex.exec( window.location.href );
  if( param == null )
    return "";
  else
    return param[1];
}

function init_vars() {
	zoom = DetectZoom.zoom();
	aID = gup("assignmentId");  
	hovertrack = new Array();
	response = new Array();
	trialDurations = new Array();
	StimDone = new Array();
	breakscreen = new Image;
	breakscreen.src = "http://s3.amazonaws.com/monkeyimgs/2way_impute/break.png";
	trialNumber = 0;
	totalTrials = img_files.length;
	numImages = %NUMIMAGES;
	BreakTimes = [Math.round(totalTrials/2)];
	imarray = new Array();
	//img_files = [["http://pics-from-sam.s3.amazonaws.com/small_tr_pics/Tech Rehearsal/24_Preshow/D70_9503.JPG",
	//              "http://pics-from-sam.s3.amazonaws.com/small_tr_pics/Tech Rehearsal/24_Preshow/D70_9515.JPG"]];
}


$(document).ready(function() {
	
	init_vars();
	init_boxes();
	
	$("#begintask").click(function(){
                                      beginExp();
                                      });

	
	$('.test').hide();
	$('#warning').hide();
    $('#boxes').hide() 
	$('#nextTrial').hide() 	

	$("#tutorial").html($("#tutorial_original").html());
	$("#tutorial").dialog({height:700,
							width:600,
							position:"center",
							title:"Instructions"
							});
							
	if (aID == "ASSIGNMENT_ID_NOT_AVAILABLE"){
	$('#warning').show();
	$('#warning').html("<font color=red style=background-color:white><b>You are in PREVIEW mode. Please ACCEPT this HIT to complete the task and receive payment.</b></font>")
	}
	
});

</script>

</head>

<body bgcolor="#7F7F7F">
<div align="center" id="warning"></div>
<div align="center"><button id="begintask" value="Begin!">Begin!</button></div></div>
<div id="_preload" align="center" style="position:fixed; top:0px; left:10px;"></div>
<div class="test" align="center" style="position:relative; z-index:200; top:125px; left:-15px;"><img id="main_test" src="" /></div>
<div id="group_container" align="center">
<div id="trialCounter"></div>

<div id="boxes"></div>
<button style="height:50px;" id="nextTrial">Go To Next Trial</button>
</div>

<div id="tutorial_link" style="position:fixed; top:0px; right:10px;" onclick="$('#tutorial').html($('#tutorial_original').html()); $('#tutorial').dialog({height:700,width:600,position:'center',title:'Instructions'})"><u>View Instructions</u></div>

<div id="tutorial" style="position:relative; z-index:-1"></div>
<div id="tutorial_original" style="position:absolute; z-index:-1; visibility:hidden;" 
<b>Please read these instructions carefully!</b>
<p>Thank you for your interest! You are contributing to ongoing vision research at the Massachusetts Institute of Technology McGovern Institute for Brain Research.</p>
<p><font color=red><b>This task will require you to look at images on your computer screen and type numbers and letters to indicate responses, for up to about 30 minutes. If you cannot meet these requirements for any reason, or if doing so could cause discomfort or injury, do not accept this HIT.</p>
<p>We encourage you to try a little bit of this HIT before accepting to ensure it is compatible with your system. If you think the task is working improperly, your computer may be incompatible.</p></font></b>
<p>We recommend this task for those who are interested in contributing to scientific endeavors. Your answers will help MIT researchers better understand how the brain processes visual information.</p>
<center><p onclick="$('#tutorial').html($('#tutorial2').html())"><font color=blue><u>Click here to continue reading</u></font></p></center></div>
<div id="tutorial2" style="visibility:hidden; position:absolute; z-index:-1;">
<ul>
<li>You will see a series of images, presented %NUMIMAGES at a time. The images are mostly of people in various dance activities.</b></li>
<p>
<li>In this task, you'll have two jobs for each group of %NUMIMAGES images.   First, you'll rank the images according to photographic quality.   By <b>photographic quality</b>, we just mean your own personal sense of good you think each image is as a composition, compared to the others images in the group of %NUMIMAGES.  Most of the images contain people, but we're looking for your response not to the looks of the specific person(s) in the image, but instead to how good the photograph is of the scene overall.  To indicate your ranking, type the number 1, 2, ... %NUMIMAGES under the image -- where 1 is the best image and %NUMIMAGES is the least good.  No ties in ranking are allowed, so you must always label exactly one image as 1 (the best), one image as 2 (second best), and so on. </li>
<p>
<li> Your second job is to get a quick count of the <b>number of people</b> in the image.  If you see one person, type "1", if you see two people, type "2", &c. But we don't want you to spend too much time on this task, so if you see more than 3 people, just type "m" (that is, for "many").  If you see no people at all, type "0".</li>
</ul>
<center><p onclick="$('#tutorial').html($('#tutorial3').html())"><font color=blue><u>Click here to continue reading</u></font></p></center>
</div>
<div id="tutorial3" style="visibility:hidden; position:absolute; z-index:-1;"> 
<ul>
<li><b>In total, you will see at most 250 sets of images, but usually fewer. We expect this experiment to take about 30 minutes.</b> Halfway through, we will give you a chance to take a short break and inform you of your progress. Note that the HIT will expire if you spend more than 1 hour, so plan your time accordingly.</li>
<p>
<li>When you are ready to begin, click the "Begin" button at the very top of the screen.</li>
<p>
<li>If you have questions or concerns about this HIT, feel free to contact the requester. You can re-read these instructions at any time by clicking the link in the upper right-hand corner of the screen. Good luck, and thank you for your help!</li>
</ul>
<center><font color=blue><u><p onclick="$('#tutorial').dialog('close')">Click here to close the instructions</p></center></font></u>
</div>

<form style="visibility:hidden" id="postdata" action="https://workersandbox.mturk.com/mturk/externalSubmit" method="post">
<input type="text" name="data" id="data" value="">
<input type="text" name="assignmentId" id="assignmentId" value="">
</form>


</body>
</html>
"""

js_template = """var img_files=%s;
"""
