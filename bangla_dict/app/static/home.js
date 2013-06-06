(function() {
var timer = null;
var lookupUrl = '/words/lookup/ajax/';
var lookupUrl = '/words/lookup/ajax/';

function onAjaxSuccess(result)
{
    if (result.word != $('#BanglaWord').val())
        return;

    $('#Throbber').hide();
    $('#Results').empty()
    if (result.dict_matches.length)
    {
        $('#Results').appendNewChild('H3').text('Matches with definitions');
        for (var i = 0; i < result.dict_matches.length; i++)
        {
            var match = result.dict_matches[i];
            var wordWrapper = $('#Results').appendNewChild('DIV', '', 'WordMatch WithDef');
            wordWrapper.appendNewChild('A').text(match.word).attr('href', match.link);
            for (var iDef = 0; iDef < match.defs.length; iDef++)
                wordWrapper.appendNewChild('SPAN').text(' - ' + match.defs[iDef]);
        }
    }
    if (result.word_matches.length)
    {
        $('#Results').appendNewChild('H3').text('Other matches');
        for (var i = 0; i < result.word_matches.length; i++)
        {
            var match = result.word_matches[i];
            var wordWrapper = $('#Results').appendNewChild('DIV', '', 'WordMatch');
            wordWrapper.text(match.word);
        }
    }
}

function doAjaxLookup()
{
    var bangla = $('#BanglaWord').val();
    if (!bangla)
        return;

    $('#Throbber').show();
    doAjax({
        url: lookupUrl,
        data: {'word': bangla},
        success: onAjaxSuccess
    });
}

function onWordChange()
{
    if (timer)
    {
        window.clearTimeout(timer)
        timer = null;
    }
    timer = window.setTimeout(doAjaxLookup, 500);
}

$(document).ready(function() {
    $('#BanglaWord').bind('input', onWordChange);
});

})();
