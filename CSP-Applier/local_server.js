var express = require('express');
var bodyParser = require('body-parser')
var path = require('path');
var config = require('./config');
var https = require('https');
var http = require('http');
var fs = require('fs');
var morgan = require('morgan');
var cors = require('cors');
var formidable = require('formidable');
var base64 = require('base-64');

var options = {
  key: fs.readFileSync(path.join(__dirname, config.key_path) ),
  cert: fs.readFileSync(path.join(__dirname, config.cert_path) )
};

var app = express();
app.use(morgan('dev'));
app.use(cors());

var corsOptions = {
  origin: '*',
  allowedHeaders : 'Content-Type'
};

app.use('/allowed-resources',
	express.static(path.join(__dirname, config.js_repository)));

app.use('/libs',
	express.static(path.join(__dirname, config.lib_repository)));

app.use(bodyParser({limit: '50mb'}));
app.use(bodyParser.json() );
//app.use(bodyParser.urlencoded({extended:false}));

app.options('/js-factory', cors(corsOptions)); // enable pre-flight request for DELETE request 
app.post('/js-factory', cors(corsOptions), function(req, res, next){
	var file_name, script, full_path, decoded_script;
  try{
    //console.log("file_name: "+req.body.file_name);
    //console.log("script: "+req.body.script);
    full_path = path.join(__dirname, config.js_repository, req.body.file_name);
    decoded_script = decodeURI(req.body.script);
    console.log("decoded_script:"+decoded_script);
    fs.writeFileSync(full_path,decoded_script);
    res.json({ success: true,
        message: 'saved '+ req.body.file_name}); 
  }
  catch (e) {
    console.log('error in js-factory: '+e);
    res.json({ success: false,
        message: e}); 
  }
});

app.options('/templates', cors(corsOptions)); // enable pre-flight request for DELETE request 
app.post('/templates', cors(corsOptions), function(req, res, next){
  var file_name, script, full_path, script,tmp_obj, obj_str;
  try{
    //console.log("file_name: "+req.body.file_name);
    //console.log("script: "+req.body.script);
    file_name = 'templates_'+Date.now()+'.js';
    full_path = path.join(__dirname, config.js_repository, file_name);
    tmp_obj = JSON.parse(decodeURI(req.body.templates));
    obj_str = escape(JSON.stringify(tmp_obj));
    
    script = "var csp_templates_str = unescape('"+obj_str+"');\r\n" +
      "var csp_templates = JSON.parse(csp_templates_str);";
    console.log(script);
    fs.writeFileSync(full_path, script);
    console.log('done saving tempates '+file_name);
    res.json({ success: true,
        file_name: file_name}); 
  }
  catch (e) {
    console.log('error in templates: '+e);
    res.json({ success: false,
        message: e}); 
  }
});

http.createServer(app).listen(config.http_port);
https.createServer(options, app).listen(config.https_port);
console.log('Listening on port http:' + 
	config.http_port+' https:'+config.https_port+
	' dirname: '+__dirname);