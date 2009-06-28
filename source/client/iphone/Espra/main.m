// Copyright (c) 2009 Metanational Commons Ltd.
// See LICENSE.txt for details.

int main(int argc, char *argv[]) {
    NSAutoreleasePool * pool = [[NSAutoreleasePool alloc] init];
    int retVal = UIApplicationMain(argc, argv, nil, @"EspraAppDelegate");
    [pool release];
    return retVal;
}

