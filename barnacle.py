from __future__ import print_function

import os
import sys
import types
import shutil
import tempfile
import subprocess    


############################################################
# Tests
############################################################

def test_getppid(): 
    """Demo. 

    This is essentially a duplication of another test in the 
    test suite, but it is repeated here to highlight how the
    wrap function to me used.

    We wrap the builtin os.getppid function. The wrapper returns
    returns the same value as the os.getpid function. This shows
    that the wrapped function is executing in a subprocess, and
    that return types are respected (what is returned is an int
    not a string.)
    """
    assert wrap(os.getppid)() == os.getpid()

def test_shell(): 
    yield check_shell, reflect,     ('A','B',''),  ('A','B',"''")
    yield check_shell, verbose_sum, (2,3),         ('2\n3\n','',"5")
    yield check_shell, nothing,     (),            ('','',"None")
    yield check_shell, os.getppid,  (),            ('','',repr(os.getpid()))

def test_wrap(): 
    yield check_wrap, reflect,      ('A','B',''),  ''
    yield check_wrap, verbose_sum,  (2,3,4),       9
    yield check_wrap, nothing,      (),            None
    yield check_wrap, os.getppid,   (),            os.getpid() 

#--- checks

def check_shell( fn, _input, _output ): 
    assert shell( fn, _input ) == _output

def check_wrap( fn, _input, _output ): 
    assert wrap(fn)(*_input) == _output

#=== grist

def nothing():
    pass

def verbose_sum(*args):
    for arg in args: 
        print( arg )
    return sum( args )

def reflect(out,err,ret=None):
    sys.stdout.write( out )
    sys.stderr.write( err )
    return ret


############################################################
# Business
############################################################

TEMPLATE='''
#~~~~~ BEGIN TEMPLATE ~~~~~

"""This code is dynamically created from a template.

Blah. Boilerplate. Blah. Boilerplate. Blah. Boilerplate.
Boilerplate. Blah. Boilerplate. Blah. Boilerplate. Blah.
Blah. Boilerplate. Blah. Boilerplate. Blah. Boilerplate.
Boilerplate. Blah. Boilerplate. Blah. Boilerplate. Blah.

Because everything deserves a docstring.
"""

import sys

from %(module)s import %(name)s as FN

sys.stdout = open( '%(out)s', 'w')
sys.stderr = open( '%(err)s', 'w')
sys_return = open( '%(ret)s', 'w')

# The following line is not PEP8 compliant, but we 
# are most concerned about readability of the source
# code (being the template in this case.)

RET = FN %(args)s 

sys_return.write( repr(RET) ) 

#~~~~~ END TEMPLATE ~~~~~

'''

def wrap(fn):
    def inner(*a):
        return eval( shell( fn, a )[-1] )
    return inner

def shell( fn, args, demo=False ):
    _validate(fn)
    with cleanup( tempfile.mkdtemp() ) as tmp:
        DATA = dict()
        DATA[ 'module' ] = fn.__module__
        DATA[ 'name' ] = fn.__name__
        DATA[ 'args' ] = repr(args)
        DATA[ 'out' ] = tmp + '/out'
        DATA[ 'err' ] = tmp + '/err'
        DATA[ 'ret' ] = tmp + '/ret'
        CODE =  TEMPLATE % DATA 
        if demo:
            return CODE
        output = subprocess.check_output( [sys.executable, "-c", TEMPLATE % DATA] )
        return (
            open( DATA['out'] ).read()
            ,open( DATA['err'] ).read()
            ,open( DATA['ret'] ).read()
        )

def _validate(fn):

    # First validate type.
    _types = list()
    _types.append( types.BuiltinFunctionType )
    _types.append( types.FunctionType )
    if not type(fn) in _types:
        raise CodemakerError('fn: is not a function')

    # Then validate scope.
    if not fn.__module__ in sys.modules:
        raise CodemakerError('fn: does not belong to an imported module')
    if not hasattr( sys.modules[fn.__module__], fn.__name__ ):
        raise CodemakerError('fn: is not found in the global scope of its module')
    if not fn is getattr( sys.modules[fn.__module__], fn.__name__ ):
        raise CodemakerError('fn: name mismatch.')

class CodemakerError(Exception):
    pass


############################################################
# Utilities
############################################################

class cleanup:
    def __init__(self, tmp):
        self.tmp = tmp
    def __enter__(self):
        return self.tmp
    def __exit__(self,a,b,c):
        shutil.rmtree(self.tmp)


############################################################
# Script
############################################################

"""This is for descriptive purposes only. A kind of showing off.
"""

def main():
    if '--template' in sys.argv:
        print( TEMPLATE )
    elif '--demo':
        import string
        print( shell( string.upper, ('hello',), demo=True ) )
    else:
        print( "Usage: <SCRIPTNAME> [ --template | --demo ]" )

if __name__ == "__main__":
    main()
