'use strict';

angular.module('GassmanApp.controllers.Transaction', [
    'GassmanApp.directives.RequiredIf',
    'GassmanApp.directives.GmUniqueEmail',
    'GassmanApp.directives.GmCurrency',
    'GassmanApp.directives.GmRequiredAccount',
    'GassmanApp.services.Gdata',
    'GassmanApp.services.AccountAutocompletion',
    'ui.select'
])

.controller('Transaction', [
         '$scope', '$stateParams', '$location', '$timeout', 'gdata', 'accountAutocompletion',
function ($scope,   $stateParams,   $location,   $timeout,   gdata,   accountAutocompletion) {

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

    function noLineEnteredIn (a) {
        return (a.length == 0 || (a.length == 1 && !a[0].desc && !a[0].amount));
    }

    $scope.amountEquals = function (a, b) {
        return Math.abs(a - b) < 0.00005; // FIXME: .00005 dipende da currency
    };

    function roundAmount (x, digits) {
        var up = Math.pow(10, digits);

        return Math.floor( x * up + .5) / up;
    }

    function totalAmount (a) {
        var t = 0.0;

        angular.forEach(a, function (l) {
            var a = parseFloat(l.amount);
            if (!isNaN(a))
                t += a;
        });

        return t;
    }

    //var AUTOCOMPLETE_PRODUCERS = 2;
    //var AUTOCOMPLETE_EXPENSESKITTY = 1;
    //var AUTOCOMPLETE_NONE = 0;

    var transId = $stateParams.transId;
    var trans = {};

    var kitties = null;

    $scope.trans = trans;

    if (gdata.isPk(transId)) {
        trans.transId = transId;
        trans.cc_type = null;
    } else if (gdata.isValidTransactionType(transId)) {
        trans.transId = 'new';
        trans.cc_type = transId;
    } else {
        // TODO: lanciare 404...
        // ovvero impostare le variabili sotto affinché
        // il template mostri errore
        throw 'illegal url';
    }

    $scope.modified_by = null;
    $scope.modifies = null;
    $scope.log_date = null;
    $scope.operator = null;
    $scope.totalAmount = null;
    $scope.totalInvoice = null;
    //$scope.totalExpensesKitty = null;
    //$scope.totalIncomesKitty = null;
    $scope.totalKitty = null;
    $scope.totalExpenses = null;
    $scope.difference = null;
    $scope.confirmDelete = false;
    $scope.currency = null;
    $scope.currencyError = null;
    $scope.currencies = {};
    $scope.autocompletionData = [];
    //$scope.autocompletionExpenses = [];
    $scope.autocompletionDataError = null;
    $scope.tsaveOk = null;
    $scope.tsaveError = null;
    $scope.readonly = true;
    $scope.canEdit = false;
    $scope.viewableContacts = false;

    $scope.currencyDigits = function () {
        return 2; // FIXME: recuperarlo da db!
    };
//    var autoCompileTotalInvoice = AUTOCOMPLETE_PRODUCERS;
/*
    var autoCompilingTotalInvoice = function () {
        if (
            !noLineEnteredIn($scope.trans.expensesKitty) &&
            !noLineEnteredIn($scope.trans.incomesKitty)
        ) {
            return AUTOCOMPLETE_PRODUCERS;
        } else {
            return AUTOCOMPLETE_EXPENSESKITTY;
        }
/ *
        if (
            justOneLineEnteredWithTotal($scope.trans.producers, $scope.totalInvoice) &&

            noLineEnteredIn($scope.trans.expenses) &&
            noLineEnteredIn($scope.trans.expensesKitty) &&
            noLineEnteredIn($scope.trans.incomesKitty)
            )
            return AUTOCOMPLETE_PRODUCERS;
        if (
            noLineEnteredIn($scope.trans.expenses) &&
            noLineEnteredIn($scope.trans.incomesKitty) &&

            justOneLineEnteredWithTotal($scope.trans.expensesKitty, $scope.totalAmount - $scope.totalInvoice)
            )
            return AUTOCOMPLETE_EXPENSESKITTY;
        return AUTOCOMPLETE_NONE;* /
    };
*/
    var newLine = function (account) {
        // NB: si lascia KITTY come costante da risolvere in fase di save, quando si sa Currency e la kitty non è più ambigua

        return {
            accountName: '',
            account: account,
            amount: account == 'KITTY' ? - $scope.difference : 0.0,
            notes: ''
        };
    };

    var setupTransaction = function (tdata) {
        var t = tdata.data;
        //var trans = $scope.trans; // è nella chiusura
        var clients = [];
        var producers = [];
        var expenses = [];
        var kittyLines = [];

        if (trans.cc_type == null)
            trans.cc_type = t.cc_type;
        else if (t.cc_type != trans.cc_type)
            // TODO: che senso ha lanciare eccezione?
            // ovvero impostare le variabili sotto affinché
            // il template mostri errore
            throw "illegal transaction type";

        $scope.canEdit = gdata.isTransactionTypeEditableByUser(trans.cc_type, $scope.gassman.loggedUser);
        $scope.readonly = t.transId != 'new';

        if (!$scope.canEdit && !$scope.readonly) {
            // TODO: gestire l'errore
            throw "permission denied";
        }

        trans.transId = t.transId;
        trans.tdesc = t.description;
        trans.tdate = new Date(t.date);
        trans.clients = clients;
        trans.producers = producers;
        trans.expenses = expenses;
        trans.kittyLines = kittyLines;

        $scope.modified_by = t.modified_by;
        $scope.modifies = t.modifies;
        $scope.log_date = t.log_date;
        $scope.operator = t.operator;

        for (var i = 0; i < t.lines.length; ++i) {
            var l = t.lines[i];

            var x = l.amount;
            var owners = t.people[l.account]; //$scope.currencies[l.account];

            //console.log(x, typeof(x));
            if (owners && owners.length) {
                if (x < 0) {
                    clients.push(l);
                    l.amount = -x;
                } else {
                    producers.push(l);
                    l.amount = +x;
                }

                if (!l.accountName) {
                    var ac = $scope.currencies[l.account];

                    if (ac) {
                        l.accountName = ac.name;
                        l.readonly = false;
                    } else {
                        l.readonly = true;
                    }
                }

                if (!l.accountNames) {
                    var pp = [];

                    angular.forEach(owners, function (o) {
                        var person = $scope.accountPeopleIndex[o];
                        pp.push({
                            pid: person.profile.id,
                            name: joinSkippingEmpties(' ', person.profile.first_name, person.profile.middle_name, person.profile.last_name)
                        });
                    });

                    l.accountNames = pp;
                    //l.accountNames = $scope.currencies[l.account].people;
                }
            } else if (l.account in kitties) {
                if (l.notes) {
                    kittyLines.push(l);
                    l.amount = +x;
                } else {
                    console.log('skipped kitty line without description:', l);
                }
            } else {
                expenses.push(l);
                l.amount = +x;
            }
        }

        clients.push(newLine());
        producers.push(newLine());

//        autoCompileTotalInvoice = $scope.trans.cc_type != 'p' || t.transId != 'new' ? AUTOCOMPLETE_NONE : AUTOCOMPLETE_PRODUCERS; // FIXME: perché autocompletamento disabilitato in modifica?

        $scope.totalExpenses = totalAmount($scope.trans.expenses);
        $scope.updateTotalAmount();
        $scope.updateTotalInvoice();
        $scope.updateTotalKittyLines();
        $scope.checkCurrencies();
        $scope.autocompletionDataError = null;

        // problema: se mi fallisce autocompletion data, non carico nemmeno la transazione
        // del resto, in quel caso non so come risolvere i nomi dei conti quindi il form è
        // comunque inutilizzabile
    };

    function addToLastElement (array, value) {
        var l = array.length;
        var e = array[l - 1];
        var v = parseFloat(e.amount);

        if (isNaN(v))
            v = 0.0;

        e.amount = v + value;
    }

    $scope.updateTotalAmount = function () {
        $scope.totalAmount = roundAmount(totalAmount($scope.trans.clients), $scope.currencyDigits());

        updateDifference();
/*
        if (autoCompileTotalInvoice == AUTOCOMPLETE_PRODUCERS) {
            addToLastElement($scope.trans.producers, - $scope.difference);

            $scope.updateTotalInvoice();

            updateDifference(); // qui la porta a 0
        } else if (autoCompileTotalInvoice == AUTOCOMPLETE_EXPENSESKITTY) {
            if ($scope.difference > 0) {
                addToLastElement($scope.trans.expensesKitty, $scope.difference);

                $scope.updateTotalExpensesKitty();
            } else {
                addToLastElement($scope.trans.incomesKitty, - $scope.difference);

                $scope.updateTotalIncomesKitty();
            }

            updateDifference();
        }*/
    };

    function updateDifference () {
        $scope.difference = roundAmount(
            + $scope.totalInvoice
            + $scope.totalExpenses
            - $scope.totalAmount
            + $scope.totalKitty
            //- $scope.totalExpensesKitty
            //+ $scope.totalIncomesKitty
            ,
            $scope.currencyDigits()
        );

        if ($scope.amountEquals($scope.difference, 0.0)) {
            $scope.difference = 0.0;
        }
    }

    $scope.updateTotalInvoice = function (f) {
/*        var ac = autoCompilingTotalInvoice();

        if (f !== undefined && ac < autoCompileTotalInvoice) {
            autoCompileTotalInvoice = ac;
        }
*/
        //console.log('update total invoice', f);

        $scope.totalInvoice = roundAmount(totalAmount($scope.trans.producers), $scope.currencyDigits());

        updateDifference();
    };

    $scope.updateTotalKittyLines = function (f) {
//        var ac = autoCompilingTotalInvoice();

        //console.log('update total invoice', f);

//        $scope.totalExpensesKitty = totalAmount($scope.trans.expensesKitty);
        $scope.totalKitty = roundAmount(totalAmount($scope.trans.kittyLines), $scope.currencyDigits()); //$scope.totalIncomesKitty - $scope.totalExpensesKitty;

//        if ($scope.amountEquals($scope.totalKitty, 0.0))
//            $scope.totalKitty = 0.0;

        updateDifference();
    };

    $scope.accountCurrency = function (a) {
        try {
            if (a == 'KITTY') {
                return $scope.currency[1];
            } else {
                return $scope.currencies[a].cur[1];
            }
        } catch (e) {
            return ' ';
        }
    };

    $scope.checkCurrencies = function () {
        $scope.currency = null;

        var cc = function (l) {
            var a = l.account;

            if (!a)
                return;

            var curr = $scope.currencies[a];

            if (!$scope.currency) {
                $scope.currency = curr.cur;
            } else if (!angular.equals($scope.currency, curr.cur)) {
                throw 'err';
            }
        };

        try {
            angular.forEach($scope.trans.clients, cc);
            angular.forEach($scope.trans.producers, cc);

            $scope.currencyError = false;
        } catch (e) {
            $scope.currency = null;
            $scope.currencyError = true;
        }
    };

    $scope.confirmDeleteTransaction = function () {
        $scope.confirmDelete = true;
        $timeout(function () { $scope.confirmDelete = false; }, 3200.0);
    };

    $scope.deleteTransaction = function () {
        $scope.confirmDelete = false;

        var data = {
                transId: $scope.trans.transId,
                cc_type: 't',
                currency: $scope.currency[0],
                lines: [],
                date: $scope.trans.tdate,
                description: $scope.trans.tdesc
            };

        gdata.transactionSave($scope.gassman.selectedCsa, data).
        then (function (r) {
            //console.log('Transaction: transactionSave/delete result:', r);
            //$scope.savedTransId = r.data;
            //$scope.transId = 'new';
            //$scope.lines = [];
            //$scope.tsaveOk = true;

            $scope.showTransaction(r.data);
        }).
        then (undefined, function (error) {
            $scope.tsaveError = error.data;
        });
    };

    $scope.addLine = function (where, account) {
        where.push(newLine(account));

        if (account == 'KITTY') {
            $scope.updateTotalKittyLines();
        }
    };

    $scope.filledLine = function (line) {
        return (
            line.account !== null &&
            line.account !== undefined &&
            !isNaN(parseFloat(line.amount))
        );
    };

    $scope.filledLineWithDescription = function (line) {
        return $scope.filledLine(line) && typeof line.notes == 'string' && line.notes.length > 0;
    };

    $scope.modifyTransaction = function () {
        $scope.readonly = false;
    };

    $scope.reloadForm = function () {
        gdata.transactionForEdit($scope.gassman.selectedCsa, $scope.trans.transId).
        then(setupTransaction).
        then(undefined, function (error) {
            $scope.autocompletionDataError = error.data;
        });
    };

    $scope.focusElement = function (eid) {
        var e = angular.element(eid);
        $timeout(function () {
            e.focus();
        });
    };

    $scope.kittyId = function () {
        if (kitties == null) {
            throw 'kitties unavailable';
        }

        if ($scope.currency == null) {
            throw 'currency not defined for transaction';
        }

        var kittyId = null;
        angular.forEach(kitties, function (curr, aid) {
            if (curr.currency_id == $scope.currency[0]) {
                kittyId = aid;
            }
        });

        if (kittyId === null) {
            throw 'wtf! kitty not found for trans currency';
        }

        return kittyId;
    };
/*
    $scope.focusAmount = function (type) {
        var e = angular.element('#' + type + this.$index)[0];
        $timeout(function () {
            e.focus();
        }, 1);
    };
*/
    $scope.showTransaction = function (tid) {
        $location.path('/transaction/' + tid);
    };

    var firstTransResp = null;

    $scope.isTransactionEditor = gdata.canEditTransactions($scope.gassman.loggedUser);
    $scope.viewableContacts = $scope.gassman.loggedUser.permissions.indexOf(gdata.permissions.P_canViewContacts) != -1;
    $scope.viewableContactsOrAccounts = $scope.viewableContacts || $scope.gassman.loggedUser.permissions.indexOf(gdata.permissions.P_canCheckAccounts) != -1;

    var p = null;

    if ($scope.isTransactionEditor) {
        p = gdata.accountsNames($scope.gassman.selectedCsa)
        .then (function (r) {
            // trasforma data in autocompletionData

            if (r) {
                $scope.currencies = accountAutocompletion.parse(r.data);

                $scope.autocompletionData = accountAutocompletion.compose($scope.currencies);

                kitties = r.data.kitty;
            }

            if ($scope.trans.transId == 'new')
                return {
                    data: {
                        transId: 'new',
                        description: '',
                        date: new Date(),
                        cc_type: $scope.trans.cc_type,
                        currency: null,
                        lines: [],
                        modified_by: null,
                        modifies: null
                    },
                    people: {}
                };
            else
                return gdata.transactionForEdit($scope.gassman.selectedCsa, $scope.trans.transId, kitties == null);
        });
    } else {
        $scope.currencies = [ ];
        $scope.autocompletionData = { };

        p = gdata.transactionForEdit($scope.gassman.selectedCsa, $scope.trans.transId, kitties == null);
    }

    p.then(function (r) {
        firstTransResp = r;

        if (kitties == null)
            kitties = r.data.kitty;

        var x = [];
        angular.forEach(r.data.people, function (pp) {
            angular.forEach(pp, function(p) {
                if (x.indexOf(p) == -1)
                    x.push(p);
            });
        });

        return x.length ? gdata.peopleProfiles($scope.gassman.selectedCsa, x) : [];
    }).then(function (r) {
        $scope.accountPeopleIndex = r.data;
        return firstTransResp;
    }).then(setupTransaction).
    then (undefined, function (error) {
        $scope.autocompletionDataError = error.data;
    });
}])
;
