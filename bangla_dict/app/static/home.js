(function() {
var timer = null;
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

    if (result.dict_matches.length + result.word_matches.length == 1 && false)
    {
        var singleMatch = result.dict_matches.length > 0 ? result.dict_matches[0] : result.word_matches[0];
        window.location = singleMatch.view_url;
    }

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
            wordWrapper.appendNewChild('A', '', 'Bangla').text(match.word).attr('href', match.view_url);
            for (var iDef = 0; iDef < match.defs.length; iDef++)
                wordWrapper.appendNewChild('SPAN').text(' - ' + match.defs[iDef]);
        }
    }
    if (result.word_matches.length)
    {
        $('#Results').appendNewChild('H3').text('Word matches');
        for (var i = 0; i < result.word_matches.length; i++)
        {
            var match = result.word_matches[i];
            var wordWrapper = $('#Results').appendNewChild('DIV', '', 'WordMatch');
            wordWrapper.appendNewChild('SPAN', '', 'Bangla').text(match.word + ' - ');
            wordWrapper.appendNewChild('A').text('Add definition').attr('href', match.add_def_url);
            wordWrapper.appendNewChild('SPAN').text(' Request definition');
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
