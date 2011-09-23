var no_logging = function() {};
no_logging.log = function() {};
no_logging.info = function(){};
window.debug = DEBUG_ON ? console: no_logging;
window.D = window.debug;

$(document).ready(function(){
    var path = window.location.pathname;
    if(path.indexOf('question') != -1){
        var question = new Question();
    }
});

function Question(){
    var that = {}
    
    that.setup = function(){
        $('.vote-arrow').click(function(e){
            e.preventDefault();
            D.log('clicked');
        });
    }
    
    
    
    that.setup();
    return that;
}