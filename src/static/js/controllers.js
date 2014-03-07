'use strict';

function getCookie (name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

/*jQuery.postJSON = function(url, args, callback) {
    args._xsrf = getCookie("_xsrf");
    $.ajax({url: url, data: $.param(args), dataType: "text", type: "POST",
        success: function(response) {
        callback(eval("(" + response + ")"));
    }});
};*/

/* Controllers */

var gassmanApp = angular.module('gassmanApp', []);
/*
gassmanApp.filter('noFractionCurrency',
		  [ '$filter', '$locale',
		  function(filter, locale) {
		    var currencyFilter = filter('currency');
		    var formats = locale.NUMBER_FORMATS;
		    return function(amount, currencySymbol) {
		      var value = currencyFilter(amount, currencySymbol);
		      var sep = value.indexOf(formats.DECIMAL_SEP);
		      if(amount >= 0) { 
		        return value.substring(0, sep);
		      }
		      return value.substring(0, sep) + ')';
		    };
		  } ]);
*/


gassmanApp.directive('whenScrolled', function() {
    return function (scope, elm, attr) {
        var raw = elm[0];

        elm.bind('scroll', function() {
            if (raw.scrollTop + raw.offsetHeight >= raw.scrollHeight) {
                scope.$apply(attr.whenScrolled);
            }
        });
    };
});

gassmanApp.controller('AccountDetail', function($scope, $http, $filter) {
	$scope.uiMode = 'accountLoading';
	$scope.movements = [];

	$scope.toggleErrorMessage = function () {
		$scope.showErrorMessage = ! $scope.showErrorMessage;
	};

	var start = 0;
	var blockSize = 25;
	var concluded = false;

	$scope.loadMore = function () {
		
		if (concluded) return;

		$http.post('/account/movements/' + start + '/' + (start + blockSize) + '?_xsrf=' + getCookie('_xsrf')). // null, { xsrfCookieName:'_xsrf' }).
		success(function (data, status, headers, config) {
			concluded = data.length < blockSize;
			start += data.length;
			$scope.uiMode = 'accountOk';
			$scope.movements = $scope.movements.concat(data);
		}).
		error (function (data, status, headers, config) {
			concluded = true;
			$scope.serverError = data[1];
			console.log('movements error:', data)
			$scope.showErrorMessage = false;
			$scope.uiMode = 'accountFailed';
			//console.log('error', data, status, headers, config);
		});
	};

	$scope.loadMore();

	$http.post('/account/amount?_xsrf=' + getCookie('_xsrf')).
		success(function (data, status, headers, config) {
			$scope.amount = parseFloat( data[0] );
			$scope.currencySymbol = data[1];

			$scope.amountClass = $scope.amount < 0.0 ? 'negative' : 'positive';
//				$filter('currency')(data[0], data[1]);
		}).
		error (function (data, status, headers, config) {
			$scope.amountClass = 'error';
			//console.log('error', data, status, headers, config);
		});
});
