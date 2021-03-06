pragma include once

default_verbosity := 1;
max_debug := F;

if( has_field(environ,'verbose') )
  default_verbosity := as_integer(environ.verbose);
if( has_field(environ,'-verbose') )
  default_verbosity := as_integer(environ['-verbose']);
if( has_field(environ,'debug') )
  max_debug := as_integer(environ.debug);
if( has_field(environ,'-debug') )
  max_debug := as_integer(environ['-debug']);

if( !is_record(default_debuglevels) )
  default_debuglevels := [=];

# scan argv for options
# this includes debug levels of form -dContext=level
override_debuglevels := [=];
for( x in argv )
{
  if( x == '-nostart' ) 
    use_nostart := T;
  else if( x == '-opt' ) 
    use_opt := T;
  else if( x == '-suspend' )
    use_suspend := T;
  else if( x == '-valgrind' )
    use_valgrind := T;
  else if( x == '-gui' )
    use_gui := T;
  else if( x =~ s/^-?verbose=(.*)$/$1/ )
    default_verbosity := as_integer(x);
  else if( x =~ s/^-?debug=(.*)$/$1/ )
    max_debug := as_integer(x);
  else if( x =~ s/^-d(.*)=(.*)$/$1$$$2/ )
  {
    override_debuglevels[x[1]] := lev := as_integer(x[2]);
    print '=======  Overriding debug level:',x[1],'=',lev;
  }
}

# apply max_debug level
if( is_integer(max_debug) )
  for( f in 1:len(default_debuglevels) )
    default_debuglevels[f] := min(max_debug,default_debuglevels[f]);

# find debug levels of form -dContext=level in the environment strings
for( f0 in field_names(environ) )
{
  f := f0;
  if( f =~ s/^-d(.*)$/$1/ )
  {
    lev := override_debuglevels[f] := as_integer(environ[f0]);
    print '=======  Overriding debug level:',f,'=',lev;
  }
}
# apply overrides from above
for( f in field_names(override_debuglevels) )
  default_debuglevels[f] := override_debuglevels[f];

print 'Levels:',default_debuglevels;

options := [];
if( use_nostart )
  options := [options,"nostart"];
if( use_suspend )
  options := [options,"suspend"];
if( use_valgrind )
  options := [options,"valgrind"];
if( use_gui )
  options := [options,"gui"];
  include_gui := True;
if( len(options) )
  print '=======        Run-time options:',options;
print '======= Default verbosity level:',default_verbosity;
print '=======         Max debug level:',max_debug;

  
