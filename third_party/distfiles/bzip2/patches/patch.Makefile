--- Makefile	2008-02-14 12:39:18.000000000 +0000
+++ Makefile.plexnet	2008-12-10 12:36:10.000000000 +0000
@@ -90,14 +90,14 @@
 	cp -f libbz2.a $(PREFIX)/lib
 	chmod a+r $(PREFIX)/lib/libbz2.a
 	cp -f bzgrep $(PREFIX)/bin/bzgrep
-	ln -s -f $(PREFIX)/bin/bzgrep $(PREFIX)/bin/bzegrep
-	ln -s -f $(PREFIX)/bin/bzgrep $(PREFIX)/bin/bzfgrep
+	ln -s -f bzgrep $(PREFIX)/bin/bzegrep
+	ln -s -f bzgrep $(PREFIX)/bin/bzfgrep
 	chmod a+x $(PREFIX)/bin/bzgrep
 	cp -f bzmore $(PREFIX)/bin/bzmore
-	ln -s -f $(PREFIX)/bin/bzmore $(PREFIX)/bin/bzless
+	ln -s -f bzmore $(PREFIX)/bin/bzless
 	chmod a+x $(PREFIX)/bin/bzmore
 	cp -f bzdiff $(PREFIX)/bin/bzdiff
-	ln -s -f $(PREFIX)/bin/bzdiff $(PREFIX)/bin/bzcmp
+	ln -s -f bzdiff $(PREFIX)/bin/bzcmp
 	chmod a+x $(PREFIX)/bin/bzdiff
 	cp -f bzgrep.1 bzmore.1 bzdiff.1 $(PREFIX)/man/man1
 	chmod a+r $(PREFIX)/man/man1/bzgrep.1
