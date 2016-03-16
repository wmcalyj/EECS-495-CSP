var queue = require('./Queue'),
    system = require('system'),
    address,
    time,
    timeout, defaultTimeout = 5000,
    userAgent, defaultUserAgent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:38.0) Gecko/20100101 Firefox/38.0",
    times;

var debug = false;

if(system.args[system.args.length - 1].toLowerCase() === "debug"){
  debug = true;
}

if (system.args.length < 3) {
  console.log(
    "usage: phantom-worker.js url times timeout-for-one-req userAgent [cookiename:cookievalue:cookiedomain] cookiename:cookievalue:cookiedomain] ...");
}else {
  address = system.args[1];
  times = parseInt(system.args[2]);
  if (system.args.length >3 ){
    timeout = parseInt(system.args[3]);
  }else{
    timeout = defaultTimeout;
  }
  if (system.args.length > 4){
    userAgent = system.args[4];
  }else {
    // userAgent = defaultTimeout;
    userAgent = defaultUserAgent;
  }
  if(system.args.length > 5){
    var l = 0;
    if(debug){
      l = 1;
    }
    var cookies = [];
    var i = 5;
    for(i = 5; i < system.args.length - l; i++){
      console.log(system.args.length);
      console.log("args: " + system.args[i]);
      var cookie = system.args[i].split(":");
      console.log("cookie: " + cookie);
      var cookiename = cookie[0];
      var cookievalue = cookie[1];
      var cookiedomain = cookie[2];
      cookies.push({
        "name" : cookiename,
        "value" : cookievalue,
        "domain" : cookiedomain
      });
      if(debug){
        var j = 0;
        for(j = 0; j < cookies.length; j++){
          console.log("cookie[" + j + "]:" + 
            "\n\tname: " + cookies[j].name + 
            "\n\tvalue: " + cookies[j].value + 
            "\n\tdomain: " + cookies[j].domain);  
        }
      }
    }
  }
  console.log("[MAIN] browsing "+address+" for "+times);
  // else {
  //   // userAgent = defaultTimeout;
  //   userAgent = defaultUserAgent;
  // }
  // if(system.args.length > 5){
  //   cookies = [];
  //   for(var i = 5; i < system.args.length; i++){
  //     cookie = system.args[i].split[":"];
  //     console.log("cookie: " + cookie);
  //     cookiename = cookie[0];
  //     cookievalue = cookie[1];
  //     cookiedomain = cookie[2];
  //     cookies.push({
  //       name : cookiename;
  //       value : cookievalue;
  //       domain : cookiedomain;
  //     });
  //     console.log("cookies: " + cookies);
  //   }
  // }
  // console.log("[MAIN] browsing "+address+" for "+times);
  // taskWorker.configure({
  //   timeout : timeout,
  //   user_agent : userAgent });
  // index = 0;
  // while (index++ < times) {
  //   taskWorker.post_task({url : address});
  // }
  // taskWorker.start_tasks();
  // waitForTaskFinish(times);
}
phantom.exit();