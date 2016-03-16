var csp_client_lib = (function() {
  var page_url;
  var csp_build_external_js_url = "https://localhost:4433/js-factory";
  var csp_js_repository_url = "https://localhost:4433/allowed-resources/";
  var config = function(u, build_url, repo_url) {
    page_url = u;
    if (build_url) {
      csp_build_external_js_url = build_url;
    }
    if (repo_url) {
      csp_js_repository_url = repo_url;
    }
  }

  var csp_base64encode_script = function (script) {
    try{
      //console.log("DEBUG: original_script:"+script);
      //console.log("DEBUG:  encoded_script:"+encodeURI(script));
      return encodeURI(script);
      //return encodeURI(btoa(script));
    }
    catch(e){
      console.log('failed to encode base64 script '+e);
      return null;
    }
  };

  var csp_create_script_node = function (src) {
    try{
      var script = document.createElement('script');
      script.src = src;
      return script;
    }
    catch (e) {
      console.log('erorr in csp_create_script_node '+ e)
    }
    return null;
  };

  var csp_replace_node = function (new_node, old_node) {
    try{
      if(old_node===null){
        document.getElementsByTagName('head')[0].appendChild(new_node);
        //return ;
      }
      else{
        var p_node = old_node.parentElement;
        if (p_node===null) {
          document.getElementsByTagName('head')[0].appendChild(new_node);
        }
        else {
          p_node.replaceChild(new_node, old_node);
        }
      }
      //console.log('done replacing node: '+new_node['src']);
    }
    catch (e) {
      console.log('erorr in csp_replace_node '+ e);
    }
  };

  var csp_match_contents = function (script) {
    return script;
  };

  var csp_parse_url = function (url){
    var parser = document.createElement('a');
    parser.href = url;
    return parser.hostname;
  };
  
  var csp_rewrite_inline_script = function (old_script_node, starting_time) {
    if (old_script_node.innerHTML === ""){
      return ;
    }
    var old_node  = old_script_node;
    var xmlhttp = new XMLHttpRequest();   // new HttpRequest instance 
    //console.log("debug inline: "+old_script_node.innerHTML);
    var times = {};
    var encoded_script = csp_base64encode_script(old_script_node.innerHTML);
    //console.log("debug encoded inline: "+encoded_script.length)
    var file_name =  'dynamic_'+csp_parse_url(page_url) + '_' +Date.now()+'.js';
    times[file_name] = starting_time;
    //var params = "file_name="+file_name+"&script=" + encoded_script;
    var obj = {file_name:file_name, script:encoded_script};
    var params = JSON.stringify(obj);
    //console.log("params:"+params);
    var new_node;

    var external_js_ready_callback = function () {
      if(xmlhttp.readyState == 4 && xmlhttp.status == 200) {
        try{
          var obj = JSON.parse(xmlhttp.responseText);
          if (obj.success === true) {
            //console.log('successfully creating external JS\n');
            new_node = csp_create_script_node(csp_js_repository_url+file_name);
            csp_replace_node(new_node, old_node);
            var end_time = Date.now();
            var diff_time = end_time - times[file_name];
            //console.log('DYNAMICJS_TIME: '+diff_time);
          }
          else {
            console.log('Failed to create external js: '+obj.message);
          }
        }
        catch (e) {
          console.log('Failed to create external js: '+obj.message);
        }
      }
    };

    xmlhttp.open("POST", csp_build_external_js_url, true);
    //xmlhttp.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
    xmlhttp.setRequestHeader("Content-type", "application/json")
    xmlhttp.onreadystatechange = external_js_ready_callback;
    
    xmlhttp.send(params);
  };

  var csp_observer = new MutationObserver(function (mutations) {
    mutations.forEach(function (mutation) {
      var node, node_name, script;
      for (var i = 0; i < mutation.addedNodes.length; i++){
        try{
          node = mutation.addedNodes[i];
          if(node.innerHTML.indexOf('Share to Facebook. Opens in a new window') !== -1 ){
            console.log("FIND THIS NODE:"+node.innerHTML);
          }
          
          node_name = node.nodeName.toUpperCase();
          if (node_name === "SCRIPT"){
            var script = node.innerHTML.trim();
            if (script.length === 0) { continue; }
            script = csp_match_contents(script);
            //console.log("captured inline script:"+script);
            if (script === "" ) { continue; }
            try{
              var t1 = Date.now();
              esprima.parse(script);
              var t2 = Date.now() - t1;
              //console.log("inline_len:"+script.length+" time:"+t2);
              csp_rewrite_inline_script(node,Date.now());
            }
            catch(e){
              console.log('CSP Error in parsing js:'+e);
            }
            //console.log("detect one added script node");
          }
          else if(node_name === "BUTTON"){
            //console.log("NewButton: "+node.innerHTML);
          }
        }
        catch (e) {
          console.log("CSP Error in MutationObserver callback "+e);
        }
       
      }

    });
  });

  var cst_test_create_node = function () {
    var script = document.createElement('script');
    script.innerHTML = 
      "var xxx = 3; var yyy = 4; var z = xxx + yyy; alert('z value be '+z)";
    document.getElementsByTagName('head')[0].appendChild(script);
  };

  var csp_run_observer = function() {
    var csp_dom_observer_options = {
      subtree: true,
      childList: true,
      attributes: false
    };
    csp_observer.observe(document, csp_dom_observer_options);
  };

  return {
    config : config,
    run_observer : csp_run_observer,
    test : cst_test_create_node
  };

}) ();

//Rewrite Eval
var TYPES = {
    'undefined'        : 'undefined',
    'number'           : 'number',
    'boolean'          : 'boolean',
    'string'           : 'string',
    '[object Function]': 'function',
    '[object RegExp]'  : 'regexp',
    '[object Array]'   : 'array',
    '[object Date]'    : 'date',
    '[object Error]'   : 'error'
},
TOSTRING = Object.prototype.toString;

function type(o) {
    return TYPES[typeof o] || TYPES[TOSTRING.call(o)] || (o ? 'object' : 'null');
};

var old_eval = window.eval;
window.eval = function (arg){
  //console.log("prepare eval: "+type(arg)+" content:"+arg); 
  try{
    return JSON.parse(arg);
  }
  catch(e){
    try{
      return JSON.parse(arg.substr(1,arg.length-2));
    }
    catch(e){
      console.log("CSP Eval exception:"+e);
    }
  }
}
Function = function(arg){
  console.log("Function: "+arg);
  if (arguments.length===0)
    return function(){};

  return  function(){};
}


csp_client_lib.config(document.URL);
csp_client_lib.run_observer();

