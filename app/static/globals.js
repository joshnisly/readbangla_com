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
