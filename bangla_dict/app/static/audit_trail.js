(function() {
function onRowClick(event)
{
    var row = $(event.target).closest('TR');
    row.next('TR').toggle();
}

$(document).ready(function() {
    $('TR').bind('click', onRowClick);

    $('TH').removeAttr('colspan');
});
})();
