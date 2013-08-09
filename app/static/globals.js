(function() {
    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie != '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = jQuery.trim(cookies[i]);
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) == (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    function csrfSafeMethod(method) {
        // these HTTP methods do not require CSRF protection
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    }
    var csrftoken = getCookie('csrftoken');
    $.ajaxSetup({
        crossDomain: false, // obviates need for sameOrigin test
        beforeSend: function(xhr, settings) {
            if (!csrfSafeMethod(settings.type)) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        }
    });
})();

(function() {
    var g_aSpellingCorrections = null;
    function simpleCorrectSpelling(word)
    {
        if (g_aSpellingCorrections === null)
        {
            g_aSpellingCorrections = JSON.parse($('#ServerData').attr('xSpellingCorrections'));
            for (var i = 0; i < g_aSpellingCorrections; i++)
                g_aSpellingCorrections[i][0] = new RegExp(g_aSpellingCorrections[i][0], 'g')
        }

        for (var i = 0; i < g_aSpellingCorrections.length; i++)
        {
            var correction = g_aSpellingCorrections[i];
            word = word.replace(correction[0], correction[1])
        }
        return word;
    }

    window.simpleCorrectSpelling = simpleCorrectSpelling;
})();

function isAuthenticated()
{
    return document.body.className.indexOf('Authenticated') != -1;
}

function isBanglaChar(char)
{
    return char >= '\u0981' && char <= '\u09FF';
}

function appendTextWithBanglaLinks(parentElem, text, fnLinkGenerator)
{
    while (text.length)
    {
        var inBangla = isBanglaChar(text[0]);
        var index = 0;
        while (index < text.length && isBanglaChar(text[index]) == inBangla)
            index++

        var textSubstr = text.substr(0, index);
        if (inBangla)
            parentElem.appendNewChild('A').text(textSubstr).attr('href', fnLinkGenerator(textSubstr));
        else
            parentElem[0].appendChild(document.createTextNode(textSubstr));

        text = text.substr(index)
    }
}

function createBanglaChart(parentElem)
{
    var banglaCodePoints = [
        '\u0985', '\u0986 / \u09BE', '\u0987 / \u09BF', '\u0988/\u09C0', '\n',
        '\u0989 / \u09C1', '\u098A / \u09C2', '\u098B / \u09C3', '\u098F/\u09C7', '\n',
        '\u0990 / \u09C8', '\u0993/\u09CB', '\u0994/\u09CC', '', '\n',
        '', '', '', '', '\n',
        '\u0995', '\u0996', '\u0997', '\u0998', '\u0999', '\n',
        '\u099A', '\u099B', '\u099C', '\u099D', '\u099E', '\n',
        '\u099F', '\u09A0', '\u09A1', '\u09A2', '\u09A3', '\n',
        '\u09A4', '\u09A5', '\u09A6', '\u09A7', '\u09A8', '\n',
        '\u09AA', '\u09AB', '\u09AC', '\u09AD', '\u09AE', '\n',
        '\u09AF', '\u09B0', '\u09B2', '\u09B6', '\u09B7', '\n',
        '\u09B8', '\u09B9', '\u09DF', '\u09DC', '\u09DD', '\n',
        '', '', '', '', '\n',
        '\u09A4\u09CD\u200D', '\u0982', '\u0983', '\u0981', '\u09CD', '\n',
        '\u0995\u09CD\u09AC', '\u0995\u09CD\u09AF', '\u0997\u09CD\u09B0', '\u09B0\u09CD\u0995', '\n',
        '\u0995\u09CD\u09B7', '\u0999\u09CD\u0997', '\u099C\u09CD\u099E', '\u099E\u09CD\u099A', '\n'
    ];

    var englishEquivalents = [
        'o', 'a', 'i', 'I', '\n',
        'u', 'U', 'rri', 'e', '\n',
        'OI', 'O', 'OU', '', '\n',
        '', '', '', '', '\n',
        'k', 'kh', 'g', 'gh', 'Ng', '\n',
        'c', 'ch', 'j', 'jh', 'NG', '\n',
        'T', 'Th', 'D', 'Dh', 'N', '\n',
        't', 'th', 'd', 'dh', 'n', '\n',
        'p', 'ph,f', 'b', 'bh,v', 'm', '\n',
        'z', 'r', 'l', 'sh,S', 'Sh', '\n',
        's', 'h', 'y,Y', 'R', 'Rh', '\n',
        '', '', '', '', '\n',
        't``', 'ng', ':', '^', ',,', '\n',
        'w', 'y,Z', 'r', 'rr', '\n',
        'kkh', 'NGg', 'gg', 'NGc', '\n'
    ];

    var table = parentElem.appendNewChild('TABLE');
    var row = table.appendNewChild('TR');
    for (var i = 0; i < banglaCodePoints.length; i++)
    {
        var bangla = banglaCodePoints[i];
        var english = englishEquivalents[i];

        if (bangla == '\n')
        {
            row = table.appendNewChild('TR');
            continue;
        }

        var cell = row.appendNewChild('TD');
        if (bangla)
        {
            cell.appendNewChild('SPAN', '', 'Bangla').text(bangla)
            cell[0].appendChild(document.createTextNode(' = ' + english));
        }
        else
            cell.html('&nbsp;');
    }
}

