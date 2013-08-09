(function() {
var lookupAjaxUrl = '/words/lookup/ajax/';
var lookupLinkUrl = '/lookup/';
var avro = OmicronLab.Avro.Phonetic;
var lastResult = null;

var isShowingBanglaChart = false;

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

function buildLookupUrl(word)
{
    return lookupLinkUrl + word + '/';
}

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

        if (word.audio_links && word.audio_links.length)
        {
            if (isAuthenticated())
            {
                for (var i = 0; i < word.audio_links.length; i++)
                {
                    var audioDiv = titleElem.appendNewChild('DIV', '', 'AudioWrapper')
                                            .css('display', 'inline-block');
                    var audioTag = document.createElement('audio');
                    var canPlayMp3 = audioTag.canPlayType && audioTag.canPlayType('audio/mpeg');
                    var canPlayOgg = audioTag.canPlayType && audioTag.canPlayType('audio/ogg');
                    if (canPlayMp3 || canPlayOgg)
                    {
                        var audioIcon = audioDiv.appendNewChild('IMG', '', 'AudioIcon');
                        // Icon from https://www.iconfinder.com/icondetails/103711/32/louder_speaker_icon
                        audioIcon.attr('src', '/static/speaker.png');
                        audioIcon.css({
                            'height': '20px',
                            'margin-left': '10px'
                        });
                        var audioElem = audioDiv.appendNewChild('AUDIO');
                        if (canPlayOgg)
                        {
                            audioElem.attr('src', word.audio_links[i] + '?type=ogg');
                            audioElem.attr('type', 'audio/ogg');
                        }
                        else
                        {
                            audioElem.attr('src', word.audio_links[i]);
                            audioElem.attr('type', 'audio/mpeg');
                        }
                    }
                    else
                    {
                        // Fall back to using Flash.
                        var audioID = word.word + i;
                        var flashWrapper = audioDiv.appendNewChild('SPAN', audioID);
                        audioDiv.css('margin-left', '10px');
                        AudioPlayer.embed(audioID, {soundFile: word.audio_links[i]});
                    }
                }
            }
            else
            {
                var textElem = titleElem.appendNewChild('SPAN').text('(Log in to listen to recordings of this word.)');
                textElem.css({
                    'font-size': '10px',
                    'margin-left': '10px'
                });
            }
        }
    }
    if (word.defs)
    {
        for (var i = 0; i < word.defs.length; i++)
        {
            var def = word.defs[i];
            var defWrapper = wrapper.appendNewChild('DIV', '', 'WordDefWrapper');
            var defLine = '(' + getPartOfSpeechDisplay(def.part_of_speech) + ') ' + def.english_word + ' ';
            var defLineWrapper = defWrapper.appendNewChild('DIV');
            defLineWrapper.appendNewChild('SPAN').text(defLine);
            if (def.definition)
            {
                var defLine = 'Definition: ' + def.definition;
                appendTextWithBanglaLinks(defWrapper.appendNewChild('DIV', '', 'DefSection'), defLine, buildLookupUrl);
            }
            if (def.notes)
            {
                var notesLine = 'Notes: ' + def.notes;
                appendTextWithBanglaLinks(defWrapper.appendNewChild('DIV', '', 'DefSection'), notesLine, buildLookupUrl);
            }

            var bottomWrapper = defWrapper.appendNewChild('DIV', '', 'BottomWrapper');
            var addedWrapper = bottomWrapper.appendNewChild('DIV', '', 'WordAddedWrapper');

            // Create "Added by" box
            var addedDate = new Date(def['added_on'] * 1000);
            var addedLine = 'Added ' + addedDate.toString('MMM d')
            if (addedDate.getYear() != (new Date()).getYear())
                addedLine += addedDate.toString(' \'yy')
            addedLine += ' at ' + addedDate.toString('h:mm tt');
            addedLine += '\nby ' + def['added_by'];
            addedWrapper.text(addedLine)

            bottomWrapper.appendNewChild('A', '', 'EditDefLink').attr('href', def.edit_def_url).text('edit');
            if (def.num_edits)
            {
                bottomWrapper.appendNewChild('SPAN').text(' | ');
                bottomWrapper.appendNewChild('BUTTON', '', 'LinkLikeButton ToggleEditsBtn').attr('href', def.edit_def_url).text(def.num_edits + ' edits');
            }
            bottomWrapper.appendNewChild('DIV').css('clear', 'both');
            if (def.num_edits)
                bottomWrapper.appendNewChild('DIV', '', 'EditsWrapper').html(def.edits_html)
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
        resultsElem.appendNewChild('H3').text('No matches for ' + result.corrected_word + ' found.');

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

    if (window.History &&
        result.word_url &&
        result.word_url != window.location.pathname &&
        result.word_url.length < 100)
    {
        window.History.pushState(result, result.corrected_word + ' - ReadBangla.com', result.word_url);
    }
    document.title = result.corrected_word + ' - ReadBangla.com';
    $('#BanglaWord').val(result.corrected_word);

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

    var isEnglish = $('#EnglishRadio')[0].checked;

    if (isAscii(bangla) && !isEnglish)
        bangla = avro.parse(bangla);

    $('#BanglaWord').val(bangla);

    // Clear any prior errors
    $('#LookupBtn').text('Lookup').removeClass('invBtnDanger');

    $('#Results').empty();
    $('#Throbber').show();
    $('#LookupBtn').hide();
    doAjax({
        url: lookupAjaxUrl,
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

function showBanglaChart()
{
    $('#BanglaChartWrapper').show();
    isShowingBanglaChart = true;
}

function hideBanglaChart()
{
    $('#BanglaChartWrapper').hide();
    isShowingBanglaChart = false;
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
        var target = $(event.target);

        if (isShowingBanglaChart && !target.closest('#BanglaChartWrapper').length && !target.closest('#BanglaWord').length)
            hideBanglaChart();

        var button = target.closest('BUTTON[xsamsadurl]');
        if (button.length)
        {
            loadSamsadPane(button.attr('xsamsadurl'));
            return;
        }
        if (target.hasClass('ToggleEditsBtn'))
        {
            target.closest('.WordDefWrapper').find('.EditsWrapper').toggle();
            return;
        }

        if (target.hasClass('AudioIcon'))
        {
            var audioElem = $(event.target).closest('.AudioWrapper').find('AUDIO')[0];
            audioElem.src = audioElem.src; // Resetting elem.src is necessary to repeat playback in Chrome.
            audioElem.play();
            return;
        };
    });

    $('#LookupBtn').bind('click', doAjaxLookup);

    $('#ShowBanglaChartBtn').bind('click', function() {
        if (!isShowingBanglaChart)
        {
            showBanglaChart();
            return false;
        }
    });

    $(document).bind('keydown', function(event) {
        if (event.keyCode == 27)
            hideBanglaChart();
    });

    createBanglaChart($('#BanglaChartWrapper'));

    History.Adapter.bind(window,'popstate',function() {
        var state = History.getState(); // Note: We are using History.getState() instead of event.state
        if (state && state.data.word)
        {
            if (!preloadedData || (state.data.word != preloadedData.word || preloadedData.word != lastResult))
            {
                var dataToLoad = state.data;
                if (preloadedData && preloadedData.word == state.data.word)
                    dataToLoad = preloadedData;
                handleResults(dataToLoad);
            }
        }
    });
});

})();
