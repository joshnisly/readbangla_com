(function() {
var curLinkElem = null;

function showPageLink(url)
{
    $('#DefIFrame')[0].src = url;
}

function onMouseIn(event)
{
    var linkElem = $(event.target).closest('*[xdefurl]');
    if (linkElem && linkElem.attr('xdefurl') && linkElem != curLinkElem)
    {
        curLinkElem = linkElem;
        window.setTimeout(createCallback(null, showPageLink, [linkElem.attr('xdefurl')]));
    }
}

$(document).ready(function() {
    $('#Results').bind('mouseover', onMouseIn);
});

})();
