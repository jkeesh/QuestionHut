var no_logging = function() {};
no_logging.log = function() {};
no_logging.info = function(){};
window.debug = DEBUG_ON ? console: no_logging;
window.D = window.debug;

$(document).ajaxSend(function(event, xhr, settings) {
    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie != '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = jQuery.trim(cookies[i]);
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) == (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    function sameOrigin(url) {
        // url could be relative or scheme relative or absolute
        var host = document.location.host; // host + port
        var protocol = document.location.protocol;
        var sr_origin = '//' + host;
        var origin = protocol + sr_origin;
        // Allow absolute or scheme relative URLs to same origin
        return (url == origin || url.slice(0, origin.length + 1) == origin + '/') ||
            (url == sr_origin || url.slice(0, sr_origin.length + 1) == sr_origin + '/') ||
            // or any other URL that isn't scheme relative or absolute i.e relative.
            !(/^(\/\/|http:|https:).*/.test(url));
    }
    function safeMethod(method) {
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    }

    if (!safeMethod(settings.type) && sameOrigin(settings.url)) {
        xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
    }
});


$(document).ready(function(){
    var path = window.location.pathname;
    if(path.indexOf('question') != -1){
        var voter = new Voter();
    }
});

function Voter(){
    var that = {}
    
    that.setup = function(){
        $('.vote-arrow').click(function(e){
            e.preventDefault();
            var action = $(this).attr('data-action');
            var type = $(this).attr('data-type');
            var id = $(this).attr('data-id');

            $.ajax({
                type: 'POST',
                url: '/ajax/vote',
                dataType: 'JSON',
                data: {
                    action: action,
                    type: type,
                    id: id
                },
                success: function(result){
                    result = $.parseJSON(result);
                    D.log(result);
                }
            });
        });
    }
    
    
    
    that.setup();
    return that;
}