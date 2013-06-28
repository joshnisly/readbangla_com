(function() {
var lookupUrl = '/words/lookup/ajax/';
var avro = OmicronLab.Avro.Phonetic;
var lastResult = null;

function isAscii(str)
{
    for (var i = 0; i < str.length; i++)
    {
        if (str[i] > 126)
            return false;
    }

    return true;
}

function getPartOfSpeechDisplay(type)
{
    for (var i = 0; i < partsOfSpeech.length; i++)
    {
        if (partsOfSpeech[i][0] == type)
           return partsOfSpeech[i][1];
    }
    return '(Unknown)';
}

function loadSamsadPane(url)
{
    var pane = $('#SamsadPane')[0];
    if (pane.src != url)
        $('#SamsadPane')[0].contentWindow.location.replace(url);
};

function createDefSection(word, parent)
{
    var wrapper = parent.appendNewChild('DIV', '', 'WordSection')
    var titleElem = wrapper.appendNewChild('DIV', '', 'WordTitle Bangla');
    titleElem.appendNewChild('A').attr('href', word.view_url).text(word.word);
    var button = titleElem.appendNewChild('BUTTON', '', 'LinkLikeButton');
    button.css('margin-left', '2em');
    button.attr('xsamsadurl', word.samsad_url);
    button.text('Samsad');
    if (word.edit_samsad_url)
    {
        var editSamsadLink = titleElem.appendNewChild('A', '', 'EditSamsadLink');
        editSamsadLink.text('(edit)')
        editSamsadLink.attr('href', word.edit_samsad_url);
    }
    if (word.defs)
    {
        for (var i = 0; i < word.defs.length; i++)
        {
            var def = word.defs[i];
            var defWrapper = wrapper.appendNewChild('DIV', '', 'WordDefWrapper');
            var defLine = '(' + getPartOfSpeechDisplay(def.part_of_speech) + ') ' + def.english_word;
            defWrapper.appendNewChild('DIV').appendNewChild('SPAN').text(defLine);
            if (def.definition)
            {
                var defLine = 'Definition: ' + def.definition;
                defWrapper.appendNewChild('DIV', '', 'DefSection').text(defLine);
            }
            if (def.notes)
            {
                var notesLine = 'Notes: ' + def.notes;
                defWrapper.appendNewChild('DIV', '', 'DefSection').text(notesLine);
            }

            var addedWrapper = defWrapper.appendNewChild('DIV', '', 'WordAddedWrapper');
            var addedLine = 'Added by ' + def['added_by'];
            addedLine += ' on ' + def['added_on_date'] + ' ' + def['added_on_time'];
            addedWrapper.text(addedLine)
        }
    }
    var bottomWrapper = wrapper.appendNewChild('DIV');
    bottomWrapper.appendNewChild('A').attr('href', word.add_def_url).text('Add Definition');
}

function createSingleWordResults(result)
{
    var resultsElem = $('#Results');

    var hasResults = result.dict_matches.length || result.word_matches.length;

    if (!hasResults)
        resultsElem.appendNewChild('H3').text('No matches for ' + result.word + ' found.');

    if (result.add_def_url)
    {
        var addDefLink = resultsElem.appendNewChild('A').css({
            'display': 'inline-block',
            'margin-bottom': '2em'
        });
        addDefLink.text('Add Definition for ' + result.corrected_word);
        addDefLink.attr('href', result.add_def_url);
    }

    if (!hasResults)
        return;

    for (var i = 0; i < result.dict_matches.length; i++)
    {
        var match = result.dict_matches[i];
        createDefSection(match, resultsElem);
    }

    if (result.word_matches.length)
        resultsElem.appendNewChild('H3').text('Possible matches');

    for (var i = 0; i < result.word_matches.length; i++)
    {
        var match = result.word_matches[i];
        createDefSection(match, resultsElem);
    }

    if (result.dict_matches.length + result.word_matches.length == 1)
    {
        var singleResult = result.dict_matches[0] || result.word_matches[0];
        loadSamsadPane(singleResult.samsad_url);
    }
}

function createPhraseResults(result)
{
    var resultsElem = $('#Results');
    resultsElem.appendNewChild('H3').text('Transliteration');
    for (var i = 0; i < result.words.length; i++)
    {
        var word = result.words[i];
        var wordWrapper = resultsElem.appendNewChild('DIV', '', 'ResultWord');
        wordWrapper.appendNewChild('SPAN', '', 'Bangla').text(word.word);
        wordWrapper.appendNewChild('BR');
        if (word.dict_matches.length)
        {
            var match = word.dict_matches[0];
            var def = match.defs[0];
            var samsadBtn = wordWrapper.appendNewChild('BUTTON', '', 'LinkLikeButton Bangla');
            samsadBtn.attr('xsamsadurl', match.samsad_url);
            samsadBtn.attr('xdef', word);
            samsadBtn.text(def.english_word);
        }
        else if (word.word_matches.length)
        {
            var match = word.word_matches[0];
            var samsadBtn = wordWrapper.appendNewChild('BUTTON', '', 'LinkLikeButton Bangla');
            samsadBtn.attr('xsamsadurl', match.samsad_url);
            samsadBtn.attr('xdef', word);
            samsadBtn.text(match.word);
        }
    }
}

function handleResults(result)
{
    lastResult = result.word;

    if (window.History && result.word_url && result.word_url != window.location.pathname)
        window.History.pushState(result, 'Lookup results', result.word_url);

    var resultsElem = $('#Results');
    $('#Throbber').hide();
    resultsElem.empty()
    loadSamsadPane('about:blank');

    if (result.phrase)
        createPhraseResults(result);
    else
        createSingleWordResults(result);
}

function onAjaxSuccess(result, origPost)
{
    if (origPost.word != $('#BanglaWord').val())
        return;

    handleResults(result);
}

function onAjaxError()
{
    $('#Results').empty();
    $('#Results').appendNewChild('H3').text('Unable to lookup word.');
    $('#Throbber').hide();
    $('#LookupBtn').show();
    $('#LookupBtn').addClass('invBtnDanger').text('Retry');
}

function doAjaxLookup()
{
    var bangla = $('#BanglaWord').val();
    if (!bangla)
        return;

    if (isAscii(bangla))
        bangla = avro.parse(bangla);

    $('#BanglaWord').val(bangla);

    // Clear any prior errors
    $('#LookupBtn').text('Lookup').removeClass('invBtnDanger');

    $('#Results').empty();
    $('#Throbber').show();
    $('#LookupBtn').hide();
    doAjax({
        url: lookupUrl,
        data: {'word': bangla},
        timeout: 15*1000,
        success: onAjaxSuccess,
        error: onAjaxError
    });
}

function onWordChange()
{
    $('#LookupBtn').show();
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

    var preloadedData = $('#Results').attr('xWordData');
    if (preloadedData)
    {
        preloadedData = JSON.parse(preloadedData);
        handleResults(preloadedData);
        $('#LookupBtn').hide();
    }
    else if ($('#BanglaWord').val())
        doAjaxLookup();

    $(document).bind('click', function(event) {
        var button = $(event.target).closest('BUTTON[xsamsadurl]');
        if (!button.length)
            return;

        loadSamsadPane(button.attr('xsamsadurl'));
    });

    History.Adapter.bind(window,'popstate',function() {
        var state = History.getState(); // Note: We are using History.getState() instead of event.state
        if (state && state.data.word)
        {
            var result = state.data;
            $('#BanglaWord').val(result.word);
            handleResults(result);
        }
    });
});

})();
