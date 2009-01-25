#
#  EspraAppDelegate.py
#  Espra
#
#  Created by tav on 22/10/2008.
#  Copyright ESP Metanational LLP 2008. All rights reserved.
#

from Foundation import *
from AppKit import *

class EspraAppDelegate(NSObject):
    def applicationDidFinishLaunching_(self, sender):
        NSLog("Application did finish launching.")
