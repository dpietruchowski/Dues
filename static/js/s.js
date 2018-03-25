$(document).ready(function() {
    $("img").mouseover(function() {
        $(this).addClass("dues-active");
    });
    $("img").mouseout(function() {
        $(this).removeClass("dues-active");
    });
});