(function() {
    var wordAjaxUrl = '/entry/new_word_ajax/';
    function checkWord(event)
    {
        var bangla = $('#id_bangla_word').val()
        if (!bangla)
            return;

        $(event.target).closest('.Action').addClass('InProgress');

        doAjax({
            url: wordAjaxUrl,
            data: {'word': bangla}
        });
    }

    $(document).ready(function() {
        $('#CheckWordBtn').bind('click', checkWord);
    });
})();
