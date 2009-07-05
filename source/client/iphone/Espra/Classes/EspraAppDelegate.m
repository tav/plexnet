// Copyright (c) 2009 Metanational Commons Ltd.
// See LICENSE.txt for details.

#import "EspraAppDelegate.h"

@implementation EspraAppDelegate

@synthesize locationManager;
@synthesize tabBarController;
@synthesize window;


- (void)applicationDidFinishLaunching:(UIApplication *)application {

    [[UIApplication sharedApplication] setStatusBarHidden:YES animated:NO];

    // NSURL *url = [NSURL URLWithString:@"http://www.espra.com/?__ua__=iphone"];
    // [[UIApplication sharedApplication] openURL:url];

    // Add the tab bar controller's current view as a subview of the window
    [window addSubview:tabBarController.view];
    [self setupLocationManager];

}


- (void)setupLocationManager {

    self.locationManager = [[[CLLocationManager alloc] init] autorelease];
    self.locationManager.delegate = self;
    [self.locationManager startUpdatingLocation];

    NSMutableString *update = [[[NSMutableString alloc] init] autorelease];
    BOOL __set = NO;

    #ifdef __IPHONE_3_0
    if (self.locationManager.headingAvailable) {
        [update appendString:@"Hello Mamading with Compass"];
        [self.locationManager startUpdatingHeading];
        __set = YES;
    }
    #endif

    if (!__set) {
        [update appendString:@"Hello Mamading"];
    }

    NSLog(update);

}

#pragma mark LocationMalarky
#pragma mark -

- (void)locationManager:(CLLocationManager *)manager
    didUpdateToLocation:(CLLocation *)newLocation
           fromLocation:(CLLocation *)oldLocation {
    NSLog(@"Updating location");
    NSMutableString *update = [[[NSMutableString alloc] init] autorelease];
    [update appendFormat:@"Location: %.4f° %@, %.4f° %@",
     fabs(newLocation.coordinate.latitude), signbit(newLocation.coordinate.latitude) ? @"South" : @"North",
     fabs(newLocation.coordinate.longitude),	signbit(newLocation.coordinate.longitude) ? @"West" : @"East"];
}


#ifdef __IPHONE_3_0
- (void)locationManager:(CLLocationManager *)manager
       didUpdateHeading:(CLHeading *)newHeading {
    NSLog(@"Updating heading");
    NSMutableString *update = [[[NSMutableString alloc] init] autorelease];
    [update appendFormat:@"\n\nHeading %.4f North", fabs(newHeading.trueHeading)];
    NSLog(update);
}
#endif


/*
// Optional UITabBarControllerDelegate method
- (void)tabBarController:(UITabBarController *)tabBarController didSelectViewController:(UIViewController *)viewController {
}
*/

/*
// Optional UITabBarControllerDelegate method
- (void)tabBarController:(UITabBarController *)tabBarController didEndCustomizingViewControllers:(NSArray *)viewControllers changed:(BOOL)changed {
}
*/


- (void)dealloc {
    [tabBarController release];
    [window release];
    [super dealloc];
}


@end