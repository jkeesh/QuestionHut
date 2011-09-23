var no_logging = function() {};
no_logging.log = function() {};
no_logging.info = function(){};
window.debug = DEBUG_ON ? console: no_logging;
window.D = window.debug;

$(document).ready(function(){
    D.log(window.location.href);

//    alert('hello');

});