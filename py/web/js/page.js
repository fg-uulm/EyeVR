/**
 * Created by fg on 08.08.16.
 */
var dpsSize = []; // dataPoints
var dpsAngle = []; // dataPoints
var dpsLength = []; // dataPoints
var chart;

var xVal = 0;
var dataLength = 100; // number of dataPoints visible at any point
var isMonitoring = true;
var isImgMonitoring = true;

//Jquery checkbox serialization helper
(function ($) {

     $.fn.serialize = function (options) {
         return $.param(this.serializeArray(options));
     };

     $.fn.serializeArray = function (options) {
         var o = $.extend({
         checkboxesAsBools: false
     }, options || {});

     var rselectTextarea = /select|textarea/i;
     var rinput = /text|hidden|password|search/i;

     return this.map(function () {
         return this.elements ? $.makeArray(this.elements) : this;
     })
     .filter(function () {
         return this.name && !this.disabled &&
             (this.checked
             || (o.checkboxesAsBools && this.type === 'checkbox')
             || rselectTextarea.test(this.nodeName)
             || rinput.test(this.type));
         })
         .map(function (i, elem) {
             var val = $(this).val();
             return val == null ?
             null :
             $.isArray(val) ?
             $.map(val, function (val, i) {
                 return { name: elem.name, value: val };
             }) :
             {
                 name: elem.name,
                 value: (o.checkboxesAsBools && this.type === 'checkbox') ? //moar ternaries!
                        (this.checked ? 'true' : 'false') :
                        val
             };
         }).get();
     };

})(jQuery);


//Write new values to chart (called from client.js)
function updateChart(count, size, angle, length) {
    dpsSize.push({
        x: xVal,
        y: size
    });

    dpsAngle.push({
        x: xVal,
        y: angle
    });

    dpsLength.push({
        x: xVal,
        y: length
    });

    xVal++;

    if (dpsSize.length > dataLength) {
        dpsSize.shift();
        dpsAngle.shift();
        dpsLength.shift();
    }
    chart.render();
};

function updateTrackingTable(d){
    $('#trackingdata').empty();
    $('#trackData').empty();

    var keys = Object.keys(d);
    keys.sort();

    $.each(keys, function(index, val){
        var value;
        if(d[val]["py/tuple"] != null){
            var val1 = d[val]["py/tuple"][0] + "";
            var val2 = d[val]["py/tuple"][1] + "";
            value = val1.substring(0,6) + "\n" + val2.substring(0,6);
        }
        else{
            value = JSON.stringify(d[val]).substring(0,6);
        }
        $('#trackData').append('<tr><td>'+val+'</td><td>'+value+'</td></tr>');
    });	
}

function updateTrackingData(d) {
    var gazeVecRaw = Victor(d["xoffs"]["py/tuple"][0] * -1, d["yoffs"]["py/tuple"][0] * -1)
        .subtract(new Victor(d["center"]["py/tuple"][0], d["center"]["py/tuple"][1]));
    updateChart(dataLength, d["size"]["py/tuple"][1], gazeVecRaw.horizontalAngleDeg(), gazeVecRaw.length());
    //console.log("Chart update");
    updateTrackingEye(gazeVecRaw.length(), gazeVecRaw.horizontalAngleDeg(), d["size"]["py/tuple"][1])
    if(d["blink"] == true) $('#imgproc').css('opacity', 0);
    else $('#imgproc').css('opacity', $('#overlayOpa').val());
}

function updateTrackingEye(length, angle, size) {
    return;
    //Apply size
    $('.pupil').css({
        transform: 'scale('+size/40+','+size/40+')'
    });

    //Calculate approx x/y transform and skew

    var xTrans = 0;
    var yTrans = 0;
    $(".iris").css(
        {
            transform: 'translateX('+xTrans+') translateY('+yTrans+')'
        }
    );
}

function updatePreview(d) {
    var yoffs = d["yoffs"]["py/tuple"][0];
    var xoffs = d["xoffs"]["py/tuple"][0];
    $("#imgproc").css({top: d["glint"]["py/tuple"][1]+yoffs, left: d["glint"]["py/tuple"][0]+xoffs, position:'absolute'});
}

function updateSettings(d) {
    console.log(d);
    $('#settings form').empty();
    $('#settings form').append('<table class="table-sm table-bordered" />');
    $('#settings form').append('<button type="submit">Change Settings</button>');   

    var keys = Object.keys(d);
    keys.sort();

    $.each(keys, function(index, val) {
        if(d[val] == "false" || d[val] == "False" || d[val] == false) {
            $('#settings form table').append( '<tr><td width="100">'+val+'</td><td><input type="checkbox" id="'+val+'" name="'+val+'" value="'+d[val]+'"></td></tr>' );
        } else if(d[val] == "true" || d[val] == "True" || d[val] == true) {
            $('#settings form table').append( '<tr><td width="100">'+val+'</td><td><input type="checkbox" id="'+val+'" name="'+val+'" value="'+d[val]+'" checked="checked"></td></tr>' );
        }
        else {
            $('#settings form table').append( '<tr><td width="100">'+val+'</td><td><input type="text" id="'+val+'" name="'+val+'" value="'+d[val]+'" /></td></tr>' );
        }
    });

    $('#settings form input').change(function() {
        postSettings();
    });
}

function updateLogs(d) {
    var keys = Object.keys(d);
    keys.sort(function(a, b){return a-b});

    $.each(keys, function(index, val) {
        //$('#logscroll').prepend( '<div data-sort="'+val+'">'+val+' : '+d[val]+'</div>' );

        $('<div></div>').text(val+": "+d[val]).prependTo('#logscroll');
    });
}

function postSettings(){
    var form = $('#settings form');
    var dat = JSON.stringify(form.serializeArray({ checkboxesAsBools: true }));

    $.ajax({
        type: "POST",
        url: "/setting",
        data: dat,
        dataType: "json"
    });

    console.log(dat);
    event.preventDefault();
}

function switchToLoop() {
    var dat = '[{"name": "mode", "value": "loop"}]';
    $.ajax({
        type: "POST",
        url: "/setting",
        data: dat,
        dataType: "json"
    });
}

function toggleMonitoring() {
    if(isMonitoring) {
        $('#monToggle').text("Monitoring OFF");
        isMonitoring = false;
    } else {
        $('#monToggle').text("Monitoring ON");
        isMonitoring = true;
    }
}

function toggleImages() {
    if(isImgMonitoring) {
        $('#imgToggle').text("Live OFF");
        isImgMonitoring = false;
    } else {
        $('#imgToggle').text("Live ON");
        isImgMonitoring = true;
    }
}

function writeLoopCmd() {
    client.socket.send("writeloop");
}


//On page init
$(document).ready(function () {
    chart = new CanvasJS.Chart("chartContainer", {
        title: {
            text: ""
        },
        data: [{
            type: "line",
            dataPoints: dpsSize,
            showInLegend: true,
            legendText: "dpsSize"
        },
            {
                type: "line",
                dataPoints: dpsLength,
                showInLegend: true,
                legendText: "dpsLength"
            },
            {
                type: "line",
                dataPoints: dpsAngle,
                showInLegend: true,
                legendText: "dpsAngle"
            }
        ],
        legend: {
            horizontalAlign: "right",
            verticalAlign: "top"
        }
    });

    $(document).keydown(function(event) {
        if ( event.which == 32 ) {
            switchToLoop();
            setTimeout(reqSettings, 1000);
            event.preventDefault();
        }
    });

    $('#overlayOpa').on('input', function() {
        $('#imgproc').css('opacity', $(this).val());
    });

    function reqImages() {
        if(!isMonitoring || !isImgMonitoring) return;
        client.socket.send("imgraw");
        client.socket.send("imgproc");
    }

    function reqTrack() {
        if(!isMonitoring) return;
        client.socket.send("track");
    }

    function reqSettings() {
        if(!isMonitoring) return;
        client.socket.send("settings");
    }

    function reqLog() {
        client.socket.send("log");
    }

    client.connect(8888);
    setTimeout(reqSettings, 2000);
    setInterval(reqImages, 50);
    setInterval(reqTrack, 50);
    setInterval(reqLog, 250);
});