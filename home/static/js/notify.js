$(document).ready(function() {
    $(".notify").click(function() {
        var regexp = /notify(\d+)/;
        var due_id_matches = regexp.exec(this.id)
        var due_id = due_id_matches[1]
        console.log(due_id);
        if(!isNaN(due_id))
            $.getJSON("/notify?due_id=" + due_id, function(data) {
              console.log(JSON.parse(data));
            })
    });
});