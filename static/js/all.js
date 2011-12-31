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
    var converter = new Showdown.converter();

    if(path.indexOf('question') != -1){
        var voter = new Voter();
        var selector = new AnswerSelector();
        new QuestionDeleter();
        $(".showdown").each(function(i){
            D.log($(this));
            var text = $(this).html();
            D.log(text);
            var formatted = converter.makeHtml(text);
            D.log(formatted);
            $(this).html(formatted);
        });
        
        $("#user_input").keyup(function(){
          var txt = $("#user_input").val();
          var html = converter.makeHtml(txt);
          $(".wikistyle").html(html)
          $("#entry-container, #user_input").css({
            height: $(".wikistyle").outerHeight()+40
          })

        });
        new Preview({
            input: '#answer_area',
            dest: '#live_preview',
            converter: converter
        });
    }
    if(path.indexOf('moderate') != -1){
        var approver = new Approver();
    }
    
    if(path.indexOf('huts') != -1){
        var jointer = new Joiner();
    }
    
    if(path.indexOf('ask') != -1){
        new Preview({
            input: '#question_textarea',
            dest: '#live_preview',
            converter: converter
        });
    }
    
    if(typeof INFINITE_SCROLL !== 'undefined' && INFINITE_SCROLL){
        D.log('infinite scroll on');
    }
});

/*
 * Setup a automatic preview from
 * @param   options {Object}    options object
 *  -   input   {string}    selector for the input field
 *  -   dest    {string}    selector for the preview field
 *  -   converter   {Object}    the showdown converter
 */
function Preview(options){
    $(options.input).keyup(function(){
       var txt = $(this).val();
       var html = options.converter.makeHtml(txt);
       $(options.dest).html(html); 
    });
}


function Joiner(){
    var that = {};
    
    that.setup = function(){
        $('a[data-join]').click(function(){
             var hut_to_join = $(this).attr('data-join');
             D.log(hut_to_join);
             that.join(hut_to_join);
        });
        
        $('a[data-drop]').click(function(){
            var hut_to_join = $(this).attr('data-drop');
            that.drop(hut_to_join);
        });
    }
    
    that.join = function(hut){
        $.ajax({
            type: "POST",
            url: '/ajax/join_hut',
            dataType: 'JSON',
            data: {
                hut: hut
            },
            success: function(result){
                D.log(result);
                if(result.status == 'ok'){
                    window.location.reload();
                }
            }
        });
    
    }
    
    that.drop = function(hut){
        $.ajax({
            type: "POST",
            url: '/ajax/drop_hut',
            dataType: 'JSON',
            data: {
                hut: hut
            },
            success: function(result){
                D.log(result);
                if(result.status == 'ok'){
                    window.location.reload();
                }
            }
        });
    }
    
    
    that.setup();
    return that;
}


function AnswerSelector(){
    var that = {};
    
    that.get_data = function(link){
        return {
            question: $(link).attr('data-question'),
            answer: $(link).attr('data-id')
        };
    }
    
    that.setup = function(){
        $('.answer-select').click(function(){
            var self = $(this);
            $.ajax({
                type: 'POST',
                url: '/ajax/select_answer',
                dataType: 'JSON',
                data: that.get_data(self),
                success: function(result){
                    D.log(result);
                    $('.answer-select').removeClass('chosen-answer');
                    self.addClass('chosen-answer');
                    
                    // if(result.status == 'ok'){
                    //      that.remove_box(self);
                    // }else{
                    //     alert('Fail.');
                    // }
                }
            });
        });
    }
    
    that.setup();
    return that;
}


function Approver(){
    var that = {};

    that.get_data = function(link){
        var action = $(link).attr('data-action');
        var id = $(link).attr('data-id'); 
        var kind = $(link).attr('data-kind'); 
        
        return {
            action: action,
            id: id,
            kind: kind
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


function QuestionDeleter(){
    var that = {};
    
    that.setup = function(){
        $('#delete_question').click(function(){
            if(confirm('Are you sure you want to delete this question?')){
                var qid = $(this).attr('data-id');
                $.ajax({
                    type: 'POST',
                    url: '/ajax/delete',
                    dataType: 'JSON',
                    data: {
                        qid: qid
                    },
                    success: function(result){
                        D.log(result);
                        if(result.status == "ok"){
                            window.location.href = '/';
                        }
                    }
                });
            }
        });
    }
    
    that.setup();
    return that;
}