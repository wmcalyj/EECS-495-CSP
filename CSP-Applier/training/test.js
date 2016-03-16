 var page = require('webpage').create();
 var server = require('webserver').create();
 var system = require('system'),
 url = system.args[1];
 page.onResourceReceived = function (res) {
 	//console.log(res.redirectURL);
      response_count++;
      if (res.redirectURL) {
          console.log(res.redirectURL)
      }
    };

 page.onLoadStarted = function() {
  console.log('Current page ' + window.location);
  console.log('Now loading a new page...');
};

 page.open(url,function (status) {

    if (status !== 'success') {
        console.log('Unable to post! '+status);
    } else {
        console.log(page.content.length);
        console.log(page.url);
    }
    phantom.exit();
});
