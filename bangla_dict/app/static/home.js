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
    if (word.defs)
    {
        for (var i = 0; i < word.defs.length; i++)
        {
            var def = word.defs[i];
            var defLine = '(' + getPartOfSpeechDisplay(def.part_of_speech) + ') ' + def.english_word;
            wrapper.appendNewChild('DIV').appendNewChild('SPAN').text(defLine);
            if (def.definition)
            {
                var defLine = 'Definition: ' + def.definition;
                wrapper.appendNewChild('DIV', '', 'DefSection').text(defLine);
            }
            if (def.notes)
            {
                var notesLine = 'Notes: ' + def.notes;
                wrapper.appendNewChild('DIV', '', 'DefSection').text(notesLine);
            }
        }
    }
    var bottomWrapper = wrapper.appendNewChild('DIV');
    var button = bottomWrapper.appendNewChild('BUTTON', '', 'LinkLikeButton');
    button.attr('xsamsadurl', word.samsad_url);
    button.text('Samsad');
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
        var addDefLink = resultsElem.appendNewChild('A');
        addDefLink.text('Add Definition for ' + result.word);
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

function onAjaxSuccess(result)
{
    if (result.word != $('#BanglaWord').val() && result.word != avro.parse($('#BanglaWord').val()))
        return;

    handleResults(result);
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

    if ($('#BanglaWord').val())
        doAjaxLookup();

    $(document).bind('click', function(event) {
        var button = $(event.target).closest('BUTTON[xsamsadurl]');
        if (!button.length)
            return;

        loadSamsadPane(button.attr('xsamsadurl'));
    });

    History.Adapter.bind(window,'popstate',function() {
        var state = History.getState(); // Note: We are using History.getState() instead of event.state
        if (state)
        {
            var result = state.data;
            $('#BanglaWord').val(result.word);
            handleResults(result);
        }
    });
});

})();
