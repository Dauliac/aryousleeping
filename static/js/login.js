$(document).ready(function(){
  $('.focus').focus();
  $(document).keypress(function(e) {
    if(e.which == 13) {
        var user = $('.user');
        var send = $('.send');
        var pass = $('.pass');
   	$('.focus').focus();
      if(user.hasClass('visible')){
        user.removeClass('visible').fadeOut(function(){
          pass.addClass('visible').fadeIn(function(){
            $('.loginput').focus();
          });
          
        });
    }else if(pass.hasClass('visible')){
          $('#login').submit();
    }
    }
});
  
});

