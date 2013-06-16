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
    if (result.word != $('#BanglaWord').val() && result.word != avro.parse($('#BanglaWord').val()))
        return;

    if (result.redirect_url)
        window.location = result.redirect_url;

    lastResult = result.word;

    $('#Throbber').hide();
    $('#Results').empty()
    if (result.dict_matches.length == 0 && result.word_matches.length == 0)
    {
        $('#Results').appendNewChild('H3').text('No matches for ' + result.word + ' found.');
        return;
    }

    if (result.dict_matches.length)
    {
        $('#Results').appendNewChild('H3').text('Matches for ' + result.word + ' with definitions');
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
        $('#Results').appendNewChild('H3').text('Word matches for ' + result.word);
        for (var i = 0; i < result.word_matches.length; i++)
        {
            var match = result.word_matches[i];
            var wordWrapper = $('#Results').appendNewChild('DIV', '', 'WordMatch');
            wordWrapper.appendNewChild('SPAN', '', 'Bangla').text(match.word + ' -');
            var button = wordWrapper.appendNewChild('BUTTON', '', 'LinkLikeButton');
            button.text('Samsad').attr('xurl', match.samsad_url);
            button.bind('click', function(event) {
                var pane = $('#SamsadPane')[0];
                var url = $(event.target).attr('xurl');
                if (pane.src != url)
                    pane.src = url;
            });
            wordWrapper.appendNewChild('A').text('Add definition').attr('href', match.add_def_url);
            wordWrapper.appendNewChild('SPAN').text(' Request definition');
        }
    }
}

function doAjaxLookup()
{
    var bangla = $('#BanglaWord').val();
    if (!bangla)
        return;

    if (isAscii(bangla))
        bangla = avro.parse(bangla);

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
    $('#LookupBtn').show();
    if (timer)
    {
        window.clearTimeout(timer)
        timer = null;
    }
    timer = window.setTimeout(doAjaxLookup, 2000);
}

$(document).ready(function() {
    $('#BanglaWord').bind('input', onWordChange);
    $('INPUT[type=radio]').bind('change', onWordChange);
    $('#BanglaWord').bind('keydown', function(event) {
        if (event.keyCode == 13)
            doAjaxLookup();
    });
    $('#LookupBtn').bind('click', doAjaxLookup);

    $('INPUT[type=radio]').bind('change', function(event) {
        $('.RadioLabel').removeClass('Checked');
        $(event.target).closest('LABEL').addClass('Checked');
    })
});

})();
