#
#  main.py
#  Espra
#
#  Created by tav on 22/10/2008.
#  Copyright ESP Metanational LLP 2008. All rights reserved.
#

#import modules required by application
import objc
import Foundation
import AppKit

from PyObjCTools import AppHelper

# import modules containing classes required to start application and load MainMenu.nib
import EspraAppDelegate

# pass control to AppKit
AppHelper.runEventLoop()
