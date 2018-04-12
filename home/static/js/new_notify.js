function notify() {
    $.getJSON("/new_notify", function(data) {
        var response = JSON.parse(data);
        var new_notifications = parseInt(response["new_notifications"]);
        if(new_notifications > 0)
            $("#notification_button").addClass("new_notify")
        else
            $("#notification_button").removeClass("new_notify")
        console.log(new_notifications);
    });
}

$(document).ready(function() {
    notify();
    setInterval(notify, 5000);
});