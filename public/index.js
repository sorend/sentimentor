
var sentimentApp = angular.module("sentimentApp", ['ngCookies']);

sentimentApp.controller("AdminController", function($scope, $http, $interval) {

    $scope.status = null;
    $scope.language = 'English';
    $scope.lang = 'en';

    $scope.setLanguage = function(s, l) {
        $scope.lang = s;
        $scope.language = l;
    };

    var status = function() {
        $http.get("/status").then(function(res){
            var d = res.data;
            if (d.status == "running") {
                $scope.status = "Receiving tweets for " + d.q + ", now received: " + d.counter;
            }
            else {
                $scope.status = null;
            }
        });
    };

    var stop;
    $scope.start = function() {
        $http.get("/start?q=" + encodeURIComponent($scope.q) + "&lang=" + $scope.lang).then(function(res){
            if (res.status != 200)
                $scope.status = "Invalid request, please enter query terms";
            else {
                $scope.status = res.data.status;
                if (angular.isDefined(stop)) return;
                stop = $interval(function() {
                    status();
                }, 3000);
            }
        });
    };

    $scope.stop = function() {
        $http.get("/stop");
        if (angular.isDefined(stop)) {
            $interval.cancel(stop);
            stop = undefined;
            $scope.status = null;
        }
    };

    
});

sentimentApp.controller("IndexController", function($scope, $http, $cookies) {

    var nextTweet = function() {
        $http.get("/tweet?username=" + $scope.username).then(function(res){
            $scope.tweet = res.data;
        });
    };

    $scope.setUsername = function() {
        var username = $scope.username;
        if (username.length > 3 && /^[a-z]+$/.test(username)) {
            $scope.isReady = true;
            $scope.alert = null;
            $cookies.put("sentimentor-un", username, {path:"/", expires:new Date(2020, 1, 1, 1, 1, 1, 1)});
            nextTweet();
        }
        else
            $scope.alert = "Minimum 3 characters username and only a-z (no spaces or otherwise)";
    };
    
    $scope.vote = function(t, v) {
        var tweet = $scope.tweet;
        $http.get("/sentiment?tweet_id=" + tweet.id + "&sentiment=" + t +
                  "&energy=" + v + "&username=" + $scope.username).then(function(res){
            nextTweet();
        });
    };

    var username = $cookies.get("sentimentor-un");
    if (username !== undefined) {
        $scope.username = username;
        $scope.isReady = true;
        nextTweet();
    }
});

