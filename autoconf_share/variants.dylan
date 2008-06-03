gnu3.compiler.conf: CXX=ccache\ g++-3.4 --enable-shared --with-cppflags="-m32 -msse -m3dnow -msse2 -Wno-deprecated -Wa,--32" --with-threads --with-sse --with-ldflags="--enable-new-dtags"
gnu3.compiler.aipspp.var: --with-casacore=/usr/local --with-wcs=/usr/local
# gnu3.compiler.aipspp.var: --with-aipspp=/aips++/prod/linux_gnu

gnu4.compiler.conf: CXX=ccache\ g++-4.1 --enable-shared --with-cppflags="-m32 -msse -m3dnow -msse2 -Wno-deprecated -Wa,--32" --with-threads --with-sse --with-ldflags="--enable-new-dtags"
gnu4.compiler.aipspp.var: --with-aipspp=/aips++/prod/linux_gnu

gnu3prod.compiler.conf: CXX=ccache\ g++-3.4 --with-cppflags="-m32 -msse -m3dnow -msse2 -Wno-deprecated -Wa,--32" --with-threads --with-sse --with-ldflags="--enable-new-dtags"
gnu3prod.compiler.aipspp.var: --with-aipspp=/aips++/prod/linux_gnu

#gnu3.compiler.conf: CXX=ccache\ /usr/local/gcc-3.4.3/bin/g++ --with-cppflags="-m32 -msse -m3dnow -msse2 -Wno-deprecated -Wa,--32" --with-threads --with-sse --with-ldflags="--enable-new-dtags"
#gnu3.compiler.aipspp.var: --with-aipspp=/aips++/prod/linux_gnu

gnu64.compiler.conf: CXX=ccache\ g++-3.4 --with-cppflags="-march=k8 -m64 -Wno-deprecated -Wno-unused-parameter" --with-ldflags="-rpath /lib64"--with-threads --with-sse --with-ldflags="--enable-new-dtags"
gnu64.compiler.aipspp.var: --with-aipspp=/aips++/prod/linux_gnu_x86_64

sse.var: --with-sse

python.var:  --with-python-version=2.4 --with-python=/usr/include/+pkg+vers --with-python-libdir=/usr/lib 

optimize.var:	--with-optimize='-O4'
debugopt.var:	--with-optimize='-ggdb -O4'
profiler.var: 	--with-debug='-ggdb -pg'
profopt.var: 	--with-optimize='-O4 -pg'

debugopt.variant.conf: 	$(standard) $(debugopt)
profopt.variant.conf: 	$(standard) $(profopt)
prof.variant.conf: 	$(standard) $(profiler)

# debug.variant.conf: $(standard) --with-optimize='-ggdb -DDMI_USE_MALLOC_ALLOC'

