/*jshint browser:true devel:true*/
/*global AbstractApp Flotr */

////////////////////////////////////////////////////////////////////////////////
//////////////////////////////////// Sub Class /////////////////////////////////
////////////////////////////////////////////////////////////////////////////////

function MyApp(divobj,uuid,dash){
  this.myuuid = uuid;
  if (!divobj) {
    throw "First argument must be a valid html object";
  }
  this.div = divobj;
  this.dash = dash;
}
MyApp.prototype = Object.create(AbstractApp.prototype);

//overwrite start and update
MyApp.prototype.start = function() {
  //
  //Starts app and loads gui.
  //
  var this_app = this;

  //set some attributes for the app div
  this.div.style.backgroundColor = "#9ebef7";
  
  this.getUIhtml(function(e,h){
    this_app.div.innerHTML = h;
    this_app.getAllElements();
    this_app.victory_button.addEventListener('click',function(){
      this_app.sendEvent('forward',{cmd: 'victoryLap',uuid: this_app.myuuid},
                         function(err,resp){
      });
    });
    this_app.start_button.addEventListener('click',function(){
      this_app.sendEvent('forward',{cmd: 'startLog',uuid: this_app.myuuid},
                         function(err,resp){
      });
    });
    this_app.stop_button.addEventListener('click',function(){
      this_app.sendEvent('forward',{cmd: 'stopLog',uuid: this_app.myuuid},
                         function(err,resp){
      });
    });
    this_app.dash.loadScript(
      "http://www.humblesoftware.com//static/js/flotr2.min.js",
      function(){
        this_app.Flotr = Flotr; //save ref to library
        this_app.update();
    });
  });
  this.setUpdateInterval(1*1000);
};
//var rSPI   = require('./rSPI');

MyApp.prototype.update = function(){
  "use strict";

  var this_app = this;
  var this_uuid = this.myuuid;
  
  // Set epoch to past 3 seconds 
  var d = new Date();
  var since = d.getTime() - (300*1000);

  // Get the info for the latest image and then post it to the app
  this_app.sendEvent('listBig', {since: since, uuid: this_uuid}, function(e, r) {
    if (e) {
      console.log('App error (Update): ' + e);
    } else {
      var info = JSON.parse(r);

      // Display the last image 
      var new_index = info.length - 1;
      console.log(new_index);
      console.log(info[new_index]);
      console.log(info[new_index].id);
      if (info[0]) {
        this_app.picture.src = '/?action=retrieveBig&uuid=' + this_uuid + '&id=' + info[info.length-1].id; // Oldest first order, start from end
      }
    }
  });
};

////////////////////////////////// Some "Private" Methods //////////////////////
MyApp.prototype.getAllElements = function(){
  this.data_div = this.getElement("data");
  this.picture = this.getElement("picture");
  this.stop_button = this.getElement("stop");
  this.start_button = this.getElement("start");
  this.victory_button = this.getElement("victory");
};

//spec says app needs to be named App
var App = MyApp;
