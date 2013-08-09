(function() {

var lastUrl = null;

function generateSamsadUrl(keyword, entriesOnly, exactMatch)
{
    var baseUrl = 'http://dsalsrv02.uchicago.edu/cgi-bin/romadict.pl?table=biswas-bengali&query='
    baseUrl += encodeURI(keyword);
    if (entriesOnly)
        baseUrl += '&searchhws=yes';
    if (exactMatch)
        baseUrl += '&matchtype=exact';

    return baseUrl;
}

function updateSamsad()
{
    $('#Throbber').show();
    var keyword = simpleCorrectSpelling($('#Keyword').val());
    $('#Keyword').val(keyword);
    var entriesOnly = $('#EntriesOnly')[0].checked;
    var exactMatch = $('#ExactMatch')[0].checked;

    var newUrl = generateSamsadUrl(keyword, entriesOnly, exactMatch);
    if (newUrl != lastUrl)
    {
        $('#SamsadPane')[0].contentWindow.location.replace(newUrl);
        lastUrl = newUrl;
    }
}

function onSamsadPaneLoaded()
{
    $('#Throbber').hide();
}

$(document).ready(function() {
    $('#Keyword').bind('input', updateSamsad);
    $('#EntriesOnly').bind('change', updateSamsad);
    $('#ExactMatch').bind('change', updateSamsad);
    $('#SamsadPane').bind('load', onSamsadPaneLoaded);

    updateSamsad();
});

})();
