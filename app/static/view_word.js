function showPromptLightbox(title, okBtnText, elem, onOK)
{
    var buttons = [{
        text: okBtnText,
        title: null,
        isPrimary: true,
        callback: onOK 
    },
    {
        text: 'Cancel',
        title: null,
        isPrimary: false,
        callback: function() {InvModal.close()}
    }]
    InvModal.open(title, elem, buttons)
}

function showFlagLightbox(event)
{
    var defID = parseInt($(event.target).attr('xdefid'), 10);
    function flagAjax()
    {
        doAjax({
            url: '/words/flag_def/',
            data: {
                'def_id': defID,
                'reason': $('#FlagReasonInput').val()
            },
            success: function() {
                $(event.target).closest('.Definition').appendNewChild('P', '', 'Message').text('This definition has been flagged for review.');
            }
        });
    }
    var promptElem = $(event.target).closest('.Definition').find('.FlagPrompt')
    showPromptLightbox('Flag for review', 'Flag', promptElem, flagAjax);
}

function showDeleteLightbox(event)
{
    var defID = parseInt($(event.target).attr('xdefid'), 10);
    function deleteAjax()
    {
        doAjax({
            url: '/words/delete_def/',
            data: {'def_id': defID},
            success: function() {
                var def = $(event.target).closest('.Definition');
                def.empty();
                def.appendNewChild('P', '', 'Message').text('This definition has been deleted.');
            }
        });
    }
    var promptElem = $(event.target).closest('.Definition').find('.DeletePrompt')
    showPromptLightbox('Delete definition', 'Delete', promptElem, deleteAjax);
}

$(document).ready(function() {
    $('.ShowOptions').bind('click', function (event) {
        $(event.target).closest('.Definition').addClass('ShowingOptions');
    });
    $('.HideOptions').bind('click', function (event) {
        $(event.target).closest('.Definition').removeClass('ShowingOptions');
    });

    // Editing
    $('.EditBtn').bind('click', function (event) {
        $(event.target).closest('.Definition').addClass('Editing');
    });
    $('.CancelEditBtn').bind('click', function (event) {
        $(event.target).closest('.Definition').removeClass('Editing');
    });

    // Flag for review
    $('.FlagBtn').bind('click', showFlagLightbox);

    // Delete
    $('.DeleteBtn').bind('click', showDeleteLightbox);
});
