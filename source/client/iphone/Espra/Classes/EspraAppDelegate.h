// Copyright (c) 2009 Metanational Commons Ltd.
// See LICENSE.txt for details.

#import <CoreLocation/CoreLocation.h>

@interface EspraAppDelegate : NSObject <
        UIApplicationDelegate, UITabBarControllerDelegate, CLLocationManagerDelegate
        > {
    CLLocationManager *locationManager;
    UITabBarController *tabBarController;
    UIWindow *window;
}

@property (nonatomic, retain) CLLocationManager *locationManager;
@property (nonatomic, retain) IBOutlet UITabBarController *tabBarController;
@property (nonatomic, retain) IBOutlet UIWindow *window;

- (void)setupLocationManager;

@end
