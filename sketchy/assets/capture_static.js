/*
 *
 *  Copyright 2014 Netflix, Inc.
 *
 *     Licensed under the Apache License, Version 2.0 (the "License");
 *     you may not use this file except in compliance with the License.
 *     You may obtain a copy of the License at
 *
 *         http://www.apache.org/licenses/LICENSE-2.0
 *
 *     Unless required by applicable law or agreed to in writing, software
 *     distributed under the License is distributed on an "AS IS" BASIS,
 *     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 *     See the License for the specific language governing permissions and
 *     limitations under the License.
 *
 */
// PhantomJS script
// Takes screeshot of a given page. This correctly handles pages which
// dynamically load content making AJAX requests.

// Instead of waiting fixed amount of time before rendering, we give a short
// time for the page to make additional requests.

var _ = require('./lodash.js');

var page = require('webpage').create(), loadInProgress = false, fs = require('fs');
page.viewportSize = {
    width: 1280,
    height: 800
};
// console.log(fs.workingDirectory);
// var curdir = fs.list(fs.workingDirectory);

var args = require('system').args;
var file_path = args[1] + '/';
var file_name = args[2];
var fullname = file_path.concat(file_name)
// output pages as PNG
var pageindex = 0;

var interval = setInterval(function() {
    if (!loadInProgress) {
        console.log('inprorsss');
        //console.log("image " + (pageindex + 1));
        console.log(fullname);
        page.open(fullname);
        //phantom.exit();
    }
}, 250);

page.onLoadStarted = function() {
    loadInProgress = true;
    console.log('page ' + (pageindex + 1) + ' load started');
};

page.onLoadFinished = function() {
    loadInProgress = false;
    console.log('FINISHED');
    page.render(file_path + '/'+ file_name.split('?')[0]  + ".png");
    //console.log('page ' + (filename + 1) + ' load finished');
    pageindex++;
    phantom.exit();
}
