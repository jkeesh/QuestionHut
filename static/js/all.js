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
    if(path.indexOf('moderate') != -1){
        var approver = new Approver();
    }
});


function Approver(){
    var that = {};

    that.get_data = function(link){
        var action = $(link).attr('data-action');
        var id = $(link).attr('data-id');  
        
        return {
            action: action,
            id: id
        }
    }

    that.remove_box = function(link){
        var box = link.parent().parent();
        box.css('background-color', '#eee');
        box.fadeOut();
    }

    that.setup = function(){
        $('.question-moderate a').click(function(){
           
           var self = $(this);
           $.ajax({
               type: 'POST',
               url: '/ajax/moderate',
               dataType: 'JSON',
               data: that.get_data(self),
               success: function(result){
                   if(result.status == 'ok'){
                        that.remove_box(self);
                   }else{
                       alert('Fail.');
                   }
               }
           });

        });
    }


    that.setup();
    return that;
}


function Voter(){
    var that = {}
    
    that.get_vote_count = function(arrow){
        return $('.vote-count[data-type="'+ arrow.attr('data-type')+'"][data-id="'+ arrow.attr('data-id')+'"]')
    }
    
    
    
    that.get_data = function(arrow){
        var action = arrow.attr('data-action');
        var type = arrow.attr('data-type');
        var id = arrow.attr('data-id');
        return {
            action: action,
            type: type,
            id: id
        }
    }
    
    that.deselect_votes = function(arrow){
        $('.vote-arrow[data-id="'+arrow.attr('data-id')+'"]').removeClass('voted');
    }
    
    that.setup = function(){
        $('.vote-arrow').click(function(e){
            var self = $(this);
            e.preventDefault();
            var vote_count = that.get_vote_count($(this));

            $.ajax({
                type: 'POST',
                url: '/ajax/vote',
                dataType: 'JSON',
                data: that.get_data(self),
                success: function(result){
                    if(result.status == 'ok'){
                        vote_count.html(result.votes);
                        already_selected = self.hasClass('voted');
                        that.deselect_votes(self);
                        if(already_selected){
                            self.removeClass('voted');
                        }else{
                            self.addClass('voted');
                        }
                    }
                }
            });
        });
    }
    
    
    
    that.setup();
    return that;
}