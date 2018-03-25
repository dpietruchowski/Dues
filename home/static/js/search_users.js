var beneficiary_dict = {};
var sum_of_contribution = 0;

function add_beneficiary_form(username) {
    var form_idx = $('#id_form-TOTAL_FORMS').val();
    var new_item = $('#empty_form').html().replace(/__prefix__/g, form_idx).replace(/__username__/g, username);
    $('#form_set').append(new_item);
    var acc_input = '#id_form-' + form_idx + '-account_id';
    $(acc_input).val(username);
    $(acc_input).attr('type', 'hidden');
    var contribution_input = '#id_form-' + form_idx + '-contribution';
    $(contribution_input).val(0);
    $('#id_form-TOTAL_FORMS').val(parseInt(form_idx) + 1);
}

function add_beneficiary(username) {
    if(username in beneficiary_dict) {
        return;
    }
    beneficiary_dict[username] = 0;
    add_beneficiary_form(username);
}

function change_id(formName, oldFormIdx) {
    oldName = "form-" + oldFormIdx + "-" + formName;
    newName = "form-" + (parseInt(oldFormIdx) - 1) + "-" + formName;
    oldId = "#id_" + oldName;
    newId = "id_" + newName;
    $(oldId).attr('name', newName);
    if (formName === "button") {
        $(oldId).attr('data-form-idx', (parseInt(oldFormIdx) - 1));
    }
    $(oldId).attr('id', newId);
}

function delete_beneficiary(username, form_id) {
    console.log(username);
    console.log(form_id);
    if(username in beneficiary_dict) {
        var total_forms = $('#id_form-TOTAL_FORMS').val();
        var acc_id = "#id_form-" + form_id + "-contribution";
        var sum_of_contribution = parseFloat($('#sum_of_contribution').text());
        sum_of_contribution = sum_of_contribution - parseFloat($(acc_id).val());
        $('#sum_of_contribution').text(sum_of_contribution.toFixed(2));
        var id = "#id_form-" + form_id + "-tr";
        $(id).remove();
        for (var i = parseInt(form_id) + 1; i < total_forms; i++) {
            change_id("account_id", i);
            change_id("contribution", i);
            change_id("tr", i);
            change_id("button", i);
        }
        $('#id_form-TOTAL_FORMS').val(total_forms - 1);
        delete beneficiary_dict[username];
    }
}

$(document).ready(function() {
    sum_of_contribution = parseInt($("#sum_of_contribution").text());
    var total_forms = $('#id_form-TOTAL_FORMS').val();
    for (var i = 0; i < total_forms; i++) {
        id = "#id_form-" + i + "-account_id";
        username = $(id).val();
        beneficiary_dict[username] = 0;
    }

    $("#search_user").click(function() {
        var query_val = $("#search_user_text").val();
        console.log(query_val);
        $('#search_user_list').empty();
        $.getJSON("/accounts?query=" + query_val, function(data) {
          console.log(JSON.parse(data));
          $.each( JSON.parse(data), function(key,  val) {
            var row = "<tr><td>" + key + "</td><td>" + val + "</td>"
            row += "<td><input class='btn btn-primary add_beneficiary' type='button' value='Dodaj' id='"
            row += val + "'/></td></tr>";
            $('#search_user_list').append(row);
          });
        })
    });

    $('#add_beneficiary_wrapper').off().on('click', '.add_beneficiary', function() {
        var selected_username = $(this).attr('id');
        console.log(selected_username);
        add_beneficiary(selected_username)
    });

    $('#form_set').off().on('click', '.delete_beneficiary', function() {
        var selected_username = $(this).attr('data-username');
        var form_idx = $(this).attr('data-form-idx');
        delete_beneficiary(selected_username, form_idx)
    });

    $(document).on('focusin', '#beneficiary_table :enabled', function() {
        var value = parseFloat($(this).val());
        if(isNaN(value))
            value = 0;
        $(this).data('val', value);
    })
    $('#beneficiary_table').off().on('change', ':enabled', function() {
        var prev_value = parseFloat($(this).data('val'));
        $(this).data('val', $(this).val());
        var value = parseFloat($(this).val());
        if(isNaN(value))
            value = 0;
        var sum_of_contribution = parseFloat($('#sum_of_contribution').text());
        console.log(prev_value);
        console.log(value);
        console.log(sum_of_contribution);
        sum_of_contribution = sum_of_contribution - (prev_value - value);
        $('#sum_of_contribution').text(sum_of_contribution.toFixed(2));
    })
});