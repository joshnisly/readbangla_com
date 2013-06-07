(function() {
var timer = null;
var lookupUrl = '/words/lookup/ajax/';
var lookupUrl = '/words/lookup/ajax/';
var avro = OmicronLab.Avro.Phonetic;
var lastResult = null;

function isAscii(str)
{
    for (var i = 0; i < str.length; i++)
    {
        if (str[i] < 32 || str[i] > 126)
            return false;
    }

    return true;
}

function onAjaxSuccess(result)
{
    if (result.word != $('#BanglaWord').val())
        return;

    lastResult = result.word;

    $('#Throbber').hide();
    $('#LookupBtn').show();
    $('#Results').empty()
    if (result.dict_matches.length)
    {
        $('#Results').appendNewChild('H3').text('Matches with definitions');
        for (var i = 0; i < result.dict_matches.length; i++)
        {
            var match = result.dict_matches[i];
            var wordWrapper = $('#Results').appendNewChild('DIV', '', 'WordMatch WithDef');
            wordWrapper.appendNewChild('A', '', 'Bangla').text(match.word).attr('href', match.link);
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
            var wordWrapper = $('#Results').appendNewChild('DIV', '', 'WordMatch Bangla');
            wordWrapper.text(match.word);
        }
    }
}

function doAjaxLookup()
{
    var bangla = $('#BanglaWord').val();
    if (!bangla || bangla == lastResult)
        return;

    if (isAscii(bangla))
    {
        bangla = avro.parse(bangla);
        $('#BanglaWord').val(bangla);
    }
    $('#Throbber').show();
    $('#LookupBtn').hide();
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
    timer = window.setTimeout(doAjaxLookup, 2000);
}

$(document).ready(function() {
    $('#BanglaWord').bind('input', onWordChange);
    $('#BanglaWord').bind('keydown', function(event) {
        if (event.keyCode == 13)
            doAjaxLookup();
    });
    $('#LookupBtn').bind('click', doAjaxLookup);
});

})();
