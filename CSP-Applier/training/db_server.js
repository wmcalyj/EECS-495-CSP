var express = require('express');
var querystring = require('querystring');
var urlParse = require('url');
var bodyParser = require('body-parser');
var util = require('util');

var mongo = require('mongodb');
var monk = require('monk');
var db = monk('localhost:27017/webcontents');

var app = express();
app.use(bodyParser({
	limit: '50mb'
}));
app.use(bodyParser.json());

var standardizeURL = function(url) {
	try {
		var url = querystring.unescape(url);
		var o = urlParse.parse(url)
		var new_url = o.protocol + '//' + o.host + o.path;
		//console.log(new_url);
		var is_google = o.host.toLowerCase().indexOf("google.com")
		if (is_google != -1) {
			return url;
		}
		return new_url;
	} catch (e) {
		console.log("failed parse url " + e);
		return null;
	}

};
app.use(function(req, res, next) {
	req.db = db;
	next();
});

/* Store Distance */
app.post('/api/web-contents/distance-store', function(req, res) {
	if (!req.body.url1 || !req.body.url2 || !req.body.distance) {
		console.log(req.body.url1 + " " + req.body.url2 + " " + req.body.distance);
		return res.json({
			success: false
		});
	}
	try {
		var url1 = standardizeURL(req.body.url1);
		var url2 = standardizeURL(req.body.url2);
		if (url1 === url2) {
			console.log("[FAIL] URL1 and URL2 are same: " + url1 + " " + url2);
			return res.json({
				success: false,
				message: "TWO_URL_SAME"
			});
		}
		if (url1 > url2) {
			var tmp = url1;
			url1 = url2;
			url2 = tmp;
		}
		res.json({
			success: true,
			url1: url1,
			url2: url2
		});
	} catch (e) {
		console.log("error: " + e);
		res.json({
			success: false,
			message: e
		});
	}

	try {
		var collection = db.get('distance');
		collection.insert({
			url1: url1,
			url2: url2,
			distance: req.body.distance
		}, function(err, doc) {
			if (err) {
				console.log("[FAIL] failed to insert distance into DB: " + err + " " + url1 + " " + url2);
			} else {
				console.log("[SUCC] inserted distance into DB: " + url1 + " " + url2);
			}
		});

		collection.insert({
			url1: url2,
			url2: url1,
			distance: req.body.distance
		}, function(err, doc) {
			if (err) {
				console.log("[FAIL] failed to insert distance into DB: " + err + " " + url1 + " " + url2);
			} else {
				console.log("[SUCC] inserted distance into DB: " + url1 + " " + url2);
			}
		});

	} catch (e) {
		console.log("[FAIL] failed to insert distance into DB " + e);
	}
});



/* Store All Pure Scripts */
app.post('/api/web-contents/pure-scripts-store', function(req, res) {
	if (!req.body.url || !req.body.script || !req.body.hostname) {
		console.log(req.body.url + " " + req.body.script + " " + req.body.hostname);
		return res.json({
			success: false
		});
	}
	try {
		var url = standardizeURL(req.body.url);

		res.json({
			success: true,
			url: url
		});
	} catch (e) {
		console.log("error: " + e);
		res.json({
			success: false,
			message: e
		});
	}

	try {
		var collection = db.get('purescripts');
		var script = req.body.script;
		var hostname = req.body.hostname;
		collection.insert({
			url: url,
			script: script,
			hostname: hostname
		}, function(err, doc) {
			if (err) {
				console.log("[FAIL] failed to insert script into DB: " + err + " " + url);
			} else {
				console.log("[SUCC] inserted script into DB: " +
					url);
			}
		});

	} catch (e) {
		console.log("[FAIL] failed to insert pure scripts into DB " + e);
	}
});

/* Store Scripts */
app.post('/api/web-contents/scripts-store', function(req, res) {
	if (!req.body.url || !req.body.hosts || !req.body.inlines) {
		console.log(req.body.url + " " + req.body.hosts + " " + req.body.inlines);
		return res.json({
			success: false
		});
	}
	try {
		var url = standardizeURL(req.body.url);

		res.json({
			success: true,
			url: url
		});
	} catch (e) {
		console.log("error: " + e);
		res.json({
			success: false,
			message: e
		});
	}

	try {
		var collection = db.get('scripthosts');
		collection.insert({
			url: url,
			hosts: req.body.hosts
		}, function(err, doc) {
			if (err) {
				console.log("[FAIL] failed to insert script hosts into DB: " + err + " " + url);
			} else {
				console.log("[SUCC] inserted script hosts into DB: " +
					url + " " + req.body.hosts.length);
			}
		});

		collection = db.get('inlinescripts');
		collection.insert({
			url: url,
			inlines: req.body.inlines
		}, function(err, doc) {
			if (err) {
				console.log("[FAIL] failed to insert inline scripts into DB: " + err + " " + url);
			} else {
				console.log("[SUCC] inserted inline scripts into DB: " +
					url + " " + req.body.hosts.length);
			}
		});
	} catch (e) {
		console.log("[FAIL] failed to insert inline scripts into DB " + e);
	}
});

/* Store Contents */
app.post('/api/web-contents/contents-store', function(req, res) {
	if (!req.body.url || !req.body.contents || !req.body.landing_url) {
		res.json({
			success: false
		});
	}
	res.json({
		success: true,
		url: req.body.url,
		size: req.body.contents.length
	});

	try {
		var url = standardizeURL(req.body.url);
		var landing_url = standardizeURL(req.body.landing_url);
		var contents = req.body.contents;
		var collection = db.get('contentscollection');
		collection.insert({
			url: url,
			landing_url: landing_url,
			contents: contents
		}, function(err, doc) {
			if (err) {
				console.log("[FAIL] failed to insert into DB: " + url);
			} else {
				console.log("[SUCC] inserted into DB " +
					url + " landing_url:" + landing_url);
			}
		});
	} catch (e) {
		console.log("[FAIL] failed to process req " + e);
	}
});

/* Store Trees */
app.post('/api/web-contents/trees-store', function(req, res) {
	if (!req.body.url || !req.body.key || !req.body.tree || !req.body.domain) {
		console.log(req.body.url + " " + req.body.key + " " + req.body.tree);
		return res.json({
			success: false
		});
	}
	var url = standardizeURL(req.body.url);
	try {
		var collection = db.get('trees');
		collection.insert({
				url: url,
				key: req.body.key,
				tree: req.body.tree,
				domain: req.body.domain
			},
			function(err, doc) {
				if (err) {
					console.log("[FAIL] failed to insert tree into DB: " + err + " " + url + " " + req.body.key);
					res.json({
						success: false,
						message: err
					});
				} else {
					console.log("[SUCC] inserted tree into DB: " +
						url + " " + req.body.key);
					res.json({
						success: true,
						url: url,
						key: req.body.key
					});
				}
			});
	} catch (e) {
		console.log("error: " + e);
		res.json({
			success: false,
			message: e
		});
	}
});

/* Fetch distance */
app.post('/api/web-contents/distance-fetch', function(req, res) {
	var url, data, index, collection;
	if (!req.body.url1 || !req.body.url2) {
		res.json({
			success: false
		});
		return
	}
	try {
		console.log("URL1:" + req.body.url1 + " URL2:" + req.body.url2)
		if (req.body.url1 === "*" && req.body.url2 === "*") {
			data = {}
		} else if (req.body.url1 === "*") {
			url = standardizeURL(req.body.url2);
			data = {
				url2: url
			}
		} else if (req.body.url2 === "*") {
			url = standardizeURL(req.body.url1);
			data = {
				url1: url
			}
		} else {
			url1 = standardizeURL(req.body.url1);
			url2 = standardizeURL(req.body.url2);
			data = {
				url1: url1,
				url2: url2
			}
		}
		console.log("  [DEBUG] fetch distance : " + data);
		collection = db.get('distance');
		collection.find(data, function(err, docs) {
			if (err) {
				console.log("[FAIL] failed to fetch contents for " + url);
				res.json({
					success: false
				});
			} else {
				console.log("[SUCC] " + docs.length + ' items');
				for (index in docs) {
					docs[index].url1 = querystring.escape(docs[index].url1);
					docs[index].url2 = querystring.escape(docs[index].url2);
				}
				res.json({
					success: true,
					result: JSON.stringify(docs)
				});
			}
		});
	} catch (e) {
		console.log("[FAIL] failed to process req " + e);
		res.json({
			success: false
		});
	}
});

/* Fetch Contents */
app.post('/api/web-contents/contents-fetch', function(req, res) {
	console.log("Start fetching urls from database");
	var url, data, index, collection;
	if (!req.body.url) {
		res.json({
			success: false
		});
		return
	}
	try {
		console.log("URL:" + req.body.url)
		if (req.body.url === "*") {
			data = {}
		} else {
			url = standardizeURL(req.body.url);
			data = {
				url: url
			}
		}
		console.log("  [DEBUG] fetch contents of url: " + url);
		collection = db.get('contentscollection');
		collection.find(data, function(err, docs) {
			if (err) {
				console.log("[FAIL] failed to fetch contents for " + url);
				res.json({
					success: false
				});
			} else {
				console.log("[SUCC] " + docs.length + ' items');
				for (index in docs) {
					docs[index].url = querystring.escape(docs[index].url);
					if (docs[index].landing_url) {
						docs[index].landing_url = querystring.escape(docs[index].landing_url);
					}
					console.log("  [DEBUG] " + docs[index].url + " l:" + docs[index].landing_url + " " +
						docs[index].contents.length);
				}
				res.json({
					success: true,
					result: JSON.stringify(docs)
				});
			}
		});
	} catch (e) {
		console.log("[FAIL] failed to process req " + e);
		res.json({
			success: false
		});
	}
});

/* Fetch Contents */
app.post('/api/web-contents/trees-fetch', function(req, res) {
	var url, data, index, collection;
	if (!req.body.domain) {
		res.json({
			success: false
		});
		return
	}
	try {
		console.log("domain:" + req.body.domain)
		if (req.body.domain === "*") {
			data = {};
		} else {
			domain = req.body.domain.trim().toLowerCase();
			data = {
				domain: domain
			};
		}
		console.log("  [DEBUG] fetch trees of domain: " + domain);
		collection = db.get('trees');
		collection.find(data, function(err, docs) {
			if (err) {
				console.log("[FAIL] failed to fetch trees from " + url);
				res.json({
					success: false
				});
			} else {
				console.log("[SUCC] " + docs.length + ' items');
				for (index in docs) {
					docs[index].url = querystring.escape(docs[index].url);
				}
				res.json({
					success: true,
					result: JSON.stringify(docs)
				});
			}
		});
	} catch (e) {
		console.log("[FAIL] failed to process fetching tree " + e);
		res.json({
			success: false
		});
	}
});

/* Fetch Scripts */
app.post('/api/web-contents/scripts-fetch', function(req, res) {
	var url, data, index, collection, val, i, j,
		result = {};
	if (!req.body.url) {
		res.json({
			success: false
		});
		return
	}
	try {
		console.log("Fetch scripts of url:" + req.body.url)
		if (req.body.url === "*") {
			data = {};
			result['url'] = "*";
		} else {
			url = standardizeURL(req.body.url);
			data = {
				url: url
			};
			result['url'] = req.body.url;
		}

		console.log("  [DEBUG] fetch scripts : " + data);
		/* fetch script hosts*/
		collection = db.get('scripthosts'); //inlinescripts
		collection.find(data, function(err, docs) {
			if (err) {
				console.log("[FAIL] failed to fetch script hosts for " + url);
				res.json({
					success: false,
					message: "FAIL_FETCH_SCRIPT_HOSTS"
				});
			} else {
				console.log("[SUCC] fetch script hosts " + docs.length + ' items');
				result['scripthosts'] = []
				for (i in docs) {
					for (j in docs[i]['hosts']) {
						val = docs[i]['hosts'][j]
						if (result['scripthosts'].indexOf(val) === -1) {
							result['scripthosts'].push(val);
						}
					}
				}
				if (result['inlinescripts']) {
					//console.log("[DEBUG] send in hosts callback");
					res.json({
						success: true,
						result: JSON.stringify(result)
					});
				}
			}
		});

		/* fetch inline scripts*/
		collection = db.get('inlinescripts'); //inlinescripts
		collection.find(data, function(err, docs) {
			if (err) {
				console.log("[FAIL] failed to fetch inline scripts for " + url);
				res.json({
					success: false,
					message: "FAIL_FETCH_INLINE_SCRIPTS"
				});
			} else {
				console.log("[SUCC] fetch inline scripts " + docs.length + ' items');
				result['inlinescripts'] = []
				for (i in docs) {
					for (j in docs[i]['inlines']) {
						val = docs[i]['inlines'][j]
							//console.log("[DEBUG ]incline:"+val);
						if (result['inlinescripts'].indexOf(val) === -1) {
							result['inlinescripts'].push(val);
						}
					}
				}
				if (result['scripthosts']) {
					//console.log("[DEBUG] send in inlines callback | "+JSON.stringify(result));
					res.json({
						success: true,
						result: JSON.stringify(result)
					});
				}
			}
		});


	} catch (e) {
		console.log("[FAIL] failed to process req " + e);
		res.json({
			success: false
		});
	}
});

/* Remove Trees */
app.post('/api/web-contents/trees-remove', function(req, res) {
	if (!req.body.domain || !req.body.key) {
		console.log(req.body.domain + " " + req.body.key);
		return res.json({
			success: false
		});
	}
	try {
		var collection = db.get('trees');
		collection.remove({
				key: req.body.key,
				domain: req.body.domain
			},
			function(err, doc) {
				if (err) {
					console.log("[FAIL] failed to remove tree into DB: " + err + " " + req.body.key);
					res.json({
						success: false,
						message: err
					});
				} else {
					console.log("[SUCC] removed tree from DB: " +
						req.body.domain + " " + req.body.key);
					res.json({
						success: true,
						domain: req.body.domain,
						key: req.body.key
					});
				}
			});
	} catch (e) {
		console.log("error: " + e);
		res.json({
			success: false,
			message: e
		});
	}
});

app.post('/api/web-contents/store-urls', function(req, res) {

});

//standardizeURL("http%3A%2F%2Fwww.cnn.com");
//standardizeURL("http://www.cnn.com/");
//standardizeURL("http://www.cnn.com/abcd/eed/ffs.html?dsd=22&dsds=233&dsdsd");

var server = app.listen(4040, function() {

	var host = server.address().address;
	var port = server.address().port;

	console.log('Example app listening at http://%s:%s', host, port);

});

/* Store Urls */
app.post('/api/web-contents/rendered-urls-store', function(req, res) {
	if (!req.body.url || req.body.rendered === null) {
		console.log("one of them is missing: " + req.body.url + " " + req.body.rendered);
		return res.json({
			success: false
		});
	}
	var url = req.body.url
	var rendered = req.body.rendered
	var cookies = req.body.cookies
	var domain = req.body.domain
	try {
		var collection = db.get('renderedUrls');
		collection.index('url', {
			unique: true
		});
		collection.insert({
				url: url,
				cookies: cookies,
				domain: domain,
				rendered: rendered
			},
			function(err, doc) {
				if (err) {
					console.log("[INFO] failed to insert urls into DB: " + err + " ");
					console.log("Start trying to update urls in DB: " + url);
					collection.update({
						url: url
					}, {
						$set: {
							url: url,
							cookies: cookies,
							domain: domain,
							rendered: rendered
						}
					}, function(err, doc) {
						if (err) {
							console.log("[FAIL] failed to update urls in DB: " + err + " " + url);
							res.json({
								success: false,
								message: err
							});
						} else {
							console.log("[SUCC] updated urls in DB - [url: <" +
								url + ">, cookies: <" + cookies + ">]");
							res.json({
								success: true,
								url: url
							});
						}
					});

				} else {
					console.log("[SUCC] inserted urls into DB - [url: <" +
						url + ">, cookies: <" + cookies + ">]");
					res.json({
						success: true,
						url: url
					});
				}
			});
	} catch (e) {
		console.log("error: " + e);
		res.json({
			success: false,
			message: e
		});
	}
});

/* Fetch Urls */
app.post('/api/web-contents/rendered-urls-fetch', function(req, res) {
	var url, cookies, userAgent;
	// By default, it will only render not rendered urls
	var findNotRenderedOnly = (req.body.unrendered === false);

	try {
		console.log("Rendering un-rendered urls only: " + findNotRenderedOnly);
		if (findNotRenderedOnly) {
			// Only render new urls (unchecked urls)
			data = {
				rendered: false
			};
		} else {
			data = {};
		}
		console.log(" [DEBUG] fetch urls, cookies and userAgent.");
		collection = db.get('renderedUrls');
		collection.find(data, function(err, docs) {
			if (err) {
				console.log("[FAIL] failed to fetch urls");
				res.json({
					success: false
				});
			} else {
				console.log("[SUCC] " + docs.length + ' items');
				for (record in docs) {
					docs[record].url = querystring.escape(docs[record].url);
				}
				res.json({
					success: true,
					result: JSON.stringify(docs)
				});
			}
		});
	} catch (e) {
		console.log("[FAIL] failed to process fetching tree " + e);
		res.json({
			success: false
		});
	}
});