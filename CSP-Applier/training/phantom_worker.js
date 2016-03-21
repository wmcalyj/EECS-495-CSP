var queue = require('./Queue'),
  system = require('system'),
  taskWorker,
  /* parameters */
  address, times, index,
  /* settings */
  defaultUserAgent, userAgent, defaultTimeout, timeout,
  /* utilities */
  waitForTaskFinish, displayObject;

var debug = false;
var fs = require('fs');
var HOST = "lotus.cs.northwestern.edu"

/* Settings */
defaultUserAgent =
  "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:38.0) Gecko/20100101 Firefox/38.0";
defaultTimeout = 5000;

function b64EncodeUnicode(str) {
  return btoa(encodeURIComponent(str).replace(/%([0-9A-F]{2})/g, function(match, p1) {
    return String.fromCharCode('0x' + p1);
  }));
}

/* Task Worker */
taskWorker = (function() {
  var user_agent, timeout, current_url,
    task_queue = new queue(),
    page = null,
    fin_task_count = 0,
    err_task_count = 0,
    error_tag = false,
    configure, post_task, start_tasks,
    open_url, open_url_callback,
    get_remaining_task_count, get_fin_task_count, get_error_tag;

  configure = function(settings) {
    user_agent = settings.user_agent;
    timeout = settings.timeout;
  };

  post_task = function(task) {
    task_queue.enqueue(task);
    console.log("[ADD_TASK] adding a browsing task: " +
      task_queue.getLength());
  };

  open_url_callback = function(result) {
    try {
      if (result.status !== 'success') {
        console.log('[FAIL] to load the address:' + result.url);
        // console.log("result content: " + result.content);

      } else {
        console.log("[SUCCEED] to load the address: " + result.url +
          ", contnet-size: " + result.content.length,
          ", failed objects: " + result.failed_obj_count,
          ", landing-page: " + result.landing_page);
        var path = result.url + '.html'
        fs.write(path, result.content, 'w');
        console.log(result.content);
        send_contents(current_url, result.content, result.landing_page)

        // Start grabing scripts out of content
        var d = document.createElement('div');
        d.innerHTML = result.content;
        scripts = d.getElementsByTagName("script");
        var path2 = result.url + "-scripts.txt";
        // fs.write(path2, scripts);
        console.log("Scripts length: " + scripts.length);

        var urlapi = require('url'),
          url = urlapi.parse(current_url);
        hostname = url.hostname;

        for (var i = 0; i < scripts.length; i++) {
          // console.log("[WRITING SCRIPTS NOW]");
          var script = scripts[i].text;
          script = script.replace(/\s/g, "");
          // console.log("script: [" + script + "]");
          fs.write(path2, script, 'a');
          fs.write(path2, "\n", 'a');
          send_scripts(current_url, script, hostname);
        }
      }
    } catch (err) {
      console.log("[PHANTOM_ERR] error in open_url_callback " + err);
    } finally {
      //fin_task_count++;   
      if (task_queue.getLength() > 0) {
        //make sure the page is null!
        console.log("[INFO] Start next task, " + task_queue.getLength() + " left");
        start_tasks();
      }
    }
  };

  send_contents = function(url, contents, landing_url) {
    var db_listener = "http://" + HOST + ":4040/api/web-contents/contents-store",
      sender, error = null,
      json_header, encoded_contents, data;
    sender = require('webpage').create();
    sender.settings.resourceTimeout = 5000;
    sender.settings.userAgent = user_agent;

    sender.onResourceTimeout = function(e) {
      error = "timeout";
    };

    console.log("[INFO] sending contents to DB: " + contents.length);
    encoded_contents = b64EncodeUnicode(contents);
    data = '{"url":"' + encodeURIComponent(url) +
      '","landing_url":"' + encodeURIComponent(landing_url) +
      '","contents":"' + encoded_contents + '"}';
    console.log("[DEBUG] " + encoded_contents.length);
    json_header = {
      "Content-Type": "application/json"
    };
    try {
      sender.open(db_listener, 'post', data, json_header,
        function(status) {
          //page.render('github.png');
          content = page.content.slice(0);
          sender.close();
          sender = null;

          if (status !== 'success') {
            err_task_count++;
            console.log("[FAIL] failed to send contents to DB; failed cases " + err_task_count);
          } else if (error) {
            err_task_count++;
            console.log("[FAIL] failed to send contents to DB; failed cases " + err_task_count);
          }
          console.log("[SUCCEED] sent contents [" + contents.length + "] to db");
          //
        });
    } catch (err) {
      console.log("[PHANTOM_ERR] error sending contents to db " + err);
      sender.close();
      page = null;
      error_tag = true;
    } finally {
      fin_task_count++;
    }
  };


  send_scripts = function(url, script, hostname) {
    var db_listener = "http://" + HOST + ":4040/api/web-contents/pure-scripts-store",
      sender, error = null,
      json_header, encoded_contents, data;
    sender = require('webpage').create();
    sender.settings.resourceTimeout = 5000;
    sender.settings.userAgent = user_agent;

    sender.onResourceTimeout = function(e) {
      error = "timeout";
    };

    console.log("[INFO] sending script to DB: " + script.length);
    encoded_script = b64EncodeUnicode(script);
    data = '{"url":"' + encodeURIComponent(url) +
      '","script":"' + encoded_script +
      '","hostname":"' + encodeURIComponent(hostname) + '"}';
    console.log("[DEBUG] " + encoded_script.length);
    json_header = {
      "Content-Type": "application/json"
    };
    try {
      sender.open(db_listener, 'post', data, json_header,
        function(status) {
          //page.render('github.png');
          content = page.content.slice(0);
          sender.close();
          sender = null;

          if (status !== 'success') {
            err_task_count++;
            console.log("[FAIL] failed to send script to DB; failed cases " + err_task_count);
          } else if (error) {
            err_task_count++;
            console.log("[FAIL] failed to send script to DB; failed cases " + err_task_count);
          }
          console.log("[SUCCEED] sent script [" + script.length + "] to db");
          //
        });
    } catch (err) {
      console.log("[PHANTOM_ERR] error sending script to db " + err);
      sender.close();
      page = null;
      error_tag = true;
    } finally {
      fin_task_count++;
    }
  };

  //this method creates and closes the page instance
  open_url = function(url) {
    var landing_page = url,
      content, timeout_count = 0,
      request_count = 0,
      response_count = 0;
    if (page !== null) {
      console.log("[ERROR] last instance hasn't finished!!!");
      return;
    }
    page = require('webpage').create();
    page.settings.javascriptEnabled = true;
    page.settings.resourceTimeout = 5000;
    page.settings.userAgent = user_agent;
    phantom.cookiesEnabled = true;
    phantom.javascriptEnabled = true;
    if (cookies != undefined) {
      for (var i = 0; i < cookies.length; i++) {
        var cookie = cookies[i];
        phantom.addCookie({
          'name': cookie.name,
          'value': cookie.value,
          'domain': cookie.domain,
          'path': cookie.path,
          'expires': cookie.expires
        });
      }
      if (debug) {
        console.log("------------------------------------\ntry again");
        for (var j = 0; j < cookies.length; j++) {
          console.log("cookie[" + j + "]:" +
            "\n\tname: " + cookies[j].name +
            "\n\tvalue: " + cookies[j].value +
            "\n\tdomain: " + cookies[j].domain +
            "\n\tpath: " + cookies[j].path +
            "\n\texpires: " + cookies[j].expires
          );
        }
        console.log("----------------------------------\n")
      }
    }

    page.onResourceRequested = function(req) {
      //console.log("request:"+req.url);
      request_count++;
    };

    page.onResourceReceived = function(response) {
      response_count++;
      if (debug) {
        console.log('Response (#' + response.id + ', stage "' + response.stage + '"): ' + JSON.stringify(response));
      }

      //if (res.redirectURL) {
      //    landing_page = res.redirectURL;
      //}
    };

    page.onResourceTimeout = function(e) {
      timeout_count++;
    };

    console.log("[INFO] start browsing: " + url);
    try {
      console.log("[DEBUG] start browsing: " + url);
      page.open(url, function(status) {
        //page.render('github.png');
        console.log("[DEBUG] done opening: " + url + " " + status);
        content = page.content.slice(0);
        if (status === "success") {
          //console.log("PAGE:"+page);
          landing_page = page.url.slice(0);
        }
        page.close();
        page = null;

        open_url_callback({
          status: status,
          url: url,
          landing_page: landing_page,
          request_count: request_count,
          response_count: response_count,
          failed_obj_count: timeout_count,
          content: content
        });
      });
    } catch (err) {
      console.log("[PHANTOM_ERR] error in open " + url + " error:" + err);
      page.close();
      page = null;
      error_tag = true;
    } finally {}
  };

  start_tasks = function() {
    var task;
    if (task_queue.getLength() > 0 && page === null) {
      task = task_queue.dequeue();
      current_url = task.url;
      open_url(task.url);
    } else {
      console.log("[INFO] can NOT start task: " +
        task_queue.getLength() + " " + page);
    }
  };

  get_remaining_task_count = function() {
    return task_queue.getLength();
  };

  get_fin_task_count = function() {
    return fin_task_count;
  };

  get_error_tag = function() {
    return error_tag;
  }

  return {
    configure: configure,
    post_task: post_task,
    start_tasks: start_tasks,
    get_remaining_task_count: get_remaining_task_count,
    get_fin_task_count: get_fin_task_count,
    get_error_tag: get_error_tag
  };

})();

/* Utilities */
displayObject = function(obj) {
  var item;
  for (item in obj) {
    if (obj.hasOwnProperty(item)) {
      console.log("KEY: " + item + " VAL:" + obj[item]);
    }
  }
};

waitForTaskFinish = function(count) {
  if (!taskWorker.get_error_tag() &&
    taskWorker.get_fin_task_count() < count) {
    console.log("[MAIN] finished [" + taskWorker.get_fin_task_count() +
      "/" + count + "] tasks, check 2s later");
    setTimeout(function() {
        waitForTaskFinish(count)
      },
      2000);
  } else {
    console.log("[MAIN] having finished " +
      taskWorker.get_fin_task_count() + " tasks");
    phantom.exit();
  }
};

/* main */
// console.log("Received args: " + system.args)
debug = true
if (system.args.length < 3) {
  console.log(
    "usage: phantom-worker.js url times timeout-for-one-req userAgent [cookiename:cookievalue:cookiedomain] cookiename:cookievalue:cookiedomain] ...");
} else {

  // If it's reading from file
  if (system.args[1] === "-f") {
    // Read from file
    var fs = require('fs');
    var fileContent = fs.read(system.args[2])
    if (debug) {
      console.log("File content - " + system.args[2] + " : {" + fileConent + "}");
    }
    args = fileContent.split(" ")
    if (debug) {
      console.log("args: " + args);
    }
    address = args[0];
    times = parseInt(args[1]);
    timeout = args[2];
    if (args[2] != null) {
      if (timeout === "/") {
        timeout = defaultTimeout;
      } else {
        timeout = parseInt(args[2]);
      }
    }
    if (args[3] != null) {
      userAgent = args[3];
      if (userAgent === "/") {
        userAgent = defaultUserAgent;
      }
    } else {
      userAgent = defaultUserAgent;
    }
    if (args[4] != null) {
      var l = 0;
      if (debug) {
        l = 1;
      }
      var cookies = [];
      for (var i = 5; i < args.length - l; i++) {
        var cookie = args[i].split("~~~");
        var cookiename = cookie[0];
        var cookievalue = cookie[1];
        var cookiedomain = cookie[2];
        var cookiepath = cookie[3];
        var cookieexpires = cookie[4];
        // var cookiesize = cookie[5];
        // var cookieHTTP = cookie[6];
        // var cookieSecure = cookie[7];
        // var cookieFirstParty = cookie[8];

        cookies.push({
          "name": cookiename,
          "value": cookievalue,
          "domain": cookiedomain,
          "path": cookiepath,
          "expires": cookieexpires
        });
      }
      if (debug) {
        for (var j = 0; j < cookies.length; j++) {
          console.log("cookie[" + j + "]:" +
            "\n\tname: " + cookies[j].name +
            "\n\tvalue: " + cookies[j].value +
            "\n\tdomain: " + cookies[j].domain +
            "\n\tpath: " + cookies[j].path +
            "\n\texpires: " + cookies[j].expires
          );
        }
      }
    }
  } else {
    console.log("Arg total length: " + system.args.length)
    console.log("trying to start now");
    address = system.args[1];
    times = parseInt(system.args[2]);
    if (system.args.length > 3) {
      if (system.args[3] === "/") {
        timeout = defaultTimeout;
      } else {
        timeout = parseInt(system.args[3]);
      }
    } else {
      timeout = defaultTimeout;
    }
    if (system.args.length > 4) {
      userAgent = system.args[4];
      if (userAgent === "/") {
        userAgent = defaultUserAgent;
      }
    } else {
      // userAgent = defaultTimeout;
      userAgent = defaultUserAgent;
    }
    if (system.args.length > 5) {
      // Receive cookies from manager will result in a string contains all cookies
      // Thus, we need to manually separate the cookie by white space
      var cookieArgs = system.args[5].split(" ");
      var cookies = [];
      // for (var i = 5; i < system.args.length - l; i++) {
      for (var i = 0; i < cookieArgs.length; i++) {
        // var cookie = system.args[i].split("~~~");
        // We only care about cookiename, cookievalue, cookiedomain & cookiepath
        var cookie = cookieArgs[i].split(",");
        var cookiename = cookie[0];
        var cookievalue = cookie[1];
        var cookiedomain = cookie[2];
        var cookiepath = cookie[3];
        // var cookieexpires = (new Date()).getTime() + (1000 * 60 * 60);
        var cookieexpires = cookie[4];

        cookies.push({
          "name": cookiename,
          "value": cookievalue,
          "domain": cookiedomain,
          "path": cookiepath,
          "expires": cookieexpires
        });
      }
      if (debug) {
        for (var j = 0; j < cookies.length; j++) {
          console.log("cookie[" + j + "]:" +
            "\n\tname: " + cookies[j].name +
            "\n\tvalue: " + cookies[j].value +
            "\n\tdomain: " + cookies[j].domain +
            "\n\tpath: " + cookies[j].path +
            "\n\texpires: " + cookies[j].expires
          );
        }
      }
    }
  }
  console.log("[MAIN] browsing " + address + " for " + times);
  taskWorker.configure({
    timeout: timeout,
    user_agent: userAgent,
    cookies: cookies
  });
  index = 0;
  while (index++ < times) {
    taskWorker.post_task({
      url: address
    });
  }
  taskWorker.start_tasks();
  waitForTaskFinish(times);
}