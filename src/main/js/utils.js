'use strict';

/**
 * Created by makeroo on 20/01/17.
 */

function joinSkippingEmpties () {
    var sep = arguments[0];
    var r = '';
    for (var i = 1; i < arguments.length; ++i) {
        var x = arguments[i];
        if (typeof(x) != 'string' || x.length == 0)
            continue;
        if (r.length > 0)
            r += sep;
        r += x;
    }
    return r;
}
