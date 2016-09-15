/*global $, WebSocket, console, window, document*/
"use strict";

/**
 * Connects to Pi server and receives video data.
 */
var client = {

    // Connects to Pi via websocket
    connect: function (port) {

        var self = this, video = document.getElementById("video"), settingsDiv = document.getElementById("settings");

        this.socket = new WebSocket("ws://" + window.location.hostname + ":" + port + "/websocket");

        // Request the video stream once connected
        this.socket.onopen = function () {
            console.log("Connected!");
            self.readCamera();
        };

        this.socket.onmessage = function (messageEvent) {
            //console.log(messageEvent.data);
            var rObj = JSON.parse(messageEvent.data);
            switch(rObj.type) {
                case "track":
                    //$('#trackingdata').html(JSON.stringify(rObj.data));
                    updateTrackingTable(rObj.data);
                    updateTrackingData(rObj.data);
                    updatePreview(rObj.data);
                    break;
                case "settings":
                    //$('#settings').html(JSON.stringify(rObj.data));
                    updateSettings(rObj.data);
                    break;
                case "imgraw":
                    imgraw.src = "data:image/jpeg;base64," + rObj.data;
                    break;
                case "imgproc":
                    imgproc.src = "data:image/jpeg;base64," + rObj.data;
                    break;
                case "log":
                    if(Object.keys(rObj.data).length > 0) updateLogs(rObj.data);
                    break;
            }
        };
    },

    // Requests video stream
    readCamera: function () {
        //console.log("request!");
        self.socket.send("track");
    }
};