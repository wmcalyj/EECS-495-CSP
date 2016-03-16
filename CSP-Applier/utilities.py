import sys, os, re, json, hashlib, uuid, warnings

'''
  Exports:
    1. displayErrorMsg(function_name, msg)
    3. extractAndStoreScriptsFromDOM(url, dom)
    4. displayScriptsFromDB(url)
'''

def displayErrorMsg(fun_name, msg=''):
  print >>sys.stderr, "error in %s: %s" %(fun_name, msg)

def deprecated(func):
    """This is a decorator which can be used to mark functions
    as deprecated. It will result in a warning being emmitted
    when the function is used."""
    def newFunc(*args, **kwargs):
        warnings.warn("Call to deprecated function %s." % func.__name__,
                      category=DeprecationWarning)
        return func(*args, **kwargs)
    newFunc.__name__ = func.__name__
    newFunc.__doc__ = func.__doc__
    newFunc.__dict__.update(func.__dict__)
    return newFunc


