--- pyOpenSSL-0.6/src/crypto/x509.c	2004-08-10 11:37:31.000000000 +0100
+++ mo-patched-pyopenssl/src/crypto/x509.c	2008-08-20 02:36:03.000000000 +0100
@@ -478,6 +478,40 @@
     return Py_None;
 }
 
+static char crypto_X509_verify_doc[] = "\n\
+Verifies a certificate request using the supplied public key\n\
+Warning, this is mo's copy&paste of the X509_reg_verify-function\n\
+might not work .. pls test it .. \n\
+ \n\
+ Arguments: self - X509Req object\n\
+            args - The Python argument tuple, should be:\n\
+            key - a public key\n\
+            Returns:   True, if the signature is correct, 0 otherwise.\n\
+";
+
+PyObject *
+crypto_X509_verify(crypto_X509Obj *self, PyObject *args)
+{ 
+    PyObject *obj;
+    crypto_PKeyObj *key;
+    int answer;
+
+    if (!PyArg_ParseTuple(args, "O!:verify", &crypto_PKey_Type, &obj))
+        return NULL;
+
+    key = (crypto_PKeyObj *)obj;
+    
+    if ((answer = X509_verify(self->x509, key->pkey)) < 0)
+    {
+           exception_from_error_queue();
+            return NULL;
+    }
+    
+    return PyInt_FromLong(answer);
+}   
+
+
+
 /*
  * ADD_METHOD(name) expands to a correct PyMethodDef declaration
  *   {  'name', (PyCFunction)crypto_X509_name, METH_VARARGS }
@@ -504,6 +538,7 @@
     ADD_METHOD(subject_name_hash),
     ADD_METHOD(digest),
     ADD_METHOD(add_extensions),
+    ADD_METHOD(verify),
     { NULL, NULL }
 };
 #undef ADD_METHOD
